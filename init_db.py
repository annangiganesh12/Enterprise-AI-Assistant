from app.database.base import Base
from app.database.database import engine
from app.core.config import settings

def init_db():
    try:
        print(f"Connecting to database... (Using URL: {settings.DATABASE_URL})")

        # Import all models here to register them with Base.metadata
        # This prevents circular imports in app/database/base.py
        from app.models.user import User
        from app.models.company import Department, Employee, LeaveRecord
        from app.models.customers import Customer, Sale
        from app.models.projects import Project
        from app.models.document import Documents
        from app.models.document_chunk import DocumentChunk
        from app.models.user_document import user_documents
        from app.models.user_memories import UserMemory
        from app.models.conversation_memory import ConversationMemory

        # Now that all models are imported, create the tables
        Base.metadata.create_all(bind=engine)
        print("Successfully created all tables based on current SQLAlchemy models!")
    except Exception as e:
        print(f"Error creating tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    init_db()
