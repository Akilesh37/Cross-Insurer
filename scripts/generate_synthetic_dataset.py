import argparse
import csv
import json
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

INSURERS = ["InsurerA", "InsurerB", "InsurerC"]
POLICY_TYPES = ["Auto", "Health", "Property"]

def generate_claim(claim_id=None):
    policy_type = random.choice(POLICY_TYPES)
    
    if policy_type == "Auto":
        diagnosis_or_incident_code = fake.bothify(text='COLL-####').upper()
        description = f"Vehicle was involved in a collision. {fake.sentence()}"
        claim_amount = round(random.uniform(500, 15000), 2)
    elif policy_type == "Health":
        diagnosis_or_incident_code = fake.bothify(text='ICD-10-?##.#').upper()
        description = f"Patient presented with symptoms requiring medical attention. {fake.sentence()}"
        claim_amount = round(random.uniform(100, 50000), 2)
    else:  # Property
        diagnosis_or_incident_code = fake.bothify(text='PROP-####').upper()
        description = f"Property damage due to covered peril. {fake.sentence()}"
        claim_amount = round(random.uniform(1000, 100000), 2)

    return {
        "claim_id": claim_id or str(uuid.uuid4()),
        "insurer_id": random.choice(INSURERS),
        "policy_type": policy_type,
        "claimant_id": fake.ssn(), # Using SSN as a proxy for claimant_id
        "incident_date": fake.date_between(start_date='-2y', end_date='today').isoformat(),
        "claim_amount": claim_amount,
        "provider_id": f"PRV-{fake.random_int(min=1000, max=9999)}",
        "diagnosis_or_incident_code": diagnosis_or_incident_code,
        "description": description
    }

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic claims dataset")
    parser.add_argument("--count", type=int, default=2000, help="Number of claims to generate")
    parser.add_argument("--output", type=str, default="synthetic_claims.csv", help="Output CSV file path")
    args = parser.parse_args()

    print(f"Generating {args.count} claims...")
    claims = [generate_claim() for _ in range(args.count)]

    if not claims:
        print("No claims generated.")
        return

    keys = claims[0].keys()
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(claims)
    
    print(f"Saved {args.count} claims to {args.output}")

if __name__ == "__main__":
    main()
