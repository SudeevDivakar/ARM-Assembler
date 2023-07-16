import os
import ply.lex as lex
import ply.yacc as yacc
from Encoder import encoder, convert_hex, convert

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

tokens = ['COMMA', 'LB', 'RB', 'LF', 'RF', 'HYPHEN', 'EM', 'CR',
          'REGISTER', 'IMMEDIATE', 'NUMBER', 'ST_REG', 'ST_REG_F',
          'MNE', 'COND', 'AMODE', 'S_FLAG', 'SHIFT_ACTION', 'RRX',
          'LABEL', 'ADDRESS', 'DIRECTIVE', 'STRING']

t_COMMA = r','
t_LB = r'\['
t_RB = r'\]'
t_LF = r'\{'
t_RF = r'\}'
t_EM = r'!'
t_CR = r'\^'
t_HYPHEN = r'-'
t_ignore = ' \t'

LC = 0x1000

DIRECTIVES = ['DATA', 'TEXT', 'WORD', 'HWORD', 'BYTE', 'ASCIZ', 'ASCII', 'END']

CONDITIONS = {'EQ': 0x0, 'NE': 0x1, 'CS': 0x2, 'HS': 0x2, 'CC': 0x3, 'LO': 0x3, 'MI': 0x4, 'PL': 0x5, 'VS': 0x6,
              'VC': 0x7, 'HI': 0x8, 'LS': 0x9, 'GE': 0xA, 'LT': 0xB, 'GT': 0xC, 'LE': 0xD, 'AL': 0xE, 'NV': 0xF}

BRANCH = [' B ', ' BL ']

B_COND = BRANCH[:]

for _ in CONDITIONS:
    B_COND.append(BRANCH[0][:2] + _ + ' ')
    B_COND.append(BRANCH[1][:3] + _ + ' ')

SHIFT_ACTIONS = {'LSL': 0b00, 'LSR': 0b01, 'ASR': 0b10, 'ROR': 0b11}

ADDR_MODE = {'IA': 0x01, 'IB': 0x11, 'DA': 0x00, 'DB': 0x10}

SPEC_REGS = {'SL': 10, 'FP': 11, 'IP': 12, 'SP': 13, 'LR': 14, 'PC': 15}

SYM_T = dict()


def t_comment(t):
    r""";.*|@.*"""
    pass


def t_LABEL(t):
    r"""([A-Z][A-Z0-9]*[:])"""
    t.value = t.value[:-1]
    return t


def t_ADDRESS(t):
    r"""([=][A-Z][A-Z0-9]*)"""
    t.value = t.value[1:]
    return t


def t_DIRECTIVE(t):
    r"""([\.][A-Z][A-Z0-9]*)"""
    t.value = t.value[1:]
    if t.value not in DIRECTIVES:
        raise Exception("Unknown directive")
    return t


def t_STRING(t):
    r""" [\"].*[\"] | [\'].*[\'] """
    t.value = t.value[1:-1]
    return t


def t_ST_REG_F(t):
    r"""([C][P][S][R][_][FSXC]+) | ([S][P][S][R][_][FSXC]+)"""
    val = t.value
    val1 = -1
    F, S, X, C = 0, 0, 0, 0
    if val[:4] == 'CPSR':
        val1 = 0
    elif val[:4] == 'SPSR':
        val1 = 1
    if 'F' in val[5:]:
        F = 1
    if 'S' in val[5:]:
        S = 1
    if 'X' in val[5:]:
        X = 1
    if 'C' in val[5:]:
        C = 1

    t.value = (val1, F, S, X, C)
    return t


def t_ST_REG(t):
    r"""([C][P][S][R]) | ([S][P][S][R])"""
    if t.value == 'CPSR':
        t.value = 0
    elif t.value == 'SPSR':
        t.value = 1
    return t


def t_MNE(t):
    r"""([A][D][C]) | ([A][D][D]) | ([A][N][D]) | ([B][I][C]) | ([B][L][E][Q]) | ([B][L][E]) | ([B][L][O]) | ([B][L][S]) | ([B][L][T]) | ([B][L][X]) | ([B][L]) | ([B][X]) | ([B]) | ([C][L][Z]) | ([C][M][N]) | ([C][M][P]) | ([E][O][R]) | ([L][D][M]) | ([L][D][R][B]) | ([L][D][R][H]) | ([L][D][R]) | ([M][L][A]) | ([M][O][V]) | ([M][R][S]) | ([M][S][R]) | ([M][U][L]) | ([M][V][N]) | ([O][R][R]) | ([R][S][B]) | ([R][S][C]) | ([S][B][C]) | ([S][M][U][L][L]) | ([S][M][L][A][L]) | ([S][T][M]) | ([S][T][R][B]) | ([S][T][R][H]) | ([S][T][R]) | ([S][U][B]) | ([S][W][I]) | ([T][E][Q]) | ([T][S][T]) | ([U][M][L][A][L]) | ([U][M][U][L][L])"""
    return t


def t_SHIFT_ACTION(t):
    r"""([L][S][L]) | ([L][S][R]) | ([A][S][R]) | ([R][O][R])"""
    t.value = SHIFT_ACTIONS[t.value]
    return t


def t_RRX(t):
    r"""[R][R][X]"""
    t.value = 4
    return t


def t_COND(t):
    r"""([E][Q]) | ([N][E]) | ([C][S]) | ([H][S]) | ([C][C]) | ([L][O]) | ([M][I]) | ([P][L]) | ([V][S]) | ([V][C]) | ([H][I]) | ([L][S]) | ([G][E]) | ([L][T]) | ([G][T]) | ([L][E]) | ([A][L]) | ([N][V])"""
    t.value = CONDITIONS[t.value]
    return t


def t_AMODE(t):
    r"""([I][A]) | ([F][D]) | ([I][B]) | ([E][D]) | ([D][A]) | ([F][A]) | ([D][B]) | ([E][A])"""
    if t.value == 'FD':
        t.value = 'IA'
    elif t.value == 'ED':
        t.value = 'IB'
    elif t.value == 'FA':
        t.value = 'DA'
    elif t.value == 'EA':
        t.value = 'DB'

    t.value = ADDR_MODE[t.value]
    return t


def t_REGISTER(t):
    r"""([R]\d+) | [S][L] | [F][P] | [I][P] | [S][P] | [L][R] | [P][C]"""
    val = t.value
    if val in SPEC_REGS.keys():
        t.value = SPEC_REGS[t.value]
    else:
        val = int(t.value[1:])
        if -1 < val < 16:
            t.value = val
        else:
            t_error(t)
    return t


def t_IMMEDIATE(t):
    r"""[#]([0][B][01]+ | [0][X][0-9A-F]+ | [1-9][0-9]* | [\-][1-9][0-9]* | [0] | [\-][0] )"""
    if isinstance(t.value, str) and len(t.value) > 3 and (t.value[2] == 'B' or t.value[2] == 'X'):
        if t.value[1] == '0' and t.value[2] == 'B':
            t.value = int(t.value[3:], 2)
        elif t.value[1] == '0' and t.value[2] == 'X':
            t.value = int(t.value[3:], 16)
    else:
        t.value = int(t.value[1:])
    return t


def t_NUMBER(t):
    r"""[0][B][01]+ | [0][X][0-9A-F]+ | (\d+) | [\-](\d+)"""
    if isinstance(t.value, str) and len(t.value) > 2:
        if t.value[0] == '0' and t.value[1] == 'B':
            t.value = int(t.value[2:], 2)
        elif t.value[0] == '0' and t.value[1] == 'X':
            t.value = int(t.value[2:], 16)
    else:
        t.value = int(t.value)
    return t


def t_S_FLAG(t):
    r"""[S]"""
    return t


def t_newline(t):
    r"""\n+"""
    t.lexer.lineno += len(t.value)


def t_error(t):
    raise Exception("Illegal character '%s' " % t.value[0])


def p_start_0(p):
    """
    start : LABEL Labels DIRECTIVE STRING Strings
    start : LABEL Labels DIRECTIVE NUMBER Numbers
    start : Labels
    start : DIRECTIVE
    Labels : EMPTY
    Labels : LABEL Labels
    Numbers : EMPTY
    Numbers : COMMA NUMBER Numbers
    Strings : EMPTY
    Strings : COMMA STRING Strings
    EMPTY :
    """
    p[0] = None


def p_start_1(p):
    """start : Labels Instruction Operands"""
    global LC
    p[0] = (LC, p[2], p[3])
    LC += 4


def p_Instruction(p):
    """Instruction : MNE Condition Flag Mode"""
    if p[1] == 'BLT':
        p[1] = 'B'
        p[2] = CONDITIONS['LT']
    if p[1] == 'BLO':
        p[1] = 'B'
        p[2] = CONDITIONS['LO']
    if p[1] == 'BLE':
        p[1] = 'B'
        p[2] = CONDITIONS['LE']
    if p[1] == 'BLS':
        p[1] = 'B'
        p[2] = CONDITIONS['LS']
    if p[1] == 'BLEQ':
        p[1] = 'BL'
        p[2] = CONDITIONS['EQ']
    p[0] = (p[1], p[2], p[3], p[4])


def p_Condition(p):
    """
    Condition : EMPTY
    Condition : COND
    """
    if p[1] is None:
        p[0] = 0xE
    else:
        p[0] = p[1]


def p_Flag(p):
    """
    Flag : EMPTY
    Flag : S_FLAG
    """
    if p[1] is None:
        p[0] = 0
    else:
        p[0] = 1


def p_Mode(p):
    """
    Mode : EMPTY
    Mode : AMODE
    """
    if p[1] is None:
        p[0] = -1
    else:
        p[0] = p[1]


def p_Operands(p):
    """
    Operands : Case_1
    Operands : Case_2
    Operands : Case_3
    Operands : Case_4
    Operands : Case_5
    Operands : Case_6
    Operands : Case_7
    Operands : Case_8
    Operands : Case_9
    Operands : Case_10
    Operands : Case_11
    Operands : Case_12
    Operands : Case_13
    Operands : Case_14
    Operands : Case_15
    Operands : Case_16
    Operands : Case_17
    Operands : Case_18
    Operands : Case_19
    """
    p[0] = p[1]


def p_Case_1(p):
    """Case_1 : REGISTER COMMA REGISTER COMMA REGISTER COMMA REGISTER"""
    p[0] = (1, (p[1], p[3], p[5], p[7]))


def p_Case_2(p):
    """Case_2 : REGISTER COMMA REGISTER COMMA REGISTER Shift"""
    p[0] = (2, (p[1], p[3], p[5], p[6]))


def p_Case_3(p):
    """Case_3 : REGISTER COMMA REGISTER COMMA IMMEDIATE"""
    p[0] = (3, (p[1], p[3], p[5]))


def p_Case_4(p):
    """Case_4 : REGISTER COMMA REGISTER Shift"""
    p[0] = (4, (p[1], p[3], p[4]))


def p_Case_5(p):
    """Case_5 : REGISTER COMMA IMMEDIATE"""
    p[0] = (5, (p[1], p[3]))


def p_Case_6(p):
    """Case_6 : REGISTER COMMA ST_REG"""
    p[0] = (6, (p[1], p[3]))


def p_Case_7(p):
    """Case_7 : ST_REG_F COMMA REGISTER"""
    p[0] = (7, (p[1], p[3]))


def p_Case_8(p):
    """Case_8 : ST_REG_F COMMA IMMEDIATE"""
    p[0] = (8, (p[1], p[3]))


def p_Case_9(p):
    """Case_9 : REGISTER"""
    p[0] = (9, (p[1],))


def p_Case_10(p):
    """Case_10 : IMMEDIATE"""
    p[0] = (10, (p[1],))


def p_Case_11(p):
    """Case_11 : NUMBER"""
    p[0] = (11, (p[1],))


def p_Case_12(p):
    """Case_12 : ADDRESS"""
    if p[1] not in SYM_T.keys():
        raise Exception("Label not defined")
    p[0] = (12, (p[1], SYM_T[p[1]]))


def p_Case_13(p):
    """
    Case_13 : REGISTER COMMA LF Reg_List RF Op_Mod
    Case_13 : REGISTER EM COMMA LF Reg_List RF Op_Mod
    """
    if p[1] == 15:
        raise Exception("PC cant be Rn")
    if p[2] == ',':
        p[0] = (13, (p[1], 0, p[4], p[6]))
    else:
        p[0] = (13, (p[1], 1, p[5], p[7]))


def p_Case_14(p):
    """Case_14 : REGISTER COMMA LB REGISTER COMMA Reg_Shift_Imm RB Write_Back"""
    if p[8] and p[1] == p[4]:
        raise Exception("Rd and Rn must be distinct")
    if p[4] == 15 and p[8]:
        raise Exception("Can't update PC")
    p[0] = (14, (p[1], p[4], p[6][0], p[6][1], p[8]))


def p_Case_15(p):
    """Case_15 : REGISTER COMMA LB REGISTER COMMA IMMEDIATE RB Write_Back"""
    print(1, '\n')
    if p[8] and p[1] == p[4]:
        raise Exception("Rd and Rn must be distinct")
    if p[4] == 15 and p[8]:
        raise Exception("Can't update PC")
    p[0] = (15, (p[1], p[4], p[6], p[8]))


def p_Case_16(p):
    """Case_16 : REGISTER COMMA LB REGISTER RB Write_Back"""
    if p[6] and p[1] == p[4]:
        raise Exception("Rd and Rn must be distinct")
    if p[4] == 15 and p[6]:
        raise Exception("Can't update PC")
    p[0] = (16, (p[1], p[4], p[6]))


def p_Case_17(p):
    """Case_17 : REGISTER COMMA LB REGISTER RB COMMA IMMEDIATE"""
    p[0] = (17, (p[1], p[4], p[7]))


def p_Case_18(p):
    """Case_18 : REGISTER COMMA LB REGISTER RB COMMA Reg_Shift_Imm"""
    p[0] = (18, (p[1], p[4], p[7][0], p[7][1]))


def p_Case_19(p):
    """Case_19 : REGISTER COMMA ADDRESS"""
    if p[3] not in SYM_T.keys():
        raise Exception("Label not defined")
    p[0] = (19, (p[1], p[3], SYM_T[p[3]]))


def p_Write_Back(p):
    """
    Write_Back : EMPTY
    Write_Back : EM
    """
    if p[1] is None:
        p[0] = 0
    else:
        p[0] = 1


def p_Reg_Shift_Imm(p):
    """Reg_Shift_Imm : Negative REGISTER Shift_Imm"""
    if p[2] == 15:
        raise Exception("Rm can't be PC")
    p[0] = ((p[1], p[2]), p[3])


def p_Negative(p):
    """
    Negative : EMPTY
    Negative : HYPHEN
    """
    if p[1] is None:
        p[0] = 0
    else:
        p[0] = 1


def p_Shift_Imm(p):
    """
    Shift_Imm : EMPTY
    Shift_Imm : COMMA SHIFT_ACTION IMMEDIATE
    Shift_Imm : COMMA RRX
    """
    if p[1] is None:
        p[0] = (-1, (0, 0))
    else:
        val = 0
        if p[2] == 0:
            if p[3] == 32:
                p[3] = 0
            if p[3] < 0 or p[3] > 31:
                raise Exception("Shift Value out of bounds")
            val = p[3]
        elif p[2] in [1, 2, 3]:
            if p[3] < 0 or p[3] > 31:
                raise Exception("Shift Value out of bounds")
            val = p[3]
        elif p[2] == 4:
            p[2] = 3
            val = 0

        p[0] = (2, (p[2], val))


def p_Reg_List(p):
    """
    Reg_List : REGISTER HYPHEN REGISTER
    Reg_List : REGISTER Registers
    """
    if p[2] == '-':
        if p[1] > p[3]:
            raise Exception("r1 can't be greater than r2 in reg list")
        p[0] = []
        for i in range(p[1], p[3] + 1):
            p[0].append(i)
    else:
        p[0] = [p[1]] + p[2]
        p[0] = sorted(list(set(p[0])))


def p_Registers(p):
    """
    Registers : EMPTY
    Registers : Registers COMMA REGISTER
    """
    if p[1] is None:
        p[0] = []
    else:
        p[0] = p[1] + [p[3]]


def p_Op_Mod(p):
    """
    Op_Mod : EMPTY
    Op_Mod : CR
    """
    if p[1] is None:
        p[0] = 0
    else:
        p[0] = 1


def p_Shift_0(p):
    """
    Shift : EMPTY
    Shift : COMMA SHIFT_ACTION REGISTER
    """
    if p[1] is None:
        p[0] = (-1, (0, 0))
    else:
        p[0] = (1, (p[2], p[3]))


def p_Shift_1(p):
    """
    Shift : COMMA SHIFT_ACTION IMMEDIATE
    Shift : COMMA RRX
    """
    val = 0
    if p[2] == 0:
        if p[3] == 32:
            p[3] = 0
        if p[3] < 0 or p[3] > 31:
            raise Exception("Shift Value out of bounds")
        val = p[3]
    elif p[2] in [1, 2, 3]:
        if p[3] < 0 or p[3] > 31:
            raise Exception("Shift Value out of bounds")
        val = p[3]
    elif p[2] == 4:
        p[2] = 3
        val = 0

    p[0] = (2, (p[2], val))


def p_error(p):
    raise Exception("Syntax Error In Input '%s' " % p)


lexer = lex.lex()

parser = yacc.yacc()

if __name__ == '__main__':

    INPUT_FNAME = 'data.s'
    MID_FNAME = 'middle.txt'
    OUTPUT_FNAME = 'out.txt'

    fd = open(MID_FNAME, 'w')
    fd.close()

    fd = open(OUTPUT_FNAME, 'w')
    fd.close()

    with open(INPUT_FNAME) as f:
        lines = f.readlines()

    LC = 0x1000
    fd = open(MID_FNAME, 'a')
    for line in lines:
        line = line.upper()
        l_copy = line[:]

        while ':' in l_copy:
            index = l_copy.find(':')
            label = l_copy[:index].lstrip()
            if label[-1] == ' ':
                raise Exception('Illegal :')
            SYM_T[label] = LC
            l_copy = l_copy[index + 1:]

        line = ' ' + line

        for instruction in B_COND:
            if instruction in line and ('"' not in line or '\'' not in line):
                index = line.find(instruction)
                index += len(instruction)
                label = line[index:].strip()
                line = line[:index] + '=' + label + '\n'

        lexer.input(line)
        for tok in lexer:
            if tok.type == 'MNE':
                LC += 4
                break

        fd.write(line[1:])
    fd.close()

    with open(MID_FNAME) as f:
        lines = f.readlines()

    LC = 0x1000

    fd = open(OUTPUT_FNAME, 'a')
    lexer.lineno = 1

    for line in lines:
        if line != "\n":
            print('\n' + line)
            lexer.input(line)
            for tok in lexer:
                print(tok)
            lexer.lineno -= 1
            
        result = parser.parse(line)

        if result is not None:
            encoding = encoder(result)
            fd.write('0x' + convert_hex(convert(LC - 0x4, 32)).upper() + ' : ' +
                     encoding + ' :: ' + line)  # + str(result) + '\n\n')
        else:
            fd.write('\n')

    fd.close()
    os.remove("middle.txt")
    print('\n', SYM_T)
