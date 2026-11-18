# settable counter

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
