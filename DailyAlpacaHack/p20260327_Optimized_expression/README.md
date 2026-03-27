# Optimized expression

## 問題

一見複雑に見える式でも、実は単純な計算の最適化結果かもしれません。
```c
#define TABLE_SIZE 34
const uint8_t table[TABLE_SIZE][2] = {
    {13, 2},
    ...
    {25, 6},
};

int is_correct(const char *buf)
{
    if (strlen(buf) != TABLE_SIZE)
    {
        return 1;
    }

    for (int i = 0; i < TABLE_SIZE; ++i)
    {
        uint64_t x = (uint8_t)buf[i];
        uint64_t y = (x * 3435973837) >> 34;
        uint64_t t = (x * 613566757) >> 32;
        uint64_t z = x - ((((x - t) >> 1) + t) >> 2) * 7;

        if (y != table[i][0] || z != table[i][1])
        {
            return 1;
        }
    }

    return 0;
}

int main()
{
    char buf[TABLE_SIZE + 1];
    scanf("%s", buf);

    if (!is_correct(buf))
    {
        printf("Correct! The flag is %s\n", buf);
        return 0;
    }
    else
    {
        printf("Incorrect...\n");
        return 1;
    }
}
```

## 概要

is_correct関数が0を返すようなbuf入力を求められています。

is_correct関数の中では以下のような処理が行われています。

* まず、入力の文字数がTABLE_SIZE(=34)であるかチェックし、文字数が違う場合は即`1`(失敗)を返す。
* 文字数チェックを通ったら１文字ずつ取り出し、文字コード`x`から計算される`y`,`z`と二次元配列`table`を用いてチェックし、１文字でも違う場合は`1`(失敗)を返す
* 全てのチェックを通ったら、`0`(成功)を返す。

## 解法

`y`と`z`から`x`の逆算を試みましたが、初心者の私にはよくわかりませんでした。

ただ、幸い`x`の範囲は0x20-0x7eの95通りしかないので、全てのパターンを同じチェックにかけて文字を特定することにします。

全パターンとはいっても１文字ずつチェックできるので$`95^{34}`$通り調べる必要はなく、最悪でも95×34=3230回のチェックで済みます。

以下はPythonで記述したソルバーです。配列の初期化の表記が違うことに要注意です。
```py
TABLE = [[13,2],[21,3],[22,0],...(略)...,[25,6],]
SIZE = 34

flag = ""
for i in range(SIZE):
    for x in range(0x20, 0x7f):
        y = (x * 3435973837) >> 34
        t = (x * 613566757) >> 32
        z = x - ((((x - t) >> 1) + t) >> 2) * 7
        if y == TABLE[i][0] and z == TABLE[i][1]:
            flag += chr(x)
            break
print(f"{flag = }")
```

## その他

フラグは取れたものの、結局問題文の意味はよくわかりませんでした。
