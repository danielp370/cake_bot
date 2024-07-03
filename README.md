# Cake Chat

This repository contains example programs for a simple and more comprehensive chat bot that
can make local LLM tools calls.
They use streamlit for UI, Ollama for local LLM support, and Langchain to put it together.

These examples are intended to demonstrate making tool calls with a variety of models,
and without use of OllamaFunctions().

Fixes and improvements welcome.

## Features

 * Uses Ollama for local or remote LLM execution, and supports multiple models.
 * Supports Langchain tools that allows the LLM to execute external function calls.
   It does this without the use of OllamaFunctions.
 * Supports sessions with message histories. The LLM is aware of the history.
 * Some effort has gone into making this configurable and extensible. See `config.ini`. (cake_chat.py only)
 * Replace the tools, prompts, logos, etc, with your own. (cake_chat.py only)

![Cake bot example image](resources/cake_bot_example_codestral.png?raw=true "Cake Bot example")

## Installing

This depends on ollama, streamlit, langchain. And if you want to try the example below install mathplotlib

```pip install streamlit
pip install ollama
pip install langchain
pip install mathplotlib (optional)
```

Optionally, you should install other python libraries, such as mathplotlib if you want to
try out how it generates and renders plot figures.

You will also need to install Ollama, and some local Ollama models, or alternately point the bot to a Ollama server.
I recommend installing `codestral` if you want to try using the python execution examples. See [Ollama Github](https://github.com/ollama/ollama) for guidance on how to install Ollama and models.

## Running Simple Chat Bot

Simple chat bot is a cut down version of Cake Bot that demonstrates tools calls such as add and multiply. Most of the functionality, including the tools calls is contained in *simple_chat_bot.py*.  It depends on *llm_tools_manager.py*, and *helper_ollama_http.py* only.

You can invoke it via

> streamlit run simple_chat_bot.py

## Running Cake Chat Bot

Cake chat is an extended version of simple chat bot. In particular, we allow it to execute python code, so you can ask it to do things like `draw y=x*x` and see what happens.  It is also more extensible, so you can customize this for your own needs.


> streamlit run cake_chat.py

## Examples that should invoke tools.

Example functions add and multiply. The LLM should calls these, although sometimes it gets creative
and does it itself or uses python exec :-). Some models may need a different prompt to encourage
them.
> What is 1 + 1?

> Multiply that by 101.

We provide python exec, which a model would use to write code to achieve the following:
> draw me y=x*x

Because we describe the tools and enviroments to the llm via the tools description and prompts, you should be able to just say `draw me y=x*x`. In other cases you may need to explain details a little more.

### python_exec

Python exec and shell exec are provided as examples. If you run cake bot, it will often attempt to write and execute python or shell code.  This can be very useful. For example, in the `draw me y=x*x` above, it will usually try to write python code to render a figure using mathplotlib.

You can take that further, by then asking it to `write the figure to a file called my_math.png`. Can you then ask it to open the file for you using a local application. For example, on mac I'd ask it to open the file for me using `open` shell command.



## Details

The tools are in my_tool_calls.py

We have in there some examples such as add, multiply, converse and python exec.
The python exec call can be dangerous, so if you want to use that in any serious setting it
should be removed or made safer. However, it is useful to have to demonstrate some capabilities.

# Issues and Limitations

## python exec

The `python_exec` tool was intended as an example, however it should probably not be used for anything serious today.  Instead, implementing specific tool calls that the model can call would likely be safer and more successful.
The python exec approach is a powerful method to allow a model to write and execute its own code to undertake a task, and this demonstrates some success, expecially when using models that are good at python coding and following instructions. Codestral is a reasonable example.

When we ask the model to draw a figure using mathplotlib, many LLM's will often try to render a figure using `mathplotlib plot()` directly, which is not going to show anything via streamlit.  You can try experimenting with different prompts and improve what I have.

Another challenge is how limtied models are for writing code.  Simple examples should work, but as code or requests get more complicated, we run into errors. For those interested in doing this, it is worth exploring other approaches such as agents to help guide the process.  Cake bot does allow for automatic re-attempts on failed code execution, and it shows some success in correcting its mistakes based on seeing the error message as feedback in the prompt chain.