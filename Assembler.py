'''import os
import ply.lex as lex
import ply.yacc as yacc
from Encoder import encoder, convert_hex, convert
'''
# ======================================================================================================================
# Rules:

# start         -> Labels Instruction Operands Comments | DIRECTIVE | Labels |
#                  LABEL Labels DIRECTIVE NUMBER numbers | LABEL Labels DIRECTIVE STRING strings
# Numbers       -> EMPTY | COMMA NUMBER Numbers
# Strings       -> EMPTY | COMMA STRING Strings
# EMPTY         -> // do nothing
# Labels        -> EMPTY | LABEL Labels
# Instruction   -> MNE Condition Flag Mode
# Condition     -> EMPTY | COND
# Flag          -> EMPTY | S_FLAG
# Mode          -> EMPTY | AMODE
# Operands      -> Case_1 -> Case_19
# Case_1        -> REGISTER COMMA REGISTER COMMA REGISTER COMMA REGISTER                     // 4
# Case_2        -> REGISTER COMMA REGISTER COMMA REGISTER Shift                              // 3
# Case_3        -> REGISTER COMMA REGISTER COMMA IMMEDIATE                                   // 3 (2 + 1)
# Case_4        -> REGISTER COMMA REGISTER Shift                                             // 2
# Case_5        -> REGISTER COMMA IMMEDIATE                                                  // 2 (1 + 1)
# Case_6        -> REGISTER COMMA ST_REG                                                     // 2 (1 + 1)
# Case_7        -> ST_REG_F COMMA REGISTER                                                   // 2 (1 + 1)
# Case_8        -> ST_REG_F COMMA IMMEDIATE                                                  // 2 (1 + 1)
# Case_9        -> REGISTER                                                                  // 1
# Case_10       -> IMMEDIATE                                                                 // 1
# Case_11       -> NUMBER
# Case_12       -> ADDRESS                                                                   // 1

# Case_13       -> REGISTER Write_Back COMMA LF Reg_List RF Op_Mod                           // STM / LDM
# Write_Back    -> EMPTY | EM
# Reg_List      -> REGISTER HYPHEN REGISTER | REGISTER Registers
# Registers     -> EMPTY | Registers COMMA REGISTER
# Op_Mod        -> EMPTY | CR

# Case_14       -> REGISTER COMMA LB REGISTER COMMA Reg_Shift_Imm RB Write_Back             // STR / LDR
# Case_15       -> REGISTER COMMA LB REGISTER COMMA IMMEDIATE RB Write_Back
# Case_16       -> REGISTER COMMA LB REGISTER RB Write_Back
# Reg_Shift_Imm -> Negative REGISTER Shift_Imm
# Negative      -> EMPTY | HYPHEN
# Shift_Imm     -> EMPTY | COMMA SHIFT_ACTION IMMEDIATE

# Case_17       -> REGISTER COMMA LB REGISTER RB COMMA IMMEDIATE
# Case_18       -> REGISTER COMMA LB REGISTER RB COMMA Reg_Shift_Imm
# Case_19       -> REGISTER COMMA ADDRESS

# Shift         -> EMPTY | COMMA SHIFT_ACTION REGISTER | COMMA SHIFT_ACTION IMMEDIATE
# Comments      -> EMPTY | COMMENT                                                           // automatically discarded

# ======================================================================================================================
# Decode:

# result = [ LC , Instruction[] , Operands[] ]
#
# Instruction[] = [ Mnemonic , Condition {0->15} , S_Flag {0/1} , Addressing_Mode {-1/0->3} ]
#
# Operands[] = [ Op_Type {1->19} , Op[] ]
#
# Op_Type 1 :  [ Rd,Rm,Rs,Rn ]
# Op[] = [ Rd , Rm , Rs , Rn ]
#
# Op_Type 2 :  [ Rd,Rn,Rm { ,Shift Imm|Rs } ]
# Op[] = [ Rd , Rn , Rm , Shift[] ]
#
# Op_Type 3 :  [ Rd,Rn,Imm ]
# Op[] = [ Rd , Rn , Imm  ]
#
# Op_Type 4 :  [ Rd,Rm { ,Shift Imm|Rs }]
# Op[] = [ Rd , Rm , Shift[] ]
#
# Op_Type 5 :  [ Rd,Imm ]
# Op[] = [ Rd , Imm ]
#
# Op_Type 6 :  [ Rd,CPSR|SPSR ]
# Op[] = [ Rd , Status_Register {0/1} ]
#
# Op_Type 7 :  [ CPSR/SPSR_<flags>,Rm ]
# Op[] = [ Status_Register_Flags[] , Rm ]
#
# Op_Type 8 :  [ CPSR/SPSR_<flags>,Imm ]
# Op[] = [ Status_Register_Flags[] , Imm ]
#
# Op_Type 9 :  [ Rm ]
# Op[] = [ Rm ]
#
# Op_Type 10 : [ Imm ]
# Op[] = [ Imm ]
#
# Op_Type 11 : [ Num ]
# Op[] = [ Num ]
#
# Op_Type 12 : [ Label ]
# Op[] = [ Label , Hex_Address ]
#
# Op_Type 13 : [ Rd{!},{R1,..}{^} ]
# Op[] = [ Rd , Write_Back {0/1} , [ {List Of Registers} ] , Operation_Modified {0/1} ]
#
# Op_Type 14 : [ Rd,[Rn,{-}Rm {, Shift Imm} ]{!} ]
# Op[] = [ Rd , Rn , [ -ve {0/1} , Rm ] , Shift_Imm[] , Write_Back ]
#
# Op_Type 15 : [ Rd,[Rn,Imm]{!} ]
# Op[] = [ Rd , Rn , Imm , Write_Back {0/1} ]
#
# Op_Type 16 : [ Rd,[Rn]{!} ]
# Op[] = [ Rd , Rn , Write_Back {0/1} ]
#
# Op_Type 17 : [ Rd,[Rn],Imm ]
# Op[] = [ Rd , Rn , Imm ]
#
# Op_Type 18 : [ Rd,[Rn],{-}Rm {, Shift Imm} ]
# Op[] = [ Rd , Rn , [ -ve {0/1} , Rm ] , Shift_Imm[] ]
#
# Op_Type 19 : [ Rd,=Label ]
# Op[] = [ Rd , Label , Hex_Address ]
#
# Status_Register_Flags[] = [ CPSR/SPSR {0/1} , F {0/1} , S {0/1} , X {0/1} , C {0/1} ]
#
# Shift_Imm[] / Shift[] = [ Sh_Type , Sh[] ]
#
# Sh_Type -1 :
# // No Shift Present
#
# Sh_Type 1 :
# Sh[] = [ Shift_Action , Rs ]
#
# Sh_Type 2 :
# Sh[] = [ Shift_Action , Imm ]

# ======================================================================================================================
# Tokens:

# COMMA         -> ,
# AT_THE_RATE   -> @
# LB            -> [
# RB            -> ]
# LF            -> {
# RF            -> }
# HYPHEN        -> -
# EM            -> !
# CR            -> ^
# COMMENT       -> ( ; | @ ) STRING
# REGISTER      -> R{NUMBER} | SL | FP | IP | SP | LR | PC
# IMMEDIATE     -> #{NUMBER}
# NUMBER        -> {Any decimal / binary / hexadecimal}
# MNE           -> ADC | ADD | AND | B | BIC | BL | BLX | BX | CLZ | CMN | CMP | EOR | LDM |
#                  LDR | LDRB | LDRH | MLA | MOV | MRS | MSR | MUL | MVN | ORR | RSB | RSC | SBC |
#                  SMULL | SMLAL | STM | STR | STRB | STRH | SUB | SWI | TEQ | TST | UMLAL | UMULL
# COND          -> EQ | NE | CS | HS | CC | LO | MI | PL | VS | VC | HI | LS | GE | LT | GT | LE | AL
# S_FLAG        -> S
# AMODE         -> IA | FD | IB | ED | DA | FA | DB | EA
# SHIFT_ACTION  -> LSL | LSR | ASR | ROR
# ST_REG        -> CPSR | SPSR
# ST_REG_F      -> CPSR_<flags> | SPSR_<flags>
# DIRECTIVE     -> .STRING
# LABEL         -> STRING:
# ADDRESS       -> =STRING

# ======================================================================================================================
