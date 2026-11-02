from pydantic import BaseModel, Field

class Claim(BaseModel):
    claim_id: str = Field(..., description="Unique identifier for the claim")
    insurer_id: str = Field(..., description="Identifier for the insurer submitting the claim")
    policy_type: str = Field(..., description="Type of policy (e.g., Auto, Health, Property)")
    claimant_id: str = Field(..., description="Identifier for the claimant (e.g., SSN)")
    incident_date: str = Field(..., description="Date of the incident in ISO-8601 format")
    claim_amount: float = Field(..., description="Amount claimed")
    provider_id: str = Field(..., description="Identifier for the service provider")
    diagnosis_or_incident_code: str = Field(..., description="Diagnostic or incident code")
    description: str = Field(..., description="Free-text description of the claim")

class FingerprintResponse(BaseModel):
    claim_id: str
    exact_hash: str
