import math
import re
from datetime import datetime
from difflib import SequenceMatcher
from typing import Tuple, Dict, Any, List
from dateutil import parser

try:
    from .models import Claim
except (ImportError, ValueError):
    from models import Claim

# Domain synonyms for insurance claim narratives to enable semantic mapping
CONCEPT_SYNONYMS = {
    # Auto / Collision
    "collision": "accident", "crash": "accident", "wreck": "accident", "fender": "accident",
    "bender": "accident", "rear-ended": "accident", "hit": "accident", "impacted": "accident",
    "vehicle": "automobile", "car": "automobile", "truck": "automobile", "sedan": "automobile",
    "auto": "automobile", "suv": "automobile",
    "st": "street", "rd": "road", "ave": "avenue", "blvd": "boulevard", "hwy": "highway",
    # Health / Injury
    "doctor": "physician", "clinic": "medical", "hospital": "medical", "er": "medical",
    "injury": "trauma", "fracture": "broken", "sprain": "injury", "whiplash": "injury",
    # Property
    "fire": "burn", "smoke": "burn", "flames": "burn", "leak": "water", "flood": "water",
    "theft": "stolen", "burglary": "stolen", "break-in": "stolen"
}

STOP_WORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with", "by", "of",
    "from", "as", "is", "was", "were", "it", "this", "that", "please", "process", "asap",
    "update", "revised", "claim", "details", "review", "needed", "additional"
}

def tokenize_and_normalize(text: str) -> List[str]:
    """Tokenizes text, strips punctuation, normalizes synonyms, and removes stopwords."""
    words = re.findall(r'\b[a-zA-Z0-9-]+\b', text.lower())
    tokens = []
    for w in words:
        if w in STOP_WORDS:
            continue
        normalized = CONCEPT_SYNONYMS.get(w, w)
        tokens.append(normalized)
    return tokens

def get_char_ngrams(text: str, n: int = 3) -> set:
    """Extracts character n-grams to catch subtle typographical mutations."""
    clean = re.sub(r'\s+', ' ', text.lower().strip())
    return {clean[i:i+n] for i in range(len(clean) - n + 1)}

def cosine_similarity(tokens1: List[str], tokens2: List[str]) -> float:
    """Calculates vector space cosine similarity with term frequency weighting."""
    if not tokens1 or not tokens2:
        return 0.0
    
    vec1: Dict[str, float] = {}
    vec2: Dict[str, float] = {}
    
    for t in tokens1:
        vec1[t] = vec1.get(t, 0.0) + 1.0
    for t in tokens2:
        vec2[t] = vec2.get(t, 0.0) + 1.0
        
    all_terms = set(vec1.keys()) | set(vec2.keys())
    dot_product = sum(vec1.get(t, 0.0) * vec2.get(t, 0.0) for t in all_terms)
    norm1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
    norm2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)

def calculate_similarity(claim1: Claim, claim2: Claim) -> Tuple[float, Dict[str, Any]]:
    """
    Computes an explainable multi-dimensional similarity score between two insurance claims:
    1. Amount Proximity (25%)
    2. Temporal Proximity (25%)
    3. Semantic Narrative Embeddings & Vector Cosine (30%)
    4. Cross-Insurer Entity Overlap (20%)
    """
    weights = {
        "amount": 0.25,
        "date": 0.25,
        "semantic": 0.30,
        "entity": 0.20
    }
    
    # --- 1. Amount Proximity ---
    amt1 = float(claim1.claim_amount)
    amt2 = float(claim2.claim_amount)
    max_amt = max(amt1, amt2)
    amount_delta = abs(amt1 - amt2)
    if max_amt > 0:
        ratio = amount_delta / max_amt
        # High score if within 5% of each other
        amount_score = max(0.0, 1.0 - (ratio * 1.5))
    else:
        amount_score = 1.0

    # --- 2. Temporal Proximity ---
    days_delta = 999
    try:
        dt1 = parser.parse(claim1.incident_date)
        dt2 = parser.parse(claim2.incident_date)
        days_delta = abs((dt1 - dt2).days)
        if days_delta == 0:
            date_score = 1.0
        elif days_delta == 1:
            date_score = 0.90
        elif days_delta <= 3:
            date_score = 0.75
        elif days_delta <= 7:
            date_score = 0.50
        elif days_delta <= 14:
            date_score = 0.25
        else:
            date_score = 0.0
    except Exception:
        date_score = 0.0

    # --- 3. Semantic Narrative Similarity ---
    desc1 = claim1.description or ""
    desc2 = claim2.description or ""
    
    tokens1 = tokenize_and_normalize(desc1)
    tokens2 = tokenize_and_normalize(desc2)
    vector_cosine = cosine_similarity(tokens1, tokens2)
    
    ngrams1 = get_char_ngrams(desc1, 3)
    ngrams2 = get_char_ngrams(desc2, 3)
    if ngrams1 and ngrams2:
        ngram_jaccard = len(ngrams1 & ngrams2) / len(ngrams1 | ngrams2)
    else:
        ngram_jaccard = 0.0
        
    seq_ratio = SequenceMatcher(None, desc1.lower().strip(), desc2.lower().strip()).ratio()
    
    # Blended semantic representation: 50% Vector Cosine + 30% Char N-Gram + 20% Sequence Matcher
    semantic_score = (0.50 * vector_cosine) + (0.30 * ngram_jaccard) + (0.20 * seq_ratio)
    semantic_score = min(1.0, max(0.0, semantic_score))

    # --- 4. Cross-Insurer Entity Overlap ---
    same_claimant = (claim1.claimant_id.strip().lower() == claim2.claimant_id.strip().lower())
    same_provider = (claim1.provider_id.strip().upper() == claim2.provider_id.strip().upper())
    same_diagnosis = (claim1.diagnosis_or_incident_code.strip().upper() == claim2.diagnosis_or_incident_code.strip().upper())
    is_cross_insurer = (claim1.insurer_id.strip().lower() != claim2.insurer_id.strip().lower())
    
    entity_subscores = []
    if same_claimant:
        entity_subscores.append(0.50)
    if same_provider:
        entity_subscores.append(0.30)
    if same_diagnosis:
        entity_subscores.append(0.20)
    entity_score = sum(entity_subscores)
    
    # --- Composite Score Calculation ---
    composite_score = (
        weights["amount"] * amount_score +
        weights["date"] * date_score +
        weights["semantic"] * semantic_score +
        weights["entity"] * entity_score
    )
    
    # Boost if high multi-signal collusion (same claimant + cross insurer + near date)
    if same_claimant and is_cross_insurer and days_delta <= 3:
        composite_score = min(1.0, composite_score * 1.15)
        
    composite_score = round(min(1.0, max(0.0, composite_score)), 4)
    
    # --- Explainability (XAI) Synthesis ---
    reasons = []
    if same_claimant and is_cross_insurer:
        reasons.append(f"Identical claimant filing cross-insurer ({claim1.insurer_id} vs {claim2.insurer_id})")
    if same_provider:
        reasons.append(f"Shared medical/service provider [{claim1.provider_id}]")
    if days_delta <= 1:
        reasons.append(f"Near-simultaneous event ({days_delta} day delta)")
    elif days_delta <= 7:
        reasons.append(f"Temporal cluster ({days_delta} days apart)")
    if amount_delta <= 50.0:
        reasons.append(f"Virtually identical claim payout ($Delta = ${amount_delta:.2f})")
    if semantic_score >= 0.80:
        reasons.append(f"High semantic narrative correlation ({semantic_score * 100:.1f}%)")

    verdict_reason = "; ".join(reasons) if reasons else "Low semantic or attribute similarity."
    
    explanation = {
        "amount": {
            "score": round(amount_score, 4),
            "delta": round(amount_delta, 2),
            "weight": weights["amount"],
            "amt1": amt1,
            "amt2": amt2
        },
        "date": {
            "score": round(date_score, 4),
            "days_delta": days_delta,
            "weight": weights["date"],
            "date1": claim1.incident_date,
            "date2": claim2.incident_date
        },
        "semantic": {
            "score": round(semantic_score, 4),
            "vector_cosine": round(vector_cosine, 4),
            "ngram_jaccard": round(ngram_jaccard, 4),
            "weight": weights["semantic"]
        },
        "entity": {
            "score": round(entity_score, 4),
            "weight": weights["entity"],
            "same_claimant": same_claimant,
            "same_provider": same_provider,
            "same_diagnosis": same_diagnosis,
            "is_cross_insurer": is_cross_insurer
        },
        "composite_score": composite_score,
        "verdict_reason": verdict_reason
    }
    
    return composite_score, explanation
