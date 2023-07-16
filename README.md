# ARM7TDMI-Assembler
This project inputs commands used in the **ARM7TDMI** architecture and converts them into eight bit hexadecimal values which are used by ARM to decode instructions furthur. 

File description : 
* data.s : Commands to be encoded into an eight bit hexadecimal value are entered here.
* out.txt : The commands along with their encoded values are presented here.
* Assembler.py - Tokenizes commands and creates tuples containing information about the given instruction. It passes these commands to Encoder.py and outputs the hexadecimal value into the out.txt file.   
* Encoder.py : Converts the respective commands into their corresponding hexadecimal values


