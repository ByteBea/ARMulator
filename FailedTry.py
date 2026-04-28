#import 
import argparse
from unicorn import *
from unicorn.arm_const import *
from capstone import *
from assembler import parse as ASMparser
from assembler import *
from history import History
from components import Registers, Memory
md = Cs(CS_ARCH_ARM, CS_MODE_ARM)#creazione oggetto Capstone per disasm


#test di input 
parser = argparse.ArgumentParser(description="ARMulator")
parser.add_argument('inputfile', help="Assembler file")
args = parser.parse_args()

with open(args.inputfile) as f:
        bytecode, bcinfos, line2addr, assertions, _, errors = ASMparser(f)
        print("Parsed source code!")
if errors:
    print("Errori:", errors)
    exit()
#Dopo la riga "if errors: ..."
#creiamo i componenti
history = History()
mem = Memory(history, bytecode)
regs = Registers(history)
# Indirizzi memoria presi da assembler tramite chiave
INTVEC_ADDR = bytecode["__MEMINFOSTART"]["INTVEC"]
CODE_ADDR   = bytecode["__MEMINFOSTART"]["CODE"]
DATA_ADDR   = bytecode["__MEMINFOSTART"]["DATA"]

# Setup Unicorn
mu = Uc(UC_ARCH_ARM, UC_MODE_ARM)
max_addr = max(bytecode["__MEMINFOEND"].values()) #cerchiamo l'indirizzo di memoria più alto tra quelli utilizzati, per caricare il codice ARM e i dati, in modo da mappare tutta la memoria necessaria per eseguire il codice ARM, senza sovrascrivere nulla.
mu.mem_map(0x0, max_addr + 0x1000)  # +0x1000 come buffer. Il buffer di 0x1000 byte per evitare di sovrascrivere la memoria mappata. In questo modo viene mappata tutta la memoria necessaria per eseguire il codice ARM, senza sovrascrivere nulla.

# Carica bytecode in memoria
mu.mem_write(INTVEC_ADDR, bytes(bytecode["INTVEC"]))
mu.mem_write(CODE_ADDR,   bytes(bytecode["CODE"]))
mu.mem_write(DATA_ADDR,   bytes(bytecode["DATA"]))
mu.reg_write(UC_ARM_REG_CPSR, regs.CPSR) #imposta il registro CPSR dell'oggetto unicorn con il valore del registro CPSR del nostro emulatore. In questo modo viene mantenuto aggiornato lo stato del registro CPSR alla fine dell'esecuzione del codice ARM e, permette di vedere il registro CPSR alla fine dell'esecuzione, se la modalità debug è attiva.
dm=input("debug on o off ")#toggle per attivare o disattivare la modalità debug che permette di eseguire il codice passo passo e vedere i registri ad ogni istruzione.
#Ora proviamo a fare un min debuger 
step=1 #contatore per tenere traccia degli step di esecuzione del codice ARM
def flow_cont(mu, addr, size, _): #hook per il controllo del flusso di esecuzione del codice ARM. Viene chiamato ogni volta che viene eseguita un'istruzione e riceve come argomenti l'oggetto unicorn, l'indirizzo dell'istruzione in esecuzione, la dimensione dell'istruzione e un parametro opzionale che non ci serve.
    code=mu.mem_read(addr,size) #legge il codice macchina dell'istruzione in esecuzione a partire dall'indirizzo e con la dimensione specificata.
    global step #richiama la variabile step per tenere traccia degli step di esecuzione del codice ARM.
    for  i in md.disasm(code, addr): #disasm è il codice macchina dell'istruzione in esecuzione e lo stampa a video, i è un oggetto che rappresenta l'istruzione disassemblata e contiene informazioni come il nome dell'istruzione (i.mnemonic) e gli operandi (i.op_str).
        if dm=="on":#modalità debug attiva, permette di eseguire il codice passo passo e vedere i registri ad ogni istruzione. Se dm è uguale a "on", allora entra in questa modalità.
            input("Premi invio per prossimo step...")
            print('sei allo step',step)
            print(f"{i.mnemonic} {i.op_str}") #i.mnemonic è il nome dell’istruzione.
            print(f"pc={hex(mu.reg_read(UC_ARM_REG_PC))}")
            #DA CONTROLLARE
            for i in range(15):
               regs.setRegister("User", i, mu.reg_read(UC_ARM_REG_R0 + i)) #utilizza il metodo setRegister dell'oggetto regs, per aggiornare i registri dell'architettura ARM con i valori letti dall'oggetto unicorn. In questo modo viene mantenuto aggiornato lo stato dei registri ad ogni istruzione eseguita, e permette di vedere i registri ad ogni istruzione se la modalità debug è attiva.
            
        else : #modalità debug disattivata, esegue il codice normalmente, senza mostrare i registri ad ogni istruzione. Se dm è diverso da "on" allora entra in questa modalità.
            print(f"{i.mnemonic} {i.op_str}") #i.mnemonic è il nome dell’istruzione.
    step=step+1#incrementa il contatore degli step di esecuzione del codice arm ad ogni istruzione eseguita
        

mu.hook_add(UC_HOOK_CODE, flow_cont)     #aggiunge l'hook per il controllo del flusso di esecuzione del codice ARM all'oggetto unicorn, in modo che venga chiamato ogni volta che viene eseguita un'istruzione, e permetta di mostrare i registri ad ogni istruzione, se la modalità debug è attiva.
  
mu.emu_start(CODE_ADDR, CODE_ADDR + len(bytes(bytecode["CODE"])))  #simula l'esecuzione del codice ARM a partire dall'indirizzo 0x1000 fino all'indirizzo 0x1000 + la lunghezza del codice macchina. In questo modo viene eseguito tutto il codice ARM caricato in memoria.
#output da angiungere 
#sicronizzazione finale registri unicorn con i registri del nostro emulatore. In questo modo viene mantenuto aggiornato lo stato dei registri alla fine dell'esecuzione del codice arm, e permette di vedere i registri alla fine dell'esecuzione se la modalità debug è attiva.
for i in range(15):
    regs.setRegister("User", i, mu.reg_read(UC_ARM_REG_R0 + i))

regs.setRegister("User", 15, mu.reg_read(UC_ARM_REG_PC) + 8)
regs.CPSR = mu.reg_read(UC_ARM_REG_CPSR)
#Gli indirizzi di memoria utilizzati per caricare il codice ARM e i dati, [in questo caso 0x00000 per il vettore di interruzione, 0x00080 per il codice ARM e 0x01000 per i dati] sono scelti arbitrariamente ma devono essere coerenti con quelli utilizzati nel codice ARM.