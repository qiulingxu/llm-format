from transformers import PreTrainedTokenizer
import string
import codecs
from trie import TrieNode, Trie
from lark import Lark
from lark.parsers.lalr_interactive_parser import InteractiveParser
from lark.lexer import Token

DEBUG = True

def numbers():
    return list(string.digits)

def word():
    return list(string.ascii_letters)

class TokenFilter:
    def __init__(self, tokenizer: PreTrainedTokenizer, grammar_file):
        self.tokenizer = tokenizer
        self.grammar = open(grammar_file, "r").read()
        self.all_token = {id : token for token, id in tokenizer.get_vocab().items()}
        self.possible_char = [chr(i) for i in range(256)]
        self.grammar_file = grammar_file
        self.translation_dict = {}
        self._OTHER_CHAR_SYMBOL = "OTHER_CHAR"
        self.trie = Trie()
        self.parser = Lark(self.grammar, parser='lalr',
            lexer='basic',
            # Disabling propagate_positions and placeholders slightly improves speed
            propagate_positions=False,
            maybe_placeholders=False,
            # Using an internal transformer is faster and more memory efficient
            start='start')
        
    def init(self):
        self.parse_grammar_for_lexer()
        self.lexify_tokenizer()
        
        
    def grammar_tokenize(self):
        pass
    
    def _add_lex_rule(self, symbol, ch):
        if ch in self.translation_dict:
            assert False, f"Found conflicting lexer definition, where {ch} can be either {self.translation_dict[ch]} or {symbol}."
        if len(ch)!=1:
            assert False, f"Found symbol composed by more than one characters. Only 1-length character is allowed to ensure soundness."
        self.translation_dict[ch] = symbol
        
        
    def add_single_character_rule(self, symbol, definition):
        """This will parse lexical rules for token in EBNF file."""
        definition = definition.strip()
        if definition.startswith("\""):
            definition = definition[1:-1]
            if definition.startswith("\\"):
                self._add_lex_rule(symbol, codecs.getdecoder("unicode_escape")(definition)[0])
            else:                      
                self._add_lex_rule(symbol, definition)
        elif definition.startswith("/"):
            definition = definition[1:-1]
            if definition.startswith("["):
                if definition.startswith("^"):
                    assert False, "We currently don't support ^ syntax. The token `OTHER_CHAR` will represent all other possible characters and it is automatically generated."
                else:
                    definition = definition[1:-1]
                    i=0
                    while (i< len(definition)):
                        if definition[i] == "\\":
                            self.single_character_lexer(symbol, f"/{definition[i:i+1]}/")
                            i = i + 2
                        else:
                            self._add_lex_rule(symbol, definition[i])
                            i = i + 1
            if definition == "\\w":
                for ch in word() + numbers() + ["_"]:
                    self._add_lex_rule(symbol, ch)
            elif definition == "\\d":
                for ch in numbers():
                    self._add_lex_rule(symbol, ch)
            elif definition == "\\s":
                for ch in ["\t", "\n", "\r"]:
                    self._add_lex_rule(symbol, ch)  
            elif definition.startswith("\\"):
                self._add_lex_rule(symbol, codecs.getdecoder("unicode_escape")(definition)[0])

    def lex(self, string):
        if string in self.translation_dict:
            return [self.translation_dict[string]]
        elif string[0] in self.translation_dict:
            return [self.translation_dict[string[0]]] + self.lex(string[1:])
        else:
            self._add_lex_rule(self._OTHER_CHAR_SYMBOL,string[0])
            return self.lex(string)
            #assert False, f"Unknown character `{string[0]}` in `{string}` captured."
        
    def parse_grammar_for_lexer(self):
        with open(self.grammar_file, "r") as file:
            
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
                if symbol == symbol.upper() and symbol !=  self._OTHER_CHAR_SYMBOL:
                    self.add_single_character_rule(symbol, definition)
                
        for ch in self.possible_char:
            if ch not in self.translation_dict.keys():
                self.translation_dict[ch] = self._OTHER_CHAR_SYMBOL
                
        self.translation_dict.update({self.tokenizer.bos_token : "WS", 
                         self.tokenizer.eos_token : "EOS", 
                         self.tokenizer.cls_token : "WS", 
                         self.tokenizer.pad_token : "WS", 
                         self.tokenizer.unk_token : "WS",
                         self.tokenizer.sep_token : "WS"})
        if DEBUG:
            print(self.translation_dict)
        
    def lexify_tokenizer(self):
        for id, llm_token in self.all_token.items(): 
            token_lst = self.lex(llm_token)
            self.trie.add(token_lst, id)
            
    def check_context(self, prev_text):
        interactive = self.parser.parse_interactive(prev_text, start="start")
        result = interactive.exhaust_lexer()
        interactive = interactive.as_immutable()
        return self._prob(interactive, self.trie.root())
        

    def _prob(self, parser : InteractiveParser, trie_state : TrieNode):
        accept_token = parser.accepts()
        next_possible_tokens = trie_state.next_possible_tokens()
        rst = []
        rst += trie_state.get_values()
        for token in accept_token:
            if token in next_possible_tokens:
                lark_token = Token(token, " ")
                rst = rst + self._prob(parser.feed_token(lark_token), trie_state.goto(token))
        return rst


if __name__ == "__main__":
    
    from transformers import LlamaForCausalLM, AutoTokenizer
    local_os_tokenizer_dir = "../tokenizer"
    tokenizer = tokenizer = AutoTokenizer.from_pretrained(local_os_tokenizer_dir)
    
    token_filter = TokenFilter(tokenizer, "json.bnf")
    token_filter.init()
    possible_token_ids = token_filter.check_context("""{"abc":"\\\\" ,"c":2.31e+""")
    for i in possible_token_ids:
        string = tokenizer.convert_ids_to_tokens([i])
        print(string, token_filter.lex(string[0]))
    #model = LlamaForCausalLM.from_pretrained()
    
    
