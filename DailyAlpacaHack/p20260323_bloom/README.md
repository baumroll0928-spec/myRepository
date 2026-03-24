# bloom

## 問題

年だけまたとにかくとった 鳥籠の中の鳥と変わらない 特に得意なこと無かったが とっくに夢は出来てんだ
```py
import os
import secrets

# it is so secure randint function!!
def secure_randint(a, b):
    return secrets.randbelow(b - a + 1) + a

FLAG = os.getenv("FLAG", "Alpaca{fake_flag_for_testing}").encode()


def xor(a, b):
    return bytes([x ^ y for x, y in zip(a, b)])


def encrypt(plain):
    key = bytes([secure_randint(1, 255) for _ in range(len(plain))])
    cipher = xor(plain, key)
    return cipher


while True:
    input("Press Enter to get the encrypted flag...")
    cipher = encrypt(FLAG)
    print(f"Encrypted flag: {cipher.hex()}")
```

## 概要

入力はありません。

Enterを押すたびに、1～255の乱数をフラグと同じ長さだけ並べたkeyを生成し、そのkeyとフラグとXORをとった暗号文を繰り返し吐き出し続けます。

keyは毎回変わる乱数列なので、特定するのは無理そうです。

## 方針

keyとXORをとることでフラグの全ての文字が必ず変化することに注目する。

## 解法

この問題におけるkeyの乱数の範囲は1～255であり、0がありません。

0とXORをとると変化しませんが、この問題では1～255のいずれかとXORをとるため、必ず変化し、かつ、0～255の中で元の値以外の全ての値を取りうることになります。

これは数回の観測ではわかりませんが、何百回、何千回と観測するうちに、暗号文の中の位置ごとに出てこない値が絞り込まれていきます。

出てこない値が１種類まで絞り込むことができれば、その出てこなかった値がフラグのその位置の文字コードということになります。

これを全て結合すれば、フラグになるのではないでしょうか。

```py
from pwn import *

# 接続
p = remote("34.170.146.252", 10790)
# 最初は読み捨て
p.recvuntil(b'flag...')
cnt = 0
while True:
    # 暗号文を取得する
    p.send(b'\n')
    d = p.recvuntil(b'flag...').decode().split()
    cipher = bytes.fromhex(d[-8])
    # 初回はテーブルとフラグを初期化する
    if cnt == 0:
        table = [{x for x in range(256)} for _ in cipher]
        flag_array = [ord('?')] * len(cipher)
    cnt += 1
    for i in range(len(cipher)):
        # 現れた値をテーブルから削除する
        table[i].discard(cipher[i])
        # 残り１種類になったらフラグにセットする
        if len(table[i]) == 1:
            flag_array[i] = table[i].pop()
    # 残数と暫定フラグを表示する
    print(','.join([str(len(table[i])) for i in range(len(cipher))]))
    print(bytes(flag_array).decode())
    # フラグが全て決まったら終わり
    if all(len(table[i])==0 for i in range(len(cipher))):
        break
print(f"{cnt = }")
```

ちなみに私が実行してみたところ、2259回かかりました。
