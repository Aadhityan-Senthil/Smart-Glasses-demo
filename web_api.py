from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
import asyncio
from pathlib import Path
from datetime import datetime
import json
import shutil
from typing import Optional, List

from config import Config
from video_capture import VideoCaptureHandler
from cv_analyzer import CVAnalyzer
from telegram_handler import TelegramHandler

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class RecordingRequest(BaseModel):
    duration: Optional[int] = None
    quality: Optional[str] = None

class AnalysisResponse(BaseModel):
    success: bool
    message: str
    results: Optional[dict] = None

class StatusResponse(BaseModel):
    status: str
    timestamp: str
    system_info: dict

class DetectionAlert(BaseModel):
    timestamp: str
    detection_type: str
    confidence: float
    location: dict
    severity: str

app = FastAPI(title="Smart Glasses Demo API", version="1.0.0")

# Add CORS middleware for web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
video_handler = None
cv_analyzer = None
telegram_handler = None

@app.on_event("startup")
async def startup_event():
    """Initialize all components on startup"""
    global video_handler, cv_analyzer, telegram_handler
    
    try:
        # Validate configuration
        Config.validate_config()
        
        # Initialize components
        video_handler = VideoCaptureHandler()
        cv_analyzer = CVAnalyzer()
        
        # Initialize Telegram handler with callbacks
        telegram_handler = TelegramHandler(
            video_callback=video_handler.record_video,
            analysis_callback=cv_analyzer.analyze_video,
            stop_callback=video_handler.stop_recording
        )
        # (Telegram bot is started only from main.py, not here)
        logger.info("Smart Glasses Demo API started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize API: {e}")
        raise

@app.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Smart Glasses Demo API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "health": "/health",
            "record": "/record",
            "analyze": "/analyze",
            "upload": "/upload",
            "status": "/status",
            "videos": "/videos",
            "latest": "/latest"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "video_handler": video_handler is not None,
            "cv_analyzer": cv_analyzer is not None,
            "telegram_handler": telegram_handler is not None
        }
    }

@app.post("/record")
async def start_recording(
    request: RecordingRequest,
    background_tasks: BackgroundTasks
):
    """Start video recording"""
    try:
        if not video_handler:
            raise HTTPException(status_code=500, detail="Video handler not initialized")
        
        # Record video in background
        background_tasks.add_task(
            _record_and_process,
            request.duration,
            request.quality
        )
        
        return {
            "success": True,
            "message": "Recording started",
            "duration": request.duration or Config.VIDEO_DURATION,
            "quality": request.quality or Config.VIDEO_QUALITY
        }
        
    except Exception as e:
        logger.error(f"Error starting recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/{video_filename}")
async def analyze_video(
    video_filename: str,
    background_tasks: BackgroundTasks
):
    """Analyze a specific video file"""
    try:
        video_path = Config.VIDEO_STORAGE_PATH / video_filename
        
        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Video file not found")
        
        if not cv_analyzer:
            raise HTTPException(status_code=500, detail="CV analyzer not initialized")
        
        # Run analysis in background
        background_tasks.add_task(_analyze_and_notify, str(video_path))
        
        return {
            "success": True,
            "message": f"Analysis started for {video_filename}",
            "video_path": str(video_path)
        }
        
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    analyze: bool = True
):
    """Upload and optionally analyze a video file"""
    try:
        # Validate file type
        if not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        # Save uploaded file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"uploaded_{timestamp}_{file.filename}"
        file_path = Config.VIDEO_STORAGE_PATH / filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        response = {
            "success": True,
            "message": "Video uploaded successfully",
            "filename": filename,
            "file_path": str(file_path)
        }
        
        # Analyze if requested
        if analyze and cv_analyzer:
            try:
                results = cv_analyzer.analyze_video(str(file_path))
                response["analysis"] = results
                
                # Send results to Telegram
                if telegram_handler and results:
                    await telegram_handler.send_analysis_results(results)
                
            except Exception as e:
                response["analysis_error"] = str(e)
        
        return response
        
    except Exception as e:
        logger.error(f"Error uploading video: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get system status"""
    try:
        # Get video files count
        video_files = list(Config.VIDEO_STORAGE_PATH.glob("*.mp4"))
        
        system_info = {
            "video_count": len(video_files),
            "storage_path": str(Config.VIDEO_STORAGE_PATH),
            "device": cv_analyzer.device if cv_analyzer else "unknown",
            "model_loaded": cv_analyzer.model is not None if cv_analyzer else False,
            "telegram_bot_active": telegram_handler is not None,
            "confidence_threshold": Config.CONFIDENCE_THRESHOLD,
            "alert_threshold": Config.ALERT_THRESHOLD
        }
        
        return StatusResponse(
            status="active",
            timestamp=datetime.now().isoformat(),
            system_info=system_info
        )
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/videos")
async def list_videos():
    """List all available videos"""
    try:
        video_files = []
        
        for video_path in Config.VIDEO_STORAGE_PATH.glob("*.mp4"):
            stat = video_path.stat()
            video_files.append({
                "filename": video_path.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        # Sort by creation time (newest first)
        video_files.sort(key=lambda x: x["created"], reverse=True)
        
        return {
            "success": True,
            "count": len(video_files),
            "videos": video_files
        }
        
    except Exception as e:
        logger.error(f"Error listing videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/videos/{filename}")
async def download_video(filename: str):
    """Download a specific video file"""
    try:
        video_path = Config.VIDEO_STORAGE_PATH / filename
        
        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Video file not found")
        
        return FileResponse(
            path=str(video_path),
            filename=filename,
            media_type='video/mp4'
        )
        
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/latest")
async def get_latest_video():
    """Get information about the latest video"""
    try:
        video_files = list(Config.VIDEO_STORAGE_PATH.glob("*.mp4"))
        
        if not video_files:
            raise HTTPException(status_code=404, detail="No videos found")
        
        latest_video = max(video_files, key=lambda x: x.stat().st_mtime)
        stat = latest_video.stat()
        
        return {
            "success": True,
            "filename": latest_video.name,
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "download_url": f"/videos/{latest_video.name}"
        }
        
    except Exception as e:
        logger.error(f"Error getting latest video: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/alerts/test")
async def test_alert():
    """Test alert system by sending a test message to Telegram"""
    try:
        if not telegram_handler:
            raise HTTPException(status_code=500, detail="Telegram handler not initialized")
        
        test_results = {
            'detections': [
                {
                    'class': 'oil_leak',
                    'confidence': 0.95,
                    'bbox': [100, 100, 200, 200],
                    'timestamp': datetime.now().isoformat()
                }
            ],
            'analysis_time': 2.5,
            'summary': {
                'total_detections': 1,
                'high_confidence_detections': 1,
                'detection_types': {
                    'oil_leak': {
                        'count': 1,
                        'max_confidence': 0.95,
                        'avg_confidence': 0.95
                    }
                }
            }
        }
        
        await telegram_handler.send_analysis_results(test_results)
        
        return {
            "success": True,
            "message": "Test alert sent successfully"
        }
        
    except Exception as e:
        logger.error(f"Error sending test alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/videos/{filename}")
async def delete_video(filename: str):
    """Delete a specific video file"""
    try:
        video_path = Config.VIDEO_STORAGE_PATH / filename
        
        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Video file not found")
        
        video_path.unlink()
        
        return {
            "success": True,
            "message": f"Video {filename} deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Error deleting video: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task functions
async def _record_and_process(duration=None, quality=None):
    """Background task to record video and optionally analyze it"""
    try:
        # Record video
        video_path = video_handler.record_video(duration)
        
        if video_path and Path(video_path).exists():
            logger.info(f"Video recorded successfully: {video_path}")
            
            # Send to Telegram
            if telegram_handler:
                await telegram_handler.send_video(
                    video_path,
                    f"🎥 New recording completed! Duration: {duration or Config.VIDEO_DURATION}s"
                )
            
            # Auto-analyze if enabled
            if Config.ENABLE_REAL_TIME_ALERTS:
                await _analyze_and_notify(video_path)
        
    except Exception as e:
        logger.error(f"Error in record and process task: {e}")

async def _analyze_and_notify(video_path):
    """Background task to analyze video and send notifications"""
    try:
        if not cv_analyzer:
            return
        
        # Generate output path for processed video
        video_file = Path(video_path)
        processed_path = Config.PROCESSED_STORAGE_PATH / f"processed_{video_file.name}"
        
        # Analyze video
        results = cv_analyzer.analyze_video(video_path, str(processed_path))
        
        if results and telegram_handler:
            await telegram_handler.send_analysis_results(results)
        
    except Exception as e:
        logger.error(f"Error in analyze and notify task: {e}")

def start_server():
    """Start the FastAPI server"""
    uvicorn.run(
        "web_api:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=False,
        log_level=Config.LOG_LEVEL.lower()
    )

if __name__ == "__main__":
    start_server()
