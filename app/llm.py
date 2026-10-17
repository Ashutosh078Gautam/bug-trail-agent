"""Optional semantic extraction for Bug Trail.

The LLM only extracts search concepts. FalkorDB remains the source of truth for
functions, call paths, commits, developers, and historical bugs.
"""

import json
import urllib.error
import urllib.request
from typing import Any

from app.settings import GEMINI_API_KEY, GEMINI_MODEL, LLM_PROVIDER


class SemanticExtractor:
    def extract(self, description: str, function_catalog: list[dict[str, Any]]) -> dict[str, Any] | None:
        if LLM_PROVIDER != "gemini" or not GEMINI_API_KEY:
            return None

        catalog = json.dumps(function_catalog[:80], separators=(",", ":"))
        prompt = f"""You are Bug Trail's semantic bug-report parser.
Return only JSON. Do not invent function names: use only names from the catalog.
Extract useful search concepts from this bug report.

Bug report: {description}
Function catalog: {catalog}

Return this shape:
{{
  "summary": "short normalized description",
  "symptoms": ["..."],
  "conditions": ["..."],
  "entities": ["..."],
  "candidate_functions": ["function names from the catalog only"],
  "search_terms": ["short lowercase terms"]
}}"""

        schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "symptoms": {"type": "array", "items": {"type": "string"}},
                "conditions": {"type": "array", "items": {"type": "string"}},
                "entities": {"type": "array", "items": {"type": "string"}},
                "candidate_functions": {"type": "array", "items": {"type": "string"}},
                "search_terms": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["summary", "symptoms", "conditions", "entities", "candidate_functions", "search_terms"],
        }
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": schema,
                "temperature": 0.1,
            },
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
            text = payload["candidates"][0]["content"]["parts"][0]["text"]
            result = json.loads(text)
            allowed = {item["name"] for item in function_catalog}
            result["candidate_functions"] = [name for name in result.get("candidate_functions", []) if name in allowed]
            return result
        except (urllib.error.URLError, TimeoutError, KeyError, IndexError, TypeError, ValueError):
            return None
