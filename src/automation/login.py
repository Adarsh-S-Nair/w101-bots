"""
Login automation module
"""
from src.core.automation_base import AutomationBase
from src.core.action_result import ActionResult
from src.core.element import ElementSearchCriteria, ElementType, DetectionMethod
from src.utils.logger import logger
from src.constants import AssetPaths
from config import config

class LoginAutomation(AutomationBase):
    """Handles Wizard101 login automation"""
    
    def __init__(self, ui_detector):
        super().__init__(ui_detector)
    
    def execute(self) -> ActionResult:
        """Execute login automation workflow"""
        try:
            logger.info("Starting login automation")
            
            # Enter credentials
            result = self.enter_credentials()
            if not result.success:
                return result
            
            # Click login button
            result = self.click_login()
            if not result.success:
                return result
            
            # Wait for login to complete
            result = self.wait_for_login_completion()
            if not result.success:
                return result
            
            # Click the play button to start the game
            result = self.click_play_button()
            if not result.success:
                return result
            
            return ActionResult.success_result("Login automation completed successfully")
            
        except Exception as e:
            return ActionResult.failure_result("Login automation failed", error=e)
    
    def enter_credentials(self) -> ActionResult:
        """Enter username and password"""
        try:
            logger.info("Starting credential entry process")
            
            # First, check if password field is already focused
            focused_criteria = ElementSearchCriteria(
                name="password_field_focused",
                element_type=ElementType.INPUT_FIELD,
                template_path=config.get_launcher_template_path(AssetPaths.LauncherTemplates.PASSWORD_FIELD_FOCUSED),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE],
                metadata={"description": "Password field in focused state"}
            )
            
            # Check if password field is focused
            if self.ui_detector.is_element_present(focused_criteria):
                logger.info("Password field is already focused, typing password directly")
                
                # Just type the password directly
                import pyautogui
                pyautogui.typewrite(config.PASSWORD, interval=0.05)
                
                logger.info("Password entered successfully (direct typing)")
                return ActionResult.success_result("Credentials entered successfully (direct typing)")
            
            # If not focused, use the normal find-and-type approach
            logger.info("Password field not focused, using normal detection and typing")
            
            # Define unfocused password field search criteria
            password_criteria = ElementSearchCriteria(
                name="password_field",
                element_type=ElementType.INPUT_FIELD,
                template_path=config.get_launcher_template_path(AssetPaths.LauncherTemplates.PASSWORD_FIELD),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Password field in unfocused state"}
            )
            
            # Find and type password
            result = self.find_and_type(password_criteria, config.PASSWORD)
            
            if result.success:
                logger.info("Password entered successfully (via detection)")
                return ActionResult.success_result("Credentials entered successfully (via detection)")
            else:
                return ActionResult.failure_result("Failed to enter password")
                
        except Exception as e:
            return ActionResult.failure_result("Failed to enter credentials", error=e)
    
    def click_login(self) -> ActionResult:
        """Click the login button"""
        try:
            logger.info("Looking for login button")
            
            # Define login button search criteria
            login_criteria = ElementSearchCriteria(
                name="login_button",
                element_type=ElementType.BUTTON,
                template_path=config.get_launcher_template_path(AssetPaths.LauncherTemplates.LOGIN_BUTTON),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL]
            )
            
            # Find and click login button
            result = self.find_and_click(login_criteria)
            
            if result.success:
                logger.info("Login button clicked successfully")
                return ActionResult.success_result("Login button clicked")
            else:
                return ActionResult.failure_result("Failed to click login button")
                
        except Exception as e:
            return ActionResult.failure_result("Failed to click login button", error=e)
    
    def wait_for_login_completion(self, timeout: float = 60.0) -> ActionResult:
        """Wait for login to complete (disabled play button appears)"""
        logger.info("Waiting for login to complete...")
        
        # Define criteria for disabled play button (indicates login successful)
        disabled_play_criteria = ElementSearchCriteria(
            name="disabled_play_button",
            element_type=ElementType.BUTTON,
            template_path=config.get_launcher_template_path(AssetPaths.LauncherTemplates.DISABLED_PLAY_BUTTON),
            confidence_threshold=0.8,
            detection_methods=[DetectionMethod.TEMPLATE],
            metadata={"description": "Disabled play button indicating login successful"}
        )
        
        # Wait for disabled play button to appear (login complete)
        result = self.wait_for_element(disabled_play_criteria, timeout=timeout, check_interval=2.0)
        
        if result.success:
            logger.info("Login completed successfully - disabled play button found")
            return ActionResult.success_result("Login completed successfully")
        else:
            logger.warning("Login completion timeout - assuming successful anyway")
            return ActionResult.success_result("Login assumed completed (timeout)")
    
    def click_play_button(self) -> ActionResult:
        """Wait for game to load and click the play button"""
        try:
            logger.info("Waiting for game to load (enabled play button)...")
            
            # Define enabled play button search criteria
            play_button_criteria = ElementSearchCriteria(
                name="play_button",
                element_type=ElementType.BUTTON,
                template_path=config.get_launcher_template_path(AssetPaths.LauncherTemplates.LAUNCHER_PLAY_BUTTON),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Enabled play button indicating game is loaded"}
            )
            
            # Wait for enabled play button to appear (game loaded) - up to 5 minutes
            result = self.wait_for_element(play_button_criteria, timeout=300.0, check_interval=5.0)
            
            if not result.success:
                logger.error("Game loading timeout - enabled play button not found")
                return ActionResult.failure_result("Game loading timeout - enabled play button not found")
            
            logger.info("Game loaded successfully - enabled play button found")
            
            # Now click the play button
            click_result = self.find_and_click(play_button_criteria, wait_time=1.0, retries=3)
            
            if click_result.success:
                logger.info("Play button clicked successfully - game starting")
                return ActionResult.success_result("Play button clicked successfully - game starting")
            else:
                logger.error("Failed to click play button")
                return ActionResult.failure_result("Failed to click play button")
                
        except Exception as e:
            return ActionResult.failure_result("Failed to wait for and click play button", error=e)
    
    def is_logged_in(self) -> bool:
        """Check if login was successful"""
        # This would check for game-specific UI elements that indicate successful login
        # For now, return True as a placeholder
        return True
