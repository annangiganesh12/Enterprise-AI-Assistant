
from langgraph.runtime import Runtime

from pydantic import BaseModel, Field

from app.langgraph.state import RAGState
from app.langgraph.context import RAGContext
from app.services.retrival_service import retrieve_and_rank
from app.services.memory_service import get_memories,create_memory
from app.services.conversation_memory_service import get_conversation_memory,save_conversation_memory

from langchain_core.messages import HumanMessage,AIMessage
from app.services.llm_service import llm

from app.tools import tools

tool_llm = llm.bind_tools(tools)

def retrieve_node(
        state:RAGState,
        runtime:Runtime[RAGContext]
):

    query = state['query']
    user_id = state['user_id']

    db = runtime.context.db

    documents = retrieve_and_rank(
        query=query,
        db=db,
        user_id=user_id,
        retrival_k=20,
        rerank_k=10
    )

    return {
       "retrieved_documents": [
        {
            "content": document.content,
            "page_number": document.page_number,
            "document_id": document.document_id
        }
        for document in documents
      ]
      }


def summarize_current_thread(state:RAGState):

    messages = state.get("messages",[])

    if len(messages) < 12:
        return {}

    old_messages = messages[:-6]
    recent_messages = messages[-6:]

    conversation = "\n".join(
        f"{message.type}: {message.content}"
        for message in old_messages
    )

    prompt = f"""
Summarize the important information from this conversation.

Preserve:
- decisions made
- important tool results those are related to company postgresql database
- important facts
- user requirements
- project context
- unresolved questions
- important technical details

Do not include unnecessary small talk.

Conversation:
{conversation}
"""
    response = llm.invoke(
        [HumanMessage(content=prompt)]
    )

    return {
        "current_thread_summary":response.content,
        "messages":recent_messages
    }

def generate_node(state: RAGState):

    route = state.get("route","general")

    query = state['query']

     # CURRENT THREAD

    current_thread_summary = state.get("current_thread_summary","")
  
    conversation_history = "\n".join(
        f"{message.type}: {message.content}"
        for message in state.get("messages", [])
    )

    prompt_parts = [
        """
You are an enterprise AI assistant.

Answer the user's current question accurately and directly.

Use only the context that is relevant to the current question.

Do not invent facts or make unsupported assumptions.

If the available information is insufficient,
clearly say that you do not have enough information.

Keep the answer relevant and concise.
"""
    ]

    # MEMORY ROUTE

    if route == "memory":

        memories = state.get("memories", [])

        if memories:

            memory_context = "\n".join(
                f"- {memory}"
                for memory in memories
            )

            prompt_parts.append(
                f"""
### Relevant long-term memory

{memory_context}
"""
            )

    # CONVERSATION MEMORY ROUTE

    if route == "conversation_memory":

        conversation_summary = state.get(
            "conversation_summary",
            ""
        )

        if conversation_summary:

            prompt_parts.append(
                f"""
### Summary of previous threads

{conversation_summary}
"""
            )

    # RAG ROUTE

    if route == "rag":

        documents = state.get(
            "retrieved_documents",
            []
        )

        if documents:

            context = "\n\n".join(
                document["content"]
                for document in documents
            )

            prompt_parts.append(
                f"""
### Relevant knowledge-base information

{context}
"""
            )

    # CURRENT THREAD CONVO HISTORY

    if conversation_history:

        prompt_parts.append(
            f"""

### Earlier context from the current thread conversation

{current_thread_summary}

### Latest conversation of the current thread conversation

{conversation_history}

"""
        )

    # USER QUESTION

    prompt_parts.append(
        f"""
### Current user question

{query}
"""
    )

    prompt = "\n\n".join(prompt_parts)

    response = llm.invoke(
        [HumanMessage(content=prompt)]
    )

    return {
        "answer": response.content,
        "messages": [
            AIMessage(content=response.content)
        ]
    }                                             



def load_memory_node(state: RAGState,runtime: Runtime[RAGContext]):

    user_id = state["user_id"]
    db = runtime.context.db

    memories = get_memories(
        db=db,
        user_id=user_id
    )

    return {
        "memories":[
            memory.memory
            for memory in memories
        ]
    }

class MemoryExtraction(BaseModel):
    memory: str | None = Field(
        description="A useful long-term fact or preference about the user. Return null if nothing should be remembered."
    )

def extract_memory_node(state: RAGState, runtime: Runtime[RAGContext]):
    query = state["query"]
    user_id = state["user_id"]

    conversation_history = "\n".join(
        f"{message.type}: {message.content}"
        for message in state.get("messages",[])
    )
    prompt = f"""
       You are responsible for identifying useful long-term memories about a user.

       Conversation:
        {conversation_history}

       Current user message:
        {query}

       Identify ONE useful long-term fact or preference about the user
       that would be useful in future conversations.

       Examples of useful memories:
       - User prefers concise explanations.
       - User prefers Python examples.
       - User is working on an AI assistant project.

       Do NOT store:
       - Facts from uploaded documents.
       - Temporary questions.
       - Information that is only relevant to this conversation.
       - The assistant's own statements.
       - General knowledge.

       If there is nothing useful to remember, return null.
      """

    structured_llm = llm.with_structured_output(MemoryExtraction)

    result = structured_llm.invoke(prompt)

    return {
        "memory_to_save": result.memory
    }

def save_memory_node(state: RAGState, runtime: Runtime[RAGContext]):

    memory = state.get("memory_to_save")

    if not memory:
        return {}
    db = runtime.context.db

    create_memory(
        db = db,
        user_id=state["user_id"],
        memory=memory
    )

    return {}

def load_conversation_memory_node(state: RAGState, runtime: Runtime[RAGContext]):

    user_id = state["user_id"]

    db = runtime.context.db

    memory = get_conversation_memory(
        db = db,
        user_id= user_id
    )

    return {
        "conversation_summary":(
            memory.summary
            if memory
            else ""
        )
    }

def update_conversation_memory_node(state: RAGState, runtime: Runtime[RAGContext]):

    old_summary = state.get(
        "conversation_summary",""
    )

    conversation_history = "\n".join(
        f"message.type: {message.content}"
        for message in state.get("messages",[])
    )

    prompt = f"""
        You maintain a cumulative summary of the user's previous conversations.

        ### Existing cumulative summary
         {old_summary}

        ### Current conversation
         {conversation_history}

        Create an updated cumulative summary by combining the
        existing cumulative summary with the important information
        from the current conversation.

        Important requirements:
         - Preserve important information from the existing summary.
         - Add important information from the current conversation.
         - Focus on projects, technical topics, goals, decisions,
           and other information that may be useful in future conversations.
         - Remove repetition.
         - Do not include trivial conversational details.
         - Do not invent information.
         - Return only the updated cumulative summary.

         ### Updated cumulative summary
      """

    result = llm.invoke(prompt)
    new_summary = result.content

    MAX_SUMMARY_LENGTH = 6000

    if len(new_summary) > MAX_SUMMARY_LENGTH:

            compression_prompt = f"""
                Compress the following cumulative conversation summary.

                Preserve important information about:
                 - projects
                 - technical work
                 - goals
                 - decisions
                 - important historical context

                Remove repetition and trivial details.

                Keep the summary concise while preserving useful
                information for future conversations.

                ### Summary
                 {new_summary}

                Return only the compressed summary.
              """

            compressed_summary = llm.invoke(compression_prompt)

            new_summary = compressed_summary.content

    content = new_summary
            
    if isinstance(content,str):
        new_summary = content

    elif isinstance(content,list):
        new_summary = "\n".join(
        item["text"]
        for item in content
        if isinstance(item, dict) and item.get("type") == "text"
    )

    else:
        new_summary = str(content)
            
    return{
        "conversation_summary":new_summary
    }

def save_conversation_memory_node(state: RAGState, runtime: Runtime[RAGContext]):

    user_id = state["user_id"]

    summary = state.get(
        "conversation_summary",
        ""
    )
    if not summary:
        return {}
    db = runtime.context.db
    save_conversation_memory(
        db=db,
        user_id=user_id,
        summary=summary
    )

    return {}

from typing import Literal
from pydantic import BaseModel

class RouterOutput(BaseModel):

    route: Literal["general","rag","memory","conversation_memory","tool"]

structured_llm = llm.with_structured_output(RouterOutput)


def router_node(state: RAGState, runtime: Runtime[RAGContext]):
    query = state["query"]
    user_id = state["user_id"]
    db = runtime.context.db

    # 1. CHECK IF USER HAS ANY DOCUMENTS
    # This ensures that if the user has uploaded data, we prioritize using it over general knowledge
    from app.models.document import Documents
    from app.models.user_document import user_documents

    has_documents = db.query(Documents).join(user_documents).filter(user_documents.c.user_id == user_id).first() is not None

    # 2. CONSTRUCT PROMPT BASED ON DOCUMENT PRESENCE
    doc_presence_context = "The user HAS uploaded documents to the knowledge base." if has_documents else "The user has NOT uploaded any documents."

    prompt = f"""
       You are the routing classifier for an enterprise AI assistant.
       Context: {doc_presence_context}

       Classify the query into exactly ONE route.

       RAG:
       Requires information from the user's uploaded documents or company-wide knowledge base (e.g., policies, manuals).
       IMPORTANT: If the user has uploaded documents and the query is technical, domain-specific, or refers to "the PDF", "the file", "the document", or "uploaded content", you MUST use this route.
       Even if the question seems answerable by general knowledge, if documents are present, check them first to provide the most specific and accurate answer based on the user's own data.

       MEMORY:
       Requires stored long-term information specifically about the user.

       CONVERSATION_MEMORY:
       Requires information from previous conversations.

       TOOL:
       Requires an external tool:
       - Analytics Tool → ALWAYS use this for any "analysis", "report", "summary", "trends", "insights", "charts", or "aggregations" on tabular datasets (CSV/Excel/Uploaded files). Do NOT use the SQL tool for these.
       - SQL Tool → structured factual information (like "Who is the manager of X?") in the company's core operational database.
       - Calculator → mathematical calculations

       GENERAL:
       Can be answered using general knowledge. Return this router ONLY if the query is completely unrelated to technical topics, the user's documents, their memory, or if the user has no documents uploaded and the query is general.

       Query:
        {query}
    """

    result = structured_llm.invoke(prompt)
    print("ROUTER RESULT:", result.route)

    return {
        "route": result.route
    }


def tool_agent_node(state: RAGState):

    messages = state["messages"]

    tool_prompt = HumanMessage(
        content="""
        You are the tool agent.

        Choose the appropriate tool based on the required information source:

        - analytics_tool → ALWAYS use this for any "analysis", "reports", "trends", "charts", "aggregations", "summary reports", or "insights" on tabular datasets (CSV/Excel/Uploaded files).
        - company_sql_tool → structured factual information in the company's core operational database (e.g., "Who is the manager of X?").
        - calculator → mathematical calculations

        IMPORTANT: If the user asks for an "analysis" or "report" of a CSV/uploaded file, you MUST use the analytics_tool. Do NOT attempt to use the sql_tool for general analysis reports.

        Use a tool when the question requires information or computation
        that the tool can provide more reliably.

        If multiple tools are needed, use them in sequence.
        Do not invent information or use the wrong information source.
        """
    )


    response = tool_llm.invoke(
        messages + [tool_prompt]
    )

    print("TOOL CALLS:")
    print(response.tool_calls)

    return {
        "messages": [response]
    }