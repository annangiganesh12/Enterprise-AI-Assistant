
from dataclasses import dataclass
from sqlalchemy.orm import Session

@dataclass
class RAGContext:
    db: Session
    