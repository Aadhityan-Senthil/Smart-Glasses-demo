import cv2
import numpy as np
import torch
import logging
from ultralytics import YOLO
from pathlib import Path
from datetime import datetime
import time
import json
from config import Config

logger = logging.getLogger(__name__)

class CVAnalyzer:
    """Computer Vision analyzer for oil leak and hazard detection"""
    
    def __init__(self):
        self.model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.class_names = {
            0: 'oil_leak',
            1: 'gas_leak',
            2: 'fire',
            3: 'smoke',
            4: 'chemical_spill',
            5: 'safety_equipment',
            6: 'worker',
            7: 'vehicle',
            8: 'pipe_damage',
            9: 'corrosion'
        }
        
        # Color mapping for different hazard types
        self.colors = {
            'oil_leak': (0, 0, 255),      # Red
            'gas_leak': (0, 255, 255),    # Yellow
            'fire': (0, 69, 255),         # Orange
            'smoke': (128, 128, 128),     # Gray
            'chemical_spill': (255, 0, 255), # Magenta
            'safety_equipment': (0, 255, 0), # Green
            'worker': (255, 255, 0),      # Cyan
            'vehicle': (255, 0, 0),       # Blue
            'pipe_damage': (0, 165, 255), # Orange
            'corrosion': (42, 42, 165)    # Brown
        }
        
    def load_model(self, model_path=None):
        """Load the YOLO model for detection"""
        try:
            model_path = model_path or Config.MODEL_PATH
            
            # If custom model doesn't exist, use a pre-trained model and fine-tune it
            if not Path(model_path).exists():
                logger.warning(f"Custom model not found at {model_path}, using YOLOv8 base model")
                # Download YOLOv8 model if it doesn't exist
                self.model = YOLO('yolov8n.pt')  # nano version for faster inference
                
                # Create a custom model configuration for industrial hazard detection
                self._setup_custom_detection()
            else:
                self.model = YOLO(model_path)
            
            self.model.to(self.device)
            logger.info(f"Model loaded successfully on {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def _setup_custom_detection(self):
        """Setup custom detection for industrial hazards when no custom model is available"""
        # This is a simplified approach - in production, you'd train a proper model
        # For demo purposes, we'll use image processing techniques combined with the base model
        logger.info("Setting up custom hazard detection rules")
    
    def analyze_video(self, video_path, output_path=None):
        """Analyze video for oil leaks and hazards"""
        start_time = time.time()
        
        if not self.model:
            if not self.load_model():
                return None
        
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                logger.error(f"Could not open video: {video_path}")
                return None
            
            # Get video properties
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Setup output video if path provided
            out = None
            if output_path:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            
            detections = []
            frame_count = 0
            
            logger.info(f"Starting video analysis: {total_frames} frames at {fps} FPS")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Run detection every few frames for performance
                if frame_count % 5 == 0:  # Analyze every 5th frame
                    frame_detections = self._analyze_frame(frame, frame_count)
                    detections.extend(frame_detections)
                    
                    # Draw detections on frame
                    annotated_frame = self._draw_detections(frame, frame_detections)
                else:
                    annotated_frame = frame.copy()
                
                # Add timestamp
                timestamp = f"Frame: {frame_count}/{total_frames}"
                cv2.putText(annotated_frame, timestamp, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                if out:
                    out.write(annotated_frame)
                
                # Progress logging
                if frame_count % 100 == 0:
                    progress = (frame_count / total_frames) * 100
                    logger.info(f"Analysis progress: {progress:.1f}%")
            
            cap.release()
            if out:
                out.release()
            
            analysis_time = time.time() - start_time
            
            # Process and summarize detections
            results = self._process_detections(detections, analysis_time, output_path)
            
            logger.info(f"Video analysis completed in {analysis_time:.2f} seconds")
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing video: {e}")
            return None
    
    def analyze_frame(self, frame):
        """Analyze a single frame for hazards"""
        if not self.model:
            if not self.load_model():
                return []
        
        return self._analyze_frame(frame, 0)
    
    def _analyze_frame(self, frame, frame_number):
        """Internal method to analyze a single frame"""
        detections = []
        
        try:
            # Run YOLO detection
            results = self.model(frame, conf=Config.CONFIDENCE_THRESHOLD)
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Extract detection info
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = box.conf[0].cpu().numpy()
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        # Map class ID to hazard type
                        class_name = self.class_names.get(class_id, f'unknown_{class_id}')
                        
                        detection = {
                            'frame': frame_number,
                            'class': class_name,
                            'confidence': float(confidence),
                            'bbox': [float(x1), float(y1), float(x2), float(y2)],
                            'timestamp': datetime.now().isoformat()
                        }
                        detections.append(detection)
            
            # Add custom detection rules for industrial hazards
            custom_detections = self._detect_custom_hazards(frame, frame_number)
            detections.extend(custom_detections)
            
        except Exception as e:
            logger.error(f"Error analyzing frame {frame_number}: {e}")
        
        return detections
    
    def _detect_custom_hazards(self, frame, frame_number):
        """Detect custom hazards using image processing techniques"""
        detections = []
        
        try:
            # Convert to different color spaces
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Oil leak detection (looking for dark, reflective patches)
            oil_detections = self._detect_oil_leaks(frame, hsv, frame_number)
            detections.extend(oil_detections)
            
            # Smoke detection (looking for gray/white motion patterns)
            smoke_detections = self._detect_smoke(frame, gray, frame_number)
            detections.extend(smoke_detections)
            
            # Fire detection (looking for orange/red regions with specific characteristics)
            fire_detections = self._detect_fire(frame, hsv, frame_number)
            detections.extend(fire_detections)
            
        except Exception as e:
            logger.error(f"Error in custom hazard detection: {e}")
        
        return detections
    
    def _detect_oil_leaks(self, frame, hsv, frame_number):
        """Detect potential oil leaks using color and texture analysis"""
        detections = []
        
        try:
            # Define color ranges for oil (dark, low saturation)
            lower_oil = np.array([0, 0, 0])
            upper_oil = np.array([180, 100, 80])
            
            # Create mask for oil-like colors
            oil_mask = cv2.inRange(hsv, lower_oil, upper_oil)
            
            # Apply morphological operations to clean up mask
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            oil_mask = cv2.morphologyEx(oil_mask, cv2.MORPH_CLOSE, kernel)
            oil_mask = cv2.morphologyEx(oil_mask, cv2.MORPH_OPEN, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(oil_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # Minimum area threshold
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Calculate confidence based on area and shape
                    confidence = min(0.9, area / 10000)  # Max confidence 0.9
                    
                    if confidence > 0.3:
                        detection = {
                            'frame': frame_number,
                            'class': 'oil_leak',
                            'confidence': confidence,
                            'bbox': [float(x), float(y), float(x+w), float(y+h)],
                            'timestamp': datetime.now().isoformat(),
                            'detection_method': 'custom_color_analysis'
                        }
                        detections.append(detection)
            
        except Exception as e:
            logger.error(f"Error in oil leak detection: {e}")
        
        return detections
    
    def _detect_smoke(self, frame, gray, frame_number):
        """Detect smoke using motion and texture analysis"""
        detections = []
        
        # This would typically require multiple frames for motion analysis
        # For now, we'll use texture analysis only
        try:
            # Use Laplacian variance to detect texture (smoke has low texture)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            variance = laplacian.var()
            
            # If overall variance is low, might indicate smoke
            if variance < 100:  # Threshold for low texture
                # Look for uniform gray regions
                _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > 1000:
                        x, y, w, h = cv2.boundingRect(contour)
                        confidence = min(0.7, area / 20000)
                        
                        if confidence > 0.2:
                            detection = {
                                'frame': frame_number,
                                'class': 'smoke',
                                'confidence': confidence,
                                'bbox': [float(x), float(y), float(x+w), float(y+h)],
                                'timestamp': datetime.now().isoformat(),
                                'detection_method': 'custom_texture_analysis'
                            }
                            detections.append(detection)
        
        except Exception as e:
            logger.error(f"Error in smoke detection: {e}")
        
        return detections
    
    def _detect_fire(self, frame, hsv, frame_number):
        """Detect fire using color analysis"""
        detections = []
        
        try:
            # Define color ranges for fire (red-orange-yellow)
            lower_fire1 = np.array([0, 120, 70])
            upper_fire1 = np.array([10, 255, 255])
            lower_fire2 = np.array([170, 120, 70])
            upper_fire2 = np.array([180, 255, 255])
            
            # Create masks for fire colors
            fire_mask1 = cv2.inRange(hsv, lower_fire1, upper_fire1)
            fire_mask2 = cv2.inRange(hsv, lower_fire2, upper_fire2)
            fire_mask = cv2.bitwise_or(fire_mask1, fire_mask2)
            
            # Clean up mask
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            fire_mask = cv2.morphologyEx(fire_mask, cv2.MORPH_OPEN, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(fire_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 300:
                    x, y, w, h = cv2.boundingRect(contour)
                    confidence = min(0.8, area / 5000)
                    
                    if confidence > 0.4:
                        detection = {
                            'frame': frame_number,
                            'class': 'fire',
                            'confidence': confidence,
                            'bbox': [float(x), float(y), float(x+w), float(y+h)],
                            'timestamp': datetime.now().isoformat(),
                            'detection_method': 'custom_color_analysis'
                        }
                        detections.append(detection)
        
        except Exception as e:
            logger.error(f"Error in fire detection: {e}")
        
        return detections
    
    def _draw_detections(self, frame, detections):
        """Draw detection boxes and labels on frame"""
        annotated_frame = frame.copy()
        
        for detection in detections:
            class_name = detection['class']
            confidence = detection['confidence']
            bbox = detection['bbox']
            
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            
            # Get color for this class
            color = self.colors.get(class_name, (255, 255, 255))
            
            # Draw bounding box
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label with confidence
            label = f"{class_name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            
            # Draw label background
            cv2.rectangle(annotated_frame, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), color, -1)
            
            # Draw label text
            cv2.putText(annotated_frame, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return annotated_frame
    
    def _process_detections(self, detections, analysis_time, processed_video_path=None):
        """Process and summarize detections"""
        results = {
            'detections': detections,
            'analysis_time': analysis_time,
            'processed_video_path': processed_video_path,
            'summary': {
                'total_detections': len(detections),
                'high_confidence_detections': len([d for d in detections if d['confidence'] > Config.ALERT_THRESHOLD]),
                'detection_types': {}
            }
        }
        
        # Count detections by type
        for detection in detections:
            class_name = detection['class']
            if class_name not in results['summary']['detection_types']:
                results['summary']['detection_types'][class_name] = {
                    'count': 0,
                    'max_confidence': 0,
                    'avg_confidence': 0
                }
            
            results['summary']['detection_types'][class_name]['count'] += 1
            results['summary']['detection_types'][class_name]['max_confidence'] = max(
                results['summary']['detection_types'][class_name]['max_confidence'],
                detection['confidence']
            )
        
        # Calculate average confidence for each type
        for class_name in results['summary']['detection_types']:
            class_detections = [d for d in detections if d['class'] == class_name]
            if class_detections:
                avg_conf = sum(d['confidence'] for d in class_detections) / len(class_detections)
                results['summary']['detection_types'][class_name]['avg_confidence'] = avg_conf
        
        return results
