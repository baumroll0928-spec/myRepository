# Camelid Match

## 問題

秘めたままにしておいたほうが、やさしい答えもある。
```py
YES = '♡♧'
NO = '♧♡'
MID = '♡'

def rot(s, k):
    k %= len(s)
    return s[k:] + s[:k]

def enc(bit):
    return YES if bit else NO

def row(a, b):
    s = enc(a) + MID + enc(b)
    s = s[1] + s[0] + s[2:]
    return rot(s, secrets.randbelow(5))

def main():
    for animal in ANIMALS:
        a = secrets.randbelow(2)
        b = secrets.randbelow(2)
        print(f'Do both Alice and Bob like {animal}? (y/n)')
        print("Open cards:", row(a, b))
        ans = input('> ').strip().lower()[:1]
        if ans not in {'y', 'n'}:
            print('Please answer with y or n.')
            return 1
        if ans != ('y' if (a and b) else 'n'):
            print('Wrong.')
            return 1

    print(FLAG)
    return 0
```

## 概要

次のルールで出題されるクイズに10回連続で正解しなければいけません。

* `0`か`1`のランダムな整数`a`と`b`が生成される
* `a`と`b`から生成された5枚のカードを観測できる
* `a`と`b`が両方`1`のときは`y`、そうでないときは`n`で答える

カードはランダムな位置で前後入れ替え（カット）をしていることから、カードを見て`a`と`b`を特定することは不可能です。

どうすれば10回連続正解できるのでしょうか？

## 解法

`y`と答えるべきとき、すなわち`a`=`b`=`1`のとき、カットする前の状態は
```
a=1,b=1 ♧♡♡♡♧
```
となり、それ以外のときは
```
a=0,b=1 ♡♧♡♡♧
a=0,b=0 ♡♧♡♧♡
a=1,b=0 ♧♡♡♧♡
```
となります。

これらをよく見比べてみると、`a`=`1`,`b`=`1`のときだけ（前後がつながると考えて）`♡`が3つ連続で並んでいて、それ以外のときは`♡`が1つと2つに分かれています。

この特徴はどこで何回カットしても変わりません。

これにより、カット後のカードに含まれる`♡`が3つ連続しているかどうかを見ることで、`a`と`b`の具体的な値はわからなくても両方`1`であるかそうでないかを見抜くことができます。

```py
import pwn

HOST, PORT = "34.170.146.252", 43344
p = pwn.remote(HOST, PORT)

def check(c):
    for i in range(5):
        if '♡♡♡' in c:
            return True
        c = c[1:] + c[:1]
    return False

for _ in range(10):
    d = p.recvuntil(b'> ')
    cards = d.decode().split()[-2]
    print(cards)
    ans = b'y' if check(cards) else b'n'
    p.sendline(ans)

print(p.recvall(timeout=5).decode())
```
