import codecs
import string
from typing import List

from lark import Lark
from lark.lexer import Token
from lark.parsers.lalr_interactive_parser import InteractiveParser
from transformers import PreTrainedTokenizer

from .trie import Trie, TrieNode

DEBUG = True


def numbers():
    return list(string.digits)


def word():
    return list(string.ascii_letters)


class TokenFilter:
    def __init__(self, tokenizer: PreTrainedTokenizer, grammar_file):
        self.tokenizer = tokenizer
        self.grammar = open(grammar_file, "r").read()
        self.all_token = {id: token for token,
                          id in tokenizer.get_vocab().items()}
        self.all_token_ids = set()
        self.possible_char = [chr(i) for i in range(256)]
        self.grammar_file = grammar_file
        self.translation_dict = {}
        self.token2symbol = {}
        self._OTHER_CHAR_SYMBOL = "OTHER_CHAR"
        self.trie = Trie()
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
        definition = definition.strip()
        if definition.startswith("\""):
            definition = definition[1:-1]
            if definition.startswith("\\"):
                self._add_lex_rule(symbol, codecs.getdecoder(
                    "unicode_escape")(definition)[0])
            else:
                self._add_lex_rule(symbol, definition)
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
                            self.single_character_lexer(
                                symbol, f"/{definition[i:i+1]}/")
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
                self._add_lex_rule(symbol, codecs.getdecoder(
                    "unicode_escape")(definition)[0])

    def lex(self, string):
        if string in self.translation_dict:
            return [self.translation_dict[string]]
        elif string[0] in self.translation_dict:
            return [self.translation_dict[string[0]]] + self.lex(string[1:])
        else:
            self._add_lex_rule(self._OTHER_CHAR_SYMBOL, string[0])
            return self.lex(string)
            # assert False, f"Unknown character `{string[0]}` in `{string}` captured."

    def _generate_lexer(self):
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
                if symbol == symbol.upper() and symbol != self._OTHER_CHAR_SYMBOL:
                    self.add_single_character_rule(symbol, definition)

        for ch in self.possible_char:
            if ch not in self.translation_dict.keys():
                self.translation_dict[ch] = self._OTHER_CHAR_SYMBOL

        self.translation_dict.update({self.tokenizer.bos_token: "WS",
                                      self.tokenizer.eos_token: "WS",
                                      self.tokenizer.cls_token: "WS",
                                      self.tokenizer.pad_token: "WS",
                                      self.tokenizer.unk_token: "WS",
                                      self.tokenizer.sep_token: "WS"})
        if DEBUG:
            print(self.translation_dict)

    def _lexify_tokenizer(self):
        for id, llm_token in self.all_token.items():
            token_lst = self.lex(llm_token)
            self.token2symbol[id] = token_lst
            self.trie.add(token_lst, id)

    def next_token_from_string(self, prev_text: string):
        """This is for raw strings"""
        interactive = self.parser.parse_interactive(prev_text, start="start")
        result = interactive.exhaust_lexer()
        interactive = interactive.as_immutable()
        return self._prob(interactive, self.trie.root())

    def next_token_from_tokens(self, prev_token_ids: List[int]):
        """This is for LLM token ids"""
        interactive = self.parser.parse_interactive("", start="start")
        for token_id in prev_token_ids:
            if token_id not in self.all_token_ids:
                assert False, f"The token list includes unknown token {token_id}: {self.tokenizer.convert_ids_to_tokens([token_id][0])}. Please check."
            symbol_lst = self.token2symbol[token_id]
            for symbol in symbol_lst:
                lark_symbol = Token(symbol, "")
                interactive.feed_token(lark_symbol)
        interactive = interactive.as_immutable()
        result = self._prob(interactive, self.trie.root())
        print(result)
        return result

    def _prob(self, parser: InteractiveParser, trie_state: TrieNode):
        accept_token = parser.accepts()
        print(accept_token)
        next_possible_tokens = trie_state.next_possible_tokens()
        rst = []
        rst += trie_state.get_values()
        for symbol in accept_token:
            if symbol in next_possible_tokens:
                lark_symbol = Token(symbol, " ")
                rst = rst + \
                    self._prob(parser.feed_token(lark_symbol),
                               trie_state.goto(symbol))
        return rst


