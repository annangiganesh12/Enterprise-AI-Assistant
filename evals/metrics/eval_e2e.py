import json
from pathlib import Path
from typing import List, Tuple, Callable
from deepeval.metrics import AnswerCorrectnessMetric, AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase
from deepeval import evaluate

def run_e2e_eval(pipeline_fn: Callable[[str], str]):
    """
    Evaluates the full End-to-End RAG pipeline as a black box.

    Args:
        pipeline_fn: Function that takes a query (str) and returns
                     the final generated answer (str).
    """
    dataset_path = Path("evals/datasets/e2e_goldens.json")
    if not dataset_path.exists():
        print(f"Error: Dataset not found at {dataset_path}")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        goldens = json.load(f)

    # E2E focus: Is the final answer correct and relevant?
    # No retrieval_context or expected_context used here.
    metrics = [
        AnswerCorrectnessMetric(threshold=0.7),
        AnswerRelevancyMetric(threshold=0.7)
    ]

    test_cases = []
    for item in goldens:
        query = item["input"]
        expected_output = item["expected_output"]

        # Execute the full pipeline
        actual_output = pipeline_fn(query)

        test_case = LLMTestCase(
            input=query,
            actual_output=actual_output,
            expected_output=expected_output
            # retrieval_context is omitted for pure E2E
        )
        test_cases.append(test_case)

    # 5. Run the evaluation
    results = evaluate(
        test_cases=test_cases,
        metrics=metrics
    )

    # Save results to local report
    import json
    from pathlib import Path

    report_path = Path("evals/reports/e2e_report.json")
    serializable_results = []
    for res in results:
        serializable_results.append({
            "test_case": str(res.test_case),
            "metrics": {m.name: m.score for m in res.metrics},
            "success": res.success
        })

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(serializable_results, f, indent=4)

    print(f"E2E report saved to {report_path}")

if __name__ == "__main__":
    from app.services.chat_service import run_single_query

    print("End-to-End Evaluation Script")
    print("---------------------------")
    print("Running E2E evaluation using run_single_query...")
    run_e2e_eval(run_single_query)
