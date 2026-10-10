import json
from pathlib import Path
from typing import List

from deepeval.synthesizer import Synthesizer
from deepeval.models import DeepEvalBaseEmbeddingModel
from sentence_transformers import SentenceTransformer

class LocalSentenceTransformerModel(DeepEvalBaseEmbeddingModel):
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


DOCUMENTS = [
    r"D:\ENTERPRISE_AI_ASSISTANT\uploads\documents\java_book.pdf",
]


OUTPUT_FILE = Path(
    "evals/datasets/retriever_goldens.json"
)


def main():

    embedder = LocalSentenceTransformerModel()
    synthesizer = Synthesizer()

    # Overriding the internal context_construction_config to use our custom embedder
    from deepeval.synthesizer.config import ContextConstructionConfig
    config = ContextConstructionConfig(embedder=embedder)

    goldens = synthesizer.generate_goldens_from_docs(
        document_paths=DOCUMENTS,
        include_expected_output=False,
        max_goldens_per_context=2,
        context_construction_config=config
    )

    dataset = []

    for golden in goldens:

        dataset.append({
            "input": golden.input,
            "context": golden.context,
        })

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            dataset,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"Generated {len(dataset)} retriever test cases."
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()