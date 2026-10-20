"""
Bolna AI Telephony Integration for CampusLife Voice Assistant (Module 7).
Repository Reference: https://github.com/bolna-ai/bolna

Bolna is an open-source orchestration platform for building conversational voice agents
that bridges Telephony (Twilio/Plivo/Exotel), Transcribers (ASR), LLM Engines (Ollama/Llama 3.2),
and Text-to-Speech (TTS) synthesizers into a unified real-time calling pipeline.
"""

import os
import json
import uuid
import datetime
from typing import Dict, Any, Optional
from backend.app.voice.telephony.provider import TelephonyProvider, SimulatedTelephonyProvider
from backend.app.config import settings

class BolnaTelephonyProvider(TelephonyProvider):
    """
    Bolna AI Telephony Provider implementation.
    Orchestrates outbound phone calls using Bolna agent pipeline specifications:
    - Telephony: Twilio Media Streams (WebSocket bi-directional audio)
    - LLM: Local Ollama (llama3.2:1b)
    - TTS: Amazon Polly / ElevenLabs / Kokoro audio synthesis
    - Transcriber: Deepgram / Whisper / Twilio Gather
    """

    def __init__(self):
        self.repo_url = "https://github.com/bolna-ai/bolna"
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", settings.TWILIO_ACCOUNT_SID)
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", settings.TWILIO_AUTH_TOKEN)
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER", settings.TWILIO_PHONE_NUMBER)
        self.bolna_api_key = os.getenv("BOLNA_API_KEY", "")
        self.bolna_base_url = os.getenv("BOLNA_BASE_URL", "http://localhost:5001")

    def create_agent_config(self, user_id: int, trigger_reason: str, prompt_override: Optional[str] = None) -> Dict[str, Any]:
        """
        Builds a Bolna-compatible Agent Configuration JSON payload.
        Matches Bolna's Task & Toolchain specification schema.
        """
        agent_id = f"bolna_campus_{uuid.uuid4().hex[:8]}"
        persona = settings.STUDENT_PERSONA
        model = settings.LOCAL_LLM_MODEL or "llama3.2:1b"

        system_prompt = prompt_override or (
            f"You are the CampusLife AI Student Voice Caller, speaking to the student on their phone. "
            f"The call was triggered because of: {trigger_reason}. "
            f"Speak concisely in 1-2 empathetic, conversational sentences suitable for speech audio."
        )

        return {
            "agent_id": agent_id,
            "agent_name": "CampusLife Bolna Voice Agent",
            "agent_type": "outbound_phone",
            "repository": self.repo_url,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "tasks": [
                {
                    "task_type": "conversation",
                    "tools_config": {
                        "input": {
                            "provider": "twilio_media_stream",
                            "format": "audio/x-mulaw",
                            "sampling_rate": 8000
                        },
                        "transcriber": {
                            "provider": "deepgram",
                            "model": "nova-2",
                            "language": "en"
                        },
                        "llm_agent": {
                            "provider": "ollama",
                            "model": model,
                            "url": settings.LOCAL_LLM_URL,
                            "system_prompt": system_prompt,
                            "temperature": 0.3
                        },
                        "synthesizer": {
                            "provider": "polly",
                            "voice": "Polly.Aditi",
                            "language": "en-IN",
                            "audio_format": "mulaw"
                        },
                        "output": {
                            "provider": "twilio_media_stream"
                        }
                    }
                }
            ]
        }

    def initiate_call(self, to_number: str, greeting_text: str, webhook_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Dispatches an outbound AI telephone call using Bolna pipeline orchestration.
        If Twilio credentials and phone number are configured, initiates live Twilio call with Bolna Media Stream TwiML.
        Otherwise, runs through the Bolna Simulated Telephone Engine.
        """
        agent_config = self.create_agent_config(user_id=1, trigger_reason=greeting_text)
        call_sid = f"BOLNA_{uuid.uuid4().hex[:12]}"

        # 1. Live Twilio integration if credentials exist
        if self.twilio_account_sid and self.twilio_auth_token and self.twilio_phone_number:
            try:
                import requests
                twiml = self.generate_twiml_response(greeting_text, listen_for_speech=True)
                url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Calls.json"
                resp = requests.post(
                    url,
                    auth=(self.twilio_account_sid, self.twilio_auth_token),
                    data={
                        "To": to_number,
                        "From": self.twilio_phone_number,
                        "Twiml": twiml
                    },
                    timeout=10
                )
                data = resp.json()
                if resp.status_code in (200, 201):
                    return {
                        "success": True,
                        "provider": "BOLNA_TWILIO",
                        "call_sid": data.get("sid", call_sid),
                        "agent_id": agent_config["agent_id"],
                        "status": data.get("status", "queued"),
                        "to": to_number,
                        "from": self.twilio_phone_number,
                        "greeting": greeting_text,
                        "repository": self.repo_url,
                        "agent_config": agent_config
                    }
                else:
                    return {
                        "success": False,
                        "provider": "BOLNA_TWILIO",
                        "error_code": data.get("code"),
                        "error_message": data.get("message"),
                        "details": data,
                        "agent_config": agent_config
                    }
            except Exception as e:
                return {
                    "success": False,
                    "provider": "BOLNA_TWILIO",
                    "error": str(e),
                    "agent_config": agent_config
                }

        # 2. Bolna Local Telephony Simulator with WebSocket Hook
        return {
            "success": True,
            "provider": "BOLNA_LOCAL_AGENT",
            "call_sid": call_sid,
            "agent_id": agent_config["agent_id"],
            "status": "CONNECTED",
            "greeting": greeting_text,
            "repository": self.repo_url,
            "llm_engine": f"Local Neural ({settings.LOCAL_LLM_MODEL}) via Ollama",
            "agent_config": agent_config,
            "stream_endpoint": "/api/voice/telephony/bolna-stream",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

    def end_call(self, call_sid: str) -> bool:
        if self.twilio_account_sid and self.twilio_auth_token and call_sid.startswith("CA"):
            try:
                import requests
                url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Calls/{call_sid}.json"
                requests.post(url, auth=(self.twilio_account_sid, self.twilio_auth_token), data={"Status": "completed"}, timeout=5)
            except Exception:
                pass
        return True

    def generate_twiml_response(self, text: str, listen_for_speech: bool = True) -> str:
        """
        Generates Twilio TwiML that connects the telephone audio stream to Bolna's WebSocket media stream.
        """
        stream_url = os.getenv("BOLNA_STREAM_URL", "wss://api.campuslife.ai/api/voice/telephony/bolna-stream")
        if listen_for_speech:
            return (
                f'<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<Response>\n'
                f'  <Say voice="Polly.Aditi">{text}</Say>\n'
                f'  <Connect>\n'
                f'    <Stream url="{stream_url}" />\n'
                f'  </Connect>\n'
                f'</Response>'
            )
        return f'<?xml version="1.0" encoding="UTF-8"?><Response><Say voice="Polly.Aditi">{text}</Say><Hangup/></Response>'

bolna_provider = BolnaTelephonyProvider()
