"""Run the production RAG function against a LangSmith dataset."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client
from langsmith.evaluation import evaluate

# Allow this file to be run directly from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv(Path(__file__).with_name(".env"), override=True)

from app.agent import answer
from app.rbac import user_for

DATASET_NAME = os.getenv("LANGSMITH_DATASET", "rag-regression")


def target(inputs: dict) -> dict:
    user = user_for("langsmith-evaluator", inputs["role"])
    return {"answer": answer(inputs["question"], user.username, user.role, user.resource_scopes)}


def keyword_evaluator(run, example) -> dict:
    answer_text = run.outputs.get("answer", "").lower()
    expected = example.outputs.get("expected_keywords", [])
    forbidden = example.outputs.get("forbidden_keywords", [])
    missing = [word for word in expected if word.lower() not in answer_text]
    present_forbidden = [word for word in forbidden if word.lower() in answer_text]
    passed = not missing and not present_forbidden
    return {"key": "regression_keywords", "score": int(passed), "comment": f"missing={missing}; forbidden={present_forbidden}"}


def evaluation_value(value, name: str):
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


def main() -> None:
    if not (os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")):
        raise SystemExit("LANGSMITH_API_KEY is required")
    results = evaluate(
        target,
        data=DATASET_NAME,
        evaluators=[keyword_evaluator],
        experiment_prefix=os.getenv("LANGSMITH_EXPERIMENT", "rag-regression"),
        metadata={"git_commit": os.getenv("GITHUB_SHA", "local")},
        client=Client(
            api_key=os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY"),
            api_url=os.getenv("LANGSMITH_ENDPOINT"),
            workspace_id=os.getenv("LANGSMITH_WORKSPACE_ID"),
        ),
    )
    rows = list(results)
    scores = []
    for row in rows:
        evaluation_results = evaluation_value(row, "evaluation_results") or {}
        evaluations = evaluation_value(evaluation_results, "results") or []
        for evaluation in evaluations:
            if evaluation_value(evaluation, "key") != "regression_keywords":
                continue
            score = evaluation_value(evaluation, "score")
            if score is not None:
                scores.append(score)
    score = sum(scores) / len(scores) if scores else 0
    print(f"regression_keywords={score:.3f}")
    if score < float(os.getenv("LANGSMITH_MIN_SCORE", "1.0")):
        raise SystemExit("LangSmith evaluation score is below the release threshold")


if __name__ == "__main__":
    main()
