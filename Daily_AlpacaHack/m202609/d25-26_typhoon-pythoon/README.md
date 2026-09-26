# typhoon-pythoon

## 問題

台風がプログラムを遠くへ飛ばしてしまいました。 どうやらフラグは台風の目の中にあるようです。

このファイルは Python 3.10 でコンパイルされています。import や実行には Python 3.10 を使用してください。

初心者向けヒント
```
.pyc ファイルにはコンパイル済みの Python バイトコードが含まれます。
モジュールとして import し、dir() や dis.dis() で調べてみましょう。
```

配布ファイル: server.pyc

## 概要

server.pycを実行したところ、
```
PS C:\ctf> python server.pyc  
RuntimeError: Bad magic number in .pyc file
```
となってしまい、実行できなかったので、Python 3.10をインストールして実行してみたところ、
```
PS C:\ctf> py -3.10 server.pyc
Hint: Move this file into the eye of the typhoon.
```
「ヒント：このファイルを台風の目の中に移動せよ。」とでてきました。

「台風の目」ってなんでしょうか？どうすれば実行できるのでしょうか？

## 解法

とりあえず初心者向けヒントにあるとおりimportしてdir()の内容を出力するコードを3.10で実行してみます。
```py
import server

print(dir(server))
```
```
PS C:\ctf> py -3.10 local.py
['EYE_DATA', 'Path', '__builtins__', '__cached__', '__doc__', '__file__', '__loader__', '__name__', '__package__', '__spec__', 'is_inside_the_typhoon_eye', 'main', 'reverse_the_wind']
```

変数名や関数名と思われるものがでてきました。

`EYE_DATA`というのはグローバル変数でしょうか？内容を出力してみます。
```py
print(server.EYE_DATA)
```
```
b'\xcf\xc5\xec\xc2\xdd\xd0\xc3\xb7\xaf\xbe\xb7\xb2\x91\xa2\x84\x9fwZi^\x7f~SIi%,.9-\x19\x0b\x06\x1a\xff\xed\xf7'
```
バイナリデータのようですね。

`Path`は`pathlib`モジュールにあるアレですね。元のソースコードの中で`from pathlib import Path`とかされているのでしょう。

`is_inside_the_typhoon_eye`, `main`, `reverse_the_wind`は関数と思われます。

しかし、同じように出力しても、
```py
print(server.main)
```
```
<function main at 0x00000237B2484790>
```
その中身まではわかりません。

そこで、ヒントにあるもう一つの`dis.dis()`を使ってみます。

```py
import server
import dis

dis.dis(server.main)
```
```
 36           0 LOAD_GLOBAL              0 (is_inside_the_typhoon_eye)
              2 CALL_FUNCTION            0
              4 POP_JUMP_IF_TRUE         9 (to 18)

 37           6 LOAD_GLOBAL              1 (print)
              8 LOAD_CONST               1 ('Hint: Move this file into the eye of the typhoon.')
             10 CALL_FUNCTION            1
             12 POP_TOP

 38          14 LOAD_CONST               0 (None)
             16 RETURN_VALUE

 40     >>   18 LOAD_GLOBAL              2 (input)
             20 LOAD_CONST               2 ('What was inside the eye? > ')
             22 CALL_FUNCTION            1
             24 STORE_FAST               0 (answer)

 42          26 LOAD_FAST                0 (answer)
             28 LOAD_GLOBAL              3 (reverse_the_wind)
             30 LOAD_GLOBAL              4 (EYE_DATA)
             32 CALL_FUNCTION            1
             34 COMPARE_OP               2 (==)
             36 POP_JUMP_IF_FALSE       25 (to 50)

 43          38 LOAD_GLOBAL              1 (print)
             40 LOAD_CONST               3 ('The typhoon is gone. Correct!')
             42 CALL_FUNCTION            1
             44 POP_TOP
             46 LOAD_CONST               0 (None)
             48 RETURN_VALUE

 45     >>   50 LOAD_GLOBAL              1 (print)
             52 LOAD_CONST               4 ('The wind is still too strong...')
             54 CALL_FUNCTION            1
             56 POP_TOP
             58 LOAD_CONST               0 (None)
             60 RETURN_VALUE
```
うわ、なにやら難しそうなコードが出てきました。

しかし、全く見たことないコードですが、よく見てみるといつもの`objdump -d chal`で出力するアセンブリコードとどことなく似ていることがわかります。

それぞれの命令は、

- LOAD_GLOBAL: スタックにグローバル変数や関数を積む
- LOAD_CONST: スタックに定数を積む
- CALL_FUNCTION: 関数を呼び出す
- RETURN_VALUE: 関数から抜ける
- POP_JUMP_IF_TRUE: スタックから取り出してTrueなら飛ぶ
- POP_JUMP_IF_FALSE: スタックから取り出してFalseなら飛ぶ
- STORE_FAST: スタックから取り出して変数に代入する
- POP_TOP: スタックから取り出して捨てる
- COMPARE_OP: スタックから2つ取り出して比較し正しい場合はTrue,そうでない場合はFalseを積みなおす

のような意味なのでしょう。スタックマシンの動作を理解していれば読めそうです。

そんなふうになんとか雰囲気をつかみ読んでみたところ、元のソースコードはこんな感じだったのではなかろうかとなりました。
```py
def main():
    if not is_inside_the_typhoon_eye():
        print('Hint: Move this file into the eye of the typhoon.')
        return None
    answer = input('What was inside the eye? > ')
    if answer == reverse_the_wind(EYE_DATA):
        print('The typhoon is gone. Correct!')
        return None
    print('The wind is still too strong...')
    return None
```
最初の実行で`Hint: Move this file into the eye of the typhoon.`とでたのは、この`is_inside_the_typhoon_eye`関数のチェックに引っかかったのが原因のようですね。

というわけで同じように`is_inside_the_typhoon_eye`関数を見てみます。
```
 19           0 LOAD_GLOBAL              0 (Path)
              2 LOAD_GLOBAL              1 (__file__)
              4 CALL_FUNCTION            1
              6 LOAD_METHOD              2 (resolve)
              8 CALL_METHOD              0
             10 LOAD_ATTR                3 (parent)
             12 LOAD_ATTR                4 (name)
             14 STORE_FAST               0 (current_place)

 20          16 LOAD_GLOBAL              5 (bytes)
             18 BUILD_LIST               0
             20 LOAD_CONST               1 ((101, 121, 101))
             22 LIST_EXTEND              1
             24 CALL_FUNCTION            1
             26 LOAD_METHOD              6 (decode)
             28 CALL_METHOD              0
             30 STORE_FAST               1 (required_place)

 21          32 LOAD_FAST                0 (current_place)
             34 LOAD_FAST                1 (required_place)
             36 COMPARE_OP               2 (==)
             38 RETURN_VALUE
```
これも頑張って読んでみます。
```py
from pathlib import Path

def is_inside_the_typhoon_eye():
    current_place = Path(__file__).resolve().parent.name
    required_place = bytes([101, 121, 101]).decode()
    return current_place == required_place
```
ふむふむなるほど、つまり、`current_place`（ソースファイルが置かれているフォルダの名前）と`required_place`（'eye'）が等しくないといけないということですね。

これが「台風の目に移動させる」ということなのでしょう。

というわけで`eye`フォルダを作って`server.pyc`をその中に入れて実行してみます。
```
PS C:\ctf\eye> py -3.10 server.pyc
What was inside the eye? >
```
ちょっと進展がありましたが、何を入力すればいいのかわかりません。

いったんてきとーな文字列を入力してみます。
```
What was inside the eye? > Alpaca{typhoon}
The wind is still too strong...
```
「風は未だに強すぎる…」とでてしまいます。

再度`main`関数を見てみると、`reverse_the_wind(EYE_DATA)`の戻り値と同じ文字列を入力すれば良いことがわかります。

最後に`reverse_the_wind`関数を見てみます。
```
 26           0 LOAD_GLOBAL              0 (Path)
              2 LOAD_GLOBAL              1 (__file__)
              4 CALL_FUNCTION            1
              6 LOAD_METHOD              2 (resolve)
              8 CALL_METHOD              0
             10 LOAD_ATTR                3 (parent)
             12 LOAD_ATTR                4 (name)
             14 LOAD_METHOD              5 (encode)
             16 CALL_METHOD              0
             18 STORE_FAST               1 (location)

 27          20 BUILD_LIST               0
             22 STORE_FAST               2 (restored)

 28          24 LOAD_GLOBAL              6 (enumerate)
             26 LOAD_FAST                0 (observations)
             28 CALL_FUNCTION            1
             30 GET_ITER
        >>   32 FOR_ITER                31 (to 96)
             34 UNPACK_SEQUENCE          2
             36 STORE_FAST               3 (position)
             38 STORE_FAST               4 (value)

 29          40 LOAD_FAST                1 (location)
             42 LOAD_FAST                3 (position)
             44 LOAD_GLOBAL              7 (len)
             46 LOAD_FAST                1 (location)
             48 CALL_FUNCTION            1
             50 BINARY_MODULO
             52 BINARY_SUBSCR
             54 STORE_FAST               5 (place)

 30          56 LOAD_FAST                3 (position)
             58 LOAD_CONST               1 (7)
             60 BINARY_MULTIPLY
             62 LOAD_CONST               2 (41)
             64 BINARY_ADD
             66 LOAD_FAST                5 (place)
             68 BINARY_ADD
             70 LOAD_CONST               3 (255)
             72 BINARY_AND
             74 STORE_FAST               6 (wind)

 31          76 LOAD_FAST                2 (restored)
             78 LOAD_METHOD              8 (append)
             80 LOAD_GLOBAL              9 (chr)
             82 LOAD_FAST                4 (value)
             84 LOAD_FAST                6 (wind)
             86 BINARY_XOR
             88 CALL_FUNCTION            1
             90 CALL_METHOD              1
             92 POP_TOP
             94 JUMP_ABSOLUTE           16 (to 32)

 32     >>   96 LOAD_CONST               4 ('')
             98 LOAD_METHOD             10 (join)
            100 LOAD_FAST                2 (restored)
            102 CALL_METHOD              1
            104 RETURN_VALUE
```
今度は長いし複雑で大変ですが同じように読んでいきます。
```py
def reverse_the_wind(observations):
    location = Path(__file__).resolve().parent.name.encode()
    restored = []
    for position, value in enumerate(observations):
        place = location[position % len(location)]
        wind = (position * 7 + 41 + place) & 255
        restored.append(chr(value ^ wind))
    return ''.join(restored)
```
`observations`はいきなり登場しているので引数だと考えられます。

これで全てがわかりました。

ファイルが正しいフォルダ名の場所に置かれていたら、暗号文`EYE_DATA`を復号し、入力値と比較判定するいわゆる「フラグチェッカー」だったのですね。

ここまできたらあとは簡単です。

復号関数`reverse_the_wind`の中でもファイルが置かれているフォルダ名が使われていますが、ここまで来ているということは'eye'フォルダに置かれているはずなので、`location`は`b'eye'`に置き換えてしまって良いでしょう。

よって、次のコードを（Pythonのバージョンやファイルの場所は関係なく）実行することで入力すべき文字列（フラグ）を得ることができます。
```py
EYE_DATA = b'\xcf\xc5\xec...略...\xf7'

def reverse_the_wind(observations):
    location = b'eye'
    restored = []
    for position, value in enumerate(observations):
        place = location[position % len(location)]
        wind = (position * 7 + 41 + place) & 255
        restored.append(chr(value ^ wind))
    return ''.join(restored)

print(reverse_the_wind(EYE_DATA))
```
```
Alpaca{*****************************}
```

再度server.pycを実行してこれを入力してみます。
```
PS C:\ctf\eye> py -3.10 server.pyc
What was inside the eye? > Alpaca{*****************************}
The typhoon is gone. Correct!
```
無事「台風は去りました。」

## 別解

今回は頑張って解析しましたが、調べてみると、pycファイルを解析してくれる「pycdc」というツールがあったようです。

[ダウンロードサイト](https://github.com/extremecoders-re/decompyle-builds/releases)

ここにある「pycdc.exe」をダウンロードして下記のように実行するだけです。
```
PS C:\ctf> .\pycdc.exe server.pyc > chall.py
```
すると先ほど解析したのとだいたい同じようなソースコードがでてきます。これは便利ですね。

しかし、ところどころ`print`や`input`がNoneになっていたり、最後にナゾの`return None`があったりと、完璧ではないようです。
```py
# Source Generated with Decompyle++
# File: server.pyc (Python 3.10)

from pathlib import Path
EYE_DATA = bytes([
    207,
    197,
    ...
    237,
    247])

def is_inside_the_typhoon_eye():
    '''Check whether the observation server is in the only calm place.'''
    current_place = Path(__file__).resolve().parent.name
    required_place = bytes([
        101,
        121,
        101]).decode()
    return current_place == required_place


def reverse_the_wind(observations = None):
    '''Return observations to their state before the wind moved them.'''
    location = Path(__file__).resolve().parent.name.encode()
    restored = []
    for position, value in enumerate(observations):
        place = location[position % len(location)]
        wind = position * 7 + 41 + place & 255
        restored.append(chr(value ^ wind))
    return ''.join(restored)


def main():
    if not is_inside_the_typhoon_eye():
        print('Hint: Move this file into the eye of the typhoon.')
        return None
    answer = None('What was inside the eye? > ')
    if answer == reverse_the_wind(EYE_DATA):
        print('The typhoon is gone. Correct!')
        return None
    None('The wind is still too strong...')

if __name__ == '__main__':
    main()
    return None
```
