
from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base

class ConversationMemory(Base):

    __tablename__ = "conversation_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("Users.id"),
        nullable=False,
        unique=True,
        index=True
    )
    summary = Column(Text,nullable=False)

    user = relationship(
        "User",
        back_populates="conversation_memory"
    )