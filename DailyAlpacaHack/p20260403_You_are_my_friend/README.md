# You are my friend

## 問題

やあ！友よ！
```py
import secrets

def rot13_char(c):
    if 'a' <= c <= 'z':
        return chr((ord(c) - ord('a') + 13) % 26 + ord('a'))
    if 'A' <= c <= 'Z':
        return chr((ord(c) - ord('A') + 13) % 26 + ord('A'))
    return c

def rot13(text):
    return ''.join(rot13_char(c) for c in text)

flag = "Alpaca{REDACTED}"

ct = rot13(flag)

key = secrets.randbelow(256)
cts = [ord(ct[0]) ^ key]
for i in range(1, len(ct)):
    cts.append(ord(ct[i]) ^ ord(ct[i - 1]))

print(cts)
```

## 概要

フラグがランダムな`key`を使って暗号化されているようです。

`key`はわかりませんがどうやって復号すればいいのでしょうか？

## 方針

フラグのプレフィックスを利用し`key`を無視して復号する。

## 解法

暗号化は、ROT13で変換したフラグ`ct`の各文字の一つ前の文字（最初は`key`）とXORをとっています。

keyがわかれば、$`cts[0] = key \oplus ct[0]`$から$`ct[0] = cts[0] \oplus key`$が求まり、以降順次$`cts[i] = ct[i] \oplus ct[i-1]`$から$`ct[i] = cts[i] \oplus ct[i-1]`$が求まりますが、`key`はわかりません。

しかし、この問題に関して言えば、`flag = "Alpaca{REDACTED}"`やフラグ入力欄のプレースホルダから、フラグ形式が`Alpaca{.*}`であることがわかっています。

よって、`ct[0] = rot13_char('A') = 'N'`となり、ここから順次`ct[i]`を求めていくことができます。

```py
def rot13_char(c):
    略

def rot13(text):
    略

cts = [238, 55, 26, 13, 30, ...略...  7, 23, 15]

ct = rot13_char('A')
for i in range(1, len(cts)):
    ct += chr(cts[i] ^ ord(ct[-1]))
flag = rot13(ct)
print(flag)
```
