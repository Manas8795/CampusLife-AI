import json
import datetime
from sqlalchemy.orm import Session
from backend.app.voice.models import Conversation, ConversationMessage, VoiceCall
from backend.app.voice.schemas import (
    VoiceMessageCreate, VoiceMessageResponse, CallInitiateRequest,
    ChatHistoryOut, ChatMessageOut
)
from backend.app.voice.agent import VoiceAgent
from backend.app.voice.policy import CallingPolicyEngine
from backend.app.voice.telephony.provider import SimulatedTelephonyProvider, TwilioProvider
from backend.app.core.models import Profile

class VoiceService:
    @staticmethod
    def get_active_conversation_history(db: Session, user_id: int) -> ChatHistoryOut:
        """Retrieves or initializes the active conversation with all stored messages in chronological order."""
        now = datetime.datetime.utcnow()
        conv = db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.status == "ACTIVE"
        ).order_by(Conversation.last_activity.desc()).first()

        if not conv:
            conv = Conversation(
                user_id=user_id,
                session_type="IN_APP_VOICE",
                status="ACTIVE",
                context_data="{}",
                started_at=now,
                last_activity=now
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)

        msgs = db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conv.id
        ).order_by(ConversationMessage.created_at.asc()).all()

        return ChatHistoryOut(
            conversation_id=conv.id,
            session_type=conv.session_type,
            started_at=conv.started_at,
            last_activity=conv.last_activity,
            messages=msgs
        )

    @staticmethod
    def clear_conversation_history(db: Session, user_id: int) -> bool:
        """Clears all conversation messages in the active conversation."""
        conv = db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.status == "ACTIVE"
        ).order_by(Conversation.last_activity.desc()).first()

        if conv:
            db.query(ConversationMessage).filter(
                ConversationMessage.conversation_id == conv.id
            ).delete()
            conv.context_data = "{}"
            conv.last_activity = datetime.datetime.now()
            db.commit()
        return True

    @staticmethod
    def handle_voice_message(db: Session, user_id: int, req: VoiceMessageCreate) -> VoiceMessageResponse:
        now = datetime.datetime.now()

        # 1. Fetch or create conversation
        if req.conversation_id:
            conv = db.query(Conversation).filter(
                Conversation.id == req.conversation_id,
                Conversation.user_id == user_id
            ).first()
        else:
            conv = db.query(Conversation).filter(
                Conversation.user_id == user_id,
                Conversation.status == "ACTIVE"
            ).order_by(Conversation.last_activity.desc()).first()

        if not conv:
            conv = Conversation(
                user_id=user_id,
                session_type="IN_APP_VOICE",
                status="ACTIVE",
                context_data="{}",
                started_at=now,
                last_activity=now
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)

        # 2. Store user message
        user_msg = ConversationMessage(
            conversation_id=conv.id,
            role="USER",
            content=req.message,
            created_at=now
        )
        db.add(user_msg)

        # 3. Process turn through Voice Agent & Local Student LLM
        context = json.loads(conv.context_data or "{}")
        if req.persona:
            context["persona"] = req.persona
        agent_res = VoiceAgent.process_turn(user_id, req.message, context)

        # 4. Store assistant message
        asst_msg = ConversationMessage(
            conversation_id=conv.id,
            role="ASSISTANT",
            content=agent_res["reply"],
            tool_name=agent_res["tool_executed"],
            tool_result=json.dumps(agent_res["tool_data"]) if agent_res["tool_data"] else None,
            created_at=datetime.datetime.now()
        )
        db.add(asst_msg)

        # 5. Update conversation context
        context["last_intent"] = agent_res["intent"]
        context["last_tool"] = agent_res["tool_executed"]
        if agent_res["requires_confirmation"]:
            context["pending_action"] = agent_res["confirmation_action"]
        else:
            context.pop("pending_action", None)

        conv.context_data = json.dumps(context)
        conv.last_activity = datetime.datetime.now()
        db.commit()

        return VoiceMessageResponse(
            conversation_id=conv.id,
            user_query=req.message,
            assistant_reply=agent_res["reply"],
            intent_detected=agent_res["intent"],
            tool_executed=agent_res["tool_executed"],
            tool_data=agent_res["tool_data"],
            requires_confirmation=agent_res["requires_confirmation"],
            confirmation_action=agent_res["confirmation_action"],
            engine=agent_res.get("engine", "Local Student Domain LLM"),
            persona=agent_res.get("persona", "EMPATHETIC_MENTOR"),
            latency_ms=agent_res.get("latency_ms", 0.0)
        )

    @staticmethod
    def initiate_call(db: Session, user_id: int, req: CallInitiateRequest) -> VoiceCall:
        # Determine phone number
        phone = req.phone_number
        if not phone:
            profile = db.query(Profile).filter(Profile.user_id == user_id).first()
            phone = profile.phone_number if profile and profile.phone_number else "+919876543210"

        # Construct proactive or reminder greeting
        greeting = (
            f"Hello, this is CampusLife AI calling with your proactive update regarding: {req.trigger_reason}. "
            "How can I assist you with your academic schedule today?"
        )

        # Telephony provider selection
        prov_upper = (req.provider or "BOLNA").upper()
        if "BOLNA" in prov_upper:
            from backend.app.voice.telephony.bolna_provider import bolna_provider
            provider_inst = bolna_provider
            prov_name = "BOLNA_AI"
        elif "TWILIO" in prov_upper:
            provider_inst = TwilioProvider()
            prov_name = "TWILIO"
        else:
            provider_inst = SimulatedTelephonyProvider()
            prov_name = "SIMULATED"

        telephony_res = provider_inst.initiate_call(phone, greeting)

        call = VoiceCall(
            user_id=user_id,
            phone_number=phone,
            direction="OUTBOUND",
            call_type=req.call_type or "PROACTIVE_INTERVENTION",
            trigger_reason=req.trigger_reason or "Proactive student co-pilot alert",
            status="INITIATED",
            provider=prov_name,
            provider_call_sid=telephony_res.get("call_sid"),
            started_at=datetime.datetime.now(),
            transcript=json.dumps([{"role": "ASSISTANT", "content": greeting}]),
            outcome="CALL_INITIATED"
        )
        db.add(call)
        db.commit()
        db.refresh(call)
        return call

    @staticmethod
    def check_and_trigger_proactive_intervention(db: Session, user_id: int, ignore_quiet_hours: bool = False) -> dict:
        """
        Scans Module 6 student intelligence and executes calling policy.
        If eligible, automatically dials an outbound AI intervention call!
        """
        eval_result = CallingPolicyEngine.evaluate_outbound_eligibility(db, user_id, ignore_quiet_hours=ignore_quiet_hours)

        if not eval_result["should_call"]:
            return {
                "should_call": False,
                "eligible_reasons": eval_result["eligible_reasons"],
                "blocked_reasons": eval_result["blocked_reasons"],
                "call_initiated": False,
                "call_id": None,
                "greeting_script": None
            }

        state = eval_result["student_state"]
        trigger_reason = state.proactive_intervention_reason or "Compound workload & wellness overload"

        call = VoiceService.initiate_call(db, user_id, CallInitiateRequest(
            call_type="PROACTIVE_INTERVENTION",
            trigger_reason=trigger_reason,
            provider="BOLNA"
        ))

        greeting = (
            f"Hello! This is CampusLife AI. We detected an important situation: {trigger_reason}. "
            "I'm calling to see if you would like me to adjust your study tasks or help you plan tonight's schedule."
        )

        return {
            "should_call": True,
            "eligible_reasons": eval_result["eligible_reasons"],
            "blocked_reasons": [],
            "call_initiated": True,
            "call_id": call.id,
            "greeting_script": greeting
        }

    @staticmethod
    def process_call_speech(db: Session, call_id: int, user_speech: str) -> dict:
        """
        Handles interactive conversational turns during an active voice phone call.
        """
        call = db.query(VoiceCall).filter(VoiceCall.id == call_id).first()
        if not call:
            raise ValueError("Call not found")

        transcript_list = json.loads(call.transcript or "[]")
        transcript_list.append({"role": "USER", "content": user_speech})

        # Process through VoiceAgent
        agent_res = VoiceAgent.process_turn(call.user_id, user_speech)
        transcript_list.append({"role": "ASSISTANT", "content": agent_res["reply"]})

        call.status = "IN_PROGRESS"
        call.transcript = json.dumps(transcript_list)
        call.outcome = "INTERACTION_IN_PROGRESS"
        db.commit()

        return {
            "call_id": call.id,
            "status": call.status,
            "assistant_reply": agent_res["reply"],
            "tool_executed": agent_res["tool_executed"]
        }

    @staticmethod
    def end_call(db: Session, call_id: int, outcome: str = "COMPLETED_SUCCESSFULLY") -> VoiceCall:
        call = db.query(VoiceCall).filter(VoiceCall.id == call_id).first()
        if not call:
            raise ValueError("Call not found")

        call.status = "COMPLETED"
        call.ended_at = datetime.datetime.now()
        if call.started_at:
            call.duration_seconds = max(5, int((call.ended_at - call.started_at).total_seconds()))
        call.outcome = outcome
        db.commit()
        db.refresh(call)
        return call

    @staticmethod
    def get_call_history(db: Session, user_id: int, limit: int = 15) -> list[VoiceCall]:
        return db.query(VoiceCall).filter(
            VoiceCall.user_id == user_id
        ).order_by(VoiceCall.created_at.desc()).limit(limit).all()
