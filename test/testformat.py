from transformers import AutoTokenizer, LlamaForCausalLM

from llmformat import TokenFilter

local_os_tokenizer_dir = "../tokenizer"
tokenizer = AutoTokenizer.from_pretrained(
    local_os_tokenizer_dir)

token_filter = TokenFilter(tokenizer, "llmformat/grammar_files/json_min.bnf")
print(tokenizer.convert_ids_to_tokens(token_filter.trie.root().goto("LCB").get_values()))
test_example = """{"abc":"\\\\" ,"c": 2.3e+2} """
for i in range(len(test_example)):
    possible_token_ids = token_filter.next_token_from_string(
        test_example[:i])
    print("test_example", test_example[:i])
    string = tokenizer.convert_ids_to_tokens(possible_token_ids)
    print(string, end=" ")
    i = input()
# model = LlamaForCausalLM.from_pretrained()
