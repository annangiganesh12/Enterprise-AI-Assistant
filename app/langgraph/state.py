
from typing import TypedDict,Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class RAGState(TypedDict):

    messages: Annotated[list[BaseMessage], add_messages]
    query: str
    user_id: int
    active_document_id: int | None
    retrieved_documents: list[dict]
    memories: list[str]
    answer: str
    memory_to_save: str | None
    conversation_summary: str
    current_thread_summary: str
    route: str