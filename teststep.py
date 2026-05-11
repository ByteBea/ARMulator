from min_egine_versione_in_mod_classe import UnicornEmulator  #importare la classe da min_engine
from unicorn import *
from unicorn.arm_const import *
emu=UnicornEmulator()
# test step
emu.dichiarazione_var()         
emu.input_file()
emu.setup()
emu.mappatura_mem()
emu.sincronizzazione_iniziale()
emu.run()
print("\n--- Test Step ---")
print("Prima del step:")
print(f"R0 = {emu.Reg.getRegister('User', 0)}")  # atteso: 0
print(f"PC = {emu.mu.reg_read(UC_ARM_REG_PC)}")  # atteso: indirizzo del primo istruzione

emu.step()  # esegue MOV R0, #5
print("\nDopo step 1:")
print(f"R0 = {emu.Reg.getRegister('User', 0)}")  # atteso: 5

emu.step()  # esegue MOV R1, #3
print("\nDopo step 2:")
print(f"R1 = {emu.Reg.getRegister('User', 1)}")  # atteso: 3

emu.step()  # esegue ADD R2, R0, R1
print("\nDopo step 3:")
print(f"R2 = {emu.Reg.getRegister('User', 2)}")  # atteso: 8

print("\n--- Verifica history ---")
emu.stampa_history()