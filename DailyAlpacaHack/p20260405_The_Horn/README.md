
# The Horn

## 問題

Originally “Carry the Flame”, but for AlpacaHack
⚓⚓⚓⚓⚓⚓⚓
What do you think is the best score?
```py
import os

ROUNDS = 32
BLOCK_SIZE = 32

KEY = os.urandom(BLOCK_SIZE)
FLAG = os.getenv("FLAG", "flag{example_flag}")

PBOX = [5, 22, 31, 18, 3, 19, 11, 13, 10, 25, 24, 0, 2, 17, 20, 12, 6, 26, 1, 7, 16, 4, 27, 21, 15, 8, 30, 28, 14, 23, 29, 9]

def bxor(bs1, bs2):
    return bytes([b1 ^ b2 for b1, b2 in zip(bs1, bs2)])

def pbox(pt):
    assert len(PBOX) == BLOCK_SIZE
    return bytes([pt[PBOX[index]] for index in range(BLOCK_SIZE)])

def encrypt(pt, key):
    for _ in range(ROUNDS):
        pt = bxor(pt, key)
        pt = pbox(pt)
    return pt

CHALLENGE = os.urandom(32)
print(f"CHALLENGE: {encrypt(CHALLENGE, KEY).hex()}")


for i in range(210):
    inp = input("pt: ")
    if inp != "guess":
        pt = bytes.fromhex(inp)
        assert len(pt) == BLOCK_SIZE
        print(encrypt(pt, KEY).hex())

    else:
        challenge_guess = input("challenge: ")
        if bytes.fromhex(challenge_guess) == CHALLENGE:
            print(f"=== Your score is {i} ===")
            print("flag:", FLAG)
        exit()
```

## 概要

実行すると、`CHALLENGE`を`KEY`で暗号化した暗号文が表示されます。（`CHALLENGE`と`KEY`はいずれもランダムな32バイト）

挑戦者は、自身で指定したバイト列を同じ`KEY`で暗号化した暗号文を、209回まで繰り返し観測することができます。

バイト列の代わりに`guess`を送信すると解答モードに移行し、そこで`CHALLENGE`を当てることができたらフラグを獲得できます。

どのようなバイト列を送信すれば、`CHALLENGE`を割り出すことができるのでしょうか？

## 結論

今回の問題のようにSBOX変換が無い場合は、１回観測すれば十分です。

## 解法

暗号化では、次の手順を32回繰り返しています。

* `KEY`とXORをとる
* `PBOX`配列を使って並び替える

一見`KEY`がわからないと暗号化`CHALLENGE`の復号は事実上不可能なように思えます。

しかし、この問題の暗号化方式では、`PBOX`が決まると「どの文字がどの位置に行くか」が決まるうえに、さらに`KEY`が決まると「どの文字が何とXORをとるか」が決まるため、

（平文を並び替えだけ32回行ったもの）⊕（暗号文）

は、平文が何であっても`PBOX`と`KEY`が同じである限り常に同じになります。

ここで、全て0のバイト列を送信し暗号文を観測します。（全て0だと並べ替えても全て0のままだしXORをとっても相手が変わらないので扱いやすいです。）

すると、

（CHALLENGE並び替え）⊕（CHALLENGE暗号化）= ~~（00...00並び替え）⊕~~（00..00暗号化）

より、

（CHALLENGE並び替え） = （CHALLENGE暗号化）⊕（00..00暗号化）

となるので、これに並び替えの逆変換を行うことで`CHALLENGE`を得ることができます。

## ソルバー作成

まず下準備として32回並び替えの逆変換を行うためのリストを作成します。
```py
ROUNDS = 32
BLOCK_SIZE = 32
PBOX = [5, 22, 31, 18, 3, 19, 11, 13, 10, 25, 24, 0, 2, 17, 20, 12, 6, 26, 1, 7, 16, 4, 27, 21, 15, 8, 30, 28, 14, 23, 29, 9]

# 32回変換する
mp = [i for i in range(BLOCK_SIZE)]
for _ in range(ROUNDS):
    mp = [mp[i] for i in PBOX]
# 逆変換にする
rev_map = [0] * BLOCK_SIZE
for i in range(BLOCK_SIZE):
    rev_map[mp[i]] = i
print(f"{rev_map = }"
```

この`rev_map`配列を使って`CHALLENGE`を求め、フラグを獲得します。
```py
import pwn

HOST, PORT = '34.170.146.252', 30351

rev_map = [1, 17, 8, 7, 19, 22, 3, 28, 12, 24, 2, 18, 25, 14, 23, 9, 4, 20, 13, 27, 21, 5, 26, 0, 31, 15, 16, 30, 29, 11, 6, 10]

def rev(bs):
    return bytes([bs[i] for i in rev_map])

def bxor(bs1, bs2):
    return bytes([b1 ^ b2 for b1, b2 in zip(bs1, bs2)])

# 接続
p = pwn.remote(HOST, PORT)

# CHALLENGEの暗号文を取得
d = p.recvuntil(b'pt: ')
c_chal_hex = d.decode().split()[1]
c_chal = bytes.fromhex(c_chal_hex)

# 00...00を送信しその暗号文を取得
p.sendline(('00' * 32).encode())
d = p.recvuntil(b'pt: ')
c_all0_hex = d.decode().split()[0]
c_all0 = bytes.fromhex(c_all0_hex)

# guessコマンドを送って解答モード開始
p.sendline(b'guess')
p.recvuntil(b'challenge: ')

# CHALLENGEを算出して送信
chal = rev(bxor(c_chal, c_all0))
chal_hex = chal.hex()
p.sendline(chal_hex.encode())

# フラグを含む残りの受信データを表示
print(p.recvall().decode())
```
