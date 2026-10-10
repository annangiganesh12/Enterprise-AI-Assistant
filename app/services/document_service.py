from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.utils.embeddings import generate_embeddings
from app.models.document_chunk import DocumentChunk
from app.models.document import Documents
import hashlib

# Global Strategy Constants - change these to trigger automatic re-processing
DEFAULT_CHUNK_SIZE = 1250
DEFAULT_CHUNK_OVERLAP = 300
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2" # Update this if you change embedding models

def get_strategy_id(chunk_size: int, chunk_overlap: int, model_name: str) -> str:
    
    return f"cs{chunk_size}_ol{chunk_overlap}_{model_name}"

def split_documents(documents, chunk_size=DEFAULT_CHUNK_SIZE, chunk_overlap=DEFAULT_CHUNK_OVERLAP):

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    chunks = text_splitter.split_documents(documents)

    return chunks

def create_embeddings(chunks):

    texts = [
        chunk.page_content
        for chunk in chunks
    ]

    embeddings = generate_embeddings(texts)

    return embeddings

def process_document(
    db,
    doc_id: int,
    content: str,
    file_hash: str,
    strategy_id: str = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
):

    if strategy_id is None:
        strategy_id = get_strategy_id(chunk_size, chunk_overlap, EMBEDDING_MODEL_NAME)

    # 1. Check if document already exists with this specific strategy
    existing_doc = db.query(Documents).filter(
        Documents.id == doc_id,
        Documents.file_hash == file_hash,
        Documents.current_strategy == strategy_id
    ).first()

    if existing_doc:
        return {"status": "skipped", "message": "Document already processed with this strategy."}

    # 2. Proceed with chunking (we simulate documents list for split_documents)
    from langchain_core.documents import Document
    docs = [Document(page_content=content)]

    chunks = split_documents(docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    embeddings = create_embeddings(chunks)

    # 3. Save chunks to DB
    save_chunks_to_db(chunks, embeddings, doc_id, db, strategy_id)

    # 4. Update the document's current strategy
    db.query(Documents).filter(Documents.id == doc_id).update({
        "current_strategy": strategy_id,
        "file_hash": file_hash
    })
    db.commit()

    return {"status": "processed", "message": "Document chunked and embedded successfully."}

def save_chunks_to_db(
        chunks,
        embeddings,
        doc_id,
        db,
        strategy_id : str = None,
        metadata: dict = None
):
    # If strategy_id is not provided, fetch it from the parent Document record to ensure consistency
    if strategy_id is None:
        from app.models.document import Documents
        doc = db.query(Documents).filter(Documents.id == doc_id).first()
        strategy_id = doc.current_strategy if doc else None

    for index, (chunk,embedding) in enumerate(zip(chunks,embeddings)):

        chunck_record = DocumentChunk(
            document_id = doc_id,
            chunk_index = index,
            content = chunk.page_content,
            page_number = chunk.metadata.get("page"),
            embedding = embedding,
            strategy_id = strategy_id,
            metadata_info = metadata
        )


        db.add(chunck_record)


    db.flush()
