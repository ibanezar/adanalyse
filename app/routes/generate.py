from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import GeneratedPrompt, Pattern
from app.services.prompt_gen import generate_prompt_for_pattern

router = APIRouter()


@router.post("/generate")
def generate(
    pattern_id: int = Form(...),
    target_product: str = Form(...),
    target_market: str = Form(""),
    db: Session = Depends(get_db),
):
    pattern = db.query(Pattern).filter(Pattern.id == pattern_id).first()
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")

    prompt_text = generate_prompt_for_pattern(
        db, pattern, target_product.strip(), target_market.strip() or None
    )

    record = GeneratedPrompt(
        based_on_pattern_id=pattern.id,
        target_product=target_product.strip(),
        prompt_text=prompt_text,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "based_on_pattern_id": pattern.id,
        "target_product": record.target_product,
        "prompt_text": record.prompt_text,
    }
