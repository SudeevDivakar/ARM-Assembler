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
    pass