digits=10**15
def gcd(a, b):
    if b==0: return a
    else: return gcd(b, a%b)
def simplify_gcd(n):
    c=gcd(n[0], n[1])
    return [n[0]/c, n[1]/c]
def simplify_sign(n):
    if n[1]<0: return [-n[0], -n[1]]
    return n
def need_simplify_p(n): return n[0]*n[1]>digits
def simplify_helper(n): return [n[0]/2, n[1]/2]
def simplify_magnitude(n):
    for i in range(20):
        if need_simplify_p(n):
            n=simplify_helper(n)
    return n
def simplify(n):
    n=simplify_magnitude(n)
    n=simplify_gcd(n)
    n=simplify_sign(n)
    return(n)
def inv(n): return [n[1], n[0]]
def plus(na, nb): return [na[0]*nb[1]+nb[0]*na[1], na[1]*nb[1]]
def neg(n): return [-n[0], n[1]]
def sub(na, nb): return plus(na, neg(nb))
def mul(na, nb): return [na[0]*nb[0], na[1]*nb[1]]
def div(na, nb): return mul(na, inv(nb))
def average(na, nb): return div(plus(na, nb), [2, 1])
def sqrt_improve(guess, n): return simplify(average(div(n, guess), guess))
def sqrt(n):
    guess=[1, 1]
    for i in range(7):
        guess=sqrt_improve(guess, n)
    return guess
def to_decimal(n): return(n[0]*1.0/n[1])

