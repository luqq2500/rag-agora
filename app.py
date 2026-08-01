from core.registry import ModelRegistry, wire_llm_system_instruction, wire_tools_registry, ToolRegistry
from core.repository import VectorRepositoryChromaDB, AgoraDocumentVectorRepository
from core.service import RAG, Agentic
from core.usecase import ChatAgoraResearchAssistant
from InquirerPy import inquirer

def main():
    model_registry = ModelRegistry()

    select_mode = inquirer.select(
        message="Select AGORA Assistant mode: ",
        choices=["RAG", "Agentic"]
    ).execute()

    select_model = inquirer.select(
        message="Select reasoning model: ",
        choices=model_registry.get_supported_models()
    ).execute()

    model = model_registry.construct_model(select_model)

    if select_mode == "RAG":
        document_repository = VectorRepositoryChromaDB()
        service = RAG(document_repository, model)
    elif select_mode == "Agentic":
        tool_registry = wire_tools_registry()
        service = Agentic(model, tool_registry.get_tools())
    else:
        raise Exception("Invalid mode")

    usecase = ChatAgoraResearchAssistant(service=service)
    usecase.run()

if __name__ == "__main__":
    main()