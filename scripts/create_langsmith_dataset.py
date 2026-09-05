"""Create the versioned regression dataset in LangSmith."""

import json
import os
from pathlib import Path

from langsmith import Client
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"), override=True)

DATASET_NAME = os.getenv("LANGSMITH_DATASET", "rag-regression")
DATASET_FILE = Path(__file__).with_name("langsmith_dataset.json")


def main() -> None:
    client = Client()
    if list(client.list_datasets(dataset_name=DATASET_NAME)):
        raise SystemExit(f"Dataset already exists: {DATASET_NAME}")
    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="Role-scoped RAG regression tests for the FinSolve assistant.",
    )
    records = json.loads(DATASET_FILE.read_text(encoding="utf-8"))
    client.create_examples(
        inputs=[record["inputs"] for record in records],
        outputs=[record["outputs"] for record in records],
        dataset_id=dataset.id,
    )
    print(f"Created {DATASET_NAME} with {len(records)} examples.")


if __name__ == "__main__":
    main()
