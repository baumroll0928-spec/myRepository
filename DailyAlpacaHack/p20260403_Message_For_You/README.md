# Message For You

## 問題

私からの隠れたメッセージを探してください
```py
from flask import Flask, session
import os
import secrets 

FLAG = os.environ.get("FLAG", "Alpaca{**REDACTED**}")

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

MESSAGE = f"""
Roses are red,
Violets are blue,
I've hidden a flag
In a session for you: {FLAG}
""".strip()

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Message for You!</title>
</head>
<body>
    <p>I've got a message for you.</p>
    <p>It's hidden somewhere around here...</p>
</body>
</html>
""".strip()

@app.get("/")
def index():
    session["message"] = MESSAGE
    return HTML

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
```

## 概要

フラグを含む隠れたメッセージ`MESSAGE`は、
```PY
session["message"] = MESSAGE
```
によってセッションに入れられているだけで、明示的にどこかに出力はしていないように見えます。

どうやってこの隠れたメッセージを取り出せばいいのでしょうか？

## 方針

Flaskのセッションの持ち方に注目する。

## 解法

PHPとかで考えると、セッションの内容はサーバー側で保持し、セッションIDを介してやり取りされるため、セッションの内容をリークなしに取り出すのは不可能に思えます。

しかし、Flaskのsessionはクライアント側のクッキーに保持されるようです。

実際、サイトにアクセスし、Chromeの開発者ツールでクッキーを覗いてみると、
```
name: session
value: .eJwlyzELwjAQhuG_cmRxcagUEbqJk6uDk3Cc5msNxlzJGaWU_ncjbi8PvLN7wkwGuM6d1GAkGZTh15d0Dhrx-ss1FlQ6rt6ge_AeiYT6KEO1X9bTgibqNdOkpaN9HOUm80GbxwbGklu2D9odS_K81QrgqSmLW77kUS59.ac6FGg.roFB-3kVF749Z7JHoM0HVkFU3ho
```
が記録されていました。

これは、
```
.[データ部].[タイムスタンプ].[署名]
```
のようです。

データ部は、JSONデータをzlibで圧縮し、urlsafeなBase64でエンコードしたものです。

よって、隠れたメッセージを得るにはこの逆手順で変換します。

```py
import base64, zlib

cookie = ".eJwlyzELwjAQhuG_c...略...U3ho"
data = cookie[1:]
data = data[:data.find('.')]
decoded = base64.urlsafe_b64decode(data)
print(zlib.decompress(decoded).decode())
```
これを実行すると、
```
{"message":"Roses are red,\nViolets are blue,\nI've hidden a flag\nIn a session for you: Alpaca{********************************}"}
```
のようにフラグが表示されます。

## その他

```
Roses are red,    # バラは赤く
Violets are blue, # スミレは青く
```
の部分、調べてみると、マザーグースの`Roses are red`の一部のようです。

原文ではさらに次のように続きます。
```
Sugar is sweet    # 砂糖は甘く
And so are you.   # 君は優しい
```
フラグはこの部分をもじっていたのですね。

問題の核心部分にもかかるところがあり、上手いと思いました。
