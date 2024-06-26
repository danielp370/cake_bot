# Generic manager for tools

from operator import itemgetter
from langchain.tools.render import render_text_description

class ToolManager:
    def __init__(self, initial_config):
        print(f"\n\n ** TOOL RESET ** \n\n")
        self.tools = {}
        self.config = initial_config
        self.tool_settings_data = {}

    def load_tools(self, tools):
        for tool_func in tools:
            self.add_tool(tool_func.name, tool_func)

    def add_tool(self, name: str, func):
        self.tools[name] = func

    def get_tool(self, name: str):
        return self.tools.get(name, None)

    def get_tools(self):
        return list(self.tools.values())

    def tool_chain(self, model_output):
        default = self.get_tool_setting('default_tool')
        chosen_tool_name = model_output.get('tool', default)
        print(f"Tool_chain {model_output} type {type(model_output)}")
        chosen_tool = self.get_tool(chosen_tool_name)
        if chosen_tool:
            print(f"chosen tool {chosen_tool}")
            return itemgetter("args") | chosen_tool
        else:
            raise ValueError(f"Tool {chosen_tool_name} not found.")

    def set_tool_settings(self, settings: dict):
        self.tool_settings_data.update(settings)

    def get_tool_setting(self, key: str):
        return self.tool_settings_data.get(key, None)

    def render_text_description(self):
        return render_text_description(self.get_tools())

    def get_format_instructions(self):

        rendered_tools = self.render_text_description()

        DEFAULT_SYSTEM_PROMPT = f"""
        You are an assistant that must use the following set of tools.
        Here are the names and descriptions for each tool:

        {rendered_tools}

        The tool name and parameters must match perfectly.
        Respond only with a JSON blob and no extra text outside that.
        The JSON blob must contain a single tool invocation which has both a parameter
        called 'tool' for the tool name, and a second key called 'args' which contains a
        dictonary of parameters matching the tool prototype. """

        return DEFAULT_SYSTEM_PROMPT


from typing import Dict, Any, NamedTuple, Optional

class ToolReturn(NamedTuple):
    message: str
    data: Optional[Dict[str, Any]]

