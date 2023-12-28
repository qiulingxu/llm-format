#  LLM Format

![](./assets/llmlogo.jpg)

## Introduction

LLM Format is a Large-language model formatter that constrain the outputs of language model to follow certain rules. Our design is to make this tool flexible and efficient to adapt to different use cases.

We currently supports **vllm** and any **LALR(1) grammar** including **JSON** format.

Different from other packages including lm-format-enforcer, jsonformer and guidance. This package ensures the generated text from LLM to be sound and complete. 


## Tutorial 

### Installation

`pip install llmformat`

### Usage

To enforce a new type of grammar, a grammar file written in EBNF is needed. We provide the JSON example as [here](https://github.com/qiulingxu/llmformat/blob/main/llmformat/grammar_files/json_min.bnf).

Once it is written, we only need one-line code change to change the output format.

In vllm, add this option to sampling_param.

```
model = LLM(...)
grammar = open("./llmformat/gammar_files/json_min.bnf", "r").read()
sampling_param.logits_processors=[llmformat.llminterface.build_vllm_logits_processor(model, grammar)]
```

### Example
The example of working on Llama2 and vllm can be found [here](https://github.com/qiulingxu/llmformat/blob/main/examples/vllm_llama2.ipynb). Note that you may want to change the location of grammar file.


- Add support for customized JSON
- Add more integrations

## Known Issues

We use cache to accelerate grammar parsing. The speed will becomes faster as it runns longer.