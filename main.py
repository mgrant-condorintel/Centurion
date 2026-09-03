#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# main.py  —  HikVision → S3 pipeline orchestrator
#
# Usage:
#   python main.py                    # run all enabled cameras
#   python main.py --camera front-door  # single camera
#   python main.py --once             # capture one frame/clip and exit
# ─────────────────────────────────────────────────────────────

import argparse
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import (
    CAMERAS, CAPTURE_INTERVAL, VIDEO_MODE, LOCAL_BUFFER_DIR,
)
from capture import capture_with_retry
from uploader import upload_bytes, upload_file, verify_bucket_access

# ── Logging setup ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline.log"),
    ],
)
logger = logging.getLogger(__name__)


def process_camera(camera: dict) -> bool:
    """Capture from one camera and upload the result to S3."""
    name = camera["name"]

    if not camera.get("enabled", True):
        logger.debug(f"[{name}] Disabled — skipping")
        return False

    result, filename = capture_with_retry(camera)

    if result is None:
        return False

    if VIDEO_MODE:
        # result is a local file path
        return upload_file(result, name, filename)
    else:
        # result is raw JPEG bytes
        return upload_bytes(result, name, filename)


def run_pipeline(cameras: list, once: bool = False):
    """Main loop — capture and upload from all cameras."""
    logger.info(f"Pipeline starting — {len(cameras)} camera(s), "
                f"mode: {'video' if VIDEO_MODE else 'snapshot'}, "
                f"interval: {CAPTURE_INTERVAL}s")

    os.makedirs(LOCAL_BUFFER_DIR, exist_ok=True)

    while True:
        start = time.time()

        with ThreadPoolExecutor(max_workers=len(cameras)) as pool:
            futures = {
                pool.submit(process_camera, cam): cam["name"]
                for cam in cameras
            }
            for future in as_completed(futures):
                cam_name = futures[future]
                try:
                    ok = future.result()
                    if not ok:
                        logger.warning(f"[{cam_name}] Cycle completed with errors")
                except Exception as exc:
                    logger.error(f"[{cam_name}] Unhandled exception: {exc}", exc_info=True)

        if once:
            logger.info("--once flag set — exiting after first cycle")
            break

        elapsed = time.time() - start
        sleep   = max(0, CAPTURE_INTERVAL - elapsed)
        logger.debug(f"Cycle took {elapsed:.1f}s — sleeping {sleep:.1f}s")
        time.sleep(sleep)


def main():
    parser = argparse.ArgumentParser(description="HikVision → AWS S3 pipeline")
    parser.add_argument(
        "--camera",
        help="Name of a single camera to run (default: all enabled cameras)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Capture one frame/clip per camera and exit",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List configured cameras and exit",
    )
    args = parser.parse_args()

    if args.list:
        print("\nConfigured cameras:")
        for cam in CAMERAS:
            status = "enabled" if cam.get("enabled", True) else "disabled"
            print(f"  {cam['name']:20s}  {status:8s}  {cam['url']}")
        print()
        return

    # Filter cameras
    if args.camera:
        cameras = [c for c in CAMERAS if c["name"] == args.camera]
        if not cameras:
            logger.error(f"Camera '{args.camera}' not found in config")
            sys.exit(1)
    else:
        cameras = [c for c in CAMERAS if c.get("enabled", True)]

    if not cameras:
        logger.error("No enabled cameras found")
        sys.exit(1)

    # Verify S3 access before starting
    if not verify_bucket_access():
        logger.error("Cannot access S3 bucket — check credentials and bucket name")
        sys.exit(1)

    try:
        run_pipeline(cameras, once=args.once)
    except KeyboardInterrupt:
        logger.info("Pipeline stopped by user")


if __name__ == "__main__":
    main()
