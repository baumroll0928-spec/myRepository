今回も面白い問題でしたね。

Hard問題でしたが、ひらめき要素が強めのためかわりと簡単に解けました。

# pyjs

## 問題
```py
import subprocess

code = input("Enter your code: ")

res1 = subprocess.run(["runuser", "-u", "nobody", "--", "python3", "-c", code], capture_output=True)
assert res1.returncode == 0 and res1.stdout.strip() == b"I LOVE ALPACA"

res2 = subprocess.run(["runuser", "-u", "nobody", "--", "node", "-e", code], capture_output=True)
assert res2.returncode == 0 and res2.stdout.strip() == b"I LOVE SECCON"

print("Wow... Alpaca{REDACTED}")
```

## 方針
両言語の // の解釈の違いを利用する。

## 解法
配布のソースを見ると、同じコードでPythonとNode(Javascript)で異なる文字列を出力し、エラーなく終了するようなコードを入力することが求められているようです。

出力すべき文字列が違うだけでなく、PythonとNodeでは標準出力関数も違うし、他の言語の関数を実行しようとするとエラーになってしまいます。どうしましょう？

さて、// はPythonでは整数商の演算子、Nodeでは行コメントを意味します。

したがって、例えば、
```
1 // 1; print("I LOVE ALPACA")
```
とすると、Python視点では
```
1 // 1
print("I LOVE ALPACA")
```
となり、Node視点だと
```
1
```
となるので、Pythonでは正しく出力しつつNodeではエラーなしに終わることができます。

※Pythonで複数の文をセミコロンで区切ると1行にまとめて書くことができます。

あとはNodeの出力ですが、以前free-commentという問題でも扱われたように、\rを使って改行し、2行目で出力することにします。
```
1 // 1; print("I LOVE ALPACA")
console.log("I LOVE SECCON")
```
しかし、これだと2行目のconsole.logによってPythonでエラーになってしまいます。

Nodeには1 # 1のような都合のいい書き方はありませんし、/* # */のようにしようにもPythonは/*を解釈することができません。

なので、指定文字列を出力し用済みのPythonは1行目で終わらせてしまいましょう。
```
1 // 1; print("I LOVE ALPACA"); exit(0)
consoloe.log("I LOVE SECCON")
```
※PythonはC言語などと違って逐次解釈しながら実行するので、解釈できないコードがあっても実際にそこにたどり着かなければエラーになりません。

これでいけるか試してみます。配布のソースの
```py
code = input("Enter your code: ")
```
のところを
```py
code = '1 // 1; print("I LOVE ALPACA"); exit(0)\rconsole.log("I LOVE SECCON")'
```
に書き換えて実行してみます。

※Windows環境ではそのままでは実行できないようです。Linux系環境で実行しましょう。（python3にsudoを付ける必要があるかも？）
```
Wow... Alpaca{REDACTED}
```
ちゃんと出ました！

あとは、このペイロードをファイルで作成して
```
nc 34.170.146.252 46654 < payload.bin
```
としてもいいし、下記のソルバーを走らせてもいいです。
```py
import pwn

payload = '1 // 1; print("I LOVE ALPACA"); exit(0)\rconsole.log("I LOVE SECCON")'

HOST = "34.170.146.252"
PORT = 46654
p = pwn.remote(HOST, PORT)
p.recvuntil(b'code: ')
p.sendline(payload.encode())
print(p.recvall())
```

## その他

こういうパズル的な問題も面白いですね。
