"""
Observer Pattern — Alert Notification System (Module 7)
=======================================================
Formally implements the GoF Observer Pattern for the proactive alert pipeline.

The AutonomousSentinelWatcher (Subject) fires alert events.
Each notification channel (WebSocket, Telegram, future: Email/SMS) is a
Concrete Observer that subscribes to the sentinel and reacts independently.

Adding a new channel (e.g. email) requires ONLY creating a new subclass —
the sentinel class itself never needs to change. (Open/Closed Principle — SOLID)

Class Hierarchy:
  AlertObserver (ABC)
    ├── WebSocketAlertObserver   ← sends call payload over WebSocket
    └── LogAlertObserver         ← records every alert in structured log

AlertEvent: typed dataclass carrying all alert metadata.
AlertSubject: mixin / base for the sentinel watcher.

Usage (in deadline_watcher.py):
  subject = AutonomousSentinelWatcher()
  subject.subscribe(WebSocketAlertObserver(mobile_call_manager))
  subject.subscribe(LogAlertObserver())
  await subject.notify(AlertEvent(...))
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("campuslife.alert_observer")


# ---------------------------------------------------------------------------
# Alert Event — carries structured data about a triggered alert
# ---------------------------------------------------------------------------
@dataclass
class AlertEvent:
    """
    Immutable data-transfer object representing one triggered alert.
    Passed to every registered observer so they have full context.
    """
    event_type: str                        # "DEADLINE" | "LOW_SLEEP" | "HEALTH_DEPRECIATION"
    call_id: str                           # Unique identifier for deduplication
    caller_name: str                       # Display name shown on mobile UI
    caller_subtitle: str                   # Short status line (e.g. "🚨 Deadline: Math HW")
    preview_text: str                      # Push-notification style preview
    greeting: str                          # Opening speech the AI reads to student
    payload: Dict[str, Any] = field(default_factory=dict)  # Extra data (task_id, sleep_hours, etc.)


# ---------------------------------------------------------------------------
# Abstract Observer
# ---------------------------------------------------------------------------
class AlertObserver(ABC):
    """
    Abstract observer interface. All notification channels implement this.
    """
    @abstractmethod
    async def on_alert(self, event: AlertEvent) -> None:
        """Called by the Subject whenever an alert condition is triggered."""
        ...


# ---------------------------------------------------------------------------
# Concrete Observer 1: WebSocket / Mobile UI broadcast
# ---------------------------------------------------------------------------
class WebSocketAlertObserver(AlertObserver):
    """
    Broadcasts the alert as a WebSocket INCOMING_CALL payload to the
    mobile_call_manager, triggering the 3D UI ringing screen on the student's device.
    """

    def __init__(self, call_manager):
        self._call_manager = call_manager

    async def on_alert(self, event: AlertEvent) -> None:
        call_payload = {
            "event": "INCOMING_CALL",
            "call_type": event.event_type,
            "caller_name": event.caller_name,
            "caller_subtitle": event.caller_subtitle,
            "preview_text": event.preview_text,
            "greeting": event.greeting,
            "call_id": event.call_id,
            **event.payload,
        }
        logger.info(
            "websocket_alert_dispatched",
            extra={"call_id": event.call_id, "event_type": event.event_type},
        )
        await self._call_manager.broadcast_call(call_payload)


# ---------------------------------------------------------------------------
# Concrete Observer 2: Structured Logger
# ---------------------------------------------------------------------------
class LogAlertObserver(AlertObserver):
    """
    Records every fired alert in the structured log for audit trail and monitoring.
    Zero external dependencies — always succeeds.
    """

    async def on_alert(self, event: AlertEvent) -> None:
        logger.info(
            "proactive_alert_fired",
            extra={
                "call_id": event.call_id,
                "event_type": event.event_type,
                "caller_name": event.caller_name,
                "preview": event.preview_text[:80],
            },
        )


# ---------------------------------------------------------------------------
# Alert Subject Mixin — used by AutonomousSentinelWatcher
# ---------------------------------------------------------------------------
class AlertSubject:
    """
    Subject (Publisher) mixin in the Observer Pattern.
    Maintains the list of registered observers and provides subscribe/notify APIs.
    """

    def __init__(self):
        self._observers: List[AlertObserver] = []

    def subscribe(self, observer: AlertObserver) -> None:
        """Register a new observer channel."""
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug(
                "observer_registered",
                extra={"observer": type(observer).__name__},
            )

    def unsubscribe(self, observer: AlertObserver) -> None:
        """Deregister an existing observer channel."""
        self._observers = [o for o in self._observers if o is not observer]

    async def notify(self, event: AlertEvent) -> None:
        """
        Broadcast an AlertEvent to all registered observers concurrently.
        Observer failures are isolated — one failing channel never blocks others.
        """
        tasks = [self._safe_notify(obs, event) for obs in self._observers]
        if tasks:
            await asyncio.gather(*tasks)

    @staticmethod
    async def _safe_notify(observer: AlertObserver, event: AlertEvent) -> None:
        try:
            await observer.on_alert(event)
        except Exception as exc:
            logger.error(
                "observer_notification_failed",
                extra={"observer": type(observer).__name__, "error": str(exc)},
            )
