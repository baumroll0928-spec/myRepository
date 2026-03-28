
今回もとても面白い問題でした。

# EncodeDecode

## 問題

swapswap は失敗でした…
今度は大丈夫なはず!
```py
import os

flag = os.environ.get("FLAG", "Alpaca{*** REDACTED ***}")

text = input("text> ")
encoding = input("encoding> ")

assert text.isascii(), "Text must be ASCII"

# This must be true, isn't it?
if text == text.encode(encoding).decode(encoding):
    print("Check passed!")
else:
    print("Check failed - !?")
    print("Here is your flag:", flag)
```

## 概要

textをエンコードしデコードしたものが元のtextと異なるようなtextとencodingの入力が求められています。

※過去問のSwapSwapではswapcaseを２回行っていましたね。

textに含まれる文字は全てASCII文字（0x00-0x7f）でなければいけません。

普通に考えたら、ASCII文字をエンコードしてデコードしたら必ず元に戻りそうに思えます。

どのようなtextやencodingを指定すれば`Check failed`を起こすことができるのでしょうか？

## 解法

１対１でエンコード、デコードするような素直なエンコーディング方式ではこの問題は解けません。

エンコードまたはデコードの段階で何らかのエスケープ等を行うエンコーディング方式があるのではないかと考えました。

そして調べていくうちに`idna`というエンコーディング方式に行きつきました。

これは、Punycodeという日本語などの非ASCII文字をドメインに使えるように変換するアルゴリズムを用いたエンコーディング方式のようです。

例えば`アルパカ`は`xn--ccks7i8d`になります。
```py
text = "アルパカ"
encoding = "idna"
print(text)
print(text.encode(encoding))
print(text.encode(encoding).decode(encoding))
```
```
アルパカ
b'xn--ccks7i8d'
アルパカ
```

エンコード結果に含まれるバイナリデータは全てASCII可視文字の範囲内のようです。

ということは、最初からこの`xn--ccks7i8d`を入力してあげれば、
```
"アルパカ"
↓
エンコード
↓
b'xn--ccks7i8d' →デコード→ "アルパカ"
↑
エンコード
↑
"xn--ccks7i8d"
```
のように、元と異なるデコード結果になるのではないでしょうか？

やってみましょう。
```py
text = "xn--ccks7i8d"
encoding = "idna"
print(text)
print(text.encode(encoding))
print(text.encode(encoding).decode(encoding))
```
```
xn--ccks7i8d
b'xn--ccks7i8d'
アルパカ
```
予想どおりでした！というわけで、
```
text> xn--ccks7i8d
encoding> idna
```
のように入力すれば、`Check failed`を起こし、フラグを取ることができます。
