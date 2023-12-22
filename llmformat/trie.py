class TrieNode:
    def __init__(self,):
        self._map = {}
        self._values = []
        self._possible_tokens = set()
    
    def add_transition(self, token, new_node = None):
        """Add another token following this state."""
        if new_node is None:
            new_node = TrieNode()
        self._map[token] = new_node
        self._possible_tokens.add(token)
    
    def next_possible_tokens(self):
        return self._possible_tokens
    
    def goto(self, token):
        if token not in self._map:
            assert False, "No avialable token found in the program."
        return self._map[token]
    
    def add_value(self, value):
        """Add possible token id to this state."""
        self._values.append(value)
    
    def get_values(self):
        """Return all possible token ids matched for this node. Excluding matches by prefix."""
        return self._values  
    
class Trie:
    def __init__(self):
        self.start = TrieNode()
        
        
    def root(self):
        return self.start 
    
    def add(self, lst, value):
        state = self.start
        for token in lst:
            if token not in state.next_possible_tokens():
                state.add_transition(token)
            state = state.goto(token)
        state.add_value(value)