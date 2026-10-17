from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.graph import BugTrailGraph
from app.investigator import Investigator


ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="Bug Trail", version="0.1.0")
store = BugTrailGraph()
investigator = Investigator(store)


class BugReport(BaseModel):
    description: str = Field(min_length=8, max_length=500)


@app.get("/")
def home() -> FileResponse:
    return FileResponse(ROOT / "web" / "index.html")


@app.get("/api/health")
def health() -> dict[str, bool]:
    try:
        return {"falkordb": store.health()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"FalkorDB unavailable: {exc}") from exc


@app.post("/api/investigate")
def investigate(report: BugReport) -> dict:
    try:
        return investigator.investigate(report.description)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Investigation failed: {exc}") from exc

