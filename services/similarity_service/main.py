try:
    from .models import SimilarityRequest, SimilarityResponse
    from .matcher import calculate_similarity
except (ImportError, ValueError):
    from models import SimilarityRequest, SimilarityResponse
    from matcher import calculate_similarity

from fastapi import FastAPI

app = FastAPI(title="Similarity Service")

@app.post("/similarity", response_model=SimilarityResponse)
def evaluate_similarity(payload: SimilarityRequest):
    result = calculate_similarity(payload.claim1, payload.claim2)
    if isinstance(result, tuple):
        score, explanation = result
    else:
        score, explanation = result, None
    is_near_duplicate = score > 0.85
    return SimilarityResponse(
        similarity_score=score,
        is_near_duplicate=is_near_duplicate,
        explanation=explanation
    )
