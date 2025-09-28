"""
Computer vision utilities for detecting Wizard101 UI elements
"""
import cv2
import numpy as np
import pyautogui
from typing import Optional, Tuple, List
from config import config
from src.logger import logger
from src.constants import AssetPaths

class VisionDetector:
    """Handles computer vision detection for UI elements"""
    
    def __init__(self):
        self.template_threshold = 0.8  # Confidence threshold for template matching
        
    def take_screenshot(self) -> np.ndarray:
        """Take a screenshot and return as OpenCV image"""
        screenshot = pyautogui.screenshot()
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    def check_template_exists(self, template_name: str) -> bool:
        """Check if a template file exists"""
        template_path = config.TEMPLATES_DIR / template_name
        return template_path.exists()
    
    def save_debug_image(self, image: np.ndarray, name: str):
        """Save an image for debugging purposes (disabled)"""
        # Screenshot saving disabled for GitHub repository
        pass
    
    def find_template(self, screenshot: np.ndarray, template_path: str) -> Optional[Tuple[int, int, int, int, float]]:
        """Find a template image within the screenshot"""
        try:
            # Load template
            template = cv2.imread(template_path)
            if template is None:
                logger.warning(f"Template not found: {template_path}")
                return None
            
            # Perform template matching
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            logger.debug(f"Template matching for {template_path}: confidence = {max_val:.3f}")
            
            if max_val >= self.template_threshold:
                h, w = template.shape[:2]
                x, y = max_loc
                return (x, y, x + w, y + h, max_val)
            
            return None
            
        except Exception as e:
            logger.error(f"Template matching failed: {e}")
            return None
    
    def find_password_field(self) -> Optional[Tuple[int, int]]:
        """Find the password input field using template matching"""
        screenshot = self.take_screenshot()
        self.save_debug_image(screenshot, "password_detection")
        
        # Check if template exists
        if not self.check_template_exists(f"{AssetPaths.LAUNCHER_TEMPLATES}/{AssetPaths.LauncherTemplates.PASSWORD_FIELD}"):
            logger.warning("Password field template not found, using fallback detection")
            password_coords = self._detect_input_field(screenshot)
            if password_coords:
                return password_coords
            return self._get_fallback_password_coords()
        
        # Method 1: Template matching (primary method)
        password_template_path = config.get_launcher_template_path(AssetPaths.LauncherTemplates.PASSWORD_FIELD)
        template_result = self.find_template(screenshot, password_template_path)
        
        if template_result:
            x, y, x2, y2, confidence = template_result
            center_x = x + (x2 - x) // 2
            center_y = y + (y2 - y) // 2
            logger.info(f"Password field found via template matching: ({center_x}, {center_y}) confidence: {confidence:.3f}")
            
            # Save debug image with match highlighted
            self._save_template_match_debug(screenshot, template_result, "password_match")
            return (center_x, center_y)
        
        # Method 2: Fallback to visual detection
        password_coords = self._detect_input_field(screenshot)
        if password_coords:
            logger.warning(f"Password field found via visual detection (template failed): {password_coords}")
            return password_coords
        
        # Method 3: Use fallback coordinates
        password_coords = self._get_fallback_password_coords()
        logger.warning(f"Using fallback password coordinates: {password_coords}")
        return password_coords
    
    def find_login_button(self) -> Optional[Tuple[int, int]]:
        """Find the login button using template matching"""
        screenshot = self.take_screenshot()
        self.save_debug_image(screenshot, "login_button_detection")
        
        # Check if template exists
        if not self.check_template_exists(f"{AssetPaths.LAUNCHER_TEMPLATES}/{AssetPaths.LauncherTemplates.LOGIN_BUTTON}"):
            logger.warning("Login button template not found, using fallback detection")
            button_coords = self._detect_gray_button(screenshot)
            if button_coords:
                return button_coords
            return self._get_fallback_login_coords()
        
        # Method 1: Template matching (primary method)
        login_template_path = config.get_launcher_template_path(AssetPaths.LauncherTemplates.LOGIN_BUTTON)
        template_result = self.find_template(screenshot, login_template_path)
        
        if template_result:
            x, y, x2, y2, confidence = template_result
            center_x = x + (x2 - x) // 2
            center_y = y + (y2 - y) // 2
            logger.info(f"Login button found via template matching: ({center_x}, {center_y}) confidence: {confidence:.3f}")
            
            # Save debug image with match highlighted
            self._save_template_match_debug(screenshot, template_result, "login_match")
            return (center_x, center_y)
        
        # Method 2: Fallback to visual detection
        button_coords = self._detect_gray_button(screenshot)
        if button_coords:
            logger.warning(f"Login button found via visual detection (template failed): {button_coords}")
            return button_coords
        
        # Method 3: Use fallback coordinates
        button_coords = self._get_fallback_login_coords()
        logger.warning(f"Using fallback login coordinates: {button_coords}")
        return button_coords
    
    def _detect_input_field(self, screenshot: np.ndarray) -> Optional[Tuple[int, int]]:
        """Detect input field by looking for rectangular white/light areas"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            
            # Look for light colored rectangles (input fields)
            # Threshold to find light areas
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Look for rectangular contours in the bottom area of the screen
            height, width = screenshot.shape[:2]
            bottom_region = height * 0.7  # Look in bottom 30% of screen
            
            for contour in contours:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Check if it's in the bottom area and roughly rectangular
                if (y > bottom_region and 
                    20 < w < 200 and 15 < h < 50 and  # Reasonable input field size
                    w/h > 2):  # Wider than tall
                    
                    # Return center of the field
                    center_x = x + w // 2
                    center_y = y + h // 2
                    return (center_x, center_y)
            
            return None
            
        except Exception as e:
            logger.debug(f"Input field detection failed: {e}")
            return None
    
    def _detect_gray_button(self, screenshot: np.ndarray) -> Optional[Tuple[int, int]]:
        """Detect gray login button"""
        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)
            
            # Define gray color range
            lower_gray = np.array([0, 0, 100])
            upper_gray = np.array([180, 30, 200])
            
            # Create mask
            mask = cv2.inRange(hsv, lower_gray, upper_gray)
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Look for button-sized contours in the bottom area
            height, width = screenshot.shape[:2]
            bottom_region = height * 0.7
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Check if it's in the bottom area and roughly button-sized
                if (y > bottom_region and 
                    50 < w < 150 and 20 < h < 60 and  # Button size
                    abs(w - h) < 30):  # Roughly square
                    
                    center_x = x + w // 2
                    center_y = y + h // 2
                    return (center_x, center_y)
            
            return None
            
        except Exception as e:
            logger.debug(f"Gray button detection failed: {e}")
            return None
    
    def _detect_login_area(self, screenshot: np.ndarray) -> Optional[Tuple[int, int]]:
        """Detect login area by looking for username/password patterns"""
        try:
            # Get screen dimensions
            height, width = screenshot.shape[:2]
            
            # Focus on bottom area where login typically is
            bottom_half = screenshot[int(height * 0.6):, :]
            
            # Convert to grayscale
            gray = cv2.cvtColor(bottom_half, cv2.COLOR_BGR2GRAY)
            
            # Look for horizontal lines or patterns that might indicate input fields
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=100, maxLineGap=10)
            
            if lines is not None:
                # Look for horizontal lines that might be input field borders
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    if abs(y1 - y2) < 10:  # Horizontal line
                        # Estimate where password field might be
                        center_x = (x1 + x2) // 2
                        center_y = y1 + 40  # Below the line
                        return (center_x, center_y + int(height * 0.6))  # Adjust for bottom half offset
            
            return None
            
        except Exception as e:
            logger.debug(f"Login area detection failed: {e}")
            return None
    
    def _detect_login_text(self, screenshot: np.ndarray) -> Optional[Tuple[int, int]]:
        """Detect login button by looking for text patterns"""
        try:
            # This is a placeholder - we could use OCR here
            # For now, use a simple approach based on screen layout
            height, width = screenshot.shape[:2]
            
            # Login button is typically in the bottom right area
            right_region = width * 0.7
            bottom_region = height * 0.7
            
            # Estimate login button position
            button_x = int(right_region + (width - right_region) / 2)
            button_y = int(bottom_region + (height - bottom_region) / 2)
            
            return (button_x, button_y)
            
        except Exception as e:
            logger.debug(f"Login text detection failed: {e}")
            return None
    
    def _get_fallback_password_coords(self) -> Tuple[int, int]:
        """Get fallback coordinates for password field"""
        # Use calibrated coordinates from config if available
        return config.PASSWORD_FIELD_COORDS
    
    def _get_fallback_login_coords(self) -> Tuple[int, int]:
        """Get fallback coordinates for login button"""
        # Use calibrated coordinates from config if available
        return config.LOGIN_BUTTON_COORDS
    
    def calibrate_coordinates(self) -> dict:
        """Interactive calibration to find correct coordinates"""
        logger.info("Starting coordinate calibration...")
        logger.info("Please position your mouse over each element when prompted")
        
        # Take initial screenshot
        screenshot = self.take_screenshot()
        self.save_debug_image(screenshot, "calibration_start")
        
        # Get password field coordinates
        logger.info("Position your mouse over the PASSWORD FIELD and press Enter...")
        input("Press Enter when ready...")
        password_x, password_y = pyautogui.position()
        
        # Get login button coordinates
        logger.info("Position your mouse over the LOGIN BUTTON and press Enter...")
        input("Press Enter when ready...")
        login_x, login_y = pyautogui.position()
        
        coordinates = {
            'password_field': (password_x, password_y),
            'login_button': (login_x, login_y)
        }
        
        logger.info(f"Calibrated coordinates: {coordinates}")
        return coordinates
    
    def _save_template_match_debug(self, screenshot: np.ndarray, match_result: Tuple[int, int, int, int, float], name: str):
        """Save debug image with template match highlighted (disabled)"""
        # Screenshot saving disabled for GitHub repository
        pass
