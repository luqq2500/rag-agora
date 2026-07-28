from pathlib import Path

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from core.repository import AgoraDocumentVectorRepository, DocumentRepositoryChromaDB


def wire_llm_system_instruction(file_name: str= 'instruction.md'):
    base_dir = Path(__file__).parent.resolve()
    return Path(base_dir / file_name).read_text()

class ModelRegistry:
    def __init__(self):
        self.registry = {
            'ollama-phi-3.5': lambda: ChatOllama(model='phi3.5:latest'),
            'gemini-3.5-flash': lambda: ChatGoogleGenerativeAI(model='gemini-3.5-flash'),
            'gemini-3.5-flash-lite': lambda: ChatGoogleGenerativeAI(model='gemini-3.5-flash-lite')
        }

    def construct_model(self, model_name: str) -> BaseChatModel:
        load_dotenv()
        if model_name not in self.registry:
            raise ValueError(f'{model_name} is not supported')
        return self.registry[model_name]()

    def get_supported_models(self)->list[str]:
        return list(self.registry.keys())

class ToolRegistry:
    def __init__(self, document_repository: AgoraDocumentVectorRepository):
        self.registry = {
            document_repository.get_metadata.__name__: document_repository.get_metadata,
            document_repository.ranking_search.__name__: document_repository.ranking_search,
        }
        self.active_tools = [tool for tool in self.registry.values()] # default take all tools in the registry

    def get_supported_tools(self):
        return self.registry.keys()

    def get_active_tools(self):
        return self.active_tools

    def set_active_tools(self, new_active_tools:list[str]):
        invalid_tools = set(new_active_tools) - set(self.registry)
        if invalid_tools:
            raise ValueError(f'{new_active_tools} is not supported')
        self.active_tools = [self.registry[tool_name] for tool_name in new_active_tools]

def wire_tools_registry():
    repository = DocumentRepositoryChromaDB()
    return ToolRegistry(repository)