class TRIE_node:
    def __init__(self,):
        self.map = {}
        self.values = []
    
    def next_possible_tokens(self):
        return self.map.keys()
    
    def goto(self, token):
        if token not in self.map:
            assert False, "No avialable token found in the program."
        return self.map[token]
    
    def add_value(self, value):
        self.values.append(value)
    
class TRIE:
    def __init__(self):
        self.start = TRIE_node()
        
        
    def root(self):
        return self.start 
    
    def add(self, lst, value):
        state = self.start
        for token in lst:
            if token not in state:
                state[token] = TRIE_node()
                state = state[token]
        state.add_value(value)