
from sqlalchemy.orm import Session

from sqlalchemy import func, or_

from app.models.user_document import user_documents
from app.models.document import Documents
from app.models.document_chunk import DocumentChunk
from app.utils.embeddings import generate_embeddings
from app.utils.reranker import rerank_documents

def vector_search(
        query: str,
        db: Session,
        user_id: int,
        top_k: int = 10,
        strategy_id: str = None,
        filters: dict = None
):

    # Generate embedding for the user"s query
    query_embedding = generate_embeddings([query])[0]

    # Search chunks belonging to documents of particular user OR global documents
    results = (
        db.query(DocumentChunk).join(
            Documents,
            DocumentChunk.document_id == Documents.id
        ).outerjoin(
            user_documents,
            user_documents.c.document_id == Documents.id
        ).filter(
            or_(
                user_documents.c.user_id == user_id,
                Documents.is_global == True
            )
        )
    )

    if strategy_id:
        results = results.filter(DocumentChunk.strategy_id == strategy_id)

    if filters:
        for key, value in filters.items():
            results = results.filter(DocumentChunk.metadata[key].astext == str(value))

    results = results.order_by(
        DocumentChunk.embedding.cosine_distance(
            query_embedding
        )
    ).limit(top_k).all()



    return results

def keyword_search(
        query: str,
        db: Session,
        user_id: int,
        top_k: int = 10,
        strategy_id: str = None,
        filters: dict = None
):

    results = (
        db.query(DocumentChunk)
        .join(
            Documents,
            DocumentChunk.document_id == Documents.id
        )
        .outerjoin(
            user_documents,
            user_documents.c.document_id == Documents.id
        )
        .filter(
            or_(
                user_documents.c.user_id == user_id,
                Documents.is_global == True
            )
        )
    )

    if strategy_id:
        results = results.filter(DocumentChunk.strategy_id == strategy_id)

    if filters:
        for key, value in filters.items():
            results = results.filter(DocumentChunk.metadata[key].astext == str(value))

    results = results.filter(
        func.to_tsvector(
            "english",
            DocumentChunk.content
        ).op("@@")(
            func.plainto_tsquery(
                "english",
                query
            )
        )
    ).order_by(
        func.ts_rank(
            func.to_tsvector(
                "english",
                DocumentChunk.content
            ),
            func.plainto_tsquery(
                "english",
                query
            )
        ).desc()
    ).limit(top_k).all()


    return results

def hybrid_search(
        query:str,
        db:Session,
        user_id:int,
        top_k:int = 20,
        retrival_k: int = 10,
        strategy_id: str = None,
        filters: dict = None
):

    vector_results = vector_search(
        query=query,
        db=db,
        user_id=user_id,
        top_k=retrival_k,
        strategy_id=strategy_id,
        filters=filters
    )

    keyword_results = keyword_search(
        query=query,
        db=db,
        user_id=user_id,
        top_k=retrival_k,
        strategy_id=strategy_id,
        filters=filters
    )


    rrf_scores = {}

    # Vector ranking

    for rank,chunk in enumerate(vector_results,start=1):

        chunk_id = chunk.id

        rrf_scores[chunk_id] = (
            rrf_scores.get(chunk_id,0) + 1/(60 + rank)
        )

    # Keyword ranking

    for rank,chunk in enumerate(keyword_results,start=1):

        chunk_id = chunk.id

        rrf_scores[chunk_id] = (
            rrf_scores.get(chunk_id,0) + 1/(60 + rank)
        )

    # Store actual chunks
    chunks_by_id = {}

    for chunk in vector_results:
        chunks_by_id[chunk.id] = chunk
    for chunk in keyword_results:
        chunks_by_id[chunk.id] = chunk

    # sort by RRF score
    ranked_chunk_ids = sorted(
        rrf_scores,
        key=rrf_scores.get,
        reverse=True
    )

    # Return up to 20 unique candidates
    hybrid_results = [
        chunks_by_id[chunk_id]
        for chunk_id in ranked_chunk_ids[:top_k]
    ]

    return hybrid_results


def retrieve_and_rank(
        query:str,
        db:Session,
        user_id:int,
        retrival_k:int = 10,
        rerank_k:int = 5,
        strategy_id: str = None,
        filters: dict = None
):

    hybrid_results = hybrid_search(
        query=query,
        db=db,
        user_id=user_id,
        top_k=20,
        retrival_k=retrival_k,
        strategy_id=strategy_id,
        filters=filters
    )


    reranked_results = rerank_documents(
        query=query,
        documents=hybrid_results,
        top_k=rerank_k
    )

    return reranked_results
