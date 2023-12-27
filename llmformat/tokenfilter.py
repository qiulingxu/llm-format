import codecs
import string
from itertools import chain
from typing import List, Optional

from lark import Lark
from lark.exceptions import UnexpectedToken
from lark.lexer import Token
from lark.parsers.lalr_interactive_parser import InteractiveParser
from lark.parsers.lalr_parser_state import ParserState
from transformers import PreTrainedTokenizer

from .constant import _OTHER_CHAR_SYMBOL, _SPECIAL_TOKENS
from .larkopt.lark_parser import FastInteractiveParser, SimpleUnexpectedToken
from .lex_helper import symbol_character_parse
from .trie import Trie, TrieNode

DEBUG = True


class TokenFilter:
    def __init__(self,
                 tokenizer: PreTrainedTokenizer, 
                 grammar_file : str,
                 memorize_state : bool = True):
        self.tokenizer = tokenizer
        self.grammar = open(grammar_file, "r").read()
        self.all_token = {id:token for token,
                          id in tokenizer.get_vocab().items()}
        self.all_token_ids = set()
        self.possible_char = [chr(i) for i in range(256)]
        self.grammar_file = grammar_file
        self.translation_dict = {}
        self.token2symbol = {}
        self.trie = Trie()
        self.memorize_state = memorize_state
        if self.memorize_state:
            self.accept_symbol_memory = {}
            self.accept_token_memory = {}
        self.parser = Lark(self.grammar, parser='lalr',
                           lexer='basic',
                           # Disabling propagate_positions and placeholders slightly improves speed
                           propagate_positions=False,
                           maybe_placeholders=False,
                           # Using an internal transformer is faster and more memory efficient
                           start='start')
        self.init()

    def init(self):
        self._generate_lexer()
        self._lexify_tokenizer()
        print(f"In total {self.trie.size} nodes Trie created.")
        self.all_token_ids = set(self.token2symbol.keys())
    def _add_lex_rule(self, symbol, ch):
        if ch in self.translation_dict:
            assert False, f"Found conflicting lexer definition, where {ch} can be either {self.translation_dict[ch]} or {symbol}."
        if len(ch) != 1:
            assert False, f"Found symbol composed by more than one characters. Only 1-length character is allowed to ensure soundness."
        self.translation_dict[ch] = symbol

    def add_single_character_rule(self, symbol, definition):
        """This will parse lexical rules for token in EBNF file."""
        symbol_character_parse(symbol, definition, self._add_lex_rule)

    def lex(self, string: Optional[str] = None, token_name: Optional[str] = None) -> List[str]:
        """Lexify a string."""
        assert (string is None) ^ (token_name is None), "Lexer takes either token name or a string"
        if token_name is not None and token_name in self.translation_dict:
            """We directly translate special tokens into lexer tokens"""
            return [self.translation_dict[token_name]]
        else:
            if string is None:
                string = self.tokenizer.convert_tokens_to_string([token_name])
            """Handle the case for string"""
            if len(string) == 0:
                """For any unprintable token, treat them as a white space in lexer."""
                token_name = _OTHER_CHAR_SYMBOL
                return [token_name]
            elif string[0] in self.translation_dict:
                if len(string) > 1:
                    return [self.translation_dict[string[0]]] + self.lex(string[1:])
                else:
                    return [self.translation_dict[string[0]]]
            else:
                self._add_lex_rule(_OTHER_CHAR_SYMBOL, string[0])
                return self.lex(string)
                # assert False, f"Unknown character `{string[0]}` in `{string}` captured."

    def _generate_lexer(self):
        """Generate minimal lexer that is consistent with tokenizer."""
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
                if symbol == symbol.upper() and symbol not in _SPECIAL_TOKENS:
                    self.add_single_character_rule(symbol, definition)

        for ch in self.possible_char:
            if ch not in self.translation_dict.keys():
                self.translation_dict[ch] = _OTHER_CHAR_SYMBOL

        self.translation_dict.update({self.tokenizer.bos_token: "WS",
                                      self.tokenizer.eos_token: "EOS",
                                      self.tokenizer.cls_token: "WS",
                                      self.tokenizer.pad_token: "WS",
                                      self.tokenizer.unk_token: "WS",
                                      self.tokenizer.sep_token: "WS"})
        if DEBUG:
            print(self.translation_dict)

    def _lexify_tokenizer(self):
        """Lexify all strings in tokenizer."""
        for id, llm_token in self.all_token.items():
            token_lst = self.lex(token_name=llm_token)
            self.token2symbol[id] = token_lst
            self.trie.add(token_lst, id)

    def next_token_from_string(self, prev_text: string):
        """This is for raw strings"""
        interactive = self.parser.parse_interactive(prev_text, start="start")
        interactive = FastInteractiveParser.copyfrom(interactive)
        interactive.exhaust_lexer()
        interactive = interactive.as_immutable()
        print(interactive.accepts())
        return list(self._prob(interactive, self.trie.root()))

    def next_token_from_tokens(self, prev_token_ids: List[int]):
        """This is for LLM token ids"""
        interactive = self.parser.parse_interactive("", start="start")
        interactive = FastInteractiveParser.copyfrom(interactive)
        for token_id in prev_token_ids:
            #if token_id not in self.all_token_ids:
            #    assert False, f"The token list includes unknown token {token_id}: {self.tokenizer.convert_ids_to_tokens([token_id][0])}. Please check."
            symbol_lst = self.token2symbol[token_id]
            for symbol in symbol_lst:
                lark_symbol = Token(symbol, "")
                interactive.feed_token(lark_symbol)
        interactive = interactive.as_immutable()
        if self.memorize_state:
            parser_state_hash = self._hash_parser_state(interactive.parser_state)
            if parser_state_hash not in self.accept_token_memory:
                self.accept_token_memory[parser_state_hash] = list(self._prob(interactive, self.trie.root()))
            result = self.accept_token_memory[parser_state_hash]
        else:
            result = list(self._prob(interactive, self.trie.root()))
        return result

    def _hash_parser_state(self, parser_state:ParserState, trie_state: TrieNode = None):
        if trie_state is not None:
            return hash((tuple(parser_state.state_stack), trie_state.repr()))
        else:
            return hash((tuple(parser_state.state_stack)))
        

    def _prob(self, parser: InteractiveParser, trie_state: TrieNode, depth=0):

        next_possible_tokens = trie_state.next_possible_tokens()
        rst = trie_state.get_values()
        

        """
        parser_state_hash = self._hash_parser_state(parser.parser_state, trie_state)
        choices = {}
        if self.memorize_state:
            if parser_state_hash not in self.accept_symbol_memory:
                choices = parser.accepts()
                valid_choices = set()
                for symbol in choices:
                    if symbol in  next_possible_tokens:
                        valid_choices.add(symbol)
                self.accept_symbol_memory[parser_state_hash] = valid_choices
                
            choices = self.accept_symbol_memory[parser_state_hash]
            for symbol in choices:
                lark_symbol = parser.lexer_thread._Token(symbol, '')
                next_state = parser.feed_token(lark_symbol)
                part_result = \
                    self._prob(next_state,
                            trie_state.goto(symbol))
                rst = chain(rst, part_result)
        else:"""
        for symbol in parser.choices():
            if symbol.isupper() and symbol in next_possible_tokens:
                lark_symbol =Token(symbol, '')
                try:
                    next_state = parser.feed_token(lark_symbol)
                    #print(f"s:{symbol} {depth}", end="\t")
                    part_result = \
                        self._prob(next_state,
                            trie_state.goto(symbol), depth=depth+1)
                    rst= chain(rst, part_result)      
                except SimpleUnexpectedToken:
                    pass              
        #print(f"v: {self.tokenizer.convert_ids_to_tokens(rst)} {depth}", end="\t")
        return rst


