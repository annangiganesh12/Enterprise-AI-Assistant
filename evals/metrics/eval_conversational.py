from typing import List, Tuple, Callable
from deepeval.simulator import ConversationSimulator
from deepeval.dataset import ConversationalGolden
from deepeval.metrics import ConversationCompletenessMetric, TurnRelevancyMetric
from deepeval import evaluate

def run_conversational_eval(chat_fn: Callable[[List[Tuple[str, str]], str], str]):
    """
    Evaluates conversational AI using the DeepEval Conversation Simulator.
    """

    # 1. Define the Simulator
    # Based on deepeval 4.2.8 help: model_callback is the target chat function
    simulator = ConversationSimulator(
        model_callback=chat_fn
    )

    # 2. Define the scenarios as ConversationalGolden objects
    goldens = [
        ConversationalGolden(
            scenario="Ask about the installation process of Java and then ask about the system requirements."
        ),
        ConversationalGolden(
            scenario="Try to find out the return policy but be slightly skeptical about the terms."
        ),
        ConversationalGolden(
            scenario="Inquire about the latest version of Java and ask if it's compatible with Windows 11."
        )
    ]

    # 3. Run the simulation to generate dynamic transcripts
    # .simulate() returns a list of ConversationalTestCase
    test_cases = simulator.simulate(conversational_goldens=goldens)

    # 4. Define Conversational Metrics
    completeness_metric = ConversationCompletenessMetric(threshold=0.7)
    relevancy_metric = TurnRelevancyMetric(threshold=0.7)

    # 5. Run the evaluation
    results = evaluate(
        test_cases=test_cases,
        metrics=[completeness_metric, relevancy_metric]
    )

    # Save results to local report
    import json
    from pathlib import Path

    report_path = Path("evals/reports/conversational_report.json")
    # Note: evaluate() returns a list of TestResult objects;
    # we convert them to a serializable format
    serializable_results = []
    for res in results:
        serializable_results.append({
            "test_case": str(res.test_case),
            "metrics": {m.name: m.score for m in res.metrics},
            "success": res.success
        })

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(serializable_results, f, indent=4)

    print(f"Conversational report saved to {report_path}")

if __name__ == "__main__":
    from app.services.chat_service import run_chat_session

    print("Conversational AI Evaluation (Simulation Mode)")
    print("---------------------------------------------")
    run_conversational_eval(run_chat_session)
