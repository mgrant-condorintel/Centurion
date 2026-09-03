# Centurion
Ingestor for live camera feed to store on AWS S3 Buckets

# HikVision → AWS S3 Pipeline

Captures live frames or video clips from HikVision RTSP streams and uploads them to an AWS S3 bucket.

## Setup

```bash
pip install -r requirements.txt
```

## Configuration

Edit `config.py`:

```python
# AWS credentials
AWS_ACCESS_KEY_ID     = "YOUR_ACCESS_KEY_ID"
AWS_SECRET_ACCESS_KEY = "YOUR_SECRET_ACCESS_KEY"
AWS_REGION            = "us-east-1"
S3_BUCKET             = "your-bucket-name"

# Add your cameras
CAMERAS = [
    {
        "name": "front-door",
        "url":  "rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101",
        "enabled": True,
    },
]
```

### HikVision RTSP URL format

```
rtsp://<user>:<password>@<ip>:<port>/Streaming/Channels/<channel>
```

- Main stream:  `/Streaming/Channels/101`
- Sub stream:   `/Streaming/Channels/102`
- Channel 2:    `/Streaming/Channels/201`

## Usage

```bash
# Run all enabled cameras (snapshot mode, loops forever)
python main.py

# Run a single camera
python main.py --camera front-door

# Capture one frame per camera and exit (good for cron)
python main.py --once

# List configured cameras
python main.py --list

# Video clip mode — set in config.py
# VIDEO_MODE = True
# CLIP_DURATION = 60  # seconds per clip
```

## S3 Structure

Footage is stored as:
```
s3://<bucket>/hikvision-footage/<camera-name>/YYYY-MM-DD/HH-MM-SS.jpg
s3://<bucket>/hikvision-footage/<camera-name>/YYYY-MM-DD/HH-MM-SS.mp4
```

## Running as a service (systemd)

```ini
[Unit]
Description=HikVision S3 Pipeline
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/hikvision-s3/main.py
WorkingDirectory=/opt/hikvision-s3
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable hikvision-s3
sudo systemctl start hikvision-s3
```

## Running on a cron schedule

```bash
# Capture one frame every 5 minutes
*/5 * * * * /usr/bin/python3 /opt/hikvision-s3/main.py --once
```
