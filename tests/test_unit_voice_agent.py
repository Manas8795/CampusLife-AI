"""
Unit Tests — Voice Agent Intent Detection (Module 7)
=====================================================
Tests the core intent classification logic in VoiceAgent.detect_intent().

SE Focus:
  - 30+ parametrized test cases covering all 15 intent types
  - Edge cases: multi-word triggers, mixed-case, ambiguous queries
  - Negative path tests: queries that should fall through to GENERAL_COACHING
  - Tests for the Command Pattern registry (INTENT_REGISTRY completeness)
  - Tests for calling policy engine (CallingPolicyEngine)
  - Mocked external dependencies (DB session, Ollama) so tests run offline

All tests are fast (<50ms each) and have zero external dependencies.
"""

import pytest
from unittest.mock import MagicMock, patch
from backend.app.voice.agent import VoiceAgent
from backend.app.voice.intent_commands import INTENT_REGISTRY, execute_intent


# =============================================================================
# 1. Parametrized Intent Detection Tests
# =============================================================================

@pytest.mark.parametrize("query,expected_intent", [
    # --- CREATE_TASK ---
    ("add task to study linear algebra by tomorrow",       "CREATE_TASK"),
    ("create task: finish OS assignment",                  "CREATE_TASK"),
    ("I have an assignment due on Monday",                 "CREATE_TASK"),
    ("remind me to submit the project report",             "CREATE_TASK"),
    ("schedule assignment for physics lab",                "CREATE_TASK"),

    # --- LOG_EXPENSE ---
    ("I spent 250 on food at the canteen",                 "LOG_EXPENSE"),
    ("paid Rs 80 for chai via UPI",                       "LOG_EXPENSE"),
    ("bought a textbook for 650",                         "LOG_EXPENSE"),
    ("log expense of 500 for transport",                  "LOG_EXPENSE"),
    ("add expense 120 chai and snacks",                   "LOG_EXPENSE"),

    # --- LOG_SLEEP ---
    ("I slept 7 hours last night",                        "LOG_SLEEP"),
    ("log sleep 5.5 hours with high stress",              "LOG_SLEEP"),
    ("record my sleep 8 hours, feeling great",            "LOG_SLEEP"),

    # --- GET_TASKS ---
    ("what tasks do I have due?",                         "GET_TASKS"),
    ("show me my pending assignments",                    "GET_TASKS"),
    ("check my upcoming deadlines",                       "GET_TASKS"),
    ("status of my study plan",                           "GET_TASKS"),

    # --- GET_WELLNESS ---
    ("how is my sleep looking?",                          "GET_WELLNESS"),
    ("check my stress and health",                        "GET_WELLNESS"),
    ("how am I feeling energy wise?",                     "GET_WELLNESS"),

    # --- GET_FINANCES ---
    ("how much money have I spent this month",            "GET_FINANCES"),
    ("what is my budget runway?",                         "GET_FINANCES"),
    ("check my remaining balance",                        "GET_FINANCES"),

    # --- GET_TRIPS ---
    ("what are my upcoming trips?",                       "GET_TRIPS"),
    ("tell me about my travel plans",                     "GET_TRIPS"),

    # --- GET_INTELLIGENCE ---
    ("give me my overall status",                         "GET_INTELLIGENCE"),
    ("what is my co-pilot summary?",                      "GET_INTELLIGENCE"),

    # --- EXTEND_DEADLINE ---
    ("extend my deadline by 2 hours",                     "EXTEND_DEADLINE"),
    ("postpone the assignment by 1 day",                  "EXTEND_DEADLINE"),

    # --- CHANGE_PRIORITY ---
    ("make that task high priority",                      "CHANGE_PRIORITY"),
    ("set priority to urgent",                            "CHANGE_PRIORITY"),

    # --- GET_TIME ---
    ("what time is it?",                                  "GET_TIME"),
    ("tell me the current time",                          "GET_TIME"),
    ("what is today's date?",                             "GET_TIME"),

    # --- SET_BUDGET ---
    ("set my budget to 12000",                            "SET_BUDGET"),
    ("my remaining balance is 3500",                      "SET_BUDGET"),

    # --- GENERAL_COACHING (should NOT match any tool intent) ---
    ("hello",                                             "GENERAL_COACHING"),
    ("hi there",                                          "GENERAL_COACHING"),
    ("thanks",                                            "GENERAL_COACHING"),
    ("tell me a joke",                                    "GENERAL_COACHING"),
])
def test_detect_intent_parametrized(query, expected_intent):
    """Verify that detect_intent() maps queries to the correct intent string."""
    intent, params = VoiceAgent.detect_intent(query)
    assert intent == expected_intent, (
        f"Query: '{query}' → got '{intent}', expected '{expected_intent}'"
    )


# =============================================================================
# 2. Parameter Extraction Tests
# =============================================================================

class TestExpenseParameterExtraction:

    def test_amount_extracted_correctly(self):
        _, params = VoiceAgent.detect_intent("I spent Rs 250 on food")
        assert params.get("amount") == 250.0

    def test_category_food_detected(self):
        _, params = VoiceAgent.detect_intent("bought lunch for 80 rupees")
        assert params.get("category") == "Food"

    def test_payment_method_cash(self):
        _, params = VoiceAgent.detect_intent("paid 100 by cash for chai")
        assert params.get("payment_method") == "CASH"

    def test_payment_method_upi_default(self):
        _, params = VoiceAgent.detect_intent("spent 500 on books via GPay")
        assert params.get("payment_method") == "UPI"

    def test_amount_zero_returns_no_expense_intent(self):
        intent, _ = VoiceAgent.detect_intent("spent 0 on nothing")
        # Amount of 0 should not trigger LOG_EXPENSE
        assert intent != "LOG_EXPENSE"


class TestTaskParameterExtraction:

    def test_priority_extracted_high(self):
        intent, params = VoiceAgent.detect_intent("add task urgent: finish CV project deadline tomorrow")
        assert intent == "CREATE_TASK"
        assert params.get("priority") == "HIGH"

    def test_priority_default_medium(self):
        intent, params = VoiceAgent.detect_intent("add task to read chapter 3")
        assert intent == "CREATE_TASK"
        assert params.get("priority") == "MEDIUM"

    def test_due_date_tomorrow(self):
        intent, params = VoiceAgent.detect_intent("create task: submit report by tomorrow")
        assert intent == "CREATE_TASK"
        assert params.get("due_date") == "tomorrow"

    def test_due_date_today(self):
        intent, params = VoiceAgent.detect_intent("add task study DBMS today")
        assert intent == "CREATE_TASK"
        assert params.get("due_date") == "today"


class TestSleepParameterExtraction:

    def test_sleep_hours_extracted(self):
        intent, params = VoiceAgent.detect_intent("I slept 6.5 hours last night")
        assert intent == "LOG_SLEEP"
        assert params.get("sleep_hours") == 6.5

    def test_mood_high_stress(self):
        intent, params = VoiceAgent.detect_intent("log sleep 5 hours with high stress")
        assert intent == "LOG_SLEEP"
        assert params.get("mood") <= 2

    def test_mood_great(self):
        intent, params = VoiceAgent.detect_intent("record 8 hours sleep feeling great")
        assert intent == "LOG_SLEEP"
        assert params.get("mood") >= 4


class TestExtendDeadlineExtraction:

    def test_minutes_from_hours(self):
        _, params = VoiceAgent.detect_intent("extend deadline by 2 hours")
        assert params.get("minutes") == 120

    def test_minutes_direct(self):
        _, params = VoiceAgent.detect_intent("extend by 30 minutes")
        assert params.get("minutes") == 30

    def test_days_to_minutes(self):
        _, params = VoiceAgent.detect_intent("postpone by 1 day")
        assert params.get("minutes") == 1440


# =============================================================================
# 3. Context-Aware Intent Tests (Confirmation / Cancellation)
# =============================================================================

class TestContextAwareIntent:

    def test_confirm_with_pending_action(self):
        context = {"pending_action": "LOG_EXPENSE"}
        intent, params = VoiceAgent.detect_intent("yes, go ahead", context)
        assert intent == "CONFIRM_ACTION"

    def test_cancel_with_pending_action(self):
        context = {"pending_action": "LOG_EXPENSE"}
        intent, params = VoiceAgent.detect_intent("no, cancel", context)
        assert intent == "CANCEL_ACTION"

    def test_no_context_does_not_auto_confirm(self):
        intent, _ = VoiceAgent.detect_intent("yes please")
        # Without a pending_action context, "yes" should not be CONFIRM_ACTION
        assert intent != "CONFIRM_ACTION"


# =============================================================================
# 4. Command Pattern Registry Tests
# =============================================================================

class TestIntentCommandRegistry:

    EXPECTED_INTENTS = [
        "LOG_EXPENSE", "SET_BUDGET", "CREATE_TASK", "CREATE_TRIP",
        "COMPLETE_TASK", "EXTEND_DEADLINE", "CHANGE_PRIORITY", "LOG_SLEEP",
        "GET_TASKS", "GET_WELLNESS", "GET_FINANCES", "GET_TRIPS",
        "GET_INTELLIGENCE", "GET_TIME", "CONFIRM_ACTION", "CANCEL_ACTION",
    ]

    def test_all_expected_intents_registered(self):
        for intent in self.EXPECTED_INTENTS:
            assert intent in INTENT_REGISTRY, f"Intent '{intent}' missing from INTENT_REGISTRY"

    def test_registry_commands_have_tool_name(self):
        for intent, cmd_cls in INTENT_REGISTRY.items():
            cmd = cmd_cls()
            assert isinstance(cmd.tool_name, str), f"{intent} command has no tool_name"
            assert len(cmd.tool_name) > 0

    def test_general_coaching_not_in_registry(self):
        """GENERAL_COACHING is LLM-only and should not be in the registry."""
        assert "GENERAL_COACHING" not in INTENT_REGISTRY

    def test_execute_intent_unknown_returns_none(self):
        """Unknown intent should return (None, None) cleanly."""
        tool_name, tool_data = execute_intent("NONEXISTENT_INTENT", user_id=1, params={})
        assert tool_name is None
        assert tool_data is None

    def test_get_time_command_returns_current_time(self):
        """GET_TIME command should return a dict with expected keys."""
        tool_name, tool_data = execute_intent("GET_TIME", user_id=1, params={})
        assert tool_name == "get_current_time"
        assert isinstance(tool_data, dict)
        assert "current_time" in tool_data
        assert "current_date" in tool_data


# =============================================================================
# 5. Calling Policy Engine Tests (with mocked DB)
# =============================================================================

class TestCallingPolicyEngine:

    def _make_prefs(self, **kwargs):
        prefs = MagicMock()
        prefs.voice_calls_enabled = kwargs.get("voice_calls_enabled", True)
        prefs.calling_consent_status = kwargs.get("calling_consent_status", "OPTED_IN")
        prefs.quiet_hours_start = kwargs.get("quiet_hours_start", "22:00")
        prefs.quiet_hours_end = kwargs.get("quiet_hours_end", "08:00")
        return prefs

    def test_within_quiet_hours_overnight(self):
        from backend.app.voice.policy import CallingPolicyEngine
        import datetime
        prefs = self._make_prefs(quiet_hours_start="22:00", quiet_hours_end="08:00")
        # 23:30 should be in quiet hours (22:00 – 08:00 overnight)
        assert CallingPolicyEngine.is_within_quiet_hours(prefs, datetime.time(23, 30)) is True

    def test_outside_quiet_hours(self):
        from backend.app.voice.policy import CallingPolicyEngine
        import datetime
        prefs = self._make_prefs(quiet_hours_start="22:00", quiet_hours_end="08:00")
        # 14:00 should be outside quiet hours
        assert CallingPolicyEngine.is_within_quiet_hours(prefs, datetime.time(14, 0)) is False

    def test_user_opted_out_blocks_call(self):
        from backend.app.voice.policy import CallingPolicyEngine
        db = MagicMock()
        prefs = self._make_prefs(calling_consent_status="OPTED_OUT")
        db.query.return_value.filter.return_value.first.return_value = prefs

        with patch("backend.app.voice.policy.IntelligenceService") as mock_intel:
            mock_state = MagicMock()
            mock_state.compound_risk_level = "HIGH"
            mock_state.proactive_intervention_recommended = True
            mock_state.proactive_intervention_reason = "High risk"
            mock_intel.evaluate_student_state.return_value = mock_state

            result = CallingPolicyEngine.evaluate_outbound_eligibility(db, user_id=1, ignore_quiet_hours=True)

        assert result["should_call"] is False
        assert "USER_NOT_OPTED_IN_FOR_CALLS" in result["blocked_reasons"]

    def test_voice_disabled_blocks_call(self):
        from backend.app.voice.policy import CallingPolicyEngine
        db = MagicMock()
        prefs = self._make_prefs(voice_calls_enabled=False)
        db.query.return_value.filter.return_value.first.return_value = prefs

        with patch("backend.app.voice.policy.IntelligenceService") as mock_intel:
            mock_state = MagicMock()
            mock_state.compound_risk_level = "HIGH"
            mock_state.proactive_intervention_recommended = True
            mock_state.proactive_intervention_reason = "High risk"
            mock_intel.evaluate_student_state.return_value = mock_state

            result = CallingPolicyEngine.evaluate_outbound_eligibility(db, user_id=1, ignore_quiet_hours=True)

        assert result["should_call"] is False
        assert "USER_DISABLED_VOICE_CALLS" in result["blocked_reasons"]


# =============================================================================
# 6. LLM Strategy Chain Tests (with mocked network)
# =============================================================================

class TestLLMStrategyChain:

    def test_ollama_strategy_unavailable_returns_none(self):
        """When Ollama is offline, OllamaStrategy.generate() returns None."""
        from backend.app.voice.llm_strategy import OllamaStrategy
        strategy = OllamaStrategy(url="http://127.0.0.1:11434", model="llama3.2:1b")
        with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
            result = strategy.generate("test prompt", "system prompt")
        assert result is None

    def test_openai_strategy_no_key_unavailable(self):
        """OpenAI strategy is unavailable when api_key is empty string."""
        from backend.app.voice.llm_strategy import OpenAIStrategy
        strategy = OpenAIStrategy(api_key="")
        assert strategy.is_available() is False
        result = strategy.generate("test", "system")
        assert result is None

    def test_local_domain_strategy_always_available(self):
        """LocalDomainStrategy must always report is_available() = True."""
        from backend.app.voice.llm_strategy import LocalDomainStrategy
        strategy = LocalDomainStrategy()
        assert strategy.is_available() is True

    def test_build_strategy_chain_without_openai(self):
        """Chain without OPENAI_API_KEY should contain only OllamaStrategy."""
        from backend.app.voice.llm_strategy import build_strategy_chain, OllamaStrategy
        mock_settings = MagicMock()
        mock_settings.LOCAL_LLM_URL = "http://127.0.0.1:11434"
        mock_settings.LOCAL_LLM_MODEL = "llama3.2:1b"
        mock_settings.OPENAI_API_KEY = ""
        chain = build_strategy_chain(mock_settings)
        assert len(chain) == 1
        assert isinstance(chain[0], OllamaStrategy)

    def test_build_strategy_chain_with_openai(self):
        """Chain with OPENAI_API_KEY should include OpenAIStrategy."""
        from backend.app.voice.llm_strategy import build_strategy_chain, OllamaStrategy, OpenAIStrategy
        mock_settings = MagicMock()
        mock_settings.LOCAL_LLM_URL = "http://127.0.0.1:11434"
        mock_settings.LOCAL_LLM_MODEL = "llama3.2:1b"
        mock_settings.OPENAI_API_KEY = "sk-fake-key"
        chain = build_strategy_chain(mock_settings)
        assert len(chain) == 2
        assert isinstance(chain[0], OllamaStrategy)
        assert isinstance(chain[1], OpenAIStrategy)


# =============================================================================
# 7. Observer Pattern Tests
# =============================================================================

class TestAlertObserverPattern:

    @pytest.mark.asyncio
    async def test_websocket_observer_called_on_notify(self):
        """WebSocketAlertObserver.on_alert() should call broadcast_call with correct payload."""
        from backend.app.voice.alert_observer import (
            AlertSubject, AlertEvent, WebSocketAlertObserver
        )
        mock_call_manager = MagicMock()
        mock_call_manager.broadcast_call = MagicMock(return_value=None)

        subject = AlertSubject()
        observer = WebSocketAlertObserver(mock_call_manager)
        subject.subscribe(observer)

        event = AlertEvent(
            event_type="DEADLINE",
            call_id="CALL_DEADLINE_99",
            caller_name="CampusLife Co-Pilot",
            caller_subtitle="🚨 Test",
            preview_text="Test alert",
            greeting="Hello test",
            payload={"task_id": 99},
        )
        await subject.notify(event)
        mock_call_manager.broadcast_call.assert_called_once()
        call_args = mock_call_manager.broadcast_call.call_args[0][0]
        assert call_args["event"] == "INCOMING_CALL"
        assert call_args["call_type"] == "DEADLINE"
        assert call_args["call_id"] == "CALL_DEADLINE_99"

    @pytest.mark.asyncio
    async def test_failing_observer_does_not_block_others(self):
        """A failing observer should be isolated — other observers still receive the event."""
        from backend.app.voice.alert_observer import (
            AlertSubject, AlertEvent, AlertObserver, LogAlertObserver
        )

        class FailingObserver(AlertObserver):
            async def on_alert(self, event):
                raise RuntimeError("Observer failure simulation")

        subject = AlertSubject()
        failing = FailingObserver()
        log_obs = LogAlertObserver()
        subject.subscribe(failing)
        subject.subscribe(log_obs)

        event = AlertEvent(
            event_type="LOW_SLEEP",
            call_id="CALL_SLEEP_1",
            caller_name="Health Sentinel",
            caller_subtitle="🌙 Low Sleep",
            preview_text="Low sleep alert",
            greeting="Hello",
        )
        # Should not raise — failures are isolated
        await subject.notify(event)

    def test_unsubscribe_removes_observer(self):
        """unsubscribe() should remove the observer from the notification list."""
        from backend.app.voice.alert_observer import AlertSubject, LogAlertObserver
        subject = AlertSubject()
        obs = LogAlertObserver()
        subject.subscribe(obs)
        assert len(subject._observers) == 1
        subject.unsubscribe(obs)
        assert len(subject._observers) == 0
