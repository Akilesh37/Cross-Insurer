import argparse
import csv
import random
import uuid
import math
from datetime import datetime, timedelta

def load_claims(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_claims(claims, filepath, fieldnames):
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(claims)

def save_ground_truth(ground_truth, filepath):
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['claim_id_a', 'claim_id_b', 'label'])
        writer.writeheader()
        writer.writerows(ground_truth)

def perturb_date(date_str):
    try:
        dt = datetime.fromisoformat(date_str)
        delta = random.choice([-3, -2, -1, 1, 2, 3])
        return (dt + timedelta(days=delta)).isoformat()
    except:
        return date_str

def perturb_amount(amount_str):
    amount = float(amount_str)
    if random.choice([True, False]):
        # Rounding
        return str(round(amount))
    else:
        # +/- 5%
        change = random.uniform(-0.05, 0.05)
        return str(round(amount * (1 + change), 2))

def perturb_description(desc):
    prefixes = ["Update: ", "Revised claim: ", "Additional details: ", ""]
    suffixes = [" Please process ASAP.", " Review needed.", ""]
    return f"{random.choice(prefixes)}{desc}{random.choice(suffixes)}"

def main():
    parser = argparse.ArgumentParser(description="Inject exact and near duplicates into claims dataset")
    parser.add_argument("--input", type=str, default="synthetic_claims.csv", help="Input CSV file")
    parser.add_argument("--output", type=str, default="final_claims.csv", help="Output CSV file with duplicates")
    parser.add_argument("--ground_truth", type=str, default="ground_truth.csv", help="Output ground truth CSV file")
    parser.add_argument("--rate", type=float, default=0.15, help="Duplicate rate (e.g., 0.15 for 15%)")
    args = parser.parse_args()

    claims = load_claims(args.input)
    if not claims:
        print("No claims to process.")
        return

    num_duplicates = int(len(claims) * args.rate)
    
    # Select claims to duplicate
    to_duplicate = random.sample(claims, num_duplicates)
    
    final_claims = list(claims)
    ground_truth = []
    
    insurers = ["InsurerA", "InsurerB", "InsurerC"]
    
    for original in to_duplicate:
        dup_type = random.choice(["exact", "near"])
        duplicate = original.copy()
        
        # Give it a new claim_id
        new_claim_id = str(uuid.uuid4())
        duplicate['claim_id'] = new_claim_id
        
        # Submit to a different insurer
        available_insurers = [i for i in insurers if i != original['insurer_id']]
        duplicate['insurer_id'] = random.choice(available_insurers)
        
        if dup_type == "near":
            # Apply perturbations
            if random.random() > 0.3:
                duplicate['incident_date'] = perturb_date(original['incident_date'])
            if random.random() > 0.3:
                duplicate['claim_amount'] = perturb_amount(original['claim_amount'])
            if random.random() > 0.3:
                duplicate['description'] = perturb_description(original['description'])
                
        final_claims.append(duplicate)
        ground_truth.append({
            'claim_id_a': original['claim_id'],
            'claim_id_b': new_claim_id,
            'label': 'exact' if dup_type == 'exact' else 'near'
        })
        
    # Shuffle final claims so duplicates aren't all at the end
    random.shuffle(final_claims)
    
    fieldnames = list(claims[0].keys())
    save_claims(final_claims, args.output, fieldnames)
    save_ground_truth(ground_truth, args.ground_truth)
    
    print(f"Original claims: {len(claims)}")
    print(f"Duplicates injected: {len(to_duplicate)}")
    print(f"Total final claims: {len(final_claims)}")
    print(f"Saved {args.output} and {args.ground_truth}")

if __name__ == "__main__":
    main()
