# Cake Chat

This repository contains an example program for a chat bot that can make local LLM tools calls.
It uses streamlit for UI, Ollama for local LLM support, and Langchain to put it together.

Fixes and improvements welcome.

## Features

 * Uses Ollama for local or remote LLM execution, and supports multiple models.
 * Supports Langchain tools that allows the LLM to execute external function calls.
   It does this without the use of OllamaFunctions.
 * Supports sessions with message histories. The LLM is aware of the history.
 * Some effort has gone into making this configurable and extensible. See `config.ini`.
 * Replace the tools, prompts, logos, etc, with your own.

## Details

The tools are in my_tool_calls.py

We have in there some examples such as add, multiply, converse and python exec.
The python exec call can be dangerous, so if you want to use that in any serious setting it
should be removed or made safer. However, it is useful to have to demonstrate some capabilities.

## Installing

This depends on ollama, streamlit, langchain. And if you want to try the example below install mathplotlib

```pip install streamlit
pip install ollama
pip install langchain
pip install mathplotlib
```

## Running

> streamlit run chat.py

## Examples that should invoke tools.

Example functions add and multiply. The LLM should calls these, although sometimes it gets creative
and does it itself or uses python exec :-). Some models may need a different prompt to encourage
them.
> What is 1 + 1?

> Multiply that by 101.

We provide python exec, which the llm would use to write code to achieve the following:
> Using streamlit and mathplotlib render me y=x*x
