"""Turn a winning pattern into new ad-creation prompts for a new product."""

import os

from anthropic import Anthropic
from sqlalchemy.orm import Session

from app.models import Ad, AdFeature, Pattern

MODEL = os.environ.get("ANTHROPIC_GENERATE_MODEL", "claude-sonnet-4-5")

_client: Anthropic | None = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


def _gather_style_detail(db: Session, pattern: Pattern) -> str:
    ad_ids = [int(x) for x in pattern.supporting_ad_ids.split(",") if x]
    features = db.query(AdFeature).filter(AdFeature.ad_id.in_(ad_ids)).all()

    lines = []
    for f in features:
        lines.append(
            f"- hook: {f.hook_type} ({f.hook_description}); "
            f"first 3s visual: {f.first_3_sec_visual}; "
            f"visual style: {f.visual_style}; "
            f"copy structure: {f.copy_structure}; "
            f"cta: {f.cta_style}; "
            f"pacing: {f.pacing_notes or 'n/a'}"
        )
    return "\n".join(lines)


def generate_prompt_for_pattern(
    db: Session, pattern: Pattern, target_product: str, target_market: str | None = None
) -> str:
    style_detail = _gather_style_detail(db, pattern)
    market_note = f" for the {target_market} market" if target_market else ""

    user_prompt = f"""You write ad-creative briefs for performance marketers.

Winning pattern observed on past ads:
{pattern.pattern_summary}

Supporting evidence from the individual winning ads:
{style_detail}

Task: apply this exact winning pattern (same hook type, visual style, copy
structure, and CTA style) to a NEW product called "{target_product}"{market_note}.

Return two clearly labeled sections:
1. IMAGE-GEN PROMPT: a single, detailed prompt suitable for an image
   generation model, describing the scene, subject, composition, and visual
   style so it matches the winning pattern.
2. AD COPY: headline + primary text + CTA, following the same copy
   structure and CTA style as the winning ads, tailored to {target_product}.
"""

    message = _get_client().messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text
