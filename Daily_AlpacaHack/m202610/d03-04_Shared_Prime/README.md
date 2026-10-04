# Shared Prime

## 問題

simple!

```py
FLAG = os.environ.get("FLAG", "Alpaca{DUMMY}").encode()
e = 65537

p = getPrime(1024)
q1 = getPrime(1024)
q2 = getPrime(1024)

n1 = p * q1
n2 = p * q2
m = bytes_to_long(FLAG)
assert m < min(n1, n2)

c1 = pow(m, e, n1)
c2 = pow(m, e, n2)

print(f"{n1 = }")
print(f"{n2 = }")
print(f"{c1 = }")
print(f"{c2 = }")
```

## 概要

2つの公開鍵`(n1, e)`,`(n2, e)`とこれらによって整数化したフラグ`m`を暗号化した`c1`,`c2`が与えられます。

それぞれ正規のRSA暗号なので破れそうにありませんが、どうしたら`m`を得ることができるのでしょうか？

## 方針

`n1`と`n2`の最大公約数から`p`を求める。

## 解法

`n1`と`n2`の作り方に注目します。

```py
n1 = p * q1
n2 = p * q2
```

`n1`も`n2`も2つの素数がかけられていますが、片方の素数に同じ`p`が使われているようです。

`p`,`q1`,`q2`は全て素数なので、`n1`と`n2`は共通の素因数`p`をもち、かつそれだけです。

よって、`n1`と`n2`の最大公約数は`p`になります。

RSAの安全性の根拠は巨大な素数の積の素因数分解が困難であることです。

しかし、最大公約数を求めるのであれば、ユークリッド互除法などの効率的なアルゴリズムが存在するため、すぐに求められてしまいます。

`p`が求まれば`q1`も求まるので、あとは通常どおりの手順で`c1`を復号することができます。

## ソルバー

```py
from Crypto.Util.number import long_to_bytes, GCD

# ここにoutput.txtの内容を全てコピペする

p = GCD(n1, n2)
q1 = n1 // p
phi1 = (p - 1) * (q1 - 1)
e = 65537
d1 = pow(e, -1, phi1)
m = pow(c1, d1, n1)
flag = long_to_bytes(m)
print(f"{flag = }")
```
