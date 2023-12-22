# LLM Format

## Introduction

LLM Format is a Large-language model formatter that constrain the outputs of language model to follow certain rules. 

Different from other packages including lm-format-enforcer, jsonformer and guidance. This package ensures the generated text from LLM to be sound and complete.

Once the grammar is provided, we can gaurantee the generation of the valid grammar. We currently support the generation of all LALR(1) grammar including JSON, XML, Regular Expression and so on.

## TODO

- Add example
- Add support for customized JSON
- Add integration