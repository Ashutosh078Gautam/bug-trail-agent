"""Optional semantic extraction for Bug Trail.

The LLM only extracts search concepts. FalkorDB remains the source of truth for
functions, call paths, commits, developers, and historical bugs.
"""

import json
import urllib.error
import urllib.request
from typing import Any

from app.settings import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    LLM_PROVIDER,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
)


class SemanticExtractor:
    def extract(self, description: str, function_catalog: list[dict[str, Any]]) -> dict[str, Any] | None:
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
        gemini_body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": schema,
                "temperature": 0.1,
            },
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
        if LLM_PROVIDER == "gemini" and GEMINI_API_KEY:
            result = self._request_json(
                url, gemini_body,
                {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY},
                lambda payload: payload["candidates"][0]["content"]["parts"][0]["text"],
            )
            if result:
                return self._sanitize(result, function_catalog)

        if OPENROUTER_API_KEY:
            result = self._request_json(
                "https://openrouter.ai/api/v1/chat/completions",
                {"model": OPENROUTER_MODEL, "messages": [
                    {"role": "system", "content": "Return only valid JSON matching the requested shape."},
                    {"role": "user", "content": prompt},
                ], "temperature": 0.1},
                {"Content-Type": "application/json", "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                 "HTTP-Referer": "http://localhost:8765", "X-Title": "Bug Trail"},
                lambda payload: payload["choices"][0]["message"]["content"],
            )
            if result:
                return self._sanitize(result, function_catalog)

        return None

    @staticmethod
    def _request_json(url: str, body: dict[str, Any], headers: dict[str, str], text_reader: Any) -> dict[str, Any] | None:
        request = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
            text = text_reader(payload).strip().removeprefix("```json").removesuffix("```").strip()
            return json.loads(text)
        except (urllib.error.URLError, TimeoutError, KeyError, IndexError, TypeError, ValueError):
            return None

    @staticmethod
    def _sanitize(result: dict[str, Any], function_catalog: list[dict[str, Any]]) -> dict[str, Any]:
        allowed = {item["name"] for item in function_catalog}
        result["candidate_functions"] = [name for name in result.get("candidate_functions", []) if name in allowed]
        return result

