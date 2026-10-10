
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, BackgroundTasks
from sqlalchemy.orm import Session

from sqlalchemy.orm import Session

import hashlib
from pathlib import Path
import shutil
from uuid import uuid4
from fastapi import Request

from app.utils.pdf_loader import extract_text_from_pdf
from app.services.document_service import (
    split_documents,
    create_embeddings,
    save_chunks_to_db
)
from app.services.retrival_service import vector_search,keyword_search,hybrid_search,retrieve_and_rank

from app.authentication.dependencies import get_current_user, get_current_admin
from app.database.session import get_db

from app.models.document import Documents
from app.models.user import User

from app.langgraph.context import RAGContext
from langchain_core.messages import HumanMessage
from app.services.memory_background_service import run_memory_updates


router = APIRouter()

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[4]

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):

     if file.content_type!="application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )

     # Read file
     file_content = await file.read()

     # calculate SHA-256
     file_hash = hashlib.sha256(file_content).hexdigest()

     # check whether document already exists
     document = db.query(Documents).filter(
         Documents.file_hash == file_hash
     ).first()

     # CASE 1: Document already exists

     if document:

         # check whether current user already has access
         if document not in current_user.documents:
             current_user.documents.append(document)
             db.commit()
             meassage = "Existing document reused and linked to user, existing embeddings has been used"
         else:
             meassage = "Document already exists for this user and existing embeddings has been used"

         return {
             "document_id": document.id,
             "filename": document.filename,
             "message": meassage
         }
     
     # CASE 2: New Document         
     # Generate unique filenames
     unique_filename = f"{uuid4()}_{file.filename}"

     #create complete path
     file_path = UPLOAD_DIR / unique_filename

     # Save uploaded file
     with file_path.open("wb") as buffer:
        buffer.write(file_content)

     # Create a document record   
     document = Documents(
        filename=file.filename,
        file_path=str(file_path),
        content_type=file.content_type,
        file_hash=file_hash
     )

     db.add(document)

     db.flush()

     current_user.documents.append(document)

     # Extract text from PDF
     documents = extract_text_from_pdf(str(file_path))

     # Split PDF into chunks
     chunks = split_documents(documents)

     # Generate embeddings
     embeddings = create_embeddings(chunks)

     # Save chunks + embeddings to PostgreSQL
     save_chunks_to_db(
         chunks,
         embeddings,
         document.id,
         db
     )

     # Commit Everything
     db.commit()

     return {
        "document_id": document.id,
        "filename": document.filename,
        "chunks_created": len(chunks),
        "message":"New document uploaded and processed successfully."
    }


@router.get("/search")
def search_documents(
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    results = vector_search(
        query=query,
        db=db,
        user_id=current_user.id,
        top_k=10
    )

    return {
        "query": query,
        "results":[
            {
                "chunk_id":chunk.id,
                "document_id":chunk.document_id,
                "chunk_index":chunk.chunk_index,
                "page_number":chunk.page_number,
                "content":chunk.content
            }
            for chunk in results
        ]
    }

@router.get("/keyword-search")
def keyword_search_documents(
    query:str,
    db:Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    results = keyword_search(
        query=query,
        db=db,
        user_id=current_user.id,
        top_k=10
    )

    return{
        "query":query,
        "results":[{
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
            "page_number": chunk.page_number,
            "content": chunk.content
        }
        for chunk in results
        ]
    }

@router.get("/hybrid-search")
def hybrid_search_documents(
    query:str,
    db:Session = Depends(get_db),
    current_user:User = Depends(get_current_user)
):

    results = hybrid_search(
        query=query,
        db=db,
        user_id=current_user.id,
        top_k=20,
        retrival_k=10        
    )

    return {
        "query":query,
        "results": [{
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
            "page_number": chunk.page_number,
            "content": chunk.content
        }
        for chunk in results
        ]
    }

@router.get("/reranking")
def retrieve_documents(
    query:str,
    db:Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    results = retrieve_and_rank(
        query=query,
        db=db,
        user_id=current_user.id,
        retrival_k=10,
        rerank_k=5
    )

    return{
        "query": query,
        "results": [
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "content": chunk.content
            }
            for chunk in results
        ]
    }


@router.get("/rag")
def rag_search(
    background_tasks: BackgroundTasks,
    request: Request,
    query: str,
    thread_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    rag_graph = request.app.state.rag_graph
    config = {
        "configurable":{
            "thread_id": thread_id
        }
    }
    result = rag_graph.invoke(
       {
        "query":query,
        "user_id":current_user.id,
        "retrieved_documents":[],
        "answer":"",
        "messages": [
            HumanMessage(content=query)
        ]
       },
       context=RAGContext(db=db),
       config=config
    )

    # Trigger memory updates in the background so the user gets an immediate response
    background_tasks.add_task(run_memory_updates, result, db)

    return{
      "query":result["query"],
      "answer":result["answer"]
    }

