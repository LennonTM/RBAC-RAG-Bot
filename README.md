# Role-Based RAG Chatbot

This project is a learning project focused on building a production-style Retrieval-Augmented Generation (RAG) application. It was inspired by the [Codebasics Gen AI Data Science Resume Project Challenge](https://codebasics.io/challenge/codebasics-gen-ai-data-science-resume-project-challenge).

The project is used to learn and practice:

- Retrieval-Augmented Generation (RAG)
- Role-Based Access Control (RBAC)
- LangChain application design
- Vector databases and semantic search
- Hugging Face embedding models
- LangSmith tracing and evaluation
- Containerization and cloud deployment with Azure

## What This Project Does

The application is an internal company chatbot. Users log in with a username and password, and each user is assigned a role such as engineering, finance, HR, marketing, or system administrator.

When a user asks a question:

1. The FastAPI backend authenticates the user.
2. RBAC determines which document scopes the user is allowed to access.
3. The question is converted into an embedding with a Hugging Face model.
4. A vector database retrieves the most relevant permitted document chunks.
5. LangChain sends the retrieved context to the language model.
6. The chatbot answers using only the information available to that user's role.

The role filter is applied during retrieval, before document content is provided to the language model. For example, a finance user can retrieve finance and general documents but cannot retrieve engineering, HR, or marketing documents.

Source documents are stored under `resources/data/` and are split, embedded, and indexed in a persistent local Chroma database by default.

## Project Status

The local RAG application is the primary working setup. Azure deployment and LangSmith integration have been implemented as learning and deployment paths, but they are currently disabled and are not required to run the project locally.

The code also includes an optional Azure AI Search vector-store backend. The default local backend is Chroma:

```text
VECTOR_STORE_BACKEND=chroma
```

LangSmith tracing, regression evaluation, Docker Hub publishing, and Azure deployment can be re-enabled when cloud credentials and resources are available.

## Architecture

```text
Chrome or another web browser
              |
              v
Streamlit chat UI (:8501)
              |
              | HTTP Basic authentication and /chat requests
              v
FastAPI backend (:8000)
              |
              +--> RBAC policy
              |
              +--> LangChain retrieval pipeline
              |       |
              |       +--> Hugging Face embeddings
              |       +--> Chroma vector database
              |
              +--> Language model through the configured OpenAI-compatible API
```

## Run Locally

The local setup uses Chrome or another browser, Hugging Face embeddings, Chroma, Streamlit, FastAPI, and Uvicorn. Python 3.10 or newer is required.

### 1. Create a virtual environment

Run these commands from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

Install the backend and frontend dependencies directly:

```powershell
pip install -r requirements-backend.txt
pip install -r requirements-frontend.txt
```

The first backend start may download the Hugging Face embedding model:
`sentence-transformers/all-MiniLM-L6-v2`.

### 3. Configure the language model

The application uses an OpenAI-compatible language-model endpoint configured through environment variables. Set an API key before starting the backend:

```powershell
$env:OPENCODE_API_KEY="your-api-key"
$env:OPENCODE_MODEL="glm-5.3-flash"
```

The backend uses the OpenCode Go endpoint by default. If you use another OpenAI-compatible provider, update the provider configuration in `app/agent.py`.

### 4. Start the FastAPI backend

Open a terminal in the repository root and run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The API and interactive documentation are available at:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`

On startup, the application loads the files in `resources/data/`, creates embeddings, and creates or reuses the persistent `chroma_huggingface_db/` directory.

### 5. Start the Streamlit frontend

Open a second terminal, activate the same virtual environment, and run:

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Open `http://localhost:8501` in Chrome. Log in with one of the example users:

| Username | Password | Role |
|---|---|---|
| `Tony` | `password123` | Engineering |
| `Bruce` | `securepass` | Marketing |
| `Sam` | `financepass` | Finance |
| `Peter` | `pete123` | Engineering |
| `Sid` | `sidpass123` | Marketing |
| `Natasha` | `hrpass123` | HR |
| `admin` | `admin` | System administrator |

The frontend calls the backend at `http://127.0.0.1:8000` by default. To use another backend URL, set `API_URL` before starting Streamlit:

```powershell
$env:API_URL="http://127.0.0.1:8000"
```

### Optional API smoke test

PowerShell's `curl` command is an alias for `Invoke-WebRequest`, so use `curl.exe`:

```powershell
curl.exe -s -X POST -u Tony:password123 "http://127.0.0.1:8000/chat?message=What is the engineering documentation about?"
```

## Technology Stack

### Application

- **Python** for the application code
- **FastAPI** for the backend API
- **Uvicorn** as the local ASGI server
- **Streamlit** for the browser-based chat interface
- **HTTP Basic authentication** for the example login flow

### RAG and access control

- **LangChain** for document loading, splitting, retrieval, and model orchestration
- **Hugging Face Sentence Transformers** for local text embeddings
- **Chroma** as the default persistent local vector database
- **Azure AI Search** as the optional cloud vector database backend
- **RBAC** for role and document-scope authorization
- **OpenAI-compatible language-model API** for response generation

### Observability and deployment

- **LangSmith** for tracing and RAG regression evaluation; currently disabled
- **Docker** for packaging the backend and frontend
- **Docker Hub** for storing container images
- **Azure Web Apps for Containers** for the planned cloud deployment
- **GitHub Actions** for the evaluation, image publishing, and deployment workflow

## Repository Structure

```text
app/
  agent.py          RAG pipeline, embeddings, vector search, and model calls
  main.py           FastAPI application and authenticated endpoints
  rbac.py           Role and resource-scope policies
resources/data/     Role-scoped source documents
scripts/            Azure Search indexing and LangSmith evaluation scripts
streamlit_app.py    Streamlit frontend
Dockerfile.backend  Backend container image
Dockerfile.frontend Frontend container image
docker-compose.yml  Local container orchestration
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/login` | Validates Basic authentication and returns the user's role |
| `GET` | `/test` | Authenticated backend smoke test |
| `POST` | `/chat?message=...` | Retrieves authorized context and generates an answer |

## Cloud Integrations

The repository contains the configuration and scripts for a future cloud deployment:

- Set `VECTOR_STORE_BACKEND=azure` to use Azure AI Search, along with `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_INDEX_NAME`, and `AZURE_SEARCH_API_KEY`.
- Use `scripts/index_azure_search.py` to create the Azure AI Search index from the source documents.
- Configure LangSmith environment variables to enable tracing and evaluation.
- The GitHub Actions workflow can build images, publish them to Docker Hub, and deploy them to Azure Web Apps for Containers.

These integrations are currently disabled. Local development with Chroma does not require an Azure subscription, Docker Hub account, or LangSmith account.
