from abc import ABC, abstractmethod
from typing import Optional, Generator

from langchain_core.documents import Document

from core.model import ModelService
from core.repository import VectorRepository

class RAGService(ABC):
    @abstractmethod
    def run(self, query: str)-> Generator[str, None, None]:
        pass

class AgoraRagService(RAGService):
    def __init__(self, repository: VectorRepository, model: ModelService):
        self.repository = repository
        self.model = model
        self.instruction = """
        You are Agora, a sophisticated AI Governance Advisor. Your tone is professional, thoughtful, and articulate, similar to a high-level policy researcher at a leading institute. 
        GUIDELINES:
        1. Grounding: You rely strictly on the provided context. If the information isn't present, state clearly: "I apologize, but the provided documents do not contain information regarding [Topic]."
        2. Recency Constraints: If the user query specifically asks for "recent", "latest", "newest", or "current" items, you must evaluate the timestamps, dates, or version numbers provided in the Metadata section of each context. In such cases, base your answer exclusively on the document(s) with the most recent timestamp available in the context. Explicitly acknowledge that you are providing information from the latest source (e.g., "According to the latest documentation from [Date]...").
        3. Nuance: When summarizing, capture the complexity of the topic. Avoid overly simplified bullet points; instead, use fluid, well-structured paragraphs.
        4. Intellectual Honesty: If documents present conflicting views, acknowledge them neutrally (e.g., "While document A suggests X, document B emphasizes Y").
        5. Style: Use clear, precise language. Avoid filler phrases, apologies, or meta-commentary (e.g., do not say "As an AI model..."). If you can't answer, be direct and brief.
        6. Formatting: Use Markdown for readability, but keep the tone conversational yet academic.
        """

    def run(self, query: str):
        retrieval: Optional[list[Document]] = self.repository.search(
            query=query,
            strategy='mmr'
        )

        contexts = [f"Metadata: {document.metadata}\nContent: {document.page_content}" for document in retrieval]
        context_prompt = f"CONTEXTS: \n{', '.join(contexts)}"
        query_prompt = f"QUERY: {query}."
        user_prompt = f"{context_prompt}. {query_prompt}"
        for token in self.model.invoke(system_prompt=self.instruction, user_prompt=user_prompt):
            print(token, end="", flush=True)
        print("\n")
