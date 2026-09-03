# ─────────────────────────────────────────────────────────────
# capture.py  —  HikVision RTSP frame/clip capture
# ─────────────────────────────────────────────────────────────

import cv2
import time
import os
import logging
from datetime import datetime
from config import (
    LOCAL_BUFFER_DIR, JPEG_QUALITY, CAPTURE_INTERVAL,
    VIDEO_MODE, CLIP_DURATION, MAX_RETRIES, RETRY_DELAY,
)

logger = logging.getLogger(__name__)


def _ensure_buffer(camera_name: str) -> str:
    """Create local buffer directory for this camera."""
    path = os.path.join(LOCAL_BUFFER_DIR, camera_name)
    os.makedirs(path, exist_ok=True)
    return path


def _timestamp() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")


def capture_frame(camera: dict) -> tuple[bytes | None, str]:
    """
    Grab a single JPEG frame from the camera RTSP stream.
    Returns (jpeg_bytes, filename) or (None, '') on failure.
    """
    name = camera["name"]
    url  = camera["url"]

    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        logger.error(f"[{name}] Cannot open stream: {url}")
        cap.release()
        return None, ""

    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        logger.warning(f"[{name}] Failed to read frame")
        return None, ""

    ts       = _timestamp()
    filename = f"{ts}.jpg"
    success, buf = cv2.imencode(
        ".jpg", frame,
        [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY],
    )
    if not success:
        logger.error(f"[{name}] Failed to encode frame")
        return None, ""

    logger.debug(f"[{name}] Captured frame → {filename}")
    return buf.tobytes(), filename


def capture_clip(camera: dict) -> tuple[str | None, str]:
    """
    Record a short video clip from the RTSP stream.
    Returns (local_filepath, filename) or (None, '') on failure.
    """
    name = camera["name"]
    url  = camera["url"]

    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        logger.error(f"[{name}] Cannot open stream: {url}")
        cap.release()
        return None, ""

    fps    = cap.get(cv2.CAP_PROP_FPS) or 15.0
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    ts        = _timestamp()
    filename  = f"{ts}.mp4"
    buf_path  = _ensure_buffer(name)
    out_path  = os.path.join(buf_path, filename)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

    end_time   = time.time() + CLIP_DURATION
    frames_out = 0

    while time.time() < end_time:
        ret, frame = cap.read()
        if not ret:
            logger.warning(f"[{name}] Frame read error mid-clip")
            break
        writer.write(frame)
        frames_out += 1

    cap.release()
    writer.release()

    if frames_out == 0:
        logger.error(f"[{name}] No frames written")
        return None, ""

    logger.info(f"[{name}] Clip recorded: {frames_out} frames → {out_path}")
    return out_path, filename


def capture_with_retry(camera: dict) -> tuple:
    """
    Wrapper that retries capture on failure up to MAX_RETRIES times.
    """
    name = camera["name"]
    for attempt in range(1, MAX_RETRIES + 1):
        if VIDEO_MODE:
            result = capture_clip(camera)
        else:
            result = capture_frame(camera)

        if result[0] is not None:
            return result

        logger.warning(
            f"[{name}] Attempt {attempt}/{MAX_RETRIES} failed. "
            f"Retrying in {RETRY_DELAY}s..."
        )
        time.sleep(RETRY_DELAY)

    logger.error(f"[{name}] All {MAX_RETRIES} attempts failed. Skipping.")
    return None, ""
