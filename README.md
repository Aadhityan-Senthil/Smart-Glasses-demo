# Smart Glasses Demo — Industrial Hazard Detection System

A production-grade Python system that captures video, integrates with Telegram for remote control and notifications, and performs computer-vision analysis to detect industrial hazards (e.g., oil leaks, smoke, fire). It exposes a REST API for automation and can be deployed locally or with Docker.


## Key Features

- Video capture from a local camera with timestamp overlay and adjustable quality/FPS
- Telegram Bot integration for recording, analysis, status, and notifications
- Computer Vision analysis using Ultralytics YOLO + custom rules for hazards
- FastAPI web server with endpoints for recording, uploading, analyzing, and file management
- Structured logging and graceful shutdown, designed for continuous monitoring
- Dockerfile + docker-compose for reproducible deployments


## Repository Layout

```
smart-glasses-demo/
├── main.py               # Application entrypoint (modes: demo, monitor, api)
├── config.py             # Env-driven configuration + logging setup
├── video_capture.py      # Camera handling and video recording
├── cv_analyzer.py        # YOLO + custom CV detection and video annotation
├── telegram_handler.py   # Telegram bot handlers, commands, and send helpers
├── web_api.py            # FastAPI server + endpoints
├── requirements.txt      # Python dependencies
├── setup.py              # Packaging metadata
├── install.sh            # One-shot installer (venv + deps)
├── docker-compose.yml    # Compose for API + optional proxy/monitoring stack
├── Dockerfile            # Production image for API service
├── QUICK_START.md        # Short setup guide
├── .env.example          # Env variables template (copy to .env and edit)
├── videos/               # Raw recorded and uploaded videos
├── processed/            # Post-processed/annotated videos
├── models/               # Model files (default path in config)
└── logs/                 # Log files
```


## Requirements

- Python 3.8+
- A camera device (webcam/USB/integrated)
- Telegram account for bot interaction
- Optional: GPU with CUDA for accelerated inference


## Installation

Option A — One command installer (recommended)

```
./install.sh
```

This script checks Python, installs system packages (where supported), creates a virtualenv, installs Python dependencies (CPU or CUDA build of PyTorch), creates folders, and scaffolds a .env if missing.

Option B — Manual setup

```
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```


## Configuration

1) Copy the environment template and edit values.

```
cp .env.example .env
# Edit .env with your editor
```

2) Environment variables reference:

- Telegram
  - TELEGRAM_BOT_TOKEN: Bot token from @BotFather (required)
  - TELEGRAM_CHAT_ID: Your chat ID (required)
- Camera
  - CAMERA_INDEX: Default 0
  - VIDEO_DURATION: Seconds per recording, default 30
  - VIDEO_QUALITY: 1080p | 720p | 480p, default 720p
  - FPS: Frames per second, default 30
- Computer Vision
  - MODEL_PATH: Path to model file, default models/oil_leak_detector.pt
  - CONFIDENCE_THRESHOLD: Default 0.7
  - NMS_THRESHOLD: Default 0.4
- Storage & Logging
  - VIDEO_STORAGE_PATH: Default ./videos
  - PROCESSED_STORAGE_PATH: Default ./processed
  - LOG_LEVEL: DEBUG | INFO | WARNING | ERROR, default INFO
- API
  - API_HOST: Default 0.0.0.0
  - API_PORT: Default 8000
- Alerts
  - ALERT_THRESHOLD: Default 0.8
  - ENABLE_REAL_TIME_ALERTS: true | false, default true

Security note: Never commit real tokens to version control. Keep .env out of public repos.


## Quick Start

- Verify configuration: ensure .env has valid Telegram credentials
- Activate venv: `source venv/bin/activate`
- Run demo (records ~10s, sends to Telegram, analyzes):

```
python main.py --mode demo
```

Modes

- Demo: `python main.py --mode demo` — one-shot record/analyze/send and run bot
- Monitor: `python main.py --mode monitor` — continuous monitoring + Telegram bot
- API: `python main.py --mode api` — run only the web API service

Default API base URL: http://localhost:8000


## Telegram Bot

Commands

- /start — Show help and Start/Stop buttons
- /record — Record a video now, then analyze and send results
- /analyze — Analyze the most recent video
- /status — System status summary
- /help — Command descriptions

You can also send videos directly to the bot for analysis.


## REST API

Base URL: `http://<host>:<port>` (default `http://localhost:8000`)

- GET / — API metadata
- GET /health — Health check
- POST /record — Start a background recording
  - JSON body: `{ "duration": 20, "quality": "720p" }` (fields optional)
- POST /analyze/{video_filename} — Analyze an existing video
- POST /upload — Upload a video (multipart form)
  - form-data: `file=@yourvideo.mp4`, optional query `?analyze=true|false`
- GET /status — System and model status
- GET /videos — List available videos
- GET /videos/{filename} — Download a specific video
- GET /latest — Retrieve metadata for the latest video
- POST /alerts/test — Send a test alert to Telegram

Example requests

- Start a recording for 10s:
```
curl -X POST http://localhost:8000/record \
  -H "Content-Type: application/json" \
  -d '{"duration": 10, "quality": "720p"}'
```

- Upload a video and analyze it:
```
curl -X POST "http://localhost:8000/upload?analyze=true" \
  -F "file=@/path/to/video.mp4"
```

- Analyze an existing video:
```
curl -X POST http://localhost:8000/analyze/video_20240101_120000.mp4
```


## Computer Vision Pipeline

- Uses Ultralytics YOLO (yolov8n by default if custom model is absent) running on CPU or CUDA
- Adds custom rules for oil leak, smoke, and fire detection using color/texture analysis
- Writes annotated output video when an output path is supplied
- Emits a detection summary with counts, max/avg confidence, and processing time

Results schema (excerpt)

```
{
  "detections": [
    {"frame": 120, "class": "oil_leak", "confidence": 0.87, "bbox": [x1,y1,x2,y2], ...},
    ...
  ],
  "analysis_time": 2.53,
  "processed_video_path": "processed/processed_video_...mp4",
  "summary": {
    "total_detections": 5,
    "high_confidence_detections": 2,
    "detection_types": {
      "oil_leak": {"count": 3, "max_confidence": 0.90, "avg_confidence": 0.78},
      ...
    }
  }
}
```


## Development

- Create venv and install deps (see Installation)
- Run unit/system checks:

```
python test_system.py
```

- Formatting/linting suggestions:

```
black .
flake8 .
```

- Run API locally without Telegram:

```
python main.py --mode api
# or directly with uvicorn if needed
# uvicorn web_api:app --host 0.0.0.0 --port 8000
```


## Docker

Build image

```
docker build -t smart-glasses-demo .
```

Run container

```
docker run -d \
  --name smart-glasses \
  -p 8000:8000 \
  -v $(pwd)/videos:/app/videos \
  -v $(pwd)/processed:/app/processed \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/models:/app/models \
  --env-file .env \
  --device /dev/video0:/dev/video0 \
  smart-glasses-demo
```

Compose (includes optional proxy/monitoring profiles):

```
docker-compose up -d
# or
docker compose up -d
```

If running on Linux, ensure the camera device is mapped (see docker-compose.yml). On macOS/Windows, camera passthrough to containers may be limited.


## Production Notes

- Use HTTPS (reverse proxy such as Nginx) in production
- Protect the API with authentication/authorization if exposed publicly
- Keep tokens/credentials in environment variables or secret stores, not in code
- Monitor disk usage for the videos/ and processed/ directories
- Consider GPU builds of PyTorch and YOLO for higher throughput


## Troubleshooting

- Camera
  - Try other CAMERA_INDEX values (0/1/2)
  - Check permissions and that another app isn’t using the camera
- Telegram
  - Verify TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
  - Ensure the bot isn’t blocked and can message your chat
- Dependencies
  - Activate venv and run `pip install -r requirements.txt` again
  - For CUDA, install appropriate NVIDIA drivers + CUDA toolkit and use the CUDA wheels for PyTorch
- API
  - Check logs in logs/smart_glasses.log
  - Validate endpoint availability at http://localhost:8000/health


## License

MIT License. See LICENSE if included in your distribution.


## Versioning

- v1.0.0 — Initial public release


## Acknowledgements

- Ultralytics YOLO for detection backbone
- python-telegram-bot for Telegram integration
- FastAPI and Uvicorn for the web service
