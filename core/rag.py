from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Generator

from langchain_core.documents import Document

from core.model import ModelService
from core.repository import VectorRepository

class RAGService(ABC):
    @abstractmethod
    def run(self, query: str)-> Generator[str, None, None]:
        pass

class AgoraRagService(RAGService):
    def __init__(self, repository: VectorRepository, model: ModelService, instruction):
        self.repository = repository
        self.model = model
        self.instruction = instruction

    def run(self, query: str):
        retrieval: Optional[list[Document]] = self.repository.similarity_search(
            query=query,
            strategy='mmr',
            k=10
        )
        contexts = [f"Metadata: {document.metadata}\nContent: {document.page_content}" for document in retrieval]
        context_prompt = f"CONTEXTS: \n{', '.join(contexts)}"
        query_prompt = f"QUERY: {query}."
        user_prompt = f"{context_prompt}. {query_prompt}"
        for token in self.model.invoke(system_prompt=self.instruction, user_prompt=user_prompt):
            print(token, end="", flush=True)
        print("\n")

def wire_instruction(file_name: str='instruction.md'):
    base_dir = Path(__file__).parent.resolve()
    return Path(base_dir / file_name).read_text()