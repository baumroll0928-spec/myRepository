# Alpaillier

## 問題
アルパイエって何者？
```py
def main():
    flag = os.getenv("FLAG", "Alpaca{REDACTED}").encode()

    bits = 1024
    p = getPrime(bits // 2)
    q = getPrime(bits // 2)
    n = p * q
    n2 = n * n
    g = n + 1

    r = getRandomRange(2, n - 1)
    while GCD(r, n) != 1:
        r = getRandomRange(2, n - 1)

    cs = []
    rn = pow(r, n, n2)
    for b in flag:
        c = (pow(g, b, n2) * rn) % n2
        cs.append(c)

    print(f"n = {n}\n")
    print(f"c = {cs}\n")
```

## 方針
rを特定する必要はなく、rnさえわかれば復号できます。

## 解法
まず、わかっていること、わかっていないことを整理します。

nはoutput.txtで提示されているのですぐにわかります。また、
```py
n2 = n * n
g = n + 1
```
から、n2とgもすぐに計算することができます。

flagの各文字に使われているbはわかりませんが、1バイトごとに分解しているので、0x00～0xffのどれかですよね。

今回はflagの文字種について明記されていませんが、たぶんASCII可視文字（0x21-0x7e）だろうと信じて進めます。

※後で思うと、フラグ形式Alpaca{...}も考慮すればもっと簡単に絞れたような気がします。

そうすると、

$`c_i\equiv g^{b_i} * rn \pmod{n2}`$

から、

$`rn\equiv g^{-b_i} * c_i \pmod{n2}`$

より、rnは$`b_i`$と$`c_i`$から計算でき、$`c_i`$はoutput.txtで提示されているので、rnも94通りに絞れそうです。

※gの逆元$`g^{-1} \pmod{n2}`$が存在するにはgとn2が互いに素である必要がありますが、
nは2つの巨大な素数p,qの積、gはn+1であり、gをp,qどちらでで割っても1あまるので、gとn2は共通の素因数をもたない互いに素な数です。

このrnはそれぞれの$`b_i`$と$`c_i`$から94通りの候補が求められるので、全ての候補リストの共通部分を求めてみることにします。

```py
n = output.txtからコピペ
c = output.txtからコピペ
g = n + 1
n2 = n * n

for i in range(len(c)):
    newlst = set()
    for b in range(0x21, 0x7f):
        rn = c[i] * pow(g, -b, n2) % n2
        newlst.add(rn)
    if i == 0:
        rnlst = newlst
    else:
        rnlst = rnlst & newlst
print(f"{len(rnlst) = }")
```

これだけの文字があるんだからさすがにrnは一意に求まるでしょう。ふふん。
```
len(rnlst) = 20
```
20個!?

なぜ20個も残っているのかはわかりませんが、とりあえず20個全てのrnを使って復号してみることにします。

20個なら目で見てそれっぽいのを探してもそんなに大変ではないでしょうし、94→20に絞れただけでもよしとしましょう（ポジティブに）。

```py
for rn in rnlst:
    tmp = []
    for i in range(len(c)):
        for b in range(0x21, 0x7f):
            if pow(g, b, n2) * rn % n2 == c[i]:
                tmp.append(b)
                break
        else:
            tmp.append(ord(' '))
    print(bytes(tmp))
```

実行してみると、1番目にめっちゃそれっぽいのが出てきました。※一応フラグは伏せておきます。

```
b'Alpaca{***************************}'
b"5`dUWUoh\\'Sd(gh'`S(`d(W(S]gSd`(W]Xq"
b'3^bSUSmfZ%Qb&ef%^Q&^b&U&Q[eQb^&U[Vo'
b':eiZ\\Ztma,Xi-lm,eX-ei-\\-XblXie-\\b]v'
b'8cgXZXrk_*Vg+jk*cV+cg+Z+V`jVgc+Z`[t'
b'?jn_a_yrf1]n2qr1j]2jn2a2]gq]nj2agb{'
b'=hl]_]wpd/[l0op/h[0hl0_0[eo[lh0_e`y'
b'1\\`QSQkdX#O`$cd#\\O$\\`$S$OYcO`\\$SYTm'
b'/Z^OQOibV!M^"ab!ZM"Z^"Q"MWaM^Z"QWRk'
b'Bmqbdb|ui4`q5tu4m`5mq5d5`jt`qm5dje~'
b'6aeVXVpi](Te)hi(aT)ae)X)T^hTea)X^Yr'
b"4_cTVTng[&Rc'fg&_R'_c'V'R\\fRc_'V\\Wp"
b';fj[][unb-Yj.mn-fY.fj.].YcmYjf.]c^w'
b'9dhY[Ysl`+Wh,kl+dW,dh,[,WakWhd,[a\\u'
b'7bfWYWqj^)Uf*ij)bU*bf*Y*U_iUfb*Y_Zs'
b'@ko`b`zsg2^o3rs2k^3ko3b3^hr^ok3bhc|'
b'>im^`^xqe0\\m1pq0i\\1im1`1\\fp\\mi1`faz'
b'2]aRTRleY$Pa%de$]P%]a%T%PZdPa]%TZUn'
b'<gk\\^\\voc.Zk/no.gZ/gk/^/ZdnZkg/^d_x'
b'0[_PRPjcW"N_#bc"[N#[_#R#NXbN_[#RXSl'
```

最後に、なぜrnの候補が20個もでてきたのか、この出力結果をみてわかりました。

詳細は省きますが、この手の暗号って、全体で上下にシフトしがちなんですよね。

今回フラグに使われた文字の中で文字コードの最大は"}"の0xfd、最小は"3"の0x33でした。
```
!  ...  3 ...  }  ~
21 ... 33 ... 7d 7e
```

"3"の前に18文字、"}"の後に1文字あり、これがいわゆるアソビになります。

よって、正規のものと合わせて20通りの候補が生まれたようですね。

## その他

問題文にもある、Alpaillierってホントに何なんでしょうか？

たぶんAlpacaと何かを掛け合わせた造語なのかなと予想して、試しにpaillierでWeb検索してみると・・・

Paillier暗号 - Wikipedia https://ja.wikipedia.org/wiki/Paillier%E6%9A%97%E5%8F%B7

Paillier暗号というのがあり、説明を読んでみると今回の暗号化方式であることがわかりました。
