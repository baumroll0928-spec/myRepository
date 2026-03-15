# flag.txt

## 問題

🦙 < フラグは flag.txt にあるパカ

## 概要

flag.txtをダウンロードしようとしたところ、サイズが8192ペタバイトとなっていて、とてもダウンロードしきれそうにありません。

## 方針

Pythonのrequestsモジュールを使って部分的にダウンロードしながらフラグの場所を探す

## 解法

curlコマンドに-rオプションを付けると部分的にダウンロードできるようです。

例えば、100～200バイトの部分を取るには
```sh
$curl -r 100-200 https://flag-txt.chal.alp4ca.com/flag.txt
.....................................................................................................
```
とします。

flag.txtの内容は
```
Flag is ....................Alpaca{REDACTED}!!!!!!!!!!!!!!!!!!!!
```
であるとserver.pyに書いてあります。"."がもっとたくさんある感じでしょうか。

それなら後ろから取ってみます。後ろから100バイト取るには
```sh
$curl -r -100 https://flag-txt.chal.alp4ca.com/flag.txt
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

あれ？これじゃダメなの？

そうか、"!"も"."と同じようにもっとたくさんあるんですね。

全体サイズを確認します。
```sh
$curl -I https://flag-txt.chal.alp4ca.com/flag.txt
HTTP/2 200
server: nginx/1.27.5
date: Sat, 14 Mar 2026 17:12:49 GMT
content-type: text/plain
content-length: 9223372036854775807
last-modified: Thu, 01 Jan 1970 00:00:00 GMT
etag: "0-7fffffffffffffff"
content-disposition: attachment; filename="flag.txt"
accept-ranges: bytes
```
全部で9223372036854775807バイトなのでその半分は4611686018427387903です。

中心から前後50バイトずつ取ってみます。
```sh
$curl -r 4611686018427387853-4611686018427387953 https://flag-txt.chal.alp4ca.com/flag.txt
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```
あれ？・・・あっ、"."の数と"!"の数が同じとは一言もいってませんでしたね。

フラグがある場所を探す必要がありそうです。さすがHard問題は一筋縄ではいきませんね。

幸い、フラグより前は（先頭の数文字を除いて）全て"."であり、フラグより後は全て"!"であることがわかっています。

よって、いま見ている場所がフラグより前なのか後なのかはすぐにわかるので、二分探索で絞り込んでいくことにします。

※探索範囲が$`2^{63}`$と膨大ですが、二分探索なので最多で63回以内には見つけることができます。

手動でやるのは大変なので、Pythonのrequestsモジュールを使って自動化してみました。

```py
import requests

URL = "https://flag-txt.chal.alp4ca.com/flag.txt"
TOTAL_SIZE = 9223372036854775807

# 探索する範囲を決める
low = 0
high = TOTAL_SIZE - 1

while low < high:
    # 探索範囲の真ん中を見る
    mid = (low + high) // 2
    print(f"{low=}, {mid=}, {high=}, size of range={high-low+1}")
    headers = {"Range": f"bytes={mid-50}-{mid+50}"}
    res = requests.get(URL, headers=headers)
    text = res.text
    print(text)
    if "Alpaca{" in text and "}" in text:
        # フラグがみつかったら終わり
        break
    if text[0] == '.':
        # フラグはもっと後にある→範囲を後半に絞る
        low = mid + 1
    else:
        # フラグはもっと前にある→範囲を前半に絞る
        high = mid - 1
```
