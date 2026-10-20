"""
Telegram Voice & Speech Telephony Integration for CampusLife Voice Assistant.
Delivers real-time neural speech notes and two-way voice companion calls
directly to the student's physical phone via Telegram.
"""

import os
import io
import asyncio
import tempfile
import requests
from typing import Dict, Any, Optional, List
import edge_tts
from backend.app.config import settings

class TelegramVoiceService:
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = settings.TELEGRAM_CHAT_ID or os.getenv("TELEGRAM_CHAT_ID", "")

    def get_api_url(self, method: str, token: Optional[str] = None) -> str:
        tok = token or self.bot_token
        base = getattr(settings, "TELEGRAM_API_BASE", "https://api.telegram.org").rstrip("/")
        return f"{base}/bot{tok}/{method}"

    def get_request_proxies(self) -> Optional[Dict[str, str]]:
        proxy = getattr(settings, "TELEGRAM_PROXY", "")
        if proxy:
            return {"http": proxy, "https": proxy}
        return None

    def verify_bot(self, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Validates the Telegram bot token with Telegram's getMe API.
        """
        tok = token or self.bot_token
        if not tok:
            return {"valid": False, "error": "No Telegram bot token provided"}
        try:
            r = requests.get(self.get_api_url("getMe", tok), proxies=self.get_request_proxies(), timeout=4)
            data = r.json()
            if data.get("ok"):
                return {
                    "valid": True,
                    "bot_name": data["result"].get("first_name"),
                    "username": data["result"].get("username"),
                    "bot_id": data["result"].get("id")
                }
            return {"valid": False, "error": data.get("description", "Invalid token")}
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
            return {
                "valid": False,
                "error": "ISP Network Blocked: api.telegram.org timed out. Your local ISP is dropping Telegram traffic. Use Cloudflare WARP/VPN or a reverse proxy."
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def detect_chat_id(self, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Polls getUpdates to automatically find the student's Chat ID
        once they click /start or send any message to the bot from their phone.
        """
        tok = token or self.bot_token
        if not tok:
            return {"success": False, "error": "Bot token required"}
        try:
            r = requests.get(self.get_api_url("getUpdates", tok), proxies=self.get_request_proxies(), timeout=4)
            data = r.json()
            if not data.get("ok"):
                return {"success": False, "error": data.get("description", "Failed to get updates")}
            
            updates = data.get("result", [])
            if not updates:
                return {
                    "success": False,
                    "chat_id": None,
                    "message": "No messages received yet. Please open your bot in Telegram on your phone and tap 'Start' or send a message."
                }

            # Get the latest message's chat
            latest = updates[-1]
            chat = latest.get("message", {}).get("chat", {})
            user_chat_id = str(chat.get("id"))
            username = chat.get("username") or chat.get("first_name", "Student")

            if user_chat_id:
                self.chat_id = user_chat_id
                return {
                    "success": True,
                    "chat_id": user_chat_id,
                    "user_name": username,
                    "message": f"Connected to {username} (Chat ID: {user_chat_id})"
                }
            return {"success": False, "error": "Could not extract chat_id from recent update"}
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
            return {
                "success": False,
                "error": "ISP Network Blocked: api.telegram.org timed out. Your local ISP is dropping Telegram traffic. Use Cloudflare WARP/VPN or a reverse proxy."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def generate_speech_audio(self, text: str, voice: str = "en-US-JennyNeural") -> bytes:
        """
        Generates high-definition neural speech audio using Edge TTS.
        """
        communicate = edge_tts.Communicate(text, voice)
        audio_stream = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])
        return audio_stream.getvalue()

    def send_voice_call(
        self,
        text: str,
        chat_id: Optional[str] = None,
        token: Optional[str] = None,
        voice: str = "en-US-JennyNeural"
    ) -> Dict[str, Any]:
        """
        Synthesizes the proactive intervention or AI co-pilot reply as neural speech
        and delivers it directly as an official Telegram Voice Note to the student's phone.
        """
        tok = token or self.bot_token
        target_chat = chat_id or self.chat_id

        if not tok or not target_chat:
            return {
                "success": False,
                "error": "Missing bot_token or chat_id. Please configure your Telegram bot first."
            }

        try:
            # 1. Synthesize audio
            audio_bytes = asyncio.run(self.generate_speech_audio(text, voice=voice))
            
            # 2. Post as Voice Message to Telegram API
            caption = f"🎙️ CampusLife AI Voice Companion:\n\"{text[:200]}...\"" if len(text) > 200 else f"🎙️ CampusLife AI Voice Companion:\n\"{text}\""
            
            url = self.get_api_url("sendVoice", tok)
            files = {
                "voice": ("voice.mp3", audio_bytes, "audio/mpeg")
            }
            data = {
                "chat_id": target_chat,
                "caption": caption
            }

            r = requests.post(url, data=data, files=files, proxies=self.get_request_proxies(), timeout=6)
            res = r.json()

            if res.get("ok"):
                return {
                    "success": True,
                    "message_id": res["result"]["message_id"],
                    "chat_id": target_chat,
                    "speech_length_bytes": len(audio_bytes),
                    "caption": caption,
                    "status": "DELIVERED_TO_PHONE"
                }
            else:
                return {
                    "success": False,
                    "error": res.get("description", "Failed to send voice message")
                }
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
            return {
                "success": False,
                "error": "ISP Network Blocked: api.telegram.org timed out. Your local ISP is dropping Telegram traffic."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_text_message(self, text: str, chat_id: Optional[str] = None) -> Dict[str, Any]:
        target_chat = chat_id or self.chat_id
        if not self.bot_token or not target_chat:
            return {"success": False, "error": "Missing credentials"}
        try:
            r = requests.post(
                self.get_api_url("sendMessage"),
                json={"chat_id": target_chat, "text": text, "parse_mode": "Markdown"},
                proxies=self.get_request_proxies(),
                timeout=4
            )
            return r.json()
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
            return {
                "success": False,
                "error": "ISP Network Blocked: api.telegram.org timed out. Your local ISP is dropping Telegram traffic."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

telegram_voice = TelegramVoiceService()
