"""AUFI Assist API. Run from the backend/ folder:   uvicorn app.main:app --port 8000

Every route is mounted twice, at "/" and at "/api", so it works both behind the Vite dev proxy
(which strips /api) and from the production frontend build (which calls /api/...).
"""
import json
import logging

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import config, kb_files
from .agent import explainer
from .pipeline import run_turn, undo_last
from .rag import retriever
from .report import build_pdf
from .schemas import ChatRequest, SearchRequest
from .scoring import scorer
from .session import store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

app = FastAPI(title="AUFI Assist API", docs_url="/api/docs", openapi_url="/api/openapi.json")
router = APIRouter()


# ---- chat -------------------------------------------------------------------------------
@router.post("/chat/stream")
def chat_stream(req: ChatRequest):
    session = store.get(req.conversation_id)

    def events():
        for kind, payload in run_turn(session, req.message, req.answer):
            data = {"type": "step", "text": payload} if kind == "step" else {"type": "final", **payload.wire()}
            yield f"data: {json.dumps(data)}\n\n"

    return StreamingResponse(
        events(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/chat")
def chat(req: ChatRequest):
    session = store.get(req.conversation_id)
    final = None
    for kind, payload in run_turn(session, req.message, req.answer):
        if kind == "final":
            final = payload
    return final.wire()


@router.post("/chat/back")
def chat_back(req: ChatRequest):
    return undo_last(store.get(req.conversation_id)).wire()


# ---- PDF report ---------------------------------------------------------------------------
@router.get("/report/{conversation_id}/pdf")
def report_pdf(conversation_id: str):
    s = store.peek(conversation_id)
    if s is None or not s.finished:
        raise HTTPException(404, "No finished case with that id.")
    with s.lock:
        pdf = build_pdf(s)
    return Response(
        pdf, media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="aufi-assist-case-summary.pdf"'},
    )


# ---- conversations (history lives in memory; the list is never served, see README) --------
@router.get("/conversations")
def conversations():
    # Deliberately empty: a refresh on a shared hospital machine must not show the previous
    # patient's cases. The browser keeps its own sidebar list for the current page session.
    return []


@router.get("/conversations/{conversation_id}/messages")
def conversation_messages(conversation_id: str):
    s = store.peek(conversation_id)
    return s.messages if s else []


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str):
    store.delete(conversation_id)
    return {"ok": True}


# ---- knowledge base -----------------------------------------------------------------------
@router.get("/knowledge-base/status")
def kb_status():
    try:
        return {"documentCount": retriever.document_count(), "lastIndexed": retriever.last_indexed()}
    except NotImplementedError:
        return {"documentCount": 0, "lastIndexed": "Not connected"}


@router.post("/search")
def search(req: SearchRequest):
    try:
        return {"results": retriever.search(req.query, req.disease, req.content_type)}
    except NotImplementedError:
        raise HTTPException(503, "Guideline search is not connected yet.")


@router.get("/kb-docs/{filename}/content")
def kb_doc_content(filename: str):
    try:
        text = kb_files.document_text(filename)
    except ImportError:
        raise HTTPException(501, "pypdf is not installed.")
    if text is None:
        raise HTTPException(404, "Document not found.")
    return {"text": text}


@router.get("/kb-docs/{filename}")
def kb_doc(filename: str):
    p = kb_files.document_path(filename)
    if p is None:
        raise HTTPException(404, "Document not found.")
    return FileResponse(p)


# ---- health: shows which of your friend's modules are still stubs -------------------------
@router.get("/health")
def health():
    mods = {"scoring": scorer, "rag": retriever, "agent": explainer}
    return {
        "ok": True,
        "modules": {k: ("stub" if getattr(m, "STUB", False) else "ready") for k, m in mods.items()},
        "settings": {
            "maxQuestions": config.MAX_QUESTIONS,
            "confidenceThreshold": config.CONFIDENCE_THRESHOLD,
            "minQuestions": config.MIN_QUESTIONS,
            "shortlistSize": config.SHORTLIST_SIZE,
        },
    }


app.include_router(router)
app.include_router(router, prefix="/api", include_in_schema=False)

# Production: serve the built frontend (npm run build) from the same process, so the whole
# thing is one command with no Node and no internet.
if config.FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=config.FRONTEND_DIST, html=True), name="frontend")
