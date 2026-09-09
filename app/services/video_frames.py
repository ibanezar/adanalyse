"""Frame sampling for video ads.

Uses ffmpeg (via subprocess) to pull a small number of representative
frames out of a video so they can be sent to the vision LLM alongside
the image-analysis prompt.
"""

import subprocess
import tempfile
from pathlib import Path

MAX_FRAMES = 8


def _probe_duration(video_path: str) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            video_path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def extract_frames(video_path: str, max_frames: int = MAX_FRAMES) -> list[bytes]:
    """Extract up to `max_frames` evenly-spaced JPEG frames from a video.

    Returns a list of raw JPEG bytes, in chronological order.
    """
    try:
        duration = _probe_duration(video_path)
    except (subprocess.CalledProcessError, ValueError):
        duration = 0.0

    # Fall back to a fixed 1-second cadence if duration can't be read.
    if duration <= 0:
        interval = 1.0
        count = max_frames
    else:
        count = min(max_frames, max(1, int(duration)))
        interval = duration / count

    frames: list[bytes] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(count):
            timestamp = i * interval
            out_path = Path(tmpdir) / f"frame_{i:02d}.jpg"
            subprocess.run(
                [
                    "ffmpeg",
                    "-ss",
                    str(timestamp),
                    "-i",
                    video_path,
                    "-frames:v",
                    "1",
                    "-q:v",
                    "2",
                    "-y",
                    str(out_path),
                ],
                capture_output=True,
                check=False,
            )
            if out_path.exists():
                frames.append(out_path.read_bytes())

    return frames
