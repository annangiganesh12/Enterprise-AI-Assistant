
from sqlalchemy import Column,Integer,String
from app.database.base import Base
from sqlalchemy.orm import relationship
from app.models.user_document import user_documents

class User(Base):

    __tablename__ = "Users"

    id = Column(Integer, primary_key=True,index=True)
    username = Column(String,unique=True)
    email = Column(String,unique=True)
    hashed_password = Column(String)
    role = Column(
        String,
        nullable=False,
        default="employee"
    )

    documents = relationship(
        "Documents",
        secondary="user_documents",
        back_populates="user"
    )

    memories = relationship(
        "UserMemory",
        back_populates="user"
    )

    conversation_memory = relationship(
        "ConversationMemory",
        back_populates="user",
        uselist=False
    )
    