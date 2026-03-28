# EncodeDecode

## 問題

swapswap は失敗でした…
今度は大丈夫なはず!
```py
import os

flag = os.environ.get("FLAG", "Alpaca{*** REDACTED ***}")

text = input("text> ")
encoding = input("encoding> ")

assert text.isascii(), "Text must be ASCII"

# This must be true, isn't it?
if text == text.encode(encoding).decode(encoding):
    print("Check passed!")
else:
    print("Check failed - !?")
    print("Here is your flag:", flag)
```
