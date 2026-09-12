# ─────────────────────────────────────────────────────────────
# config.py  —  HikVision → AWS S3 Pipeline Configuration
# ─────────────────────────────────────────────────────────────

# ── AWS ──────────────────────────────────────────────────────
AWS_ACCESS_KEY_ID     = "AKIAIOSFODNN74FT9MW2"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYjAwERTiU"
AWS_REGION            = "us-east-2"
S3_BUCKET             = "condor-centurion-events"

# S3 key prefix — footage is stored as:
# s3://<bucket>/<S3_PREFIX>/<camera_name>/YYYY-MM-DD/HH-MM-SS.jpg
S3_PREFIX             = "hikvision-footage"

# ── CAMERAS ──────────────────────────────────────────────────
# Add as many cameras as needed.
# RTSP stream URL format:
#   rtsp://<user>:<pass>@<ip>:<port>/Streaming/Channels/<channel>
CAMERAS = [
    {
        "name":     "I95-South-Fairfield",
        "url":      "rtsp://condor-admin:6tfc%RDX4esz#W@89.43.73.224:554/Streaming/Channels/101",
        "enabled":  True,
    },
    {
        "name":     "I95-North-Fairfield",
        "url":      "rtsp://condor-admin:Xcvb$2356@98.73.45.128:554/Streaming/Channels/101",
        "enabled":  True,
    },
    {
        "name":     "server-room",
        "url":      "rtsp://condor-admin:nhy67ujmNHY^&UJM@192.168.1.102:554/Streaming/Channels/101",
        "enabled":  True,
    },
]

# ── CAPTURE SETTINGS ─────────────────────────────────────────
# How often to capture a frame (seconds)
CAPTURE_INTERVAL      = 10

# Save clips as short MP4 segments instead of frames
# Set to True to upload video clips rather than JPEG snapshots
VIDEO_MODE            = False

# Length of each video clip in seconds (VIDEO_MODE only)
CLIP_DURATION         = 60

# JPEG quality for snapshot mode (1-100)
JPEG_QUALITY          = 85

# Max consecutive connection failures before skipping a camera
MAX_RETRIES           = 5

# Seconds to wait before retrying a failed camera
RETRY_DELAY           = 15

# ── LOCAL BUFFER ─────────────────────────────────────────────
# Temporarily store frames/clips here before uploading
# Useful if you want to keep a local copy too
LOCAL_BUFFER_DIR      = "/tmp/hikvision_buffer"
KEEP_LOCAL_COPY       = False
