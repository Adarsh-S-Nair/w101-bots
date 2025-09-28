"""
Launcher automation module
"""
import subprocess
import time
from typing import Optional

from src.core.automation_base import AutomationBase
from src.core.action_result import ActionResult
from src.core.element import ElementSearchCriteria, ElementType, DetectionMethod
from src.utils.logger import logger
from src.constants import AssetPaths
from config import config

class LauncherAutomation(AutomationBase):
    """Handles Wizard101 launcher automation"""
    
    def __init__(self, ui_detector):
        super().__init__(ui_detector)
        self.launcher_process: Optional[subprocess.Popen] = None
        
    def execute(self) -> ActionResult:
        """Execute launcher automation workflow"""
        try:
            logger.info("Starting launcher automation")
            
            # Launch the game
            result = self.launch_game()
            if not result.success:
                return result
            
            # Wait for launcher to load (looking for login elements, not play button)
            result = self.wait_for_launcher()
            if not result.success:
                return result
            
            return ActionResult.success_result("Launcher automation completed successfully")
            
        except Exception as e:
            return ActionResult.failure_result("Launcher automation failed", error=e)
    
    def launch_game(self) -> ActionResult:
        """Launch Wizard101 game"""
        try:
            logger.info(f"Launching Wizard101 from: {config.LAUNCHER_PATH}")
            
            from pathlib import Path
            launcher_path = Path(config.LAUNCHER_PATH)
            self.launcher_process = subprocess.Popen([
                str(launcher_path)
            ], cwd=launcher_path.parent)
            
            logger.info("Wizard101 launcher started successfully")
            return ActionResult.success_result("Game launched successfully")
            
        except Exception as e:
            return ActionResult.failure_result("Failed to launch Wizard101", error=e)
    
    def wait_for_launcher(self, timeout: float = 30.0) -> ActionResult:
        """Wait for the launcher to fully load"""
        logger.info(f"Waiting for launcher to load (timeout: {timeout}s)")
        
        # Wait a bit for the launcher process to start
        import time
        time.sleep(3.0)
        
        # Define multiple criteria for detecting that launcher is ready
        # Try different elements that might indicate the launcher is loaded
        
        # Look for login elements to confirm launcher is ready
        # Try to find the password field first (most reliable indicator)
        password_field_criteria = ElementSearchCriteria(
            name="password_field",
            element_type=ElementType.INPUT_FIELD,
            template_path=config.get_launcher_template_path(AssetPaths.LauncherTemplates.PASSWORD_FIELD),
            confidence_threshold=0.7,
            metadata={"description": "Password field to confirm launcher is ready"}
        )
        
        # Try to find the password field first
        result = self.wait_for_element(password_field_criteria, timeout=timeout, check_interval=2.0)
        
        if result.success:
            logger.info("Launcher loaded successfully - password field found")
            return ActionResult.success_result("Launcher loaded successfully")
        
        # If password field not found, try to find the login button as fallback
        logger.warning("Password field not found, trying login button as fallback...")
        
        login_button_criteria = ElementSearchCriteria(
            name="login_button",
            element_type=ElementType.BUTTON,
            template_path=config.get_launcher_template_path(AssetPaths.LauncherTemplates.LOGIN_BUTTON),
            confidence_threshold=0.6,
            metadata={"description": "Login button as fallback to confirm launcher is ready"}
        )
        
        result = self.wait_for_element(login_button_criteria, timeout=10.0, check_interval=2.0)
        
        if result.success:
            logger.info("Launcher loaded successfully - login button found as fallback")
            return ActionResult.success_result("Launcher loaded successfully")
        
        # If still not found, try a simple approach - wait for launcher window to be visible
        logger.warning("UI elements not detected, using fallback method...")
        
        # Simple fallback: wait a fixed time and assume it's ready
        # This is not ideal but better than failing completely
        logger.info("Using fallback: assuming launcher is ready after delay")
        time.sleep(5.0)  # Give it a bit more time
        
        return ActionResult.success_result("Launcher assumed ready (fallback method)")
    
    def click_play_button(self) -> ActionResult:
        """Click the play button to start the game"""
        try:
            logger.info("Looking for play button to click")
            
            # Define play button search criteria
            play_button_criteria = ElementSearchCriteria(
                name="play_button",
                element_type=ElementType.BUTTON,
                template_path=config.get_launcher_template_path(AssetPaths.LauncherTemplates.LAUNCHER_PLAY_BUTTON),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Play button to start the game"}
            )
            
            # Find and click the play button
            result = self.find_and_click(play_button_criteria, wait_time=1.0, retries=3)
            
            if result.success:
                logger.info("Play button clicked successfully")
                return ActionResult.success_result("Play button clicked successfully")
            else:
                logger.error("Failed to click play button")
                return ActionResult.failure_result("Failed to click play button")
                
        except Exception as e:
            return ActionResult.failure_result("Failed to click play button", error=e)
    
    def unfocus_fields(self) -> ActionResult:
        """Click away from any focused fields to reset their appearance"""
        try:
            logger.info("Unfocusing any active fields...")
            
            # Click on a neutral area of the launcher
            import pyautogui
            screen_width, screen_height = pyautogui.size()
            
            unfocus_x = screen_width // 4  # Left quarter of screen
            unfocus_y = screen_height // 3  # Upper third of screen
            
            logger.info(f"Clicking unfocus area at ({unfocus_x}, {unfocus_y})")
            pyautogui.click(unfocus_x, unfocus_y)
            time.sleep(0.5)
            
            return ActionResult.success_result("Fields unfocused successfully")
            
        except Exception as e:
            return ActionResult.failure_result("Failed to unfocus fields", error=e)
    
    def is_launcher_ready(self) -> bool:
        """Check if launcher is ready for interaction"""
        # Simple check - look for the login button
        login_criteria = ElementSearchCriteria(
            name="login_button",
            element_type=ElementType.BUTTON,
            template_path=config.get_launcher_template_path(AssetPaths.LauncherTemplates.LOGIN_BUTTON),
            confidence_threshold=0.7
        )
        
        return self.ui_detector.is_element_present(login_criteria)
    
    def close(self):
        """Clean up and close the launcher"""
        if self.launcher_process:
            try:
                self.launcher_process.terminate()
                logger.info("Launcher process terminated")
            except Exception as e:
                logger.error(f"Failed to terminate launcher: {e}")
