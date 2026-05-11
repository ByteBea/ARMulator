SECTION INTVEC
B main

SECTION CODE
main
    MOV R0, #42
    LDR R1, =myvar
    STR R0, [R1]
    LDR R2, [R1]

SECTION DATA
myvar ALLOC32 1