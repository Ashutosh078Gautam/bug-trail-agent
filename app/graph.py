from typing import Any

from falkordb import FalkorDB

from app.settings import FALKORDB_GRAPH, FALKORDB_HOST, FALKORDB_PORT


class BugTrailGraph:
    def __init__(self) -> None:
        self.db = FalkorDB(host=FALKORDB_HOST, port=FALKORDB_PORT)
        self.graph = self.db.select_graph(FALKORDB_GRAPH)

    def query(self, cypher: str, params: dict[str, Any] | None = None) -> list[list[Any]]:
        result = self.graph.query(cypher, params or {})
        return result.result_set

    def health(self) -> bool:
        self.query("RETURN 1")
        return True

