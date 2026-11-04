# Remnant

## 問題

何か消し忘れた気がします。

```py
flag = b64encode(b"Alpaca{?????}")

while True:
    try:
        x = input("Input: ").encode()
        b64decode(bytes(a ^ b for a, b in zip(flag, x))) # remnant
        if x == flag:
            print("Correct!")
        else:
            print("Incorrect...")
    except:
        print("Error...")
```

## 概要

flagをBase64エンコードしたものを繰り返し予測し、当たっていたら`Correct!`、はずれだったら`Incorrect...`と表示されるようになっています。

その判定の前に、なぜか正解と入力値のXORをとったものをBase64デコードしていますが、このデコード結果は表示されないので確認することができません。

フラグの未知部分はたったの5文字ですが全て試すと $`95^{5}=7,737,809,375`$ 通りありとんでもない時間がかかりそうです。

どうすれば現実的な時間内にBase64エンコードされたフラグを得ることができるのでしょうか？

## 方針

b64decode関数は対象文字(A-Za-z0-9+/=)以外の文字を全て無視することを利用して、エラーの有無から1文字ずつ特定していく。

## 解法

Pythonの`zip(a, b)`は、2つのイテラブル`a`, `b`を並行させますが、長さが異なる場合は短い方に合わせて切られます。

さて、ダミーフラグ`Alpaca{?????}`をBase64エンコードすると`QWxwYWNhez8/Pz8/fQ==`になりますが、これと`Q`をzipを使ってXORすると`\x00`に、`QW`とXORすると`\x00\x00`といった具合になります。

これらはb64decode関数的には全て無視されて空文字列になるので、デコード結果も空文字列となり何ら問題はありません。

しかし、もし最後の文字だけが対象文字(A-Za-z0-9+/=)だったらどうでしょうか？

この場合はその対象文字1文字だけに見えるので、デコードに失敗してエラーになります。（正しいBase64文字列は必ず長さが4の倍数になります。）

これを利用して、途中までわかっている状態からいろいろな文字を末尾に付け加えてエラーの有無を確認し、1文字ずつ特定していくことができるのではないでしょうか？

そうすると、フラグのプレフィックスの関係で`QWxwYWNhe`までは確定なので、その後につづく7文字分を1文字ずつ探すことになりますね。

具体的にどんな文字を試せばいいか考えてみます。

※ここから先は適宜ASCIIコード表を見ながら読んだ方がわかりやすいかもしれません。

ASCIIコードにおいて、対象文字は

- +: 0x2b
- /: 0x2f
- 0-9: 0x30-0x39
- =: 3d
- A-Z: 0x41-0x5a
- a-z: 0x61-0x7a

のように分布しています。

というわけで、手始めに、空白(0x20)をつけてみます。

0x20とXORをとることにより、0x00-0x1fと0x20-0x3f、0x40-0x5fと0x60-0x7fが入れ替わります。

このとき、アルファベットだったら大文字と小文字が入れ替わるだけなのでエラーになり、数字または記号の場合は制御文字になるのでエラー回避します。

これで、アルファベットとそれ以外に場合分けすることができました。

まず、アルファベットの場合を考えます。

!(0x21)～/(0x2f)の15個を順番に試し、エラー回避の個数を数えます。

これにより、大文字小文字を入れ替えた先の段全て(0x?0-0x?f)を見ることになるのですが、エラー回避の個数が1個であれば上段(0x4?または0x6?)、2個以上であれば下段(0x5?または0x7?)であることがわかります。（上段にエラー回避文字はそれぞれ@(0x40)と`(0x60)の1つずつしかないからです。）

そして上段の場合、その唯一のエラー回避の場所(1～15)から大文字小文字の2種類まで特定できます。（例えば5でエラー回避の場合、`E`または`e`となります。）

あとは0x4fと前記場所の1～15をXORしたものを試せば、大文字の場合は/(0x2f)になりエラー、小文字の場合は制御文字の0x0fになりエラー回避となるので、区別することができます。

下段の場合も同様に、0(0x30)～:(0x3a)で試し、0x5fを使って大文字か小文字かを区別します。

そして、アルファベット以外の場合も同様に、`(0x60)～o(0x6f)とp(0x70)～y(0x79)で回すことで特定することができます。

## ソルバー

```py
from base64 import b64decode
import pwn

HOST, PORT = "localhost", 1337
#HOST, PORT = "34.170.146.252", 57207
p = pwn.remote(HOST, PORT)

def is_error(pre:str, ch:str)->bool:
    p.sendlineafter(b': ', (pre + ch).encode())
    d = p.recvline()
    return (d.startswith(b'Err'))

def find_next_char(pre:str)->str:
    cnt = 0
    last_idx = -1
    if is_error(pre, ' '):
        # アルファベット
        for i in range(1, 16):
            if not is_error(pre, chr(0x20 + i)):
                cnt += 1
                last_idx = i
        if cnt == 1:
            # 上段
            if is_error(pre, chr(0x4f ^ last_idx)):
                # 小文字(a-o)
                return chr(0x60 + last_idx)
            else:
                # 大文字(A-O)
                return chr(0x40 + last_idx)
        # 下段
        for i in range(11):
            if not is_error(pre, chr(0x30 + i)):
                last_idx = i
                break
        if is_error(pre, chr(0x5f - last_idx)):
            # 小文字(p-z)
            return chr(0x70 + last_idx)
        else:
            # 大文字(P-Z)
            return chr(0x50 + last_idx)
    else:
        # アルファベット以外
        for i in range(16):
            if not is_error(pre, chr(0x60 + i)):
                cnt += 1
                last_idx = i
        if cnt == 1:
            # 記号(+/)
            return chr(0x20 + last_idx)
        for i in range(10):
            if not is_error(pre, chr(0x70 + i)):
                # 数字(0-9)
                return chr(0x30 + i)
        # 記号(=)
        return '='

flag_b64 = 'QWxwYWNhe'
for _ in range(7):
    flag_b64 += find_next_char(flag_b64)
    print(flag_b64)
flag = b64decode(flag_b64.encode()) + b'}'
print(f"{flag = }")
```

## その他

たぶん制御文字を送っても大丈夫だと思いますが、入力にLF(0x0a)などが含まれていると誤作動するかもしれないと思い、ASCII印字可能文字(0x20-0x7e)だけ使って解くことにこだわってみました。
