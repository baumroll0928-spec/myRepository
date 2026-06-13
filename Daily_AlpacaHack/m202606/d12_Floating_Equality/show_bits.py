def bits(x_str:str)->str:
    dot_pos = x_str.find(".")
    if dot_pos < 0:
        i = x_str
        f = "0"
    else:
        i = x_str[:dot_pos]
        f = x_str[dot_pos + 1:]
    s = f"{int(i):b}."
    m = 24
    n = int(f.ljust(m, "0"))
    base = pow(10, m)
    for _ in range(m):
        n *= 2
        s += str(n // base)
        n %= base
    return s

x = bits("3.14")
print(x)
di = x.find(".")
print("digits of integer:", di)
