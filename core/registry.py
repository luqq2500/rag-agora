import datetime
from pathlib import Path
from typing import Callable, Any

from dotenv import load_dotenv
from langchain_community.tools import TavilySearchResults
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from core.repository import VectorRepositoryChromaDB


def wire_llm_system_instruction(file_name: str= 'instruction.md'):
    base_dir = Path(__file__).parent.resolve()
    return Path(base_dir / file_name).read_text()

class ModelRegistry:
    def __init__(self):
        self.registry = {
            'ollama-phi-3.5': lambda temp: ChatOllama(model='phi3.5:latest', temperature=temp),
            'gemini-3.5-flash': lambda temp: ChatGoogleGenerativeAI(model='gemini-3.5-flash', temperature=temp),
            'gemini-3.5-flash-lite': lambda temp: ChatGoogleGenerativeAI(model='gemini-3.5-flash-lite', temperature=temp),
            'gemini-3.6-flash': lambda temp: ChatGoogleGenerativeAI(model='gemini-3.6-flash', temperature=temp),
        }

    def construct_model(self, model_name: str, temperature: float=0.1) -> BaseChatModel:
        load_dotenv()
        if model_name not in self.registry:
            raise ValueError(f'{model_name} is not supported')
        return self.registry[model_name](temperature)

    def get_supported_models(self)->list[str]:
        return list(self.registry.keys())

class ToolRegistry:
    def __init__(self):
        self.registry: dict[str, Callable[..., Any]] = {}

    def get_tools(self):
        return list(self.registry.values())

    def add_tools(self, methods: list[Callable[..., Any]]):
        for method in methods:
            if hasattr(method, "name") and hasattr(method, "description"):
                name =  method.name
                doc = method.description
            else:
                name = method.__name__
                doc = method.__doc__

            if not name or name.startswith("__"):
                continue
            if not doc:
                raise ValueError(f'Tool {name} does not have docstring for description.')
            if name in self.registry:
                raise RuntimeWarning(f'Tool {name} is already registered.')
            self.registry[name] = method

def wire_tools_registry():
    load_dotenv()
    tool_registry = ToolRegistry()
    repository = VectorRepositoryChromaDB()

    def get_date_time():
        """
        Return the current local date and time as "YYYY-MM-DD HH:MM:SS".

        Takes no arguments. This is the only way to know today's date — do not assume
        it. Call it before any claim that depends on the present moment: whether a
        deadline has passed, how long an instrument has been in force, whether a
        compliance phase has begun, or how old a document is.
        """
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    tool_registry.add_tools([
        repository.get_search_filters,
        repository.ranking_search,
        TavilySearchResults(max_results=10),
        get_date_time
    ])

    return tool_registry
