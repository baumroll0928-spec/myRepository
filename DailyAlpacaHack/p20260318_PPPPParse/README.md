# PPPPParse

## 問題

Parse! Parse! Parse! Parse! Parse!

```js
(async () => {
  const input = await rl.question("> ");
  if (input.includes("\\\\")) return "Invalid";

  const ans = JSON.parse(JSON.parse(JSON.parse(JSON.parse(JSON.parse(input)))));
  if (ans === "42") {
    return process.env.FLAG;
  } else {
    return "Failed";
  }
})()
  .then(console.log)
  .finally(() => rl.close());
```

## 概要

JSONパースを繰り返し５回行ったときに文字列型の`42`になるような文字列の入力が求められているようです。

チェック時の比較は`==`ではなく`===`が用いられているので、型の一致まで求められています。

よって、単に`42`や`"42"`と入力しただけでは、数値型の`42`になってしまうので、`Failed`になってしまいます。

また、
```js
  if (input.includes("\\\\")) return "Invalid";
```
によって連続する`\`を含む入力は弾かれてしまいます。

どうすれば入力チェックを回避しつつ５回のパース後に文字列型の`42`にすることができるのでしょうか？

## 方針

`\`を使ったエスケープを利用する。

## 解法

５回目のパース後に
```
100
```
にするためには、４回目のパース後に
```
"100"
```
になるようにする必要があります。

ここで、JSONの文字列で一部の文字を`\`を使ってエスケープできる仕組みを利用します。
```js
console.log(JSON.parse('"\\"abc\\""')); // "\"abc\"" -> "abc"
console.log(JSON.parse('"C:\\\\Windows"')); // "C:\\Windows" -> C:\Windows
```
先ほどの`"100"`の中の`"`をエスケープして`"`で囲んであげると、
```
"\"100\""
```
となり、これが３回目のパース後の形となります。ここまでは順調です。

しかし、ここで問題が起こります。

同じように`\`と`"`をエスケープして`"`で囲むと、
```
"\"\\\"100\\\"\""
```
となってしまい、禁止文字列の`\\`を含んでしまいます。

そこで調べてみると、JSONの文字列では`\uXXXX`の形のUnicodeエスケープが使えることがわかりました。
```js
console.log(JSON.parse("\\u3042")); // "\u3042" -> あ
```

`\`のコードは005cです。

よって、`\`をエスケープするときに`\\`ではなく`\u005c`にすればいいのではないでしょうか。
```
"\"\u005c\"100\u005c\"\""
```
これなら`\\`は現れません。

あと２回手動で変換するのは面倒くさいし間違いのもとなので、プログラムで作成しました。

```py
txt = '42'
for _ in range(5):
    txt = txt.replace('\\', '\\u005c')
    txt = txt.replace('"', '\\"')
    txt = '"' + txt + '"'
print(txt)
```
