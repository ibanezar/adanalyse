# adanalyse — Winning Ads Analyzer

Upload your own ad creatives (image or video), extract structured "creative
DNA" from each one via an LLM vision call, find the patterns that separate
winners from losers, and generate new ad prompts for a new product based on
the winning pattern.

## Stack

Python + FastAPI + SQLite (SQLAlchemy ORM), LLM calls via the Anthropic API.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export ANTHROPIC_API_KEY=sk-ant-...
# optional overrides:
# export ANTHROPIC_ANALYZE_MODEL=claude-sonnet-4-5
# export ANTHROPIC_GENERATE_MODEL=claude-sonnet-4-5

uvicorn app.main:app --reload
```

Video analysis requires `ffmpeg`/`ffprobe` on PATH.

Open http://localhost:8000 for a minimal upload form.

## API

- `POST /ads` — multipart form: `file`, `product`, `market`, `outcome`
  (`winner`/`mid`/`loser`), `metric_note` (optional). Stores the file under
  `storage/uploads/` and creates an `ads` row.
- `POST /ads/{id}/analyze` — runs the vision LLM (image directly, or sampled
  video frames) against a fixed JSON schema and stores the result in
  `ad_features`.
- `GET /report/{product}?market=...` — HTML report: the extracted winning
  pattern plus a grid of winners/mids/losers with their tags. Add
  `?format=json` for a JSON payload instead. Persists a `patterns` row each
  time it runs.
- `POST /generate` — form: `pattern_id`, `target_product`, `target_market`
  (optional). Produces an image-gen prompt + ad copy for a new product,
  following the winning pattern's hook/visual style/copy structure/CTA, and
  stores it in `generated_prompts`.

## How pattern extraction works

For a given product (optionally scoped to a market), winning ads are grouped
by `(hook_type, visual_style, copy_structure)`. The most frequent group is
"the pattern" — this needs no ML at small ad counts; it can be swapped for
embedding-based clustering later (see `app/services/clustering.py`) without
touching callers.

## Repo layout

```
app/
├── main.py                # FastAPI app entrypoint
├── db.py                  # SQLite setup + session
├── models.py              # SQLAlchemy models
├── routes/
│   ├── upload.py          # POST /ads
│   ├── analyze.py         # POST /ads/{id}/analyze
│   ├── report.py          # GET /report/{product}
│   └── generate.py        # POST /generate
├── services/
│   ├── video_frames.py    # ffmpeg frame sampling
│   ├── feature_extract.py # LLM call -> structured JSON
│   ├── clustering.py      # frequency-based pattern extraction
│   └── prompt_gen.py      # new ad prompts from winning pattern
└── templates/             # upload form + report page
storage/
└── uploads/                # raw ad files (gitignored)
```
