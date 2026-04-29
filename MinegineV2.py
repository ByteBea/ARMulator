from unicorn import *
from unicorn.arm_const import *
import argparse
from components import Registers, Memory, Breakpoint, ComponentException
from history import History
from assembler import parse as ASMparser
parser = argparse.ArgumentParser(description="ARMulator")
parser.add_argument('inputfile', help="Assembler file")
args = parser.parse_args()

with open(args.inputfile) as f:
        bytecode, bcinfos, line2addr, assertions, _, errors = ASMparser(f)
        print("Parsed source code!")
if errors:
    print("Errori:", errors)
    exit()
history=History()
Reg=Registers(history)
mem=Memory(history,bytecode)

# mappatura memoria, che in seguito dovra venire da assembler.py

INTVEC_ADDR = bytecode["__MEMINFOSTART"]["INTVEC"]
CODE_ADDR   = bytecode["__MEMINFOSTART"]["CODE"]
DATA_ADDR   = bytecode["__MEMINFOSTART"]["DATA"]

ADDRESS=0x0
mu = Uc(UC_ARCH_ARM, UC_MODE_ARM)
mu.mem_map(0x0, 0x10000)
mu.mem_write(INTVEC_ADDR, bytes(mem.data["INTVEC"]))
mu.mem_write(CODE_ADDR,   bytes(mem.data["CODE"]))
mu.mem_write(DATA_ADDR,   bytes(mem.data["DATA"]))
print("INTVEC_ADDr", INTVEC_ADDR)
print("CODE_ADDR", CODE_ADDR)
print("DATA_ADDR", DATA_ADDR)



mu.emu_start(0x0, 0x10000, count=300)


#output da implementare e da non stqampare
print("\n risultati")
print("R0 =", mu.reg_read(UC_ARM_REG_R0))
print("R1 =", mu.reg_read(UC_ARM_REG_R1))
print("R2 =", mu.reg_read(UC_ARM_REG_R2))


#da aggiungere ancora la parte degli input del start state
