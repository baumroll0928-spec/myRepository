# settable counter

## はじめに

久しぶりに新作を出題させていただきましたbaumroll1234です、こんばんは。

デビュー作の「Vending Machine」の公開からもう半年以上がたちますが、問題を解くだけでなく作りたいという欲はまだまだ収まりません。

さて、今回はCryptoジャンルのAESに関する問題です。

AESのCTRモードを使った問題は、Daily AlpacaHackでまだ見たことがなかったので、作ってみました。

※uminekoさんの「シリーズシエラ」は前から気になっていたんですが、ついに私も書いてもらえることに！言い回しがかっこよすぎて思わず3回読んじゃいました（笑）

## 問題

フラグの暗号化のときに使ったカウンター以外であれば、自由にセットすることができます。

```py
FLAG = os.getenv("flag", "Alpaca{*** dummy ***}").encode()

key = secrets.token_bytes(16)
nonce = secrets.token_bytes(8)
cipher = AES.new(key, AES.MODE_CTR, nonce=nonce)

enc_flag = cipher.encrypt(FLAG)
print(f"encrypted flag = {enc_flag.hex()}")

print("- menu -")
print("1: encrypt")
print("2: set counter")
print("0: exit")

while True:
    select = input("select> ")
    try:
        if select == "1":
            # encrypt
            plain = bytes.fromhex(input("plaintext(hex)> "))
            enc = cipher.encrypt(plain)
            print(f"encrypted text = {enc.hex()}")

        elif select == "2":
            # set counter
            cnt = int(input("counter(dec)> "))
            if cnt <= (len(FLAG) - 1) // 16:
                print("Invalid counter value.")
            else:
                cipher = AES.new(key, AES.MODE_CTR, nonce=nonce, initial_value=cnt)
                print("Counter has been set.")

    except:
        print("Error.")
```

## 概要

最初に、フラグをAESのCTRモードで暗号化した暗号文が16進数で提示されます。

その後、次の2つの中から1つを選んで満足できるまで何回でも繰り返すことができます。

- 1: 平文を16進数で入力し、それを同じ暗号器で暗号化した暗号文を得る。
- 2: 暗号器のcounterを任意の値に変更する。（ただし最初の暗号化で使用済みのものはダメ。）

keyやnonceはわかりませんが、暗号化されたフラグを復号するにはどうすればいいのでしょうか？

## 方針

counterがオーバーフローして0に戻る性質を利用する。

## AES-CTRについて

AESは、共通鍵暗号方式（暗号化と復号に同じ鍵を使用する暗号化方式）のひとつです。

原則16バイトのブロックの単位で暗号化、復号を行います。

CTRはAESのモードの一つで、次のような処理によってストリーム暗号のような暗号化が行われます。

- key（16,24,32バイトのいずれか）を用意する。
- nonceは自動的に生成されるが指定することもできる。
- nonceとcounter（原則0から始まるが初期値の設定も可能）を結合した16バイトをkeyで暗号化し、16バイト分のキーストリームを生成する。
- 平文とキーストリームのXORをとって暗号化する。
- counterを+1しながら繰り返す。

キーストリームとXORをとるため、暗号化と復号が同じ手順になるという特徴があります。

また、16バイトごとにcounterが変わるため、CBCモード等と同様、平文ブロックが同じでも異なる暗号文ブロックに暗号化されます。

しかし、CBCモード等と違い、平文の長さが16バイトの倍数でなくてもよく、暗号化前にパディングする必要がありません。

※平文に16バイトに満たない半端な部分がある場合、例えば28バイトの場合は余った4バイトのキーストリームは捨てられることなく次に持ち越されます。

## 解法

同じkey, nonce, counterのとき、同じキーストリームが生成されます。

ちょっと実験してみましょう。
```
select> 2
counter(dec)> 10
Counter has been set.
select> 1
plaintext(hex)> 00112233445566778899
encrypted text = 94d555542d88a11b1793
select> 1
plaintext(hex)> aabbccddeeff  
encrypted text = 38bf4f352f15
select> 2
counter(dec)> 10
Counter has been set.
select> 1
plaintext(hex)> 00112233445566778899aabbccddeeff
encrypted text = 94d555542d88a11b179338bf4f352f15
```

counterに同じ10をセットした後に同じ平文を投げることで、同じ暗号化結果が返ってきていることから、同じキーストリームが生成されていることがわかります。

そして、暗号化と復号は同じなので、もしcounterを0に戻すことができたとしたら、その状態で暗号化フラグを暗号化してあげれば、復号されてフラグの平文を得ることができるはずです。

```
select> 2
counter(dec)> 10
Counter has been set.
select> 1               
plaintext(hex)> 0123456789abcdef
encrypted text = f6a49593d4cb7f04
select> 2
counter(dec)> 10
Counter has been set.
select> 1
plaintext(hex)> f6a49593d4cb7f04
encrypted text = 0123456789abcdef
```

※それか、暗号化フラグの桁数と同じ個数の0を平文として送ってキーストリームを取得し、これを使って暗号化フラグを復号しても良いですね。

しかし、最初の暗号化で使われたcounterの値である0とか1とかは入力チェックで弾かれてしまいますが、どうしましょう？

ここで、counterが8バイトで表されていることに注目します。（※nonceとcounterは必ずしも8バイト+8バイトである必要はありませんが、このサイズがバランスが良いことから使われることが多いようで、この問題でもそうしてあります。なお、nonceを指定しない自動生成の場合もこのサイズになります。）

8バイトなので $`0 ～ 2^{64}-1`$ までしか表すことができず、 $`2^{64}`$ に達するとオーバーフローして0に戻ってしまうのです。

本来ここまでcounterを使い尽くすことは現実的にはありえませんが、今回の問題ではcounterを自由に設定できるので、意図的にそのような状態にすることが可能になっています。

しかし、直接 $`2^{64}`$ をセットしようとすると、
```
ValueError: Initial counter value is too large
```
という例外（エラー）が発生してしまいます。（※この問題のプログラムでは例外がtry-exceptで握りつぶされているのでこのエラーメッセージは表示されません。）

これを回避するために、 $`2^{64}-1`$ をセットした後、キーストリームを16バイト分消費してから、改めて暗号文を送ることにします。

実験してみましょう。フラグは既知のダミーフラグ`Alpaca{*** dummy ***}`の状態です。
```
encrypted flag = 9f0915cd8db3cd38c6686c31721b74ee1c854d00b7
- menu -
1: encrypt
2: set counter
0: exit
select> 2
counter(dec)> 18446744073709551615
Counter has been set.
select> 1
plaintext(hex)> 00000000000000000000000000000000
encrypted text = 0aa6ce260e5a5b5f067989d098c4dddd
select> 1                                         
plaintext(hex)> 416c706163617b2a2a2a2064756d6d79202a2a2a7d
encrypted text = 9f0915cd8db3cd38c6686c31721b74ee1c854d00b7
```

`18446744073709551615`は$`2^{64}-1`$、`416c706163617b2a2a2a2064756d6d79202a2a2a7d`は`Alpaca{*** dummy ***}`を16進数化したものです。

これにより、最初の暗号文と同じ結果を得ることができ、最初の暗号化時と同じキーストリームを生成できたことがわかります。

この要領で、本番環境で得られた暗号文を入力し、結果の16進数列を[CyberChef](https://gchq.github.io/CyberChef/)とかで文字列に戻してあげれば、フラグを得ることができます。

## ソルバー

暗号文を直接送る場合
```py
from pwn import remote

HOST, PORT = "localhost", 1337
# HOST, PORT = "34.170.146.252", 26148
p = remote(HOST, PORT)

p.recvuntil(b'flag = ')
enc_flag_hex = p.recvline().strip()
print(f"{enc_flag_hex = }")
p.sendlineafter(b'> ', b'2')
p.sendlineafter(b'> ', str(2**64 - 1).encode())
p.sendlineafter(b'> ', b'1')
p.sendlineafter(b'> ', b'00' * 16)
p.sendlineafter(b'> ', b'1')
p.sendlineafter(b'> ', enc_flag_hex)
p.recvuntil(b'text = ')
flag_hex = p.recvline().strip()
print(f"{flag_hex = }")
flag = bytes.fromhex(flag_hex.decode())
print(f"{flag = }")
```
キーストリームを取得して復号する場合
```py
from pwn import remote, xor

HOST, PORT = "localhost", 1337
# HOST, PORT = "34.170.146.252", 26148
p = remote(HOST, PORT)

p.recvuntil(b'flag = ')
enc_flag_hex = p.recvline().strip()
print(f"{enc_flag_hex = }")
p.sendlineafter(b'> ', b'2')
p.sendlineafter(b'> ', str(2**64 - 1).encode())
p.sendlineafter(b'> ', b'1')
p.sendlineafter(b'> ', b'00' * 16)
p.sendlineafter(b'> ', b'1')
p.sendlineafter(b'> ', b'0' * len(enc_flag_hex))
p.recvuntil(b'text = ')
keystream_hex = p.recvline().strip()
print(f"{keystream_hex = }")
enc_flag = bytes.fromhex(enc_flag_hex.decode())
keystream = bytes.fromhex(keystream_hex.decode())
flag = xor(enc_flag, keystream)
print(f"{flag = }")
```

## おわりに

Daily AlpacaHackにハマりすぎて、最近"Alpaca"をASCIIコード(0x416c70616361)で読めるようになってしまいました。

さて、AESの使い方の欠陥を突いて解く問題でしたが、いかがでしたでしょうか？

今回の脆弱性はいうまでもなく、同じkey, nonceのもとでユーザーに自由にcounterを設定させてしまったことです。

AESは強力な暗号だけど使い方を誤ると破綻するといういい例だったのではないかと思います。

きちんと基本どおりの使い方をするのが一番大事なのですね。

余談ですが、今回の問題作成で一番時間がかかったのは、実装でもデバッグプレイでもなく、フラグを何にしようか考えることでした（笑）

フラグを考えるのも作問の醍醐味の一つだと思っているし、別に何でも問題はないとは思いますが、ついこだわって悩み考え込んじゃいますよね。

最終的に、counter ⇒ 数えるという連想からこのフラグでいこうということになりました。
