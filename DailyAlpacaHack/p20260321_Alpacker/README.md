# Alpacker

## 問題

ミニアルパカが隠れているよ🦙

## 概要

バイナリファイル`chal`が１つだけ配布されています。ELF形式の実行ファイルのようです。

Ghidraで解析したところ、main関数が見当たりません・・・。

## 解法

※これはあくまでも初心者の私がこうやったらできた！というものなので、絶対もっといい方法があるかと思います。

とりあえずGhidraに投げてみます。

main関数が見当たりませんが、関数一覧を見てみると、FUN_00101229というすごくそれっぽいのがありました。

※変数名はいくつか書き換えてあります。
```c

undefined8 FUN_00101229(void)

{
  int is_correct;
  char *ptr;
  size_t len_input;
  undefined8 uVar1;
  code *__dest;
  long in_FS_OFFSET;
  uint i;
  char input_flag [136];
  long local_10;
  
  local_10 = *(long *)(in_FS_OFFSET + 0x28);
  printf("flag: ");
  ptr = fgets(input_flag,0x80,stdin);
  if (ptr == (char *)0x0) {
    uVar1 = 1;
  }
  else {
    ptr = strchr(input_flag,10);
    if (ptr != (char *)0x0) {
      *ptr = '\0';
    }
    len_input = strlen(input_flag);
    if (len_input == 0x24) {
      __dest = mmap((void *)0x0,0x11b,7,0x22,-1,0);
      if (__dest == (code *)0xffffffffffffffff) {
        uVar1 = 1;
      }
      else {
        memcpy(__dest,&DAT_00104020,0x11b);
        for (i = 0; i < 0x11b; i = i + 1) {
          __dest[(int)i] = (code)((char)__dest[(int)i] * 's');
        }
        is_correct = (*__dest)(input_flag);
        if (is_correct == 0) {
          puts("wrong...");
        }
        else {
          puts("correct!");
        }
        uVar1 = 0;
      }
    }
    else {
      puts("wrong...");
      uVar1 = 0;
    }
  }
  if (local_10 != *(long *)(in_FS_OFFSET + 0x28)) {
                    /* WARNING: Subroutine does not return */
    __stack_chk_fail();
  }
  return uVar1;
}
```

重要そうなのは次の３か所でしょうか。

```c
      __dest = mmap((void *)0x0,0x11b,7,0x22,-1,0);
```
0x11b(=283)バイト分の領域を展開しているようです。
```c
        memcpy(__dest,&DAT_00104020,0x11b);
        for (i = 0; i < 0x11b; i = i + 1) {
          __dest[(int)i] = (code)((char)__dest[(int)i] * 's');
        }
```
DAT_00104020というところからデータを283バイト分コピーした後、各バイトに対して's'倍して8ビット切り取り、つまり` * 115 % 256`という暗号化チックな変換をしています。
```c
        is_correct = (*__dest)(input_flag);
```
コピー、変換した領域を関数として、引数に入力したフラグを渡して実行します。

その後、戻り値が`0`なら失敗、`0`以外なら成功としています。

このDAT_00104020というのがどこにあるのかわかりませんでしたが、Listingの部分を見るとこんなのがありました。
```
                             DAT_00104020                                    XREF[2]:     FUN_00101229:0010133b(*), 
                                                                                          FUN_00101229:00101342(*)  
        00104020 cb              ??         CBh
        00104021 40              ??         40h    @
        00104022 80              ??         80h
        ...
```

chalファイルをバイナリエディタで開き、最初の３バイト`cb 40 80`で検索してみると１つ見つかったので、そこから283バイト分取ってみました。
```
CB 40 80 05 7B F5 27 F5 BB 00 00 80 C5 91 4F F5 27 A7 BB 00 00 80 C5 BB E4 F5 27 59 00 00 00 80 C5 B0 5A F5 27 0B 00 00 00 80 C5 EC 51 F5 27 BD 00 00 00 80 C5 9C A3 F5 27 6F 00 00 00 80 C5 A7 DB F5 27 21 00 00 00 80 C5 D8 DB F5 27 D3 00 00 00 80 C5 CD DB F5 27 85 00 00 00 80 C5 26 FC F5 27 37 00 00 00 80 C5 FE 5A F5 27 E9 00 00 00 80 C5 93 ED F5 27 9B 00 00 00 80 C5 C4 B3 F5 27 4D 00 00 00 80 C5 4E FC F5 27 FF 00 00 00 80 C5 7F 65 F5 27 B1 00 00 00 80 C5 F5 B3 77 4F 80 C5 EA D0 77 ED 80 C5 3A 9F 77 8B 80 C5 60 51 77 29 80 C5 1B DB 77 C7 80 C5 62 D9 77 65 80 C5 57 DB 77 03 80 C5 76 D0 77 A1 80 C5 D6 1B 77 3F 80 C5 E1 CB 77 DD 80 C5 2F E4 77 7B 80 C5 74 FC 77 19 80 C5 88 65 77 B7 80 C5 6B CB 77 55 80 C5 43 CB 77 F3 80 C5 A5 FC 77 91 80 C5 09 B3 77 2F 80 C5 31 DB 77 CD 80 C5 B9 65 77 6B 80 C5 1D 29 77 09 80 C5 12 51 77 A7 68 BB 00 00 00 71
```
これに前述の変換をかけるとこうなります。
```
31 C0 80 3F 41 0F 85 0F 01 00 00 80 7F 23 7D 0F 85 05 01 00 00 80 7F 01 6C 0F 85 FB 00 00 00 80 7F 10 6E 0F 85 F1 00 00 00 80 7F 04 63 0F 85 E7 00 00 00 80 7F 14 39 0F 85 DD 00 00 00 80 7F 05 61 0F 85 D3 00 00 00 80 7F 08 61 0F 85 C9 00 00 00 80 7F 17 61 0F 85 BF 00 00 00 80 7F 12 34 0F 85 B5 00 00 00 80 7F 1A 6E 0F 85 AB 00 00 00 80 7F 09 77 0F 85 A1 00 00 00 80 7F 0C 69 0F 85 97 00 00 00 80 7F 0A 34 0F 85 8D 00 00 00 80 7F 0D 5F 0F 85 83 00 00 00 80 7F 0F 69 75 7D 80 7F 1E 70 75 77 80 7F 0E 6D 75 71 80 7F 20 63 75 6B 80 7F 21 61 75 65 80 7F 06 7B 75 5F 80 7F 15 61 75 59 80 7F 02 70 75 53 80 7F 22 21 75 4D 80 7F 13 31 75 47 80 7F 1D 6C 75 41 80 7F 1C 34 75 3B 80 7F 18 5F 75 35 80 7F 11 31 75 2F 80 7F 19 31 75 29 80 7F 1F 34 75 23 80 7F 0B 69 75 1D 80 7F 03 61 75 17 80 7F 1B 5F 75 11 80 7F 07 6B 75 0B 80 7F 16 63 75 05 B8 01 00 00 00 C3
```
このバイナリデータをいったん`code.bin`というファイルに保存し、この部分だけアセンブリ化してみました。
```sh
objdump -D -b binary -m i386:x86-64 code.bin > res.txt
```
すると、こんな感じになりました。
```
code.bin:     ファイル形式 binary


セクション .data の逆アセンブル:

0000000000000000 <.data>:
   0:	31 c0                	xor    %eax,%eax
   2:	80 3f 41             	cmpb   $0x41,(%rdi)
   5:	0f 85 0f 01 00 00    	jne    0x11a
   b:	80 7f 23 7d          	cmpb   $0x7d,0x23(%rdi)
   f:	0f 85 05 01 00 00    	jne    0x11a
  15:	80 7f 01 6c          	cmpb   $0x6c,0x1(%rdi)
  19:	0f 85 fb 00 00 00    	jne    0x11a
  ...   ...                     ...    ...
 109:	80 7f 07 6b          	cmpb   $0x6b,0x7(%rdi)
 10d:	75 0b                	jne    0x11a
 10f:	80 7f 16 63          	cmpb   $0x63,0x16(%rdi)
 113:	75 05                	jne    0x11a
 115:	b8 01 00 00 00       	mov    $0x1,%eax
 11a:	c3                   	ret
```
最初の`xor %eax,%eax`で、戻り値を表すレジスタを0（=失敗）にしています。

次の行からは、入力の指定位置の文字と定数を比較して、違ったらそのまま`ret`まで直行で飛ぶ、という比較処理の繰り返しです。

例えば最初は`[0]`（オフセット無し）と`0x41(="A")`を比較し、２つ目は`[0x23(=35)]`と`0x7d(="}")`を比較しています。

フラグの長さは36文字なので、最初が`A`、最後が`}`まで判明しました。これで間違いなさそうです。

全てのチェックが通ったら、`mov $0x1,%eax`で戻り値を1（=成功）にしています。

これ以降全部手動で復元してもできないことはないですが、とても面倒くさいので、Pythonで抽出しました。

```py
code = bytes.fromhex("31 C0 80 ...略... C3")
flag_array = [ord('?')] * 36
pos = -1
while True:
    pos = code.find(b'\x80', pos+1)
    if pos == -1:
        break
    cmd = code[pos + 1]
    if cmd == 0x3f:
        i = 0
        x = code[pos + 2]
    else:
        i = code[pos + 2]
        x = code[pos + 3]
    flag_array[i] = x

flag = bytes(flag_array).decode()
print(f"{flag = }")
```
