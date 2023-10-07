import random
import shor_kvantni


def nzd(a, b):
    if b == 0:
        return a
    else:
        return nzd(b, a % b)
    
def shor_klasicni(N):

    neuspjesi = set()

    while len(neuspjesi) < N - 2:
        a = random.randint(2, N - 1)

        while a in neuspjesi:
            a = random.randint(2, N - 1)

        print("Odabiremo nasumični broj a =", a)

        d = nzd(a, N)

        if d == 1:
            print("Formiramo funkciju f(x) = ", a, "^x (mod ", N,") i tražimo njen period", sep="")
        else:
            print("Pogodili smo a s jednim istim prostim faktorom kao ", N, ", ne moramo dalje računati", "\nRješenja su ", d, " i ", N//d, sep="")
            return d, N//d
        
        try:
            r_opcije = shor_kvantni.pronalazak_perioda(a, N)
        except shor_kvantni.nemogucOperatorIznimka:
            print("Nije moguće konstruirati potrebni operator za tu vrijednost a")
            neuspjesi.add(a)
            continue
        
        uspjeh = False
        for r in r_opcije:
            print("Provjera za r =", r)
            if r % 2:
                print("Period r = ", r, ", neparan -> NEUSPJEH", sep="")
            elif (a**(r // 2) + 1) % N == 0:
                print("Period r = ", r, ", a^(r/2) + 1 = 0 (mod N) -> NEUSPJEH", sep="")
            else:
                print("r =", r, "zadovoljava kriterije")
                p = nzd(a**(r // 2) + 1, N)
                q = nzd(a**(r // 2) - 1, N)
                print("Račuanmo nzd(a^(r/2) + 1, N) = nzd(", a**(r // 2) + 1, ", ", N, ") = ", p, sep="")
                print("Račuanmo nzd(a^(r/2) - 1, N) = (", a**(r // 2) - 1, ", ", N, ") = ", q, sep="")

                if p != 1:
                    print("Rješenja su", p, "i", N//p)
                    return p, N//p
                elif q != 1:
                    print("Rješenja su", q, "i", N//q)
                    return  q, N//q
        

        neuspjesi.add(a)
        continue
    
    print("Neuspjeh. Jeste li sigurni da je N umnožak 2 prosta broja?")

