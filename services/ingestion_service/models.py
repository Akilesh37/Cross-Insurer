from typing import List, Optional
from pydantic import BaseModel

class Claim(BaseModel):
    claim_id: str
    insurer_id: str
    policy_type: str
    claimant_id: str
    incident_date: str
    claim_amount: float
    provider_id: str
    diagnosis_or_incident_code: str
    description: str

class BatchIngestRequest(BaseModel):
    claims: List[Claim]

class EvaluationResult(BaseModel):
    claim_id: str
    status: str
    confidence: float
    exact_hash: Optional[str] = None
    similarity_score: Optional[float] = None

class IngestionSummary(BaseModel):
    total_processed: int
    unique_count: int
    exact_duplicates: int
    near_duplicates: int
    errors: int
    results: List[EvaluationResult]
