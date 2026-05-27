from sympy import Symbol, solve

# example
n = 187
phi = 216

x = Symbol('x')
expr = x * (phi - n - 1 - x) - n
ans = solve(expr, x)
p = ans[0]
q = ans[1]

print(f"{p = }") # p = 11
print(f"{q = }") # q = 17
print(f"Correct?", p * q == n) # Correct? True
