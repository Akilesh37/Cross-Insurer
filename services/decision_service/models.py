from pydantic import BaseModel
from typing import Optional

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

class EvaluationResponse(BaseModel):
    claim_id: str
    status: str
    confidence: float
    exact_hash: Optional[str] = None
    similarity_score: Optional[float] = None
    matched_claim_id: Optional[str] = None
    matched_insurer: Optional[str] = None
    explanation: Optional[dict] = None
    blockchain_tx: Optional[dict] = None
