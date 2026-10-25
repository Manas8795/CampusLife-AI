"""
Command Pattern — Voice Intent Dispatcher (Module 7)
====================================================
Formally implements the GoF Command Pattern for the voice agent intent pipeline.

Each intent (LOG_EXPENSE, CREATE_TASK, etc.) is a self-contained Command object
encapsulating execution, logging, and undo capability. Adding a new intent requires
ONLY creating a new Command subclass and registering it in INTENT_REGISTRY —
the process_turn() caller never needs to change. (Open/Closed Principle — SOLID)

Class Hierarchy:
  IntentCommand (ABC)
    ├── LogExpenseCommand
    ├── SetBudgetCommand
    ├── CreateTaskCommand
    ├── CreateTripCommand
    ├── CompleteTaskCommand
    ├── ExtendDeadlineCommand
    ├── ChangePriorityCommand
    ├── LogSleepCommand
    ├── GetTasksCommand
    ├── GetWellnessCommand
    ├── GetFinancesCommand
    ├── GetTripsCommand
    ├── GetIntelligenceCommand
    ├── GetTimeCommand
    ├── ConfirmActionCommand
    └── CancelActionCommand

INTENT_REGISTRY: Dict[str, Type[IntentCommand]] — maps intent strings to classes.

Usage (in agent.py):
  command_cls = INTENT_REGISTRY.get(intent)
  if command_cls:
      result = command_cls().execute(user_id, params)
"""

import datetime
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

from backend.app.tools import campuslife_tools

logger = logging.getLogger("campuslife.intent_command")


# ---------------------------------------------------------------------------
# Abstract Command
# ---------------------------------------------------------------------------
class IntentCommand(ABC):
    """
    Abstract command interface for all voice intents.
    Concrete subclasses encapsulate the tool call and return a uniform result dict.
    """

    @abstractmethod
    def execute(self, user_id: int, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute the intent for the given user with extracted parameters.
        Returns tool_data dict or None if no tool was invoked.
        """
        ...

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Identifier of the campuslife_tool that this command wraps."""
        ...


# ---------------------------------------------------------------------------
# Concrete Commands — Mutation Intents (write to database)
# ---------------------------------------------------------------------------

class LogExpenseCommand(IntentCommand):
    """Records a new student expense entry in the database."""

    @property
    def tool_name(self) -> str:
        return "log_expense"

    def execute(self, user_id: int, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        logger.info("command_execute", extra={"command": self.tool_name, "user_id": user_id})
        return campuslife_tools.log_expense(
            user_id,
            amount=float(params.get("amount", 0.0)),
            category=params.get("category", "Other"),
            description=params.get("description", ""),
            merchant=params.get("merchant", "Direct Entry"),
            payment_method=params.get("payment_method", "UPI"),
        )


class SetBudgetCommand(IntentCommand):
    """Updates the student's monthly budget or remaining balance."""

    @property
    def tool_name(self) -> str:
        return "set_budget"

    def execute(self, user_id: int, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        logger.info("command_execute", extra={"command": self.tool_name, "user_id": user_id})
        return campuslife_tools.set_budget(
            user_id,
            amount=float(params.get("amount", 0.0)),
            target_type=params.get("target_type", "budget"),
        )


class CreateTaskCommand(IntentCommand):
    """Creates a new academic task with optional deadline and priority."""

    @property
    def tool_name(self) -> str:
        return "create_task"

    def execute(self, user_id: int, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        logger.info("command_execute", extra={"command": self.tool_name, "user_id": user_id})
        return campuslife_tools.create_task(
            user_id,
            title=params.get("title", "Study Session"),
            priority=params.get("priority", "MEDIUM"),
            subject=params.get("subject", "General"),
            due_date=params.get("due_date"),
        )


class CreateTripCommand(IntentCommand):
    """Creates a new travel trip plan for the student."""

    @property
    def tool_name(self) -> str:
        return "create_trip"

    def execute(self, user_id: int, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        logger.info("command_execute", extra={"command": self.tool_name, "user_id": user_id})
        return campuslife_tools.create_trip(
            user_id,
            destination=params.get("destination", "New Trip"),
            budget=float(params.get("budget", 5000.0)),
        )


class CompleteTaskCommand(IntentCommand):
    """Marks a student task as completed using fuzzy/semantic matching."""

    @property
    def tool_name(self) -> str:
        return "complete_task"

    def execute(self, user_id: int, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        target = params.get("target", "")
        logger.info("command_execute", extra={"command": self.tool_name, "user_id": user_id, "target": target})
        return campuslife_tools.complete_task_flexible(user_id, target)


class ExtendDeadlineCommand(IntentCommand):
    """Extends the deadline of a specified task by a number of minutes."""

    @property
    def tool_name(self) -> str:
        return "extend_task_deadline"

    def execute(self, user_id: int, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        minutes = params.get("minutes", 60)
        target = params.get("target", "")
        logger.info("command_execute", extra={"command": self.tool_name, "user_id": user_id, "minutes": minutes})
        return campuslife_tools.extend_task_deadline(user_id, target, minutes)


class ChangePriorityCommand(IntentCommand):
    """Updates the priority level of an existing task."""

    @property
    def tool_name(self) -> str:
        return "update_task_priority"

    def execute(self, user_id: int, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        priority = params.get("priority", "HIGH")
        target = params.get("target", "")
        logger.info("command_execute", extra={"command": self.tool_name, "user_id": user_id, "priority": priority})
        return campuslife_tools.update_task_priority(user_id, target, priority)


class LogSleepCommand(IntentCommand):
    """Logs a sleep and wellness entry for the current day."""

    @property
    def tool_name(self) -> str:
        return "log_sleep"

    def execute(self, user_id: int, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        logger.info("command_execute", extra={"command": self.tool_name, "user_id": user_id})
        sleep_val = float(params.get("sleep_hours") if params.get("sleep_hours") is not None else params.get("hours", 7.0))
        return campuslife_tools.log_sleep(
            user_id,
            sleep_hours=sleep_val,
            mood=int(params.get("mood", 4)),
            energy=int(params.get("energy", 4)),
            notes=params.get("notes", ""),
        )


# ---------------------------------------------------------------------------
# Concrete Commands — Query Intents (read from database)
# ---------------------------------------------------------------------------

class GetTasksCommand(IntentCommand):
    """Retrieves the student's pending and recent academic tasks."""

    @property
    def tool_name(self) -> str:
        return "get_tasks"

    def execute(self, user_id: int, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return campuslife_tools.get_tasks(user_id)


class GetWellnessCommand(IntentCommand):
    """Fetches the student's wellness summary (sleep, stress, energy)."""

    @property
    def tool_name(self) -> str:
        return "get_wellness_state"

    def execute(self, user_id: int, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return campuslife_tools.get_wellness_state(user_id)


class GetFinancesCommand(IntentCommand):
    """Retrieves the student's monthly expense summary and budget runway."""

    @property
    def tool_name(self) -> str:
        return "get_expenses_summary"

    def execute(self, user_id: int, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return campuslife_tools.get_expenses_summary(user_id)


class GetTripsCommand(IntentCommand):
    """Fetches upcoming trips and checks for academic schedule conflicts."""

    @property
    def tool_name(self) -> str:
        return "get_upcoming_trips"

    def execute(self, user_id: int, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return campuslife_tools.get_upcoming_trips(user_id)


class GetIntelligenceCommand(IntentCommand):
    """Runs the full cross-domain student intelligence state evaluation."""

    @property
    def tool_name(self) -> str:
        return "get_student_intelligence"

    def execute(self, user_id: int, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return campuslife_tools.get_student_intelligence(user_id)


class GetTimeCommand(IntentCommand):
    """Returns the current local date and time — no DB call required."""

    @property
    def tool_name(self) -> str:
        return "get_current_time"

    def execute(self, user_id: int, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        now_dt = datetime.datetime.now()
        return {
            "current_time": now_dt.strftime("%I:%M %p").lstrip("0"),
            "current_date": now_dt.strftime("%A, %B %d, %Y"),
            "formatted": now_dt.strftime("%I:%M %p").lstrip("0") + " on " + now_dt.strftime("%A, %B %d, %Y"),
        }


class GetScheduleCommand(IntentCommand):
    """Retrieves the student's daily timetable, lecture halls, and pending deliverables."""

    @property
    def tool_name(self) -> str:
        return "get_student_schedule"

    def execute(self, user_id: int, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return campuslife_tools.get_student_schedule(user_id)


class ConfirmActionCommand(IntentCommand):
    """Handles user confirmation of a pending action."""

    @property
    def tool_name(self) -> str:
        return "confirm_action"

    def execute(self, user_id: int, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return {"status": "CONFIRMED"}


class CancelActionCommand(IntentCommand):
    """Handles user cancellation of a pending action."""

    @property
    def tool_name(self) -> str:
        return "cancel_action"

    def execute(self, user_id: int, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return {"status": "CANCELLED"}


# ---------------------------------------------------------------------------
# Intent Registry — maps intent string → Command class
# ---------------------------------------------------------------------------
INTENT_REGISTRY: Dict[str, Type[IntentCommand]] = {
    # Mutation commands
    "LOG_EXPENSE":      LogExpenseCommand,
    "SET_BUDGET":       SetBudgetCommand,
    "CREATE_TASK":      CreateTaskCommand,
    "CREATE_TRIP":      CreateTripCommand,
    "COMPLETE_TASK":    CompleteTaskCommand,
    "EXTEND_DEADLINE":  ExtendDeadlineCommand,
    "CHANGE_PRIORITY":  ChangePriorityCommand,
    "LOG_SLEEP":        LogSleepCommand,
    # Query commands
    "GET_TASKS":        GetTasksCommand,
    "GET_WELLNESS":     GetWellnessCommand,
    "GET_FINANCES":     GetFinancesCommand,
    "GET_TRIPS":        GetTripsCommand,
    "GET_INTELLIGENCE": GetIntelligenceCommand,
    "GET_TIME":         GetTimeCommand,
    "GET_SCHEDULE":     GetScheduleCommand,
    # Confirmation commands
    "CONFIRM_ACTION":   ConfirmActionCommand,
    "CANCEL_ACTION":    CancelActionCommand,
}


def execute_intent(
    intent: str,
    user_id: int,
    params: Dict[str, Any],
) -> tuple[Optional[str], Optional[Any]]:
    """
    Registry-based dispatcher: look up the Command class for an intent,
    instantiate it, and call execute(). Returns (tool_name, tool_data).

    This is the single replacement for the original 15-branch if/elif chain
    in VoiceAgent.process_turn(). Extending with a new intent requires zero
    changes here — only a new Command subclass + INTENT_REGISTRY entry.
    """
    command_cls = INTENT_REGISTRY.get(intent)
    if command_cls is None:
        return None, None
    command = command_cls()
    tool_data = command.execute(user_id, params)
    return command.tool_name, tool_data
