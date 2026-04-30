
# import
from unicorn import *
from unicorn.arm_const import *
import argparse
from components import Registers, Memory, Breakpoint, ComponentException
from history import History
from assembler import parse as ASMparser

#eseguio il parsing del file assembly, ottenendo il bytecode, le informazioni sulle istruzioni, la mappatura degli indirizzi, le asserzioni, e eventuali errori. Se ci sono errori, li stampo e termino l'esecuzione.

parser = argparse.ArgumentParser(description="ARMulator")
parser.add_argument('inputfile', help="Assembler file")
args = parser.parse_args()
with open(args.inputfile) as f:
        bytecode, bcinfos, line2addr, assertions, _, errors = ASMparser(f)
print("Parsed source code!")
if errors:
    print("Errori:", errors)
    exit()

#creazione oggetti per la simulazione
history=History()
Reg=Registers(history)
mem=Memory(history,bytecode)
history.clear()#pulliamo la hisory 
# mappatura memoria,fatta tramite i dati della classe Memory, che contiene i dati di INTVEC, CODE e DATA, con i rispettivi indirizzi

INTVEC_ADDR = bytecode["__MEMINFOSTART"]["INTVEC"]
CODE_ADDR   = bytecode["__MEMINFOSTART"]["CODE"]
DATA_ADDR   = bytecode["__MEMINFOSTART"]["DATA"]

#creazione dell'istanza di Unicorn per ARM in modalità ARM (non Thumb), mappatura della memoria, e scrittura dei dati di INTVEC, CODE e DATA nei rispettivi indirizzi di memoria. Questo permette a Unicorn di eseguire il codice e gestire gli interrupt correttamente durante la simulazione.
mu = Uc(UC_ARCH_ARM, UC_MODE_ARM) #ogg unicorn per ARM in modalità ARM (non Thumb)
mu.mem_map(0x0, 0x10000) #mappa di memoria 
mu.mem_write(INTVEC_ADDR, bytes(mem.data["INTVEC"])) # prima comparto di memoria con vettore dei interupt 
mu.mem_write(CODE_ADDR,   bytes(mem.data["CODE"])) # secondo comparto di memoria con il code 
mu.mem_write(DATA_ADDR,   bytes(mem.data["DATA"])) # trezo comparto di memoria con i dati

# print degli indirizzi di memoria, per verificare che siano corretti, e per avere un riferimento durante la simulazione da toglirere dopo
print("INTVEC_ADDr", INTVEC_ADDR)
print("CODE_ADDR", CODE_ADDR)
print("DATA_ADDR", DATA_ADDR)

#sicronizzazione inizilae dei registri, in modo da poterli stampare alla fine, e anche per poterli usare durante la simulazione, ad esempio per le istruzioni che modificano i registri, o per le istruzioni di salto che usano i registri come indirizzi
# Sincronizzazione iniziale da components a Unicorn
print("\n--- Sincronizzazione iniziale ---")

# R0-R14
for i in range(15):
    mu.reg_write(UC_ARM_REG_R0 + i, Reg.getRegister(Reg.mode, i))

# PC (senza +8 perché Unicorn usa PC reale)
mu.reg_write(UC_ARM_REG_PC, CODE_ADDR)

# CPSR
mu.reg_write(UC_ARM_REG_CPSR, Reg.CPSR)

# SPSR solo se non User mode
if Reg.mode != "User":
    mu.reg_write(UC_ARM_REG_SPSR, Reg.SPSR)

print("Sincronizzazione iniziale completata!")
#verifca tramite printi che i registri siano stati sincronizzati correttamente poi va tolta 
for i in range(15):
    val_unicorn = mu.reg_read(UC_ARM_REG_R0 + i)
    val_component = Reg.getRegister(Reg.mode, i)
    print(f"R{i} Unicorn={val_unicorn} Component={val_component}")
mu.emu_start(CODE_ADDR, CODE_ADDR + len(bytes(mem.data["CODE"])),count=1000)#la simulazione parte da code, e finisce alla fine del bytecode, che è dato da CODE_ADDR + len(bytecode["CODE"])
#il count è un limite di istruzioni da eseguire, per evitare che la simulazione vada in loop infinito, perche il test e proggetato per cosii 
#sicronizzare i registri con quelli della classe Registers, in modo da poterli stampare alla fine, e anche per poterli usare durante la simulazione, ad esempio per le istruzioni che modificano i registri, o per le istruzioni di salto che usano i registri come indirizzi
#reg di uso generale
#creaiamo una nuova history 
history.newCycle()
for i in range(15):
    
    Reg.setRegister(Reg.mode, i, mu.reg_read(UC_ARM_REG_R0 + i))#chiamo la fuzione di set dei regisri presente in componte per settare i reg e gestire i vari history brek poinr ecc..
    
# PC
Reg.setRegister(Reg.mode, 15, mu.reg_read(UC_ARM_REG_PC) + 8)

# CPSR (aggiorna anche la modalità automaticamente)
Reg.CPSR = mu.reg_read(UC_ARM_REG_CPSR)

# SPSR solo se non User
if Reg.mode != "User":
    Reg.SPSR = mu.reg_read(UC_ARM_REG_SPSR)

#verifica che i registri siano stati sincronizzati correttamente
print("\n--- Verifica sincronizzazione ---")
sync_ok = True # flag utilizta per tenere traccia se la sincronizzazione è avvenuta correttamente, inizializzato a True e settato a False se viene trovato un registro non sincronizzato

# Verifica R0-R14
for i in range(15):
    val_unicorn = mu.reg_read(UC_ARM_REG_R0 + i) # il valorew ottenuto da la aimulazione uicorn 
    val_component = Reg.getRegister(Reg.mode, i) #il valore teoricame aggiornto da comporare 
    
    if val_unicorn != val_component:
        print(f"R{i} NON sincronizzato! Unicorn={val_unicorn} Component={val_component}") # per chi non lo sa questa e una stringa formattata, che permette di inserire variabili all'interno di una stringa in modo più leggibile e comodo rispetto alla concatenazione tradizionale. In questo caso, viene usata per stampare il numero del registro (i) e i valori ottenuti da Unicorn e dal componente.
        sync_ok = False #flag che indica che la sincronizzazione non è avvenuta correttamente, settato a False se viene trovato un registro non sincronizzato
    else:
        print(f"R{i} OK = {val_unicorn}")# se il registro è sincronizzato, stampo un messaggio di conferma con il valore del registro ottenuto da Unicorn

# Verifica PC
val_unicorn_pc = mu.reg_read(UC_ARM_REG_PC) + 8 #il + 8 e perché in ARM, durante l'esecuzione, il PC punta all'istruzione corrente + 8 (a causa del pipelining), quindi per confrontarlo con il valore del componente, che è il valore reale dell'istruzione corrente, dobbiamo aggiungere 8 al valore letto da Unicorn.
val_component_pc = Reg.getRegister(Reg.mode, 15)
if val_unicorn_pc != val_component_pc:
    print(f"PC NON sincronizzato! Unicorn={val_unicorn_pc} Component={val_component_pc}")
    sync_ok = False
else:
    print(f"PC OK = {val_unicorn_pc}")

# Verifica CPSR
val_unicorn_cpsr = mu.reg_read(UC_ARM_REG_CPSR)
if val_unicorn_cpsr != Reg.CPSR:
    print(f"CPSR NON sincronizzato! Unicorn={val_unicorn_cpsr} Component={Reg.CPSR}")
    sync_ok = False
else:
    print(f"CPSR OK = {val_unicorn_cpsr}")

# Risultato finale
if sync_ok:
    print("\n Sincronizzazione completata correttamente!")
else:
    print("\n Errore di sincronizzazione!")
#da aggiungere ancora la parte degli input del start state
