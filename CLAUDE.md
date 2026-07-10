# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

There is no build step, linter, or test suite configured in this project.

**Setup** (from this directory):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install "fastapi[standard]>=0.115.12" streamlit requests ollama
ollama pull llama3.2
```
`pip install -e .` fails here — `pyproject.toml`'s flat layout has two top-level dirs (`app/`, `resources/`), which trips setuptools' package auto-discovery. Install dependencies directly instead.

**Run the backend** (FastAPI, port 8000):
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Run the chat UI** (Streamlit, port 8501, needs the backend running):
```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

**Manual smoke test** (PowerShell's `curl` is aliased to `Invoke-WebRequest`, so use `curl.exe` explicitly):
```powershell
curl.exe -s -X POST -u Tony:password123 "http://127.0.0.1:8000/chat?message=hello"
```

**Ollama must be running** with the `llama3.2` model pulled (`ollama pull llama3.2`) before `/chat` will work — `/chat` calls it directly, with no fallback. The first request after Ollama loads (or reloads) the model into memory is slow; subsequent requests are fast while it stays loaded.

## Architecture

Three independent processes, no shared code between them beyond the HTTP contract:

```
Streamlit UI (streamlit_app.py, :8501)
        │  HTTP Basic auth + /chat requests
        ▼
FastAPI backend (app/main.py, :8000)
        │  role-aware system prompt
        ▼
Ollama (localhost:11434) running llama3.2 locally
```

- **`app/main.py`** is the entire backend today: HTTP Basic auth (`authenticate` dependency) checked against an in-memory `users_db` dict (username → password + role), plus three routes (`/login`, `/test`, `/chat`). `/chat` calls `ollama.chat(...)` with the authenticated user's `username`/`role` folded into the system prompt, and maps Ollama failure modes to HTTP errors (connection refused → 502, model not pulled → 500, other Ollama errors → 502).
- **`streamlit_app.py`** is a thin client with no business logic: a login form that calls `/login`, then a chat loop that calls `/chat` with the same Basic-auth credentials on every turn. Session state (`st.session_state.auth`, `.messages`) is the only state it keeps.
- **`app/schemas/`, `app/services/`, `app/utils/`** are currently empty (`__init__.py` only) — placeholders for request/response models, retrieval logic, and helpers respectively, once retrieval is built out.
- **`resources/data/<role>/`** holds role-scoped source documents (engineering, finance, general, hr, marketing) that are **not yet wired into `/chat`** — there is no retrieval, embedding, or vector store in this codebase yet. `/chat` currently answers purely from the model's own knowledge plus the user's role label; it does not read these files. Building role-scoped RAG retrieval over this directory is the main unimplemented piece.
- The top-level `main.py` referenced in older commits/docs has been removed; the only backend entry point is `app/main.py`.

## Key constraints worth knowing before editing

- `users_db` in `app/main.py` is hardcoded and in-memory — restarting the server resets nothing (it's not persisted anywhere to begin with). One entry (`Natasha`) has a typo'd key `passwoed` instead of `password` — logging in as `Natasha` doesn't just fail auth, it raises an unhandled `KeyError` in `authenticate()` (there's no `.get()` guard), so FastAPI returns a raw `500` instead of a clean `401`. This may be intentional test data or a latent bug; check with the user before "fixing" it.
- The LLM model is hardcoded as `OLLAMA_MODEL = "llama3.2"` in `app/main.py`. Changing it requires also running `ollama pull <new-model>` locally.
- No API keys or `.env` file are needed for the current Ollama-based setup — `.env`/`.env.example` are still listed in `.gitignore` from an earlier Anthropic-API-based version of `/chat`, but nothing in the code reads them now.
