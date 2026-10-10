import json
from pathlib import Path
from typing import List, Callable
from deepeval.metrics import ContextualRecallMetric, ContextualPrecisionMetric
from deepeval.test_case import LLMTestCase
from deepeval import evaluate

def run_retrieval_eval(retriever_fn: Callable[[str], List[str]]):
    """
    Evaluates the Retrieval component of the RAG pipeline.

    Args:
        retriever_fn: Function that takes a query (str) and returns retrieved chunks (List[str]).
    """
    dataset_path = Path("evals/datasets/retriever_goldens.json")
    if not dataset_path.exists():
        print(f"Error: Dataset not found at {dataset_path}")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        goldens = json.load(f)

    # --- RETRIEVAL METRICS ---
    # 1. Contextual Recall: Did we find the golden context?
    recall_metric = ContextualRecallMetric(threshold=0.7)
    # 2. Contextual Precision: Are the relevant chunks ranked highly?
    precision_metric = ContextualPrecisionMetric(threshold=0.7)

    test_cases = []
    for item in goldens:
        query = item["input"]
        golden_context = item["context"]

        # Call the actual application retriever logic
        actual_context = retriever_fn(query)

        test_case = LLMTestCase(
            input=query,
            actual_output="N/A", # Not used for retrieval
            expected_output="N/A", # Not used for retrieval
            retrieval_context=actual_context,
            gold_context=golden_context
        )
        test_cases.append(test_case)

    # Run evaluation for both Recall and Precision
    results = evaluate(
        test_cases=test_cases,
        metrics=[recall_metric, precision_metric]
    )

    # Save results to local report
    import json
    from pathlib import Path

    report_path = Path("evals/reports/retrieval_report.json")
    serializable_results = []
    for res in results:
        serializable_results.append({
            "test_case": str(res.test_case),
            "metrics": {m.name: m.score for m in res.metrics},
            "success": res.success
        })

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(serializable_results, f, indent=4)

    print(f"Retrieval report saved to {report_path}")

if __name__ == "__main__":
    from app.services.retrieval_service_bridge import run_retrieval

    print("Retrieval Evaluation Script")
    print("---------------------------")
    print("Running retrieval evaluation using run_retrieval...")
    run_retrieval_eval(run_retrieval)
