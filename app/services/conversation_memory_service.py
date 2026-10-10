
from sqlalchemy.orm import Session
from app.models.conversation_memory import ConversationMemory

def get_conversation_memory(
        db: Session,
        user_id: int
):

    return (
        db.query(ConversationMemory)
        .filter(
            ConversationMemory.user_id == user_id
        )
        .first()
    )

def save_conversation_memory(
        db: Session,
        user_id: int,
        summary: str
):

    memory = (
        db.query(ConversationMemory)
        .filter(
            ConversationMemory.user_id == user_id
        )
        .first()
    )

    if memory:
        memory.summary = summary

    else:
        memory = ConversationMemory(
            user_id = user_id,
            summary = summary
        )
        db.add(memory)

    db.commit()
    db.refresh(memory)

    return memory  