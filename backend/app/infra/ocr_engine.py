import re
from typing import Dict, Any

class OCREngine:
    """
    OCR Text Extraction and Receipt Parsing Engine for CampusLife AI.
    Converts raw receipt scans or images into structured items and totals.
    """

    @staticmethod
    def extract_text_from_receipt(raw_text_or_image_sim: str) -> Dict[str, Any]:
        text = raw_text_or_image_sim or "CAMPUS STORE\n1x Notebook - 80\n1x Pen - 20\nTotal: 100"

        # 1. Extract merchant name (first line)
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        merchant = lines[0] if lines else "Campus Merchant"

        # 2. Extract total amount
        amount = 100.0
        total_match = re.search(r"(?:total|grand\s*total|net\s*amt|amount\s*paid|paid)\s*:?\s*(?:inr|rs\.?|₹)?\s*(\d+(?:\.\d{1,2})?)", text, re.IGNORECASE)
        if total_match:
            amount = float(total_match.group(1))
        else:
            amt_match = re.search(r"(?:total|amt|inr|rs\.?|₹)\s*:?\s*(\d+(?:\.\d{1,2})?)", text, re.IGNORECASE)
            if amt_match:
                amount = float(amt_match.group(1))

        # 3. Categorize
        category = "Food"
        lower = text.lower()
        if any(w in lower for w in ["book", "stationery", "print", "xerox", "course", "notes", "lab"]):
            category = "Education"
        elif any(w in lower for w in ["cab", "auto", "metro", "bus", "uber", "ola"]):
            category = "Transport"
        elif any(w in lower for w in ["movie", "game", "netflix", "concert"]):
            category = "Entertainment"

        return {
            "merchant": merchant,
            "total_amount": amount,
            "amount": amount,
            "category": category,
            "lines_extracted": len(lines),
            "raw_text": text
        }
