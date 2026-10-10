from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.retrival_service import retrieve_and_rank
from typing import List

# Setup local DB session for evaluation
engine = create_engine(settings.DATABASE_URL.replace("postgresql+psycopg://", "postgresql://"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def run_retrieval(query: str) -> List[str]:
    """
    Bridge function for retrieval evaluation.
    Handles DB session and provides a simple (query) -> List[str] interface.
    """
    db = SessionLocal()
    try:
        # Use a default test user ID (1) for evaluation purposes
        test_user_id = 1

        # Call existing orchestration: Hybrid Search -> Rerank
        chunks = retrieve_and_rank(
            query=query,
            db=db,
            user_id=test_user_id,
            retrival_k=10,
            rerank_k=5
        )

        # Return only the text content of the chunks for deepeval
        return [chunk.content for chunk in chunks]
    except Exception as e:
        print(f"Error during retrieval: {e}")
        return []
    finally:
        db.close()
