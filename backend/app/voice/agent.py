import re
import json
import datetime
import logging
from typing import Dict, Any, Tuple, Optional
from backend.app.tools import campuslife_tools

from backend.app.voice.llm_engine import local_student_llm
from backend.app.voice.intent_commands import execute_intent

logger = logging.getLogger("campuslife.agent")

class VoiceAgent:
    """
    Conversational dialogue agent for CampusLife AI.
    Understands student voice queries, manages context, executes tools,
    and synthesizes natural speech responses through the Local Student LLM Engine.
    """

    @staticmethod
    def parse_expense_query(query: str) -> Optional[Dict[str, Any]]:
        """
        Robustly extracts amount, category, description, and payment method
        from student conversational input (voice or text).
        """
        q_low = query.lower().strip()

        # Check if query indicates spending / logging an expense
        is_expense = (
            re.search(r"\b(?:spent|spend|spended|paid|pay|paying|bought|buy|buying|purchased|purchase|log(?:ged)?\s+(?:an?\s+)?expense|add(?:ed)?\s+(?:an?\s+)?expense|expense(?:\s+of)?)\b", q_low) or
            re.search(r"(?:₹|rs\.?|inr|rupees|bucks)\s*(?:for|on|towards|spent|paid)", q_low) or
            re.search(r"\b(?:for|on)\s+.*?\s+(?:₹|rs\.?|inr|rupees|bucks)", q_low)
        )
        if not is_expense:
            return None

        # 1. Payment Method Detection
        pay_method = "UPI"
        if re.search(r"\b(?:via|by|with|in|through)?\s*cash\b", q_low):
            pay_method = "CASH"
        elif re.search(r"\b(?:via|by|with|in|through)?\s*(?:debit|credit)?\s*card\b", q_low):
            pay_method = "CARD"
        elif re.search(r"\b(?:via|by|with|in|through)?\s*(?:upi|gpay|google\s*pay|phonepe|paytm|bhim|qr|online|netbanking)\b", q_low):
            pay_method = "UPI"

        # 2. Amount Extraction
        amt = None
        amt_match = re.search(r"(?:₹|rs\.?|inr|\$)\s*(\d+(?:,\d+)*(?:\.\d+)?)", q_low)
        if not amt_match:
            amt_match = re.search(r"(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:₹|rs\.?|inr|rupees|bucks)", q_low)
        if not amt_match:
            amt_match = re.search(r"\b(?:spent|spend|paid|pay|expense(?:\s+of)?|for|amount(?:\s+of)?)\s*(\d+(?:,\d+)*(?:\.\d+)?)\b", q_low)
        if not amt_match:
            amt_match = re.search(r"\b(\d+(?:,\d+)*(?:\.\d+)?)\b", q_low)

        if amt_match:
            try:
                amt = float(amt_match.group(1).replace(",", ""))
            except ValueError:
                return None
        else:
            return None

        if amt <= 0:
            return None

        # 3. Clean Description Extraction
        clean_desc = q_low
        clean_desc = re.sub(r"\b(?:via|by|with|in|through)?\s*(?:cash|upi|gpay|google\s*pay|phonepe|paytm|bhim|qr|online|(?:debit|credit)?\s*card|netbanking)\b", " ", clean_desc, flags=re.I)
        clean_desc = re.sub(r"\b(?:i|have|just|please|can you)?\s*(?:spent|spend|spended|paid|pay|buying|bought|purchased|purchase|log(?:ged)?(?:\s+an?)?\s+expense|add(?:ed)?(?:\s+an?)?\s+expense|expense(?:\s+of)?)\b", " ", clean_desc, flags=re.I)

        amt_clean = str(int(amt) if amt.is_integer() else amt)
        clean_desc = re.sub(r"\b(?:for|on|worth|of|at|towards)\s*(?:₹|rs\.?|inr|\$)?\s*" + re.escape(amt_clean) + r"(?:,\d+)*(?:\.\d+)?\s*(?:₹|rs\.?|inr|rupees|bucks)?\b", " ", clean_desc, flags=re.I)
        clean_desc = re.sub(r"(?:₹|rs\.?|inr|\$)?\s*" + re.escape(amt_clean) + r"(?:,\d+)*(?:\.\d+)?\s*(?:₹|rs\.?|inr|rupees|bucks)?", " ", clean_desc, flags=re.I)
        clean_desc = re.sub(r"\b" + re.escape(amt_clean) + r"\b", " ", clean_desc)

        clean_desc = re.sub(r"^\s*\b(?:for|on|worth(?:\s+of)?|towards|in|at|of)\b\s+", " ", clean_desc, flags=re.I)
        clean_desc = re.sub(r"\s+\b(?:for|on|worth|towards|at|of|today|yesterday|now|please|it)\b\s*$", " ", clean_desc, flags=re.I)
        clean_desc = re.sub(r"\s+", " ", clean_desc).strip()

        # 4. Intelligent Category Classification
        detected_category = campuslife_tools.classify_expense_category(
            description=clean_desc,
            category_hint=q_low
        )

        final_description = clean_desc.strip().title() if clean_desc.strip() else f"{detected_category} Expense"

        return {
            "amount": amt,
            "category": detected_category,
            "description": final_description,
            "payment_method": pay_method
        }

    @staticmethod
    def detect_intent(query: str, context: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any]]:
        q = query.lower().strip()

        # Follow-up context check
        if context and context.get("pending_action"):
            if any(w in q for w in ["yes", "yeah", "sure", "ok", "confirm", "proceed", "do it"]):
                return "CONFIRM_ACTION", {"action": context["pending_action"]}
            elif any(w in q for w in ["no", "cancel", "don't", "stop", "nevermind"]):
                return "CANCEL_ACTION", {}

        # 1. Create Task with Deadlines (Mutation -> Database)
        if any(w in q for w in ["add task", "create task", "new task", "remind me to", "add a task", "schedule task", "schedule assignment", "have an assignment", "have homework", "add assignment", "create a task"]):
            pri = "HIGH" if any(w in q for w in ["urgent", "important", "high priority", "critical"]) else ("LOW" if "low priority" in q else "MEDIUM")
            clean_title = re.sub(r"^(?:please\s+)?(?:add|create|new|schedule|remind me to)\s*(?:a\s*)?(?:task|assignment|homework)?(?:\s*to|\s*for)?\s*", "", q, flags=re.I).strip()

            due_str = None
            due_match = re.search(r"\b(?:due|by|before|on)\s+((?:today|tonight|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d+[\w\s:]+))\b", clean_title, flags=re.I)
            if due_match:
                due_str = due_match.group(1).strip()
                clean_title = clean_title[:due_match.start()].strip()
            elif "tomorrow" in q:
                due_str = "tomorrow"
            elif "today" in q:
                due_str = "today"

            clean_title = clean_title.capitalize() if clean_title else "Study Task"
            return "CREATE_TASK", {"title": clean_title, "priority": pri, "due_date": due_str}

        # 2. Log Expense (Mutation -> Database)
        expense_data = VoiceAgent.parse_expense_query(query)
        if expense_data and expense_data.get("amount"):
            return "LOG_EXPENSE", expense_data

        # 2b. Set Budget / Balance (Mutation -> Database)
        budget_set_match = re.search(
            r"\b(?:set|update|change|make|adjust|put|reset|fix)\b.*?\b(?:remaining\s+)?(balance|budget)\b.*?(?:to|at|=|is)?\s*(?:₹|rs\.?|inr|\$)?\s*(\d+(?:,\d+)*(?:\.\d+)?)",
            q,
            re.I
        )
        if not budget_set_match:
            budget_set_match = re.search(
                r"\b(?:my\s+)?(?:remaining\s+)?(balance|budget)(?:\s+limit)?\s*(?:is|=|to|:)\s*(?:₹|rs\.?|inr|\$)?\s*(\d+(?:,\d+)*(?:\.\d+)?)",
                q,
                re.I
            )
        if not budget_set_match:
            budget_set_match_rev = re.search(
                r"\b(?:set|make|update)\s*(?:₹|rs\.?|inr|\$)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:as|for|to)\s*(?:my\s+)?(?:remaining\s+)?(balance|budget)\b",
                q,
                re.I
            )
            if budget_set_match_rev:
                num_str = budget_set_match_rev.group(1).replace(",", "")
                target_type = "balance" if ("balance" in q or "remaining" in q) else "budget"
                return "SET_BUDGET", {"amount": float(num_str), "target_type": target_type}

        if budget_set_match:
            num_str = budget_set_match.group(2).replace(",", "")
            target_type = "balance" if ("balance" in q or "remaining" in q) else "budget"
            return "SET_BUDGET", {"amount": float(num_str), "target_type": target_type}

        # 3. Complete Task
        if re.search(r"\b(complete|completed|finish|finished|done|done with|submitted|submit|mark.*complete|mark.*done)\b", q):
            target = re.sub(r"\b(i|have|finished|the|task|mark|it|as|complete|completed|done|with|please|submitted|already|just)\b", "", q, flags=re.I).strip()
            return "COMPLETE_TASK", {"target": target or "it"}

        # 4. Extend / Increase Deadline (Mutation -> Database)
        if any(w in q for w in ["extend", "increase deadline", "more time", "postpone", "push deadline", "delay deadline", "add hour", "add minute", "extend deadline"]):
            minutes = 60
            hour_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours|hour|hrs|hr|h)\b", q)
            min_match = re.search(r"(\d+)\s*(?:minutes|minute|mins|min|m)\b", q)
            day_match = re.search(r"(\d+)\s*(?:days|day|d)\b", q)
            if hour_match:
                minutes = int(float(hour_match.group(1)) * 60)
            elif min_match:
                minutes = int(min_match.group(1))
            elif day_match:
                minutes = int(day_match.group(1)) * 1440
            elif "half an hour" in q or "30 min" in q:
                minutes = 30
            return "EXTEND_DEADLINE", {"minutes": minutes, "target": q}

        # 5. Change Priority (Mutation -> Database)
        if any(w in q for w in ["priority", "urgent", "make it high", "make it low", "make it medium", "set priority"]):
            pri = "HIGH" if any(w in q for w in ["high", "urgent", "top", "critical"]) else ("LOW" if "low" in q else "MEDIUM")
            return "CHANGE_PRIORITY", {"priority": pri, "target": q}

        # 6. Log Sleep / Wellness & Vitals Update (Mutation -> Database)
        is_wellness_logging = (
            (re.search(r"\b(sleep|slept)\b", q) and re.search(r"\d", q)) or
            re.search(r"\b(?:log|record|track|save)\b.*(?:sleep|vitals|health|wellness|mood|stress|felt)", q) or
            re.search(r"\b(?:into|in)\s+my\s+(?:health|vitals|wellness|hair|felt)\b", q)
        )
        if is_wellness_logging:
            match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours|hrs|hr|h)?", q)
            hours = float(match.group(1)) if match else 7.5

            mood = 4
            if any(w in q for w in ["low stress", "relaxed", "calm", "great", "excellent", "happy", "refreshed"]):
                mood = 5
            elif any(w in q for w in ["good", "fine", "decent", "normal", "balanced"]):
                mood = 4
            elif any(w in q for w in ["moderate stress", "medium stress", "okay", "busy"]):
                mood = 3
            elif any(w in q for w in ["high stress", "stressed", "anxious", "bad", "terrible", "exhausted", "tired", "depressed"]):
                mood = 2

            mood_num_match = re.search(r"\bmood(?:\s+is|\s*:)?\s*(\d)\b", q)
            if mood_num_match:
                mood = max(1, min(5, int(mood_num_match.group(1))))

            energy = 4
            if any(w in q for w in ["high energy", "energetic", "full of energy", "hyper"]):
                energy = 5
            elif any(w in q for w in ["low energy", "fatigued", "exhausted", "drained"]):
                energy = 2

            return "LOG_SLEEP", {"sleep_hours": hours, "mood": mood, "energy": energy, "notes": query.strip()}

        # 7. Create Trip (Mutation -> Database)
        trip_match = re.search(r"\b(?:plan|create|add|book)\s+(?:a\s*)?trip\s+to\s+([a-zA-Z\s]+)", q)
        if trip_match:
            dest = trip_match.group(1).strip().title()
            return "CREATE_TRIP", {"destination": dest}

        # 8. Inquiry & Status Checks (Read intents prioritized over fallback)
        if any(w in q for w in ["what time", "current time", "what's the time", "tell me the time", "what is the time", "today's date", "what date", "what day is today"]):
            return "GET_TIME", {}

        # Wellness inquiry
        if any(w in q for w in ["sleep", "mood", "health", "stress", "tired", "wellness", "energy"]) and any(w in q for w in ["how", "what", "tell", "show", "check", "status", "my"]):
            return "GET_WELLNESS", {}

        # Trip inquiry
        if any(w in q for w in ["trip", "travel", "vacation", "holiday", "itinerary", "flight"]) and any(w in q for w in ["how", "what", "tell", "show", "check", "any", "upcoming", "list"]):
            return "GET_TRIPS", {}

        # Task inquiry (read, not create/complete/extend/priority)
        if any(w in q for w in ["task", "tasks", "assignment", "assignments", "homework", "deadline", "deadlines", "study plan"]) or (("due" in q or "pending" in q) and any(w in q for w in ["what", "show", "check", "list", "any", "do i have", "my"])):
            return "GET_TASKS", {}

        # Finance inquiry (read, not log/set)
        if any(w in q for w in ["money", "budget", "spent", "spend", "expense", "expenses", "finances", "balance", "runway", "rupees"]) and any(w in q for w in ["how much", "how", "what", "show", "check", "tell", "my", "remaining", "left", "total", "summary"]):
            return "GET_FINANCES", {}

        # Schedule / Timetable inquiry
        if any(w in q for w in ["schedule", "timetable", "routine", "classes", "agenda", "what do i have today", "calendar", "lectures"]):
            return "GET_SCHEDULE", {}

        # Overall summary / intelligence
        if any(w in q for w in ["overall", "co-pilot", "summary", "status", "focus", "advice", "overview", "campus life index", "briefing"]):
            return "GET_INTELLIGENCE", {}

        # 9. Fast Conversational Filter (Instant 0ms routing for greetings and chat)
        conversational_starters = (
            "hi", "hello", "hey", "how are you", "who are you", "what can you do",
            "good morning", "good evening", "good afternoon", "thanks", "thank you",
            "tell me a joke", "how is it going", "what's up", "help", "cool", "okay", "ok"
        )
        if any(q == w or q.startswith(w + " ") or q.endswith(" " + w) for w in conversational_starters):
            return "GENERAL_COACHING", {}

        # 10. Neural Action Extraction via Ollama (ONLY when mutation keywords are present)
        action_indicator_words = {
            "log", "record", "save", "track", "add", "spent", "spend", "paying", "paid",
            "bought", "buy", "create", "mark", "schedule", "extend", "postpone", "delay",
            "budget", "trip", "completed", "done", "deadline"
        }
        if any(w in q for w in action_indicator_words):
            extracted = local_student_llm.classify_and_extract_tool(query)
            if extracted and extracted.get("action"):
                act = extracted["action"]
                p = extracted.get("params", {})
                if act == "log_expense" and p.get("amount"):
                    return "LOG_EXPENSE", p
                elif act == "create_task" and p.get("title"):
                    return "CREATE_TASK", p
                elif act == "log_sleep" and p.get("sleep_hours"):
                    return "LOG_SLEEP", p
                elif act == "create_trip" and p.get("destination"):
                    return "CREATE_TRIP", p
                elif act == "complete_task":
                    return "COMPLETE_TASK", p
                elif act == "extend_task_deadline":
                    return "EXTEND_DEADLINE", p
                elif act == "set_budget" and p.get("amount"):
                    return "SET_BUDGET", p

        return "GENERAL_COACHING", {}

    @staticmethod
    def process_turn(user_id: int, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executes a single conversational turn:
        Detects intent -> dispatches via Command Pattern registry -> synthesizes response.

        The original 15-branch if/elif block has been replaced by a single
        execute_intent() call that looks up the appropriate IntentCommand subclass
        from INTENT_REGISTRY. Adding a new intent requires ONLY adding a new Command
        subclass — this method never needs to change. (Open/Closed Principle)
        """
        context = context or {}
        intent, params = VoiceAgent.detect_intent(query, context)
        requires_confirmation = False
        confirmation_action = None

        logger.info(
            "intent_dispatched",
            extra={"user_id": user_id, "intent": intent, "params_keys": list(params.keys())},
        )

        # ── Command Pattern Dispatch ────────────────────────────────────────
        # execute_intent() looks up INTENT_REGISTRY[intent] → instantiates the
        # correct IntentCommand subclass → calls execute(user_id, params).
        # GENERAL_COACHING is the only intent not in the registry (LLM-only).
        tool_executed, tool_data = execute_intent(intent, user_id, params)

        # Generate contextual speech response via Local Student LLM
        persona = context.get("persona")
        llm_output = local_student_llm.generate_student_response(
            user_query=query,
            intent=intent,
            tool_executed=tool_executed,
            tool_data=tool_data,
            persona=persona,
            user_id=user_id
        )

        return {
            "intent": intent,
            "reply": llm_output["text"],
            "engine": llm_output["engine"],
            "persona": llm_output["persona"],
            "latency_ms": llm_output["latency_ms"],
            "tool_executed": tool_executed,
            "tool_data": tool_data,
            "requires_confirmation": requires_confirmation,
            "confirmation_action": confirmation_action
        }

