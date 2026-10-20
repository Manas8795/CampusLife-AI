from typing import List, Dict, Any
import datetime

class SemanticMemoryStore:
    """
    RAG & Semantic Memory Infrastructure for CampusLife AI.
    Stores and retrieves historical contextual snippets for personalized student intelligence.
    """

    def __init__(self):
        self._memory_cache: Dict[int, List[Dict[str, Any]]] = {}

    def store_memory(self, user_id: int, category: str, content: str, importance: float = 1.0):
        if user_id not in self._memory_cache:
            self._memory_cache[user_id] = []
        
        self._memory_cache[user_id].append({
            "category": category,
            "content": content,
            "importance": importance,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

    def retrieve_relevant_context(self, user_id: int, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        memories = self._memory_cache.get(user_id, [])
        if not memories:
            # Seed default semantic background
            return [
                {
                    "category": "ACADEMIC",
                    "content": "Alex typically performs well when revising in morning blocks and benefits from short Pomodoro breaks.",
                    "importance": 0.9
                },
                {
                    "category": "WELLNESS",
                    "content": "Baseline sleep is 7.5 hours. Historical fatigue and anxiety spike when sleep drops below 5.5 hours.",
                    "importance": 0.95
                },
                {
                    "category": "FINANCIAL",
                    "content": "Prefers to keep an emergency runway cushion of at least INR 2,000 towards the end of the month.",
                    "importance": 0.85
                }
            ]

        # Simple semantic relevance ranking based on keyword overlap
        q_words = set(query.lower().split())
        ranked = sorted(
            memories,
            key=lambda m: len(q_words.intersection(set(m["content"].lower().split()))) * m.get("importance", 1.0),
            reverse=True
        )
        return ranked[:top_k]

rag_memory = SemanticMemoryStore()
