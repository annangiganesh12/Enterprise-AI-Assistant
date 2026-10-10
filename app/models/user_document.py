
from sqlalchemy import Table,Column,Integer, ForeignKey

from app.database.base import Base

user_documents = Table(
    "user_documents",
    Base.metadata,

    Column(
        "user_id",
        Integer,
        ForeignKey("Users.id"),
        primary_key=True
    ),

    Column(
        "document_id",
        Integer,
        ForeignKey("documents.id"),
        primary_key=True
    )
)
