import secrets
from typing import Dict

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from .agent import AgentError, answer
from .rbac import user_for


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
    "Natasha": {"password": "hrpass123", "role": "hr"},
    "admin": {"password": "admin", "role": "system_admin"},
}


# Authentication dependency
def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    password = credentials.password
    user = users_db.get(username)
    if not user or not secrets.compare_digest(user.get("password", ""), password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    try:
        return user_for(username, user["role"])
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="User has no valid role") from exc


# Login endpoint
@app.get("/login")
def login(user=Depends(authenticate)):
    return {"message": f"Welcome {user.username}!", "role": user.role}


# Protected test endpoint
@app.get("/test")
def test(user=Depends(authenticate)):
    return {"message": f"Hello {user.username}! You can now chat.", "role": user.role}


# Protected chat endpoint
@app.post("/chat")
def query(user=Depends(authenticate), message: str = "Hello"):
    try:
        content = answer(message, user.username, user.role, user.resource_scopes)
    except AgentError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    return {"hello": content}
