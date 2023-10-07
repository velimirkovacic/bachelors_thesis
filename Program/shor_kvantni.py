import numpy as np
import math
from qiskit import QuantumCircuit, transpile
from qiskit import QuantumRegister, ClassicalRegister
from qiskit import Aer
from qiskit.quantum_info.operators import Operator
from qiskit_ibm_provider import IBMProvider
from fractions import Fraction

API_KLJUC = ""      # IBM API ključ
SHOTS = 100         # broj izvođenja kvantnog logičkog kruga na simulatoru
K = 2               # minimalno 2
IBM_BACKEND = ""


class nemogucOperatorIznimka(Exception):
    pass



def brzo_potenciranje_2(a, N, e):
    for i in range (0, e):
        a = (a * a) % N
    return a



def f(a, N, x):
    return (x * a) % N



def stavarnje_mod_operatora(a, N, p, e, broj_qbit):
    broj_stanja = 2**broj_qbit
    matrica_operatora = np.zeros((broj_stanja, broj_stanja))
    a_potenciran = brzo_potenciranje_2(a, N, e)

    for i in range(broj_stanja):
        if i >= N:
            matrica_operatora[i][i] = 1
        else:
            matrica_operatora[f(a_potenciran, N, i)][i] = 1

    if not np.linalg.det(matrica_operatora):
        raise nemogucOperatorIznimka("Greška pri stvaranju operatora, nije moguće stvoriti operator za a = " + a)

    operator = Operator(matrica_operatora).to_instruction()
    operator.label = " x*" + str(a) + "^" + str(p) + " (mod " + str(N) + ")"

    return operator



def dodavanje_potenciranja(a, N, qreg_x, qreg_w, qkrug):
    U_mod_potenciranje = QuantumCircuit(name=" " + str(a) + "^x (mod " + str(N) + ")")
    U_mod_potenciranje.add_register(qreg_x)
    U_mod_potenciranje.add_register(qreg_w)
    potencija = 1
    eksponent = 0 # potencija = 2^eksponent
    
    for ctrl in qreg_x:
        l = [ctrl] + list(qreg_w)
        U_mod_potencija = stavarnje_mod_operatora(a, N, potencija, eksponent, qreg_w.size)
        
        potencija_krug = QuantumCircuit(qreg_w, name=" x*" + str(a) + "^" + str(potencija) + " (mod " + str(N) + ")")
        potencija_krug.append(U_mod_potencija, qreg_w)
        potencija_krug = potencija_krug.to_gate()
        potencija_krug = potencija_krug.control()
        
        U_mod_potenciranje.append(potencija_krug, l)

        potencija *= 2
        eksponent += 1

    qkrug.append(U_mod_potenciranje,  list(qreg_x) + list(qreg_w))



def dodavanje_qft_dagger(qreg_x, qkrug):
    qft_dagger = QuantumCircuit(qreg_x, name="QFT†")
    qft_dagger.h(0)

    for i in range(1, qreg_x.size):
        for j in range(i):
            qft_dagger.cp(-np.pi / 2**(i - j), control_qubit = i, target_qubit = j)
        qft_dagger.h(i)

    qkrug.append(qft_dagger, qreg_x)



def stvaranje_qkruga(a, N, broj_qbit, k):


    # Inicijalizacija registara
    qreg_w = QuantumRegister(broj_qbit, "w")
    qreg_x = QuantumRegister(k * broj_qbit, "x'")
    creg_r = ClassicalRegister(qreg_x.size, "c")


    # Incijalizacija kvantnog logičkog kruga
    qkrug = QuantumCircuit()
    qkrug.add_register(qreg_x)
    qkrug.add_register(qreg_w)
    qkrug.add_register(creg_r)


    # Dodavanje Hadamard operatora na sve kvantne bitove registra x
    for reg in qreg_x:
        qkrug.h(reg)


    # Dodavanje operatora modularnog potenciranja 
    qkrug.x(qreg_w[0])
    dodavanje_potenciranja(a, N, qreg_x, qreg_w, qkrug)


    # Mjerenje kvantnog registra w (nije potrebno)
    #qkrug.measure(qreg_w, creg_r[0:qreg_w.size])
    #qkrug.barrier()


    # Dodavanje QFT†
    for i in range(qreg_x.size//2):
        qkrug.swap(qreg_x[i], qreg_x[qreg_x.size - i - 1])
    dodavanje_qft_dagger(qreg_x, qkrug)
    
    
    # Mjerenje kvantnog registra x
    qkrug.measure(qreg_x, creg_r)

    return qkrug


def pronalazak_perioda(a, N):
    print("Stvaranje kvantnog logičkog kruga")
    broj_qbit = int(math.ceil(math.log(N + 1, 2)))

    global K
    qkrug = stvaranje_qkruga(a, N, broj_qbit, K)

    # Crtanje/spremanje kvantnog logičkog kruga
    print(qkrug)
    qkrug.draw(output="mpl", justify="left", filename="shor_krug.png", fold=999999)
    qkrug.qasm(filename="shor_qasm.txt")
    #plt.show()

    
    # Simulacija/pokretanje kvantnog logičkog kruga
    print("Priprema simulacije")


    global API_KLJUC
    global SHOTS
    if API_KLJUC == "":
        backend = Aer.get_backend('aer_simulator')
        mapped_circuit = transpile(qkrug, backend=backend)
    else:
        if "default-ibm-quantum" not in IBMProvider.saved_accounts().keys():
            IBMProvider.save_account(API_KLJUC)
        provider = IBMProvider()
        backend = provider.get_backend('ibm_perth')
        mapped_circuit = transpile(qkrug, backend=backend)
    
    print("Pokretanje simulacije")
    job = backend.run(mapped_circuit, shots=SHOTS)
    result = job.result()
    counts = result.get_counts()

    print("Kraj simulacije")
    
    broj_stanja = 2**(broj_qbit * K)
    r_opcije = set()
    r_ucestalost = dict()
    rezultati = set()
    for count in sorted(counts.keys()):
        rezultati.add((int(count, 2), counts[count]))

    print("Izmjereni fazni pomaci:")
    for rez in rezultati:
        x = rez[0]

        if x == 0:
            continue
        
        r = 0

        if broj_stanja > x:
            frac = Fraction(x/broj_stanja).limit_denominator(N)
            r = frac.denominator
            print("\ttheta =", frac)


        r_opcije.add(r)
        if r not in r_ucestalost.keys():
            r_ucestalost[r] = rez[1]
        else:
            r_ucestalost[r] += rez[1]
    
    print("Mogući periodi i broj ponavljanja:")
    for r in  r_ucestalost:
        print("\tr = ", r, "  (", r_ucestalost[r], " ponavljanja)", sep="")
    r_opcije_sort= sorted(r_ucestalost.items(), key=lambda x:x[1], reverse=True)
    r_opcije = []
    for r in r_opcije_sort:
        r_opcije += [r[0]]
    return r_opcije
