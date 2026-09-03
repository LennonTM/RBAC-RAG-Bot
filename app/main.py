import os
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv
import requests

load_dotenv(Path(__file__).with_name(".env"))

OPENCODE_API_URL = "https://opencode.ai/zen/go/v1/chat/completions"
OPENCODE_MODEL = "glm-5.3-flash"


app = FastAPI()
security = HTTPBasic()

# Dummy user database
users_db: Dict[str, Dict[str, str]] = {
    "123": {"password": "123", "role": "engineering"},
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
    api_key = os.getenv("OPENCODE_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENCODE_API_KEY is not configured.",
        )

    try:
        response = requests.post(
            OPENCODE_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "x-opencode-session": f"rag-{user['username']}",
            },
            json={
                "model": OPENCODE_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are an internal assistant. The user is {user['username']}, role: {user['role']}.",
                    },
                    {"role": "user", "content": message},
                ],
            },
            timeout=120,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"OpenCode API request failed: {e}",
        )
    except (KeyError, IndexError, TypeError, ValueError):
        raise HTTPException(
            status_code=502,
            detail="OpenCode API returned an unexpected response.",
        )

    return {"hello": content}
