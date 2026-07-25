from pathlib import Path

from core.model import wire_model
from core.repository import wire_repository
from core.rag import AgoraRagService, wire_instruction
from core.usecase import AskRagAgoraUseCase

if __name__ == "__main__":
    repository = wire_repository(repository='chroma', collection_name='agora_documents')
    model = wire_model(model_name='phi3.5:latest', temperature=0.3)
    instruction = wire_instruction()
    rag_service = AgoraRagService(repository, model, instruction)
    usecase = AskRagAgoraUseCase(rag_service)
    usecase.run()

