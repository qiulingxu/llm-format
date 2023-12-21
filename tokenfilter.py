from transformers import PreTrainedTokenizer
from lark import Lark
import string
from trie import TRIE_node, TRIE
from lark.parsers.lalr_interactive_parser import InteractiveParser


def numbers():
    return list(string.digits)

def word():
    return list(string.ascii_letters)

class TokenFilter:
    def __init__(self, tokenizer: PreTrainedTokenizer, grammar_file):
        self.tokenizer = tokenizer
        self.all_token = {id : token for token, id in tokenizer.get_vocab().items()}
        self.lookup = self.build_trie()
        self.possible_char = [ord(i) for i in range(256)]
        self.grammar_file = grammar_file
        self.translation_dict = {}
        self._OTHER_CHAR_SYMBOL = "OTHER_CHAR"
        self.trie = TRIE()
        
    def init(self):
        self.parse_grammar_for_lexer()
        
        
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
        if definition.startswith("\""):
            definition = definition[1:-1]
        elif definition.startwith("/"):
            definition = definition[1:-1]
            if definition.startswith("["):
                if definition.startswith("^"):
                    assert False, "We currently don't support ^ syntax. The token `OTHER_CHAR` will be automatically generated and represent all other possible characters."
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
                self._add_lex_rule(symbol, definition.decode('string_escape'))

    def lex(self, string):
        if string in self.translation_dict:
            return [self.translation_dict]
        elif string[0] in self.translation_dict:
            return [self.translation_dict[0]] + self.lex(string[1:])
        else:
            assert False, f"Unknown character in token {string} captured."
        
    def parse_grammar_for_lexer(self):
        with open(self.grammar_file, "r") as file:
            
            for line in file.read.split("\n"):
                pos = line.find(":")
                if pos == -1:
                    continue
                symbol = line[:pos].strip()
                definition = line[pos+1:].strip()
                # Capitalized symbol is token in grammar
                if symbol == symbol.captialize() and symbol !=  self._OTHER_CHAR_SYMBOL:
                    self.add_single_character_rule(symbol, definition)
                
        for ch in self.possible_char:
            if ch not in self.translation_dict:
                self.translation_dict[ch] = self._OTHER_CHAR_SYMBOL
                
        self.translation_dict.update({self.tokenizer.bos_token : "WS", 
                         self.tokenizer.eos_token : "EOS", 
                         self.tokenizer.cls_token : "WS", 
                         self.tokenizer.pad_token : "WS", 
                         self.tokenizer.unk_token : "WS",
                         self.tokenizer.sep_token : "WS"})
        
    def lex_tokenizer(self):
        for id, llm_token in self.all_token.items(): 
            token_lst = self.lex(llm_token)
            self.trie.add(token_lst, id)
            
    def check_context(self, prev_text):
        interactive = self.parser.parse_interactive(prev_text, start="start")
        interactive.exhaust_lexer()
        return self._prob(interactive, self.trie.root())
        

    def _prob(self, parser : InteractiveParser, trie_state : TRIE_node):
        accept_token = parser.accepts()
        next_possible_tokens = trie_state.next_possible_tokens()
        rst = []
        
        for token in accept_token:
            if token in next_possible_tokens:
                rst += trie_state.values()
                rst = rst + self._prob(parser.copy(), trie_state.goto(token))
        return rst



    
