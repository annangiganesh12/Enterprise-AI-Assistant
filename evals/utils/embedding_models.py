from typing import List
from deepeval.models import DeepEvalBaseEmbeddingModel
from sentence_transformers import SentenceTransformer

class LocalSentenceTransformerModel(DeepEvalBaseEmbeddingModel):
    """
    Custom Embedding Model using Sentence-Transformers to run locally
    and avoid OpenAI API costs.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        super().__init__(model_name)

    def embed_text(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts).tolist()

    async def a_embed_text(self, text: str) -> List[float]:
        return self.embed_text(text)

    async def a_embed_texts(self, texts: List[str]) -> List[List[float]]:
        return self.embed_texts(texts)

    def get_model_name(self) -> str:
        return f"{self.name} (Local)"

    def load_model(self, async_mode: bool = False):
        return self.model