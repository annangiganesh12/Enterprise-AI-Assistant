

from sentence_transformers import CrossEncoder

reranker_model = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

def rerank_documents(query,documents,top_k=5):
    pairs = [
        (query,document.content)
        for document in documents
    ]

    scores = reranker_model.predict(pairs)

    ranked_documents = sorted(
        zip(documents,scores),
        key=lambda x: x[1],
        reverse=True
    )

    return [
        document
        for document,score in ranked_documents[:top_k]
    ]
