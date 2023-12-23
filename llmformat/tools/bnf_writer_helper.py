_OTHER_CHAR_SYMBOL = "OTHER_CHAR"
grammar_file = "./llmformat/json_min.bnf"
with open(grammar_file, "r") as file:
    all_chars = []
    for line in file.read().split("\n"):
        line = line.strip()
        if line.startswith("#") or line.startswith("\\") or line.startswith("//"):
            continue
        pos = line.find(":")
        if pos == -1:
            continue
        symbol = line[:pos].strip()
        definition = line[pos+1:].strip()
        # Capitalized symbol is token in grammar
        if symbol == symbol.upper() and symbol != _OTHER_CHAR_SYMBOL:
            all_chars.append(symbol)
    all_chars = f"all_chars : {'|'.join(all_chars)}"
    print(all_chars)