from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os
import json
import uuid
import datetime

class TelephonyProvider(ABC):
    @abstractmethod
    def initiate_call(self, to_number: str, greeting_text: str, webhook_url: Optional[str] = None) -> Dict[str, Any]:
        """Initiates an outbound phone call."""
        pass

    @abstractmethod
    def end_call(self, call_sid: str) -> bool:
        """Terminates an active phone call."""
        pass

    @abstractmethod
    def generate_twiml_response(self, text: str, listen_for_speech: bool = True) -> str:
        """Generates TwiML for speech interaction."""
        pass

class SimulatedTelephonyProvider(TelephonyProvider):
    """
    In-memory simulated telephony provider for testing and browser demo.
    Simulates ringing, connect, speech turns, and hangup without requiring Twilio credentials.
    """
    def initiate_call(self, to_number: str, greeting_text: str, webhook_url: Optional[str] = None) -> Dict[str, Any]:
        call_sid = f"SIM_{uuid.uuid4().hex[:12]}"
        return {
            "success": True,
            "provider": "SIMULATED",
            "call_sid": call_sid,
            "status": "RINGING",
            "greeting": greeting_text,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

    def end_call(self, call_sid: str) -> bool:
        return True

    def generate_twiml_response(self, text: str, listen_for_speech: bool = True) -> str:
        if listen_for_speech:
            return f'<?xml version="1.0" encoding="UTF-8"?><Response><Say voice="Polly.Aditi">{text}</Say><Gather input="speech" timeout="5" action="/api/voice/webhooks/twilio" method="POST"/></Response>'
        return f'<?xml version="1.0" encoding="UTF-8"?><Response><Say voice="Polly.Aditi">{text}</Say><Hangup/></Response>'

class TwilioProvider(TelephonyProvider):
    """
    Production Twilio telephony provider using Twilio REST API.
    Gracefully falls back to simulation if credentials are not configured.
    """
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")

    def is_configured(self) -> bool:
        return bool(self.account_sid and self.auth_token and self.from_number)

    def initiate_call(self, to_number: str, greeting_text: str, webhook_url: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_configured():
            # Graceful fallback to simulation
            sim = SimulatedTelephonyProvider()
            res = sim.initiate_call(to_number, greeting_text, webhook_url)
            res["provider"] = "SIMULATED (Twilio credentials not configured in env)"
            return res

        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            twiml = self.generate_twiml_response(greeting_text, listen_for_speech=True)
            call = client.calls.create(
                to=to_number,
                from_=self.from_number,
                twiml=twiml
            )
            return {
                "success": True,
                "provider": "TWILIO",
                "call_sid": call.sid,
                "status": call.status,
                "greeting": greeting_text
            }
        except Exception as e:
            return {
                "success": False,
                "provider": "TWILIO",
                "error": str(e)
            }

    def end_call(self, call_sid: str) -> bool:
        if not self.is_configured():
            return True
        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            client.calls(call_sid).update(status="completed")
            return True
        except Exception:
            return False

    def generate_twiml_response(self, text: str, listen_for_speech: bool = True) -> str:
        if listen_for_speech:
            return f'<?xml version="1.0" encoding="UTF-8"?><Response><Say voice="Polly.Aditi">{text}</Say><Gather input="speech" timeout="5" action="/api/voice/webhooks/twilio" method="POST"/></Response>'
        return f'<?xml version="1.0" encoding="UTF-8"?><Response><Say voice="Polly.Aditi">{text}</Say><Hangup/></Response>'
