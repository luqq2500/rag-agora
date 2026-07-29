import os.path
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Any
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

base_path = Path(__file__).resolve().parent.parent
chroma_persists_path = base_path / "dev" / "assets" / "db" / "chroma"

class AgoraDocumentVectorRepository(ABC):
    @abstractmethod
    def similarity_search(self, query: str, k: int, filter: Optional[dict[str, Any]])->list[Document]:
        pass
    @abstractmethod
    def ranking_search(self, query: str, k: int, fetch_k: int, lambda_mult: float, filter: Optional[dict[str, Any]])->list[Document]:
        pass
    @abstractmethod
    def get_metadata(self)-> dict[str, Any]:
        pass

class VectorRepositoryChromaDB(AgoraDocumentVectorRepository):
    def __init__(self, persist_path: str= chroma_persists_path, collection_name: str = 'agora_documents', embed_model:str= 'sentence-transformers/all-mpnet-base-v2'):
        if not os.path.exists(chroma_persists_path):
            raise FileNotFoundError(f"File to persistent paths not found.")
        try:
            self.chroma = Chroma(
                persist_directory=persist_path,
                embedding_function=HuggingFaceEmbeddings(model_name=embed_model),
                collection_name=collection_name,
            )
            collection = self.chroma._client.get_collection(name=collection_name)
            count = collection.count()
            if count == 0:
                raise ValueError(f"Collection {collection_name} is empty.")
            self.cached_metadata = None

        except Exception as e:
            raise RuntimeError(f'Failed to initialize chroma: {e}')

    def similarity_search(self, query: str, k: int=4, filter: Optional[dict[str, Any]]=None)-> Optional[list[Document]]:
        """
        Performs standard semantic vector search to retrieve documents closest to the query.

        Returns top-k results with the highest similarity, prioritizing exact relevance over diversity.

        Guidance:
        - Use for direct, specific matches where redundant information across documents is acceptable.
        - The `filter` argument accepts ONE key-value pair (e.g., {"sectors": "government"}).
        - For queries requiring MULTIPLE independent metadata constraints (e.g., comparing 'government' vs 'private'),
          generate multiple tool calls in parallel or sequence—one per metadata value.
        """
        return self.chroma.similarity_search(query=query, k=k, filter=filter)

    def ranking_search(self, query: str, k: int=4, fetch_k: int=20, lambda_mult: float=0.5, filter: Optional[dict[str, Any]]=None) -> Optional[list[Document]]:
        """
        Performs Maximal Marginal Relevance (MMR) search to balance semantic relevance and document diversity.

        Guidance:
        - For broad topics: Increase `fetch_k` (e.g., 40-60) and lower `lambda_mult` (e.g., 0.2-0.4) for broader coverage.
        - For narrow queries: Increase `lambda_mult` (e.g., 0.7-1.0) to focus strictly on direct similarity.
        - Ensure `fetch_k` is significantly larger than `k`.
        - The `filter` argument accepts ONE key-value pair (e.g., {"sectors": "government"}).
        - For comparative or multi-domain analysis, generate separate tool calls in parallel for each metadata scope.

        """
        return self.chroma.max_marginal_relevance_search(query=query, k=k, fetch_k=fetch_k, lambda_mult=lambda_mult, filter=filter)

    def get_metadata(self)->dict[str, Any]:
        """
        Retrieves all unique metadata keys and available categorical values present in the repository.

        Guidance:
        - Call this tool BEFORE performing `ranking_search` or `similarity_search` if the query implies structured filtering
          (e.g., searching by specific authors, regions, sectors, or document types).
        - Use the output keys and values to build valid `filter` dictionaries. Do not invent or guess filter keys.
        """
        if self.cached_metadata is not None:
            return self.cached_metadata

        documents = self.chroma.get(include=['metadatas'])
        unique_metadata = {}
        for metadata in documents['metadatas']:
            for key, values in metadata.items():
                if key not in unique_metadata:
                    unique_metadata[key] = []
                if isinstance(values, str):
                    disjoin_values = values.split(", ")
                    for value in disjoin_values:
                        if value not in unique_metadata[key]:
                            unique_metadata[key].append(value)
                elif isinstance(values, int):
                    value = str(values)
                    if value not in unique_metadata[key]:
                        unique_metadata[key].append(value)
        self.cached_metadata = unique_metadata
        return unique_metadata

