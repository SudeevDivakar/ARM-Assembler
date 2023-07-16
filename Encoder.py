MNEMONICS = {'AND': 0, 'EOR': 1, 'SUB': 2, 'RSB': 3, 'ADD': 4, 'ADC': 5, 'SBC': 6, 'RSC': 7,
             'STM': 0, 'LDM': 1, 'UMULL': 0, 'UMLAL': 1, 'SMULL': 2, 'SMLAL': 3, 'B': 0, 'BL': 0,
             'TST': 0, 'TEQ': 1, 'CMP': 2, 'CMN': 3, 'ORR': 0, 'BIC': 1, 'BX': 0, 'BLX': 1, 'STRH': 0, 'LDRH': 1,
             'STR': 0, 'LDR': 1, 'STRB': 2, 'LDRB': 3, 'MOV': 0, 'MVN': 1}


def convert(num, l):
    data = bin(num)[2:]
    if len(data) > l:
        raise Exception("Somethings too big")
    if len(data) < l:
        data = '0' * (l - len(data)) + data
    return data


def convert_hex(data):
    res = ''
    while len(data):
        x = hex(int(data[:4], 2))
        data = data[4:]
        res += str(x)[2:]
    return res


def encoder(res):
    data = ''

    Location = res[0]
    Ins = res[1]
    Operands = res[2]

    Mnemonic = Ins[0]
    Condition = Ins[1]
    S_Flag = Ins[2]
    A_Mode = Ins[3]

    Op_Type = Operands[0]
    Operands = Operands[1]

    if Mnemonic in ['AND', 'EOR', 'SUB', 'RSB', 'ADD', 'ADC', 'SBC', 'RSC']:
        if A_Mode != -1:
            raise Exception("Illegal Addressing Mode")
        if Op_Type not in [2, 3]:
            raise Exception("Wrong Operands")

        data = convert(Condition, 4)

        if Op_Type == 2:
            data += convert(0, 4)
        else:
            data += convert(2, 4)

        data += convert(MNEMONICS[Mnemonic], 3)

        data += convert(S_Flag, 1)

        data += convert(Operands[1], 4)

        data += convert(Operands[0], 4)

        if Op_Type == 3:
            if Operands[2] > -1:
                if Operands[2] > 256:
                    raise Exception("Immediate is too big")
                if Operands[2] == 256:
                    data += '110000000001'
                else:
                    data += '0000' + convert(Operands[2], 7)
            else:
                if Mnemonic in ['EOR', 'RSB', 'RSC']:
                    raise Exception("Immediate can't be -ve")
                if Mnemonic == 'AND':
                    data = data[:4] + '00111100' + data[12:]
                if Mnemonic == 'SUB':
                    data = data[:8] + '1000' + data[12:]
                if Mnemonic == 'ADD':
                    data = data[:8] + '0100' + data[12:]
                if Mnemonic == 'ADC':
                    data = data[:8] + '1100' + data[12:]
                if Mnemonic == 'SBC':
                    data = data[:8] + '1010' + data[12:]
                if Operands[2] < -257:
                    raise Exception("Immediate is too small")
                if Operands[2] == -257:
                    data += '110000000001'
                else:
                    data += '0000' + convert(~Operands[2], 7)
        else:
            Rm = Operands[2]
            Shift = Operands[3]
            Sh_type = Shift[0]
            Shift = Shift[1]

            if Sh_type == 1:
                Sh_Act = Shift[0]
                Rs = Shift[1]
                data += convert(Rs, 4)
                data += '0'
                data += convert(Sh_Act, 2)
                data += '1'
            else:
                Sh_Act = Shift[0]
                Imm = Shift[1]
                data += convert(Imm, 5)
                data += convert(Sh_Act, 2)
                data += '0'

            data += convert(Rm, 4)

    elif Mnemonic in ['STM', 'LDM']:
        if S_Flag != 0:
            raise Exception("CPSR Cannot Be Set For LDM, STM Instructions")
        if Op_Type != 13:
            raise Exception("Wrong Operands")
        if A_Mode == -1:
            raise Exception("Addressing Mode Should Be Specified")

        rn = Operands[0]
        W = Operands[1]
        Reg_List = Operands[2]
        Op_Mod = Operands[3]

        data = convert(Condition, 4)
        data += '100'
        data += convert(A_Mode, 2)
        data += str(Op_Mod)
        data += str(W)
        data += str(MNEMONICS[Mnemonic])
        data += convert(rn, 4)

        for i in range(15, -1, -1):
            if i in Reg_List:
                data += '1'
            else:
                data += '0'

    elif Mnemonic in ['UMULL', 'UMLAL', 'SMULL', 'SMLAL']:
        if A_Mode != -1:
            raise Exception("Illegal Addressing Mode")
        if Op_Type not in [1]:
            raise Exception("Wrong Operands")
        data = convert(Condition, 4)

        if Op_Type == 1:
            data += convert(0, 4)
            data += convert(1, 1)
            data += convert(MNEMONICS[Mnemonic], 2)
            data += convert(S_Flag, 1)
            data += convert(Operands[1], 4)
            data += convert(Operands[0], 4)
            data += convert(Operands[3], 4)
            data += '1001'
            data += convert(Operands[2], 4)

    elif Mnemonic in ['B']:
        if A_Mode != -1:
            raise Exception("Illegal Addressing Mode")
        if Op_Type not in [12]:
            raise Exception("Wrong Operands")
        data = convert(Condition, 4)
        if Op_Type == 12:
            data += '1010'
            offset = (Operands[1] - Location - 8) // 4
            if offset < -2 ** 23 or offset >= 2 ** 23:
                raise ValueError("Offset out of range for branch instruction")
            offset = offset & 0xffffff
            data += convert(offset, 24)

    elif Mnemonic in ['BL']:
        if A_Mode != -1:
            raise Exception("Illegal Addressing Mode")
        if Op_Type not in [12]:
            raise Exception("Wrong Operands")
        data = convert(Condition, 4)
        if Op_Type == 12:
            data += '1011'
            offset = (Operands[1] - Location - 8) // 4
            if offset < -2 ** 23 or offset >= 2 ** 23:
                raise ValueError("Offset out of range for branch instruction")
            offset = offset & 0xffffff
            data += convert(offset, 24)

    elif Mnemonic in ['TST', 'TEQ', 'CMP', 'CMN']:
        if A_Mode != -1:
            raise Exception("Illegal Addressing Mode")
        if Op_Type not in [4, 5]:
            raise Exception("Wrong Operands")
        data = convert(Condition, 4)

        if Op_Type == 4:
            data += convert(1, 4)
        elif Op_Type == 5:
            data += convert(3, 4)

        data += '0'

        data += convert(MNEMONICS[Mnemonic], 2)

        data += '1'

        data += convert(Operands[0], 4)

        data += convert(0, 4)

        if Op_Type == 5:
            if Operands[1] > -1:
                if Operands[1] > 256:
                    raise Exception("Immediate is too big")
                if Operands[1] == 256:
                    data += '110000000001'
                else:
                    data += '0000' + convert(Operands[1], 8)

            else:
                if Operands[1] < -256:
                    raise Exception("Immediate is too small")
                if Mnemonic in ['TST', 'TEQ']:
                    raise Exception("Immediate can't be -ve")
                if Mnemonic in ['CMP', 'CMN']:

                    if Operands[1] > -257 and Mnemonic == 'CMP':
                        data = data[:8] + '0111' + data[12:]
                    elif Operands[1] > -257 and Mnemonic == 'CMN':
                        data = data[:8] + '0101' + data[12:]

                    if Operands[1] == -256:
                        data += '110000000001'
                    else:
                        data += '0000' + convert(-Operands[1], 8)

        else:
            Rm = Operands[1]
            Shift = Operands[2]
            Sh_type = Shift[0]
            Shift = Shift[1]

            if Sh_type == 1:
                Sh_Act = Shift[0]
                Rs = Shift[1]
                data += convert(Rs, 4)
                data += '0'
                data += convert(Sh_Act, 2)
                data += '1'
            else:
                Sh_Act = Shift[0]
                Imm = Shift[1]
                data += convert(Imm, 5)
                data += convert(Sh_Act, 2)
                data += '0'

            data += convert(Rm, 4)

    elif Mnemonic in ['ORR', 'BIC']:
        if A_Mode != -1:
            raise Exception("Illegal Addressing Mode")
        if Op_Type not in [2, 3]:
            raise Exception("Wrong Operands")
        data = convert(Condition, 4)

        if Op_Type == 2:
            data += convert(1, 4)
        elif Op_Type == 3:
            data += convert(3, 4)

        data += '1'

        data += convert(MNEMONICS[Mnemonic], 1)

        data += '0'

        data += convert(S_Flag, 1)

        data += convert(Operands[1], 4)

        data += convert(Operands[0], 4)

        if Op_Type == 3:
            if Operands[2] > -1:
                if Operands[2] > 256:
                    raise Exception("Immediate is too big")
                if Operands[2] == 256:
                    data += '110000000001'
                else:
                    data += '0000' + convert(Operands[2], 8)
            else:
                if Mnemonic == 'ORR':
                    raise Exception("Immediate can't be -ve")
                if Mnemonic == 'BIC':
                    data = data[:4] + '00100000' + data[12:]
                if Operands[2] < -257:
                    raise Exception("Immediate is too small")
                if Operands[2] == -257:
                    data += '110000000001'
                else:
                    data += '0000' + convert(~Operands[2], 8)
        else:
            Rm = Operands[2]
            Shift = Operands[3]
            Sh_type = Shift[0]
            Shift = Shift[1]

            if Sh_type == 1:
                Sh_Act = Shift[0]
                Rs = Shift[1]
                data += convert(Rs, 4)
                data += '0'
                data += convert(Sh_Act, 2)
                data += '1'
            else:
                Sh_Act = Shift[0]
                Imm = Shift[1]
                data += convert(Imm, 5)
                data += convert(Sh_Act, 2)
                data += '0'

            data += convert(Rm, 4)

    elif Mnemonic in ['MRS']:
        if A_Mode != -1:
            raise Exception("Illegal Addressing Mode")
        if Op_Type != 6:
            raise Exception("Wrong Operands")
        data = convert(Condition, 4)

        data += '0001'

        data += '0'

        data += str(Operands[1])

        data += '00'

        data += '1111'

        data += convert(Operands[0], 4)

        data += '0000'

        data += '000'

        data += '0'

        data += '0000'

    elif Mnemonic in ['MSR']:
        if A_Mode != -1:
            raise Exception("Illegal Addressing Mode")
        if Op_Type not in [7, 8]:
            raise Exception("Wrong Operands")
        data = convert(Condition, 4)

        if Op_Type == 7:
            data += convert(1, 4)
        elif Op_Type == 8:
            data += convert(3, 4)

        data += '0'

        data += str(Operands[0][0])

        data += '10'

        data += str(Operands[0][1])

        data += str(Operands[0][2])

        data += str(Operands[0][3])

        data += str(Operands[0][4])

        data += '1111'

        if Op_Type == 8:
            if Operands[1] > -1:
                if Operands[1] > 256:
                    raise Exception("Immediate is too big")
                if Operands[1] == 256:
                    data += '110000000001'
                else:
                    data += '0000' + convert(Operands[1], 8)
            else:
                raise Exception("Immediate can't be -ve")

        elif Op_Type == 7:
            data += '0000'

            data += '000'

            data += '0'

            data += convert(Operands[1], 4)

    elif Mnemonic in ['BX', 'BLX']:
        if A_Mode != -1:
            raise Exception("Illegal Addressing Mode")
        if Op_Type != 9:
            raise Exception("Wrong Operands")
        data = convert(Condition, 4)

        data += '0001001011111111111100'
        data += convert(MNEMONICS[Mnemonic], 1)
        data += '1'
        data += convert(Operands[0], 4)

    elif Mnemonic in ['STR', 'LDR', 'STRB', 'LDRB']:
        if A_Mode != -1:
            raise Exception("Illegal Addressing Mode")
        if Op_Type not in [15, 17, 16, 18, 14]:
            raise Exception("Wrong Operands")
        data = convert(Condition, 4)

        if Op_Type == 17:
            data += '0100'
            temp = convert(MNEMONICS[Mnemonic], 2)
            if -1 < Operands[2] < 4096:
                data += '1'
                data += temp[0]
                data += '0'
                data += temp[1]
                data += convert(Operands[1], 4)
                data += convert(Operands[0], 4)
                data += convert(Operands[2], 12)
            elif 0 > Operands[2] > -4096:
                data += '0'
                data += temp[0]
                data += '0'
                data += temp[1]
                data += convert(Operands[1], 4)
                data += convert(Operands[0], 4)
                data += convert(-Operands[2], 12)
            else:
                raise Exception("Immediate value out of bounds")

        elif Op_Type == 15:
            data += '0101'
            temp = convert(MNEMONICS[Mnemonic], 2)
            if -1 < Operands[2] < 4096:
                data += '1'
                data += temp[0]
                data += convert(Operands[3], 1)
                data += temp[1]
                data += convert(Operands[1], 4)
                data += convert(Operands[0], 4)
                data += convert(Operands[2], 12)
            elif 0 > Operands[2] > -4096:
                data += '0'
                data += temp[0]
                data += convert(Operands[3], 1)
                data += temp[1]
                data += convert(Operands[1], 4)
                data += convert(Operands[0], 4)
                data += convert(-Operands[2], 12)
            else:
                raise Exception("Immediate value out of bounds")

        elif Op_Type == 16:
            if Operands[2] == 1:
                raise Exception("Unexpected !")
            data += '0101'
            temp = convert(MNEMONICS[Mnemonic], 2)
            data += '1'
            data += temp[0]
            data += '0'
            data += temp[1]
            data += convert(Operands[1], 4)
            data += convert(Operands[0], 4)
            data += '000000000000'

        elif Op_Type == 18:
            data += '0110'
            temp = convert(MNEMONICS[Mnemonic], 2)
            if Operands[2][0] == 0:
                data += '1'
                data += temp[0]
                data += '0'
                data += temp[1]
            else:
                data += '0'
                data += temp[0]
                data += '0'
                data += temp[1]

            data += convert(Operands[1], 4)
            data += convert(Operands[0], 4)

            Rm = Operands[2][1]
            Shift = Operands[3]
            Shift = Shift[1]
            Sh_Act = Shift[0]
            Imm = Shift[1]
            data += convert(Imm, 5)
            data += convert(Sh_Act, 2)
            data += '0'
            data += convert(Rm, 4)

        elif Op_Type == 14:
            data += '0111'
            temp = convert(MNEMONICS[Mnemonic], 2)
            if Operands[2][0] == 0:
                data += '1'
                data += temp[0]
                data += convert(Operands[4], 1)
                data += temp[1]
            else:
                data += '0'
                data += temp[0]
                data += convert(Operands[4], 1)
                data += temp[1]

            data += convert(Operands[1], 4)
            data += convert(Operands[0], 4)

            Rm = Operands[2][1]
            Shift = Operands[3]
            Shift = Shift[1]
            Sh_Act = Shift[0]
            Imm = Shift[1]
            data += convert(Imm, 5)
            data += convert(Sh_Act, 2)
            data += '0'
            data += convert(Rm, 4)

    elif Mnemonic in ['STRH', 'LDRH']:
        if A_Mode != -1:
            raise Exception("Illegal Addressing Mode")
        if Op_Type not in [14, 15, 16, 17, 18]:
            raise Exception("Wrong Operands")
        data = convert(Condition, 4)
        if Op_Type == 16:
            if Operands[2] == 1:
                raise Exception("Unexpected !")
            data += '0000'
            data += '000'
            data += convert(MNEMONICS[Mnemonic], 1)
            data += convert(Operands[1], 4)
            data += convert(Operands[0], 4)
            data += '000010110000'
        elif Op_Type == 14 or Op_Type == 18:
            if Operands[3][0] != -1:
                raise Exception("Cant Shift in STRH or LDRH")
        elif Op_Type == 17 or Op_Type == 18:
            data += '0000'
            data += '000'
            data += convert(MNEMONICS[Mnemonic], 1)
            data += '00010000000010110000'
        else:
            data += convert(1, 4)
            if Op_Type == 14 and Operands[2][0] == 0:
                data += '10'
                data += convert(Operands[4], 1)
            elif Op_Type == 14 and Operands[2][0] == 1:
                data += '00'
                data += convert(Operands[4], 1)
            elif Op_Type == 15 and 0 > Operands[2] > -256:
                data += '01'
                data += convert(Operands[3], 1)
            elif Op_Type == 15 and -1 < Operands[2] < 256:
                data += '11'
                data += convert(Operands[3], 1)
            elif Op_Type == 15 and Operands[2] < -256 or Operands[2] > 256:
                raise Exception("Immediate value out of bounds")
            data += convert(MNEMONICS[Mnemonic], 1)
            data += convert(Operands[1], 4)
            data += convert(Operands[0], 4)
            if Op_Type == 14:
                data += '00001011'
                data += convert(Operands[2][1], 4)
            elif Op_Type == 15 and Operands[2] > -1:
                temp = convert(Operands[2], 8)
                data += temp[:4]
                data += '1011'
                data += temp[4:]
            elif Op_Type == 15 and Operands[2] < 0:
                temp = convert(-Operands[2], 8)
                data += temp[:4]
                data += '1011'
                data += temp[4:]

    elif Mnemonic in ["CLZ"]:
        if Op_Type != 4:
            raise Exception("Wrong Operand Type")
        else:
            Shift = Operands[2]
            Sh_type = Shift[0]
            if A_Mode != -1:
                raise Exception("Illegal Addressing Mode")
            if Op_Type == 4 and Sh_type != -1:
                raise Exception("Wrong Operands")

        data = convert(Condition, 4)
        data += '000101101111'
        data += convert(Operands[0], 4)
        data += '11110001'
        data += convert(Operands[1], 4)

    elif Mnemonic in ["SWI"]:
        if Op_Type != 11:
            raise Exception("Wrong Operand Type")
        else:
            if A_Mode != -1:
                raise Exception("Illegal Addressing Mode")

        data = convert(Condition, 4)
        data += "1111"
        data += convert(Operands[0], 24)

    elif Mnemonic in ["MUL"]:
        if Op_Type != 2:
            raise Exception("Wrong Operand Type")
        else:
            Shift = Operands[3]
            Sh_type = Shift[0]
            if A_Mode != -1:
                raise Exception("Illegal Addressing Mode")
            if Op_Type == 2 and Sh_type != -1:
                raise Exception("Wrong Operands")

        data = convert(Condition, 4)
        data += "0000000"
        data += str(S_Flag)
        data += convert(Operands[0], 4)
        data += "0000"
        data += convert(Operands[2], 4)
        data += "1001"
        data += convert(Operands[1], 4)

    elif Mnemonic in ["MLA"]:
        if Op_Type != 1:
            raise Exception("Wrong Operand Type")
        else:
            if A_Mode != -1:
                raise Exception("Illegal Addressing Mode")

        data = convert(Condition, 4)
        data += "0000001"
        data += str(S_Flag)
        data += convert(Operands[0], 4)
        data += convert(Operands[3], 4)
        data += convert(Operands[2], 4)
        data += "1001"
        data += convert(Operands[1], 4)

    elif Mnemonic in ['MOV', 'MVN']:

        if A_Mode != -1:
            raise Exception("Illegal Addressing Mode")
        if Op_Type not in [4, 5]:
            raise Exception("Wrong Operands")

        data = convert(Condition, 4)

        if Op_Type == 5:
            data += '0011'
            if Operands[1] < -257 or Operands[1] > 256:
                raise Exception("Immediate value out of bounds")

            cond1 = Mnemonic == 'MOV' and -1 < Operands[1] < 257
            cond2 = Mnemonic == 'MVN' and -1 < Operands[1] < 257
            cond3 = Mnemonic == 'MOV' and -258 < Operands[1] < 0
            cond4 = Mnemonic == 'MVN' and -258 < Operands[1] < 0

            if cond1 or cond4:
                data += '1010'

            elif cond2 or cond3:
                data += '1110'

            data += '0000'
            data += convert(Operands[0], 4)
            if 0 > Operands[1] > -257:
                data += '0000'
                data += convert(-(Operands[1]) - 1, 8)
            elif -1 < Operands[1] < 256:
                data += '0000'
                data += convert(Operands[1], 8)
            elif Operands[1] in [256, -257]:
                data += '110000000001'
        elif Op_Type == 4:
            data += convert(1, 4)
            if Mnemonic == 'MOV':
                data += '1010'
            else:
                data += '1110'

            data += '0000'
            data += convert(Operands[0], 4)
            Rm = Operands[1]
            Shift = Operands[2]
            Sh_type = Shift[0]
            Shift = Shift[1]

            if Sh_type == 1:
                Sh_Act = Shift[0]
                Rs = Shift[1]
                data += convert(Rs, 4)
                data += '0'
                data += convert(Sh_Act, 2)
                data += '1'
            else:
                Sh_Act = Shift[0]
                Imm = Shift[1]
                data += convert(Imm, 5)
                data += convert(Sh_Act, 2)
                data += '0'

            data += convert(Rm, 4)

    return '0x' + convert_hex(data).upper()
