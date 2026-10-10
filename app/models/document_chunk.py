
from sqlalchemy import Column, Integer, Text, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector


from app.database.base import Base

class DocumentChunk(Base):

    __tablename__ = "document_chunks"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    document_id = Column(
        Integer,
        ForeignKey("documents.id"),
        nullable=False
    )

    chunk_index = Column(
        Integer,
        nullable=False
    )

    content = Column(
        Text,
        nullable=False
    )

    page_number = Column(
        Integer,
        nullable=True
    )

    strategy_id = Column(
        String,
        index=True,
        nullable=True
    )

    metadata_info = Column(
        JSONB,
        nullable=True
    )

    embedding = Column(

        Vector(384),
        nullable=False
    )

    document = relationship(
        "Documents",
        back_populates="chunks"
    )

