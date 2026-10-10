
from fastapi import FastAPI
import os
from app.core.config import settings

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.documents import router as documents_router
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.ingest import router as ingest_router
from app.langgraph.graph import graph




from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres import PostgresSaver

db_url = settings.DATABASE_URL.replace(
      "postgresql+psycopg://",
      "postgresql://"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    with PostgresSaver.from_conn_string(
        db_url
    ) as checkpointer:

        checkpointer.setup()

        app.state.rag_graph = graph.compile(
            checkpointer=checkpointer
        )

        yield

    
app = FastAPI(
    title="Enterprise AI Assistant",
    description="AI-powered Enterprise Knowledge and Operations Assistant",
    lifespan=lifespan
)

@app.get("/")
def root():
    return {
        "message":"Welcome to Enterprise AI Assistant"
    }

@app.get("/health")
def health_check():
    return {
        "status":"healthy"
    }

app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    documents_router,
    prefix="/api/v1/documents",
    tags=["Documents"]
)

app.include_router(
    ingest_router,
    prefix="/api/v1",
    tags=["Ingestion"]
)

app.include_router(
    admin_router,
    prefix="/api/v1",
    tags=["Admin"]
)



