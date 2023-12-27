from abc import ABC
from os import path
from typing import Dict, List, Optional, Tuple

from .grammar_files.grammar_constant import parse_lex_definition

_default_rule_manage = None

class Rule(str):
    def __init(self, string, name : Optional[str] = None):
        super.__init__(string)
        self.name = name
    
    @property
    def name(self):
        return self.name

class RuleManager():
    def __init__(self, basefile = None, rules : Optional[Dict[str, str]] = None):
        
        if basefile is None:
            basepath = path.dirname(__file__)
            filepath = path.abspath(path.join(basepath, "..", "grammar_files", "base.bnf"))
        self.symbol2def, self.char2symbol = parse_lex_definition(filepath)
        if rules is None:
            self.rules = []
        self.rules = rules
        global _default_rule_manage
        if _default_rule_manage is not None:
            raise ValueError("RuleManager doesn not support initialize twice.")
        _default_rule_manage = RuleManager
    
    def get_rule(self, rule_name : str) -> str:
        if rule_name not in self.rules:
            raise KeyError(f"{rule_name} is not found in rules.")
        return rule_name
    
    def add_rule(self, rule_name, rule_def) -> None:
        if rule_name not in self.rules:
            self.rules = rule_name
        else:
            if self.rules[rule_name] != rule_def:
                raise ValueError(f"Rule {rule_name} has conflicting definitions `{self.rules[rule_name]}` and `{rule_def}`")
    
    def add_rules(self, rules: List[Tuple(str, str)]) -> None:
        for rule_name, rule in rules:
            self.add_rule(rule_name, rule)
    
class BaseFormat():
    def __init__(self, context:Optional[RuleManager] = None):
        if context is None:
            global _default_rule_manage
            context = _default_rule_manage
        self.context = context
    
    @property
    def symbol(self):
        return self.rules.keys()
    
    @property
    def definition(self):
        return self.rules.values()

    @staticmethod
    def rule_for_or(lst_of_rules:List[str]) -> str:
        lst = ["(" + rule + ")" for rule in lst_of_rules]
        return Rule("|".join(lst))
        
    @staticmethod
    def rule_for_string(string:str) -> str:
        context = _default_rule_manage
        lst = []
        for ch in string:
            if ch not in context.char2symbol:
                raise KeyError(f"{ch} not found in token definition base.bnf")
            lst += context.char2symbol[ch]
        return Rule(" ".join(lst))
    
    @staticmethod
    def rule_for_adding_quotes(rule:str, quotes_str: List[Tuple(str, str)]) -> str:
        """_summary_

        Args:
            string (str): the rule for enclosed content
            quotes_str (List[Tuple): A list of possible quotes. Each tuple indicates rule for left quote and rule for right quote

        Returns:
            str: _description_
        """
        lst_of_rules = []
        for rule_left_quote, rule_right_quote in quotes_str:
            lst_of_rules += " ".join([rule_left_quote, rule, rule_right_quote])
        return BaseFormat.rule_for_or(lst_of_rules)


    @staticmethod
    def token_for_other_char():
        escapped_chars = ["\"", "]", "/", "-"]
    
    @staticmethod
    def rule_for_any_char(exclude_char : Optional[List[str]] = None, exclude_symbol: Optional[List[str]] = None):
        context = _default_rule_manage
        char_to_symbol = context.char2symbol
        lst_of_symbols = set()
        if exclude_char is not None:
            for char in exclude_char:
                if char not in char_to_symbol:
                    raise(KeyError(f"`{char}` not Found in char_to_symbol. A symbol definition is required before exclusion."))
        else:
            exclude_char = []
        for char in char_to_symbol:
            if char not in exclude_char and char_to_symbol[char] not in exclude_symbol:
                lst_of_symbols.add(char_to_symbol[char])
        rule = " ".join(list(lst_of_symbols))
        return rule
    
    @staticmethod
    def chars_to_symbol(lst_chars: List[str]) -> List[str]:
        context = _default_rule_manage
        result = []
        for char in lst_chars:
            result.append(context.char2symbol[char])
        return result
    
    @staticmethod
    def string_to_symbol(string: str) -> str:
        return " ".join(BaseFormat.chars_to_symbol(string))
    
class QuotedStringFormat(BaseFormat):
    def __init__(self, rule_name: str ,fixed_string : bool, string : Optional[str] = None, allowed_quotes : List[Tuple(str, str)] = None, context=None):
        super().__init__()
        self.rule_name = rule_name
        self.fixed_string = fixed_string
        self.string = string
        
        if allowed_quotes is None:
            allowed_quotes = [("\"", "\""), ("\'", "\'")]
            
        self.allowed_quotes = allowed_quotes
        self.definition = self.build_def()
        
    def build_def(self):
        if self.fixed_string:
            if self.string is None:
                raise ValueError(f"string can not be None when fixed_string option is on.")
            rule = QuotedStringFormat.rule_for_adding_quotes(self.string)
        else:
            # This is the char without quote
            rules = []
            for left_quote, right_quote in self.allowed_quotes:
                if left_quote == right_quote:
                    left_quote_name = self.context.char2symbol[left_quote]
                    right_quote_name = left_quote_name
                    quote_name = left_quote_name.lower()
                    escape_set = [left_quote, "\\"]
                else:
                    left_quote_name = self.context.char2symbol[left_quote]
                    right_quote_name = self.context.char2symbol[right_quote]
                    quote_name = f"{left_quote_name}_{right_quote_name}".lower()
                    escape_set = [left_quote, right_quote, "\\"]
                rule_name = f"ac_{quote_name}"
                char_woquote_escape = QuotedStringFormat.rule_for_any_char(exclude_char=escape_set, context=self.context)
                self.context.add_rule(rule_name, char_woquote_escape)
                
                to_escape_char_symbols = self.chars_to_symbol(escape_set)
                part1 = self.chars_to_symbol(["\\"])[0]
                part2 = "|".join(to_escape_char_symbols)
                escaped_char_rule = f"{part1} | ({part2})"
                escaped_char_rulename = f"ec_{quote_name}"
                self.context.add_rule(escaped_char_rulename, escaped_char_rule)

                string_rule_name = "is_{quote_name}"
                string_rule = f"{left_quote_name} ( {escaped_char_rulename} | {char_woquote_escape} )+ {right_quote_name} | {left_quote_name}  {right_quote_name}"
                self.context.add_rule(string_rule_name, string_rule)
                rules.append(string_rule)
            rule = QuotedStringFormat.rule_for_or(rules)
        return rule
                


class FixedStringFormat(BaseFormat):
    def __init__(self, rule_name: str, string : Optional[str] = None, allowed_quotes : List[Tuple(str, str)] = None):
        super().__init__()
        if not self.fixed_string:
            rule_name = "string"
        self.rule_name = rule_name
            
        self.string = string
        
        if allowed_quotes is None:
            allowed_quotes = [("\"", "\""), ("\'", "\'")]
            
        self.allowed_quotes = allowed_quotes
        self.definition = self.build_def()
        self.context.add_rule(rule_name=self.rule_name, rule_def=self.definition)
        
    def build_def(self):
        rule = QuotedStringFormat.rule_for_adding_quotes(self.string, self.allowed_quotes)
   
    
class SimpleQuotedStringFormat(BaseFormat):
    def __init__(self, rule_name: str = "string", allowed_quotes : List[Tuple(str, str)] = None, context=None):
        super().__init__()

        assert rule_name == "string"
        self.rule_name = rule_name
        
        if allowed_quotes is None:
            allowed_quotes = [("\"", "\""), ("\'", "\'")]
            
        self.allowed_quotes = allowed_quotes
        self.definition = self.build_def()
    def build_def(self):
        rules = [["escape_char", "BACKSLASH any_char"],
                    ["inner_string_dq", "( char_wo_escape_dq | escape_char ) +"],
                    ["inner_string_sq", "( char_wo_escape_sq | escape_char ) +"],
                    ["dq_string", "(DQ inner_string_dq DQ) | (DQ DQ)"],
                    ["sq_string", "(SQ inner_string_sq SQ) | (SQ SQ)"],
                    ["string", "dq_string | sq_string"]]
        self.context.add_rules(rules)
        return rules[-1][-1]
    
    
class ArrayFormat(BaseFormat):
    def __init__(self, rule_name: str = "array",):
        super().__init__()

        assert rule_name == "array"
        self.rule_name = rule_name
        
        self.definition = self.build_def()
    def build_def(self):
        rules = [["array", "(LSB [wss] ( value [wss] (COMMA [wss] value [wss])*)+ RSB) | (LSB [wss] RSB)"]]
        self.context.add_rules(rules)
        return rules[-1][-1]
    
class DictFormat(BaseFormat):
    def __init__(self, rule_name: str = "object",):
        super().__init__()

        assert rule_name == "object"
        self.rule_name = rule_name
        
        self.definition = self.build_def()
    def build_def(self):
        rules = [["pair", "string [wss] COLON [wss] value]"],
                 ["object", "LCB [wss] [pair [wss] (COMMA [wss] pair [wss])*] RCB"],]
        self.context.add_rules(rules)
        return rules[-1][-1]
    
class NumberFormat(BaseFormat):
    def __init__(self, rule_name: str = "number",):
        super().__init__()

        assert rule_name == "number"
        self.rule_name = rule_name
        
        self.definition = self.build_def()
    def build_def(self):
        rules = [["number", "[MINUS] DIGIT+ [PERIOD DIGIT*] [(LE | UE) [PLUS | MINUS] DIGIT+ ]"],]
        self.context.add_rules(rules)
        return rules[-1][-1]