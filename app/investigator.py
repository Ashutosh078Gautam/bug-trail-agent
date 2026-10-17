import re
from datetime import datetime, timezone
from typing import Any

from app.graph import BugTrailGraph


STOP_WORDS = {
    "the", "and", "when", "with", "from", "this", "that", "does", "not",
    "is", "are", "for", "into", "after", "wrong", "being", "issue", "bug",
}


class Investigator:
    def __init__(self, store: BugTrailGraph) -> None:
        self.store = store

    def investigate(self, description: str) -> dict[str, Any]:
        candidates = self._candidate_functions(description)
        if not candidates:
            candidates = self._fallback_candidates()

        ranked = self._rank_candidates(description, candidates)
        best = ranked[0]
        evidence = self._evidence(best["name"])
        similar = self._similar_bugs(description, best["name"])
        test_recommendation = self._test_recommendation(best["name"], similar)
        bug_id = f"bug-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"

        self.store.query(
            """
            CREATE (b:Bug {id: $id, description: $description, created_at: $created_at,
                           suspected_function: $function, confidence: $confidence})
            """,
            {"id": bug_id, "description": description, "created_at": datetime.now(timezone.utc).isoformat(),
             "function": best["name"], "confidence": best["score"]},
        )
        self.store.query(
            """
            MATCH (b:Bug {id: $id}), (f:Function {name: $function})
            CREATE (b)-[:AFFECTS]->(f)
            """,
            {"id": bug_id, "function": best["name"]},
        )
        if similar:
            self.store.query(
                """
                MATCH (b:Bug {id: $id}), (old:Bug {id: $old_id})
                CREATE (b)-[:SIMILAR_TO]->(old)
                """,
                {"id": bug_id, "old_id": similar["id"]},
            )

        return {
            "bug_id": bug_id,
            "description": description,
            "suspected_function": best["name"],
            "confidence": best["score"],
            "summary": self._summary(best, evidence, similar),
            "ranked_candidates": ranked,
            "evidence": evidence,
            "similar_bug": similar,
            "test_recommendation": test_recommendation,
            "queries": {
                "path": "MATCH p=(f:Function {name: $function})-[:CALLS*0..3]->(downstream:Function) RETURN p",
                "commit": "MATCH (f:Function {name: $function})-[:CHANGED_IN]->(c:Commit)-[:AUTHORED_BY]->(d:Developer) RETURN c,d",
                "memory": "MATCH (b:Bug)-[:AFFECTS]->(f:Function) WHERE f.name = $function RETURN b ORDER BY b.created_at DESC",
            },
        }

    def _test_recommendation(self, function: str, similar: dict[str, Any] | None) -> dict[str, Any]:
        rows = self.store.query(
            """
            MATCH (f:Function {name: $function})<-[:AFFECTS]-(b:Bug)-[:RESOLVED_BY]->(fix:Fix)-[:VERIFIED_BY]->(t:Test)
            RETURN t.name, fix.description
            ORDER BY b.created_at DESC LIMIT 1
            """, {"function": function},
        )
        if rows:
            return {
                "name": rows[0][0],
                "status": "historical",
                "rationale": f"A previous fix for {function} was verified by this test.",
            }
        return {
            "name": f"Add a regression test for {function}",
            "status": "recommended",
            "rationale": "No linked verification test was found in the graph yet.",
        }

    def _candidate_functions(self, description: str) -> list[str]:
        words = set(re.findall(r"[a-zA-Z][a-zA-Z0-9]+", description.lower()))
        rows = self.store.query("MATCH (f:Function) RETURN f.name, f.keywords")
        candidates = []
        for name, keywords in rows:
            haystack = set(str(keywords or "").lower().split(",")) | set(name.lower().split("_"))
            if words & haystack:
                candidates.append(name)
        return candidates

    def _fallback_candidates(self) -> list[str]:
        return [row[0] for row in self.store.query("MATCH (f:Function) RETURN f.name LIMIT 5")]

    def _rank_candidates(self, description: str, candidates: list[str]) -> list[dict[str, Any]]:
        words = set(re.findall(r"[a-zA-Z][a-zA-Z0-9]+", description.lower())) - STOP_WORDS
        rows = self.store.query(
            """
            MATCH (f:Function)
            WHERE f.name IN $names
            OPTIONAL MATCH (f)-[:CHANGED_IN]->(c:Commit)-[:AUTHORED_BY]->(d:Developer)
            RETURN f.name, f.keywords, c.id, c.message, c.timestamp, d.name
            """,
            {"names": candidates},
        )
        output = []
        for name, keywords, commit_id, message, timestamp, developer in rows:
            keyword_set = set(str(keywords or "").lower().split(","))
            score = min(96, 48 + 12 * len(words & keyword_set))
            output.append({"name": name, "score": score, "commit": commit_id, "message": message,
                           "timestamp": timestamp, "developer": developer})
        return sorted(output, key=lambda x: x["score"], reverse=True)

    def _evidence(self, function: str) -> dict[str, Any]:
        path_rows = self.store.query(
            """
            MATCH p=(start:Function {name: $function})-[:CALLS*0..3]->(downstream:Function)
            RETURN p
            ORDER BY length(p) DESC LIMIT 1
            """, {"function": function},
        )
        commit_rows = self.store.query(
            """
            MATCH (f:Function {name: $function})-[:CHANGED_IN]->(c:Commit)-[:AUTHORED_BY]->(d:Developer)
            RETURN c.id, c.message, c.timestamp, d.name
            ORDER BY c.timestamp DESC LIMIT 1
            """, {"function": function},
        )
        module_rows = self.store.query(
            "MATCH (f:Function {name: $function})-[:BELONGS_TO]->(m:Module) RETURN m.name", {"function": function}
        )
        commit = commit_rows[0] if commit_rows else [None, None, None, None]
        path = path_rows[0][0] if path_rows else None
        call_path = [node.properties.get("name") for node in path.nodes()] if path else [function]
        return {
            "call_path": call_path,
            "module": module_rows[0][0] if module_rows else "unknown",
            "commit": {"id": commit[0], "message": commit[1], "timestamp": commit[2], "developer": commit[3]},
        }

    def _similar_bugs(self, description: str, function: str) -> dict[str, Any] | None:
        rows = self.store.query(
            """
            MATCH (b:Bug)-[:AFFECTS]->(f:Function {name: $function})
            OPTIONAL MATCH (b)-[:RESOLVED_BY]->(fix:Fix)-[:IMPLEMENTED_BY]->(c:Commit)
            RETURN b.id, b.description, fix.description, c.id
            ORDER BY b.created_at DESC LIMIT 1
            """, {"function": function},
        )
        if not rows:
            return None
        row = rows[0]
        return {"id": row[0], "description": row[1], "fix": row[2], "commit": row[3]}

    @staticmethod
    def _summary(best: dict[str, Any], evidence: dict[str, Any], similar: dict[str, Any] | None) -> str:
        text = f"The issue most likely originates in {best['name']} with {best['score']}% confidence."
        if evidence["commit"]["id"]:
            text += f" It was changed in {evidence['commit']['id']} by {evidence['commit']['developer']}."
        if similar:
            text += f" A similar bug was previously reported: {similar['description']}"
        return text

