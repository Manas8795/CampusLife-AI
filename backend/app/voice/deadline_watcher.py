"""
Autonomous Sentinel Watcher — Deadline & Wellness Monitor (Module 7)
====================================================================
Continuously monitors the student's academic deadlines, sleep, and wellness
and fires proactive alert calls via the Observer Pattern notification pipeline.

SE Improvements Applied:
  1. Observer Pattern: Inherits AlertSubject mixin — all notification channels
     (WebSocket, log) are registered observers rather than hardcoded calls.
     Adding a new channel (Telegram, email) requires ZERO changes here.
  2. State Persistence Bug Fix: Notified alert IDs are now stored in the
     database (AlertLog table) instead of in-memory Python sets. This means
     re-triggering after server restart is prevented correctly.

Monitoring Loop Cadence: every 4 seconds.
Alert Types:
  - DEADLINE: task.due_date has passed and task is PENDING/OVERDUE
  - LOW_SLEEP: most recent HealthRecord has sleep_hours < 6.0
  - HEALTH_DEPRECIATION: high stress score OR mood+energy critically low
"""

import asyncio
import datetime
import logging
from typing import Optional

from backend.app.database import SessionLocal
from backend.app.study.models import Task
from backend.app.health.models import HealthRecord
from backend.app.voice.router import mobile_call_manager
from backend.app.voice.alert_observer import (
    AlertSubject,
    AlertEvent,
    WebSocketAlertObserver,
    LogAlertObserver,
)

logger = logging.getLogger("campuslife.autonomous_sentinel")


# ---------------------------------------------------------------------------
# Persistent Alert Log helpers
# Stores which alert IDs have already been fired in the DB to survive restarts.
# ---------------------------------------------------------------------------

def _has_been_notified(db, alert_key: str) -> bool:
    """Check if an alert with this key has already been fired (DB-backed)."""
    from sqlalchemy import text
    try:
        result = db.execute(
            text("SELECT 1 FROM sentinel_alert_log WHERE alert_key = :k LIMIT 1"),
            {"k": alert_key},
        ).fetchone()
        return result is not None
    except Exception:
        # Table may not exist yet — create it and return False
        _ensure_alert_log_table(db)
        return False


def _mark_notified(db, alert_key: str) -> None:
    """Record that an alert has been fired (DB-backed)."""
    from sqlalchemy import text
    try:
        db.execute(
            text(
                "INSERT OR IGNORE INTO sentinel_alert_log (alert_key, fired_at) "
                "VALUES (:k, :t)"
            ),
            {"k": alert_key, "t": datetime.datetime.utcnow().isoformat()},
        )
        db.commit()
    except Exception as exc:
        logger.warning("alert_log_write_failed", extra={"error": str(exc)})


def _unmark_notified(db, alert_key: str) -> None:
    """Remove a notification record (e.g. task extended back into future)."""
    from sqlalchemy import text
    try:
        db.execute(
            text("DELETE FROM sentinel_alert_log WHERE alert_key = :k"),
            {"k": alert_key},
        )
        db.commit()
    except Exception:
        pass


def _ensure_alert_log_table(db) -> None:
    """Creates the sentinel_alert_log table if it does not yet exist."""
    from sqlalchemy import text
    try:
        db.execute(text(
            "CREATE TABLE IF NOT EXISTS sentinel_alert_log ("
            "  alert_key TEXT PRIMARY KEY, "
            "  fired_at  TEXT NOT NULL"
            ")"
        ))
        db.commit()
    except Exception as exc:
        logger.error("alert_log_table_creation_failed", extra={"error": str(exc)})


# ---------------------------------------------------------------------------
# Autonomous Sentinel Watcher (Subject in Observer Pattern)
# ---------------------------------------------------------------------------

class AutonomousSentinelWatcher(AlertSubject):
    """
    Continuous real-time autonomous sentinel that monitors:
    1. Task Deadlines    — alerts when an assignment deadline hits.
    2. Low Sleep         — alerts when sleep drops critically low (< 6.0 hours).
    3. Health Burnout    — alerts when stress is high or energy/mood crash.

    Inherits AlertSubject to support multiple registered notification observers.
    Uses DB-backed alert log (sentinel_alert_log) to prevent duplicate firing
    across server restarts (fixes the previous in-memory Set bug).
    """

    def __init__(self):
        super().__init__()
        self.is_running: bool = False

    async def start(self):
        """
        Main monitoring loop. Registers observers and starts the 4-second
        polling cycle. Called once from FastAPI startup event.
        """
        # Register all notification channels (Observer Pattern)
        self.subscribe(WebSocketAlertObserver(mobile_call_manager))
        self.subscribe(LogAlertObserver())

        # Ensure persistence table exists
        with SessionLocal() as db:
            _ensure_alert_log_table(db)

        self.is_running = True
        logger.info("sentinel_started", extra={"observers": len(self._observers)})

        while self.is_running:
            try:
                await self._check_deadlines()
                await self._check_sleep_and_health()
            except Exception as exc:
                logger.error("sentinel_loop_error", extra={"error": str(exc)})
            await asyncio.sleep(4)

    # ------------------------------------------------------------------
    # Check 1: Task Deadlines
    # ------------------------------------------------------------------
    async def _check_deadlines(self):
        now = datetime.datetime.now()
        with SessionLocal() as db:
            tasks = db.query(Task).filter(Task.due_date.isnot(None)).all()

            for task in tasks:
                alert_key = f"DEADLINE_{task.id}"

                # Reset if task was completed or deadline pushed to the future
                if task.status == "COMPLETED" or task.due_date > now:
                    _unmark_notified(db, alert_key)
                    continue

                # Fire alert if deadline has passed and not yet notified
                if task.due_date <= now and task.status in ("PENDING", "OVERDUE"):
                    if not _has_been_notified(db, alert_key):
                        _mark_notified(db, alert_key)
                        task.status = "OVERDUE"
                        db.commit()

                        event = AlertEvent(
                            event_type="DEADLINE",
                            call_id=f"CALL_DEADLINE_{task.id}",
                            caller_name="CampusLife Co-Pilot",
                            caller_subtitle=f"🚨 Deadline Expired: {task.title}",
                            preview_text=(
                                f"Deadline alert for '{task.title}'. "
                                "Tap Accept Call to connect with your 3D AI mentor."
                            ),
                            greeting=(
                                f"Hello! Your deadline for '{task.title}' has just arrived. "
                                "Have you completed this task, or would you like to extend "
                                "your deadline or adjust its priority?"
                            ),
                            payload={"task_id": task.id, "task_title": task.title},
                        )
                        logger.info(
                            "deadline_alert_triggered",
                            extra={"task_id": task.id, "task_title": task.title},
                        )
                        await self.notify(event)

    # ------------------------------------------------------------------
    # Check 2: Sleep Deprivation & Health Burnout
    # ------------------------------------------------------------------
    async def _check_sleep_and_health(self):
        with SessionLocal() as db:
            recent = db.query(HealthRecord).order_by(HealthRecord.id.desc()).first()
            if not recent:
                return

            # 2a. Critical Sleep Deprivation (< 6.0 hours)
            if recent.sleep_hours and recent.sleep_hours < 6.0:
                alert_key = f"LOW_SLEEP_{recent.id}"
                if not _has_been_notified(db, alert_key):
                    _mark_notified(db, alert_key)
                    sleep_h = round(recent.sleep_hours, 1)
                    event = AlertEvent(
                        event_type="LOW_SLEEP",
                        call_id=f"CALL_SLEEP_{recent.id}",
                        caller_name="CampusLife Health Sentinel",
                        caller_subtitle=f"🌙 Critical Sleep Deficit: {sleep_h}h",
                        preview_text=(
                            f"Sleep Alert: Only {sleep_h} hours recorded. "
                            "Tap Accept Call to adjust your recovery plan."
                        ),
                        greeting=(
                            f"Hello! CampusLife Health Sentinel detected your sleep was only {sleep_h} hours. "
                            "Your cognitive recovery and focus are at critical risk. Let's adjust your study "
                            "schedule today so you can wind down and sleep early tonight."
                        ),
                        payload={"sleep_hours": sleep_h},
                    )
                    logger.info(
                        "sleep_alert_triggered",
                        extra={"sleep_hours": sleep_h, "record_id": recent.id},
                    )
                    await self.notify(event)
                return

            # 2b. Health & Burnout Depreciation (High Stress or Vitals Crash)
            is_depreciating = (
                recent.stress_level == "HIGH"
                or (recent.stress_score and recent.stress_score >= 0.65)
                or (
                    recent.mood is not None
                    and recent.energy_level is not None
                    and recent.mood <= 2
                    and recent.energy_level <= 2
                )
            )
            if is_depreciating:
                alert_key = f"HEALTH_{recent.id}"
                if not _has_been_notified(db, alert_key):
                    _mark_notified(db, alert_key)
                    event = AlertEvent(
                        event_type="HEALTH_DEPRECIATION",
                        call_id=f"CALL_HEALTH_{recent.id}",
                        caller_name="CampusLife Wellness Sentinel",
                        caller_subtitle="⚠️ Health Depreciating: High Stress",
                        preview_text=(
                            "Wellness Warning: High fatigue and stress detected. "
                            "Tap Accept Call to protect your recovery."
                        ),
                        greeting=(
                            "Hello! Your wellness telemetry indicates your physical and mental energy "
                            "are critically depleted with elevated stress. Please pause what you are doing, "
                            "take a 15-minute breather, and let's reschedule non-urgent deadlines to protect your health."
                        ),
                        payload={},
                    )
                    logger.info(
                        "health_alert_triggered",
                        extra={"record_id": recent.id},
                    )
                    await self.notify(event)


deadline_watcher = AutonomousSentinelWatcher()
