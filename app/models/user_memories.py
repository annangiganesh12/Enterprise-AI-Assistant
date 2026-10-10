
from sqlalchemy import Column,Integer,Text,ForeignKey
from app.database.base import Base
from sqlalchemy.orm import relationship

class UserMemory(Base):

    __tablename__ = "user_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer,ForeignKey("Users.id"),nullable=False, index=True)
    memory = Column(Text, nullable=False)

    user = relationship(
        "User",
        back_populates="memories"
    )