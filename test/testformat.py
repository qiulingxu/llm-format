from transformers import AutoTokenizer, LlamaForCausalLM

from llmformat import TokenFilter

local_os_tokenizer_dir = "../tokenizer"
tokenizer = AutoTokenizer.from_pretrained(
    local_os_tokenizer_dir)

token_filter = TokenFilter(tokenizer, "llmformat/json_min.bnf")
possible_token_ids = token_filter.next_token_from_string(
    """{"abc":"\\\\" ,"c""")
for i in possible_token_ids:
    string = tokenizer.convert_ids_to_tokens([i])
    print(string, token_filter.lex(string[0]))
# model = LlamaForCausalLM.from_pretrained()
