from abc import ABC, abstractmethod
from typing import Generator, Optional, Callable, Any, Literal

from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.constants import END, START
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from core.registry import wire_llm_system_instruction
from core.repository import AgoraDocumentVectorRepository


class AgoraResearchAssistantService(ABC):
    @abstractmethod
    def run(self, query: str)-> Generator[str, None, None]:
        pass

class Agentic(AgoraResearchAssistantService):
    def __init__(self, llm: BaseChatModel, tools: list[Callable[..., Any]]):
        if not tools:
            raise ValueError(f"Agents are not given any tools.")
        self.llm = llm.bind_tools(tools)
        self.tools = tools
        self.system_instruction = wire_llm_system_instruction()
        self.environment = self.compile_env()

    def call_llm(self, state: MessagesState):
        system = self.system_instruction
        response = self.llm.invoke([SystemMessage(content=system)] + state["messages"])
        return {"messages": response}

    def should_call_tool(self, state: MessagesState)->Literal["call_tool", "__end__"]:
        last = state["messages"][-1] # check the last cleaned message from MessageState AIMessage
        if isinstance(last, AIMessage) and last.tool_calls:
            return "call_tool"
        return END

    def compile_env(self):
        workflow = StateGraph(MessagesState)
        workflow.add_node("agent", self.call_llm)
        workflow.add_node("tools", ToolNode(self.tools))
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", self.should_call_tool, {"call_tool": "tools", END: END})
        workflow.add_edge("tools", "agent")
        return workflow.compile()

    def run(self, prompt: str):
        initial_input = {"messages": ("user", prompt)}
        result = self.environment.invoke(initial_input)
        clean_message = result["messages"][-1]
        print(clean_message.text, end="", flush=True)
        print("\n")

class RAG(AgoraResearchAssistantService):
    def __init__(self, repository: AgoraDocumentVectorRepository, model: BaseChatModel):
        self.model = model
        self.repository = repository
        self.instruction = wire_llm_system_instruction()

    def run(self, query: str):
        retrieval = self.retrieve(query)
        prompt = self.augment(query, retrieval)
        for chunk in self.model.stream(prompt):
            content = getattr(chunk, 'text', getattr(chunk, 'content', '')) # handle Google format .text vs others .content
            print(content, end="", flush=True)
        print('\n')

    def retrieve(self, query: str) -> list[Document] | None:
        retrieval: Optional[list[Document]] = self.repository.ranking_search(
            query=query,
            k=4,
            filter=None
        )
        return retrieval

    def augment(self, query: str, retrieval: list[Document] | None) -> list[SystemMessage | HumanMessage]:
        contexts = [f"Metadata: {document.metadata}\nContent: {document.page_content}" for document in retrieval or []]
        context_prompt = f"CONTEXTS: \n{', '.join(contexts)}"
        query_prompt = f"QUERY: {query}."
        user_prompt = f"{context_prompt}. {query_prompt}"
        prompt = [SystemMessage(self.instruction), HumanMessage(user_prompt)]
        return prompt