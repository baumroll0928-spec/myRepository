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
