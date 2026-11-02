try:
    from .models import Claim, FingerprintResponse
    from .canonicalizer import canonicalize_claim
    from .hasher import generate_exact_hash
except (ImportError, ValueError):
    from models import Claim, FingerprintResponse
    from canonicalizer import canonicalize_claim
    from hasher import generate_exact_hash

from fastapi import FastAPI

app = FastAPI(title="Fingerprint Service", version="1.0.0")

@app.post("/fingerprint", response_model=FingerprintResponse)
def fingerprint_claim(claim: Claim):
    """
    Receives a claim, canonicalizes it, and returns an exact-match hash.
    """
    canonical_json = canonicalize_claim(claim)
    exact_hash = generate_exact_hash(canonical_json)
    
    return FingerprintResponse(
        claim_id=claim.claim_id,
        exact_hash=exact_hash
    )

@app.get("/health")
def health_check():
    return {"status": "ok"}
