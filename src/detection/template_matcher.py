"""
Template matching detection module
"""
import cv2
import numpy as np
import time
from typing import Optional
from pathlib import Path

from src.core.element import UIElement, ElementSearchCriteria, ElementType, DetectionMethod, BoundingBox
from src.core.action_result import ActionResult
# from src.utils.screenshot import ScreenshotManager  # Disabled for GitHub
from config import config
from src.utils.logger import logger

class TemplateMatcher:
    """Template matching for UI element detection"""
    
    def __init__(self):
        # self.screenshot_manager = ScreenshotManager()  # Disabled for GitHub
        self.confidence_threshold = 0.8
        
    def find_element(self, criteria: ElementSearchCriteria) -> Optional[UIElement]:
        """Find an element using template matching"""
        if not criteria.template_path:
            logger.debug(f"No template path provided for '{criteria.name}'")
            return None
        
        try:
            # Check if template file exists
            template_path = Path(criteria.template_path)
            if not template_path.exists():
                logger.warning(f"Template file not found: {template_path}")
                return None
            
            # Take current screenshot (directly)
            import pyautogui
            screenshot = pyautogui.screenshot()
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            if screenshot is None:
                logger.error("Failed to take screenshot for template matching")
                return None
            
            # Perform template matching
            match_result = self._match_template(screenshot, template_path, criteria.confidence_threshold)
            
            if match_result:
                x, y, width, height, confidence = match_result
                bounding_box = BoundingBox(x, y, width, height)
                
                # Save debug image
                self._save_match_debug(screenshot, match_result, criteria.name)
                
                return UIElement(
                    name=criteria.name,
                    element_type=criteria.element_type,
                    detection_method=DetectionMethod.TEMPLATE,
                    confidence=confidence,
                    bounding_box=bounding_box,
                    template_path=criteria.template_path,
                    metadata=criteria.metadata
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Template matching failed for '{criteria.name}': {e}")
            return None
    
    def _match_template(self, screenshot: np.ndarray, template_path: Path, min_confidence: float) -> Optional[tuple]:
        """Perform template matching and return match result"""
        try:
            # Load template
            template = cv2.imread(str(template_path))
            if template is None:
                logger.error(f"Failed to load template: {template_path}")
                return None
            
            # Perform template matching
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            logger.debug(f"Template matching confidence: {max_val:.3f}")
            
            if max_val >= min_confidence:
                h, w = template.shape[:2]
                x, y = max_loc
                return (x, y, w, h, max_val)
            
            return None
            
        except Exception as e:
            logger.error(f"Template matching error: {e}")
            return None
    
    def _save_match_debug(self, screenshot: np.ndarray, match_result: tuple, element_name: str):
        """Save debug image with match highlighted (disabled)"""
        # Screenshot saving disabled for GitHub repository
        pass
