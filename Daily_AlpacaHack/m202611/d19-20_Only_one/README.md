# Only one

## 問題

1文字だけ！

```c
command = input("$ ")[:1]
subprocess.run([command]).check_returncode()
print("FLAG: Alpaca{REDACTED}")
```

## 概要

たったの1文字で正常終了するLinuxのコマンドの入力を求められています。

一般的によく知られているコマンドで短いものと言えば`ls`などがありますが、2文字です。

以前出てきた`source`コマンドの短縮形`.`は1文字ですが、引数が必要です。

aliasを張って独自の短縮コマンドを作ることもできません。

さて、どうしましょうか？

## 方針

全部試す

## 解法

ASCII可視文字は`!`(0x21)～`~`(0x7e)の94個しかありません。

これらを全て試せば、どこかでフラグが出てくるはずです。

手動で試しても良いですが、面倒くさいので自動化します。

```py
from pwn import remote

PORT, HOST = "localhost", 1337

for cd in range(0x21, 0x7f):
    p = remote(PORT, HOST)
    p.sendlineafter(b'$ ', bytes([cd]))
    d = p.recvall(timeout=3)
    p.close()
    if b'Alpaca{' in d:
        ch = chr(cd)
        print(f"{cd = }")
        print(f"{ch = }")
        print(f"{d = }")
        break
else:
    print("Not found.")
```

ローカルのDockerでサーバーを起動してこれを実行すると正解のコマンドがわかるので、本番環境に接続して入力すればフラグを得ることができます。

※本番環境で上記のプログラムを回すのは時間もかかるし本番サーバーに負荷をかけてしまうのでお勧めしません。

## 補足

このコマンドは、ログインしているユーザーとその処理状況の一覧を表示してくれるコマンドのようです。

※socatによる接続はログインではないので、一覧は空(0件)になります。

ちなみに、94通りのうち正解は1つだけでした。
