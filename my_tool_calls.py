from langchain_core.tools import tool

import subprocess
from io import StringIO
from contextlib import redirect_stdout

from llm_tools_manager import ToolManager, ToolReturn
from helper_st_tool_options import helper_unsafe_user_dialog, auto_prompt_set


# Define tools available.
@tool
def multiply(first: int, second: int) -> int:
    """Multiply two integers together."""
    return first * second

@tool
def add(first: int, second: int) -> int:
    """Add two integers."""
    print('adding')
    return first + second

@tool
def converse(response: str) -> str:
    """Use this to respond conversationally.
       Respond conversationally if no other tools should be called for a given query."""
    return response

@tool
def write_to_file(filename: str, data: str) -> bool:
    """Write data to a file."""
    print(f"writing file {filename} : {data} \n\n")
    return True


def shell_code_execute(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        return ToolReturn(result.stdout, None)
    else:
        return ToolReturn(f"Command failed! (exit code: {result.returncode})\n{result.stderr}", None)

def python_exec_execute(code) -> ToolReturn:

    f = StringIO()
    with redirect_stdout(f):
        exec(code)
    s = f.getvalue()

    # Check if there are any other objects we want to return
    supported_variables = ['return_object', 'csv_object']

    # Check locals() and copy supported variables to a new dictionary
    extras_dict = {}
    for var in supported_variables:
        if var in locals():
            extras_dict[var] = locals()[var]

    # set the AI to run again so it can respond in english.
    if extras_dict == {} and s == "":
        auto_prompt_set(1)

    return ToolReturn(s, extras_dict)

def execute_callback_return(execute_function, code, response):
    """Helper function for executing external code"""
    chat_ai_callback = _tool_manager.get_tool_setting('chat_ai_callback')
    if code != None:
        try:
            response = execute_function(code)
        except Exception as e:
            response = f"Execution failed: {e}"
            auto_prompt_set(1)

    if chat_ai_callback:
        chat_ai_callback(response)
    else:
        print("ERROR chat_ai_callback should be defined.")

def exec_check(setting_key, execute_function, code):
    allow_unsafe = _tool_manager.get_tool_setting(setting_key)
    present_exec_dialog = _tool_manager.get_tool_setting('present_exec_dialog')

    if allow_unsafe == None or allow_unsafe == False:
        return f"exec_check did not execute, you need to {setting_key} via settings"

    if present_exec_dialog == True:
        helper_unsafe_user_dialog(code, execute_function, execute_callback_return)

        return "Waiting for you to allow or deny code execution."
    else:
        return execute_function(code)

# Exec tool flow with common intrastructure:
# [python_exec|shell_exec] -> exec_check -> optional helper_unsafe_user_dialog ->
#    [shell_code_execute|python_exec_code_execute] -> execute_callback_return
#
# For phython exec, codestral runs nice. Probably any mistral, mixtral model.
#
@tool
def python_exec(code: str) -> str:
    """Use this tool as a last resort. Run some generated Python code.
       It captures stdout and returns it as a str.
       Don't try to display objects such as figures, I will do that via a streamlit call.
       Instead, return an object that I can render using streamlit's pyplot or image or write commands.
       Put it in a local variable called return_object.
       Remember to return non-text objects in return_object."""

    return exec_check('allow_python_exec', python_exec_execute, code)

@tool
def shell_exec(command: str) -> str:
    """Use this tool as a last resort. Run a system command. Captures stdout and returns it."""

    return exec_check('allow_shell_exec', shell_code_execute, command)


# Our custom tool management:

_tool_manager : ToolManager = None

def my_tools_init(tm, model):
    global _tool_manager
    _tool_manager = tm

    tools = [add, multiply, converse, python_exec, shell_exec]

    # set any state you want to pass into tools
    _tool_manager.set_tool_settings({'default_tool': 'converse'})

    _tool_manager.load_tools(tools)

def my_tools_get_option_keys():
    # A list of setting option key bools we want to present to help us manage our tools
    return [('allow_python_exec', 'Allow python code execution'),
            ('allow_shell_exec', 'Allow shell execution'),
            ('present_exec_dialog', 'Present code execution dialog')]


