Padding Oracle攻撃という言葉は聞いたことがあったものの、まともに挑むのは今回が初めてなbaumroll1234です。

Padding Oracle攻撃についてはWeb検索すればいくらでも出てくると思うので、ここでは初心者の私がつまづいたところ、難しかったところを中心にまとめていきます。

# One Byte Padding Oracle Attack
## 問題
Padding Oracle Attack は各ブロックの後ろの1バイトから徐々に復元してく手法です。 まずは1ブロック目の復元に挑戦してみましょう。
```py
FLAG = os.getenv("FLAG", "Alpaca{dummy}")
key = secrets.token_bytes(16)

def encrypt(plaintext):
    cipher = AES.new(key=key, mode=AES.MODE_CBC)
    encrypted_flag = cipher.encrypt(pad(plaintext.encode(), 16))
    return cipher.iv + encrypted_flag

def decrypt(iv, ciphertext):
    cipher = AES.new(key=key, mode=AES.MODE_CBC, iv=iv)
    a = cipher.decrypt(ciphertext)
    try:
        unpad(a,16)
        return True
    except:
        return False

plaintext = ""
for c in FLAG:
    plaintext += "?"*15 + c

iv_ciphertext = encrypt(plaintext)
print(f"iv_ciphertext={iv_ciphertext.hex()}")

while True:
    iv_ciphertext = bytes.fromhex(input('iv+ciphertext> '))
    iv, ciphertext = iv_ciphertext[:16], iv_ciphertext[16:]
    print(decrypt(iv, ciphertext))
```

## 方針
問題のタイトル通り、Padding Oracle攻撃を使う。

## 解法

今回の問題は、各ブロックの最後の文字だけ復号すればいいので、Padding Oracleの簡易版で解くことができます。

### CBCモードについて

まずAESのCBCモードについておさらいしましょう。

CBCは、前のブロックの暗号文（最初はIV）と平文のXORをとってから暗号化する方式です。

* 平文ブロック：$`P_{1} ～ P_{N}`$
* 暗号文ブロック：$`C_{1} ～ C_{N}`$
* IV: $`C_{0}`$

とします。そうすると、

$`C_{N} = Enc(C_{N-1} \oplus P_{N})`$

となります。（Enc(X)はXを暗号化したもの）

この等式の両辺を復号すると、

$`Dec(C_{N}) = C_{N-1} \oplus P_{N}`$

となるので、（Dec(Y)はYを復号したもの）

$`P_{N} = C_{N-1} \oplus Dec(C_{N})`$

となります。これにより暗号文から平文が復元できます。（keyがあれば。）

### Padding Oracle攻撃について

オラクル攻撃は、入力に対してわずかな情報しか返してくれないシステムに繰り返し入力を与えて情報を抜き取る手法です。Blind SQLiとかもそうですよね。

今回の問題では、keyはサーバーが握っているのでわからず、そのkeyで復号した結果のパディングが正しいか正しくないかだけしか教えてくれません。

最初にIVと暗号文が提示されるので、それをそのまま投げ返せば当然Trueが返ってきますが、それでは平文は全くわかりません。

ですが、回数制限はないので、同じkeyに対して何度でも復号を試みることができますので、それを利用します。

さて、PKCS#7のパディングが正しい状態とは、
```
? ? ? ? ? ? ? ? ? ? ? ? ? ? ? \x01
```
とか、
```
? ? ? ? ? ? ? ? ? ? \x06 \x06 \x06 \x06 \x06 \x06
```
のような状態ですよね。

先ほど見たように、

$`P_{N} = C_{N-1} \oplus Dec(C_{N})`$

となりますが、この$`C_{N-1}`$は自由に変えることができます。

ここで、ブロックの最後の16バイト目だけに注目してみます。（ブロックXの16バイト目をX[15]と書くことにします。）

そうすると、$`C_{N-1}[15]`$を0x00～0xffの全256通りで試すことで、$`P_{N}[15]`$が0x01になるように調整できることになります。

※$`C_{N-1}`$を書き換えると当然それ以前の平文は壊れてしまいますが、ここではパディングが正しいかどうかだけが重要なので、前の方の平文が壊れても全く問題ありません。

$`P_{N}[15]`$が0x01になったとき、正しいパディングとなるため、その状態で投げるとTrueが返ってきます。

そのときの$`C_{N-1}[15]`$をiとします。そうすると、

$`Dec(C_{N})[15] = i \oplus 0x01 = C_{N-1}[15] \oplus P_{N}[15]`$

が成立するので、

$`P_{N}[15] = i \oplus 0x01 \oplus C_{N-1}[15]`$

によって、$`P_{N}[15]`$すなわち最後のブロックの最後のバイトが求まります。

同じことを、最後の16バイトを削りながら繰り返せば、他のブロックの最後のバイトも求めることができます。

※この問題では平文の性質上長さが必ず16の倍数なので、パディングは必ず\x10 \x10 ... \x10となり、最後の16バイトはいきなり捨てることができます。

### 解いてみる

しくみが分かったところで、ソルバーを自分でイチから実装しても良いのですが、せっかく添付のREADME.mdにほぼ完成済みのヒントが示されているので、これを利用することにします。
```py
iv_ciphertext = iv_ciphertext[:-16]

flag = ""
while len(iv_ciphertext) > 16:
    for i in range(256):
        b = change_byte(iv_ciphertext, len(iv_ciphertext)-17, i)
        if send(sc, b):
            a = iv_ciphertext[len(iv_ciphertext)-17]
            flag += "??????????" # TODO: try change this line!
            break
    iv_ciphertext = iv_ciphertext[:-16]

print(''.join(reversed(flag)))
```
「この行を変えてみよう！」と書いてあります。

このプログラムを先ほどの説明と照らし合わせると、

* i: 書き換えを試みる値（0～255）
* b: $`C_{N-1}`$をiで書き換えたブロック
* a: 書き換える前のもとの$`C_{N-1}[15]`$

であり、これを
```py
    iv_ciphertext = iv_ciphertext[:-16]
```
で末尾の16バイトを削りながら繰り返していることがわかります。

よって、"??????????"のところに入るのは
```py
bytes([i ^ 1 ^ a]).decode()
```
となります。

この方法だとフラグの文字が後ろから順に求まるので、
```py
print(''.join(reversed(flag)))
```
で逆転して元通りにして表示しています。

### 実行してみる

ローカルでdocker compose upして実行してみると、
```sh
[x] Opening connection to localhost on port 2468
[x] Opening connection to localhost on port 2468: Trying ::1
[+] Opening connection to localhost on port 2468: Done
Alpaca{REDACTED}
[*] Closed connection to localhost port 2468
```
すぐにフラグが出ました。

次に本番環境で実行してみると、なかなかフラグが出てきません。ちゃんと動いているか不安になります。

確認するため、経過を表示してみます。
```py
while len(iv_ciphertext) > 16:
    print(f"{flag = }\n***")
    for i in range(256):
        print(f"\033[F\033[K{i = }")
        b = change_byte(iv_ciphertext, len(iv_ciphertext)-17, i)
```
すると、ちゃんと動いていることがわかりました。ただ時間がかかっていただけのようです。

※先週のDancing Cursorで出てきたANSIエスケープシーケンスを使ってみました。
```
[x] Opening connection to 34.170.146.252 on port 60240
[x] Opening connection to 34.170.146.252 on port 60240: Trying 34.170.146.252
[+] Opening connection to 34.170.146.252 on port 60240: Done
flag = ''
i = 57
flag = '}'
（略）
flag = '}*****{acapl'
i = 20
Alpaca{*****}
[*] Closed connection to 34.170.146.252 port 60240
```

## その他

今後、ブロックの1～15バイト目も復号する問題が出題されるかもしれませんね。

こちらについては今あまり詳しく書くと、もし本当に出題されたときにネタバレになってアルパカから強烈なキックを浴びることになるといけないので、やめておきます。
