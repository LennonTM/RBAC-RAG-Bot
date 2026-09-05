"""Create or replace the Azure AI Search index from the local documents."""

import hashlib
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchableField,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(Path(__file__).with_name(".env"), override=True)

DOC_PATHS = [
    "resources/data/engineering/engineering_master_doc.md",
    "resources/data/finance/financial_summary.md",
    "resources/data/finance/quarterly_financial_report.md",
    "resources/data/general/employee_handbook.md",
    "resources/data/hr/hr_data.csv",
    "resources/data/marketing/market_report_q4_2024.md",
    "resources/data/marketing/marketing_report_2024.md",
    "resources/data/marketing/marketing_report_q1_2024.md",
    "resources/data/marketing/marketing_report_q2_2024.md",
    "resources/data/marketing/marketing_report_q3_2024.md",
]


def load_documents():
    documents = []
    from langchain_core.documents import Document

    for relative_path in DOC_PATHS:
        path = ROOT / relative_path
        text = path.read_text(encoding="utf-8")
        metadata = {
            "source": str(path),
            "resource_scope": Path(relative_path).parts[2],
        }
        if path.suffix.lower() == ".csv":
            header, *rows = text.splitlines()
            documents.extend(
                Document(page_content=f"{header}\n{row}", metadata=metadata)
                for row in rows
                if row.strip()
            )
        else:
            documents.append(Document(page_content=text, metadata=metadata))
    return RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200
    ).split_documents(documents)


def main():
    endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
    index_name = os.environ["AZURE_SEARCH_INDEX_NAME"]
    api_key = os.environ["AZURE_SEARCH_API_KEY"]
    embeddings = HuggingFaceEmbeddings(
        model_name=os.getenv(
            "HUGGINGFACE_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
    )
    documents = load_documents()
    vectors = embeddings.embed_documents([doc.page_content for doc in documents])
    dimensions = len(vectors[0])
    credential = AzureKeyCredential(api_key)

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
        SimpleField(
            name="resource_scope",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=dimensions,
            vector_search_profile_name="default",
        ),
    ]
    index = SearchIndex(
        name=index_name,
        fields=fields,
        vector_search=VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
            profiles=[
                VectorSearchProfile(
                    name="default", algorithm_configuration_name="hnsw"
                )
            ],
        ),
    )
    SearchIndexClient(endpoint, credential).create_or_update_index(index)

    actions = []
    for document, vector in zip(documents, vectors):
        identity = f"{document.metadata['source']}\n{document.page_content}"
        actions.append(
            {
                "id": hashlib.sha256(identity.encode("utf-8")).hexdigest(),
                "content": document.page_content,
                "source": document.metadata["source"],
                "resource_scope": document.metadata["resource_scope"],
                "content_vector": vector,
            }
        )

    SearchClient(endpoint, index_name, credential).upload_documents(actions)
    print(f"Indexed {len(actions)} chunks into {index_name}.")


if __name__ == "__main__":
    main()
