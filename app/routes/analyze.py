import json
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Ad, AdFeature
from app.routes.upload import stored_path_for_ad
from app.services import feature_extract, video_frames

router = APIRouter()


@router.post("/ads/{ad_id}/analyze")
def analyze_ad(ad_id: int, db: Session = Depends(get_db)):
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    file_path = stored_path_for_ad(ad)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Stored ad file missing")

    if ad.media_type == "image":
        result = feature_extract.extract_features_from_image(file_path)
    elif ad.media_type == "video":
        frames = video_frames.extract_frames(file_path)
        if not frames:
            raise HTTPException(status_code=422, detail="Could not extract frames from video")
        result = feature_extract.extract_features_from_video(frames)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown media_type: {ad.media_type}")

    parsed = result["parsed"]

    existing = db.query(AdFeature).filter(AdFeature.ad_id == ad.id).first()
    if existing:
        feature = existing
    else:
        feature = AdFeature(ad_id=ad.id)
        db.add(feature)

    feature.hook_type = parsed.get("hook_type")
    feature.hook_description = parsed.get("hook_description")
    feature.first_3_sec_visual = parsed.get("first_3_sec_visual")
    feature.visual_style = parsed.get("visual_style")
    feature.copy_structure = parsed.get("copy_structure")
    feature.cta_style = parsed.get("cta_style")
    feature.pacing_notes = parsed.get("pacing_notes")
    feature.raw_json = json.dumps(parsed)

    db.commit()
    db.refresh(feature)

    return {
        "ad_id": ad.id,
        "hook_type": feature.hook_type,
        "hook_description": feature.hook_description,
        "first_3_sec_visual": feature.first_3_sec_visual,
        "visual_style": feature.visual_style,
        "copy_structure": feature.copy_structure,
        "cta_style": feature.cta_style,
        "pacing_notes": feature.pacing_notes,
    }
