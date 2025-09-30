"""
Enter game automation module
Handles entering the game from any state (fresh startup or already running)
"""
import time
import pyautogui
from src.core.automation_base import AutomationBase
from src.core.action_result import ActionResult
from src.core.element import ElementSearchCriteria, ElementType, DetectionMethod
from src.utils.logger import logger
from src.utils.process_utils import ProcessUtils
from src.constants import AssetPaths
from config import config

class EnterGameAutomation(AutomationBase):
    """Handles entering Wizard101 game from any state"""
    
    def __init__(self, ui_detector):
        super().__init__(ui_detector)
    
    def execute(self) -> ActionResult:
        """Execute enter game automation workflow"""
        try:
            logger.info("Starting enter game automation")
            
            # Use the initial state passed from bot framework
            if self.initial_game_state:
                logger.info("Game is already running - checking for crown shop and spellbook")
                return self._handle_already_running_game()
            else:
                logger.info("Game not running - performing fresh startup")
                return self._handle_fresh_startup()
            
        except Exception as e:
            return ActionResult.failure_result("Enter game automation failed", error=e)
    
    def _handle_already_running_game(self) -> ActionResult:
        """Handle case where game is already running"""
        try:
            # Wait for spellbook to verify we're in the game
            result = self.wait_for_spellbook()
            if not result.success:
                return result
            
            # Check for crown shop and close it if present (only after confirming we're in the game)
            result = self._check_and_close_crown_shop()
            if not result.success:
                logger.warning(f"Crown shop handling failed: {result.message}")
                # Continue anyway, don't fail the entire process
            
            logger.info("Successfully entered already running game")
            return ActionResult.success_result("Successfully entered already running game")
            
        except Exception as e:
            return ActionResult.failure_result("Failed to handle already running game", error=e)
    
    def _handle_fresh_startup(self) -> ActionResult:
        """Handle fresh game startup from launcher"""
        try:
            # Wait for title screen to appear
            result = self.wait_for_title_screen()
            if not result.success:
                return result
            
            # Press spacebar when title screen is detected
            result = self.press_spacebar()
            if not result.success:
                return result
            
            # Wait for play button to appear and click it
            result = self.wait_and_click_play_button()
            if not result.success:
                return result
            
            # Wait for spellbook to appear (verify we're in the game)
            result = self.wait_for_spellbook()
            if not result.success:
                return result
            
            # Check for crown shop and close it if present (only after confirming we're in the game)
            result = self._check_and_close_crown_shop()
            if not result.success:
                logger.warning(f"Crown shop handling failed: {result.message}")
                # Continue anyway, don't fail the entire process
            
            logger.info("Successfully completed fresh game startup")
            return ActionResult.success_result("Successfully completed fresh game startup")
            
        except Exception as e:
            return ActionResult.failure_result("Failed to handle fresh startup", error=e)
    
    def _check_and_close_crown_shop(self) -> ActionResult:
        """Check for crown shop and close it if present using Escape key"""
        try:
            logger.info("Checking for crown shop...")
            
            # Define search criteria for crown shop window
            crown_shop_criteria = ElementSearchCriteria(
                name="crown_shop",
                element_type=ElementType.IMAGE,
                template_path=config.get_game_template_path(AssetPaths.GameTemplates.CROWN_SHOP),
                confidence_threshold=0.7,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Crown shop window"}
            )
            
            # Check if crown shop is present
            crown_shop_present = self.ui_detector.is_element_present(crown_shop_criteria)
            logger.info(f"Crown shop window present: {crown_shop_present}")
            
            if crown_shop_present:
                logger.info("Crown shop detected - closing it with Escape key")
                
                # Click on the crown shop window to focus it
                element = self.ui_detector.find_element(crown_shop_criteria)
                if element:
                    logger.info(f"Clicking on crown shop window at {element.center} to focus it")
                    pyautogui.moveTo(element.center.x, element.center.y)
                    time.sleep(0.2)
                    pyautogui.click()
                    time.sleep(0.5)  # Wait for window to be focused
                else:
                    logger.warning("Could not find crown shop element for clicking")
                
                # Press Escape key twice (first opens settings, second closes settings)
                logger.info("Pressing Escape key (first press - opens settings)")
                pyautogui.press('escape')
                time.sleep(0.5)  # Wait for settings to open
                
                logger.info("Pressing Escape key (second press - closes settings)")
                pyautogui.press('escape')
                time.sleep(0.5)  # Wait for settings to close
                
                # Verify that the crown shop is actually closed
                crown_shop_still_present = self.ui_detector.is_element_present(crown_shop_criteria)
                logger.info(f"Crown shop window still present: {crown_shop_still_present}")
                
                if not crown_shop_still_present:
                    logger.info("Crown shop closed successfully - verified")
                    return ActionResult.success_result("Crown shop closed successfully - verified")
                else:
                    logger.warning("Crown shop still present after Escape key presses")
                    return ActionResult.failure_result("Crown shop failed to close after Escape key presses")
            else:
                logger.info("Crown shop not present - proceeding normally")
                return ActionResult.success_result("Crown shop not present - proceeding normally")
                
        except Exception as e:
            logger.error(f"Failed to check and close crown shop: {e}")
            return ActionResult.failure_result("Failed to check and close crown shop", error=e)
    
    def wait_for_title_screen(self, timeout: float = 60.0) -> ActionResult:
        """Wait for title screen to appear"""
        try:
            logger.info("Waiting for title screen to appear...")
            
            # Define search criteria for the title screen
            title_screen_criteria = ElementSearchCriteria(
                name="title_screen",
                element_type=ElementType.IMAGE,
                template_path=config.get_game_template_path(AssetPaths.GameTemplates.TITLE_SCREEN),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Title screen indicating game is loaded"}
            )
            
            # Wait for the title screen to appear
            result = self.wait_for_element(title_screen_criteria, timeout=timeout, check_interval=2.0)
            
            if result.success:
                logger.info("Title screen detected successfully")
                return ActionResult.success_result("Title screen detected - game is loaded")
            else:
                logger.warning("Title screen not found within timeout")
                return ActionResult.failure_result("Title screen not found - game may not have loaded")
                
        except Exception as e:
            logger.error(f"Failed to wait for title screen: {e}")
            return ActionResult.failure_result("Failed to wait for title screen", error=e)
    
    def press_spacebar(self) -> ActionResult:
        """Press spacebar to proceed from title screen"""
        try:
            logger.info("Pressing spacebar to proceed from title screen...")
            pyautogui.press('space')
            time.sleep(2.0)  # Wait for transition
            return ActionResult.success_result("Spacebar pressed successfully")
        except Exception as e:
            logger.error(f"Failed to press spacebar: {e}")
            return ActionResult.failure_result("Failed to press spacebar", error=e)
    
    def wait_and_click_play_button(self, timeout: float = 30.0) -> ActionResult:
        """Wait for play button to appear and click it"""
        try:
            logger.info("Waiting for play button to appear...")
            
            # Define search criteria for the play button
            play_button_criteria = ElementSearchCriteria(
                name="play_button",
                element_type=ElementType.IMAGE,
                template_path=config.get_game_template_path(AssetPaths.GameTemplates.PLAY_BUTTON),
                confidence_threshold=0.7,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Play button to start the game"}
            )
            
            # Wait for the play button to appear
            result = self.wait_for_element(play_button_criteria, timeout=timeout, check_interval=2.0)
            
            if result.success:
                logger.info("Play button detected - clicking it")
                # Click the play button
                click_result = self.find_and_click(play_button_criteria, wait_time=1.0, retries=3)
                
                if click_result.success:
                    logger.info("Play button clicked successfully")
                    return ActionResult.success_result("Play button clicked successfully")
                else:
                    logger.error("Failed to click play button")
                    return ActionResult.failure_result("Failed to click play button")
            else:
                logger.warning("Play button not found within timeout")
                return ActionResult.failure_result("Play button not found - game may not have loaded")
                
        except Exception as e:
            logger.error(f"Failed to wait and click play button: {e}")
            return ActionResult.failure_result("Failed to wait and click play button", error=e)
    
    def wait_for_spellbook(self, timeout: float = 60.0) -> ActionResult:
        """Wait for spellbook to appear on screen (verify we're in the game)"""
        try:
            logger.info("Waiting for spellbook to appear (indicating we're in the game)...")
            
            # Define search criteria for the spellbook
            spellbook_criteria = ElementSearchCriteria(
                name="spellbook",
                element_type=ElementType.IMAGE,
                template_path=config.get_game_template_path(AssetPaths.GameTemplates.SPELLBOOK),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Spellbook icon indicating we are in the game"}
            )
            
            # Wait for the spellbook to appear
            result = self.wait_for_element(spellbook_criteria, timeout=timeout, check_interval=2.0)
            
            if result.success:
                logger.info("Spellbook detected successfully - confirmed we are in the game")
                return ActionResult.success_result("Spellbook detected - game verification successful")
            else:
                logger.warning("Spellbook not found within timeout")
                return ActionResult.failure_result("Spellbook not found - game verification failed")
                
        except Exception as e:
            logger.error(f"Failed to wait for spellbook: {e}")
            return ActionResult.failure_result("Failed to wait for spellbook", error=e)