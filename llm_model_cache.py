from config import Config
from helper_ollama_http import get_ollama_model_names
from llm_tools_manager import ToolManager

from langchain_community.llms import Ollama

class ModelCache:
    def __init__(self, config: Config):
        self.model_cache = {}
        self.config = config
        self.model_server_url   = config.get_value_by_key('chat', 'model_server_url',
                                                          'http://localhost:11434')
        self.current_model_name = config.get_value_by_key('chat', 'model_name_default',
                                                          'mistral:instruct')
        self.current_model_temperature = config.get_value_by_key('chat', 'model_temperature',
                                                          0.9)
        self.current_model_num_predict = config.get_value_by_key('chat', 'model_num_predict',
                                                          128)
        self.current_model = None
        self.current_tools = None
        self.available_models = get_ollama_model_names(self.model_server_url)

    def load_model(self, model_name: str):
        """
        Returns:
            tuple: A tuple containing the model and its tools.
        """

        if model_name in self.model_cache:
            print(f"Found in cache {model_name}")
            self.current_model_name = model_name
            self.current_model, self.current_tools = self.model_cache[model_name]
        else:
            print(f"Model NOT found {model_name}")
            model = Ollama(model=model_name, format='json',
                           temperature=self.current_model_temperature,
                           num_predict=self.current_model_num_predict)
            tools = ToolManager(self.config)

            self.set_model(model_name, model, tools)

        return self.current_model, self.current_tools


    def set_model(self, model_name: str, model, tools):
        self.current_model_name = model_name
        self.model_cache[model_name] = (model, tools)
        self.current_model = model
        self.current_tools = tools

    def get_model(self):
        """
        Get current model and tools, if any.

        Returns:
            tuple: A tuple containing the model and its tools.
        """
        return self.current_model, self.current_tools
