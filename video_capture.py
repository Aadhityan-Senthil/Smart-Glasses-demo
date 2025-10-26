import cv2
import time
import threading
import logging
from datetime import datetime
from pathlib import Path
from config import Config
import numpy as np

logger = logging.getLogger(__name__)

class VideoCaptureHandler:
    """Handles video capture from camera with various recording modes"""
    
    def __init__(self):
        self.camera = None
        self.is_recording = False
        self.current_video_path = None
        self.frame_buffer = []
        self.recording_thread = None
        
    def initialize_camera(self):
        """Initialize camera connection"""
        try:
            self.camera = cv2.VideoCapture(Config.CAMERA_INDEX)
            
            # Set camera properties based on quality
            if Config.VIDEO_QUALITY == '1080p':
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            elif Config.VIDEO_QUALITY == '720p':
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            else:  # 480p default
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 854)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            self.camera.set(cv2.CAP_PROP_FPS, Config.FPS)
            
            # Test camera
            ret, frame = self.camera.read()
            if not ret:
                raise Exception("Could not read from camera")
            
            logger.info(f"Camera initialized successfully - {Config.VIDEO_QUALITY} at {Config.FPS} FPS")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            return False
    
    def record_video(self, duration=None, output_path=None):
        """Record video for specified duration"""
        if not self.camera:
            if not self.initialize_camera():
                return None
        
        duration = duration or Config.VIDEO_DURATION
        
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Config.VIDEO_STORAGE_PATH / f"video_{timestamp}.mp4"
        
        # Get frame dimensions
        width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Define codec and create VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, Config.FPS, (width, height))
        
        if not out.isOpened():
            logger.error("Failed to create video writer")
            return None
        
        logger.info(f"Starting video recording for {duration} seconds...")
        self.is_recording = True
        self.current_video_path = output_path
        
        start_time = time.time()
        frame_count = 0
        
        try:
            while self.is_recording and (time.time() - start_time) < duration:
                ret, frame = self.camera.read()
                if not ret:
                    logger.warning("Could not read frame from camera")
                    break
                
                # Add timestamp overlay
                timestamp_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(frame, timestamp_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                out.write(frame)
                frame_count += 1
                
                # Store frame in buffer for real-time analysis
                if len(self.frame_buffer) > 30:  # Keep last 30 frames
                    self.frame_buffer.pop(0)
                self.frame_buffer.append(frame.copy())
                
                time.sleep(1/Config.FPS)
        
        except Exception as e:
            logger.error(f"Error during video recording: {e}")
        
        finally:
            out.release()
            self.is_recording = False
            
        logger.info(f"Video recording completed: {frame_count} frames, saved to {output_path}")
        return str(output_path)
    
    def start_continuous_recording(self):
        """Start continuous recording in background thread"""
        if self.recording_thread and self.recording_thread.is_alive():
            logger.warning("Continuous recording already running")
            return
        
        self.recording_thread = threading.Thread(target=self._continuous_recording_loop)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        logger.info("Started continuous recording thread")
    
    def _continuous_recording_loop(self):
        """Internal method for continuous recording"""
        while True:
            try:
                video_path = self.record_video()
                if video_path:
                    logger.info(f"Continuous recording saved: {video_path}")
                    # You can add logic here to process the video immediately
                time.sleep(5)  # Short break between recordings
            except Exception as e:
                logger.error(f"Error in continuous recording: {e}")
                time.sleep(10)  # Longer break on error
    
    def stop_recording(self):
        """Stop current recording"""
        self.is_recording = False
        logger.info("Recording stop requested")
    
    def capture_frame(self):
        """Capture a single frame"""
        if not self.camera:
            if not self.initialize_camera():
                return None
        
        ret, frame = self.camera.read()
        if ret:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            frame_path = Config.VIDEO_STORAGE_PATH / f"frame_{timestamp}.jpg"
            cv2.imwrite(str(frame_path), frame)
            return str(frame_path)
        return None
    
    def get_latest_frame(self):
        """Get the latest frame from buffer"""
        if self.frame_buffer:
            return self.frame_buffer[-1]
        return None
    
    def release_camera(self):
        """Release camera resources"""
        self.is_recording = False
        if self.camera:
            self.camera.release()
            self.camera = None
        logger.info("Camera resources released")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.release_camera()
