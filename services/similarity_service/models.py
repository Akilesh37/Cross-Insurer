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

class SimilarityRequest(BaseModel):
    claim1: Claim
    claim2: Claim

class SimilarityResponse(BaseModel):
    similarity_score: float
    is_near_duplicate: bool
    explanation: Optional[dict] = None
