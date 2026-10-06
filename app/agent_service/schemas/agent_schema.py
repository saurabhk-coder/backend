from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ----------------------------------------------------
# Profile & Config Schemas
# ----------------------------------------------------
class AgentActionItem(BaseModel):
    id: str = Field(..., description="Action ID, e.g., 'book_meeting'")
    title: str = Field(..., description="Button label, e.g., 'Book a Meeting'")
    action: str = Field("open_modal", description="Action type: open_modal, trigger_event, navigate")
    icon: Optional[str] = None


class AgentProfileResponse(BaseModel):
    agent_name: str = "Leslie"
    agent_title: str = "AI Product & Support Specialist"
    company_name: str = "Aaralia"
    avatar_url: Optional[str] = "/html/assets/leslie_avatar.jpg"
    video_url: Optional[str] = None
    greeting_message: str = (
        "Hi! I'm Leslie. How are you currently managing team goals and daily tasks? "
        "I can help show how our platform connects strategy to execution smoothly."
    )
    suggested_questions: List[str] = [
        "What are our shift timings?",
        "Who is available in the engineering department?",
        "Find employees with Python or SQL skills",
        "What is our weekend and calendar policy?",
    ]
    quick_actions: List[AgentActionItem] = [
        AgentActionItem(id="book_meeting", title="Book a Meeting", action="open_modal"),
        AgentActionItem(id="request_support", title="Request Support", action="open_modal"),
    ]
    voice_enabled: bool = True
    streaming_enabled: bool = True
    database_search_enabled: bool = True


class AgentProfileUpdate(BaseModel):
    agent_name: Optional[str] = None
    agent_title: Optional[str] = None
    company_name: Optional[str] = None
    avatar_url: Optional[str] = None
    video_url: Optional[str] = None
    greeting_message: Optional[str] = None
    suggested_questions: Optional[List[str]] = None
    quick_actions: Optional[List[AgentActionItem]] = None
    system_prompt: Optional[str] = None


# ----------------------------------------------------
# Session Schemas
# ----------------------------------------------------
class CreateSessionRequest(BaseModel):
    visitor_id: Optional[str] = None
    session_name: Optional[str] = "Chat with Leslie"
    metadata: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    session_id: str
    session_name: str
    is_active: bool
    created_at: datetime
    greeting_message: str
    quick_actions: List[AgentActionItem]


# ----------------------------------------------------
# Chat Schemas
# ----------------------------------------------------
class ChatMessageRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1, description="User's question or message")
    search_database: bool = Field(True, description="Whether to search the backend database for live context")
    stream: bool = Field(False, description="Whether client requests streaming response")


class ChatMessageResponse(BaseModel):
    session_id: str
    message_id: str
    response: str
    sender_type: str = "assistant"
    action_type: str = "chat"
    db_sources: Optional[List[Dict[str, Any]]] = None
    suggested_followups: Optional[List[str]] = None
    created_at: datetime


class MessageItem(BaseModel):
    id: str
    session_id: str
    sender_type: str
    content: str
    action_type: Optional[str] = "chat"
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime


class MessageHistoryResponse(BaseModel):
    session_id: str
    total_messages: int
    messages: List[MessageItem]


# ----------------------------------------------------
# Action Handlers: Book a Meeting & Request Support
# ----------------------------------------------------
class BookMeetingRequest(BaseModel):
    session_id: Optional[str] = None
    full_name: str = Field(..., min_length=2)
    email: str = Field(..., min_length=5)
    phone: Optional[str] = None
    preferred_date: date
    preferred_time: str = Field(..., description="e.g. '10:00 AM' or '14:30'")
    topic: Optional[str] = "Product Demo & Consultation"


class BookMeetingResponse(BaseModel):
    booking_id: str
    full_name: str
    email: str
    preferred_date: str
    preferred_time: str
    status: str
    confirmation_message: str


class SupportRequestCreate(BaseModel):
    session_id: Optional[str] = None
    full_name: str = Field(..., min_length=2)
    email: str = Field(..., min_length=5)
    subject: str = Field(..., min_length=3)
    description: str = Field(..., min_length=5)
    priority: str = Field("medium", description="low, medium, high, urgent")


class SupportRequestResponse(BaseModel):
    request_id: str
    full_name: str
    email: str
    subject: str
    priority: str
    status: str
    confirmation_message: str


# ----------------------------------------------------
# Direct Database Search
# ----------------------------------------------------
class DbSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language search term or keyword")
    entity_types: Optional[List[str]] = Field(
        default=["employees", "shifts", "departments", "calendar", "organizations"],
        description="Filter by database entities",
    )
    limit: int = 10


class DbSearchResponse(BaseModel):
    query: str
    total_found: int
    results: Dict[str, Any]
    summary: str


# ----------------------------------------------------
# Voice & Avatar Schemas
# ----------------------------------------------------
class TranscribeResponse(BaseModel):
    text: str
    confidence: float = 0.98
    language: str = "en"


class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    voice_id: Optional[str] = "en-US-Leslie-Neural"


class SynthesizeResponse(BaseModel):
    text: str
    audio_format: str = "audio/mp3"
    audio_base64: Optional[str] = None
    audio_url: Optional[str] = None
    duration_seconds: float = 3.5


class AvatarSessionResponse(BaseModel):
    session_id: str
    avatar_status: str = "idle"  # idle, speaking, listening
    video_stream_url: Optional[str] = None
    avatar_image_url: Optional[str] = None
    speak_now_available: bool = True
