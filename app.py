from core.registry import ModelRegistry, wire_llm_system_instruction, wire_tools_registry, ToolRegistry
from core.repository import DocumentRepositoryChromaDB
from core.service import RAG, AgenticRAG
from core.usecase import ChatAgoraResearchAssistant
from InquirerPy import inquirer

if __name__ == "__main__":

    model_registry = ModelRegistry()
    repository = DocumentRepositoryChromaDB()
    tool_registry = ToolRegistry(repository)

    select_mode = inquirer.select(
        message = "Select AGORA Assistant mode: ",
        choices = ["RAG", "Agentic"]
    ).execute()

    select_model = inquirer.select(
        message = "Select reasoning model: ",
        choices = model_registry.get_supported_models()
    ).execute()

    model = model_registry.construct_model(select_model)

    if select_mode == "RAG":
        service = RAG(repository, model, wire_llm_system_instruction())
    elif select_mode == "Agentic":
        service = AgenticRAG(model, tool_registry.get_active_tools())
    else:
        raise Exception("Invalid mode")

    usecase = ChatAgoraResearchAssistant(service=service)
    usecase.run()