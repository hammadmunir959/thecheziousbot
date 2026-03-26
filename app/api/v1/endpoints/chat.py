"""
chat.py — CheziousBot chat endpoints.
"""

import json
import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langgraph.types import Command
from sqlmodel import Session

from ....schemas.schemas import ChatRequest, ChatResponse
from ....database.db import get_db
from ....agent.graphs.graph import workflow
from ....api.api_utils import (
    get_user,
    resolve_thread,
    make_config,
    build_input,
    get_interrupt,
    get_last_ai,
    stream_response
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, response: Response, db: Session = Depends(get_db)):
    user = get_user(request.user_id, db)
    thread_id = resolve_thread(user.id, request.thread_id)
    config = make_config(user.id, thread_id)
    graph_input, _ = build_input(config, request.message)

    try:
        workflow.invoke(graph_input, config=config)
    except Exception:
        logger.exception("Graph invocation failed")
        raise HTTPException(status_code=500, detail="Agent graph execution failed.")

    response.headers["X-Thread-ID"] = thread_id

    interrupt = get_interrupt(config)
    reply = interrupt or get_last_ai(config)
    if not reply:
        raise HTTPException(status_code=500, detail="Agent graph produced no response.")

    return ChatResponse(
        reply=reply, 
        thread_id=thread_id
        
        )


@router.post("/chat-stream")
def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Endpoint for streaming chat responses using Server-Sent Events (SSE).
    invokes the agent graph and streams the response back to the client as it is generated.
    """
    
    user = get_user(request.user_id, db)
    thread_id = resolve_thread(user.id, request.thread_id)
    config = make_config(user.id, thread_id)

    return StreamingResponse(
        stream_response(config, request.message),
        media_type="text/event-stream",
        headers={"X-Thread-ID": thread_id},
    )