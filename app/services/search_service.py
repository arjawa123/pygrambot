import re
import logging
from app.db import Database
from typing import List, Tuple

logger = logging.getLogger(__name__)

class SearchService:
    @staticmethod
    def extract_keywords(query: str) -> List[str]:
        """Simple keyword extractor from a user question."""
        # Remove common stopwords and symbols
        clean = re.sub(r'[^a-zA-Z0-9\s]', '', query).lower()
        words = clean.split()
        # Only keep words longer than 3 chars for better matching
        return [w for w in words if len(w) > 3]

    @classmethod
    async def find_relevant_files(cls, chat_id: int, user_query: str, limit: int = 3) -> List[Tuple]:
        """Finds files related to the user's question by matching keywords."""
        keywords = cls.extract_keywords(user_query)
        if not keywords:
            # Fallback to recent files if no specific keywords found
            return await Database.get_recent_files(chat_id, 2)
        
        # We try to search for the most significant keyword first
        # In a real RAG system, we'd use embeddings. Here we use LIKE query.
        results = []
        seen_paths = set()
        
        for kw in keywords[:3]: # limit to top 3 keywords to avoid too many DB calls
            found = await Database.search_files(chat_id, kw, limit=2)
            for f in found:
                if f[1] not in seen_paths:
                    results.append(f)
                    seen_paths.add(f[1])
        
        # If no keywords matched, return most recent
        if not results:
            return await Database.get_recent_files(chat_id, 2)
            
        return results[:limit]
