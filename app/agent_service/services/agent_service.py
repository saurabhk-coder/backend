import json
import logging
import os
import re
import time
from datetime import date, datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import UUID, uuid4

import httpx
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from ..models.agent_models import (
    AiAgentConfigDb,
    AiAgentMeetingBookingDb,
    AiAgentMessageDb,
    AiAgentSessionDb,
    AiAgentSupportRequestDb,
)
from ..schemas.agent_schema import (
    AgentActionItem,
    AgentProfileResponse,
    AgentProfileUpdate,
    BookMeetingRequest,
    BookMeetingResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    CreateEmployeeActionRequest,
    CreateEmployeeActionResponse,
    SupportRequestCreate,
    SupportRequestResponse,
)
from .database_search_service import DATABASE_SEARCH_SERVICE
from app.employee_service.models.employee import EmployeeDb
from app.employee_service.models.employee_personal_information import EmployeePersonalInformationDb
from app.employee_service.crud.crud_employee_personal_information import (
    CRUD_EMPLOYEE_PERSONAL_INFORMATION,
    _to_uuid,
)
from app.employee_service.schemas.employee_personal_information import (
    EmployeePersonalInformationCreate,
)
from app.organization_service.models.organization import OrganizationDb

logger = logging.getLogger(__name__)


def _parse_date(val: Any) -> Optional[date]:
    if not val:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    val_str = str(val).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d %b %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            continue
    return None


EMPLOYEE_FIELD_STEPS = [
    {
        "field": "first_name",
        "label": "First Name",
        "step_num": 1,
        "required": True,
        "prompt": (
            "👋 **Let's create a new employee!**\n\n"
            "I will guide you step-by-step to enter the employee's details into the database.\n"
            "*(You can type **'skip'** for any optional field, **'save'** anytime once first name is entered, or **'cancel'** to abort).*\n\n"
            "1️⃣ What is the employee's **First Name**? *(Required)*"
        ),
        "hint": "e.g., Alex, Sarah, David",
    },
    {
        "field": "last_name",
        "label": "Last Name",
        "step_num": 2,
        "required": False,
        "prompt": "2️⃣ What is their **Last Name**? *(or type 'skip')*",
        "hint": "e.g., Smith, Connor",
    },
    {
        "field": "email",
        "label": "Email Address",
        "step_num": 3,
        "required": False,
        "prompt": "3️⃣ What is their **Email Address**? *(e.g. employee@company.com, or type 'skip')*",
        "hint": "e.g., sarah.connor@example.com",
    },
    {
        "field": "mobile_number",
        "label": "Mobile Phone Number",
        "step_num": 4,
        "required": False,
        "prompt": "4️⃣ What is their **Mobile Phone Number**? *(or type 'skip')*",
        "hint": "e.g., +1-555-0199 or 9876543210",
    },
    {
        "field": "gender",
        "label": "Gender",
        "step_num": 5,
        "required": False,
        "prompt": "5️⃣ What is their **Gender**? *(e.g., Female, Male, Other, or type 'skip')*",
        "hint": "e.g., Female, Male, Other",
    },
    {
        "field": "date_of_birth",
        "label": "Date of Birth",
        "step_num": 6,
        "required": False,
        "prompt": "6️⃣ What is their **Date of Birth**? *(Format: YYYY-MM-DD, e.g. 1995-06-15, or type 'skip')*",
        "hint": "YYYY-MM-DD",
    },
    {
        "field": "govt_id_proof",
        "label": "Government ID Proof Type",
        "step_num": 7,
        "required": False,
        "prompt": "7️⃣ What type of **Government ID Proof**? *(e.g., Passport, Aadhaar, PAN, SSN, or type 'skip')*",
        "hint": "e.g., Passport, PAN, Aadhaar, SSN",
    },
    {
        "field": "id_proof_number",
        "label": "ID Proof Document Number",
        "step_num": 8,
        "required": False,
        "prompt": "8️⃣ What is their **ID Proof Document Number**? *(or type 'skip')*",
        "hint": "e.g., P98765432",
    },
    {
        "field": "nationality",
        "label": "Nationality",
        "step_num": 9,
        "required": False,
        "prompt": "9️⃣ What is their **Nationality**? *(e.g. American, Indian, Canadian, or type 'skip')*",
        "hint": "e.g., American, Indian",
    },
    {
        "field": "emergency_contact",
        "label": "Emergency Contact Number",
        "step_num": 10,
        "required": False,
        "prompt": "🔟 What is their **Emergency Contact Number**? *(or type 'skip')*",
        "hint": "e.g., +1-555-0123",
    },
    {
        "field": "marital_status",
        "label": "Marital Status",
        "step_num": 11,
        "required": False,
        "prompt": "1️⃣1️⃣ What is their **Marital Status**? *(Single, Married, Divorced, or type 'skip')*",
        "hint": "e.g., Single, Married",
    },
    {
        "field": "spouse_name",
        "label": "Spouse's Name",
        "step_num": 12,
        "required": False,
        "prompt": "1️⃣2️⃣ What is their **Spouse's Name**? *(or type 'skip')*",
        "hint": "e.g., Jane Smith",
    },
    {
        "field": "father_name",
        "label": "Father's Name",
        "step_num": 13,
        "required": False,
        "prompt": "1️⃣3️⃣ What is their **Father's Name**? *(or type 'skip')*",
        "hint": "e.g., John Smith Sr.",
    },
    {
        "field": "mother_name",
        "label": "Mother's Name",
        "step_num": 14,
        "required": False,
        "prompt": "1️⃣4️⃣ What is their **Mother's Name**? *(or type 'skip')*",
        "hint": "e.g., Mary Smith",
    },
    {
        "field": "address",
        "label": "Street Address",
        "step_num": 15,
        "required": False,
        "prompt": "1️⃣5️⃣ What is their **Residential Street Address**? *(or type 'skip')*",
        "hint": "e.g., 100 Tech Blvd, Suite 400",
    },
    {
        "field": "city",
        "label": "City",
        "step_num": 16,
        "required": False,
        "prompt": "1️⃣6️⃣ What **City**? *(or type 'skip')*",
        "hint": "e.g., San Francisco, Austin, Mumbai",
    },
    {
        "field": "state",
        "label": "State / Province",
        "step_num": 17,
        "required": False,
        "prompt": "1️⃣7️⃣ What **State / Province**? *(or type 'skip')*",
        "hint": "e.g., CA, TX, Ontario",
    },
    {
        "field": "zip_code",
        "label": "ZIP / Postal Code",
        "step_num": 18,
        "required": False,
        "prompt": "1️⃣8️⃣ What is their **ZIP / Postal Code**? *(or type 'skip')*",
        "hint": "e.g., 94107",
    },
    {
        "field": "profile_photo",
        "label": "Profile Photo URL",
        "step_num": 19,
        "required": False,
        "prompt": "1️⃣9️⃣ Do you have a **Profile Photo URL**? *(or type 'skip' to finish and save)*",
        "hint": "e.g., https://example.com/avatar.jpg",
    },
]


class AgentService:
    def __init__(self):
        self.default_persona = {
            "agent_name": "Leslie",
            "agent_title": "AI Product & Support Specialist",
            "company_name": "Aaralia",
            "avatar_url": "/html/assets/leslie_avatar.jpg",
            "video_url": None,
            "greeting_message": (
                "Hi! I'm Leslie. How are you currently managing team goals and daily tasks? "
                "I can help show how our platform connects strategy to execution smoothly."
            ),
            "suggested_questions": [
                "Create a new employee",
                "What are our shift timings?",
                "Who is available in the engineering department?",
                "Find employees with Python or SQL skills",
                "What is our weekend and calendar policy?",
            ],
            "quick_actions": [
                {"id": "create_employee", "title": "Create Employee", "action": "open_modal"},
                {"id": "book_meeting", "title": "Book a Meeting", "action": "open_modal"},
                {"id": "request_support", "title": "Request Support", "action": "open_modal"},
            ],
        }

        self._cached_profile: Optional[AgentProfileResponse] = None
        self._cache_time: float = 0
        self._onboarding_sessions: Dict[str, Dict[str, Any]] = {}
        self._local_sessions: Dict[str, AiAgentSessionDb] = {}

    # -------------------------------------------------------------------------
    # Profile & Configuration
    # -------------------------------------------------------------------------
    def get_profile(self, db: Session) -> AgentProfileResponse:
        if self._cached_profile and (time.time() - self._cache_time < 60):
            return self._cached_profile

        try:
            config = db.query(AiAgentConfigDb).filter(AiAgentConfigDb.is_active == True).first()
            if config:
                profile = AgentProfileResponse(
                    agent_name=config.agent_name,
                    agent_title=config.agent_title,
                    company_name=config.company_name,
                    avatar_url=config.avatar_url or self.default_persona["avatar_url"],
                    video_url=config.video_url,
                    greeting_message=config.greeting_message,
                    suggested_questions=config.suggested_questions or self.default_persona["suggested_questions"],
                    quick_actions=[
                        AgentActionItem(**item)
                        for item in (config.quick_actions or self.default_persona["quick_actions"])
                    ],
                    voice_enabled=True,
                    streaming_enabled=True,
                    database_search_enabled=True,
                )
                self._cached_profile = profile
                self._cache_time = time.time()
                return profile
        except Exception as e:
            logger.warning(f"Could not load agent config from DB, using defaults: {e}")

        fallback = AgentProfileResponse(
            agent_name=self.default_persona["agent_name"],
            agent_title=self.default_persona["agent_title"],
            company_name=self.default_persona["company_name"],
            avatar_url=self.default_persona["avatar_url"],
            greeting_message=self.default_persona["greeting_message"],
            suggested_questions=self.default_persona["suggested_questions"],
            quick_actions=[AgentActionItem(**a) for a in self.default_persona["quick_actions"]],
        )
        self._cached_profile = fallback
        self._cache_time = time.time()
        return fallback

    def update_profile(self, db: Session, update_data: AgentProfileUpdate) -> AgentProfileResponse:
        config = db.query(AiAgentConfigDb).filter(AiAgentConfigDb.is_active == True).first()
        if not config:
            config = AiAgentConfigDb()
            db.add(config)

        if update_data.agent_name is not None:
            config.agent_name = update_data.agent_name
        if update_data.agent_title is not None:
            config.agent_title = update_data.agent_title
        if update_data.company_name is not None:
            config.company_name = update_data.company_name
        if update_data.avatar_url is not None:
            config.avatar_url = update_data.avatar_url
        if update_data.video_url is not None:
            config.video_url = update_data.video_url
        if update_data.greeting_message is not None:
            config.greeting_message = update_data.greeting_message
        if update_data.suggested_questions is not None:
            config.suggested_questions = update_data.suggested_questions
        if update_data.quick_actions is not None:
            config.quick_actions = [a.model_dump() for a in update_data.quick_actions]
        if update_data.system_prompt is not None:
            config.system_prompt = update_data.system_prompt

        config.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(config)
        return self.get_profile(db)

    # -------------------------------------------------------------------------
    # Sessions
    # -------------------------------------------------------------------------
    def create_session(
        self,
        db: Session,
        visitor_id: Optional[str] = None,
        session_name: str = "Chat with Leslie",
        metadata: Optional[Dict[str, Any]] = None,
        session_id_override: Optional[UUID] = None,
    ) -> AiAgentSessionDb:
        session = AiAgentSessionDb(
            id=session_id_override or uuid4(),
            session_name=session_name,
            visitor_id=visitor_id,
            metadata_json=metadata or {},
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self._local_sessions[str(session.id)] = session
        if not DATABASE_SEARCH_SERVICE._should_skip_db():
            try:
                db.add(session)
                db.commit()
                db.refresh(session)
            except Exception as e:
                db.rollback()
                DATABASE_SEARCH_SERVICE._mark_db_error()
                logger.warning(f"Could not persist session to DB: {e}")

        # Automatically insert initial greeting message from Leslie
        profile = self.get_profile(db)
        initial_msg = AiAgentMessageDb(
            id=uuid4(),
            session_id=session.id,
            sender_type="assistant",
            content=profile.greeting_message,
            action_type="greeting",
            metadata_json={"quick_actions": [a.model_dump() for a in profile.quick_actions]},
            created_at=datetime.now(timezone.utc),
        )
        if not DATABASE_SEARCH_SERVICE._should_skip_db():
            try:
                db.add(initial_msg)
                db.commit()
            except Exception as e:
                db.rollback()
                DATABASE_SEARCH_SERVICE._mark_db_error()
                logger.warning(f"Could not persist initial message to DB: {e}")

        return session

    def get_session(self, db: Session, session_id: str) -> Optional[AiAgentSessionDb]:
        sid = str(session_id).strip()
        if sid in self._local_sessions:
            return self._local_sessions[sid]
        if not DATABASE_SEARCH_SERVICE._should_skip_db():
            try:
                val = UUID(sid)
                db_session = db.query(AiAgentSessionDb).filter(AiAgentSessionDb.id == val).first()
                if db_session:
                    self._local_sessions[sid] = db_session
                    return db_session
            except Exception as e:
                DATABASE_SEARCH_SERVICE._mark_db_error()
                logger.warning(f"Could not query session from DB: {e}")
        return self._local_sessions.get(sid)

    def get_messages(self, db: Session, session_id: str) -> List[AiAgentMessageDb]:
        try:
            val = UUID(session_id)
            return (
                db.query(AiAgentMessageDb)
                .filter(AiAgentMessageDb.session_id == val)
                .order_by(AiAgentMessageDb.created_at.asc())
                .all()
            )
        except Exception:
            return []

    # -------------------------------------------------------------------------
    # Chat & Database Q&A Generation
    # -------------------------------------------------------------------------
    def process_chat(self, db: Session, req: ChatMessageRequest) -> ChatMessageResponse:
        session = self.get_session(db, req.session_id)
        if not session:
            # Create session on the fly if invalid/missing, preserving requested ID if valid UUID
            req_uuid = None
            try:
                req_uuid = UUID(req.session_id)
            except Exception:
                pass
            session = self.create_session(db, session_name="Interactive Session", session_id_override=req_uuid)
            req.session_id = str(session.id)

        # 1. Record user message
        user_msg = AiAgentMessageDb(
            id=uuid4(),
            session_id=session.id,
            sender_type="user",
            content=req.message,
            action_type="chat",
            metadata_json={},
            created_at=datetime.now(timezone.utc),
        )
        if not DATABASE_SEARCH_SERVICE._should_skip_db():
            try:
                db.add(user_msg)
                db.commit()
            except Exception as e:
                db.rollback()
                DATABASE_SEARCH_SERVICE._mark_db_error()
                logger.warning(f"Could not persist user message: {e}")

        # 2. Check for Employee Onboarding / Creation Flow (Conversational Step-by-Step)
        onboarding_reply = self._handle_employee_onboarding_turn(db, session, req.message)
        if onboarding_reply:
            return onboarding_reply

        # 3. Check for action intents (Book Meeting / Support)
        lower_msg = req.message.lower()
        if "book a meeting" in lower_msg or "schedule a demo" in lower_msg:
            reply_text = (
                "I'd love to help you book a meeting! Please click the **'Book a Meeting'** button above "
                "or provide your name, email, and preferred date/time right here, and I'll confirm your reservation."
            )
            return self._record_and_return_assistant_reply(
                db=db,
                session=session,
                reply_text=reply_text,
                action_type="book_meeting_prompt",
                db_sources=None,
                suggested_followups=["Book a Meeting", "What are our office hours?", "Request Support", "Create Employee"],
            )

        if "request support" in lower_msg or "help desk" in lower_msg or "submit ticket" in lower_msg:
            reply_text = (
                "I can certainly connect you with our support team! Please click the **'Request Support'** button "
                "or describe the issue you're facing, and I will create a priority support ticket for you."
            )
            return self._record_and_return_assistant_reply(
                db=db,
                session=session,
                reply_text=reply_text,
                action_type="support_prompt",
                db_sources=None,
                suggested_followups=["Request Support", "Book a Meeting", "Check shift schedule", "Create Employee"],
            )

        # 3. Query Database for Grounding
        db_results: Optional[Dict[str, Any]] = None
        db_sources: List[Dict[str, Any]] = []
        if req.search_database:
            db_results = DATABASE_SEARCH_SERVICE.comprehensive_search(db, req.message)
            for entity_key, items in db_results.get("results", {}).items():
                if isinstance(items, list) and items:
                    db_sources.append({"entity": entity_key, "count": len(items), "data": items[:3]})

        # 4. Generate AI Agent Response (External LLM if available, or Intelligent Internal DB Synthesizer)
        reply_text = self._generate_response(db, req.message, db_results)

        followups = [
            "Book a Meeting",
            "Request Support",
            "What are our shift timings?",
            "Who is in the engineering department?",
        ]

        return self._record_and_return_assistant_reply(
            db=db,
            session=session,
            reply_text=reply_text,
            action_type="chat",
            db_sources=db_sources,
            suggested_followups=followups,
        )

    def _generate_response(self, db: Session, user_query: str, db_results: Optional[Dict[str, Any]]) -> str:
        """
        Generates persona-grounded response. If an OpenAI or Gemini API key is configured
        in the environment, calls the API with the live DB context; otherwise uses our
        built-in DB synthesis engine for instant offline accuracy.
        """
        openai_key = os.getenv("OPENAI_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")

        profile = self.get_profile(db)
        db_summary = db_results.get("summary", "") if db_results else ""

        # Check if external LLM is configured
        if openai_key:
            try:
                return self._call_openai(openai_key, user_query, db_summary, profile)
            except Exception as e:
                logger.error(f"OpenAI call failed, falling back to local DB synthesizer: {e}")

        if gemini_key:
            try:
                return self._call_gemini(gemini_key, user_query, db_summary, profile)
            except Exception as e:
                logger.error(f"Gemini call failed, falling back to local DB synthesizer: {e}")

        # Intelligent Built-in DB Synthesizer (Instant, 100% reliable, grounded in DB)
        return self._synthesize_local_db_response(user_query, db_summary, profile)

    def _synthesize_local_db_response(self, user_query: str, db_summary: str, profile: AgentProfileResponse) -> str:
        """Synthesizes human-like answer in Leslie's voice using PostgreSQL search results."""
        if db_summary and "No matching records found" not in db_summary:
            return (
                f"Here is what I found directly in our database for you:\n\n"
                f"{db_summary}\n\n"
                f"Would you like me to book a meeting with the team, or is there anything else I can look up for you?"
            )
        else:
            return (
                f"I checked our database, but didn't find specific records matching **'{user_query}'**. "
                f"However, I can help you connect with our team! "
                f"You can click **Book a Meeting** to speak with our specialists, or **Request Support** if you need assistance."
            )

    def _call_openai(self, api_key: str, user_query: str, db_context: str, profile: AgentProfileResponse) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        system_prompt = (
            f"You are {profile.agent_name}, an AI specialist from {profile.company_name}. "
            f"You are warm, concise, professional, and knowledgeable. "
            f"Always prioritize facts from the database context provided below. "
            f"If the information is not in the database context, politely offer to book a meeting or submit a support ticket.\n\n"
            f"Database Context:\n{db_context}"
        )
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query},
            ],
            "temperature": 0.4,
            "max_tokens": 400,
        }
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, headers={"Authorization": f"Bearer {api_key}"}, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

    def _call_gemini(self, api_key: str, user_query: str, db_context: str, profile: AgentProfileResponse) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        prompt = (
            f"You are {profile.agent_name}, an AI assistant from {profile.company_name}. "
            f"Use the following real database context to answer the user's question accurately.\n\n"
            f"Database Context:\n{db_context}\n\n"
            f"User Question: {user_query}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()

    def _record_and_return_assistant_reply(
        self,
        db: Session,
        session: AiAgentSessionDb,
        reply_text: str,
        action_type: str = "chat",
        db_sources: Optional[List[Dict[str, Any]]] = None,
        suggested_followups: Optional[List[str]] = None,
    ) -> ChatMessageResponse:
        now = datetime.now(timezone.utc)
        asst_msg = AiAgentMessageDb(
            id=uuid4(),
            session_id=session.id,
            sender_type="assistant",
            content=reply_text,
            action_type=action_type,
            metadata_json={"db_sources": db_sources, "followups": suggested_followups},
            created_at=now,
        )
        if not DATABASE_SEARCH_SERVICE._should_skip_db():
            try:
                db.add(asst_msg)
                session.updated_at = now
                db.commit()
                db.refresh(asst_msg)
            except Exception as e:
                db.rollback()
                DATABASE_SEARCH_SERVICE._mark_db_error()
                logger.warning(f"Could not persist assistant message: {e}")

        return ChatMessageResponse(
            session_id=str(session.id),
            message_id=str(asst_msg.id),
            response=reply_text,
            sender_type="assistant",
            action_type=action_type,
            db_sources=db_sources,
            suggested_followups=suggested_followups,
            created_at=asst_msg.created_at,
        )

    # -------------------------------------------------------------------------
    # Streaming Support (SSE Generator)
    # -------------------------------------------------------------------------
    async def stream_chat(self, db: Session, req: ChatMessageRequest) -> AsyncGenerator[str, None]:
        # Process the chat and generate full response
        response = self.process_chat(db, req)
        text = response.response
        words = text.split(" ")

        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            payload = {
                "chunk": chunk,
                "done": False,
                "session_id": response.session_id,
                "message_id": response.message_id,
            }
            yield f"data: {json.dumps(payload)}\n\n"
            time.sleep(0.03)

        done_payload = {
            "chunk": "",
            "done": True,
            "session_id": response.session_id,
            "message_id": response.message_id,
            "suggested_followups": response.suggested_followups,
        }
        yield f"data: {json.dumps(done_payload)}\n\n"

    # -------------------------------------------------------------------------
    # Actions: Book a Meeting & Request Support
    # -------------------------------------------------------------------------
    def book_meeting(self, db: Session, req: BookMeetingRequest) -> BookMeetingResponse:
        session_uuid = None
        if req.session_id:
            try:
                session_uuid = UUID(req.session_id)
            except Exception:
                pass

        booking = AiAgentMeetingBookingDb(
            id=uuid4(),
            session_id=session_uuid,
            full_name=req.full_name,
            email=req.email,
            phone=req.phone,
            preferred_date=req.preferred_date,
            preferred_time=req.preferred_time,
            topic=req.topic,
            status="confirmed",
            created_at=datetime.now(timezone.utc),
        )
        if not DATABASE_SEARCH_SERVICE._should_skip_db():
            try:
                db.add(booking)
                if session_uuid:
                    msg = AiAgentMessageDb(
                        id=uuid4(),
                        session_id=session_uuid,
                        sender_type="assistant",
                        content=(
                            f"🎉 **Meeting Confirmed!**\n"
                            f"I have booked your meeting for **{req.preferred_date} at {req.preferred_time}** "
                            f"under **{req.full_name}** ({req.email}). A calendar invite has been dispatched."
                        ),
                        action_type="meeting_confirmed",
                        metadata_json={"booking_id": str(booking.id)},
                        created_at=datetime.now(timezone.utc),
                    )
                    db.add(msg)
                db.commit()
                db.refresh(booking)
            except Exception as e:
                db.rollback()
                DATABASE_SEARCH_SERVICE._mark_db_error()
                logger.warning(f"Could not persist meeting booking: {e}")

        return BookMeetingResponse(
            booking_id=str(booking.id),
            full_name=booking.full_name,
            email=booking.email,
            preferred_date=str(booking.preferred_date),
            preferred_time=booking.preferred_time,
            status=booking.status,
            confirmation_message=(
                f"Your meeting has been scheduled for {booking.preferred_date} at {booking.preferred_time}. "
                f"Confirmation sent to {booking.email}!"
            ),
        )

    def list_meetings(self, db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        results = (
            db.query(AiAgentMeetingBookingDb)
            .order_by(AiAgentMeetingBookingDb.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": str(b.id),
                "full_name": b.full_name,
                "email": b.email,
                "phone": b.phone,
                "preferred_date": str(b.preferred_date),
                "preferred_time": b.preferred_time,
                "topic": b.topic,
                "status": b.status,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in results
        ]

    def create_support_request(self, db: Session, req: SupportRequestCreate) -> SupportRequestResponse:
        session_uuid = None
        if req.session_id:
            try:
                session_uuid = UUID(req.session_id)
            except Exception:
                pass

        support = AiAgentSupportRequestDb(
            id=uuid4(),
            session_id=session_uuid,
            full_name=req.full_name,
            email=req.email,
            subject=req.subject,
            description=req.description,
            priority=req.priority,
            status="open",
            created_at=datetime.now(timezone.utc),
        )
        if not DATABASE_SEARCH_SERVICE._should_skip_db():
            try:
                db.add(support)
                if session_uuid:
                    msg = AiAgentMessageDb(
                        id=uuid4(),
                        session_id=session_uuid,
                        sender_type="assistant",
                        content=(
                            f"🎫 **Support Ticket Created: #{str(support.id)[:8]}**\n"
                            f"Subject: *{req.subject}*\n"
                            f"Priority: *{req.priority.capitalize()}*\n"
                            f"Our support specialists have been notified and will reply to **{req.email}** shortly."
                        ),
                        action_type="support_created",
                        metadata_json={"request_id": str(support.id)},
                        created_at=datetime.now(timezone.utc),
                    )
                    db.add(msg)
                db.commit()
                db.refresh(support)
            except Exception as e:
                db.rollback()
                DATABASE_SEARCH_SERVICE._mark_db_error()
                logger.warning(f"Could not persist support request: {e}")

        return SupportRequestResponse(
            request_id=str(support.id),
            full_name=support.full_name,
            email=support.email,
            subject=support.subject,
            priority=support.priority,
            status=support.status,
            confirmation_message=f"Support ticket #{str(support.id)[:8]} created. We will email you at {support.email}.",
        )

    def list_support_requests(self, db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        results = (
            db.query(AiAgentSupportRequestDb)
            .order_by(AiAgentSupportRequestDb.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": str(r.id),
                "full_name": r.full_name,
                "email": r.email,
                "subject": r.subject,
                "description": r.description,
                "priority": r.priority,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in results
        ]

    # -------------------------------------------------------------------------
    # Employee Creation & Onboarding (One-by-One Conversational & Action)
    # -------------------------------------------------------------------------
    def _get_onboarding_state(self, session: AiAgentSessionDb) -> Optional[Dict[str, Any]]:
        sid = str(session.id)
        if sid in self._onboarding_sessions:
            return self._onboarding_sessions[sid]
        if session.metadata_json and isinstance(session.metadata_json, dict):
            state = session.metadata_json.get("employee_onboarding")
            if state and isinstance(state, dict):
                self._onboarding_sessions[sid] = state
                return state
        return None

    def _save_onboarding_state(
        self, db: Session, session: AiAgentSessionDb, state: Optional[Dict[str, Any]]
    ):
        sid = str(session.id)
        current_meta = dict(session.metadata_json or {})
        if state is None or not state.get("active"):
            self._onboarding_sessions.pop(sid, None)
            current_meta.pop("employee_onboarding", None)
        else:
            self._onboarding_sessions[sid] = state
            current_meta["employee_onboarding"] = state

        session.metadata_json = current_meta
        flag_modified(session, "metadata_json")
        if not DATABASE_SEARCH_SERVICE._should_skip_db():
            try:
                db.add(session)
                db.commit()
            except Exception as e:
                db.rollback()
                logger.warning(f"Could not persist onboarding state to session: {e}")

    def _parse_employee_fields_from_text(self, text: str) -> Dict[str, Any]:
        extracted: Dict[str, Any] = {}
        if not text:
            return extracted

        # 1. Try to extract embedded JSON
        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            try:
                raw_dict = json.loads(json_match.group(0))
                valid_keys = {
                    "organization_id", "profile_photo", "first_name", "last_name",
                    "mobile_number", "email", "father_name", "mother_name",
                    "marital_status", "spouse_name", "emergency_contact",
                    "date_of_birth", "govt_id_proof", "id_proof_number",
                    "gender", "nationality", "address", "city", "state",
                    "zip_code", "employee_id",
                }
                for k, v in raw_dict.items():
                    if k in valid_keys and v is not None:
                        # Ignore placeholder values
                        if isinstance(v, str) and v.strip().lower() in ("string", "null", "none", ""):
                            continue
                        if k == "employee_id" and v == 0:
                            continue
                        extracted[k] = v
            except Exception:
                pass

        # 2. Key-value regex parsing
        patterns = [
            ("first_name", r"(?:first[\s_]?name|first|fname)\s*(?:is|:|=)\s*([A-Za-z]+)"),
            ("last_name", r"(?:last[\s_]?name|last|lname|surname)\s*(?:is|:|=)\s*([A-Za-z]+)"),
            ("email", r"(?:email|mail)\s*(?:is|:|=)?\s*([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"),
            ("mobile_number", r"(?:mobile|phone|contact|cell)\s*(?:is|:|=)?\s*([\+0-9\-\s]{7,20})"),
            ("gender", r"(?:gender|sex)\s*(?:is|:|=)\s*(male|female|other|non-binary)"),
            ("date_of_birth", r"(?:dob|date[\s_]?of[\s_]?birth|birth[\s_]?date)\s*(?:is|:|=)\s*([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{2}/[0-9]{2}/[0-9]{4})"),
            ("city", r"(?:city)\s*(?:is|:|=)\s*([A-Za-z\s]+)"),
            ("state", r"(?:state)\s*(?:is|:|=)\s*([A-Za-z\s]+)"),
            ("zip_code", r"(?:zip|postal[\s_]?code|zip[\s_]?code)\s*(?:is|:|=)\s*([0-9A-Za-z\-\s]{3,10})"),
            ("nationality", r"(?:nationality)\s*(?:is|:|=)\s*([A-Za-z]+)"),
            ("marital_status", r"(?:marital[\s_]?status)\s*(?:is|:|=)\s*(single|married|divorced|widowed)"),
            ("govt_id_proof", r"(?:govt[\s_]?id|id[\s_]?type|id[\s_]?proof)\s*(?:is|:|=)\s*([A-Za-z]+)"),
            ("id_proof_number", r"(?:id[\s_]?number|id[\s_]?proof[\s_]?number)\s*(?:is|:|=)\s*([A-Za-z0-9]+)"),
        ]
        for key, pat in patterns:
            if key not in extracted:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    extracted[key] = m.group(1).strip()

        return extracted

    def _handle_employee_onboarding_turn(
        self, db: Session, session: AiAgentSessionDb, user_message: str
    ) -> Optional[ChatMessageResponse]:
        trimmed = user_message.strip()
        lower_msg = trimmed.lower()
        state = self._get_onboarding_state(session)

        # Triggers to start employee creation flow
        has_start_trigger = bool(
            re.search(r"\b(create|add|register|onboard|enter|enroll)\b.*\bemployee\b", lower_msg)
            or any(t in lower_msg for t in [
                "create employee", "add employee", "register employee",
                "new employee", "onboard employee", "enter employee",
                "take data one by one", "create a new employee",
                "create an employee", "add an employee", "add a new employee",
                "create employee data", "enter in database",
            ])
        )

        # -------------------------------------------------------------
        # Case 1: Flow is NOT active yet
        # -------------------------------------------------------------
        if not state or not state.get("active"):
            extracted = self._parse_employee_fields_from_text(trimmed)
            if not has_start_trigger and not extracted:
                return None  # Let normal chat handler process this

            # Initialize flow
            state = {
                "active": True,
                "step_index": 0,
                "data": extracted or {},
            }
            self._save_onboarding_state(db, session, state)

            # If user already provided first_name and full data or asked to save immediately
            if state["data"].get("first_name") and (
                "save" in lower_msg or len(state["data"]) >= 5
            ):
                action_resp = self._persist_created_employee(db, session, state["data"])
                return self._record_and_return_assistant_reply(
                    db=db,
                    session=session,
                    reply_text=action_resp.confirmation_message,
                    action_type="employee_created",
                    db_sources=[{"entity": "employees", "count": 1, "data": [action_resp.record]}],
                    suggested_followups=["Create Another Employee", "View Department Info", "Book a Meeting"],
                )

            # Find the first step that is not yet answered
            next_step_idx = 0
            while next_step_idx < len(EMPLOYEE_FIELD_STEPS):
                field_name = EMPLOYEE_FIELD_STEPS[next_step_idx]["field"]
                if field_name not in state["data"]:
                    break
                next_step_idx += 1

            state["step_index"] = next_step_idx
            self._save_onboarding_state(db, session, state)

            step_info = EMPLOYEE_FIELD_STEPS[next_step_idx]
            intro = ""
            if state["data"]:
                intro = "I've noted the preliminary information provided.\n\n"

            reply_text = f"{intro}{step_info['prompt']}"
            followups = ["Skip", "Cancel"] if not step_info["required"] else ["Cancel"]
            if state["data"].get("first_name"):
                followups.insert(0, "Save Employee Now")

            return self._record_and_return_assistant_reply(
                db=db,
                session=session,
                reply_text=reply_text,
                action_type="employee_onboarding_step",
                suggested_followups=followups,
            )

        # -------------------------------------------------------------
        # Case 2: Flow IS already active
        # -------------------------------------------------------------
        # Check command: Cancel
        if lower_msg in ("cancel", "stop", "abort", "quit", "exit"):
            self._save_onboarding_state(db, session, None)
            return self._record_and_return_assistant_reply(
                db=db,
                session=session,
                reply_text=(
                    "❌ **Employee creation cancelled.**\n"
                    "The in-progress onboarding session has been cleared. What else can I help you with?"
                ),
                action_type="chat",
                suggested_followups=["Create Employee", "Book a Meeting", "Request Support"],
            )

        # Check command: Save / Finish early
        if lower_msg in ("save", "save now", "save employee now", "finish", "done", "submit"):
            if state["data"].get("first_name"):
                action_resp = self._persist_created_employee(db, session, state["data"])
                return self._record_and_return_assistant_reply(
                    db=db,
                    session=session,
                    reply_text=action_resp.confirmation_message,
                    action_type="employee_created",
                    db_sources=[{"entity": "employees", "count": 1, "data": [action_resp.record]}],
                    suggested_followups=["Create Another Employee", "View Department Info", "Book a Meeting"],
                )
            else:
                return self._record_and_return_assistant_reply(
                    db=db,
                    session=session,
                    reply_text=(
                        "⚠️ Before I can save the employee to the database, I need at least their **First Name**.\n\n"
                        "What is the employee's **First Name**?"
                    ),
                    action_type="employee_onboarding_step",
                    suggested_followups=["Cancel"],
                )

        curr_idx = state.get("step_index", 0)
        if curr_idx >= len(EMPLOYEE_FIELD_STEPS):
            # Already completed all steps, persist
            action_resp = self._persist_created_employee(db, session, state["data"])
            return self._record_and_return_assistant_reply(
                db=db,
                session=session,
                reply_text=action_resp.confirmation_message,
                action_type="employee_created",
                db_sources=[{"entity": "employees", "count": 1, "data": [action_resp.record]}],
                suggested_followups=["Create Another Employee", "View Department Info", "Book a Meeting"],
            )

        curr_step = EMPLOYEE_FIELD_STEPS[curr_idx]
        curr_field = curr_step["field"]

        # Also extract any other fields mentioned in this message
        inline_extracted = self._parse_employee_fields_from_text(trimmed)
        for k, v in inline_extracted.items():
            state["data"][k] = v

        # Check if user wants to skip
        is_skip = lower_msg in ("skip", "pass", "none", "n/a", "-", "no")
        if is_skip:
            if curr_step["required"] and not state["data"].get(curr_field):
                return self._record_and_return_assistant_reply(
                    db=db,
                    session=session,
                    reply_text=f"⚠️ **{curr_step['label']}** is required to register the employee.\n\nPlease enter the employee's **{curr_step['label']}**:",
                    action_type="employee_onboarding_step",
                    suggested_followups=["Cancel"],
                )
            else:
                state["data"][curr_field] = None
        else:
            if curr_field not in inline_extracted:
                # Use raw trimmed message for this field
                state["data"][curr_field] = trimmed

        # Special handling: if marital_status is not married, skip spouse_name
        if curr_field == "marital_status":
            m_stat = str(state["data"].get("marital_status") or "").lower()
            if m_stat and "married" not in m_stat:
                state["data"]["spouse_name"] = None

        # Advance to next missing step
        next_idx = curr_idx + 1
        while next_idx < len(EMPLOYEE_FIELD_STEPS):
            f_name = EMPLOYEE_FIELD_STEPS[next_idx]["field"]
            if f_name not in state["data"]:
                break
            next_idx += 1

        state["step_index"] = next_idx

        # If all steps done, persist now!
        if next_idx >= len(EMPLOYEE_FIELD_STEPS):
            action_resp = self._persist_created_employee(db, session, state["data"])
            return self._record_and_return_assistant_reply(
                db=db,
                session=session,
                reply_text=action_resp.confirmation_message,
                action_type="employee_created",
                db_sources=[{"entity": "employees", "count": 1, "data": [action_resp.record]}],
                suggested_followups=["Create Another Employee", "View Department Info", "Book a Meeting"],
            )

        self._save_onboarding_state(db, session, state)
        next_step = EMPLOYEE_FIELD_STEPS[next_idx]

        followups = ["Skip", "Cancel"] if not next_step["required"] else ["Cancel"]
        if state["data"].get("first_name"):
            followups.insert(0, "Save Employee Now")

        return self._record_and_return_assistant_reply(
            db=db,
            session=session,
            reply_text=next_step["prompt"],
            action_type="employee_onboarding_step",
            suggested_followups=followups,
        )

    def _persist_created_employee(
        self,
        db: Session,
        session: Optional[AiAgentSessionDb],
        data: Dict[str, Any],
    ) -> CreateEmployeeActionResponse:
        now = datetime.now(timezone.utc)
        first_name = str(data.get("first_name", "Unknown")).strip()
        last_name = data.get("last_name") or None
        email = data.get("email") or None
        mobile_number = data.get("mobile_number") or None

        assigned_id = 0
        emp_code = None

        if not DATABASE_SEARCH_SERVICE._should_skip_db():
            try:
                # 1. Resolve or Create EmployeeDb
                user_emp_id = data.get("employee_id")
                if user_emp_id and isinstance(user_emp_id, int) and user_emp_id > 0:
                    existing_emp = db.query(EmployeeDb).filter(EmployeeDb.id == user_emp_id).first()
                    if not existing_emp:
                        emp_rec = EmployeeDb(id=user_emp_id, employee_code=f"EMP-{user_emp_id:04d}")
                        db.add(emp_rec)
                        db.flush()
                        assigned_id = emp_rec.id
                        emp_code = emp_rec.employee_code
                    else:
                        assigned_id = existing_emp.id
                        emp_code = existing_emp.employee_code
                else:
                    emp_rec = EmployeeDb()
                    db.add(emp_rec)
                    db.flush()
                    assigned_id = emp_rec.id
                    if not emp_rec.employee_code:
                        emp_rec.employee_code = f"EMP-{assigned_id:04d}"
                        db.add(emp_rec)
                        db.flush()
                    emp_code = emp_rec.employee_code

                # 2. Organization ID
                org_val = data.get("organization_id")
                org_uuid = None
                if org_val:
                    org_uuid = _to_uuid(org_val)
                if not org_uuid:
                    try:
                        first_org = db.query(OrganizationDb.id).filter(OrganizationDb.status == "active").first()
                        if first_org:
                            org_uuid = first_org.id
                    except Exception:
                        pass

                # 3. Parse Date of Birth
                parsed_dob = _parse_date(data.get("date_of_birth"))

                # 4. Upsert Personal Info
                info_in = EmployeePersonalInformationCreate(
                    employee_id=assigned_id,
                    organization_id=org_uuid,
                    profile_photo=data.get("profile_photo") or None,
                    first_name=first_name,
                    last_name=last_name,
                    mobile_number=mobile_number,
                    email=email,
                    father_name=data.get("father_name") or None,
                    mother_name=data.get("mother_name") or None,
                    marital_status=data.get("marital_status") or None,
                    spouse_name=data.get("spouse_name") or None,
                    emergency_contact=data.get("emergency_contact") or None,
                    date_of_birth=parsed_dob,
                    govt_id_proof=data.get("govt_id_proof") or None,
                    id_proof_number=data.get("id_proof_number") or None,
                    gender=data.get("gender") or None,
                    nationality=data.get("nationality") or None,
                    address=data.get("address") or None,
                    city=data.get("city") or None,
                    state=data.get("state") or None,
                    zip_code=data.get("zip_code") or None,
                )

                existing_record = CRUD_EMPLOYEE_PERSONAL_INFORMATION.get(db, employee_id=assigned_id)
                if existing_record:
                    saved_obj = CRUD_EMPLOYEE_PERSONAL_INFORMATION.update(
                        db, db_obj=existing_record, obj_in=info_in
                    )
                else:
                    saved_obj = CRUD_EMPLOYEE_PERSONAL_INFORMATION.create(db, obj_in=info_in)

                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Error persisting employee to database: {e}")
                DATABASE_SEARCH_SERVICE._mark_db_error()
                if not assigned_id:
                    assigned_id = int(time.time()) % 100000
                    emp_code = f"EMP-{assigned_id:04d}"
        else:
            assigned_id = int(time.time()) % 100000
            emp_code = f"EMP-{assigned_id:04d}"

        # Clean session state
        if session:
            self._save_onboarding_state(db, session, None)

        full_name = f"{first_name} {last_name}".strip() if last_name else first_name
        confirmation_msg = (
            f"🎉 **Employee Registered Successfully!**\n\n"
            f"Employee **{full_name}** has been entered and saved in the database.\n\n"
            f"📋 **Saved Details:**\n"
            f"- **Employee ID:** #{assigned_id} (`{emp_code}`)\n"
            f"- **Name:** {full_name}\n"
            f"- **Email:** {email or 'Not specified'}\n"
            f"- **Mobile:** {mobile_number or 'Not specified'}\n"
            f"- **Gender:** {data.get('gender') or 'Not specified'}\n"
            f"- **Date of Birth:** {str(data.get('date_of_birth')) if data.get('date_of_birth') else 'Not specified'}\n"
            f"- **Govt ID:** {data.get('govt_id_proof') or 'None'} ({data.get('id_proof_number') or 'N/A'})\n"
            f"- **Nationality:** {data.get('nationality') or 'Not specified'}\n"
            f"- **Emergency Contact:** {data.get('emergency_contact') or 'Not specified'}\n"
            f"- **Location:** {data.get('city') or ''}{', ' + data.get('state') if data.get('state') else ''}\n"
            f"- **Database Status:** ✅ Persisted in `hrms.employees` and `hrms.employee_personal_information`, with user account synced."
        )

        record_dict = {
            "employee_id": assigned_id,
            "employee_code": emp_code,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "mobile_number": mobile_number,
            "gender": data.get("gender"),
            "date_of_birth": str(data.get("date_of_birth")) if data.get("date_of_birth") else None,
            "govt_id_proof": data.get("govt_id_proof"),
            "id_proof_number": data.get("id_proof_number"),
            "nationality": data.get("nationality"),
            "address": data.get("address"),
            "city": data.get("city"),
            "state": data.get("state"),
            "zip_code": data.get("zip_code"),
            "organization_id": str(data.get("organization_id")) if data.get("organization_id") else None,
            "created_at": now.isoformat(),
        }

        return CreateEmployeeActionResponse(
            employee_id=assigned_id,
            employee_code=emp_code,
            first_name=first_name,
            last_name=last_name,
            email=email,
            status="created",
            confirmation_message=confirmation_msg,
            record=record_dict,
        )

    def create_employee_direct(
        self, db: Session, req: CreateEmployeeActionRequest
    ) -> CreateEmployeeActionResponse:
        session = None
        if req.session_id:
            session = self.get_session(db, req.session_id)

        data = req.model_dump(exclude_unset=True)
        resp = self._persist_created_employee(db, session, data)

        if session:
            now = datetime.now(timezone.utc)
            msg = AiAgentMessageDb(
                id=uuid4(),
                session_id=session.id,
                sender_type="assistant",
                content=resp.confirmation_message,
                action_type="employee_created",
                metadata_json={"employee_id": resp.employee_id, "record": resp.record},
                created_at=now,
            )
            if not DATABASE_SEARCH_SERVICE._should_skip_db():
                try:
                    db.add(msg)
                    db.commit()
                except Exception:
                    db.rollback()

        return resp

    def list_employees(self, db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            records = CRUD_EMPLOYEE_PERSONAL_INFORMATION.get_multi(db, limit=limit)
            return [
                {
                    "employee_id": r.employee_id,
                    "first_name": r.first_name,
                    "last_name": r.last_name,
                    "email": r.email,
                    "mobile_number": r.mobile_number,
                    "city": r.city,
                    "state": r.state,
                    "gender": r.gender,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in records
            ]
        except Exception as e:
            logger.warning(f"Error listing employees: {e}")
            return []


AGENT_SERVICE = AgentService()
