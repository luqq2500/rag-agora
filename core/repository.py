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
    def get_search_filters(self)-> dict[str, Any]:
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
        Search the governance corpus. Returns `k` document chunks selected by Maximal
        Marginal Relevance: `fetch_k` candidates are retrieved by embedding similarity,
        then `k` are chosen from them trading off similarity against diversity.

        Parameters:
        - `query`: the search text. Embedded and matched against chunk embeddings, so
          phrase it as the substance you want to find, not as a question.
        - `k`: how many chunks are returned. Raise it when a provision is long or split
          across chunks; keep it low when confirming a specific fact. Large values
          crowd out reasoning space and may truncate on small-context models.
        - `fetch_k`: candidate pool size. Must be substantially larger than `k` or MMR
          has nothing to select among and degenerates into plain similarity search.
        - `lambda_mult`: 0.0 to 1.0. High (0.7–1.0) keeps results tight to the query;
          low (0.2–0.4) spreads them across distinct documents. Use high values when
          you know what you are looking for, low values when surveying an unfamiliar
          topic.
        - `filter`: optional metadata constraint. See below.

        Suggested settings:
        - Precise lookup of one provision or defined term: k=4-6, fetch_k=20,
          lambda_mult=0.7-1.0.
        - Wide survey of an unfamiliar topic: k=8-10, fetch_k=40-60,
          lambda_mult=0.2-0.4.

        Filter constraints:
        - Accepts exactly ONE key-value pair, e.g. {"sectors": "government"}. Lists
          such as {"sectors": ["government", "private"]} are invalid, as is combining
          two different keys in one call.
        - To cover several values, issue separate calls, one per value. Calls that do
          not depend on each other's results should be emitted together in a single
          message: they then execute as one batch.
        - Matching is exact string equality. Some fields store several values joined
          into one string, so a filter on one value alone will miss documents that do
          contain it. A filtered search that returns nothing is therefore weak
          evidence about the corpus — re-run unfiltered before drawing any conclusion
          about coverage.
        - Use `get_search_filters` to obtain valid keys and values. Never guess them.

        Returns chunks with their metadata. Nearest matches are returned regardless of
        whether anything relevant exists; there is no relevance floor. Inspect what
        comes back rather than assuming a high rank implies a match.

        """
        return self.chroma.max_marginal_relevance_search(query=query, k=k, fetch_k=fetch_k, lambda_mult=lambda_mult, filter=filter)

    def get_search_filters(self)->dict[str, Any]:
        """
        List the metadata keys and values available for filtering corpus searches.
        Call this before any filtered search and build filters only from what it
        returns.

        Filterable keys:
        - `authority`: the enacting body — a US state, a federal department, a
          national government, or an international organization.
        - `status`: one of "Enacted", "Proposed", "Defunct".
        - `collection`: broad document family, e.g. US federal laws, US state and
          local laws, Chinese law and policy, corporate policies and commitments.
        - `sectors`: "government" or "private".
        - `strategies`, `applications`, `risks`, `harms`, `incentives`: analytical
          taxonomy applied across the corpus.

        Also returned but not usefully filterable: `agora_id`, `segment`,
        `current_chunk`, `total_chunks` are chunking bookkeeping and should be
        ignored.

        Two caveats about the values returned:
        - Some documents carry several values in one field, stored joined into a
          single string. An exact-match filter on one value alone will not match
          those documents.
        - Values containing commas are split when listed here, so a few entries are
          fragments of longer values that were never stored in that form and cannot
          match anything.

        Treat filters as an optimization that narrows a search, never as an
        authoritative statement of what the corpus contains.
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

        exclude_keys = {"agora_id", "segment", "current_chunk", "total_chunks"}
        unique_metadata = {k: v for k, v in unique_metadata.items() if k not in exclude_keys}
        self.cached_metadata = unique_metadata
        return unique_metadata

