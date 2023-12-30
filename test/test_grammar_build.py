from llmformat.grammar_builder import JsonFormat, LLMFormat, gen_bnf_grammar

format = LLMFormat(JsonFormat())
print(gen_bnf_grammar())