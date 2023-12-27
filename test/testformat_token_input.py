from transformers import AutoTokenizer, LlamaForCausalLM

from llmformat import TokenFilter

local_os_tokenizer_dir = "../tokenizer"
tokenizer = AutoTokenizer.from_pretrained(
    local_os_tokenizer_dir)

token_filter = TokenFilter(tokenizer, "llmformat/grammar_files/json_min.bnf")
test_example = """{"abc":"\\\\" ,"c": 2.3e+2} """
for i in range(len(test_example)):
    token_ids = tokenizer.convert_tokens_to_ids(tokenizer.tokenize(test_example[:i]))
    print(token_ids, tokenizer.convert_ids_to_tokens(token_ids), tokenizer.convert_tokens_to_string(tokenizer.tokenize(test_example[:i])))
    possible_token_ids = token_filter.next_token_from_tokens(
        token_ids)
    print("test_example", test_example[:i])
    string = tokenizer.convert_ids_to_tokens(possible_token_ids)
    print(string, end=" ")
