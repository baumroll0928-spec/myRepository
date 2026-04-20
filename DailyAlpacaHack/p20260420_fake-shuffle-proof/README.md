# fake-shuffle-proof

## 問題

証明を手に入れて、証明を破壊して
```py
CARDS = {
    0: "A♠",
    1: "A♥",
    2: "K♠",
    3: "K♥",
}
KEY = secrets.token_hex(16)
FLAG = os.getenv("FLAG", "Alpaca{DUMMY}")

def is_diff_color(a, b):
    return (a % 2) != (b % 2)

def rank_only_commit(a, b):
    ra = a // 2
    rb = b // 2
    x, y = sorted([ra, rb])
    return hashlib.sha256(f"{x}|{y}|{KEY}".encode()).hexdigest()

def main():
    while True:
        print(
            "\n=== Fake Shuffle Proof ===\n\n"
            "Cards:\n"
            "0 = A♠\n"
            "1 = A♥\n"
            "2 = K♠\n"
            "3 = K♥\n\n"
            "1) issue\n"
            "2) verify\n"
            "3) exit\n"
        )
        cmd = input("> ")

        if cmd == "1":
            a = int(input("left: "))
            b = int(input("right: "))

            if a not in CARDS or b not in CARDS or a == b:
                print("[-] invalid cards")
                continue

            if not is_diff_color(a, b):
                print("[-] only different-color pairs allowed")
                continue

            proof = rank_only_commit(a, b)
            print(f"[+] proof = {proof}")

        elif cmd == "2":
            a = int(input("left: "))
            b = int(input("right: "))
            proof = input("proof: ")

            if a not in CARDS or b not in CARDS or a == b:
                print("[-] invalid cards")
                continue

            expected = rank_only_commit(a, b)
            if proof != expected:
                print("[-] invalid proof")
                continue

            if not is_diff_color(a, b):
                print(f"[+] {FLAG}")
                break

            print("[+] valid proof")

        elif cmd == "3":
            print("bye")
            break

        else:
            print("[-] unknown option")
```

## 概要

この問題は、発行(issue)フェーズと検証(verify)フェーズに分かれています。

発行フェーズでは、左右２枚のカードを選択すると、これらのカードからSHA256ハッシュ値が証明書（？）として発行されます。

ただし、存在しないカードや同じカード、色が同じカードを選択することはできません。

検証フェーズでは、左右２枚のカードを選択し、これらのカードから発行されるであろう証明書を入力します。

ここでも、存在しないカードや同じカードは選択できません。

入力された証明書と実際の証明書を比較して、正しい証明書であることが確認できた場合、２枚のカードの色が同じであればフラグが表示されます。

ここまでまとめると、発行フェーズでは同じ色のカードの選択が許されないのに、検証フェーズでは同じ色のカードの証明書が求められるということです。

証明書の発行時にランダムで不明な`KEY`をソルトとしてくっつけているので、勝手に証明書を発行することは事実上不可能です。

どうすれば発行されない証明書を入手できるのでしょうか？

## 方針

証明書にカードの色の情報が含まれていないことに注目する。

## 解法

証明書を発行する`rank_only_commit`関数を見てみると、その関数名のとおりカードの色を無視してランク（A,K）の情報だけから発行しています。

したがって、
```
left: 0  # A♠ color=0, rank=0
right: 3 # K♥ color=1, rank=1
```
の場合と、
```
left: 1  # A♥ color=1, rank=0
right: 3 # K♥ color=1, rank=1
```
の場合では、全く同じ証明書が発行されます。

そして、前者は違う色、後者は同じ色です。

よって、発行フェーズで前者のペアを選択して証明書を入手し、検証フェーズで後者のペアを選択して入手した証明書を入力すれば、フラグを得ることができます。

```py
import pwn

#HOST, PORT = "localhost", 1337
HOST, PORT = "34.170.146.252", 17391
p = pwn.remote(HOST, PORT)

p.sendlineafter(b'> ', b'1')
p.sendlineafter(b'left: ', b'0')
p.sendlineafter(b'right: ', b'3')

d = p.sendlineafter(b'> ', b'2')
h = d.split()[3]
print(f"{h = }")
p.sendlineafter(b'left: ', b'1')
p.sendlineafter(b'right: ', b'3')
p.sendlineafter(b'proof: ', h)

print(p.recvall(timeout=10).decode())
```
