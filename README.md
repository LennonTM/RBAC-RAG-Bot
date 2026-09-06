# DS RPC-01: Internal Chatbot with Role-Based Access Control

An internal chatbot starter project: a FastAPI backend with HTTP Basic auth and per-user roles, a Streamlit chat UI, and an LLM accessed through OpenCode Go. Originally based on Codebasics's [Resume Project Challenge](https://codebasics.io/challenge/codebasics-gen-ai-data-science-resume-project-challenge) for building a RAG-based internal chatbot with role-based access control — see the challenge page for the original brief and `resources/RPC_01_Thumbnail.jpg`.

### Roles Provided

- **engineering**
- **finance**
- **general**
- **hr**
- **marketing**

Role-scoped source documents for each department live under `resources/data/` (e.g. `resources/data/finance/quarterly_financial_report.md`). These aren't wired into the chat flow yet — see [Current State](#current-state-and-whats-not-built-yet) below.

## Architecture

```
Streamlit UI (streamlit_app.py, :8501)
        │  HTTP Basic auth + /chat requests
        ▼
FastAPI backend (app/main.py, :8000)
        │  role-aware system prompt
        ▼
OpenCode Go API (glm-5.3-flash by default)
```

- **`app/main.py`** — the FastAPI app. HTTP Basic auth against an in-memory `users_db`, with roles resolved through `app/rbac.py`. The `/chat` endpoint passes the authenticated user's authorized resource scopes into the backend retrieval flow.
- **`app/rbac.py`** — the centralized role-to-permission policy. Resource access is deny-by-default and enforced during vector-store retrieval, before chunks are sent to the model.
- **`streamlit_app.py`** — a thin client: a login form that authenticates against `/login`, then a `st.chat_input`/`st.chat_message` loop that posts to `/chat` using the same Basic-auth credentials on every turn.
- **OpenCode Go** — hosted model access through the OpenAI-compatible OpenCode Go API. The app reads the API key from `OPENCODE_API_KEY`.

## Running the project

Requires Python 3.10+.

1. Create and activate a virtual environment (from this directory):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```powershell
    pip install "fastapi[standard]>=0.115.12" streamlit requests
   ```
   (`pip install -e .` will fail — `pyproject.toml`'s flat layout has two top-level dirs, `app/` and `resources/`, which trips setuptools' package auto-discovery. Installing the dependencies directly avoids this.)
3. Add your OpenCode Go API key to `app/.env`:
    ```powershell
   OPENCODE_API_KEY=your-opencode-go-api-key
    ```
    The backend uses `glm-5.3-flash` by default. Change `OPENCODE_MODEL` in `app/main.py` to use another chat-completions model available through Go.
4. Start the backend:
   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
5. Try it out at http://127.0.0.1:8000/docs, or with curl:
   ```powershell
   curl.exe -s -X POST -u Tony:password123 "http://127.0.0.1:8000/chat?message=hello"
   ```
   (`curl` in PowerShell is aliased to `Invoke-WebRequest`, which doesn't understand curl's flags — use `curl.exe` explicitly, or `Invoke-RestMethod` with a Basic auth header instead.)
6. In a second terminal (with the backend still running), start the chat UI:
   ```powershell
   .\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
   ```
   This opens `http://localhost:8501` in your browser, where you can log in with any of the dummy users below and chat through `/chat`.

Dummy users (see `app/main.py`): `Tony`/`password123` (engineering), `Bruce`/`securepass` (marketing), `Sam`/`financepass` (finance), `Peter`/`pete123` (engineering), `Sid`/`sidpass123` (marketing).

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/login` | Basic | Validates credentials, returns `{"message": ..., "role": ...}` |
| `GET` | `/test` | Basic | Simple authenticated smoke-test endpoint |
| `POST` | `/chat?message=...` | Basic | Sends `message` to OpenCode Go and returns `{"hello": <reply>}` |

## Current state (and what's not built yet)

This is a starting point, not a finished RAG pipeline:

- **Retrieval is role-scoped.** Documents are tagged with their directory scope and both the relevance check and retrieval tool apply the authenticated user's allowed scopes before the model sees any chunks.
- **`app/schemas/`, `app/services/`, `app/utils/`** are empty scaffolding (`__init__.py` only) — intended homes for request/response models, retrieval logic, and helpers respectively, once retrieval is implemented.
- **`users_db` is in-memory and hardcoded** in `app/main.py` — fine for local dev, not meant for production use.
- **Model:** `glm-5.3-flash` via OpenCode Go, hardcoded as `OPENCODE_MODEL` in `app/main.py`. Swap the string to try another chat-completions model available through Go.

## LangSmith tracing and release evaluations

Configure these Azure application settings. LangChain automatically traces the agent, retrieval tool, subagent calls, and model calls:

```text
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_PROJECT=rag-production
```

Create the regression dataset once, then run evaluations in CI before deployment:

```powershell
python scripts/create_langsmith_dataset.py
$env:LANGSMITH_MIN_SCORE="1.0"
python scripts/run_langsmith_eval.py
```

The evaluation exits non-zero when a role-access, out-of-scope, or keyword regression fails. Configure LangSmith credentials as CI secrets, not in the repository. Use `LANGSMITH_PROJECT=rag-evaluations` for CI runs.

### Azure deployment gate

`.github/workflows/deploy-azure.yml` runs the LangSmith regression evaluation before it logs in to Docker Hub, builds or pushes images, or changes Azure. A failed or under-threshold evaluation therefore blocks the deployment and leaves the existing Azure version running. Successful runs keep publishing both images to Docker Hub, tagged with the immutable Git SHA and `latest`, then deploy the SHA tags to Azure Web App for Containers.

Configure these GitHub Actions secrets in the repository or the `production` environment:

- `LANGSMITH_API_KEY`
- `OPENCODE_API_KEY`
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN` (a Docker Hub access token)
- `AZURE_CREDENTIALS` (the JSON output of `az ad sp create-for-rbac --sdk-auth`)

Configure these GitHub Actions secrets in the repository or `production` environment:

- `AZURE_RESOURCE_GROUP`
- `AZURE_BACKEND_APP_NAME`
- `AZURE_FRONTEND_APP_NAME`

Optional secrets are `LANGSMITH_DATASET` (default `rag-regression`), `LANGSMITH_MIN_SCORE` (default `1.0`), `OPENCODE_MODEL` (default `glm-5.3-flash`), `AZURE_LOCATION` (default `swedencentral`), and `AZURE_APP_SERVICE_PLAN` (default `rag-linux-plan`). Set `AZURE_LOCATION` to an App Service region allowed by your Azure subscription; it may differ from the existing resource group's region. `LANGSMITH_WORKSPACE_ID` should identify the workspace that owns the dataset. The deployment workflow creates the resource group, Linux App Service plan, and both Web Apps when they do not already exist, then configures the custom containers and runtime settings.
