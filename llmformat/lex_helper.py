import codecs
import string
from typing import Callable


def numbers():
    return list(string.digits)

def word():
    return list(string.ascii_letters)

def symbol_character_parse(symbol : str, definition : str, op: Callable[[str, str], None]) -> None :
    """Gives the symbo : definition. Extract every possible character ch in definition and call op(symbol, ch)."""
    definition = definition.strip()
    if definition.startswith("\""):
        definition = definition[1:-1]
        if definition.startswith("\\"):
            op(symbol, codecs.getdecoder(
                "unicode_escape")(definition)[0])
        else:
            op(symbol, definition)
    elif definition.startswith("/"):
        definition = definition[1:-1]
        if definition.startswith("["):
            if definition.startswith("^"):
                assert False, "We currently don't support ^ syntax. The token `OTHER_CHAR` will represent all other possible characters and it is automatically generated."
            else:
                definition = definition[1:-1]
                i = 0
                while (i < len(definition)):
                    if definition[i] == "\\":
                        symbol_character_parse(
                            symbol, f"/{definition[i:i+1]}/", op)
                        i = i + 2
                    else:
                        op(symbol, definition[i])
                        i = i + 1
        if definition == "\\w":
            for ch in word() + numbers() + ["_"]:
                op(symbol, ch)
        elif definition == "\\d":
            for ch in numbers():
                op(symbol, ch)
        elif definition == "\\s":
            for ch in ["\t", "\n", "\r"]:
                op(symbol, ch)
        elif definition.startswith("\\"):
            op(symbol, codecs.getdecoder(
                "unicode_escape")(definition)[0])