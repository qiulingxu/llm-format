import copy
from typing import List, Optional

from typing_extensions import Self


class TrieNode:
    def __init__(self, identifier = None):
        self._map = {}
        self._values = []
        self._possible_tokens = set()
        self.idetifier = identifier
    
    def repr(self) -> int:
        return self.idetifier
    
    def add_transition(self, token : str, new_node : Optional[Self] = None, cnt : Optional[int] = None ):
        """Add another token following this state."""
        if new_node is None:
            new_node = TrieNode(cnt)
        self._map[token] = new_node
        self._possible_tokens.add(token)
    
    def next_possible_tokens(self) -> set:
        return self._possible_tokens
    
    def goto(self, token : str) -> Self:
        if token not in self._map:
            assert False, "No avialable token found in the program."
        return self._map[token]
    
    def add_value(self, value) -> None:
        """Add possible token id to this state."""
        self._values.append(value)
    
    def get_values(self) -> List[int]:
        """Return all possible token ids matched for this node. Excluding matches by prefix."""
        return self._values
    
class Trie:
    def __init__(self):
        self.size = 0
        self._start = TrieNode(identifier=self.size)
        
    def root(self) -> TrieNode:
        return self._start 
    
    def add(self, lst : List[str], value:int) -> None:
        state = self._start
        for token in lst:
            if token not in state.next_possible_tokens():
                self.size += 1
                state.add_transition(token, cnt=self.size)
            state = state.goto(token)
        state.add_value(value)