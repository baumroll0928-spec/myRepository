
# 1️⃣

## 問題

使えるのは1文字だけ
```py
import os
os.system(f"{input("> ")[:1]} /app/flag.txt")
```

## 概要

コマンド
```
(ユーザー入力の１文字) /app/flag.txt
```
が実行されます。

以前、`cat3`という過去問で
```
cat (ユーザー入力の３文字)
```
というのがありましたが、今回は１文字です。

全く意味が分かりません。どうすればいいんですか？（半ギレ）

## 解法

`cat`としたいところですが３文字必要なので全然枠が足りません。

たったの１文字ということはおそらく`A`などの普通の文字ではなく何らかの記号文字なのではないかと考えました。

```
> $
sh: 1: $: not found
```
```
> |
sh: 1: Syntax error: "|" unexpected
```
```
> \
sh: 1:  /app/flag.txt: not found
```
ちょっと近づいた気がします（？）
```
> ;
sh: 1: Syntax error: ";" unexpected
```
```
> >
sh: 1: cannot create /app/flag.txt: Permission denied
```
```
> /
sh: 1: /: Permission denied
```
```
> .
sh: 1: /app/flag.txt: Alpaca{REDACTED}: not found
```
出ました！

意味は全然分かりませんが、とりあえずフラグはゲットできました。

調べてみると、Linuxのシェルにおいて`.`は`source`コマンドの短縮形のようです。

これは、ファイルの中身をそのシェルでコマンドとして実行するコマンドです。

試しに`mycmd`というファイルに`ls`と書き込んで`source mycmd`や`$ . mycmd`を実行してみると、この`ls`が実行されることがわかります。

このとき`./mycnd`として実行するには`mycmd`ファイルに実行権限`+x`が必要ですが、`source mycmd`で実行する場合は必要ないようです。

今回の問題では、ファイル`/app/flag.txt`にフラグ`Alpaca{...}`が書かれています。

ここで`$ . /app/flag.txt`を実行すると、`Alpaca{...}`をコマンドとして実行しようとするので、`Alpaca{...}`なんていうコマンドは無いよ、というエラーメッセージを吐いてくれるというわけです。
