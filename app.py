from infra.model import OllamaModel
from infra.repository import ChromaDB
from infra.rag import RAGService
from usecase import AskRagAgoraUseCase

if __name__ == "__main__":
    vector_repository = ChromaDB()
    model = OllamaModel()
    rag_service = RAGService(vector_repository, model)
    usecase = AskRagAgoraUseCase(rag_service)
    usecase.run()

