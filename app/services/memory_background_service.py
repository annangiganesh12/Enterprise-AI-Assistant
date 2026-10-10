from typing import Any, Dict
from app.langgraph.node_functions import (
    extract_memory_node,
    save_memory_node,
    update_conversation_memory_node,
    save_conversation_memory_node
)
from langgraph.runtime import Runtime
from app.langgraph.context import RAGContext

async def run_memory_updates(state: Dict[str, Any], db):
    """
    Executes the memory update chain as a background process.
    Since we are outside the StateGraph, we manually invoke the node functions.
    """
    try:
        # Create a mock runtime context for the nodes
        runtime = Runtime(context=RAGContext(db=db))

        # 1. Extract Memory
        extract_result = extract_memory_node(state, runtime)
        if extract_result and extract_result.get("memory_to_save"):
            state.update(extract_result)
            # 2. Save Memory
            save_memory_node(state, runtime)

        # 3. Update Conversation Memory
        update_result = update_conversation_memory_node(state, runtime)
        if update_result:
            state.update(update_result)
            # 4. Save Conversation Memory
            save_conversation_memory_node(state, runtime)

    except Exception as e:
        print(f"Background Memory Update Error: {str(e)}")
