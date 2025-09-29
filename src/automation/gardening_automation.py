"""
Gardening automation module
Handles red barn farm equipping and gardening-specific tasks
"""
import time
import yaml
import pyautogui
from src.core.automation_base import AutomationBase
from src.core.action_result import ActionResult
from src.core.element import ElementSearchCriteria, ElementType, DetectionMethod
from src.utils.logger import logger
from src.utils.ocr_utils import OCRUtils
from src.constants import AssetPaths
from config import config
from src.automation.movement_automation import MovementAutomation

class GardeningAutomation(AutomationBase):
    """Handles gardening-specific automation tasks in Wizard101"""
    
    def __init__(self, ui_detector):
        super().__init__(ui_detector)
        self.movement_automation = MovementAutomation(ui_detector)
        self.ocr_utils = OCRUtils()
        self.garden_config = self._load_garden_config()
    
    def execute(self) -> ActionResult:
        """Execute gardening automation workflow"""
        try:
            logger.info("Starting gardening automation")
            
            # First, navigate to the main garden area
            result = self.navigate_to_garden()
            if not result.success:
                return result
            
            # # Check if elder couch potatoes are ready
            # result = self.check_couch_potatoes_ready()
            # if not result.success:
            #     logger.warning("Failed to check couch potatoes status")
            #     return ActionResult.failure_result("Failed to check couch potatoes status")
            
            # # Guard clause: If not ready, do nothing and return
            # if not (result.data and result.data.get('couch_potatoes_ready', False)):
            #     logger.info("Couch potatoes are not ready yet, doing nothing")
            #     return ActionResult.success_result("Couch potatoes not ready, no action taken")
            
            # # At this point, we know couch potatoes are ready - harvest and replant
            # logger.info("Couch potatoes are ready! Starting harvest and replant cycle...")
            
            # # Harvest the couch potatoes
            # result = self.harvest_couch_potatoes()
            # if not result.success:
            #     logger.warning("Harvest failed")
            #     return ActionResult.failure_result("Harvest failed")

            # # Now replant the couch potatoes
            # logger.info("Starting replanting process...")
            # replant_result = self.replant_couch_potatoes()
            # if not replant_result.success:
            #     logger.warning("Replanting failed")
            #     return ActionResult.failure_result("Replanting failed")
            
            # After replanting, update plant status
            logger.info("Replanting completed, updating plant status...")
            status_result = self.update_plant_status()
            if not status_result.success:
                logger.warning("Failed to update plant status")
                return ActionResult.failure_result("Failed to update plant status")
            
            logger.info("Gardening automation completed successfully")
            return ActionResult.success_result("Gardening automation completed successfully")
            
        except Exception as e:
            return ActionResult.failure_result("Gardening automation failed", error=e)
    
    def navigate_to_garden(self) -> ActionResult:
        """Navigate to the main garden area"""
        try:
            logger.info("Navigating to garden area...")
            
            # Use movement automation to navigate to garden
            result = self.movement_automation.navigate_to_garden()
            if not result.success:
                return result
            
            logger.info("Successfully navigated to garden area")
            
            
            return ActionResult.success_result("Successfully navigated to garden area")
            
        except Exception as e:
            logger.error(f"Failed to navigate to garden: {e}")
            return ActionResult.failure_result("Failed to navigate to garden", error=e)
    
    def get_movement_automation(self) -> MovementAutomation:
        """Get the movement automation instance for external use"""
        return self.movement_automation
    
    def check_couch_potatoes_ready(self) -> ActionResult:
        """Check if elder couch potatoes are ready for harvest"""
        try:
            logger.info("Checking if elder couch potatoes are ready...")
            
            # Define search criteria for elder couch potatoes ready
            couch_potatoes_criteria = ElementSearchCriteria(
                name="elder_couch_potatoes_ready",
                element_type=ElementType.IMAGE,
                template_path=config.get_gardening_template_path(AssetPaths.GardeningTemplates.ELDER_COUCH_POTATOES_READY),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Elder couch potatoes ready indicator"}
            )
            
            # Check if elder couch potatoes ready image is present
            if self.ui_detector.is_element_present(couch_potatoes_criteria):
                logger.info("The couch potatoes are ready! (Not harvesting yet)")
                return ActionResult.success_result("Elder couch potatoes are ready", data={'couch_potatoes_ready': True})
            else:
                logger.info("Couch potatoes are not ready yet")
                return ActionResult.success_result("Couch potatoes are not ready yet", data={'couch_potatoes_ready': False})
                
        except Exception as e:
            logger.error(f"Failed to check couch potatoes status: {e}")
            return ActionResult.failure_result("Failed to check couch potatoes status", error=e)
    
    def _load_garden_config(self) -> dict:
        """Load garden configuration from garden_config.yaml"""
        try:
            with open('garden_config.yaml', 'r', encoding='utf-8') as file:
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            logger.warning("garden_config.yaml not found, using default configuration")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing garden_config.yaml: {e}")
            return {}
    
    def _is_garden_actions_enabled(self) -> bool:
        """Check if garden actions are enabled in the garden config"""
        actions_config = self.garden_config.get('garden_actions', {})
        return actions_config.get('enabled', False)
    
    def harvest_couch_potatoes(self) -> ActionResult:
        """Harvest elder couch potatoes using the configured garden actions"""
        try:
            logger.info("Starting couch potatoes harvest...")
            
            if not self._is_garden_actions_enabled():
                logger.warning("Garden actions disabled, cannot harvest")
                return ActionResult.failure_result("Garden actions disabled")
            
            actions_config = self.garden_config.get('garden_actions', {})
            actions = actions_config.get('actions', [])
            
            if not actions:
                logger.warning("No garden actions configured")
                return ActionResult.failure_result("No garden actions configured")
            
            # Execute each action in sequence
            for i, action in enumerate(actions):
                key = action.get('key', 'space')
                duration = action.get('duration', 0.1)
                wait_after = action.get('wait_after', 0.5)
                should_harvest = action.get('harvest', False)
                
                logger.info(f"Harvest action {i+1}/{len(actions)}: pressing '{key}' for {duration}s")
                
                # Press the key for the specified duration
                if duration > 0:
                    pyautogui.keyDown(key)
                    time.sleep(duration)
                    pyautogui.keyUp(key)
                else:
                    pyautogui.press(key)
                
                # Wait after the action
                if wait_after > 0:
                    time.sleep(wait_after)
                
                # Perform harvesting if requested
                if should_harvest:
                    logger.info("Harvesting requested after this action")
                    harvest_result = self._harvest_until_complete()
                    if not harvest_result.success:
                        logger.warning("Harvesting failed, but continuing with next action")
            
            logger.info("Couch potatoes harvest completed successfully")
            return ActionResult.success_result("Couch potatoes harvest completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to harvest couch potatoes: {e}")
            return ActionResult.failure_result("Failed to harvest couch potatoes", error=e)
    
    def _harvest_until_complete(self) -> ActionResult:
        """Harvest plants by pressing 'x' repeatedly until elder_couch_potatoes_ready is no longer visible"""
        try:
            logger.info("Starting harvest until complete...")
            
            max_attempts = 50  # Prevent infinite loop
            attempts = 0
            consecutive_not_visible = 0
            required_consecutive = 5  # Must not be visible for 0.5 seconds (5 * 0.1s)
            
            while attempts < max_attempts:
                attempts += 1
                
                # Check if elder_couch_potatoes_ready is visible
                if self._is_elder_couch_potatoes_visible():
                    logger.info(f"Elder couch potatoes still visible (attempt {attempts}), pressing 'x' to harvest")
                    
                    # Press 'x' to harvest
                    pyautogui.press('x')
                    time.sleep(0.3)  # Wait a bit for harvest action
                    
                    consecutive_not_visible = 0  # Reset counter
                else:
                    consecutive_not_visible += 1
                    logger.info(f"Elder couch potatoes not visible ({consecutive_not_visible}/{required_consecutive})")
                    
                    # If we haven't seen the plant for enough consecutive checks, we're done
                    if consecutive_not_visible >= required_consecutive:
                        logger.info("Harvest complete - elder couch potatoes no longer visible for 0.5+ seconds")
                        return ActionResult.success_result("Harvest completed successfully")
                    
                    time.sleep(0.1)  # Short wait before next check
            
            logger.warning(f"Harvest incomplete - reached maximum attempts ({max_attempts})")
            return ActionResult.failure_result("Harvest incomplete - reached maximum attempts")
            
        except Exception as e:
            logger.error(f"Failed to harvest until complete: {e}")
            return ActionResult.failure_result("Failed to harvest until complete", error=e)
    
    def _is_elder_couch_potatoes_visible(self) -> bool:
        """Check if elder_couch_potatoes_ready image is visible on screen"""
        try:
            plant_criteria = ElementSearchCriteria(
                name="elder_couch_potatoes_ready",
                element_type=ElementType.IMAGE,
                template_path=config.get_gardening_template_path("elder_couch_potatoes_ready.png"),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Elder couch potatoes ready detection"}
            )
            
            return self.ui_detector.is_element_present(plant_criteria)
            
        except Exception as e:
            logger.error(f"Failed to check if elder couch potatoes are visible: {e}")
            return False
    
    def _navigate_to_house_start(self) -> ActionResult:
        """Navigate back to the start of the house using housing navigation"""
        try:
            logger.info("Navigating back to house start...")
            
            # Import housing navigation here to avoid circular imports
            from src.automation.housing_navigation import HousingNavigationAutomation
            
            # Create housing navigation instance
            housing_nav = HousingNavigationAutomation(self.ui_detector)
            
            # Execute the house navigation flow (which handles being already in house)
            result = housing_nav.execute()
            
            if result.success:
                logger.info("Successfully navigated back to house start")
                return ActionResult.success_result("Successfully navigated back to house start")
            else:
                logger.error(f"Failed to navigate to house start: {result.message}")
                return ActionResult.failure_result(f"Failed to navigate to house start: {result.message}")
                
        except Exception as e:
            logger.error(f"Failed to navigate to house start: {e}")
            return ActionResult.failure_result("Failed to navigate to house start", error=e)
    
    def _navigate_to_garden(self) -> ActionResult:
        """Navigate back to the garden using movement automation"""
        try:
            logger.info("Navigating back to garden...")
            
            # Use movement automation to navigate to garden
            result = self.movement_automation.navigate_to_garden()
            
            if result.success:
                logger.info("Successfully navigated back to garden")
                return ActionResult.success_result("Successfully navigated back to garden")
            else:
                logger.error(f"Failed to navigate to garden: {result.message}")
                return ActionResult.failure_result(f"Failed to navigate to garden: {result.message}")
                
        except Exception as e:
            logger.error(f"Failed to navigate to garden: {e}")
            return ActionResult.failure_result("Failed to navigate to garden", error=e)
    
    def _navigate_house_front_and_back_to_garden(self) -> ActionResult:
        """Navigate to house front and then back to garden - reusable pattern for gardening operations"""
        try:
            logger.info("Navigating to house front and back to garden...")
            
            # Step 1: Navigate to house start
            logger.info("Step 1: Navigating to house start...")
            house_nav_result = self._navigate_to_house_start()
            if not house_nav_result.success:
                logger.warning("Failed to navigate to house start")
                return ActionResult.failure_result("Failed to navigate to house start")
            
            # Step 2: Navigate back to garden
            logger.info("Step 2: Navigating back to garden...")
            garden_nav_result = self._navigate_to_garden()
            if not garden_nav_result.success:
                logger.warning("Failed to navigate back to garden")
                return ActionResult.failure_result("Failed to navigate back to garden")
            
            logger.info("Successfully completed house front to garden navigation")
            return ActionResult.success_result("Successfully completed house front to garden navigation")
            
        except Exception as e:
            logger.error(f"Failed to navigate house front and back to garden: {e}")
            return ActionResult.failure_result("Failed to navigate house front and back to garden", error=e)
    
    def replant_couch_potatoes(self) -> ActionResult:
        """Replant elder couch potatoes after harvesting"""
        try:
            logger.info("Starting replanting process for elder couch potatoes...")
            
            # # Step 1: Plant the first seed
            # logger.info("Step 1: Planting first seed...")
            # first_seed_result = self.plant_first_seed()
            # if not first_seed_result.success:
            #     return first_seed_result
            
            # Step 2: Plant all remaining seeds
            logger.info("Step 2: Planting all remaining seeds...")
            plant_all_result = self.plant_all_seeds()
            if not plant_all_result.success:
                return plant_all_result
            
            logger.info("Replanting process completed successfully!")
            logger.info("All couch potato seeds have been planted")
            
            return ActionResult.success_result("Replanting process completed successfully - all seeds planted")
            
        except Exception as e:
            logger.error(f"Failed to replant couch potatoes: {e}")
            return ActionResult.failure_result("Failed to replant couch potatoes", error=e)
    
    def plant_first_seed(self) -> ActionResult:
        """Plant the first couch potato seed"""
        try:
            logger.info("Starting first seed planting process...")
            
            # Navigate to house front and back to garden
            nav_result = self._navigate_house_front_and_back_to_garden()
            if not nav_result.success:
                logger.warning("Failed to navigate to house front and back to garden")
                return ActionResult.failure_result("Failed to navigate to house front and back to garden")
            
            # Press 'g' to open the gardening menu
            logger.info("Opening gardening menu...")
            pyautogui.press('g')
            time.sleep(1.0)  # Wait for menu to open
            
            # Look for the seeds gardening menu and click on it
            logger.info("Looking for seeds gardening menu...")
            seeds_menu_criteria = ElementSearchCriteria(
                name="seeds_gardening_menu",
                element_type=ElementType.IMAGE,
                template_path=config.get_gardening_template_path(AssetPaths.GardeningTemplates.SEEDS_GARDENING_MENU),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Seeds gardening menu button"}
            )
            
            # Find and click the seeds menu
            seeds_menu_element = self.ui_detector.find_element(seeds_menu_criteria)
            if seeds_menu_element:
                logger.info("Found seeds gardening menu, clicking on it...")
                click_result = self.click_element(seeds_menu_element)
                if click_result.success:
                    logger.info("Successfully clicked on seeds gardening menu")
                    time.sleep(1.0)  # Wait for seeds menu to open
                else:
                    logger.warning("Failed to click on seeds gardening menu")
                    return ActionResult.failure_result("Failed to click on seeds gardening menu")
            else:
                logger.warning("Could not find seeds gardening menu")
                return ActionResult.failure_result("Could not find seeds gardening menu")
            
            # Now look for and click on the couch potatoes gardening menu
            logger.info("Looking for couch potatoes gardening menu...")
            couch_potatoes_menu_criteria = ElementSearchCriteria(
                name="couch_potatoes_gardening_menu",
                element_type=ElementType.IMAGE,
                template_path=config.get_gardening_template_path(AssetPaths.GardeningTemplates.COUCH_POTATOES_GARDENING_MENU),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Couch potatoes gardening menu button"}
            )
            
            # Find and click the couch potatoes menu
            couch_potatoes_menu_element = self.ui_detector.find_element(couch_potatoes_menu_criteria)
            if couch_potatoes_menu_element:
                logger.info("Found couch potatoes gardening menu, clicking on it...")
                click_result = self.click_element(couch_potatoes_menu_element)
                if click_result.success:
                    logger.info("Successfully clicked on couch potatoes gardening menu")
                    time.sleep(1.0)  # Wait for couch potatoes menu to open
                else:
                    logger.warning("Failed to click on couch potatoes gardening menu")
                    return ActionResult.failure_result("Failed to click on couch potatoes gardening menu")
            else:
                logger.warning("Could not find couch potatoes gardening menu")
                return ActionResult.failure_result("Could not find couch potatoes gardening menu")
            
            # Now look for the plant first seed location
            logger.info("Looking for plant first seed location...")
            plant_first_seed_criteria = ElementSearchCriteria(
                name="plant_first_seed",
                element_type=ElementType.IMAGE,
                template_path=config.get_gardening_template_path(AssetPaths.GardeningTemplates.PLANT_FIRST_SEED),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Plant first seed location"}
            )
            
            # Find the plant first seed location
            plant_first_seed_element = self.ui_detector.find_element(plant_first_seed_criteria)
            if plant_first_seed_element:
                logger.info("Found plant first seed location, moving mouse there...")
                
                # Get the center coordinates of the element
                center_coords = plant_first_seed_element.center
                
                logger.info(f"Moving mouse to plant first seed location at ({center_coords.x}, {center_coords.y})")
                
                # Move mouse to the location and click to plant
                pyautogui.moveTo(center_coords.x, center_coords.y)
                time.sleep(0.5)  # Brief pause after moving mouse
                
                logger.info("Mouse positioned at plant first seed location, clicking to plant...")
                
                # Click to plant the couch potato
                pyautogui.click(center_coords.x, center_coords.y)
                time.sleep(1.0)  # Wait for planting action to complete
                
                logger.info("Successfully planted first couch potato seed")
                return ActionResult.success_result("First seed planted successfully")
            else:
                logger.warning("Could not find plant first seed location")
                return ActionResult.failure_result("Could not find plant first seed location")
                
        except Exception as e:
            logger.error(f"Failed to plant first seed: {e}")
            return ActionResult.failure_result("Failed to plant first seed", error=e)
    
    def plant_all_seeds(self) -> ActionResult:
        """Plant all remaining seeds using the plant_all spell"""
        try:
            logger.info("Starting plant all seeds process...")
            
            # Navigate to house front and back to garden for planting remaining seeds
            nav_result = self._navigate_house_front_and_back_to_garden()
            if not nav_result.success:
                logger.warning("Failed to navigate to house front and back to garden")
                return ActionResult.failure_result("Failed to navigate to house front and back to garden")
            
            # Press 'g' to open the gardening menu again
            logger.info("Opening gardening menu again...")
            pyautogui.press('g')
            time.sleep(1.0)  # Wait for menu to open
            
            # Look for and click on the utility gardening menu
            logger.info("Looking for utility gardening menu...")
            utility_menu_criteria = ElementSearchCriteria(
                name="utility_gardening_menu",
                element_type=ElementType.IMAGE,
                template_path=config.get_gardening_template_path(AssetPaths.GardeningTemplates.UTILITY_GARDENING_MENU),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Utility gardening menu button"}
            )
            
            # Find and click the utility menu
            utility_menu_element = self.ui_detector.find_element(utility_menu_criteria)
            if utility_menu_element:
                logger.info("Found utility gardening menu, clicking on it...")
                click_result = self.click_element(utility_menu_element)
                if click_result.success:
                    logger.info("Successfully clicked on utility gardening menu")
                    time.sleep(1.0)  # Wait for utility menu to open
                else:
                    logger.warning("Failed to click on utility gardening menu")
                    return ActionResult.failure_result("Failed to click on utility gardening menu")
            else:
                logger.warning("Could not find utility gardening menu")
                return ActionResult.failure_result("Could not find utility gardening menu")
            
            # Now look for and click on the plant_all spell
            logger.info("Looking for plant_all spell...")
            plant_all_criteria = ElementSearchCriteria(
                name="plant_all",
                element_type=ElementType.IMAGE,
                template_path=config.get_gardening_template_path(AssetPaths.GardeningTemplates.PLANT_ALL),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Plant all spell button"}
            )
            
            # Find and click the plant_all spell
            plant_all_element = self.ui_detector.find_element(plant_all_criteria)
            if plant_all_element:
                logger.info("Found plant_all spell, clicking on it...")
                click_result = self.click_element(plant_all_element)
                if click_result.success:
                    logger.info("Successfully clicked on plant_all spell")
                    time.sleep(2.0)  # Wait for plant_all spell to complete
                else:
                    logger.warning("Failed to click on plant_all spell")
                    return ActionResult.failure_result("Failed to click on plant_all spell")
            else:
                logger.warning("Could not find plant_all spell")
                return ActionResult.failure_result("Could not find plant_all spell")
            
            # Now look for and click on the planted couch potato
            logger.info("Looking for planted couch potato...")
            planted_potato_criteria = ElementSearchCriteria(
                name="planted_couch_potato",
                element_type=ElementType.IMAGE,
                template_path=config.get_gardening_template_path(AssetPaths.GardeningTemplates.PLANTED_COUCH_POTATO),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Planted couch potato to click"}
            )
            
            # Find and click the planted couch potato
            planted_potato_element = self.ui_detector.find_element(planted_potato_criteria)
            if planted_potato_element:
                logger.info("Found planted couch potato, positioning mouse and wiggling...")
                
                # Get the center coordinates of the element
                center_coords = planted_potato_element.center
                
                # Move mouse to the center position
                pyautogui.moveTo(center_coords.x, center_coords.y)
                time.sleep(0.2)  # Brief pause
                
                # Wiggle the mouse slightly to ensure cursor locks onto the plant
                wiggle_result = self._wiggle_mouse(center_coords.x, center_coords.y)
                if not wiggle_result.success:
                    logger.warning("Mouse wiggle failed, but continuing with click")
                
                logger.info("Mouse positioned and wiggled, clicking on planted couch potato...")
                pyautogui.click(center_coords.x, center_coords.y)
                time.sleep(1.0)  # Wait for action to complete
                
                logger.info("Successfully clicked on planted couch potato")
            else:
                logger.warning("Could not find planted couch potato")
                return ActionResult.failure_result("Could not find planted couch potato")
            
            # Finally, look for and click on the confirm plant all button
            logger.info("Looking for confirm plant all button...")
            confirm_plant_all_criteria = ElementSearchCriteria(
                name="confirm_plant_all",
                element_type=ElementType.IMAGE,
                template_path=config.get_gardening_template_path(AssetPaths.GardeningTemplates.CONFIRM_PLANT_ALL),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Confirm plant all button"}
            )
            
            # Find and click the confirm plant all button
            confirm_plant_all_element = self.ui_detector.find_element(confirm_plant_all_criteria)
            if confirm_plant_all_element:
                logger.info("Found confirm plant all button, clicking on it...")
                click_result = self.click_element(confirm_plant_all_element)
                if click_result.success:
                    logger.info("Successfully clicked on confirm plant all button")
                    time.sleep(2.0)  # Wait for confirmation to complete
                else:
                    logger.warning("Failed to click on confirm plant all button")
                    return ActionResult.failure_result("Failed to click on confirm plant all button")
            else:
                logger.warning("Could not find confirm plant all button")
                return ActionResult.failure_result("Could not find confirm plant all button")
            
            logger.info("Plant all seeds process completed successfully")
            return ActionResult.success_result("Plant all seeds process completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to plant all seeds: {e}")
            return ActionResult.failure_result("Failed to plant all seeds", error=e)
    
    def update_plant_status(self) -> ActionResult:
        """Update plant status by navigating to garden, opening menu, and hovering over plant location"""
        try:
            logger.info("Starting plant status update process...")
            
            # # Step 1: Navigate to house front and back to garden
            # nav_result = self._navigate_house_front_and_back_to_garden()
            # if not nav_result.success:
            #     logger.warning("Failed to navigate to house front and back to garden")
            #     return ActionResult.failure_result("Failed to navigate to house front and back to garden")
            
            # Step 2: Press 'g' to open the gardening menu
            logger.info("Opening gardening menu...")
            pyautogui.press('g')
            time.sleep(1.0)  # Wait for menu to open
            
            # Step 3: Position mouse at center horizontally and middle of top half vertically
            logger.info("Positioning mouse at center of screen (middle of top half)...")
            
            # Get screen dimensions
            screen_width, screen_height = pyautogui.size()
            
            # Calculate position: center horizontally, 35% from top
            center_x = screen_width // 2
            center_y = int(screen_height * 0.35)  # 35% from top
            
            logger.info(f"Moving mouse to center position at ({center_x}, {center_y})")
            
            # Move mouse to the calculated position
            pyautogui.moveTo(center_x, center_y)
            time.sleep(0.5)  # Brief pause after moving mouse
            
            # Wiggle the mouse to lock onto any plant in that area
            wiggle_result = self._wiggle_mouse(center_x, center_y)
            if not wiggle_result.success:
                logger.warning("Mouse wiggle failed, but continuing")
            
            # Wait for popup to appear after hovering
            time.sleep(1.5)
            
            # Try to read the plant popup content
            popup_result = self.ocr_utils.read_plant_popup()
            if popup_result.success:
                logger.info("Successfully read plant popup content")
                
                # Parse the plant status from the OCR text
                plant_status = self._parse_plant_status(popup_result.data)
                if plant_status:
                    self._log_plant_status(plant_status)
                else:
                    logger.warning("Failed to parse plant status from popup content")
            else:
                logger.warning("Failed to read plant popup content")
            
            logger.info("Successfully positioned and wiggled mouse at center of screen")
            return ActionResult.success_result("Successfully positioned and wiggled mouse at center of screen")
                
        except Exception as e:
            logger.error(f"Failed to update plant status: {e}")
            return ActionResult.failure_result("Failed to update plant status", error=e)
    
    def _wiggle_mouse(self, x: int, y: int) -> ActionResult:
        """Wiggle the mouse slightly to ensure cursor locks onto a plant or element"""
        try:
            logger.info(f"Wiggling mouse at position ({x}, {y}) to lock onto element...")
            
            # Wiggle the mouse slightly in a pattern to ensure cursor locks onto the plant
            pyautogui.moveTo(x + 2, y + 1)  # Move slightly right and down
            time.sleep(0.1)
            pyautogui.moveTo(x - 2, y - 1)  # Move slightly left and up
            time.sleep(0.1)
            pyautogui.moveTo(x + 1, y - 2)  # Move slightly right and up
            time.sleep(0.1)
            pyautogui.moveTo(x - 1, y + 2)  # Move slightly left and down
            time.sleep(0.1)
            pyautogui.moveTo(x, y)  # Return to center
            time.sleep(0.2)  # Brief pause after wiggling
            
            logger.info("Mouse wiggle completed successfully")
            return ActionResult.success_result("Mouse wiggle completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to wiggle mouse: {e}")
            return ActionResult.failure_result("Failed to wiggle mouse", error=e)
    
    def _parse_plant_status(self, ocr_text: str) -> dict:
        """Parse plant status from OCR text"""
        try:
            import yaml
            import re
            
            # Load plant database
            with open('plant_database.yaml', 'r', encoding='utf-8') as file:
                plant_db = yaml.safe_load(file)
            
            # Extract plant name
            plant_name = self._extract_plant_name(ocr_text)
            if not plant_name:
                logger.warning("Could not identify plant name from OCR text")
                return None
            
            # Get plant data from database
            plant_data = plant_db['plants'].get(plant_name)
            if not plant_data:
                logger.warning(f"Plant '{plant_name}' not found in database")
                return None
            
            # Extract current stage
            current_stage = self._extract_current_stage(ocr_text)
            if not current_stage:
                logger.warning("Could not determine current plant stage")
                return None
            
            # Extract likes
            likes = self._extract_likes(ocr_text)
            
            # Calculate growth modifiers
            modifiers = self._calculate_growth_modifiers(likes, plant_data['growth_modifiers'])
            
            # Determine next stage and time to next stage
            next_stage, time_to_next = self._calculate_next_stage(current_stage, plant_data['stages'], modifiers)
            
            return {
                'plant_name': plant_data['name'],
                'current_stage': current_stage,
                'next_stage': next_stage,
                'time_to_next_hours': time_to_next,
                'likes': likes,
                'modifiers': modifiers,
                'total_modifier_percent': sum(modifiers.values())
            }
            
        except Exception as e:
            logger.error(f"Failed to parse plant status: {e}")
            return None
    
    def _extract_plant_name(self, text: str) -> str:
        """Extract plant name from OCR text"""
        # Look for known plant names in the text
        plant_names = {
            'COUCH POTATOES': 'couch_potatoes',
            'Couch Potatoes': 'couch_potatoes'
        }
        
        for display_name, db_name in plant_names.items():
            if display_name in text.upper():
                return db_name
        
        return None
    
    def _extract_current_stage(self, text: str) -> str:
        """Extract current plant stage from OCR text"""
        text_upper = text.upper()
        
        # Look for progress indicators
        if 'PROGRESS TO YOUNG:' in text_upper:
            return 'seedling'
        elif 'PROGRESS TO MATURE:' in text_upper:
            return 'young'
        elif 'PROGRESS TO ELDER:' in text_upper:
            return 'mature'
        elif 'ELDER' in text_upper and 'PROGRESS' not in text_upper:
            return 'elder'
        
        return None
    
    def _extract_likes(self, text: str) -> list:
        """Extract likes from OCR text"""
        likes = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith('LIKES:'):
                like_item = line.replace('LIKES:', '').strip()
                if like_item:
                    # Clean up OCR anomalies
                    like_item = self._clean_like_item(like_item)
                    
                    # Handle "This House" - we'll need to determine the actual house type
                    if like_item.upper() == 'THIS HOUSE':
                        # For now, we'll assume Red Barn Farm since that's what we're using
                        # In a real implementation, you'd need to detect the actual house type
                        like_item = 'Red Barn Farm'
                    
                    if like_item:  # Only add if we have something after cleaning
                        likes.append(like_item)
        
        return likes
    
    def _clean_like_item(self, item: str) -> str:
        """Clean up OCR anomalies in like items"""
        import re
        
        # Remove common OCR artifacts
        cleaned = item.strip()
        
        # Remove trailing punctuation and symbols
        cleaned = re.sub(r'[|!@#$%^&*()_+=\[\]{};:"\\|,.<>?/~`]+$', '', cleaned)
        
        # Remove leading punctuation and symbols
        cleaned = re.sub(r'^[|!@#$%^&*()_+=\[\]{};:"\\|,.<>?/~`]+', '', cleaned)
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _calculate_growth_modifiers(self, likes: list, plant_modifiers: dict) -> dict:
        """Calculate growth modifiers based on likes"""
        modifiers = {}
        
        for like in likes:
            for modifier_percent, items in plant_modifiers.items():
                for item in items:
                    # Use flexible matching to handle OCR variations
                    if self._matches_like_item(like, item):
                        # Convert percentage string to float
                        percent = float(modifier_percent.replace('%', '').replace('+', ''))
                        modifiers[item] = percent
                        break
        
        return modifiers
    
    def _matches_like_item(self, like: str, database_item: str) -> bool:
        """Check if a like item matches a database item with OCR tolerance"""
        like_upper = like.upper().strip()
        item_upper = database_item.upper().strip()
        
        # Exact match
        if like_upper == item_upper:
            return True
        
        # Check if like contains the database item (for partial matches)
        if item_upper in like_upper:
            return True
        
        # Check if database item contains the like (for partial matches)
        if like_upper in item_upper:
            return True
        
        return False
    
    def _calculate_next_stage(self, current_stage: str, stages: dict, modifiers: dict) -> tuple:
        """Calculate next stage and time to reach it"""
        stage_order = ['seedling', 'young', 'mature', 'elder']
        
        try:
            current_index = stage_order.index(current_stage)
            if current_index >= len(stage_order) - 1:
                return 'elder', 0  # Already at final stage
            
            next_stage = stage_order[current_index + 1]
            
            # Get base time for current stage to next stage
            stage_key = f"{current_stage}_to_{next_stage}"
            base_time = stages.get(stage_key, 0)
            
            # Apply modifiers (positive modifiers make growth faster = less time)
            total_modifier = sum(modifiers.values())
            modified_time = base_time * (1 - total_modifier / 100)
            
            return next_stage, modified_time
            
        except (ValueError, KeyError) as e:
            logger.error(f"Failed to calculate next stage: {e}")
            return None, 0
    
    def _log_plant_status(self, status: dict):
        """Log detailed plant status information"""
        logger.info("=" * 50)
        logger.info("PLANT STATUS ANALYSIS")
        logger.info("=" * 50)
        logger.info(f"Plant: {status['plant_name']}")
        logger.info(f"Current Stage: {status['current_stage'].upper()}")
        logger.info(f"Next Stage: {status['next_stage'].upper()}")
        logger.info(f"Time to Next Stage: {status['time_to_next_hours']:.1f} hours")
        logger.info("")
        logger.info("LIKES:")
        for like in status['likes']:
            logger.info(f"  - {like}")
        logger.info("")
        logger.info("GROWTH MODIFIERS:")
        if status['modifiers']:
            for item, percent in status['modifiers'].items():
                sign = "+" if percent > 0 else ""
                logger.info(f"  {item}: {sign}{percent:.0f}%")
        else:
            logger.info("  No growth modifiers found")
        logger.info(f"")
        logger.info(f"TOTAL MODIFIER: {status['total_modifier_percent']:+.0f}%")
        logger.info("=" * 50)
    
