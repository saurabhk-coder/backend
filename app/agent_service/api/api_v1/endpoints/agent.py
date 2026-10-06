import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.agent_service.schemas.agent_schema import (
    AgentProfileResponse,
    AgentProfileUpdate,
    AvatarSessionResponse,
    BookMeetingRequest,
    BookMeetingResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    CreateSessionRequest,
    DbSearchRequest,
    DbSearchResponse,
    MessageHistoryResponse,
    MessageItem,
    SessionResponse,
    SupportRequestCreate,
    SupportRequestResponse,
    SynthesizeRequest,
    SynthesizeResponse,
    TranscribeResponse,
)
from app.agent_service.services.agent_service import AGENT_SERVICE
from app.agent_service.services.database_search_service import DATABASE_SEARCH_SERVICE
from app.agent_service.services.voice_service import VOICE_SERVICE
from app.agent_service.api.deps import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# 1. Profile & Configuration
# =============================================================================
@router.get("/profile", response_model=AgentProfileResponse, summary="Get Agent Persona & Widget Config")
def get_agent_profile(db: Session = Depends(get_db)) -> AgentProfileResponse:
    """
    Returns the agent profile, avatar image/video, greeting message,
    quick actions ('Book a Meeting', 'Request Support'), and suggested questions.
    """
    return AGENT_SERVICE.get_profile(db)


@router.put("/profile", response_model=AgentProfileResponse, summary="Update Agent Configuration")
def update_agent_profile(
    update_data: AgentProfileUpdate,
    db: Session = Depends(get_db),
) -> AgentProfileResponse:
    """Update agent persona, greeting, or system prompt."""
    return AGENT_SERVICE.update_profile(db, update_data)


# =============================================================================
# 2. Conversation & Session Management
# =============================================================================
@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED, summary="Start New Agent Session")
def create_session(
    payload: Optional[CreateSessionRequest] = None,
    db: Session = Depends(get_db),
) -> SessionResponse:
    """
    Initializes a new interactive session with Leslie, creates session records,
    and returns initial greeting message and quick action buttons.
    """
    payload = payload or CreateSessionRequest()
    session = AGENT_SERVICE.create_session(
        db=db,
        visitor_id=payload.visitor_id,
        session_name=payload.session_name or "Chat with Leslie",
        metadata=payload.metadata,
    )
    profile = AGENT_SERVICE.get_profile(db)
    return SessionResponse(
        session_id=str(session.id),
        session_name=session.session_name,
        is_active=session.is_active,
        created_at=session.created_at,
        greeting_message=profile.greeting_message,
        quick_actions=profile.quick_actions,
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse, summary="Get Session Details")
def get_session(session_id: str, db: Session = Depends(get_db)) -> SessionResponse:
    session = AGENT_SERVICE.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    profile = AGENT_SERVICE.get_profile(db)
    return SessionResponse(
        session_id=str(session.id),
        session_name=session.session_name,
        is_active=session.is_active,
        created_at=session.created_at,
        greeting_message=profile.greeting_message,
        quick_actions=profile.quick_actions,
    )


@router.get("/sessions/{session_id}/messages", response_model=MessageHistoryResponse, summary="Get Message History")
def get_messages(session_id: str, db: Session = Depends(get_db)) -> MessageHistoryResponse:
    session = AGENT_SERVICE.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = AGENT_SERVICE.get_messages(db, session_id)
    items = [
        MessageItem(
            id=str(m.id),
            session_id=str(m.session_id),
            sender_type=m.sender_type,
            content=m.content,
            action_type=m.action_type,
            metadata_json=m.metadata_json,
            created_at=m.created_at,
        )
        for m in messages
    ]
    return MessageHistoryResponse(
        session_id=str(session.id),
        total_messages=len(items),
        messages=items,
    )


# =============================================================================
# 3. Interactive Chat & Streaming Q&A Grounded in Database
# =============================================================================
@router.post("/chat", response_model=ChatMessageResponse, summary="Send Message to Agent")
def chat_with_agent(
    req: ChatMessageRequest,
    db: Session = Depends(get_db),
) -> ChatMessageResponse:
    """
    Processes user's message, searches the PostgreSQL database for real context
    (employees, shifts, departments, calendar settings), and returns Leslie's answer.
    """
    return AGENT_SERVICE.process_chat(db, req)


@router.post("/chat/stream", summary="Stream Agent Response (SSE)")
async def stream_chat_with_agent(
    req: ChatMessageRequest,
    db: Session = Depends(get_db),
):
    """
    Server-Sent Events (SSE) streaming endpoint for typing animation in the UI.
    """
    return StreamingResponse(
        AGENT_SERVICE.stream_chat(db, req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# =============================================================================
# 4. Direct Database Search Engine
# =============================================================================
@router.post("/search-db", response_model=DbSearchResponse, summary="Search Database Directly")
def search_database(
    req: DbSearchRequest,
    db: Session = Depends(get_db),
) -> DbSearchResponse:
    """
    Directly queries the database for employees, shifts, departments,
    calendar settings, and organizations matching natural language keywords.
    """
    res = DATABASE_SEARCH_SERVICE.comprehensive_search(db, req.query)
    return DbSearchResponse(
        query=res["query"],
        total_found=res["total_found"],
        results=res["results"],
        summary=res["summary"],
    )


# =============================================================================
# 5. Quick Actions: Book a Meeting & Request Support
# =============================================================================
@router.post("/actions/book-meeting", response_model=BookMeetingResponse, summary="Book a Meeting (CTA)")
def book_meeting(
    payload: BookMeetingRequest,
    db: Session = Depends(get_db),
) -> BookMeetingResponse:
    """
    Handles the 'Book a Meeting' button submission.
    Persists reservation in database and returns confirmation.
    """
    return AGENT_SERVICE.book_meeting(db, payload)


@router.get("/actions/meetings", summary="List All Booked Meetings")
def list_meetings(limit: int = 20, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    return AGENT_SERVICE.list_meetings(db, limit)


@router.post("/actions/request-support", response_model=SupportRequestResponse, summary="Request Support (CTA)")
def request_support(
    payload: SupportRequestCreate,
    db: Session = Depends(get_db),
) -> SupportRequestResponse:
    """
    Handles the 'Request Support' button submission.
    Creates support ticket in database and returns confirmation.
    """
    return AGENT_SERVICE.create_support_request(db, payload)


@router.get("/actions/support-requests", summary="List All Support Tickets")
def list_support_requests(limit: int = 20, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    return AGENT_SERVICE.list_support_requests(db, limit)


# =============================================================================
# 6. Voice & Avatar ("Speak now" capability)
# =============================================================================
@router.post("/voice/transcribe", response_model=TranscribeResponse, summary="Speech to Text (Microphone)")
async def transcribe_voice(
    file: UploadFile = File(..., description="Audio recording file (webm/wav/mp3)"),
) -> TranscribeResponse:
    """Transcribes audio from the widget microphone into text."""
    return await VOICE_SERVICE.transcribe_audio(file)


@router.post("/voice/synthesize", response_model=SynthesizeResponse, summary="Text to Speech")
async def synthesize_voice(req: SynthesizeRequest) -> SynthesizeResponse:
    """Synthesizes text answer into speech audio for avatar playback."""
    return await VOICE_SERVICE.synthesize_speech(req.text, req.voice_id)


@router.get("/avatar/status", response_model=AvatarSessionResponse, summary="Avatar Interactive Status")
def get_avatar_status(session_id: Optional[str] = "default") -> AvatarSessionResponse:
    """Returns avatar state (idle, speaking, listening) and video stream URL."""
    return VOICE_SERVICE.get_avatar_session(session_id or "default")
