from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from pathlib import Path

from app.authentication.dependencies import get_current_admin
from app.database.session import get_db
from app.models.user import User
from app.models.document import Documents
from app.models.dataset import Dataset

from app.services.storage_service import BaseStorageService
from app.services.document_service import (
    split_documents,
    create_embeddings,
    save_chunks_to_db,
    get_strategy_id,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    EMBEDDING_MODEL_NAME
)
from app.services.dataset_service import DatasetService
from app.utils.pdf_loader import extract_text_from_pdf

router = APIRouter()

# Configuration
BASE_DIR = Path(__file__).resolve().parents[4]
storage_service = BaseStorageService(BASE_DIR / "uploads")
dataset_service = DatasetService()

@router.post("/ingest")
async def ingest_file(
    file: UploadFile = File(...),
    is_global: bool = False,
    document_type: str | None = None,
    department: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):

    """
    Unified ingestion endpoint for PDFs and Tabular data.
    Saves the file, checks for duplicates and strategy match, and routes to the correct processing pipeline.
    """
    # SECURITY: Only admins can set is_global=True
    # Since we use get_current_admin, only admins can even reach this endpoint.

    # 1. Save file and get hash via BaseStorageService
    sub_dir = "documents"
    if "csv" in file.content_type or "spreadsheetml" in file.content_type or "excel" in file.content_type:
        sub_dir = "datasets"

    file_path, file_hash = await storage_service.save_file(file, sub_dir=sub_dir)

    # 2. Route based on content type
    if file.content_type == "application/pdf":
        # --- PDF PIPELINE ---
        current_strategy = get_strategy_id(DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP, EMBEDDING_MODEL_NAME)

        # Check for duplicates AND strategy match
        document = db.query(Documents).filter(
            Documents.file_hash == file_hash,
            Documents.current_strategy == current_strategy
        ).first()

        if document:
            # Link the admin to the existing document if not already linked
            if document not in current_admin.documents:
                current_admin.documents.append(document)
                db.commit()
            return {"document_id": document.id, "message": "Existing document reused with matching strategy."}

        # If document exists but strategy is different, we must clear old chunks
        if document is None:
            # Check if the file exists under a DIFFERENT strategy
            doc_any_strategy = db.query(Documents).filter(Documents.file_hash == file_hash).first()
            if doc_any_strategy:
                document = doc_any_strategy
                from app.models.document_chunk import DocumentChunk
                db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete()
                db.commit()
                document.current_strategy = current_strategy
        else:
            # Strategy mismatch case
            from app.models.document_chunk import DocumentChunk
            db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete()
            db.commit()
            document.current_strategy = current_strategy

        # If still no document, create a new record
        if not document:
            document = Documents(
                filename=file.filename,
                file_path=str(file_path),
                content_type=file.content_type,
                file_hash=file_hash,
                is_global=is_global,
                current_strategy=current_strategy
            )
            db.add(document)
            db.flush()
        else:
            # Update existing document to new strategy
            document.current_strategy = current_strategy
            db.add(document)
            db.flush()

        # Process PDF
        docs = extract_text_from_pdf(str(file_path))
        chunks = split_documents(docs)
        embeddings = create_embeddings(chunks)

        metadata = {
            "document_type": document_type,
            "department": department,
            "category": category,
            "is_global": is_global
        }
        save_chunks_to_db(chunks, embeddings, document.id, db, metadata=metadata)

        db.commit()
        return {"document_id": document.id, "message": "PDF uploaded and processed successfully with current strategy."}

    elif "csv" in file.content_type or "spreadsheetml" in file.content_type or "excel" in file.content_type:
        # --- DATASET PIPELINE ---
        try:
            dataset = dataset_service.process_and_import_dataset(
                db=db,
                file_path=file_path,
                filename=file.filename,
                content_type=file.content_type,
                uploaded_by=current_admin.id,
                file_hash=file_hash,
                is_global=is_global
            )

            return {"dataset_id": dataset.id, "table_name": dataset.table_name, "message": "Dataset imported successfully."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Dataset import failed: {str(e)}")

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Please upload PDF, CSV, or XLSX."
        )
