#!/usr/bin/env python3
"""
Smart Glasses Demo - Main Application
A production-ready system for capturing video, sending through Telegram API,
and performing computer vision analysis for oil leak and hazard detection.
"""

import asyncio
import logging
import signal
import sys
import threading
import time
from pathlib import Path
from datetime import datetime

from config import Config, logger
from video_capture import VideoCaptureHandler
from cv_analyzer import CVAnalyzer
from telegram_handler import TelegramHandler
from web_api import start_server

class SmartGlassesDemo:
    """Main application class that coordinates all components"""
    
    def __init__(self):
        self.video_handler = None
        self.cv_analyzer = None
        self.telegram_handler = None
        self.api_thread = None
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self):
        """Initialize all components"""
        logger.info("Initializing Smart Glasses Demo System...")
        
        try:
            # Validate configuration
            Config.validate_config()
            logger.info("Configuration validated successfully")
            
            # Initialize video capture handler
            self.video_handler = VideoCaptureHandler()
            logger.info("Video capture handler initialized")
            
            # Initialize computer vision analyzer
            self.cv_analyzer = CVAnalyzer()
            if not self.cv_analyzer.load_model():
                logger.warning("Failed to load CV model, continuing with limited functionality")
            logger.info("Computer vision analyzer initialized")
            
            # Initialize Telegram handler with callbacks
            self.telegram_handler = TelegramHandler(
                video_callback=self._video_recording_callback,
                analysis_callback=self._analysis_callback,
                stop_callback=self.video_handler.stop_recording
            )
            logger.info("Telegram handler initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            return False
    
    def _video_recording_callback(self, duration=None):
        """Callback function for video recording requests"""
        try:
            logger.info(f"Recording video - Duration: {duration or Config.VIDEO_DURATION}s")
            video_path = self.video_handler.record_video(duration)
            
            if video_path:
                logger.info(f"Video recorded successfully: {video_path}")
                
                # Auto-analyze if real-time alerts are enabled
                if Config.ENABLE_REAL_TIME_ALERTS:
                    threading.Thread(
                        target=self._async_analysis,
                        args=(video_path,),
                        daemon=True
                    ).start()
            
            return video_path
            
        except Exception as e:
            logger.error(f"Error in video recording callback: {e}")
            return None
    
    def _analysis_callback(self, video_path):
        """Callback function for video analysis requests"""
        try:
            logger.info(f"Analyzing video: {video_path}")
            
            # Generate output path for processed video
            video_file = Path(video_path)
            processed_path = Config.PROCESSED_STORAGE_PATH / f"processed_{video_file.name}"
            
            # Perform analysis
            results = self.cv_analyzer.analyze_video(video_path, str(processed_path))
            
            if results:
                logger.info(f"Analysis completed: {results['summary']['total_detections']} detections found")
            else:
                logger.warning("Analysis returned no results")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in analysis callback: {e}")
            return None
    
    def _async_analysis(self, video_path):
        """Run analysis in a separate thread"""
        try:
            results = self._analysis_callback(video_path)
            
            if results and self.telegram_handler:
                # Send results to Telegram (this needs to be run in async context)
                asyncio.create_task(
                    self.telegram_handler.send_analysis_results(results)
                )
                
        except Exception as e:
            logger.error(f"Error in async analysis: {e}")
    
    async def start_telegram_bot(self):
        """Start the Telegram bot asynchronously in the main thread"""
        try:
            await self.telegram_handler.run_bot()
            logger.info("Telegram bot started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
            return False
    
    def start_web_api(self):
        """Start the web API server in a separate thread"""
        try:
            self.api_thread = threading.Thread(target=start_server, daemon=True)
            self.api_thread.start()
            logger.info(f"Web API server started on {Config.API_HOST}:{Config.API_PORT}")
            return True
        except Exception as e:
            logger.error(f"Failed to start web API: {e}")
            return False
    
    async def start_continuous_monitoring(self):
        """Start continuous monitoring mode (async)"""
        logger.info("Starting continuous monitoring mode...")
        try:
            # Start continuous recording if enabled
            # await self.video_handler.start_continuous_recording()
            self.running = True
            monitor_interval = 30  # Check every 30 seconds
            while self.running:
                try:
                    self._health_check()
                    await asyncio.sleep(monitor_interval)
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    await asyncio.sleep(10)  # Short delay before retrying
        except Exception as e:
            logger.error(f"Error in continuous monitoring: {e}")
    
    def _health_check(self):
        """Perform system health check"""
        try:
            # Check camera availability
            if self.video_handler and not self.video_handler.camera:
                logger.warning("Camera not initialized, attempting to reinitialize...")
                self.video_handler.initialize_camera()
            
            # Check storage space
            storage_path = Config.VIDEO_STORAGE_PATH
            if storage_path.exists():
                # Get storage stats
                stat = storage_path.stat()
                # You could add logic here to check available disk space
            
            # Check if Telegram bot is responsive
            # This would require implementing a ping mechanism
            
            logger.debug("Health check completed successfully")
            
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
    
    def run_demo_mode(self):
        """Run a quick demo of the system"""
        logger.info("Running Smart Glasses Demo...")
        
        print("\n" + "="*50)
        print("🤖 SMART GLASSES DEMO - OIL LEAK DETECTOR")
        print("="*50)
        print(f"📹 Video Storage: {Config.VIDEO_STORAGE_PATH}")
        print(f"🔍 Confidence Threshold: {Config.CONFIDENCE_THRESHOLD}")
        print(f"⚠️  Alert Threshold: {Config.ALERT_THRESHOLD}")
        print(f"🤖 Telegram Bot: {'✅ Active' if self.telegram_handler else '❌ Inactive'}")
        print(f"🌐 Web API: http://{Config.API_HOST}:{Config.API_PORT}")
        print("="*50)
        
        try:
            # Record a demo video
            print("\n1. Recording demo video...")
            video_path = self.video_handler.record_video(10)  # 10 second demo
            
            if video_path:
                print(f"✅ Video recorded: {Path(video_path).name}")
                
                # Send to Telegram
                if self.telegram_handler:
                    print("2. Sending video to Telegram...")
                    asyncio.run(self.telegram_handler.send_video(
                        video_path, 
                        "🎥 Demo video from Smart Glasses system!"
                    ))
                    print("✅ Video sent to Telegram")
                
                # Analyze video
                print("3. Analyzing video for hazards...")
                processed_path = Config.PROCESSED_STORAGE_PATH / f"demo_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                results = self.cv_analyzer.analyze_video(video_path, str(processed_path))
                
                if results:
                    print(f"✅ Analysis completed:")
                    print(f"   - Total detections: {results['summary']['total_detections']}")
                    print(f"   - High confidence: {results['summary']['high_confidence_detections']}")
                    print(f"   - Analysis time: {results['analysis_time']:.2f}s")
                    
                    # Send results to Telegram
                    if self.telegram_handler:
                        print("4. Sending analysis results to Telegram...")
                        asyncio.run(self.telegram_handler.send_analysis_results(results))
                        print("✅ Results sent to Telegram")
                
                print(f"\n✅ Demo completed successfully!")
                print(f"📁 Files saved in: {Config.VIDEO_STORAGE_PATH}")
                
            else:
                print("❌ Failed to record demo video")
                
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            logger.error(f"Demo mode error: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)
    
    def shutdown(self):
        """Gracefully shutdown all components"""
        logger.info("Shutting down Smart Glasses Demo System...")
        
        self.running = False
        
        try:
            # Release camera resources
            if self.video_handler:
                self.video_handler.release_camera()
            
            # Wait for API thread to finish
            if self.api_thread and self.api_thread.is_alive():
                # Note: FastAPI server doesn't have a clean shutdown method here
                # In production, you'd want to implement proper shutdown handling
                pass
            
            logger.info("System shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

async def main_async():
    import argparse
    parser = argparse.ArgumentParser(description='Smart Glasses Demo - Oil Leak Detection System')
    parser.add_argument('--mode', choices=['demo', 'monitor', 'api'], default='demo',
                       help='Run mode: demo (quick test), monitor (continuous), api (web server only)')
    parser.add_argument('--config', help='Path to configuration file')
    args = parser.parse_args()

    app = SmartGlassesDemo()
    if not app.initialize():
        logger.error("Failed to initialize system, exiting...")
        sys.exit(1)

    if args.mode != 'api':
        app.start_web_api()
        time.sleep(2)  # Give server time to start

    try:
        if args.mode == 'demo':
            # Run demo mode and Telegram bot together
            demo_task = asyncio.create_task(app.start_telegram_bot())
            app.run_demo_mode()
            print("\n💡 Demo completed! You can now:")
            print(f"   - Visit http://localhost:{Config.API_PORT} for web interface")
            print(f"   - Use Telegram bot commands: /start, /record, /analyze")
            print(f"   - Send videos directly to the Telegram bot")
            print("\n   Press Ctrl+C to exit...")
            await demo_task
        elif args.mode == 'monitor':
            await asyncio.gather(
                app.start_telegram_bot(),
                app.start_continuous_monitoring()
            )
        elif args.mode == 'api':
            start_server()  # This will block
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
    finally:
        if hasattr(app, 'telegram_handler') and app.telegram_handler:
            try:
                await app.telegram_handler.stop_bot()
            except Exception:
                pass
        app.shutdown()

if __name__ == "__main__":
    asyncio.run(main_async())
