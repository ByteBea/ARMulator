from unicorn import *
from unicorn.arm_const import *
import argparse
from components import Registers, Memory, Breakpoint, ComponentException
from history import History
from assembler import parse as ASMparser
#è il file Test_integrazione_reg.py ma gestito con una classe efunzioni

class UnicornEmulator:
    
    def dichiarazione_var(self):
        """
            dichiarazione delle variabbili in un valore nullo per evitare errori
        """
        self.mu = None
        self.bytecode = None
        self.errors = None

        self.history = None
        self.Reg = None
        self.mem = None

        self.INTVEC_ADDR = None
        self.CODE_ADDR = None
        self.DATA_ADDR = None

    def input_file(self):
        #eseguio il parsing del file assembly, ottenendo il bytecode, le informazioni sulle istruzioni, la mappatura degli indirizzi, le asserzioni, e eventuali errori. Se ci sono errori, li stampo e termino l'esecuzione.
        parser = argparse.ArgumentParser(description="ARMulator")
        parser.add_argument('inputfile', help="Assembler file")
        args = parser.parse_args()

        with open(args.inputfile) as f:
            self.bytecode, self.bcinfos, self.line2addr, self.assertions, _, self.errors = ASMparser(f)

        print("Parsed source code!")

        if self.errors:
            raise Exception(f"Errori: {self.errors}")

        self.mu = Uc(UC_ARCH_ARM, UC_MODE_ARM)

    def setup(self):
        #creazione oggetti per la simulazione
        self.history = History()
        self.Reg = Registers(self.history)
        self.mem = Memory(self.history, self.bytecode)
        self.history.clear()#pulliamo la hisory 

    def mappatura_mem(self):
        #mappatura memoria,fatta tramite i dati della classe Memory, che contiene i dati di INTVEC, CODE e DATA, con i rispettivi indirizzi
        self.INTVEC_ADDR = self.bytecode["__MEMINFOSTART"]["INTVEC"]
        self.CODE_ADDR   = self.bytecode["__MEMINFOSTART"]["CODE"]
        self.DATA_ADDR   = self.bytecode["__MEMINFOSTART"]["DATA"]
        #creazione dell'istanza di Unicorn per ARM in modalità ARM (non Thumb), mappatura della memoria, e scrittura dei dati di INTVEC, CODE e DATA nei rispettivi indirizzi di memoria. Questo permette a Unicorn di eseguire il codice e gestire gli interrupt correttamente durante la simulazione.
        self.mu.mem_map(0x0, 0x10000)
        self.mu.mem_write(self.INTVEC_ADDR, bytes(self.mem.data["INTVEC"]))
        self.mu.mem_write(self.CODE_ADDR,   bytes(self.mem.data["CODE"]))
        self.mu.mem_write(self.DATA_ADDR,   bytes(self.mem.data["DATA"]))
        # print degli indirizzi di memoria, per verificare che siano corretti, e per avere un riferimento durante la simulazione da toglirere dopo
        print("INTVEC_ADDR", self.INTVEC_ADDR)
        print("CODE_ADDR", self.CODE_ADDR)
        print("DATA_ADDR", self.DATA_ADDR)

    def sincronizzazione_iniziale(self):
        #sicronizzazione inizilae dei registri, in modo da poterli stampare alla fine, e anche per poterli usare durante la simulazione,
        #ad esempio per le istruzioni che modificano i registri, o per le istruzioni di salto che usano i registri come indirizzi
        # Sincronizzazione iniziale da components a Unicorn
        print("\n--- Sincronizzazione iniziale ---")
        # R0-R14
        for i in range(15):
            self.mu.reg_write(UC_ARM_REG_R0 + i,
                              self.Reg.getRegister(self.Reg.mode, i))
        # PC (senza +8 perché Unicorn usa PC reale)
        self.mu.reg_write(UC_ARM_REG_PC, self.CODE_ADDR)
        # CPSR
        self.mu.reg_write(UC_ARM_REG_CPSR, self.Reg.CPSR)
        # SPSR solo se non User mode
        if self.Reg.mode != "User":
            self.mu.reg_write(UC_ARM_REG_SPSR, self.Reg.SPSR)

        print("Sincronizzazione iniziale completata!")

    def run(self):
        self.mu.emu_start(
            self.CODE_ADDR,
            self.CODE_ADDR + len(bytes(self.mem.data["CODE"])),
            count=1000
        )

    def verifica(self):
        #verifica e stampa dei risultati
        print("\n--- Verifica sincronizzazione ---")

        self.history.newCycle()

        for i in range(15):
            self.Reg.setRegister(
                self.Reg.mode,
                i,
                self.mu.reg_read(UC_ARM_REG_R0 + i)
            )

        self.Reg.setRegister(
            self.Reg.mode,
            15,
            self.mu.reg_read(UC_ARM_REG_PC) + 8
        )

        self.Reg.CPSR = self.mu.reg_read(UC_ARM_REG_CPSR)

        if self.Reg.mode != "User":
            self.Reg.SPSR = self.mu.reg_read(UC_ARM_REG_SPSR)

        # confronto
        sync_ok = True

        for i in range(15):
            val_unicorn = self.mu.reg_read(UC_ARM_REG_R0 + i)
            val_component = self.Reg.getRegister(self.Reg.mode, i)

            if val_unicorn != val_component:
                print(f"R{i} NON sincronizzato! Unicorn={val_unicorn} Component={val_component}")
                sync_ok = False
            else:
                print(f"R{i} OK = {val_unicorn}")

        # PC
        val_unicorn_pc = self.mu.reg_read(UC_ARM_REG_PC) + 8
        val_component_pc = self.Reg.getRegister(self.Reg.mode, 15)

        if val_unicorn_pc != val_component_pc:
            print(f"PC NON sincronizzato! Unicorn={val_unicorn_pc} Component={val_component_pc}")
            sync_ok = False
        else:
            print(f"PC OK = {val_unicorn_pc}")

        # CPSR
        val_unicorn_cpsr = self.mu.reg_read(UC_ARM_REG_CPSR)

        if val_unicorn_cpsr != self.Reg.CPSR:
            print(f"CPSR NON sincronizzato! Unicorn={val_unicorn_cpsr} Component={self.Reg.CPSR}")
            sync_ok = False
        else:
            print(f"CPSR OK = {val_unicorn_cpsr}")

        # risultato
        if sync_ok:
            print("\n✔ Sincronizzazione completata correttamente!")
        else:
            print("\n✖ Errore di sincronizzazione!")
        


