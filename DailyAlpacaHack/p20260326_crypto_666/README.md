# crypto_666

## 問題

悪魔の素数を作ることはできますか？
```py
import os
from Crypto.Util.number import isPrime

flag = os.environ.get("FLAG", "Alpaca{*** REDACTED ***}")

p = input("p > ")
if ("6"*666 in p) and isPrime(int(p)):
    print(flag)
else:
    print("fail")
```

## 概要

連続する666個の6を含む素数の入力を求められているようです。

## 解法

まずはズルできないかいろいろ考えてみました。
```
p > 2 #666…6
```
```
p > 2.666…6
```
```
p > 2+1//666…6
```
残念ながらいずれもエラーになってしまいます。

ちゃんと666個の連続する6を含む素数を探す必要があるようです。

### 方針１：ループして探す

2より大きい整数が素数であるためには、少なくとも1の位が奇数である必要があります。

なので、666…6の右に奇数をつけたものを順次素数判定で探していきます。

とりあえず４桁までに絞ってありますが、もしこれで見つからなければ範囲を広げる必要があるでしょう。
```py
from Crypto.Util.number import isPrime

p = "6" * 666

for i in range(1, 10000, 2):
    q = str(i)
    n = int(p + q)
    if isPrime(n):
        print("found.", q)
        break
else:
    print("not found.")
```
結果
```
found. 113
```
意外と早く見つかってよかったです。

ちなみに10行目のbreakを削除すると10000未満の答えを全て出せますが、12個もあるようです。

あとは
```sh
$ python3 -c 'print("6"*666+"113")' | nc 34.170.146.252 15827
```
のように投げればオッケーです。

### 方針２：sympyのnextprimeを使う

sympyモジュールには、それより大きい最小の素数を返す関数nextprimeがあるので、これを利用します。

最初に桁数を決め、最小の素数を取得した後、666…6の部分に侵食していないか確認します。

※ただ、方針１の解法より少し処理が遅いようです。
```py
from sympy import nextprime

p = "6" * 666

for d in range(1, 5):
    p0 = p + "0" * d
    n = nextprime(int(p0))
    s = str(n)
    if s.startswith(p):
        print("found.", s[-d:])
        break
else:
    print("not found.")
```
