from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Ad, AdFeature, Pattern
from app.services.clustering import build_pattern_for_product

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _ads_with_features(db: Session, product: str, market: str | None, outcome: str):
    query = db.query(Ad).filter(Ad.product == product, Ad.outcome == outcome)
    if market:
        query = query.filter(Ad.market == market)
    ads = query.all()
    out = []
    for ad in ads:
        feature = db.query(AdFeature).filter(AdFeature.ad_id == ad.id).first()
        out.append({"ad": ad, "feature": feature})
    return out


@router.get("/report/{product}")
def get_report(
    product: str,
    request: Request,
    market: str | None = Query(default=None),
    format: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    pattern_data = build_pattern_for_product(db, product, market)

    pattern = None
    if pattern_data:
        pattern = Pattern(
            product=product,
            market=market,
            pattern_summary=pattern_data["pattern_summary"],
            supporting_ad_ids=",".join(str(i) for i in pattern_data["supporting_ad_ids"]),
        )
        db.add(pattern)
        db.commit()
        db.refresh(pattern)

    winners = _ads_with_features(db, product, market, "winner")
    mids = _ads_with_features(db, product, market, "mid")
    losers = _ads_with_features(db, product, market, "loser")

    if not winners and not mids and not losers:
        raise HTTPException(status_code=404, detail="No ads found for this product/market")

    if format == "json":
        def serialize(rows):
            return [
                {
                    "ad_id": r["ad"].id,
                    "filename": r["ad"].filename,
                    "media_type": r["ad"].media_type,
                    "metric_note": r["ad"].metric_note,
                    "features": {
                        "hook_type": r["feature"].hook_type if r["feature"] else None,
                        "visual_style": r["feature"].visual_style if r["feature"] else None,
                        "copy_structure": r["feature"].copy_structure if r["feature"] else None,
                        "cta_style": r["feature"].cta_style if r["feature"] else None,
                    }
                    if r["feature"]
                    else None,
                }
                for r in rows
            ]

        return JSONResponse(
            {
                "product": product,
                "market": market,
                "pattern": pattern_data,
                "winners": serialize(winners),
                "mids": serialize(mids),
                "losers": serialize(losers),
            }
        )

    return templates.TemplateResponse(
        request,
        "report.html",
        {
            "product": product,
            "market": market,
            "pattern": pattern,
            "pattern_data": pattern_data,
            "winners": winners,
            "mids": mids,
            "losers": losers,
        },
    )
