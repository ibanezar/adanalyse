"""Frequency-based pattern extraction across winning ads.

At small sample sizes there's no need for embeddings/ML: group winning
ads by (hook_type, visual_style, copy_structure) and treat the most
common combination as "the pattern". This can be swapped for
embedding-based clustering later without changing the caller.
"""

from collections import Counter

from sqlalchemy.orm import Session

from app.models import Ad, AdFeature


def build_pattern_for_product(db: Session, product: str, market: str | None = None) -> dict | None:
    query = (
        db.query(Ad, AdFeature)
        .join(AdFeature, AdFeature.ad_id == Ad.id)
        .filter(Ad.product == product, Ad.outcome == "winner")
    )
    if market:
        query = query.filter(Ad.market == market)

    rows = query.all()
    if not rows:
        return None

    def key_of(feature: AdFeature) -> tuple:
        return (
            feature.hook_type or "unknown",
            feature.visual_style or "unknown",
            feature.copy_structure or "unknown",
        )

    counter: Counter = Counter()
    groups: dict[tuple, list[Ad]] = {}
    cta_counter: Counter = Counter()

    for ad, feature in rows:
        k = key_of(feature)
        counter[k] += 1
        groups.setdefault(k, []).append(ad)
        if feature.cta_style:
            cta_counter[feature.cta_style] += 1

    (hook_type, visual_style, copy_structure), count = counter.most_common(1)[0]
    supporting_ads = groups[(hook_type, visual_style, copy_structure)]
    total = len(rows)
    top_cta = cta_counter.most_common(1)[0][0] if cta_counter else "unknown"

    market_note = f" ({market})" if market else ""
    summary = (
        f"{count} of {total} winning {product}{market_note} ads use a '{hook_type}' hook, "
        f"'{visual_style}' visual style, and a '{copy_structure}' copy structure, "
        f"most commonly ending in a '{top_cta}' CTA."
    )

    return {
        "product": product,
        "market": market,
        "pattern_summary": summary,
        "supporting_ad_ids": [ad.id for ad in supporting_ads],
        "hook_type": hook_type,
        "visual_style": visual_style,
        "copy_structure": copy_structure,
        "cta_style": top_cta,
    }
