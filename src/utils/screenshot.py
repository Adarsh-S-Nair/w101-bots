"""
Screenshot utilities
"""
import time
import pyautogui
import cv2
import numpy as np
from typing import Optional
from pathlib import Path

from config import config
from src.utils.logger import logger

class ScreenshotManager:
    """Manages screenshot capture and processing"""
    
    def __init__(self):
        self.screenshot_dir = config.SCREENSHOT_DIR
        self.screenshot_dir.mkdir(exist_ok=True)
    
    def take_screenshot(self) -> Optional[np.ndarray]:
        """Take a screenshot and return as OpenCV image"""
        try:
            screenshot = pyautogui.screenshot()
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None
    
    def save_screenshot(self, image: np.ndarray, name: str) -> Optional[Path]:
        """Save a screenshot to disk"""
        try:
            if not config.SAVE_SCREENSHOTS:
                return None
            
            timestamp = int(time.time())
            filename = f"{name}_{timestamp}.png"
            filepath = self.screenshot_dir / filename
            
            cv2.imwrite(str(filepath), image)
            logger.debug(f"Screenshot saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save screenshot '{name}': {e}")
            return None
    
    def save_debug_screenshot(self, name: str) -> Optional[Path]:
        """Take and save a debug screenshot"""
        screenshot = self.take_screenshot()
        if screenshot is not None:
            return self.save_screenshot(screenshot, f"debug_{name}")
        return None
    
    def crop_screenshot(self, image: np.ndarray, bounding_box) -> Optional[np.ndarray]:
        """Crop a screenshot to a specific region"""
        try:
            x, y, width, height = bounding_box.x, bounding_box.y, bounding_box.width, bounding_box.height
            return image[y:y+height, x:x+width]
        except Exception as e:
            logger.error(f"Failed to crop screenshot: {e}")
            return None
    
    def save_cropped_screenshot(self, image: np.ndarray, bounding_box, name: str) -> Optional[Path]:
        """Crop and save a screenshot region"""
        cropped = self.crop_screenshot(image, bounding_box)
        if cropped is not None:
            return self.save_screenshot(cropped, name)
        return None

