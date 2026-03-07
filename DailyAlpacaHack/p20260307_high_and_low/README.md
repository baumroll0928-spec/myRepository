# high and low

## 問題

guess the high or low!
```py
import os
import secrets
import signal

class RNG:
    N = 624
    M = 397
    UPPER_MASK = 0x80000000
    LOWER_MASK = 0x7FFFFFFF

    def __init__(self):
        self.state = [secrets.randbits(32) for _ in range(self.N)]
        self.p = 0

    def next_value(self):
        p, q, r = self.p, (self.p+1) % self.N, (self.p + self.M) % self.N
        a = self.state[p] & self.UPPER_MASK
        b = self.state[q] & self.LOWER_MASK
        x = (a | b) ^ self.state[r]

        self.state[p] = x
        self.p = q

        y = ((x >> 11) | ((x << 21) & 0xFFFFF800)) ^ 0xDEADBEEF
        return y

signal.alarm(600)

rng = RNG()

money = rng.N
while True:
    print(f"money: {money}")
    if money < 0:
        print("bankrupt!")
        exit()
    if money > 1337:
        flag = os.environ.get("FLAG", "Alpaca{REDACTED}")
        print("rich man!")
        print(flag)
        exit()

    value = rng.next_value()
    print(f"value: {value}")

    choice = input("high or low? ")
    print(f"[{choice}]")

    next_value = rng.next_value()
    print(f"next: {next_value}")
    if  (choice == "h") == (value < next_value):
        print("you win")
        money += 1
    else:
        print("you lose")
        money -= 1
```

## 方針

受け取った値から乱数生成器の内部配列stateの内容を徐々に明らかにしていく。

## 解法

所持金624から始め、次の値が現在の値より大きいか大きくないかを予想し結果によってお金が+1/-1になるゲームを繰り返し、所持金を1338以上にするのがこの問題の目的です。

てきとーにやっていたら、初期金額の624の付近を行き来することになり、いつまでたっても終わりません。

戦略的に次の値を予測して積極的に当てにいく必要がありそうです。

この乱数生成器は、2つの内部状態変数pとstateをもっています。

pは0から始まりnext_value()が呼ばれるたびに1つずつ増えていくだけなので、容易に再現することができますが、やっかいなのはstateです。

stateは最初に32ビットの乱数で初期化された長さNの配列で、next_value()が呼び出されると、pやstateの一部から計算されるxをpの場所に書き込んだあと、xから計算されるyを次の値として返します。

stateのp,q,rの場所の値が全てわかれば、次に出てくる値を特定できますが、最初はランダムなのでわかりません。

なので、最初は様子見します。624から+1/-1で変遷するのでそう簡単には破産しないでしょう。

yを計算する方法を見てみます。
```py
y = ((x >> 11) | ((x << 21) & 0xFFFFF800)) ^ 0xDEADBEEF
```
xは最大32ビットなので、yはxの上位21ビットと下位11ビットを入れ替えたものに0xDEADBEEFをXORしたものになります。

よって、
```py
y ^= 0xDEADBEEF
x = (y >> 21) | ((y << 11) & 0xFFFFF800)
```
でyからxを逆算することができます。

このとき、state[p]にこのxが書き込まれたことを記録しておきます。

これをN回繰り返すと、pは0に戻り、stateは全て既知になります。こうなればもうこっちのものです。

### ソルバーを書いてみる

RNGクラスに、stateを書き換える関数set_state(y)を追加します。
```py
    def set_state(self, y:int):
        y ^= 0xDEADBEEF
        x = (y >> 21) | ((y << 11) & 0xFFFFF800)
        self.state[self.p] = x
        print(f"state[{self.p}] = {x}")
        self.p = (self.p + 1) % self.N
```

まずは観察フェーズです。

ループ１回につきnext_value()が２回呼び出されていて、次の値は解答を送ったあとにわかるので、stateの組み立て方に少し工夫が要りそうです。

```py
HOST = "34.170.146.252"
PORT = 6881
p = pwn.remote(HOST, PORT)

rng = RNG()
for i in range(rng.N // 2 + 1):
    data = p.recvuntil(b'low? ')
    d = data.decode().split()
    if b'next' in data:
        next = int(d[-10])
        rng.set_state(next)
    value = int(d[-4])
    rng.set_state(value)
    if i < rng.N // 2:
        p.sendline(b'h')
```

続いて攻略フェーズです。

内部状態を把握済みの乱数生成器を使ってnextを先読みし、大小を確実に当て続けていきます。
```py
while True:
    print("money:", int(d[-6]))
    next = rng.next_value()
    p.sendline(b'h' if value < next else b'l')
    
    data = p.recv(timeout=1)
    if b'rich' in data:
        print(data)
        break
    d = data.decode().split()

    value = rng.next_value()
```

## 別解

実はこの問題、乱数生成器の内部構造を全く理解しなくても解くことができます。

valueが$`2^{31}`$より小さい場合、次はそれよりも大きい可能性が高いですし、逆の場合もまたしかりです。

つまり、valueが$`2^{31}`$より小さい場合は"h"を、そうでない場合は"l"を投げ返し続けてあげるだけで、期待値的にmoneyが徐々に増えていき、いずれは目標値の1338にたどり着くことになります。

※具体的には、乱数が一様分布だと仮定すると、平均的に１ゲームあたり+0.5くらい稼ぐことができ、1428ゲームくらいでクリアできる計算になります。

```py
while True:
    data = p.recv(timeout=1)
    if b'rich' in data:
        print(data)
        break
    d = data.decode().split()
    money = int(d[-6])
    value = int(d[-4])
    print("money:", money)
    p.sendline(b'h' if value < (1 << 31) else b'l')
```
