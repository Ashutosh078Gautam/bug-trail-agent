# Bug Trail demo checklist

## Before recording

```powershell
docker compose up -d falkordb
python scripts\seed_graph.py
python scripts\load_codebase.py
uvicorn app.main:app --host 127.0.0.1 --port 19123
```

Run the evaluation:

```powershell
python scripts\evaluate.py
```

## Three-minute demo

1. Explain that Bug Trail connects bug symptoms to code, commit history, and previous fixes.
2. Enter: `Checkout total is wrong when a percentage coupon is applied.`
3. Show `applyCoupon` as the likely origin.
4. Show the call path and commit `abc123` by Priya.
5. Show the recalled coupon bug and its historical verification test.
6. Submit a paraphrase of the same bug to demonstrate persistent memory.
7. Enter: `Tax is being charged twice for a taxable order.`
8. Show that the agent follows a different graph path and identifies Mateo's commit.
9. Open the Cypher section and explain that FalkorDB produced the evidence.

## Claims to make carefully

- Say “most likely introduced by,” not “proven to be caused by.”
- State that the dataset is synthetic and public-safe.
- Explain that the graph is the reasoning layer, not just a visualization.
- Disclose the use of AI coding assistance in the submission.

