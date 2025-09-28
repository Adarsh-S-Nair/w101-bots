"""
Wizard101 Launcher automation module
Handles launching the game and logging in
"""
import os
import time
import subprocess
import pyautogui
from typing import Optional, Tuple
from config import config
from src.logger import logger
from src.vision import VisionDetector

class Wizard101Launcher:
    """Handles Wizard101 launcher automation"""
    
    def __init__(self):
        self.launcher_process: Optional[subprocess.Popen] = None
        self.vision = VisionDetector()
        
        # Configure pyautogui
        pyautogui.PAUSE = config.CLICK_DELAY
        pyautogui.FAILSAFE = True  # Move mouse to corner to stop
        
        logger.info("Wizard101 Launcher initialized")
    
    def launch_game(self) -> bool:
        """Launch Wizard101 game"""
        try:
            logger.info(f"Launching Wizard101 from: {config.LAUNCHER_PATH}")
            
            # Launch the game
            self.launcher_process = subprocess.Popen([
                config.LAUNCHER_PATH
            ], cwd=os.path.dirname(config.LAUNCHER_PATH))
            
            logger.info("Wizard101 launcher started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to launch Wizard101: {e}")
            return False
    
    def wait_for_launcher(self, timeout: int = None) -> bool:
        """Wait for the launcher to fully load"""
        timeout = timeout or config.WAIT_TIMEOUT
        
        logger.info(f"Waiting for launcher to load (timeout: {timeout}s)")
        
        for i in range(timeout):
            try:
                # Take a screenshot to check if launcher is visible
                screenshot = pyautogui.screenshot()
                
                # Look for the login button (gray color indicates it's loaded)
                # This is a simple check - we'll improve this later with computer vision
                if self._is_launcher_ready():
                    logger.info("Launcher loaded successfully")
                    return True
                    
            except Exception as e:
                logger.debug(f"Launcher not ready yet: {e}")
            
            time.sleep(1)
            logger.debug(f"Waiting... ({i+1}/{timeout})")
        
        logger.error("Timeout waiting for launcher to load")
        return False
    
    def _is_launcher_ready(self) -> bool:
        """Check if the launcher is ready for interaction"""
        try:
            # Look for the login button by checking for gray color
            # This is a basic implementation - we'll improve with computer vision
            screenshot = pyautogui.screenshot()
            
            # Convert to numpy array for color analysis
            import numpy as np
            img_array = np.array(screenshot)
            
            # Look for gray pixels that might indicate the login button
            # This is a placeholder - we'll implement proper image recognition
            gray_pixels = np.sum((img_array[:,:,0] > 100) & (img_array[:,:,0] < 200) & 
                               (img_array[:,:,1] > 100) & (img_array[:,:,1] < 200) & 
                               (img_array[:,:,2] > 100) & (img_array[:,:,2] < 200))
            
            # If we find enough gray pixels, assume launcher is ready
            return gray_pixels > 10000
            
        except Exception as e:
            logger.debug(f"Error checking launcher readiness: {e}")
            return False
    
    def login(self) -> bool:
        """Perform login to Wizard101"""
        try:
            logger.info("Starting login process")
            
            # Wait a bit for the launcher to be fully ready
            time.sleep(config.LOAD_DELAY)
            
            # Take a screenshot for debugging
            self._save_debug_screenshot("before_login")
            
            # Click away from any focused fields first
            self._unfocus_fields()
            
            # Click on password field and enter credentials
            if self._enter_credentials():
                logger.info("Credentials entered successfully")
                
                # Click login button
                if self._click_login():
                    logger.info("Login button clicked")
                    
                    # Wait for login to complete
                    return self._wait_for_login_completion()
                else:
                    logger.error("Failed to click login button")
                    return False
            else:
                logger.error("Failed to enter credentials")
                return False
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def _enter_credentials(self) -> bool:
        """Enter username and password using computer vision"""
        try:
            logger.info("Detecting password field...")
            
            # Use computer vision to find the password field
            password_coords = self.vision.find_password_field()
            
            if not password_coords:
                logger.error("Could not detect password field")
                return False
            
            password_x, password_y = password_coords
            logger.info(f"Clicking password field at ({password_x}, {password_y})")
            
            # Move mouse to password field and click
            pyautogui.moveTo(password_x, password_y)
            time.sleep(0.5)
            pyautogui.click()
            time.sleep(0.5)
            
            # Clear the field and type password
            pyautogui.hotkey('ctrl', 'a')  # Select all
            time.sleep(0.2)
            pyautogui.typewrite(config.PASSWORD, interval=config.TYPE_DELAY)
            
            logger.info("Password entered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enter credentials: {e}")
            return False
    
    def _click_login(self) -> bool:
        """Click the login button using computer vision"""
        try:
            logger.info("Detecting login button...")
            
            # Use computer vision to find the login button
            login_coords = self.vision.find_login_button()
            
            if not login_coords:
                logger.error("Could not detect login button")
                return False
            
            login_x, login_y = login_coords
            logger.info(f"Clicking login button at ({login_x}, {login_y})")
            
            # Move mouse to login button and click
            pyautogui.moveTo(login_x, login_y)
            time.sleep(0.5)
            pyautogui.click()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to click login button: {e}")
            return False
    
    def _wait_for_login_completion(self) -> bool:
        """Wait for login to complete and game to load"""
        logger.info("Waiting for login to complete...")
        
        # Wait for the launcher window to close or change
        # This is a simple implementation - we'll improve this later
        for i in range(30):  # Wait up to 30 seconds
            try:
                # Check if the launcher process is still running
                if self.launcher_process and self.launcher_process.poll() is not None:
                    logger.info("Login completed - launcher closed")
                    return True
                
                # Check for game window (placeholder)
                # We'll implement proper game detection later
                time.sleep(1)
                
            except Exception as e:
                logger.debug(f"Checking login status: {e}")
        
        logger.warning("Login completion timeout - assuming successful")
        return True
    
    def _save_debug_screenshot(self, name: str):
        """Save a screenshot for debugging (disabled)"""
        # Screenshot saving disabled for GitHub repository
        pass
    
    def _unfocus_fields(self):
        """Click away from any focused fields to reset their appearance"""
        try:
            logger.info("Unfocusing any active fields...")
            
            # Click on a neutral area of the launcher (like the background)
            # This will unfocus any input fields and reset their appearance
            screen_width, screen_height = pyautogui.size()
            
            # Click on the center-left area (away from input fields)
            unfocus_x = screen_width // 4  # Left quarter of screen
            unfocus_y = screen_height // 3  # Upper third of screen
            
            logger.info(f"Clicking unfocus area at ({unfocus_x}, {unfocus_y})")
            pyautogui.click(unfocus_x, unfocus_y)
            time.sleep(0.5)
            
            # Take another screenshot to see the unfocused state
            self._save_debug_screenshot("after_unfocus")
            
        except Exception as e:
            logger.warning(f"Failed to unfocus fields: {e}")
    
    def close(self):
        """Clean up and close the launcher"""
        if self.launcher_process:
            try:
                self.launcher_process.terminate()
                logger.info("Launcher process terminated")
            except Exception as e:
                logger.error(f"Failed to terminate launcher: {e}")
