import json
from pathlib import Path
from deepeval.synthesizer import Synthesizer
from deepeval.synthesizer.config import ContextConstructionConfig
from evals.utils.embedding_models import LocalSentenceTransformerModel

DOCUMENTS = [
    r"D:\ENTERPRISE_AI_ASSISTANT\uploads\documents\java_book.pdf",
]

OUTPUT_FILE = Path("evals/datasets/e2e_goldens.json")

def main():
    # Initialize local embedder and synthesizer
    embedder = LocalSentenceTransformerModel()
    synthesizer = Synthesizer()

    # Configure the local embedder
    config = ContextConstructionConfig(embedder=embedder)

    # Generate goldens (E2E: Question -> Expected Answer)
    goldens = synthesizer.generate_goldens_from_docs(
        document_paths=DOCUMENTS,
        include_expected_output=True,
        max_goldens_per_context=2,
        context_construction_config=config
    )

    dataset = []
    for golden in goldens:
        dataset.append({
            "input": golden.input,
            "expected_output": golden.expected_output,
        })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(dataset)} E2E test cases.")
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()