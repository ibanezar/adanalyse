import mimetypes
import os

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Ad

router = APIRouter()

UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "storage",
    "uploads",
)

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm", ".mkv"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
VALID_OUTCOMES = {"winner", "mid", "loser"}


def _media_type_for(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in IMAGE_EXTENSIONS:
        return "image"

    guessed, _ = mimetypes.guess_type(filename)
    if guessed:
        if guessed.startswith("video/"):
            return "video"
        if guessed.startswith("image/"):
            return "image"
    raise HTTPException(status_code=400, detail=f"Unsupported file type: {filename}")


@router.post("/ads")
async def create_ad(
    file: UploadFile,
    product: str = Form(...),
    market: str = Form(""),
    outcome: str = Form(...),
    metric_note: str = Form(""),
    db: Session = Depends(get_db),
):
    outcome = outcome.lower().strip()
    if outcome not in VALID_OUTCOMES:
        raise HTTPException(
            status_code=400, detail=f"outcome must be one of {sorted(VALID_OUTCOMES)}"
        )

    media_type = _media_type_for(file.filename)

    ad = Ad(
        filename=file.filename,
        media_type=media_type,
        product=product.strip(),
        market=market.strip() or None,
        outcome=outcome,
        metric_note=metric_note.strip() or None,
    )
    db.add(ad)
    db.commit()
    db.refresh(ad)

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    dest_path = os.path.join(UPLOAD_DIR, f"{ad.id}{ext}")
    with open(dest_path, "wb") as out:
        out.write(await file.read())

    return {
        "id": ad.id,
        "filename": ad.filename,
        "media_type": ad.media_type,
        "product": ad.product,
        "market": ad.market,
        "outcome": ad.outcome,
        "metric_note": ad.metric_note,
    }


def stored_path_for_ad(ad: Ad) -> str:
    ext = os.path.splitext(ad.filename)[1]
    return os.path.join(UPLOAD_DIR, f"{ad.id}{ext}")
