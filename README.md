# ARM7TDMI-Assembler
This project inputs commands used in the **ARM7TDMI** architecture and converts them into eight bit hexadecimal values which are used by ARM to decode instructions furthur. 

<br>

**File description :**
* data.s : Commands to be encoded into an eight bit hexadecimal value are entered here.
* out.txt : The commands along with their encoded values are presented here.
* Assembler.py - Tokenizes commands and creates tuples containing information about the given instruction. It passes these commands to Encoder.py and outputs the hexadecimal value into the out.txt file.   
* Encoder.py : Converts the respective commands into their corresponding hexadecimal values

<br>

**To run :**
* Add instructions to data.s
* Run Assembler.py
  
  ```python Assembler.py``` or ```python3 Assembler.py```
* Open out.txt to view the corresponding encoded values

<br>

**Instructions Supported:**

ADC | ADD | AND | B | BIC | BL | BLX | BX | CLZ | CMN | CMP | EOR | LDM |
LDR | LDRB | LDRH | MLA | MOV | MRS | MSR | MUL | MVN | ORR | RSB | RSC | SBC |
SMULL | SMLAL | STM | STR | STRB | STRH | SUB | SWI | TEQ | TST | UMLAL | UMULL
