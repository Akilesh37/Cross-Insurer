from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any

try:
    from .models import Claim, EvaluationResponse
    from .orchestrator import evaluate, mock_blockchain_registry, mock_claims_db, simulate_multi_insurer_attack
    from .storage import claim_store
    from .graph_analytics import build_fraud_network_graph
    from .blockchain import blockchain_ledger
    from .benchmark import run_academic_benchmark
except (ImportError, ValueError):
    from models import Claim, EvaluationResponse
    from orchestrator import evaluate, mock_blockchain_registry, mock_claims_db, simulate_multi_insurer_attack
    from storage import claim_store
    from graph_analytics import build_fraud_network_graph
    from blockchain import blockchain_ledger
    from benchmark import run_academic_benchmark

app = FastAPI(title="Decision Service", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/evaluate_claim", response_model=EvaluationResponse)
def evaluate_claim(claim: Claim):
    return evaluate(claim)

# --- Graph Network Analytics ---
@app.get("/graph/analytics")
def get_graph_analytics():
    """Generates cross-insurer entity graph and detects collusive fraud rings."""
    return build_fraud_network_graph()

# --- Blockchain Smart Contract Ledger ---
@app.get("/blockchain/ledger")
def get_blockchain_ledger():
    """Returns the immutable on-chain consortium transaction ledger and event log."""
    return {
        "contract": "0x5FbDB2315678afecb367f032d93F642f64180aa3",
        "block_height": blockchain_ledger.block_height,
        "ledger": blockchain_ledger.get_ledger()
    }

# --- Multi-Insurer Simulation Demo ---
@app.post("/simulate/multi_insurer")
def run_simulation():
    """Executes a live 4-stage cross-carrier fraud simulation demonstration."""
    return simulate_multi_insurer_attack()

# --- Academic Benchmark & Evaluation ---
@app.get("/benchmark/stats")
def get_benchmark_stats(threshold: float = 0.85):
    """Computes empirical Confusion Matrix, ROC curve, and F1 metrics on labeled ground truth."""
    return run_academic_benchmark(threshold=threshold)

@app.post("/benchmark/run")
def post_run_benchmark(payload: Dict[str, Any] = Body(default={})):
    th = float(payload.get("threshold", 0.85))
    return run_academic_benchmark(threshold=th)

# --- Debug & Reset ---
@app.get("/debug/registry")
def get_registry():
    return {"registered_hashes": list(mock_blockchain_registry)}

@app.get("/debug/db")
def get_db():
    return {"stored_claims": [c.dict() for c in claim_store.get_all_claims()]}

@app.delete("/debug/reset")
def reset_mocks():
    claim_store.reset()
    blockchain_ledger.reset()
    return {"status": "reset", "message": "Databases and blockchain ledger restored to genesis state"}
