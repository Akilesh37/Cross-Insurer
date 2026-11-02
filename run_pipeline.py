import requests
import json
import time

DECISION_SERVICE_URL = "http://localhost:8003/evaluate_claim"

# Sample 1: The original claim
claim_1 = {
    "claim_id": "c-100",
    "insurer_id": "InsurerA",
    "policy_type": "Auto",
    "claimant_id": "123-45-6789",
    "incident_date": "2024-10-15T12:00:00",
    "claim_amount": 1500.00,
    "provider_id": "prv-999",
    "diagnosis_or_incident_code": "coll-123",
    "description": "Minor fender bender on main st"
}

# Sample 2: Exact duplicate (different ID, different insurer)
claim_2 = {
    "claim_id": "c-999",
    "insurer_id": "InsurerB",
    "policy_type": "auto",
    "claimant_id": " 123-45-6789 ",
    "incident_date": "2024-10-15",
    "claim_amount": 1500.0,
    "provider_id": "PRV-999",
    "diagnosis_or_incident_code": "COLL-123",
    "description": "Minor fender bender on main st"
}

# Sample 3: Near duplicate (slightly modified description and date)
claim_3 = {
    "claim_id": "c-555",
    "insurer_id": "InsurerC",
    "policy_type": "Auto",
    "claimant_id": "123-45-6789",
    "incident_date": "2024-10-16T12:00:00",
    "claim_amount": 1550.00,
    "provider_id": "prv-999",
    "diagnosis_or_incident_code": "coll-123",
    "description": "Minor fender bender on main street"
}

# Sample 4: Completely unique claim
claim_4 = {
    "claim_id": "c-777",
    "insurer_id": "InsurerA",
    "policy_type": "Home",
    "claimant_id": "999-88-7777",
    "incident_date": "2024-11-01T08:00:00",
    "claim_amount": 5000.00,
    "provider_id": "prv-111",
    "diagnosis_or_incident_code": "fire-01",
    "description": "Kitchen fire damage"
}

def evaluate_claim(claim_data):
    try:
        print(f"\n--- Submitting Claim {claim_data['claim_id']} from {claim_data['insurer_id']} ---")
        resp = requests.post(DECISION_SERVICE_URL, json=claim_data)
        resp.raise_for_status()
        result = resp.json()
        print(f"Status: {result['status']}")
        print(f"Confidence: {result['confidence']:.2f}")
        return result
    except Exception as e:
        print(f"Failed to submit claim: {e}")

if __name__ == "__main__":
    print("Resetting mock DBs...")
    try:
        requests.delete("http://localhost:8003/debug/reset")
    except:
        print("Decision service not running or reachable on localhost:8003")
        exit(1)

    print("\n1. Submitting Original Claim...")
    evaluate_claim(claim_1)
    
    print("\n2. Submitting Exact Duplicate Claim...")
    evaluate_claim(claim_2)
    
    print("\n3. Submitting Near Duplicate Claim...")
    evaluate_claim(claim_3)
    
    print("\n4. Submitting Unique Claim...")
    evaluate_claim(claim_4)
