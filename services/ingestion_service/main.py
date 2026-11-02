import os
import csv
import io
import requests
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

try:
    from .models import Claim, BatchIngestRequest, EvaluationResult, IngestionSummary
except (ImportError, ValueError):
    from models import Claim, BatchIngestRequest, EvaluationResult, IngestionSummary

app = FastAPI(title="Claim Ingestion Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DECISION_SERVICE_URL = os.getenv("DECISION_SERVICE_URL", "http://decision_service:8000/evaluate_claim")
if not DECISION_SERVICE_URL.endswith("/evaluate_claim"):
    DECISION_SERVICE_URL = f"{DECISION_SERVICE_URL.rstrip('/')}/evaluate_claim"

def call_decision_service(claim_dict: dict) -> EvaluationResult:
    try:
        resp = requests.post(DECISION_SERVICE_URL, json=claim_dict, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return EvaluationResult(**data)
    except Exception as e:
        return EvaluationResult(
            claim_id=claim_dict.get("claim_id", "unknown"),
            status="ERROR",
            confidence=0.0
        )

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ingestion_service"}

@app.post("/ingest/claim", response_model=EvaluationResult)
def ingest_single_claim(claim: Claim):
    """Ingest and evaluate an individual claim."""
    return call_decision_service(claim.dict())

@app.post("/ingest/batch", response_model=IngestionSummary)
def ingest_batch_claims(batch: BatchIngestRequest):
    """Ingest and evaluate a batch of claims."""
    results: List[EvaluationResult] = []
    unique_cnt = 0
    exact_cnt = 0
    near_cnt = 0
    err_cnt = 0

    for c in batch.claims:
        res = call_decision_service(c.dict())
        results.append(res)
        if res.status == "UNIQUE":
            unique_cnt += 1
        elif res.status == "EXACT_DUPLICATE":
            exact_cnt += 1
        elif res.status == "NEAR_DUPLICATE":
            near_cnt += 1
        else:
            err_cnt += 1

    return IngestionSummary(
        total_processed=len(results),
        unique_count=unique_cnt,
        exact_duplicates=exact_cnt,
        near_duplicates=near_cnt,
        errors=err_cnt,
        results=results
    )

@app.post("/ingest/csv", response_model=IngestionSummary)
async def ingest_csv(file: UploadFile = File(...)):
    """Upload and process a CSV file of claims."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()
    decoded = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))

    results: List[EvaluationResult] = []
    unique_cnt = 0
    exact_cnt = 0
    near_cnt = 0
    err_cnt = 0

    for row in reader:
        try:
            claim_payload = {
                "claim_id": row["claim_id"],
                "insurer_id": row["insurer_id"],
                "policy_type": row["policy_type"],
                "claimant_id": row["claimant_id"],
                "incident_date": row["incident_date"],
                "claim_amount": float(row["claim_amount"]),
                "provider_id": row["provider_id"],
                "diagnosis_or_incident_code": row["diagnosis_or_incident_code"],
                "description": row["description"]
            }
            res = call_decision_service(claim_payload)
        except Exception:
            res = EvaluationResult(
                claim_id=row.get("claim_id", "unknown"),
                status="ERROR",
                confidence=0.0
            )

        results.append(res)
        if res.status == "UNIQUE":
            unique_cnt += 1
        elif res.status == "EXACT_DUPLICATE":
            exact_cnt += 1
        elif res.status == "NEAR_DUPLICATE":
            near_cnt += 1
        else:
            err_cnt += 1

    return IngestionSummary(
        total_processed=len(results),
        unique_count=unique_cnt,
        exact_duplicates=exact_cnt,
        near_duplicates=near_cnt,
        errors=err_cnt,
        results=results
    )
