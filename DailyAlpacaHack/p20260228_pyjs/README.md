# pyjs

## 問題
```py
import subprocess

code = input("Enter your code: ")

res1 = subprocess.run(["runuser", "-u", "nobody", "--", "python3", "-c", code], capture_output=True)
assert res1.returncode == 0 and res1.stdout.strip() == b"I LOVE ALPACA"

res2 = subprocess.run(["runuser", "-u", "nobody", "--", "node", "-e", code], capture_output=True)
assert res2.returncode == 0 and res2.stdout.strip() == b"I LOVE SECCON"

print("Wow... Alpaca{REDACTED}")
```
