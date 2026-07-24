from core.model import wire_model
from core.repository import wire_repository
from core.rag import AgoraRagService
from core.usecase import AskRagAgoraUseCase

if __name__ == "__main__":
    repository = wire_repository(repository='chroma', collection_name='agora_documents')
    model = wire_model(model_name='phi3.5:latest', temperature=0.3)
    rag_service = AgoraRagService(repository, model)
    usecase = AskRagAgoraUseCase(rag_service)
    usecase.run()

