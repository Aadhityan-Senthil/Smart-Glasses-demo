import os
import logging
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the smart glasses demo system"""
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Camera Configuration
    CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', 0))
    VIDEO_DURATION = int(os.getenv('VIDEO_DURATION', 30))
    VIDEO_QUALITY = os.getenv('VIDEO_QUALITY', '720p')
    FPS = int(os.getenv('FPS', 30))
    
    # Computer Vision Configuration
    MODEL_PATH = os.getenv('MODEL_PATH', 'models/oil_leak_detector.pt')
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', 0.7))
    NMS_THRESHOLD = float(os.getenv('NMS_THRESHOLD', 0.4))
    
    # Storage Configuration
    VIDEO_STORAGE_PATH = Path(os.getenv('VIDEO_STORAGE_PATH', './videos'))
    PROCESSED_STORAGE_PATH = Path(os.getenv('PROCESSED_STORAGE_PATH', './processed'))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # API Configuration
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 8000))
    
    # Alert Configuration
    ALERT_THRESHOLD = float(os.getenv('ALERT_THRESHOLD', 0.8))
    ENABLE_REAL_TIME_ALERTS = os.getenv('ENABLE_REAL_TIME_ALERTS', 'true').lower() == 'true'
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is present"""
        required_vars = [
            ('TELEGRAM_BOT_TOKEN', cls.TELEGRAM_BOT_TOKEN),
            ('TELEGRAM_CHAT_ID', cls.TELEGRAM_CHAT_ID),
        ]
        
        missing_vars = [var_name for var_name, var_value in required_vars if not var_value]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Create directories if they don't exist
        cls.VIDEO_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
        cls.PROCESSED_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
        Path('logs').mkdir(exist_ok=True)
        Path('models').mkdir(exist_ok=True)
        
        return True

# Setup logging
def setup_logging():
    """Setup logging configuration"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler('logs/smart_glasses.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()
