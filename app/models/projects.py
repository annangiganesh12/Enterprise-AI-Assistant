from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database.base import Base



class Project(Base):

    __tablename__ = "projects"

    id = Column(Integer,primary_key=True,index=True)
    name = Column(String,nullable=False,unique=True)
    description = Column(String)
    status = Column(String,nullable=False)