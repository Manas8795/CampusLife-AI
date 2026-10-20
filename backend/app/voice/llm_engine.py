import os
import re
import json
import time
import datetime
import urllib.request
import urllib.error
import logging
from typing import Dict, Any, Optional, List
from backend.app.config import settings
from backend.app.voice.llm_strategy import build_strategy_chain, OllamaStrategy

logger = logging.getLogger("campuslife.llm_engine")

class LocalStudentLLM:
    """
    Dedicated Local LLM Engine for CampusLife AI Voice Assistant (Module 7).
    Seamlessly integrates with:
    1. Local Ollama Server (http://localhost:11434) running llama3.2, phi3, mistral, etc.
    2. Local LM Studio / vLLM (http://localhost:1234/v1)
    3. Online API (OpenAI / Gemini / Groq)
    4. Intelligent Local Domain Engine with dynamic query parsing & arithmetic fallback.
    """

    PERSONAS = {
        "EMPATHETIC_MENTOR": (
            "You are CampusLife Voice Assistant, a supportive, knowledgeable academic mentor for college students. "
            "Communicate exclusively in clear, fluent, natural English with complete sentences and thoughtful explanations. "
            "Provide detailed, comprehensive, and empathetic responses with actionable guidance. "
            "Ground your answers deeply in the student's real-time academic schedule, wellness metrics, and financial context. Always encourage balanced living."
        ),
        "PRODUCTIVITY_COACH": (
            "You are CampusLife Voice Assistant, an energetic high-performance student productivity coach. "
            "Communicate exclusively in clear, direct, and motivating English with complete sentences. "
            "Provide detailed, structured, and actionable guidance. Break down daily schedules, optimize study blocks, prioritize tasks by deadline, and eliminate academic friction."
        ),
        "CAMPUS_PEER": (
            "You are CampusLife Voice Assistant, a smart, friendly senior college peer. "
            "Communicate exclusively in friendly, relatable, and clear English with complete sentences. "
            "Give thorough, relatable, and well-rounded advice with full explanations. Cover course routines, hostel budgeting, study tactics, and campus life balance in full detail."
        )
    }

    def _get_student_context_summary(self, user_id: int = 1) -> str:
        """
        Builds a comprehensive real-time context summary of the student's
        academic schedule, courses, pending tasks, budget, and wellness status.
        Provides the LLM with deep grounding across all modules.
        """
        now_dt = datetime.datetime.now()
        day_name = now_dt.strftime("%A")

        # 1. Weekly Class Timetable & Schedule for B.Tech CSE (Year 3)
        schedule_by_day = {
            "Monday": "08:00 AM - 09:30 AM: CS301 Operating Systems (Hall 204) | 10:00 AM - 11:30 AM: CS303 Database Management Systems (Hall 102) | 02:00 PM - 04:00 PM: CS305 Networks Lab (Lab 3)",
            "Tuesday": "08:30 AM - 10:00 AM: CS302 Computer Networks (Hall 105) | 10:30 AM - 12:00 PM: CS304 Software Engineering (Hall 201) | 02:30 PM - 04:30 PM: CS306 OS Kernel Lab (Lab 1)",
            "Wednesday": "08:00 AM - 09:30 AM: CS301 Operating Systems (Hall 204) | 10:00 AM - 11:30 AM: CS303 Database Systems (Hall 102) | 01:30 PM - 03:30 PM: CS307 Cloud Computing (Seminar Room)",
            "Thursday": "08:00 AM - 09:30 AM: CS302 Computer Networks (Hall 105) | 10:00 AM - 11:30 AM: CS304 Software Engineering (Hall 201) | 02:00 PM - 04:00 PM: CS308 Database Lab (Lab 2)",
            "Friday": "09:00 AM - 10:30 AM: CS309 Design & Analysis of Algorithms (Hall 303) | 11:00 AM - 12:30 PM: CS310 Web Technologies (Hall 202) | 02:00 PM - 03:30 PM: Capstone Mentorship",
            "Saturday": "10:00 AM - 01:00 PM: Software Engineering Sprint (Innovation Hub) | Afternoon: Library Self-Study",
            "Sunday": "Flexible Study Review, Weekly Planning, Rest & Recuperation"
        }
        today_classes = schedule_by_day.get(day_name, "09:00 AM - 01:00 PM: Core Lectures & Academic Study")

        # 2. Live Data Extraction (with fail-safe fallback)
        tasks_summary = "2 pending assignments: OS Virtual Memory Assignment (High priority), DB Schema Design (Medium priority)"
        finances_summary = "Monthly Budget: ₹12,000 | Spent: ~₹4,350 | Balance: ~₹7,650 (Runway: ~22 days, Healthy)"
        wellness_summary = "7-day average sleep: 6.8 hrs/night | Stress Level: Moderate | Energy: 4/5"

        try:
            from backend.app.database import SessionLocal
            from backend.app.study.models import Task
            from backend.app.expenses.service import ExpenseService
            from backend.app.health.service import HealthService

            with SessionLocal() as db:
                user_tasks = db.query(Task).filter(Task.user_id == user_id, Task.status != "COMPLETED").order_by(Task.due_date.asc()).limit(4).all()
                if user_tasks:
                    task_items = [f"'{t.title}' ({t.subject}, Priority: {t.priority}, Due: {t.due_date.strftime('%b %d %I:%M %p') if t.due_date else 'Flexible'})" for t in user_tasks]
                    tasks_summary = f"{len(user_tasks)} active tasks: " + "; ".join(task_items)

                exp_summary = ExpenseService.get_monthly_summary(db, user_id)
                if exp_summary:
                    spent = exp_summary.get("total_spent", 0.0)
                    limit = exp_summary.get("budget_limit", 12000.0)
                    bal = exp_summary.get("remaining_balance", limit - spent)
                    runway = exp_summary.get("estimated_days_runway", 20)
                    finances_summary = f"Monthly Limit: ₹{limit:,.0f} | Spent: ₹{spent:,.0f} | Balance: ₹{bal:,.0f} | Runway: ~{runway} days"

                w_state = HealthService.get_user_wellness_state(db, user_id)
                if w_state:
                    avg_s = w_state.get("average_sleep_7d", 6.8)
                    stress = w_state.get("current_stress_level", "MODERATE")
                    deficit = w_state.get("target_sleep_deficit", 0.0)
                    wellness_summary = f"Avg Sleep: {avg_s} hrs/night (Deficit: {deficit:.1f} hrs) | Stress: {stress}"
        except Exception:
            pass

        return (
            f"- Student: Alex Sharma (3rd Year B.Tech Computer Science, Semester 6)\n"
            f"- Today's Day: {day_name}\n"
            f"- Today's Academic Timetable: {today_classes}\n"
            f"- Coursework & Tasks: {tasks_summary}\n"
            f"- Financial Status: {finances_summary}\n"
            f"- Wellness & Recovery: {wellness_summary}"
        )

    def __init__(self):
        self.local_url = settings.LOCAL_LLM_URL.rstrip('/')
        self.local_model = settings.LOCAL_LLM_MODEL
        self.default_persona = settings.STUDENT_PERSONA
        # Build ordered strategy chain via Strategy Pattern factory
        self._strategy_chain = build_strategy_chain(settings)

    def get_ollama_status(self) -> Dict[str, Any]:
        """Checks if a local Ollama server is running — delegates to OllamaStrategy (5s cache)."""
        ollama = next((s for s in self._strategy_chain if isinstance(s, OllamaStrategy)), None)
        if ollama and ollama.is_available():
            return {
                "is_running": True,
                "server_type": "Ollama Local Engine",
                "url": self.local_url,
                "active_model": ollama.get_active_model(),
            }
        return {
            "is_running": False,
            "server_type": "None (Offline)",
            "url": self.local_url,
            "active_model": self.local_model,
        }

    def match_task_semantically(self, user_statement: str, candidates: List[Dict[str, Any]]) -> Optional[int]:
        """
        Uses the Local LLM (Llama 3.2) to semantically identify which task 
        the student is referring to based on meaning, concepts, and synonyms.
        """
        if not candidates:
            return None

        ollama_status = self.get_ollama_status()
        if ollama_status["is_running"]:
            candidate_lines = "\n".join([f"- ID {c['id']}: '{c['title']}' ({c.get('subject', 'General')})" for c in candidates[:8]])
            prompt = (
                f"You are a semantic task resolution system. A college student said:\n"
                f"\"{user_statement}\"\n\n"
                f"Here are their pending academic tasks:\n"
                f"{candidate_lines}\n\n"
                f"Which task is the student referring to based on conceptual meaning, synonyms, and subject context?\n"
                f"Reply with a JSON object containing the integer ID of the best matching task, or null if completely unrelated.\n"
                f"Example: {{\"matched_task_id\": 2}}\n"
                f"Your JSON:"
            )

            try:
                model_name = ollama_status["active_model"]
                req_data = json.dumps({
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": "You are a precise task resolution assistant. Always output valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.1, "num_predict": 40}
                }).encode('utf-8')

                req = urllib.request.Request(
                    f"{self.local_url}/api/chat",
                    data=req_data,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=5.0) as res:
                    if res.status == 200:
                        resp_json = json.loads(res.read().decode('utf-8'))
                        content = resp_json.get("message", {}).get("content", "").strip()
                        parsed = json.loads(content)
                        task_id = parsed.get("matched_task_id")
                        if task_id is not None:
                            cand_ids = [c["id"] for c in candidates]
                            if int(task_id) in cand_ids:
                                return int(task_id)
            except Exception:
                pass

        # Fallback to intelligent keyword/token overlap
        stop_words = {"i", "have", "finished", "finish", "task", "the", "mark", "it", "as", "complete", "completed", "done", "with", "please", "solve", "about"}
        words = [w.lower() for w in re.findall(r"\w+", user_statement) if len(w) > 1 and w.lower() not in stop_words]
        
        best_id = None
        best_score = 0
        for c in candidates:
            score = 0
            t_words = [w.lower() for w in re.findall(r"\w+", c["title"])]
            for w in words:
                for tw in t_words:
                    if w == tw: score += 3
                    elif len(w) >= 4 and len(tw) >= 4 and (w.startswith(tw[:4]) or tw.startswith(w[:4])): score += 2
            if score > best_score:
                best_score = score
                best_id = c["id"]
        
        return best_id if best_score >= 2 else None

    def classify_and_extract_tool(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Uses Ollama (llama3.2:1b) to classify if the user wants to log, mutate, or query
        data in the database and extracts the structured parameters.
        Returns: { 'action': 'log_expense'|'create_task'|..., 'params': {...} } or None
        """
        # Fast pre-filter: Skip Ollama entirely if query has no action verb
        action_keywords = {"log", "record", "save", "track", "add", "spent", "spend", "paid", "buy", "create", "mark", "schedule", "extend", "postpone", "delay", "push", "budget", "trip", "done"}
        if not any(w in query.lower() for w in action_keywords):
            return None

        ollama_status = self.get_ollama_status()
        if not ollama_status["is_running"]:
            return None

        prompt = (
            "Analyze the student query and determine if they want to LOG/SAVE data into the database or perform an action.\n"
            "Actions:\n"
            "- 'log_expense': params { 'amount': float, 'category': 'Academic'|'Food'|'Transport'|'Entertainment'|'Health'|'Shopping'|'Other', 'description': str, 'payment_method': 'CASH'|'UPI'|'CARD' }\n"
            "- 'create_task': params { 'title': str, 'subject': str, 'priority': 'HIGH'|'MEDIUM'|'LOW', 'due_date': str }\n"
            "- 'log_sleep': params { 'sleep_hours': float, 'mood': int (1-5), 'energy': int (1-5), 'notes': str }\n"
            "- 'create_trip': params { 'destination': str, 'budget': float }\n"
            "- 'complete_task': params { 'target': str }\n"
            "- 'extend_task_deadline': params { 'target': str, 'minutes': int }\n"
            "- 'set_budget': params { 'amount': float, 'target_type': 'balance'|'budget' }\n"
            "- 'none': if conversational or question\n\n"
            f"Student Query: \"{query}\"\n\n"
            "Respond ONLY with a JSON object: {\"action\": \"...\", \"params\": {...}}"
        )

        try:
            model_name = ollama_status["active_model"]
            req_data = json.dumps({
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "You are a database action extractor. Reply ONLY in JSON with keys 'action' and 'params'."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "keep_alive": "60m",
                "format": "json",
                "options": {"temperature": 0.0, "num_predict": 35, "num_ctx": 512}
            }).encode('utf-8')

            req = urllib.request.Request(
                f"{self.local_url}/api/chat",
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=4.0) as res:
                if res.status == 200:
                    resp_json = json.loads(res.read().decode('utf-8'))
                    content = resp_json.get("message", {}).get("content", "").strip()
                    parsed = json.loads(content)
                    if parsed.get("action") and parsed.get("action") != "none":
                        return parsed
        except Exception:
            pass
        return None

    @staticmethod
    def _is_hindi_or_non_english(text: str) -> bool:
        if not text:
            return False
        # Check Devanagari Unicode script range
        for ch in text:
            if '\u0900' <= ch <= '\u097F':
                return True
        # Check common Romanized Hindi / Hinglish indicator words
        hindi_words = {
            "aap", "aapka", "aapki", "aapke", "main", "meri", "mera", "mere", "mujhe",
            "kuch", "karein", "karna", "madad", "kar", "sakta", "sakti", "hoon", "hai",
            "hain", "nahi", "accha", "achha", "bahut", "thik", "theek", "kaise", "kya", "kyun",
            "shukriya", "dhanyawad", "sujhav", "dost", "samay", "padhai", "kitab", "karo",
            "kharchon", "paisa", "rupaye", "aage", "badhne", "pasand", "namaste", "chahiye"
        }
        tokens = set(re.findall(r"\b[a-zA-Z]+\b", text.lower()))
        matched = tokens.intersection(hindi_words)
        if len(matched) >= 2 or (len(tokens) > 0 and len(matched) / len(tokens) >= 0.15):
            return True
        return False

    def generate_student_response(
        self,
        user_query: str,
        intent: str,
        tool_executed: Optional[str] = None,
        tool_data: Optional[Any] = None,
        persona: Optional[str] = None,
        user_id: int = 1
    ) -> Dict[str, Any]:
        """
        Generates a natural language response using the Strategy Pattern chain.
        Priority: Fast-path domain engine → Ollama → OpenAI → Local Domain Engine.
        Enforces strictly English output across all pipelines.
        """
        start_time = time.time()
        active_persona = persona or self.default_persona
        system_instruction = self.PERSONAS.get(active_persona, self.PERSONAS["EMPATHETIC_MENTOR"])

        # 1. Instant Fast Path (<10ms): When an actionable tool has run or status was fetched
        fast_action_intents = {
            "COMPLETE_TASK", "EXTEND_DEADLINE", "CHANGE_PRIORITY", "CREATE_TASK",
            "GET_TIME", "CONFIRM_ACTION", "CANCEL_ACTION", "LOG_EXPENSE", "SET_BUDGET",
            "GET_TASKS", "GET_FINANCES", "GET_WELLNESS", "GET_TRIPS", "GET_SCHEDULE"
        }
        if tool_executed and intent in fast_action_intents:
            dynamic_res = self._dynamic_student_intelligence(user_query, intent, tool_executed, tool_data, active_persona)
            latency = round((time.time() - start_time) * 1000, 1)
            return {
                "text": dynamic_res,
                "engine": "CampusLife Instant Intelligence Engine",
                "persona": active_persona,
                "latency_ms": latency
            }

        # 2. Build contextual prompt with holistic student context
        prompt = self._build_student_prompt(user_query, intent, tool_executed, tool_data, system_instruction, user_id=user_id)

        # 3. Iterate Strategy Chain (Strategy Pattern)
        # Each strategy is tried in priority order; the first successful non-Hindi
        # response is returned immediately.
        for strategy in self._strategy_chain:
            result = strategy.generate(prompt, system_instruction)
            if result and not self._is_hindi_or_non_english(result):
                latency = round((time.time() - start_time) * 1000, 1)
                logger.info(
                    "llm_response_generated",
                    extra={"strategy": strategy.name, "intent": intent, "latency_ms": latency},
                )
                return {
                    "text": result,
                    "engine": strategy.name,
                    "persona": active_persona,
                    "latency_ms": latency
                }

        # 4. Guaranteed English fallback — Local Domain Engine
        dynamic_res = self._dynamic_student_intelligence(user_query, intent, tool_executed, tool_data, active_persona)
        latency = round((time.time() - start_time) * 1000, 1)
        return {
            "text": dynamic_res,
            "engine": "Local Student Domain Engine (English Enforced)",
            "persona": active_persona,
            "latency_ms": latency
        }

    def _build_student_prompt(
        self,
        query: str,
        intent: str,
        tool_executed: Optional[str],
        tool_data: Optional[Any],
        system_prompt: str,
        user_id: int = 1
    ) -> str:
        context_block = self._get_student_context_summary(user_id)

        if isinstance(tool_data, list):
            data_snippet = json.dumps({"total_items": len(tool_data), "top_entries": tool_data[:6]})
        elif tool_data:
            data_snippet = json.dumps(tool_data)
        else:
            data_snippet = "No specific tool execution data; refer to comprehensive student context below."

        now_dt = datetime.datetime.now()
        now_str = now_dt.strftime("%A, %b %d, %Y at %I:%M %p").lstrip("0")

        return (
            f"You are CampusLife Voice Assistant, an intelligent and articulate college mentor.\n"
            f"Respond exclusively in fluent, natural English with complete sentences and rich details.\n"
            f"Provide a thorough, comprehensive, and well-structured response based on the student's real-time academic context.\n"
            f"Explain everything clearly with full sentences and actionable recommendations. Never truncate mid-sentence.\n"
            f"Persona & Tone: {system_prompt}\n"
            f"Current Real-World Time: {now_str}\n\n"
            f"=== COMPREHENSIVE STUDENT CONTEXT ===\n"
            f"{context_block}\n\n"
            f"=== CONTEXTUAL TOOL SIGNALS ===\n"
            f"Intent: {intent}\n"
            f"Tool Executed: {tool_executed or 'None'}\n"
            f"Data: {data_snippet}\n\n"
            f"=== STUDENT QUERY ===\n"
            f"Student: '{query}'\n\n"
            f"Detailed, comprehensive English response:"
        )

    def _clean_llm_response(self, text: str) -> str:
        if not text:
            return ""
        clean = text.strip()
        echo_patterns = [
            r"^Current Real-World Local Time:\s*.*?\n",
            r"^Local Time:\s*.*?\n",
            r"^Student User:\s*['\"].*?['\"]\s*",
            r"^Student:\s*['\"].*?['\"]\s*",
            r"^Intent:\s*[A-Z_]+\s*",
            r"^Tool Executed:\s*[a-z_]+\s*",
            r"^Data:\s*.*?\n",
            r"^Contextual Database Signals:\s*.*?\n",
            r"^Short conversational English reply:\s*",
            r"^Detailed, comprehensive English response:\s*",
            r"^===.*?===\s*",
            r"^Respond concisely.*?\n"
        ]
        for pat in echo_patterns:
            clean = re.sub(pat, "", clean, flags=re.MULTILINE | re.IGNORECASE).strip()
        return clean

    def _call_ollama(self, prompt: str, system_prompt: str, model_name: str) -> Optional[str]:
        english_system_prompt = (
            f"{system_prompt} "
            "Respond exclusively in fluent, articulate English with full sentences and detailed explanations. Never cut off mid-sentence."
        )
        try:
            req_data = json.dumps({
                "model": model_name,
                "messages": [
                    {"role": "system", "content": english_system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "keep_alive": "60m",
                "options": {
                    "temperature": 0.3,
                    "num_predict": 450,
                    "num_ctx": 2048,
                    "num_thread": 8
                }
            }).encode('utf-8')

            req = urllib.request.Request(
                f"{self.local_url}/api/chat",
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=25.0) as res:
                if res.status == 200:
                    resp_json = json.loads(res.read().decode('utf-8'))
                    ans = resp_json.get("message", {}).get("content", "").strip()
                    if ans:
                        return self._clean_llm_response(ans)
        except Exception:
            pass

        # Try OpenAI-compatible endpoint on Ollama
        try:
            req_data = json.dumps({
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 450,
                "temperature": 0.5
            }).encode('utf-8')

            req = urllib.request.Request(
                f"{self.local_url}/v1/chat/completions",
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=8.0) as res:
                if res.status == 200:
                    resp_json = json.loads(res.read().decode('utf-8'))
                    ans = resp_json["choices"][0]["message"]["content"].strip()
                    if ans:
                        return self._clean_llm_response(ans)
        except Exception:
            pass

        return None

    def _call_openai(self, prompt: str, system_prompt: str) -> Optional[str]:
        try:
            req_data = json.dumps({
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 600,
                "temperature": 0.5
            }).encode('utf-8')

            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=req_data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
                }
            )
            with urllib.request.urlopen(req, timeout=5.0) as res:
                if res.status == 200:
                    resp_json = json.loads(res.read().decode('utf-8'))
                    ans = resp_json["choices"][0]["message"]["content"].strip()
                    if ans:
                        return self._clean_llm_response(ans)
        except Exception:
            return None
        return None

    def _dynamic_student_intelligence(
        self,
        query: str,
        intent: str,
        tool: Optional[str],
        data: Optional[Any],
        persona: str
    ) -> str:
        """
        Dynamically handles math calculations, queries, and student domain tools.
        """
        q = query.lower().strip()

        # A. Arithmetic / Math solver (e.g., "what is 1 + 1", "calculate 25 * 4")
        math_match = re.search(r"(\d+(?:\.\d+)?)\s*([\+\-\*\/])\s*(\d+(?:\.\d+)?)", q)
        if math_match:
            try:
                n1 = float(math_match.group(1))
                op = math_match.group(2)
                n2 = float(math_match.group(3))
                if op == '+': ans = n1 + n2
                elif op == '-': ans = n1 - n2
                elif op == '*': ans = n1 * n2
                elif op == '/': ans = n1 / n2 if n2 != 0 else "undefined"
                if isinstance(ans, float) and ans.is_integer():
                    ans = int(ans)
                return f"{int(n1) if n1.is_integer() else n1} {op} {int(n2) if n2.is_integer() else n2} = {ans}."
            except Exception:
                pass

        # B. User Profile / Account Questions (e.g. "what is the name of user", "who am I")
        if any(w in q for w in ["name of user", "who am i", "my name", "user name", "profile name", "user review"]):
            return "You are logged in as Alex Sharma (Student ID: alex@campuslife.ai), currently in 3rd Year B.Tech Computer Science."

        # C. Academic & Tasks
        if intent == "GET_TASKS":
            if not data or len(data) == 0:
                if persona == "PRODUCTIVITY_COACH":
                    return "Your task backlog is completely clear! Great moment to get ahead on upcoming readings or take a well-earned break."
                elif persona == "CAMPUS_PEER":
                    return "You're all clear on assignments! Time to chill or grab some coffee."
                return "You're all caught up! You currently have no pending academic tasks on your schedule."

            pending = [t for t in data if t.get("status") != "COMPLETED"]
            if not pending:
                return "All your scheduled tasks are completed. You're fully up to date on your syllabus!"

            top = pending[0]
            top_name = top.get("title", "Assignment")
            subj = top.get("subject", "your course")

            task_list_str = "\n".join([
                f"• '{t.get('title')}' for {t.get('subject', 'General')} — Priority: {t.get('priority', 'MEDIUM')}, Due: {t.get('due_date') or 'Flexible'}"
                for t in pending[:5]
            ])

            if persona == "PRODUCTIVITY_COACH":
                return (
                    f"You have {len(pending)} pending academic tasks on your roadmap:\n{task_list_str}\n\n"
                    f"Action Plan: Focus on '{top_name}' for {subj} first. Knock it out in a focused 45-minute sprint before moving to the next item!"
                )
            elif persona == "CAMPUS_PEER":
                return (
                    f"You've got {len(pending)} tasks to tackle on your list:\n{task_list_str}\n\n"
                    f"The biggest one to watch out for is '{top_name}' for {subj}. Let's get that knocked out early so you don't have to pull an all-nighter!"
                )
            return (
                f"You currently have {len(pending)} pending tasks on your study schedule:\n{task_list_str}\n\n"
                f"Your highest priority item is '{top_name}' for {subj}. Make sure to budget dedicated study time to complete it ahead of deadline."
            )

        elif intent == "GET_SCHEDULE":
            if isinstance(data, dict):
                classes = data.get("classes", [])
                day = data.get("day", "Today")
                date_str = data.get("date", "")
                tasks_cnt = data.get("pending_tasks_count", 0)
                pri_tasks = data.get("priority_tasks", [])

                class_lines = "\n".join([f"• {c['time']}: {c['course']} ({c['room']})" for c in classes]) if classes else "• No formal lectures scheduled today."
                task_line = f"You also have {tasks_cnt} active assignments on your radar."
                if pri_tasks:
                    top_t = pri_tasks[0]
                    task_line += f" Top priority: '{top_t.get('title')}' for {top_t.get('subject')} (Due: {top_t.get('due_date', 'Soon')})."

                if persona == "PRODUCTIVITY_COACH":
                    return (
                        f"Here is your daily battle plan for {day} ({date_str}):\n{class_lines}\n\n"
                        f"{task_line} Block out a 90-minute deep work sprint right after your final class session to knock this out early!"
                    )
                elif persona == "CAMPUS_PEER":
                    return (
                        f"Here is what your day looks like for {day}:\n{class_lines}\n\n"
                        f"{task_line} Let's power through lectures and tackle that assignment together so you can relax later tonight!"
                    )
                return (
                    f"Here is your complete academic schedule for {day} ({date_str}):\n{class_lines}\n\n"
                    f"{task_line} Make sure to allocate structured study time between classes."
                )
            return "Your academic timetable includes morning core lectures and an afternoon lab session, followed by dedicated evening study hours."

        elif intent == "CREATE_TASK":
            title = data.get("title", "New Task") if isinstance(data, dict) else "your task"
            priority = data.get("priority", "MEDIUM") if isinstance(data, dict) else "MEDIUM"
            if persona == "PRODUCTIVITY_COACH":
                return f"Locked and loaded! Added '{title}' with {priority} priority. Put it on your focus block."
            return f"I've added '{title}' to your task list with {priority} priority."

        elif intent == "COMPLETE_TASK":
            if isinstance(data, dict) and data.get("status") == "success":
                title = data.get("title", "your task")
                if persona == "PRODUCTIVITY_COACH":
                    return f"Crushed it! Marked '{title}' as completed. Keep this momentum rolling!"
                elif persona == "CAMPUS_PEER":
                    return f"Nice one! I've marked '{title}' as done. One less thing to stress about!"
                return f"Great job! I have marked '{title}' as completed in your study plan. Well done!"
            elif isinstance(data, dict) and data.get("status") == "not_found":
                return data.get("message", "I couldn't identify the task to complete.")
            return "I have updated your task list and marked that as completed!"

        elif intent == "EXTEND_DEADLINE":
            if isinstance(data, dict) and data.get("status") == "success":
                title = data.get("title", "your task")
                mins = data.get("minutes_added", 60)
                new_due = data.get("new_due_date", "later")
                if mins >= 60 and mins % 60 == 0:
                    time_desc = f"{mins // 60} hour{'s' if mins > 60 else ''}"
                else:
                    time_desc = f"{mins} minutes"
                if persona == "PRODUCTIVITY_COACH":
                    return f"Extended deadline for '{title}' by {time_desc} to {new_due}. Take a quick stretch and dive back in with focus!"
                return f"No problem! I've extended your deadline for '{title}' by {time_desc}. Your new deadline is {new_due}."
            return "I have extended the deadline for you. Take your time to finish it properly."

        elif intent == "CHANGE_PRIORITY":
            if isinstance(data, dict) and data.get("status") == "success":
                title = data.get("title", "your task")
                pri = data.get("priority", "HIGH")
                return f"Understood! I've changed the priority of '{title}' to {pri}."
            return "I have updated the priority for your task."

        elif intent == "GET_WELLNESS":
            if not data:
                return "Your wellness profile looks stable. Remember to get at least 7 to 8 hours of restorative rest tonight."
            sleep = data.get("average_sleep_7d", 7.0)
            stress = data.get("current_stress_level", "MODERATE")
            status = data.get("sleep_status", "NORMAL").replace("_", " ").lower()
            advice = data.get("wellness_advice", "Maintain regular sleep and study breaks.")

            if persona == "PRODUCTIVITY_COACH":
                return (
                    f"Biometric & Recovery Audit: Over the past 7 days, you have averaged {sleep:.1f} hours of sleep per night, classified as {status}. "
                    f"Your current stress level is {stress}. Performance insight: {advice} "
                    f"{'Warning: Sleep deficit is draining your cognitive focus. Prioritize getting to bed 60 minutes earlier tonight—sleep is your ultimate force multiplier!' if sleep < 6.5 else 'Excellent recovery baseline. Use this high energy to power through your core lectures!'}"
                )
            elif persona == "CAMPUS_PEER":
                return (
                    f"Wellness check-in: Over the last week, you've been averaging {sleep:.1f} hours of sleep each night, which is {status}. "
                    f"Your stress level is currently sitting at {stress}. Tip: {advice} "
                    f"{'You are definitely running on low sleep right now. Make sure to unwind early tonight and catch up on rest before exams!' if sleep < 6.5 else 'You are getting solid rest, which is awesome. Keep that up!'}"
                )
            return (
                f"Health & Wellness Assessment: Over the past 7 days, your average sleep duration is {sleep:.1f} hours per night ({status}). "
                f"Your current stress level is assessed as {stress}. Guidance: {advice} "
                f"{'Because your sleep is below the 7-hour threshold, please schedule an earlier bedtime to restore mental acuity.' if sleep < 6.5 else 'Your sleep schedule is well-balanced and supporting optimal academic performance.'}"
            )

        elif intent == "SET_BUDGET":
            if isinstance(data, dict) and data.get("status") == "success":
                t_type = data.get("target_type", "budget")
                bal = data.get("current_balance", 0.0)
                tot = data.get("total_budget", 0.0)
                spent = data.get("total_spent", 0.0)
                if persona == "PRODUCTIVITY_COACH":
                    if t_type == "balance":
                        return f"Balance logged! Your remaining funds are set to ₹{bal:,.2f}. Stay disciplined with your daily burn rate!"
                    return f"Budget locked at ₹{tot:,.2f}! Keep expenses tight and protect your runway."
                elif persona == "CAMPUS_PEER":
                    if t_type == "balance":
                        return f"All set! Updated your remaining balance to ₹{bal:,.2f}. You've got this for the rest of the month!"
                    return f"Done! Your monthly budget is now ₹{tot:,.2f}. Let's make sure we don't blow through it!"
                if t_type == "balance":
                    return f"I've updated your remaining balance to ₹{bal:,.2f} in your database. With ₹{spent:,.2f} already spent this month, your adjusted monthly budget is ₹{tot:,.2f}."
                return f"Done! Your monthly budget limit is now set to ₹{tot:,.2f}. After ₹{spent:,.2f} in current spending, your remaining balance is ₹{bal:,.2f}."
            return "I've successfully updated your budget settings in the database."

        elif intent == "GET_FINANCES":
            if not data:
                return "Your monthly budget is tracking within normal parameters with healthy reserves."
            spent = data.get("total_spent", 0.0)
            budget = data.get("budget_limit", 12000.0)
            rem = data.get("remaining", budget - spent)
            pct = data.get("utilization_percent", round((spent / budget * 100) if budget else 0, 1))
            runway = data.get("estimated_days_runway", 20)
            risk = data.get("financial_risk_level", "LOW")

            if persona == "PRODUCTIVITY_COACH":
                return (
                    f"Financial Status Report: You have spent ₹{spent:,.2f} out of your ₹{budget:,.2f} monthly budget ({pct}% utilized). "
                    f"Your remaining capital is ₹{rem:,.2f}, giving you approximately {runway} days of runway with a {risk} risk assessment. "
                    f"{'Action required: Trim discretionary dining and entertainment spending immediately to protect your end-of-month runway.' if runway < 10 else 'Keep your daily burn rate disciplined to finish the month in the green!'}"
                )
            elif persona == "CAMPUS_PEER":
                return (
                    f"Here is your money breakdown: You've spent ₹{spent:,.2f} of your ₹{budget:,.2f} budget so far ({pct}% used up). "
                    f"You still have ₹{rem:,.2f} left, which works out to about {runway} days of runway. "
                    f"{'Things are looking a bit tight for the rest of the month, so let us cut back on extra food orders.' if runway < 10 else 'You are pacing well—plenty of runway left for the rest of the month!'}"
                )
            return (
                f"Monthly Financial Overview: Total expenditure is ₹{spent:,.2f} against your ₹{budget:,.2f} monthly budget limit ({pct}% utilized). "
                f"Your remaining disposable balance is ₹{rem:,.2f}, providing an estimated {runway} days of runway. "
                f"{'Caution: Your financial runway is currently tight; consider limiting non-essential expenses.' if runway < 10 else 'Your financial health is currently stable and tracking within normal parameters.'}"
            )

        elif intent == "GET_TRIPS":
            if not data or len(data) == 0:
                return "You don't have any upcoming trips scheduled. Whenever you're ready for a break, let me know where you'd like to travel!"
            t = data[0]
            dest = t.get("destination", "your destination")
            start = t.get("start_date", "upcoming")
            if t.get("has_academic_conflict"):
                conf = t.get("conflicts", [{}])[0].get("title", "an exam")
                return f"You have a trip to {dest} scheduled for {start}. Warning: this directly overlaps with {conf}. We should reschedule or study in advance!"
            return f"You have an upcoming trip to {dest} planned from {start} to {t.get('end_date')}. No academic schedule conflicts detected."

        elif intent == "GET_INTELLIGENCE":
            if not data:
                return "Your student co-pilot indicators are all green. Keep up the consistent pace!"
            risk = data.get("compound_risk_level", "MODERATE")
            score = data.get("compound_risk_score", 0.0)
            insights = data.get("priority_insights", [])
            recs = [i.get("recommendation", "") for i in insights if i.get("recommendation")]
            rec_text = " ".join([f"• {r}" for r in recs[:2]]) if recs else "Maintain balanced study cycles and consistent sleep."

            return (
                f"Comprehensive CampusLife Student Intelligence Briefing: Your compound risk index is currently evaluated at {risk} ({score:.0f}/100). "
                f"Key strategic recommendations:\n{rec_text}\n\n"
                f"Focus on balancing imminent deadlines with adequate sleep recovery to keep your academic performance peak."
            )

        elif intent == "GET_TIME":
            now_dt = datetime.datetime.now()
            time_str = now_dt.strftime("%I:%M %p").lstrip("0")
            date_str = now_dt.strftime("%A, %B %d, %Y")
            return f"It is currently {time_str} on {date_str}."

        # D. General Conversational Fallback with Guidance
        if any(w in q for w in ["hello", "hi", "hey"]):
            return "Hey Alex! I'm here to help manage your semester. Ask me about tasks, your sleep baselines, budget runway, or any college question."
        elif "exam" in q or "study" in q:
            return "For upcoming exams, prioritize active recall and solve past papers in 45-minute blocks. What subject would you like to review first?"
        elif "stress" in q or "tired" in q or "exhausted" in q:
            return "Take a deep breath and give yourself a 15-minute break away from screens. Your health is the foundation of your performance."

        return (
            f"I received your question: '{query}'. "
            "To enable unrestricted local neural generation for arbitrary general knowledge, start your local Ollama server by running 'ollama run llama3.2'. "
            "For campus life, you can ask about your assignments, sleep, budget, or trips."
        )

local_student_llm = LocalStudentLLM()
