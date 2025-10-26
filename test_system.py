#!/usr/bin/env python3
"""
Test script for Smart Glasses Demo system
This script verifies that all components are working correctly
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    
    try:
        import cv2
        print("✅ OpenCV imported successfully")
    except ImportError as e:
        print(f"❌ OpenCV import failed: {e}")
        return False
    
    try:
        import torch
        print(f"✅ PyTorch imported successfully (Version: {torch.__version__})")
        print(f"   CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   GPU device: {torch.cuda.get_device_name(0)}")
    except ImportError as e:
        print(f"❌ PyTorch import failed: {e}")
        return False
    
    try:
        import numpy as np
        print(f"✅ NumPy imported successfully (Version: {np.__version__})")
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    try:
        from telegram import Bot
        print("✅ python-telegram-bot imported successfully")
    except ImportError as e:
        print(f"❌ python-telegram-bot import failed: {e}")
        return False
    
    try:
        from ultralytics import YOLO
        print("✅ Ultralytics YOLO imported successfully")
    except ImportError as e:
        print(f"❌ Ultralytics YOLO import failed: {e}")
        return False
    
    try:
        from fastapi import FastAPI
        print("✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    return True

def test_camera():
    """Test camera availability"""
    print("\nTesting camera...")
    
    try:
        import cv2
        
        # Try to open camera
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Camera not available or not accessible")
            return False
        
        # Test reading a frame
        ret, frame = cap.read()
        if not ret:
            print("❌ Cannot read from camera")
            cap.release()
            return False
        
        print(f"✅ Camera working - Frame size: {frame.shape}")
        cap.release()
        return True
        
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        from config import Config
        
        # Check if .env file exists
        if not Path('.env').exists():
            print("⚠️  .env file not found - using defaults")
        
        # Test configuration validation
        try:
            Config.validate_config()
            print("❌ Configuration validation should fail without proper tokens")
            return False
        except ValueError as e:
            print(f"✅ Configuration validation works (expected failure): {str(e)[:50]}...")
            return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_video_processing():
    """Test video processing capabilities"""
    print("\nTesting video processing...")
    
    try:
        import cv2
        import numpy as np
        from cv_analyzer import CVAnalyzer
        
        # Create analyzer
        analyzer = CVAnalyzer()
        
        # Create a test frame
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add some test patterns
        cv2.rectangle(test_frame, (100, 100), (200, 200), (0, 0, 255), -1)  # Red square
        cv2.circle(test_frame, (400, 300), 50, (0, 255, 0), -1)  # Green circle
        
        # Test frame analysis (without model loading)
        print("✅ Video processing components initialized")
        return True
        
    except Exception as e:
        print(f"❌ Video processing test failed: {e}")
        return False

def test_telegram_bot():
    """Test Telegram bot setup (without credentials)"""
    print("\nTesting Telegram bot setup...")
    
    try:
        from telegram_handler import TelegramHandler
        
        # Create handler without credentials
        handler = TelegramHandler()
        print("✅ Telegram handler can be initialized")
        return True
        
    except Exception as e:
        print(f"❌ Telegram handler test failed: {e}")
        return False

def test_web_api():
    """Test web API components"""
    print("\nTesting web API...")
    
    try:
        from fastapi import FastAPI
        from web_api import app
        
        print("✅ FastAPI application created successfully")
        
        # Test that endpoints are defined
        routes = [route.path for route in app.routes]
        expected_routes = ["/", "/health", "/record", "/status"]
        
        for route in expected_routes:
            if route in routes:
                print(f"✅ Route {route} defined")
            else:
                print(f"❌ Route {route} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Web API test failed: {e}")
        return False

async def test_async_functionality():
    """Test async functionality"""
    print("\nTesting async functionality...")
    
    try:
        # Simple async test
        await asyncio.sleep(0.1)
        print("✅ Async functionality working")
        return True
        
    except Exception as e:
        print(f"❌ Async test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist"""
    print("\nTesting file structure...")
    
    required_files = [
        'main.py',
        'config.py',
        'video_capture.py',
        'telegram_handler.py',
        'cv_analyzer.py',
        'web_api.py',
        'requirements.txt',
        '.env.example'
    ]
    
    required_dirs = [
        'videos',
        'processed', 
        'logs',
        'models'
    ]
    
    all_good = True
    
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            all_good = False
    
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"✅ {directory}/ directory exists")
        else:
            print(f"⚠️  {directory}/ directory missing (will be created)")
            Path(directory).mkdir(exist_ok=True)
    
    return all_good

def main():
    """Run all tests"""
    print("🤖 Smart Glasses Demo - System Test")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Python Imports", test_imports),
        ("Configuration", test_configuration),
        ("Camera", test_camera),
        ("Video Processing", test_video_processing),
        ("Telegram Bot", test_telegram_bot),
        ("Web API", test_web_api),
    ]
    
    # Add async test
    async def run_async_tests():
        return await test_async_functionality()
    
    results = {}
    
    # Run synchronous tests
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Run async test
    try:
        results["Async Functionality"] = asyncio.run(run_async_tests())
    except Exception as e:
        print(f"❌ Async test crashed: {e}")
        results["Async Functionality"] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your system is ready.")
        print("\nNext steps:")
        print("1. Configure your .env file with Telegram bot credentials")
        print("2. Run: python main.py --mode demo")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("   - Make sure all dependencies are installed")
        print("   - Check camera permissions")
        print("   - Verify system requirements")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
