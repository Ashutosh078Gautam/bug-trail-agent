# Bug Trail

Bug Trail is an explainable codebase agent that takes a plain-English bug report, traces code and commit history through FalkorDB, identifies the most likely origin, recalls similar bugs, and shows the evidence path behind its answer.

## What is included

- A synthetic shopping application with checkout, coupons, taxes, cart, and payment modules.
- An AST loader that extracts the sample application's functions and local call relationships.
- A FalkorDB graph containing functions, modules, commits, developers, bugs, fixes, and tests.
- A deterministic investigation engine that ranks candidate functions using graph evidence.
- Optional Gemini semantic extraction that understands paraphrased bug reports before graph retrieval.
- Persistent bug memory: investigations are stored in FalkorDB and can be recalled later.
- A browser UI with an evidence timeline, confidence score, and graph path.
- A regression-test recommendation based on historical fixes and verification tests.
- Reproducible evaluation cases and a judge-ready demo checklist.
- A JSON API for integration and demo automation.

## Run locally

### 1. Start FalkorDB

Install Docker Desktop, then run:

```powershell
docker compose up -d falkordb
```

FalkorDB will be available at `localhost:6379` and its browser at `http://localhost:3000`.

### 2. Install Python dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 3. Load the demo graph and start the app

```powershell
python scripts\seed_graph.py
python scripts\load_codebase.py
python scripts\evaluate.py
uvicorn app.main:app --reload --host 127.0.0.1 --port 8765
```

Open `http://localhost:8765`.

### Optional Gemini semantic search

Bug Trail works without an LLM by using its deterministic keyword fallback. To enable richer semantic extraction, copy `.env.example` to `.env`, add your local `GEMINI_API_KEY`, and install the requirements. The key is read only from `.env` and must never be committed. Gemini extracts search concepts; FalkorDB remains the source of truth for functions, call paths, commits, developers, and bug memory.

### Optional: run the app in Docker

Build and start the application container:

```powershell
docker compose up -d --build
docker compose exec app python scripts/seed_graph.py
docker compose exec app python scripts/load_codebase.py
```

Open `http://localhost:8080`.

To investigate from the command line:

```powershell
Invoke-RestMethod http://localhost:8000/api/investigate -Method Post `
  -ContentType 'application/json' `
  -Body '{"description":"Checkout total is wrong when a percentage coupon is applied."}'
```

## Graph model

```text
Bug -[:AFFECTS]-> Function -[:CALLS]-> Function
Function -[:BELONGS_TO]-> Module
Function -[:CHANGED_IN]-> Commit -[:AUTHORED_BY]-> Developer
Bug -[:SIMILAR_TO]-> Bug
Bug -[:RESOLVED_BY]-> Fix -[:IMPLEMENTED_BY]-> Commit
Fix -[:VERIFIED_BY]-> Test
```

The graph is the reasoning layer: it determines candidate functions, call paths, commit evidence, historical similarity, and persistent memory. The UI is only a view of those graph-backed results.

## Demo scenarios

Try these reports:

1. `Checkout total is wrong when a percentage coupon is applied.`
2. `Tax is being charged twice for a taxable order.`
3. `Removing an item does not update the cart total.`

Run the first report, then submit a paraphrase of it in a new request to show persistent memory.

## Submission notes

- FalkorDB is the primary graph database.
- The data is synthetic and safe for a public repository.
- The investigation endpoint returns the Cypher queries used as evidence.
- AI coding assistance should be disclosed in the final submission.

