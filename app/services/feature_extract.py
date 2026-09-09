"""LLM-based "creative DNA" extraction for a single ad (image or video)."""

import base64
import json
import mimetypes
import os

from anthropic import Anthropic

MODEL = os.environ.get("ANTHROPIC_ANALYZE_MODEL", "claude-sonnet-4-5")

SYSTEM_PROMPT = """You are analyzing an ad creative. Return ONLY valid JSON, no markdown, no preamble, matching this schema:
{
  "hook_type": string,
  "hook_description": string,
  "first_3_sec_visual": string,
  "visual_style": string,
  "copy_structure": string,
  "cta_style": string,
  "pacing_notes": string or null
}
Base every field only on what is visible/audible in the provided material. Be specific and concise."""

_client: Anthropic | None = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


def _image_block(image_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": base64.standard_b64encode(image_bytes).decode("utf-8"),
        },
    }


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def extract_features_from_image(image_path: str) -> dict:
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    media_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"

    message = _get_client().messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    _image_block(image_bytes, media_type),
                    {
                        "type": "text",
                        "text": "Analyze this ad creative image and return the JSON described in the system prompt.",
                    },
                ],
            }
        ],
    )
    raw_text = message.content[0].text
    parsed = _parse_json_response(raw_text)
    return {"parsed": parsed, "raw_text": raw_text}


def extract_features_from_video(frames: list[bytes], transcript: str | None = None) -> dict:
    content = [_image_block(frame) for frame in frames]
    instruction = (
        "The images above are sequential frames sampled from a single video ad, in "
        "chronological order. Analyze the ad and return the JSON described in the "
        "system prompt, including pacing_notes (cut frequency, overall length/feel)."
    )
    if transcript:
        instruction += f"\n\nTranscript / on-screen text:\n{transcript}"
    content.append({"type": "text", "text": instruction})

    message = _get_client().messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )
    raw_text = message.content[0].text
    parsed = _parse_json_response(raw_text)
    return {"parsed": parsed, "raw_text": raw_text}
