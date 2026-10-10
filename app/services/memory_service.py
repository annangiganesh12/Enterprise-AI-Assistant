
from sqlalchemy.orm import Session
from app.models.user_memories import UserMemory

def create_memory(
        db: Session,
        user_id: int,
        memory: str
):

    new_memory = UserMemory(
        user_id = user_id,
        memory = memory
    )

    db.add(new_memory)
    db.commit()
    db.refresh(new_memory)

    return new_memory

def get_memories(
        db: Session,
        user_id: int
):

    return(
        db.query(UserMemory).filter(UserMemory.user_id == user_id)
        .all()
    )

def delete_memory(
        db: Session,
        memory_id: int,
        user_id: int
):

    memory = (
        db.query(UserMemory)
        .filter(
            UserMemory.id == memory_id,
            UserMemory.user_id == user_id
        )
        .first()
    )

    if memory:

        db.delete(memory)
        db.commit()

    return memory
    