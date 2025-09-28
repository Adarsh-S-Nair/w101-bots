"""
Visual pattern detection module
"""
import cv2
import numpy as np
from typing import Optional

from src.core.element import UIElement, ElementSearchCriteria, ElementType, DetectionMethod, BoundingBox, Coordinates
# from src.utils.screenshot import ScreenshotManager  # Disabled for GitHub
from src.utils.logger import logger

class VisualDetector:
    """Visual pattern detection for UI elements"""
    
    def __init__(self):
        # self.screenshot_manager = ScreenshotManager()  # Disabled for GitHub
        pass
    def find_element(self, criteria: ElementSearchCriteria) -> Optional[UIElement]:
        """Find an element using visual pattern detection"""
        try:
            # Take current screenshot (directly)
            import pyautogui
            screenshot = pyautogui.screenshot()
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            if screenshot is None:
                logger.error("Failed to take screenshot for visual detection")
                return None
            
            # Try different visual detection methods based on element type
            if criteria.element_type == ElementType.BUTTON:
                return self._detect_button(screenshot, criteria)
            elif criteria.element_type == ElementType.INPUT_FIELD:
                return self._detect_input_field(screenshot, criteria)
            elif criteria.element_type == ElementType.TEXT:
                return self._detect_text(screenshot, criteria)
            else:
                # Generic detection
                return self._detect_generic(screenshot, criteria)
                
        except Exception as e:
            logger.error(f"Visual detection failed for '{criteria.name}': {e}")
            return None
    
    def _detect_button(self, screenshot: np.ndarray, criteria: ElementSearchCriteria) -> Optional[UIElement]:
        """Detect button-like elements"""
        try:
            # Look for rectangular regions with button-like characteristics
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            
            # Edge detection to find rectangular shapes
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Look for rectangular contours that might be buttons
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Check if it looks like a button (reasonable size, aspect ratio)
                if (50 < w < 200 and 20 < h < 60 and 
                    0.3 < w/h < 5.0):  # Reasonable button proportions
                    
                    # Check if it's in the expected region (bottom area for login buttons)
                    height, width = screenshot.shape[:2]
                    if y > height * 0.6:  # Bottom 40% of screen
                        bounding_box = BoundingBox(x, y, w, h)
                        
                        return UIElement(
                            name=criteria.name,
                            element_type=ElementType.BUTTON,
                            detection_method=DetectionMethod.VISUAL,
                            confidence=0.7,  # Moderate confidence for visual detection
                            bounding_box=bounding_box,
                            metadata=criteria.metadata
                        )
            
            return None
            
        except Exception as e:
            logger.debug(f"Button detection failed: {e}")
            return None
    
    def _detect_input_field(self, screenshot: np.ndarray, criteria: ElementSearchCriteria) -> Optional[UIElement]:
        """Detect input field elements"""
        try:
            # Look for light-colored rectangular areas
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            
            # Threshold to find light areas (input fields are usually light)
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Look for rectangular light areas that might be input fields
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Check if it looks like an input field (rectangular, reasonable size)
                if (100 < w < 300 and 15 < h < 50 and 
                    w/h > 3):  # Input fields are much wider than tall
                    
                    # Check if it's in the expected region (bottom area for login fields)
                    height, width = screenshot.shape[:2]
                    if y > height * 0.7:  # Bottom 30% of screen
                        bounding_box = BoundingBox(x, y, w, h)
                        
                        return UIElement(
                            name=criteria.name,
                            element_type=ElementType.INPUT_FIELD,
                            detection_method=DetectionMethod.VISUAL,
                            confidence=0.6,  # Lower confidence for visual detection
                            bounding_box=bounding_box,
                            metadata=criteria.metadata
                        )
            
            return None
            
        except Exception as e:
            logger.debug(f"Input field detection failed: {e}")
            return None
    
    def _detect_text(self, screenshot: np.ndarray, criteria: ElementSearchCriteria) -> Optional[UIElement]:
        """Detect text elements (placeholder for future OCR integration)"""
        # This would integrate with OCR detection
        # For now, return None to fall back to other methods
        return None
    
    def _detect_generic(self, screenshot: np.ndarray, criteria: ElementSearchCriteria) -> Optional[UIElement]:
        """Generic visual detection"""
        try:
            # Simple approach: look for areas with significant color changes
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            
            # Find areas with high gradient (edges)
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            
            # Find regions with high gradient activity
            _, thresh = cv2.threshold(gradient_magnitude, 50, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Return the largest contour as a potential UI element
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_contour)
                
                bounding_box = BoundingBox(x, y, w, h)
                
                return UIElement(
                    name=criteria.name,
                    element_type=ElementType.UNKNOWN,
                    detection_method=DetectionMethod.VISUAL,
                    confidence=0.4,  # Low confidence for generic detection
                    bounding_box=bounding_box,
                    metadata=criteria.metadata
                )
            
            return None
            
        except Exception as e:
            logger.debug(f"Generic detection failed: {e}")
            return None
