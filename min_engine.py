from unicorn import *
from unicorn.arm_const import *
from keystone import *
from capstone import *

md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
# arm_code deve linguaggio macchina
arm_code = """
mov r1,#5 
mov r2,#5 
add r0,r2,r2 
"""

#trasformazione del keyston in bytecode
ks = Ks(KS_ARCH_ARM, KS_MODE_ARM)
encoding, _ = ks.asm(arm_code)
code = bytes(encoding)

# mappatura memoria, che in seguito dovra venire da assembler.py
ADDRESS = 0x1000
mu = Uc(UC_ARCH_ARM, UC_MODE_ARM)

mu.mem_map(0x1000, 0x2000)
mu.mem_map(0x3000, 0x1000)
mu.mem_map(0x4000, 0x1000)

mu.mem_write(ADDRESS, code)

mu.mem_write(0x2000, (0x22).to_bytes(4, "little"))
mu.mem_write(0x2008, (0x11223344).to_bytes(4, "little"))
mu.mem_write(0x3000, (0x0).to_bytes(4, "little"))

step = 1

def hook(mu, addr, size, _):
    global step

    if addr < 0x1000 or addr > 0x1800:
        print("errore:", hex(addr))
        mu.emu_stop()
        return

    data = mu.mem_read(addr, 4)

    for i in md.disasm(data, addr):
        print("\nSTEP", step)
        print(i.mnemonic, i.op_str)
        print("PC:", hex(mu.reg_read(UC_ARM_REG_PC)))
        print("R0:", mu.reg_read(UC_ARM_REG_R0))
        print("R1:", mu.reg_read(UC_ARM_REG_R1))
        print("R2:", mu.reg_read(UC_ARM_REG_R2))

    step += 1

mu.hook_add(UC_HOOK_CODE, hook)

mu.emu_start(ADDRESS, ADDRESS + len(code), count=300)


#output da implementare e da non stqampare
print("\n risultati")
print("R0 =", mu.reg_read(UC_ARM_REG_R0))
print("R1 =", mu.reg_read(UC_ARM_REG_R1))
print("R2 =", mu.reg_read(UC_ARM_REG_R2))


#da aggiungere ancora la parte degli input del start state