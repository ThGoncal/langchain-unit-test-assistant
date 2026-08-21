"""
API principale de l'assistant de tests unitaires Python.
"""

import json
import os

import requests
from fastapi import FastAPI, Depends, HTTPException, Header

from api.authentification.auth import User
from core.chains import (
    get_analysis_chain,
    get_test_chain,
    get_explain_test_chain,
    get_chat_agent,
)
from core.schemas import CodeRequest, ChatRequest, ExplainTestRequest
from memory import memory

AUTH_URL = os.getenv("AUTH_URL", "http://auth:8001")

app = FastAPI(title="Assistant de Tests Unitaires Python")


def get_current_user(authorization: str = Header(...)) -> User:
    try:
        response = requests.get(
            f"{AUTH_URL}/me",
            headers={"Authorization": authorization},
            timeout=10,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=503, detail="API d'authentification indisponible"
        ) from exc

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Non authentifié")

    return User(**response.json())


def _log(username: str, request_content: str, result: dict) -> None:
    """Enregistre un échange requête/réponse dans l'historique de l'utilisateur."""
    memory.add_message(username, "user", request_content)
    memory.add_message(username, "assistant", json.dumps(result, ensure_ascii=False))


@app.post("/analyze")
def analyze(request: CodeRequest, user: User = Depends(get_current_user)):
    chain = get_analysis_chain()
    result = chain.invoke({"code": request.code}).model_dump()
    _log(user.username, request.code, result)
    return result


@app.post("/generate_test")
def generate_test(request: CodeRequest, user: User = Depends(get_current_user)):
    chain = get_test_chain()
    result = chain.invoke({"code": request.code}).model_dump()
    _log(user.username, request.code, result)
    return result


@app.post("/explain_test")
def explain_test(request: ExplainTestRequest, user: User = Depends(get_current_user)):
    chain = get_explain_test_chain()
    result = chain.invoke(
        {"code": request.code, "unit_test": request.unit_test}
    ).model_dump()
    _log(user.username, request.unit_test, result)
    return result


@app.post("/full_pipeline")
def full_pipeline(request: CodeRequest, user: User = Depends(get_current_user)):
    analysis = get_analysis_chain().invoke({"code": request.code})

    if not analysis.is_optimal:
        result = {"error": "Code non optimal", "analysis": analysis.model_dump()}
        _log(user.username, request.code, result)
        return result

    test_result = get_test_chain().invoke({"code": request.code})
    explanation_result = get_explain_test_chain().invoke(
        {"code": request.code, "unit_test": test_result.unit_test}
    )

    result = {
        "analysis": analysis.model_dump(),
        "test": test_result.model_dump(),
        "explanation": explanation_result.model_dump(),
    }
    _log(user.username, request.code, result)
    return result


@app.post("/chat")
def chat(request: ChatRequest, user: User = Depends(get_current_user)):
    agent = get_chat_agent()
    config = {"configurable": {"thread_id": user.username}}

    result = agent.invoke(
        {"messages": [{"role": "user", "content": request.input}]},
        config=config,
    )
    response_text = result["messages"][-1].content

    memory.add_message(user.username, "user", request.input)
    memory.add_message(user.username, "assistant", response_text)

    return {"response": response_text}


@app.get("/history")
def history(user: User = Depends(get_current_user)):
    return {"history": memory.get_history(user.username)}