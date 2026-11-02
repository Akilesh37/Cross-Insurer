import hashlib
import json
from datetime import datetime
try:
    from .models import Claim
except (ImportError, ValueError):
    from models import Claim

def canonicalize_claim(claim: Claim) -> str:
    """
    Deterministically normalizes a claim dictionary for exact-match hashing.
    Excludes claim_id and insurer_id to allow matching across different insurers.
    """
    
    # 1. Lowercase policy_type and strip whitespace
    policy_type = claim.policy_type.strip().lower()
    
    # 2. SHA-256 hash claimant_id (PII masking)
    claimant_id_clean = claim.claimant_id.strip()
    claimant_hash = hashlib.sha256(claimant_id_clean.encode('utf-8')).hexdigest()
    
    # 3. Validate and normalize incident_date to strict ISO-8601 date
    try:
        # Assuming we just want the date part for consistency
        dt = datetime.fromisoformat(claim.incident_date.strip())
        incident_date = dt.date().isoformat()
    except ValueError:
        # Fallback if invalid format, just strip
        incident_date = claim.incident_date.strip()
        
    # 4. Round claim_amount to exactly 2 decimals
    claim_amount = f"{claim.claim_amount:.2f}"
    
    # 5. Uppercase provider_id and diagnosis_or_incident_code
    provider_id = claim.provider_id.strip().upper()
    diagnosis_code = claim.diagnosis_or_incident_code.strip().upper()
    
    # 6. Description (just strip whitespace)
    description = claim.description.strip()
    
    # Construct canonical dictionary with ONLY fields relevant to the actual claim event
    canonical_dict = {
        "claim_amount": claim_amount,
        "claimant_id": claimant_hash,
        "description": description,
        "diagnosis_or_incident_code": diagnosis_code,
        "incident_date": incident_date,
        "policy_type": policy_type,
        "provider_id": provider_id
    }
    
    # Return JSON string with sorted keys for determinism
    return json.dumps(canonical_dict, sort_keys=True, separators=(',', ':'))
