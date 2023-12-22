

import sys
import json
from lark import Lark, Transformer, v_args

json_grammar = open("json.bnf", "r").read()


class TreeToJson(Transformer):
    @v_args(inline=True)
    def string(self, s):
        return s[1:-1].replace('\\"', '"')

    array = list
    pair = tuple
    object = dict
    number = v_args(inline=True)(float)

    null = lambda self, _: None
    true = lambda self, _: True
    false = lambda self, _: False


### Create the JSON parser with Lark, using the Earley algorithm
# json_parser = Lark(json_grammar, parser='earley', lexer='basic')
# def parse(x):
#     return TreeToJson().transform(json_parser.parse(x))

### Create the JSON parser with Lark, using the LALR algorithm
json_parser = Lark(json_grammar, parser='lalr',
                   # Using the basic lexer isn't required, and isn't usually recommended.
                   # But, it's good enough for JSON, and it's slightly faster.
                   lexer='basic',
                   # Disabling propagate_positions and placeholders slightly improves speed
                   propagate_positions=False,
                   maybe_placeholders=False,
                   # Using an internal transformer is faster and more memory efficient
                   start='start')
parse = json_parser.parse

def constrain_sets():
    json.loads()

def test():
    test_json = '''
        {
            "empty_object" : {},
            "empty_array"  : [],
            "booleans"     : { "YES" : true, "NO" : false },
            "numbers"      : [ 0, 1, -2, 3.3, 4.4e5, 6.6e-7 ],
            "strings"      : [ "This", [ "And" , "That", "And a \\"b" ] ],
            "nothing"      : null
        }
    '''

    j = parse(test_json)
    print(j)
    import json
    
    assert j == json.loads(test_json)


if __name__ == '__main__':
    #test()

    text = """
    {"abc":"\\\\" ,"c":2.31e+1, "D":[1, 2, "S"]}"""
    print(text)
    interactive = json_parser.parse_interactive("", start="start")

    # feeds the text given to above into the parsers. This is not done automatically.
    i=0
    while i<len(text):
        print(text[:i+1], end="\t")
        interactive = json_parser.parse_interactive(text[:i+1], start="start")
        interactive.exhaust_lexer()
        # returns the names of the Terminals that are currently accepted.
        #print(interactive.accepts())
        #print(json_parser.terminals)
        i = i + 1
