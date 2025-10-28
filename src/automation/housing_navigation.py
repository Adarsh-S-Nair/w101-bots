"""
Generic housing navigation automation module
Handles navigation to housing/castles after game verification
"""
import time
import pyautogui
from src.core.automation_base import AutomationBase
from src.core.action_result import ActionResult
from src.core.element import ElementSearchCriteria, ElementType, DetectionMethod
from src.utils.logger import logger
from src.constants import AssetPaths
from config import config

class HousingNavigationAutomation(AutomationBase):
    """Handles generic navigation to housing/castles in Wizard101"""
    
    def __init__(self, ui_detector, house_type="red_barn_farm"):
        super().__init__(ui_detector)
        self.house_type = house_type
    
    def execute(self) -> ActionResult:
        """Execute housing navigation automation workflow"""
        try:
            logger.info("Starting housing navigation automation")
            
            # Check if player is already in the house
            result = self.check_if_already_in_house()
            if not result.success:
                return result
            
            # If we're already in house, handle the house navigation flow
            if result.data and result.data.get('already_in_house', False):
                logger.info("Player is already in house, executing house navigation flow")
                return self.execute_house_navigation_flow()
            
            # Press 'b' key to open housing menu
            result = self.press_b_key()
            if not result.success:
                return result
            
            # Wait for housing navigation to appear and click it
            result = self.wait_and_click_housing_nav()
            if not result.success:
                return result
            
            # Wait for castles to appear and click it
            result = self.wait_and_click_castles()
            if not result.success:
                return result
            
            # Wait for the specified house to appear and click it
            result = self.wait_and_click_house()
            if not result.success:
                return result
            
            # Handle equip/unequip logic for red barn farm
            result = self.handle_equip_unequip()
            if not result.success:
                return result
            
            # Click go home button after confirming red barn farm is equipped
            result = self.click_go_home()
            if not result.success:
                return result
            
            logger.info("Housing navigation automation completed successfully")
            return ActionResult.success_result("Housing navigation automation completed successfully")
            
        except Exception as e:
            return ActionResult.failure_result("Housing navigation automation failed", error=e)
    
    def execute_house_selection_only(self) -> ActionResult:
        """Execute only house selection without navigating to front of house (for farming bot)"""
        try:
            logger.info("Starting house selection only automation")
            
            # Check if player is already in the house
            result = self.check_if_already_in_house()
            if not result.success:
                return result
            
            # If we're already in house, just return success (no need to navigate to front)
            if result.data and result.data.get('already_in_house', False):
                logger.info("Player is already in house, no additional navigation needed")
                return ActionResult.success_result("Player is already in house")
            
            # Press 'b' key to open housing menu
            result = self.press_b_key()
            if not result.success:
                return result
            
            # Wait for housing navigation to appear and click it
            result = self.wait_and_click_housing_nav()
            if not result.success:
                return result
            
            # Wait for castles to appear and click it
            result = self.wait_and_click_castles()
            if not result.success:
                return result
            
            # Wait for the specified house to appear and click it
            result = self.wait_and_click_house()
            if not result.success:
                return result
            
            # Handle equip/unequip logic for red barn farm
            result = self.handle_equip_unequip()
            if not result.success:
                return result
            
            # Click go home button after confirming red barn farm is equipped
            result = self.click_go_home()
            if not result.success:
                return result
            
            logger.info("House selection automation completed successfully")
            return ActionResult.success_result("House selection automation completed successfully")
            
        except Exception as e:
            return ActionResult.failure_result("House selection automation failed", error=e)
    
    def press_b_key(self) -> ActionResult:
        """Press the 'b' key to open housing menu"""
        try:
            logger.info("Pressing 'b' key to open housing menu...")
            
            # Press 'b' key
            pyautogui.press('b')
            
            # Wait a moment for the action to register
            time.sleep(0.3)
            
            logger.info("'b' key pressed successfully")
            return ActionResult.success_result("'b' key pressed successfully")
            
        except Exception as e:
            return ActionResult.failure_result("Failed to press 'b' key", error=e)
    
    def wait_and_click_housing_nav(self, timeout: float = 30.0) -> ActionResult:
        """Wait for housing navigation to appear and click it"""
        try:
            logger.info("Waiting for housing navigation to appear...")
            
            # Define search criteria for housing navigation
            housing_nav_criteria = ElementSearchCriteria(
                name="housing_nav",
                element_type=ElementType.BUTTON,
                template_path=config.get_game_template_path(AssetPaths.GameTemplates.HOUSING_NAV),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Housing navigation button"}
            )
            
            # Wait for the housing navigation to appear
            result = self.wait_for_element(housing_nav_criteria, timeout=timeout, check_interval=2.0)
            
            if not result.success:
                logger.warning("Housing navigation not found within timeout")
                return ActionResult.failure_result("Housing navigation not found within timeout")
            
            logger.info("Housing navigation detected successfully")
            
            # Click the housing navigation button
            click_result = self.find_and_click(housing_nav_criteria, wait_time=1.0, retries=3)
            
            if click_result.success:
                logger.info("Housing navigation clicked successfully")
                return ActionResult.success_result("Housing navigation clicked successfully")
            else:
                logger.error("Failed to click housing navigation")
                return ActionResult.failure_result("Failed to click housing navigation")
                
        except Exception as e:
            return ActionResult.failure_result("Failed to wait for and click housing navigation", error=e)
    
    def wait_and_click_castles(self, timeout: float = 30.0) -> ActionResult:
        """Wait for castles to appear and click it"""
        try:
            logger.info("Waiting for castles to appear...")
            
            # Define search criteria for castles
            castles_criteria = ElementSearchCriteria(
                name="castles",
                element_type=ElementType.BUTTON,
                template_path=config.get_game_template_path(AssetPaths.GameTemplates.CASTLES),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Castles button"}
            )
            
            # Wait for the castles to appear
            result = self.wait_for_element(castles_criteria, timeout=timeout, check_interval=2.0)
            
            if not result.success:
                logger.warning("Castles not found within timeout")
                return ActionResult.failure_result("Castles not found within timeout")
            
            logger.info("Castles detected successfully")
            
            # Click the castles button
            click_result = self.find_and_click(castles_criteria, wait_time=1.0, retries=3)
            
            if click_result.success:
                logger.info("Castles clicked successfully")
                return ActionResult.success_result("Castles clicked successfully")
            else:
                logger.error("Failed to click castles")
                return ActionResult.failure_result("Failed to click castles")
                
        except Exception as e:
            return ActionResult.failure_result("Failed to wait for and click castles", error=e)
    
    def wait_and_click_house(self, timeout: float = 30.0) -> ActionResult:
        """Wait for the specified house text to appear and click it"""
        try:
            logger.info(f"Waiting for {self.house_type} text to appear...")
            
            # Get the appropriate template path based on house type
            template_path = self._get_house_template_path()
            if not template_path:
                return ActionResult.failure_result(f"Unknown house type: {self.house_type}")
            
            # Define search criteria for the house with lower confidence threshold
            # to handle background color variations (selected vs unselected state)
            house_criteria = ElementSearchCriteria(
                name=self.house_type,
                element_type=ElementType.TEXT,
                template_path=template_path,
                confidence_threshold=0.6,  # Reduced from 0.8 to handle background color variations
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": f"{self.house_type} text to click on"}
            )
            
            # Wait for the house text to appear
            result = self.wait_for_element(house_criteria, timeout=timeout, check_interval=2.0)
            
            if not result.success:
                logger.warning(f"{self.house_type} text not found within timeout")
                # Try with even lower confidence threshold as fallback
                logger.info(f"Trying fallback detection with lower confidence threshold...")
                fallback_criteria = ElementSearchCriteria(
                    name=f"{self.house_type}_fallback",
                    element_type=ElementType.TEXT,
                    template_path=template_path,
                    confidence_threshold=0.4,  # Even lower threshold for fallback
                    detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                    metadata={"description": f"{self.house_type} text fallback detection"}
                )
                
                fallback_result = self.wait_for_element(fallback_criteria, timeout=10.0, check_interval=1.0)
                if fallback_result.success:
                    logger.info(f"{self.house_type} detected with fallback confidence threshold")
                    # Update the criteria to use the fallback result
                    house_criteria = fallback_criteria
                else:
                    return ActionResult.failure_result(f"{self.house_type} text not found even with fallback detection")
            
            logger.info(f"{self.house_type} text detected successfully")
            
            # Click the house text
            click_result = self.find_and_click(house_criteria, wait_time=1.0, retries=3)
            
            if click_result.success:
                logger.info(f"{self.house_type} clicked successfully")
                return ActionResult.success_result(f"{self.house_type} clicked successfully")
            else:
                logger.error(f"Failed to click {self.house_type}")
                return ActionResult.failure_result(f"Failed to click {self.house_type}")
                
        except Exception as e:
            logger.error(f"Failed to wait for and click {self.house_type}: {e}")
            return ActionResult.failure_result(f"Failed to wait for and click {self.house_type}", error=e)
    
    def _get_house_template_path(self) -> str:
        """Get the template path for the specified house type"""
        house_templates = {
            "red_barn_farm": AssetPaths.GameTemplates.RED_BARN_FARM,
            "wysteria_villa": AssetPaths.GameTemplates.WYSTERIA_VILLA
        }
        
        if self.house_type in house_templates:
            return config.get_game_template_path(house_templates[self.house_type])
        
        return None
    
    def test_house_detection(self, confidence_levels: list = [0.8, 0.6, 0.4, 0.2]) -> ActionResult:
        """Test house detection with different confidence levels for debugging"""
        try:
            logger.info(f"Testing {self.house_type} detection with different confidence levels...")
            
            template_path = self._get_house_template_path()
            if not template_path:
                return ActionResult.failure_result(f"Unknown house type: {self.house_type}")
            
            for confidence in confidence_levels:
                logger.info(f"Testing with confidence threshold: {confidence}")
                
                test_criteria = ElementSearchCriteria(
                    name=f"{self.house_type}_test_{confidence}",
                    element_type=ElementType.TEXT,
                    template_path=template_path,
                    confidence_threshold=confidence,
                    detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                    metadata={"description": f"{self.house_type} test detection at {confidence}"}
                )
                
                # Quick check without waiting
                if self.ui_detector.is_element_present(test_criteria):
                    logger.info(f"✓ {self.house_type} detected with confidence {confidence}")
                    return ActionResult.success_result(f"House detected with confidence {confidence}", data={'confidence': confidence})
                else:
                    logger.info(f"✗ {self.house_type} not detected with confidence {confidence}")
            
            return ActionResult.failure_result(f"{self.house_type} not detected with any confidence level")
            
        except Exception as e:
            logger.error(f"Failed to test house detection: {e}")
            return ActionResult.failure_result("Failed to test house detection", error=e)
    
    def handle_equip_unequip(self, timeout: float = 10.0) -> ActionResult:
        """Handle equip/unequip logic for red barn farm"""
        try:
            logger.info("Checking for equip/unequip status...")
            
            # First check for unequip button (indicates already equipped)
            unequip_criteria = ElementSearchCriteria(
                name="unequip",
                element_type=ElementType.BUTTON,
                template_path=config.get_game_template_path(AssetPaths.GameTemplates.UNEQUIP),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Unequip button indicating red barn farm is equipped"}
            )
            
            # Check if unequip button is present
            if self.ui_detector.is_element_present(unequip_criteria):
                logger.info("Red barn farm is already equipped (unequip button found)")
                return ActionResult.success_result("Red barn farm is already equipped")
            
            # If no unequip button, look for equip button
            logger.info("Red barn farm not equipped, looking for equip button...")
            
            equip_criteria = ElementSearchCriteria(
                name="equip",
                element_type=ElementType.BUTTON,
                template_path=config.get_game_template_path(AssetPaths.GameTemplates.EQUIP),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Equip button to equip red barn farm"}
            )
            
            # Wait for equip button to appear
            result = self.wait_for_element(equip_criteria, timeout=timeout, check_interval=1.0)
            
            if not result.success:
                logger.warning("Equip button not found within timeout")
                return ActionResult.failure_result("Equip button not found - cannot equip red barn farm")
            
            logger.info("Equip button detected successfully")
            
            # Click the equip button
            click_result = self.find_and_click(equip_criteria, wait_time=1.0, retries=3)
            
            if click_result.success:
                logger.info("Equip button clicked successfully - red barn farm equipped")
                return ActionResult.success_result("Red barn farm equipped successfully")
            else:
                logger.error("Failed to click equip button")
                return ActionResult.failure_result("Failed to click equip button")
                
        except Exception as e:
            logger.error(f"Failed to handle equip/unequip logic: {e}")
            return ActionResult.failure_result("Failed to handle equip/unequip logic", error=e)
    
    def click_go_home(self, timeout: float = 10.0) -> ActionResult:
        """Click the go home button after confirming red barn farm is equipped"""
        try:
            logger.info("Looking for go home button...")
            
            # Define search criteria for go home button
            go_home_criteria = ElementSearchCriteria(
                name="go_home",
                element_type=ElementType.BUTTON,
                template_path=config.get_game_template_path(AssetPaths.GameTemplates.GO_HOME),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Go home button to return to the game world"}
            )
            
            # Wait for go home button to appear
            result = self.wait_for_element(go_home_criteria, timeout=timeout, check_interval=1.0)
            
            if not result.success:
                logger.warning("Go home button not found within timeout")
                return ActionResult.failure_result("Go home button not found - cannot return to game world")
            
            logger.info("Go home button detected successfully")
            
            # Click the go home button
            click_result = self.find_and_click(go_home_criteria, wait_time=1.0, retries=3)
            
            if not click_result.success:
                logger.error("Failed to click go home button")
                return ActionResult.failure_result("Failed to click go home button")
            
            logger.info("Go home button clicked successfully - waiting for navigation to complete")
            
            # Wait for spellbook to disappear (indicates loading screen)
            result = self.wait_for_spellbook_disappear()
            if not result.success:
                return result
            
            # Wait for spellbook to reappear (indicates successful navigation to house)
            result = self.wait_for_spellbook_reappear()
            if not result.success:
                return result
            
            logger.info("Successfully navigated to house - spellbook reappeared")
            return ActionResult.success_result("Successfully returned to game world and navigated to house")
                
        except Exception as e:
            logger.error(f"Failed to click go home button: {e}")
            return ActionResult.failure_result("Failed to click go home button", error=e)
    
    def wait_for_spellbook_disappear(self, timeout: float = 15.0) -> ActionResult:
        """Wait for spellbook to disappear after clicking go home (indicates loading screen)"""
        try:
            logger.info("Waiting for spellbook to disappear (loading screen)...")
            
            # Define search criteria for spellbook
            spellbook_criteria = ElementSearchCriteria(
                name="spellbook",
                element_type=ElementType.BUTTON,
                template_path=config.get_game_template_path(AssetPaths.GameTemplates.SPELLBOOK),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Spellbook button that should disappear during loading"}
            )
            
            # Wait for spellbook to disappear
            start_time = time.time()
            while time.time() - start_time < timeout:
                if not self.ui_detector.is_element_present(spellbook_criteria):
                    logger.info("Spellbook disappeared - loading screen detected")
                    return ActionResult.success_result("Spellbook disappeared - loading screen detected")
                
                time.sleep(0.5)  # Check every 0.5 seconds
            
            logger.warning("Spellbook did not disappear within timeout")
            return ActionResult.failure_result("Spellbook did not disappear within timeout - navigation may have failed")
            
        except Exception as e:
            logger.error(f"Failed to wait for spellbook to disappear: {e}")
            return ActionResult.failure_result("Failed to wait for spellbook to disappear", error=e)
    
    def wait_for_spellbook_reappear(self, timeout: float = 30.0) -> ActionResult:
        """Wait for spellbook to reappear (indicates successful navigation to house)"""
        try:
            logger.info("Waiting for spellbook to reappear (navigation complete)...")
            
            # Define search criteria for spellbook
            spellbook_criteria = ElementSearchCriteria(
                name="spellbook",
                element_type=ElementType.BUTTON,
                template_path=config.get_game_template_path(AssetPaths.GameTemplates.SPELLBOOK),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Spellbook button that should reappear when navigation is complete"}
            )
            
            # Wait for spellbook to reappear
            result = self.wait_for_element(spellbook_criteria, timeout=timeout, check_interval=1.0)
            
            if result.success:
                logger.info("Spellbook reappeared - navigation to house completed successfully")
                return ActionResult.success_result("Spellbook reappeared - navigation to house completed successfully")
            else:
                logger.warning("Spellbook did not reappear within timeout")
                return ActionResult.failure_result("Spellbook did not reappear within timeout - navigation may have failed")
            
        except Exception as e:
            logger.error(f"Failed to wait for spellbook to reappear: {e}")
            return ActionResult.failure_result("Failed to wait for spellbook to reappear", error=e)
    
    def check_if_already_in_house(self) -> ActionResult:
        """Check if player is already in the house by looking for place_object image"""
        try:
            logger.info("Checking if player is already in house...")
            
            # Define search criteria for place_object
            place_object_criteria = ElementSearchCriteria(
                name="place_object",
                element_type=ElementType.BUTTON,
                template_path=config.get_game_template_path(AssetPaths.GameTemplates.PLACE_OBJECT),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Place object button indicating player is in house"}
            )
            
            # Check if place_object is present
            if self.ui_detector.is_element_present(place_object_criteria):
                logger.info("Player is already in house (place_object found)")
                return ActionResult.success_result("Player is already in house", data={'already_in_house': True})
            else:
                logger.info("Player is not in house (place_object not found)")
                return ActionResult.success_result("Player is not in house", data={'already_in_house': False})
                
        except Exception as e:
            logger.error(f"Failed to check if already in house: {e}")
            return ActionResult.failure_result("Failed to check if already in house", error=e)
    
    def execute_house_navigation_flow(self) -> ActionResult:
        """Execute the house navigation flow when player is already in house"""
        try:
            logger.info("Executing house navigation flow...")
            
            # Press 'h' key to toggle housing menu and look for house_start button
            result = self.toggle_housing_menu_and_find_house_start()
            if not result.success:
                return result
            
            # Wait for outside_button to appear and click it
            result = self.wait_and_click_outside_button()
            if not result.success:
                return result
            
            # Press 'H' key to close housing menu
            result = self.close_housing_menu()
            if not result.success:
                return result
            
            logger.info("House navigation flow completed successfully")
            return ActionResult.success_result("House navigation flow completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to execute house navigation flow: {e}")
            return ActionResult.failure_result("Failed to execute house navigation flow", error=e)
    
    def click_place_object(self, timeout: float = 10.0) -> ActionResult:
        """Click the place_object button"""
        try:
            logger.info("Clicking place_object button...")
            
            # Define search criteria for place_object
            place_object_criteria = ElementSearchCriteria(
                name="place_object",
                element_type=ElementType.BUTTON,
                template_path=config.get_game_template_path(AssetPaths.GameTemplates.PLACE_OBJECT),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Place object button"}
            )
            
            # Click the place_object button
            click_result = self.find_and_click(place_object_criteria, wait_time=1.0, retries=3)
            
            if click_result.success:
                logger.info("Place object button clicked successfully")
                return ActionResult.success_result("Place object button clicked successfully")
            else:
                logger.error("Failed to click place object button")
                return ActionResult.failure_result("Failed to click place object button")
                
        except Exception as e:
            logger.error(f"Failed to click place object button: {e}")
            return ActionResult.failure_result("Failed to click place object button", error=e)
    
    def wait_and_click_house_start(self, timeout: float = 15.0) -> ActionResult:
        """Wait for house_start to appear and click it with retry logic"""
        try:
            logger.info("Waiting for house_start to appear...")
            
            # Define search criteria for house_start
            house_start_criteria = ElementSearchCriteria(
                name="house_start",
                element_type=ElementType.BUTTON,
                template_path=config.get_game_template_path(AssetPaths.GameTemplates.HOUSE_START),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "House start button"}
            )
            
            # Define search criteria for outside_button (to verify click success)
            outside_button_criteria = ElementSearchCriteria(
                name="outside_button",
                element_type=ElementType.BUTTON,
                template_path=config.get_game_template_path(AssetPaths.GameTemplates.OUTSIDE_BUTTON),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Outside button"}
            )
            
            # Wait for the house_start to appear initially
            result = self.wait_for_element(house_start_criteria, timeout=timeout, check_interval=2.0)
            
            if not result.success:
                logger.warning("House start button not found within timeout")
                return ActionResult.failure_result("House start button not found within timeout")
            
            logger.info("House start button detected successfully")
            
            # Retry logic: try up to 3 times
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                logger.info(f"Attempt {attempt}/{max_retries}: Clicking house start button...")
                
                # Click the house_start button
                click_result = self.find_and_click(house_start_criteria, wait_time=1.0, retries=1)
                
                if not click_result.success:
                    logger.warning(f"Failed to click house start button on attempt {attempt}")
                    if attempt < max_retries:
                        logger.info("Moving mouse up 50 pixels and waiting 5 seconds before retry...")
                        current_x, current_y = pyautogui.position()
                        pyautogui.moveTo(current_x, current_y - 50)
                        time.sleep(5.0)
                        continue
                    else:
                        return ActionResult.failure_result("Failed to click house start button after all retries")
                
                # Wait 1 second and check for outside_button
                logger.info("Waiting 1 second to check if outside button appears...")
                time.sleep(1.0)
                
                if self.ui_detector.is_element_present(outside_button_criteria):
                    logger.info(f"Success! Outside button appeared after attempt {attempt}")
                    return ActionResult.success_result("House start button clicked successfully")
                else:
                    logger.warning(f"Outside button not found after attempt {attempt} - button may have been grayed out")
                    if attempt < max_retries:
                        logger.info("Moving mouse up 50 pixels and waiting 5 seconds before retry...")
                        current_x, current_y = pyautogui.position()
                        pyautogui.moveTo(current_x, current_y - 50)
                        time.sleep(5.0)
                    else:
                        logger.error("Failed to get outside button to appear after all retries")
                        return ActionResult.failure_result("Failed to navigate to house start: Outside button not found within timeout")
                
        except Exception as e:
            logger.error(f"Failed to wait for and click house start button: {e}")
            return ActionResult.failure_result("Failed to wait for and click house start button", error=e)
    
    def wait_and_click_outside_button(self, timeout: float = 15.0) -> ActionResult:
        """Wait for outside_button to appear and click it"""
        try:
            logger.info("Waiting for outside_button to appear...")
            
            # Define search criteria for outside_button
            outside_button_criteria = ElementSearchCriteria(
                name="outside_button",
                element_type=ElementType.BUTTON,
                template_path=config.get_game_template_path(AssetPaths.GameTemplates.OUTSIDE_BUTTON),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Outside button"}
            )
            
            # Wait for the outside_button to appear
            result = self.wait_for_element(outside_button_criteria, timeout=timeout, check_interval=2.0)
            
            if not result.success:
                logger.warning("Outside button not found within timeout")
                return ActionResult.failure_result("Outside button not found within timeout")
            
            logger.info("Outside button detected successfully")
            
            # Click the outside_button
            click_result = self.find_and_click(outside_button_criteria, wait_time=1.0, retries=3)
            
            if click_result.success:
                logger.info("Outside button clicked successfully")
                return ActionResult.success_result("Outside button clicked successfully")
            else:
                logger.error("Failed to click outside button")
                return ActionResult.failure_result("Failed to click outside button")
                
        except Exception as e:
            logger.error(f"Failed to wait for and click outside button: {e}")
            return ActionResult.failure_result("Failed to wait for and click outside button", error=e)
    
    def toggle_housing_menu_and_find_house_start(self) -> ActionResult:
        """Press 'h' key to toggle housing menu and find house_start button with retry logic"""
        try:
            logger.info("Pressing 'h' key to toggle housing menu...")
            
            # Define search criteria for house_start
            house_start_criteria = ElementSearchCriteria(
                name="house_start",
                element_type=ElementType.BUTTON,
                template_path=config.get_game_template_path(AssetPaths.GameTemplates.HOUSE_START),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "House start button"}
            )
            
            # Define search criteria for outside_button (to verify click success)
            outside_button_criteria = ElementSearchCriteria(
                name="outside_button",
                element_type=ElementType.BUTTON,
                template_path=config.get_game_template_path(AssetPaths.GameTemplates.OUTSIDE_BUTTON),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Outside button"}
            )
            
            # First attempt: Press 'h' and look for house_start
            pyautogui.press('h')
            time.sleep(0.3)  # Wait for menu to toggle
            
            logger.info("Waiting for house_start to appear...")
            result = self.wait_for_element(house_start_criteria, timeout=2.0, check_interval=0.5)
            
            if result.success:
                logger.info("House start button found after first 'h' press")
                # Click the house_start button with retry logic
                return self._click_house_start_with_retry(house_start_criteria, outside_button_criteria)
            else:
                logger.info("House start button not found after first 'h' press, trying second 'h' press...")
                
                # Second attempt: Press 'h' again and look for house_start
                pyautogui.press('h')
                time.sleep(0.3)  # Wait for menu to toggle
                
                logger.info("Waiting for house_start to appear after second 'h' press...")
                result = self.wait_for_element(house_start_criteria, timeout=2.0, check_interval=0.5)
                
                if result.success:
                    logger.info("House start button found after second 'h' press")
                    # Click the house_start button with retry logic
                    return self._click_house_start_with_retry(house_start_criteria, outside_button_criteria)
                else:
                    logger.error("House start button not found after both 'h' presses")
                    return ActionResult.failure_result("House start button not found after both 'h' presses")
            
        except Exception as e:
            logger.error(f"Failed to toggle housing menu and find house start: {e}")
            return ActionResult.failure_result("Failed to toggle housing menu and find house start", error=e)
    
    def _click_house_start_with_retry(self, house_start_criteria, outside_button_criteria) -> ActionResult:
        """Click house_start button with retry logic"""
        try:
            logger.info("House start button detected successfully")
            
            # Retry logic: try up to 3 times
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                logger.info(f"Attempt {attempt}/{max_retries}: Clicking house start button...")
                
                # Click the house_start button
                click_result = self.find_and_click(house_start_criteria, wait_time=1.0, retries=1)
                
                if not click_result.success:
                    logger.warning(f"Failed to click house start button on attempt {attempt}")
                    if attempt < max_retries:
                        logger.info("Moving mouse up 50 pixels and waiting 5 seconds before retry...")
                        current_x, current_y = pyautogui.position()
                        pyautogui.moveTo(current_x, current_y - 50)
                        time.sleep(5.0)
                        continue
                    else:
                        return ActionResult.failure_result("Failed to click house start button after all retries")
                
                # Wait 1 second and check for outside_button
                logger.info("Waiting 1 second to check if outside button appears...")
                time.sleep(1.0)
                
                if self.ui_detector.is_element_present(outside_button_criteria):
                    logger.info(f"Success! Outside button appeared after attempt {attempt}")
                    return ActionResult.success_result("House start button clicked successfully")
                else:
                    logger.warning(f"Outside button not found after attempt {attempt} - button may have been grayed out")
                    if attempt < max_retries:
                        logger.info("Moving mouse up 50 pixels and waiting 5 seconds before retry...")
                        current_x, current_y = pyautogui.position()
                        pyautogui.moveTo(current_x, current_y - 50)
                        time.sleep(5.0)
                    else:
                        logger.error("Failed to get outside button to appear after all retries")
                        return ActionResult.failure_result("Failed to navigate to house start: Outside button not found within timeout")
            
        except Exception as e:
            logger.error(f"Failed to click house start button with retry: {e}")
            return ActionResult.failure_result("Failed to click house start button with retry", error=e)

    def close_housing_menu(self) -> ActionResult:
        """Press the 'H' key to close the housing menu"""
        try:
            logger.info("Pressing 'H' key to close housing menu...")
            
            # Press 'H' key
            pyautogui.press('h')
            
            # Wait a moment for the action to register
            time.sleep(0.3)
            
            logger.info("'H' key pressed successfully - housing menu should be closed")
            return ActionResult.success_result("'H' key pressed successfully - housing menu closed")
            
        except Exception as e:
            logger.error(f"Failed to press 'H' key: {e}")
            return ActionResult.failure_result("Failed to press 'H' key", error=e)