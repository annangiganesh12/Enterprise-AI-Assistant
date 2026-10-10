
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.models.user_document import user_documents

from app.database.base import Base

class Documents(Base):

    __tablename__ = "documents"

    id = Column(Integer,primary_key=True,index=True)
    filename = Column(String,nullable=False)
    file_path = Column(String,nullable=False)
    content_type = Column(String, nullable=False)
    file_hash = Column(String,nullable=False,index=True)
    current_strategy = Column(String, nullable=True, index=True)
    is_global = Column(Boolean, default=False, nullable=False)


    user = relationship(
        "User",
        secondary="user_documents",
        back_populates="documents"
    )

    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan"
    )
    
