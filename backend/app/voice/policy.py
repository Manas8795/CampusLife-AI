import datetime
from sqlalchemy.orm import Session
from backend.app.core.models import UserPreference
from backend.app.intelligence.service import IntelligenceService
from backend.app.voice.models import VoiceCall

class CallingPolicyEngine:
    @staticmethod
    def is_within_quiet_hours(prefs: UserPreference, current_time: datetime.time = None) -> bool:
        if not current_time:
            current_time = datetime.datetime.now().time()

        try:
            start_h, start_m = map(int, prefs.quiet_hours_start.split(":"))
            end_h, end_m = map(int, prefs.quiet_hours_end.split(":"))
            start_time = datetime.time(start_h, start_m)
            end_time = datetime.time(end_h, end_m)

            if start_time < end_time:
                return start_time <= current_time <= end_time
            else:
                # Overnights, e.g. 23:00 to 07:30
                return current_time >= start_time or current_time <= end_time
        except Exception:
            return False

    @staticmethod
    def evaluate_outbound_eligibility(db: Session, user_id: int, ignore_quiet_hours: bool = False) -> dict:
        """
        Evaluates whether an outbound AI call should be placed to the student.
        Returns a decision dictionary with reasons.
        """
        eligible_reasons = []
        blocked_reasons = []

        # 1. Fetch user preferences
        prefs = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        if not prefs or not prefs.voice_calls_enabled:
            blocked_reasons.append("USER_DISABLED_VOICE_CALLS")
        elif prefs.calling_consent_status != "OPTED_IN":
            blocked_reasons.append("USER_NOT_OPTED_IN_FOR_CALLS")

        # 2. Quiet Hours check
        if not ignore_quiet_hours and prefs and CallingPolicyEngine.is_within_quiet_hours(prefs):
            blocked_reasons.append(f"CURRENT_TIME_IN_QUIET_HOURS ({prefs.quiet_hours_start}-{prefs.quiet_hours_end})")

        # 3. Frequency capping (last call within 4 hours, bypassed during test override)
        if not ignore_quiet_hours:
            four_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=4)
            recent_call = db.query(VoiceCall).filter(
                VoiceCall.user_id == user_id,
                VoiceCall.status.in_(["INITIATED", "CONNECTED", "IN_PROGRESS", "COMPLETED"]),
                VoiceCall.created_at >= four_hours_ago
            ).first()
            if recent_call:
                blocked_reasons.append("CALL_COOLDOWN_ACTIVE_RECENT_CALL_EXISTS")

        # 4. Intelligence State check
        state = IntelligenceService.evaluate_student_state(db, user_id)
        if state.compound_risk_level in ["HIGH", "CRITICAL"] and state.proactive_intervention_recommended:
            eligible_reasons.append(state.proactive_intervention_reason or "High compound academic and wellness risk detected")
        else:
            blocked_reasons.append("NO_CRITICAL_COMPOUND_RISK_DETECTED")

        should_call = len(blocked_reasons) == 0 and len(eligible_reasons) > 0

        return {
            "should_call": should_call,
            "eligible_reasons": eligible_reasons,
            "blocked_reasons": blocked_reasons,
            "student_state": state
        }
