# magic number

## 問題

Can you find the hidden gem?
```py
import os

code = """
magic = /*code*/
if magic == 2508766360454420426020902195377847924746:
    print("/*flag*/")
else:
    print("bye")
"""

print("Show me your magic 🪄 ")
payload = input()
if len(payload) > 20:
    print("too long")
    exit(1)

compiled = code.replace("/*code*/", payload).replace("/*flag*/", os.environ.get("FLAG", "DUMMY_FLAG"))

exec(compiled, {"__builtins__": {"print": print}}, {})
```

## 方針

2つのreplaceの順番を利用して直接フラグを表示させる。

## 解法

文字列変数codeの一部を差し替えたcompiledをPythonのコードとして実行しています。

コードでは、payloadと40桁の巨大な整数を比較し同じならフラグを表示するようになっているようです。

ただし、payloadにあたる入力は20文字以下でないと弾かれてしまいます。

普通に考えたらこの問題、例えば
```
2**130+3**82
```
のように短い文字でターゲットの巨大な整数を作る問題のように思えます。

しかし、ちょうどいい計算式は私はみつけられませんでした。

ここでちょっとメタな視点でこの問題を見てみます。

なんでこんな回りくどいことをしているんだろう？

この問題が単純にターゲットを作らせる数的パズル問題だったら、もっとシンプルな書き方があるはずです。

わざわざこのようにしているのは、何か別の意味があるのではないかと考えました。

そうすると関係がありそうなのはコレでしょうか。
```py
compiled = code.replace("/*code*/", payload).replace("/*flag*/", os.environ.get("FLAG", "DUMMY_FLAG"))
```
これを見ると、codeの中の"/\*code\*/"をpayloadに置き換えたあと、さらに"/\*flag\*/"をフラグに置き換えています。

よって、payloadの中に"/\*flag\*/"が含まれる場合、それもフラグに置き換えられてしまうことになります。

それなら、入力はもう
```
/*flag*/
```
これでいいのではないでしょうか？

これなら、DUMY_FLAGは定義されていないとか、Alpaca{...}の{で構文エラーを起こすとかでエラーメッセージの中にフラグが現れるはずです。

ローカル環境で試します。
```
nc localhost 1337
Show me your magic 🪄
/*flag*/
```
あれ、何も表示されない？もしかしてエラーメッセージが握られているのかな？

Dockerfileを見てみると、
```
CMD ["socat", "-T30", "tcp-listen:1337,fork,reuseaddr", "exec:'python server.py'"]
```
案の定最後に
```
,stderr
```
がついていませんでした。

それなら次に考えられるのは、
```
print("/*flag*/")
```
でしょうか。

こうすると、
```py
magic = print("Alpaca{...}")
```
のように変換されることから、無事フラグを表示することができました。

※Pythonのprint関数はNoneを返すので、変数に代入してもエラーになりません。

## その他

こういうミスリードなパズル問題は私は大好きです。

でも実際のところ、累乗とかをうまく組み合せて解く方法もあるんでしょうか？

magic numberというからには何か意味がありそうな気がしますが。
