# Optimize Lark LALR parser for better efficiency
#See https://github.com/lark-parser/lark/issues/1142
from copy import copy, deepcopy
from typing import Any, Dict, Generic, List

from lark.common import ParserCallbacks
#from lark.exceptions import UnexpectedToken
from lark.lexer import LexerThread, Token
from lark.parsers.lalr_analysis import ParseTableBase, Shift, StateT
from lark.parsers.lalr_interactive_parser import InteractiveParser
from lark.parsers.lalr_parser_state import ParseConf
from typing_extensions import Self


#We simplify error signal
class SimpleUnexpectedToken(Exception):
    ...
    pass


class FastParserState(Generic[StateT]):
    __slots__ = 'parse_conf', 'lexer', 'state_stack', 'value_stack'

    parse_conf: ParseConf[StateT]
    lexer: LexerThread
    state_stack: List[StateT]
    value_stack: list

    def __init__(self, parse_conf: ParseConf[StateT], lexer: LexerThread, state_stack=None):
        self.parse_conf = parse_conf
        self.lexer = lexer
        self.state_stack = state_stack or [self.parse_conf.start_state]

    @property
    def position(self) -> StateT:
        return self.state_stack[-1]

    # Necessary for match_examples() to work
    def __eq__(self, other) -> bool:
        if not isinstance(other, FastParserState):
            return NotImplemented
        return len(self.state_stack) == len(other.state_stack) and self.position == other.position

    def __copy__(self):
        return type(self)(
            self.parse_conf,
            self.lexer, # XXX copy
            copy(self.state_stack),
        )

    def copy(self) -> 'ParserState[StateT]':
        return copy(self)


    def feed_token(self, token: Token, is_end=False) -> Any:
        #assert isinstance(token, Token), f"Received {token} instead of Token"
        state_stack = self.state_stack
        states = self.parse_conf.states
        end_state = self.parse_conf.end_state
        callbacks = self.parse_conf.callbacks
        
        while True:
            
            state = state_stack[-1]
            try:
                action, arg = states[state][token.type]
            except KeyError:
                #expected = {s for s in states[state].keys() if s.isupper()}
                raise SimpleUnexpectedToken()#token, expected, state=self, interactive_parser=None

            assert arg != end_state
            #print(token.type, state, arg)
            
            if action is Shift:
                # shift once and return
                assert not is_end
                state_stack.append(arg)
                return
            else:
                # reduce+shift as many times as necessary
                rule = arg
                size = len(rule.expansion)
                if size:
                    del state_stack[-size:]
                else:
                    s = []

                _action, new_state = states[state_stack[-1]][rule.origin.name]
                assert _action is Shift
                state_stack.append(new_state)


class FastInteractiveParser(InteractiveParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_state = FastParserState(
            self.parser_state.parse_conf,
            self.parser_state.lexer,
            self.parser_state.state_stack,
        )

    def accepts(self):
        """Returns the set of possible tokens that will advance the parser into a new valid state."""
        accepts = set()
        conf_no_callbacks = copy(self.parser_state.parse_conf)
        # We don't want to call callbacks here since those might have arbitrary side effects
        # and are unnecessarily slow.
        conf_no_callbacks.callbacks = {}
        for t in self.choices():
            if t.isupper(): # is terminal?
                new_cursor = copy(self)
                new_cursor.parser_state.parse_conf = conf_no_callbacks
                try:
                    new_cursor.feed_token(self.lexer_thread._Token(t, ''))
                except SimpleUnexpectedToken:
                    pass
                else:
                    accepts.add(t)
        return accepts

    @staticmethod
    def copyfrom(parser : InteractiveParser) -> Self:
        return FastInteractiveParser(parser = parser.parser,
                                     parser_state = parser.parser_state,
                                     lexer_thread = parser.lexer_thread)
    
    def as_immutable(self):
        """Convert to an ``ImmutableInteractiveParser``."""
        p = copy(self)
        return FastImmutableInteractiveParser(p.parser, p.parser_state, p.lexer_thread)

class FastImmutableInteractiveParser(FastInteractiveParser):
    """Same as ``InteractiveParser``, but operations create a new instance instead
    of changing it in-place.
    """

    result = None

    def __hash__(self):
        return hash((self.parser_state, self.lexer_thread))

    def feed_token(self, token):
        c = copy(self)
        c.result = InteractiveParser.feed_token(c, token)
        return c

    def exhaust_lexer(self):
        """Try to feed the rest of the lexer state into the parser.

        Note that this returns a new ImmutableInteractiveParser and does not feed an '$END' Token"""
        cursor = self.as_mutable()
        cursor.exhaust_lexer()
        return cursor.as_immutable()

    def as_mutable(self):
        """Convert to an ``InteractiveParser``."""
        p = copy(self)
        return FastInteractiveParser(p.parser, p.parser_state, p.lexer_thread)
