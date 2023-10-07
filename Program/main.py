import shor_klasicni
import time

N = int(input("Unesite broj za rastav na proste faktore: "))

pocetak = time.time()
shor_klasicni.shor_klasicni(N)
print("Vrijeme izvođenja", round(time.time() - pocetak, 2), "s")