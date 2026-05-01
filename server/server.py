"""FastAPI app — endpoints for in-store navigation sessions."""
from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from server.goal_decomposer import decompose_goal
from server.models import StartSessionRequest, StartSessionResponse, ErrorResponse
from server.session import SessionStore

log = logging.getLogger(__name__)

app = FastAPI(title="UniGoal Store-Nav Server")

_store = SessionStore()


def get_store() -> SessionStore:
    return _store


@app.exception_handler(HTTPException)
async def http_exc_handler(request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        body = ErrorResponse(
            error=exc.detail.get("error", "error"),
            detail=exc.detail.get("detail", ""),
        ).model_dump()
    else:
        body = ErrorResponse(error="error", detail=str(exc.detail)).model_dump()
    return JSONResponse(status_code=exc.status_code, content=body)


@app.post("/session", response_model=StartSessionResponse)
def start_session(req: StartSessionRequest) -> StartSessionResponse:
    if not req.goal.strip():
        raise HTTPException(status_code=400, detail={"error": "bad_request", "detail": "goal is empty"})
    goal_objects = decompose_goal(req.goal)
    s = _store.create(goal=req.goal, goal_objects=goal_objects)
    return StartSessionResponse(
        session_id=s.id,
        guidance="Upload a starting photo so I can see where you are.",
        goal_objects=goal_objects,
    )
