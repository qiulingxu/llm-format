from abc import ABC
from os import path
from typing import Dict, List, Optional, Tuple, Union

from typing_extensions import Self

from .constant import _EOS_TOKEN, _OTHER_CHAR_SYMBOL
from .grammar_files.grammar_constant import parse_lex_definition


class RuleName(str):
    pass

class AnoymousRule(str):
    pass

class RuleDef(str):
    def __new__(cls, string, dependencies : Optional[List[RuleName]] = None):
        obj = str.__new__(cls, string)
        obj._dependencies = dependencies
        return obj

    @property
    def dependencies(self):
        return self._dependencies

class Rule():
    def __init__(self, rule_name : RuleName, rule_def :RuleDef):
        super.__init__()
        self._rule_name = rule_name
        self._rule_def = rule_def
    
    @property
    def rule_name(self):
        return self._rule_name
    
    @property
    def rule_def(self):
        return self._rule_def

class RuleManager():
    def __init__(self, basefile = None, rules : Optional[Dict[RuleName, RuleDef]] = None):
        
        if basefile is None:
            basepath = path.dirname(__file__)
            filepath = path.abspath(path.join(basepath, "grammar_files", "base.bnf"))
        self.symbol2def, self.char2symbol = parse_lex_definition(filepath)
        if rules is None:
            self.rules = {}
        else:
            self.rules = rules
        """global _default_context
        if _default_context["manager"] is not None:
            raise ValueError("RuleManager does not support initialize twice.")
        _default_context["manager"] = self"""
    
    def get_rule(self, rule_name : RuleName) -> RuleDef:
        if rule_name not in self.rules:
            raise KeyError(f"{rule_name} is not found in rules.")
        return rule_name
    
    def add_rule(self, rule_name : RuleName, rule_def : RuleDef) -> None:
        if rule_name not in self.rules:
            self.rules[rule_name] = rule_def
        else:
            if self.rules[rule_name] != rule_def:
                raise ValueError(f"Rule {rule_name} has conflicting definitions `{self.rules[rule_name]}` and `{rule_def}`")
    
    def add_rules(self, rules: List[Tuple[RuleName, RuleDef]]) -> None:
        for rule_name, rule in rules:
            self.add_rule(rule_name, rule)

    def to_bnf_grammar(self):
        rules_bnf = ""
        for rule_name, rule_def in self.rules.items():
            rules_bnf += f"{rule_name} : {rule_def}\n"
        return rules_bnf

_default_context = {"manager": RuleManager()}

def get_curr_context():
    if _default_context["manager"] is None:
        raise ValueError("RuleManager has not been set up.")
    else:
        return _default_context["manager"]
    
def gen_bnf_grammar():
    return _default_context["manager"].to_bnf_grammar()

class BaseFormat():
    
    ESCAPED_CHARACTERS = ["\\", "\"", "'", "]"]
    
    def __init__(self, context:Optional[RuleManager] = None):
        if context is None:
            context = get_curr_context()
        self.context = context
    
    def set_rule(self, rule_name, rule_def):
        if isinstance(rule_name, str):
            rule_name = RuleName(rule_name)
        if isinstance(rule_def, str):
            rule_def = RuleDef(rule_def)
        self._rule_name = rule_name
        self._definition = rule_def
        self.context.add_rule(self._rule_name, self._definition)
    
    @property
    def rule_name(self):
        return self._rule_name
    
    @property
    def rule_def(self):
        return self._definition
        
    
    @property
    def symbol(self):
        return self.rules.keys()
    
    @property
    def definition(self):
        return self.rules.values()

    @staticmethod
    def rule_for_or(lst_of_rules:List[RuleName]) -> RuleDef:
        lst = [ "(" + rule + ")" for rule in lst_of_rules]
        return RuleDef("(" + "|".join(lst) + ")")

    @staticmethod
    def rule_for_sequence(lst_of_rules:List[RuleName]) -> RuleDef:
        lst = ["(" + rule + ")" for rule in lst_of_rules]
        return RuleDef("(" + " ".join(lst) + ")")
        
    @staticmethod
    def rule_for_string(string:str) -> str:
        context = get_curr_context()
        lst = []
        for ch in string:
            if ch not in context.char2symbol:
                raise KeyError(f"{ch} not found in token definition base.bnf")
            if ch in BaseFormat.ESCAPED_CHARACTERS:
                lst += [context.char2symbol["\\"], context.char2symbol[ch]]
            else:
                lst.append(context.char2symbol[ch])
        return RuleDef(" ".join(lst))
    
    @staticmethod
    def rule_for_adding_quotes(rule:RuleName, quotes_str: List[Tuple[str, str]]) -> RuleDef:
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
        #escapped_chars = ["\"", "]", "/", "-"]
        return _OTHER_CHAR_SYMBOL
    
    @staticmethod
    def rule_for_any_char(exclude_char : Optional[List[str]] = None, exclude_symbol: Optional[List[str]] = None) -> RuleDef:
        context = get_curr_context()
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
        rule = RuleDef(" ".join(list(lst_of_symbols)))
        return rule
    
    @staticmethod
    def chars_to_symbol(lst_chars: List[str]) -> List[str]:
        context = get_curr_context()
        result = []
        for char in lst_chars:
            result.append(context.char2symbol[char])
        return result
    
    @staticmethod
    def string_to_symbol(string: str) -> str:
        return " ".join(BaseFormat.chars_to_symbol(string))

    

RuleNameOrFormat = Union[BaseFormat, RuleName]
def get_rule_name(rule: RuleNameOrFormat) -> str:
    if isinstance(rule, BaseFormat):
        return rule.rule_name
    elif isinstance(rule, RuleName):
        return rule
    elif isinstance(rule, str):
        return RuleName(rule)
    else:
        raise ValueError(f"rule {rule} of type {type(rule)} is neither BaseFormat or RuleName.")


class QuotedStringFormat(BaseFormat):
    def __init__(self, 
                 rule_name: RuleName ,
                 fixed_string : bool,
                 string : Optional[str] = None,
                 allowed_quotes : List[Tuple[str, str]] = None):
        super().__init__()
        self.fixed_string = fixed_string
        self.string = string
        
        if allowed_quotes is None:
            allowed_quotes = [("\"", "\""), ("\'", "\'")]
            
        self.allowed_quotes = allowed_quotes
        self.set_rule(rule_name, self.build_def())
        
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
    """Generates rule for fixed string characters"""
    def __init__(self,
                 rule_name: RuleName,
                 string : Optional[str] = None,
                 allowed_quotes : List[Tuple[str, str]] = None):
        super().__init__()
            
        self.string = string
        
        if allowed_quotes is None:
            allowed_quotes = [("\"", "\""), ("\'", "\'")]
            
        self.allowed_quotes = allowed_quotes
        definition = self.build_def()
        self.set_rule(rule_name, definition)
        
    def build_def(self):
        return QuotedStringFormat.rule_for_adding_quotes(self.string, self.allowed_quotes)

class BooleanFormat(BaseFormat):
    """Generates rule for fixed string characters"""
    def __init__(self, capitalize=False):
        super().__init__()
        self.capitalize = capitalize
        self.set_rule("boolean", self.build_def())
        
    def build_def(self):
        true_string = "true"
        false_string = "false"
        if self.capitalize:
            true_string = true_string.capitalize()
            false_string = false_string.capitalize()
        rule = BooleanFormat.rule_for_or([BooleanFormat.rule_for_string(true_string),
                                          BooleanFormat.rule_for_string(false_string)])
        return rule
    
class NoneFormat(BaseFormat):
    """Generates rule for fixed string characters"""
    def __init__(self, capitalize=False):
        super().__init__()
        self.capitalize = capitalize
        self.set_rule("null", self.build_def())
        
    def build_def(self):
        null_string = "null"
        if self.capitalize:
            null_string = null_string.capitalize()
        rule = NoneFormat.rule_for_string(null_string)
        return rule
    
class SimpleQuotedStringFormat(BaseFormat):
    """Generates rule for any escapped characters"""
    def __init__(self,):
        super().__init__()
        if allowed_quotes is None:
            allowed_quotes = [("\"", "\""), ("\'", "\'")]
            
        self.allowed_quotes = allowed_quotes
        self.set_rule("string", self.build_def())
        
    def build_def(self):
        dep_rules = [["escape_char", "BACKSLASH any_char"],
                    ["inner_string_dq", "( char_wo_escape_dq | escape_char ) +"],
                    ["inner_string_sq", "( char_wo_escape_sq | escape_char ) +"],
                    ["dq_string", "(DQ inner_string_dq DQ) | (DQ DQ)"],
                    ["sq_string", "(SQ inner_string_sq SQ) | (SQ SQ)"]]
        self.context.add_rules(dep_rules)
        return RuleDef("dq_string | sq_string")
    
class SimpleArrayFormat(BaseFormat):
    def __init__(self, rule_name: RuleName = "array",
                        element_rule_name : RuleNameOrFormat = RuleName("value")):
        super().__init__()
        self.element_rule_name = get_rule_name(element_rule_name)
        self.set_rule(rule_name, self.build_def())
        
    def build_def(self):
        value = self.element_rule_name
        return RuleDef(f"(LSB [wss] ( {value} [wss] (COMMA [wss] {value} [wss])*)+ RSB) | (LSB [wss] RSB)")
    
class SimpleDictFormat(BaseFormat):
    def __init__(self, 
                 key_rule_name : RuleNameOrFormat = "string",
                 value_rule_name : RuleNameOrFormat = "value"):
        super().__init__()
        self.key_rule_name = get_rule_name(key_rule_name)
        self.value_rule_name = get_rule_name(value_rule_name)
        self.set_rule("object", self.build_def())
        
    def build_def(self):
        value = self.value_rule_name
        key = self.key_rule_name
        dep_rules = [["pair", f"{key} [wss] COLON [wss] {value}]"]]
        self.context.add_rules(dep_rules)
        return RuleDef("LCB [wss] [pair [wss] (COMMA [wss] pair [wss])*] RCB")
    
class NumberFormat(BaseFormat):
    def __init__(self):
        super().__init__()
        self.set_rule("number", self.build_def())
        
    def build_def(self):
        rules = [["number", "[MINUS] DIGIT+ [PERIOD DIGIT*] [(LE | UE) [PLUS | MINUS] DIGIT+ ]"],]
        self.context.add_rules(rules)
        return rules[-1][-1]

    
class SimpleDictFormat(BaseFormat):
    def __init__(self, value_rule_name = "value"):
        super().__init__()
        self.value_rule_name = value_rule_name
        self.set_rule("object", self.build_def())
    
    def build_def(self):
        value = self.value_rule_name
        rules = [["array", f"(LSB [wss] ( {value} [wss] (COMMA [wss] {value} [wss])*)+ RSB) | (LSB [wss] RSB)"],]
        self.context.add_rules(rules)
        return rules[-1][-1]

class JsonFormat(BaseFormat):
    def __init__(self, 
                 value_types : List[RuleNameOrFormat] = [BooleanFormat(), SimpleArrayFormat(), SimpleDictFormat(), NumberFormat(), NoneFormat()]):
        super().__init__()
        self.value_types = []
        for name in value_types:
            self.value_types.append(get_rule_name(name))
        self.set_rule("value", self.build_def())
        
    
    def build_def(self):
        return JsonFormat.rule_for_or(self.value_types)
    
class LLMFormat(BaseFormat):
    def __init__(self, start_rule_name : RuleNameOrFormat):
        super().__init__()
        self.start_rule_name = get_rule_name(start_rule_name)
        self.set_rule("start", self.build_def())
        
    def build_def(self):
        return LLMFormat.rule_for_sequence(
            [RuleName("wss"), self.start_rule_name, RuleName("wss"), RuleName(_EOS_TOKEN)]
        )

def get_default_format(dependencies:Dict[str, BaseFormat]):
    default_format_translation = \
        {
            "string" : SimpleQuotedStringFormat,
            "number" : NumberFormat,
            "array" : ArrayFormat,
            "dict" : DictFormat
            
        }
    completed_dependencies = dependencies.copy()
    for k, v in dependencies.items():
        if v is None:
            if k in default_format_translation:
                v = default_format_translation[k]
            else:
                raise ValueError(f"The format {k} is not defined either dependencies nor default dependencies.")
            completed_dependencies[k] = v
    return completed_dependencies