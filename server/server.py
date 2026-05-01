"""FastAPI app — endpoints for in-store navigation sessions."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse, Response

from server.annotator import annotate
from server.config import ensure_output_dir
from server.goal_decomposer import decompose_goal
from server.models import (
    AnswerRequest,
    ErrorResponse,
    StartSessionRequest,
    StartSessionResponse,
    TurnResponse,
    VLMAction,
)
from server.perception import Perception
from server.session import SessionStore
from server.vlm import decide as _vlm_decide_impl

log = logging.getLogger(__name__)

app = FastAPI(title="UniGoal Store-Nav Server")

_store = SessionStore()
_perception: Optional[Perception] = None


def get_store() -> SessionStore:
    return _store


def get_perception() -> Perception:
    global _perception
    if _perception is None:
        _perception = Perception()
        _perception.load()
    return _perception


def vlm_decide(*args, **kwargs):
    return _vlm_decide_impl(*args, **kwargs)


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


@app.post("/session/{session_id}/photo", response_model=TurnResponse)
async def upload_photo(session_id: str, photo: UploadFile = File(...)) -> TurnResponse:
    s = _store.get(session_id)
    if s is None:
        raise HTTPException(status_code=404, detail={"error": "session_not_found", "detail": session_id})
    if s.arrived:
        raise HTTPException(status_code=409, detail={"error": "already_arrived", "detail": "session is complete"})
    if s.pending_question is not None:
        raise HTTPException(status_code=409, detail={"error": "answer_pending", "detail": "POST /answer first"})

    out_dir = ensure_output_dir(session_id)
    photo_bytes = await photo.read()
    nid_for_path = s.topomap.graph.number_of_nodes()
    photo_path = out_dir / "photo" / f"{nid_for_path}.jpg"
    photo_path.write_bytes(photo_bytes)

    perception = get_perception()
    detections = perception.detect(str(photo_path), s.goal_objects)
    detected_labels = [d.label for d in detections]

    nid = s.topomap.add_node(photo_path=str(photo_path), detected=detected_labels, summary="")
    if s.last_node_id is not None:
        s.topomap.add_edge(s.last_node_id, nid, action=s.last_planned_action or "(unknown)")

    detections_summary = ", ".join(f"{d.label} ({d.score:.2f})" for d in detections) or "(none)"
    topomap_summary = s.topomap.summarize_for_vlm(current_id=nid)

    vlm_resp = vlm_decide(
        image_path=str(photo_path),
        goal=s.goal,
        goal_objects=s.goal_objects,
        topomap_summary=topomap_summary,
        detections_summary=detections_summary,
        prior_question=None,
        prior_answer=None,
    )

    s.topomap.graph.nodes[nid]["summary"] = vlm_resp.vlm_summary
    s.last_detections = [d.__dict__ for d in detections]
    s.last_photo_path = str(photo_path)
    s.last_node_id = nid

    annotated_path = out_dir / "annotated" / f"{nid}.jpg"
    annotate(str(photo_path), str(annotated_path), detections, banner_text=f"{vlm_resp.action.value}: {vlm_resp.guidance}")

    s.history.append({
        "kind": "photo",
        "node_id": nid,
        "vlm_action": vlm_resp.action.value,
        "vlm_guidance": vlm_resp.guidance,
    })

    if vlm_resp.action == VLMAction.ARRIVED:
        s.arrived = True
        s.goal_node = nid
        s.last_planned_action = None
    elif vlm_resp.action == VLMAction.ASK:
        s.pending_question = vlm_resp.question
    else:  # MOVE
        s.last_planned_action = vlm_resp.guidance

    return TurnResponse(
        action=vlm_resp.action,
        guidance=vlm_resp.guidance,
        question=vlm_resp.question,
        node_id=nid,
        annotated_photo_url=f"/session/{session_id}/photo/{nid}.jpg",
    )


@app.post("/session/{session_id}/answer", response_model=TurnResponse)
def post_answer(session_id: str, req: AnswerRequest) -> TurnResponse:
    s = _store.get(session_id)
    if s is None:
        raise HTTPException(status_code=404, detail={"error": "session_not_found", "detail": session_id})
    if s.pending_question is None:
        raise HTTPException(status_code=409, detail={"error": "no_question_pending", "detail": "no question is open"})
    if s.last_photo_path is None or s.last_node_id is None:
        raise HTTPException(status_code=409, detail={"error": "no_prior_photo", "detail": "answer requires a prior photo"})

    detections_summary = ", ".join(
        f"{d['label']} ({d['score']:.2f})" for d in s.last_detections
    ) or "(none)"
    topomap_summary = s.topomap.summarize_for_vlm(current_id=s.last_node_id)
    prior_question = s.pending_question

    vlm_resp = vlm_decide(
        image_path=s.last_photo_path,
        goal=s.goal,
        goal_objects=s.goal_objects,
        topomap_summary=topomap_summary,
        detections_summary=detections_summary,
        prior_question=prior_question,
        prior_answer=req.answer,
    )

    s.history.append({
        "kind": "answer",
        "user_answer": req.answer,
        "vlm_action": vlm_resp.action.value,
        "vlm_guidance": vlm_resp.guidance,
    })

    s.pending_question = None
    if vlm_resp.action == VLMAction.ARRIVED:
        s.arrived = True
        s.goal_node = s.last_node_id
        s.last_planned_action = None
    elif vlm_resp.action == VLMAction.ASK:
        s.pending_question = vlm_resp.question
    else:
        s.last_planned_action = vlm_resp.guidance

    return TurnResponse(
        action=vlm_resp.action,
        guidance=vlm_resp.guidance,
        question=vlm_resp.question,
        node_id=s.last_node_id,
        annotated_photo_url=f"/session/{session_id}/photo/{s.last_node_id}.jpg",
    )


@app.get("/session/{session_id}/map")
def get_map(session_id: str, format: str = Query(default="json")):
    s = _store.get(session_id)
    if s is None:
        raise HTTPException(status_code=404, detail={"error": "session_not_found", "detail": session_id})
    if format == "png":
        png = s.topomap.render_png(current_id=s.last_node_id)
        return Response(content=png, media_type="image/png")
    return s.topomap.to_dict(current_node=s.last_node_id, goal_node=s.goal_node)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/session/{session_id}")
def get_session(session_id: str):
    s = _store.get(session_id)
    if s is None:
        raise HTTPException(status_code=404, detail={"error": "session_not_found", "detail": session_id})
    return {
        "id": s.id,
        "goal": s.goal,
        "goal_objects": s.goal_objects,
        "history": s.history,
        "pending_question": s.pending_question,
        "arrived": s.arrived,
        "last_node_id": s.last_node_id,
        "goal_node": s.goal_node,
        "created_at": s.created_at.isoformat(),
    }
