
from langgraph.graph import StateGraph, START,END

from app.langgraph.state import RAGState
from app.langgraph.context import RAGContext
from app.langgraph.node_functions import (
    retrieve_node,generate_node, 
    load_memory_node,
    extract_memory_node,
    save_memory_node,
    load_conversation_memory_node,
    update_conversation_memory_node,
    save_conversation_memory_node,
    router_node,
    tool_agent_node
    )

from langgraph.prebuilt import ToolNode,tools_condition
from app.tools import tools

from app.core.config import settings

from langgraph.checkpoint.postgres import PostgresSaver

graph = StateGraph(
    RAGState,
    context_schema=RAGContext
)

tool_execution_node = ToolNode(tools, handle_tool_errors=True)

def route_query(state: RAGState):

    route = state["route"]

    if route == "rag":
        return "rag"
    
    elif route == "memory":
        return "memory"

    elif route == "conversation_memory":
        return "conversation_memory"

    elif route == "tool":
        return "tool"

    return "general"

# add nodes
graph.add_node("load_memory",load_memory_node)
graph.add_node("load_conversation_memory",load_conversation_memory_node)
graph.add_node("router",router_node)
graph.add_node("retrieve",retrieve_node)
graph.add_node("tool_agent",tool_agent_node)
graph.add_node("tool_execution",tool_execution_node)
graph.add_node("generate",generate_node)
graph.add_node("extract_memory",extract_memory_node)
graph.add_node("save_memory",save_memory_node)
graph.add_node("update_conversation_memory",update_conversation_memory_node)
graph.add_node("save_conversation_memory",save_conversation_memory_node)

# add edges
graph.add_edge(START,"load_memory")
graph.add_edge("load_memory","load_conversation_memory")
graph.add_edge("load_conversation_memory","router")
graph.add_conditional_edges(
    "router",
    route_query,
    {
        "rag":"retrieve",
        "memory":"generate",
        "conversation_memory":"generate",
        "general":"generate",
        "tool":"tool_agent"
    }
    )
graph.add_edge("retrieve","generate")
graph.add_conditional_edges(
    "tool_agent",
    tools_condition,
    {
        "tools":"tool_execution",
        "__end__":"generate"
    }
    )
graph.add_edge("tool_execution","tool_agent")
graph.add_edge("generate",END)