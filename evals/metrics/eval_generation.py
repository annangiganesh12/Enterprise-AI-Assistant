import json
from pathlib import Path
from typing import List, Callable
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric, AnswerCorrectnessMetric
from deepeval.test_case import LLMTestCase
from deepeval import evaluate

def run_generation_eval(generator_fn: Callable[[str, List[str]], str]):
    """
    Evaluates the Generator component of the RAG pipeline.

    Args:
        generator_fn: Function that takes (query, context_list) and returns a generated answer (str).
    """
    dataset_path = Path("evals/datasets/rag_goldens.json")
    if not dataset_path.exists():
        print(f"Error: Dataset not found at {dataset_path}")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        goldens = json.load(f)

    # --- GENERATION METRICS ---

    # 1. Faithfulness: Is the answer derived strictly from the provided context? (Anti-Hallucination)
    faithfulness_metric = FaithfulnessMetric(threshold=0.7)

    # 2. Answer Relevancy: Does the answer actually address the user's query?
    relevancy_metric = AnswerRelevancyMetric(threshold=0.7)

    # 3. Answer Correctness: Does the answer match the ground truth (Golden Answer)?
    correctness_metric = AnswerCorrectnessMetric(threshold=0.7)

    test_cases = []
    for item in goldens:
        query = item["input"]
        golden_answer = item["expected_output"]
        golden_context = item["context"]

        # Call the actual application generator logic.
        # We provide the GOLDEN context here to isolate the Generator's performance.
        # This ensures we are testing if the LLM can answer correctly GIVEN the right data.
        actual_answer = generator_fn(query, golden_context)

        test_case = LLMTestCase(
            input=query,
            actual_output=actual_answer,
            expected_output=golden_answer,
            retrieval_context=golden_context
        )
        test_cases.append(test_case)

    # Run evaluation for all three dimensions of generation quality
    evaluate(
        test_cases=test_cases,
        metrics=[faithfulness_metric, relevancy_metric, correctness_metric]
    )

if __name__ == "__main__":
    print("Generator Evaluation Script")
    print("---------------------------")
    print("To run this, import your generator function and call run_generation_eval(your_fn)")
    # Example usage:
    # from app.services.generator import generate_answer
    # run_generation_eval(generate_answer)
