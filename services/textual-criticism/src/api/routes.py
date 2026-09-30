from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.scoring import calculate_variant_score

router = APIRouter()

class VariantRequest(BaseModel):
    verse_ref: str
    base_text: str
    variant_text: str
    witnesses: list[str]

class VariantResponse(BaseModel):
    verse_ref: str
    variant_text: str
    confidence_score: float
    witness_weight: float
    text_type_affinity: str

@router.post("/variants/score", response_model=VariantResponse)
def score_variant(request: VariantRequest):
    """
    Computes the confidence score of a textual variant based on its manuscript witnesses.
    """
    if not request.witnesses:
        raise HTTPException(status_code=400, detail="Must provide at least one manuscript witness.")
        
    score_data = calculate_variant_score(request.witnesses, request.variant_text)
    
    return VariantResponse(
        verse_ref=request.verse_ref,
        variant_text=request.variant_text,
        confidence_score=score_data["confidence"],
        witness_weight=score_data["weight"],
        text_type_affinity=score_data["affinity"]
    )
