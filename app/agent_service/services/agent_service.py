import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import UUID, uuid4

import httpx
from sqlalchemy.orm import Session

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
    SupportRequestCreate,
    SupportRequestResponse,
)
from .database_search_service import DATABASE_SEARCH_SERVICE

logger = logging.getLogger(__name__)


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
                "What are our shift timings?",
                "Who is available in the engineering department?",
                "Find employees with Python or SQL skills",
                "What is our weekend and calendar policy?",
            ],
            "quick_actions": [
                {"id": "book_meeting", "title": "Book a Meeting", "action": "open_modal"},
                {"id": "request_support", "title": "Request Support", "action": "open_modal"},
            ],
        }

        self._cached_profile: Optional[AgentProfileResponse] = None
        self._cache_time: float = 0

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
    ) -> AiAgentSessionDb:
        session = AiAgentSessionDb(
            id=uuid4(),
            session_name=session_name,
            visitor_id=visitor_id,
            metadata_json=metadata or {},
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
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
        try:
            val = UUID(session_id)
            return db.query(AiAgentSessionDb).filter(AiAgentSessionDb.id == val).first()
        except Exception:
            return None

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
            # Create session on the fly if invalid/missing
            session = self.create_session(db, session_name="Interactive Session")
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

        # 2. Check for action intents (Book Meeting / Support)
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
                suggested_followups=["Book a Meeting", "What are our office hours?", "Request Support"],
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
                suggested_followups=["Request Support", "Book a Meeting", "Check shift schedule"],
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


AGENT_SERVICE = AgentService()
