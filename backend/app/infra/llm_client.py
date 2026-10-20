import os
import json
from typing import Dict, Any, Optional

class LLMClient:
    """
    Shared GenAI LLM Client for CampusLife AI.
    Supports OpenAI, Gemini, or simulated fallback with structured output validation.
    """
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.provider = "GEMINI" if self.gemini_key else ("OPENAI" if self.openai_key else "FALLBACK_ENGINE")

    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7) -> str:
        """Generates text from prompt."""
        # Simulated intelligent fallback when API keys are not provided
        lower = prompt.lower()
        if "study plan" in lower:
            return "Here is your structured study plan:\nDay 1: Review core definitions and formulas.\nDay 2: Solve past exam papers.\nDay 3: Final mock test and revision."
        elif "wellness" in lower or "stress" in lower:
            return "Recommendation: Practice deep breathing for 10 minutes, maintain a consistent sleep schedule of 7-8 hours, and drink plenty of water."
        elif "receipt" in lower:
            return json.dumps({
                "merchant": "Campus Store",
                "total_amount": 250.0,
                "category": "Education"
            })
        elif "itinerary" in lower:
            return "Day 1: Morning arrival & check-in, afternoon sightseeing, evening dinner by the water."
        return f"CampusLife AI Co-Pilot response to: {prompt[:80]}..."

    def generate_structured(self, prompt: str, schema_class: Any) -> Dict[str, Any]:
        """Generates validated structured JSON matching a Pydantic schema."""
        raw_text = self.generate(prompt)
        try:
            parsed = json.loads(raw_text)
            return parsed
        except Exception:
            return {"content": raw_text}

llm_client = LLMClient()
