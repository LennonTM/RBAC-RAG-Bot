from typing import Dict

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

import ollama

OLLAMA_MODEL = "llama3.2"


app = FastAPI()
security = HTTPBasic()

# Dummy user database
users_db: Dict[str, Dict[str, str]] = {
    "Lennon": {"password": "123", "role": "engineering"},
    "Tony": {"password": "password123", "role": "engineering"},
    "Bruce": {"password": "securepass", "role": "marketing"},
    "Sam": {"password": "financepass", "role": "finance"},
    "Peter": {"password": "pete123", "role": "engineering"},
    "Sid": {"password": "sidpass123", "role": "marketing"},
    "Natasha": {"passwoed": "hrpass123", "role": "hr"}
}


# Authentication dependency
def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    password = credentials.password
    user = users_db.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"username": username, "role": user["role"]}


# Login endpoint
@app.get("/login")
def login(user=Depends(authenticate)):
    return {"message": f"Welcome {user['username']}!", "role": user["role"]}


# Protected test endpoint
@app.get("/test")
def test(user=Depends(authenticate)):
    return {"message": f"Hello {user['username']}! You can now chat.", "role": user["role"]}


# Protected chat endpoint
@app.post("/chat")
def query(user=Depends(authenticate), message: str = "Hello"):
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": f"You are an internal assistant. The user is {user['username']}, role: {user['role']}.",
                },
                {"role": "user", "content": message},
            ],
        )
    except ConnectionError:
        raise HTTPException(
            status_code=502,
            detail="Could not reach Ollama. Make sure `ollama serve` is running.",
        )
    except ollama.ResponseError as e:
        if e.status_code == 404:
            raise HTTPException(
                status_code=500,
                detail=f"Model '{OLLAMA_MODEL}' not found locally. Run `ollama pull {OLLAMA_MODEL}` first.",
            )
        raise HTTPException(status_code=502, detail=f"Ollama error: {e.error}")

    return {"hello": response["message"]["content"]}