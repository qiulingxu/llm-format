"""
This file is to manually generate lexer aligned parser for LLM. Will later make it automatic based on Regex and basic characters
"""
import json
from string import ascii_lowercase as alc
symbol_file = open("symbol.bnf", "w")
symbols = ""
for i in alc:
    symbols += f"U{i.upper()} : \"{i.upper()}\"\n"
    symbols += f"L{i.upper()} : \"{i}\"\n"
    #symbol_file.write(f"U{i.upper()} : \"{i.upper()}\"\n")
    #symbol_file.write(f"L{i.upper()} : \"{i}\"\n")
    
    
symbols += """BACKSLASH : "\\"
FORWARDSLASH : "/"
WS : " "
TAB : /\\t/
EOL : /[\\n\\r]/
DQ : "\""
SQ : "'"
COMMA : ","
DIGIT : /\d/
LP : "("
RP : ")"
LSB : "["
UNDERSCORE : "_"
ASTERISK : "*"
RSB : "]"
LCB : "{"
RCB : "}"
COLON : ":"
SEMICOLON : ";"
PLUS : "+"
MINUS : "-"
PERIOD : "."
QUESTION : "?"
PERCENT : "*"
TILDE : "~"
LT : "<"
EQ : "="
GT : ">"
DOLLAR : "$"\n"""
any_char = []
other_char = []
allowed_sets = {}
all_sets = set()
for i in range(255):
    all_sets.add(i)
for line in symbols.split("\n"):
    line = line.strip()
    print(line)
    line = line.split(" : ")
    any_char.append(line[0])
    repr = line[1]
    if repr.find("\"")>=0:
        repr = repr[1:-1]
    else:
        repr = repr[2:-2]
    other_char.append(repr)
    allowed_sets[line[0]] = [ord(repr)]
    all_sets.remove(ord(repr))
    
allowed_sets["OTHER_CHAR"] = list(all_sets)
open("json.allowsets",json.dumps(allowed_sets)) 

any_char.append("OTHER_CHAR")
any_char = "any_char : " + " | ".join(any_char)
symbols += any_char + "\n"
#symbols += "OTHER_CHAR : / [^" + "".join(other_char) +  "]/"
symbols += """OTHER_CHAR : /[^a-zA-Z0-9\/\\\\\\n\\r"',()[_*\]{}:;+\-.?*~<=>$]/"""
print(symbols)
#print("OTHER_CHAR : / [^" + "".join(other_char) +  "]/" )
open("symbol.bnf", "w").write(symbols)