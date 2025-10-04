"""
World navigation automation module
Handles navigation through worlds in Wizard101
"""
import time
import yaml
import pyautogui
from src.core.automation_base import AutomationBase
from src.core.action_result import ActionResult
from src.core.element import ElementSearchCriteria, ElementType, DetectionMethod
from src.utils.logger import logger
from src.constants import AssetPaths, WorldConstants
from config import config
from src.automation.movement_automation import MovementAutomation

class WorldNavigationAutomation(AutomationBase):
    """Handles world navigation in Wizard101"""
    
    def __init__(self, ui_detector, world_config=None, target_world=None, farming_config=None):
        super().__init__(ui_detector)
        self.world_config = world_config or self._load_world_config()
        self.farming_config = farming_config
        self.movement_automation = MovementAutomation(ui_detector, config=self.world_config)
        self.target_world = target_world or WorldConstants.GRIZZLEHEIM  # Default to Grizzleheim
    
    def execute(self) -> ActionResult:
        """Execute world navigation automation workflow"""
        try:
            logger.info(f"Starting world navigation automation to {self.target_world}")
            
            # First, navigate to the house
            house_result = self.navigate_to_house()
            if not house_result.success:
                raise RuntimeError("Failed to navigate to house")
            
            # Then navigate to the world gate
            world_gate_result = self.navigate_to_world_gate()
            if not world_gate_result.success:
                raise RuntimeError("Failed to navigate to world gate")
            
            # Press 'x' to open the world gate
            world_gate_open_result = self.open_world_gate()
            if not world_gate_open_result.success:
                raise RuntimeError("Failed to open world gate")
            
            # Wait for the spiral map to open
            spiral_map_result = self.wait_for_spiral_map()
            if not spiral_map_result.success:
                raise RuntimeError("Failed to detect spiral map")
            
            # Find and select the target world on the spiral map
            world_selection_result = self.select_target_world()
            if not world_selection_result.success:
                raise RuntimeError(f"Failed to select target world: {world_selection_result.message}")
            
            # TODO: Add world navigation steps here after world selection
            # This is where the user will specify the next steps
            
            logger.info("World navigation automation completed successfully")
            return ActionResult.success_result("World navigation automation completed successfully")
        except Exception as e:
            return ActionResult.failure_result("World navigation automation failed", error=e)
    
    def navigate_to_house(self) -> ActionResult:
        """Navigate to the house using housing navigation (house selection only, no front navigation)"""
        try:
            logger.info("Navigating to house...")
            
            # Import housing navigation here to avoid circular imports
            from src.automation.housing_navigation import HousingNavigationAutomation
            
            # Create housing navigation instance
            housing_nav = HousingNavigationAutomation(self.ui_detector)
            
            # Execute only house selection (no front navigation for world navigation bot)
            result = housing_nav.execute_house_selection_only()
            
            if result.success:
                logger.info("Successfully navigated to house")
                return ActionResult.success_result("Successfully navigated to house")
            else:
                logger.error(f"Failed to navigate to house: {result.message}")
                return ActionResult.failure_result(f"Failed to navigate to house: {result.message}")
                
        except Exception as e:
            logger.error(f"Failed to navigate to house: {e}")
            return ActionResult.failure_result("Failed to navigate to house", error=e)
    
    def navigate_to_world_gate(self) -> ActionResult:
        """Navigate to the world gate from the house start position"""
        try:
            logger.info("Navigating to world gate...")
            
            # Check if we have world gate movement pattern in config
            if self.world_config and "go_to_world_gate" in self.world_config:
                logger.info("Using configured world gate movement pattern...")
                result = self.movement_automation.execute_pattern("go_to_world_gate")
                if result.success:
                    logger.info("Successfully navigated to world gate using configured pattern")
                    return ActionResult.success_result("Successfully navigated to world gate")
                else:
                    logger.warning("Configured world gate pattern failed")
                    return ActionResult.failure_result("Configured world gate pattern failed")
            else:
                logger.warning("No world gate movement pattern configured")
                return ActionResult.failure_result("No world gate movement pattern configured")
            
        except Exception as e:
            logger.error(f"Failed to navigate to world gate: {e}")
            return ActionResult.failure_result("Failed to navigate to world gate", error=e)
    
    def open_world_gate(self) -> ActionResult:
        """Open the world gate by pressing the 'x' key"""
        try:
            logger.info("Opening world gate...")
            
            # Press the 'x' key to open the world gate
            result = self.movement_automation.press_key("x", 0.1)  # Short press for key activation
            
            if result.success:
                logger.info("Successfully opened world gate")
                return ActionResult.success_result("Successfully opened world gate")
            else:
                logger.error(f"Failed to open world gate: {result.message}")
                return ActionResult.failure_result(f"Failed to open world gate: {result.message}")
                
        except Exception as e:
            logger.error(f"Failed to open world gate: {e}")
            return ActionResult.failure_result("Failed to open world gate", error=e)
    
    def wait_for_spiral_map(self) -> ActionResult:
        """Wait for the spiral map to appear after opening world gate"""
        try:
            logger.info("Waiting for spiral map to appear...")
            
            # Get the spiral map template path
            spiral_map_path = config.get_game_template_path(AssetPaths.GameTemplates.SPIRAL_MAP)
            
            # Wait for spiral map to appear with timeout
            timeout = self.world_config.get("world_settings", {}).get("spiral_map_timeout", 10.0)
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # Check if spiral map is visible
                element = self.ui_detector.find_element(
                    ElementSearchCriteria(
                        name="spiral_map",
                        element_type=ElementType.IMAGE,
                        template_path=spiral_map_path,
                        confidence_threshold=0.8,
                        detection_methods=[DetectionMethod.TEMPLATE]
                    )
                )
                
                if element is not None:
                    logger.info("Spiral map detected successfully")
                    return ActionResult.success_result("Spiral map detected")
                
                # Wait a bit before checking again
                time.sleep(0.5)
            
            logger.error("Spiral map not detected within timeout period")
            return ActionResult.failure_result("Spiral map not detected within timeout period")
            
        except Exception as e:
            logger.error(f"Failed to wait for spiral map: {e}")
            return ActionResult.failure_result("Failed to wait for spiral map", error=e)
    
    def select_target_world(self) -> ActionResult:
        """Find and select the target world on the spiral map"""
        try:
            logger.info(f"Looking for target world: {self.target_world}")
            
            # Get world selection settings from config (prefer farming config if available)
            if self.farming_config and "world_navigation" in self.farming_config:
                world_selection_config = self.farming_config.get("world_navigation", {})
            else:
                world_selection_config = self.world_config.get("world_selection", {})
            
            max_rotations = world_selection_config.get("max_spiral_rotations", 10)
            detection_timeout = world_selection_config.get("world_detection_timeout", 5.0)
            arrow_delay = world_selection_config.get("arrow_click_delay", 1.0)
            
            # Try to find the world on the current spiral map view
            for rotation in range(max_rotations):
                logger.info(f"Checking spiral map rotation {rotation + 1}/{max_rotations}")
                
                # Try to find the target world
                world_element = self.find_world_on_spiral_map()
                if world_element:
                    logger.info(f"Found {self.target_world} on spiral map")
                    
                    # Click on the world to select it
                    click_result = self.click_world(world_element)
                    if not click_result.success:
                        return ActionResult.failure_result(f"Failed to click on {self.target_world}")
                    
                    # Wait a moment for the world selection to register
                    time.sleep(1.0)
                    
                    # Click the go_to_world button
                    go_to_world_result = self.click_go_to_world()
                    if not go_to_world_result.success:
                        return ActionResult.failure_result("Failed to click go_to_world button")
                    
                    logger.info(f"Successfully selected and navigated to {self.target_world}")
                    return ActionResult.success_result(f"Successfully navigated to {self.target_world}")
                
                # If not found and we haven't reached max rotations, click the right arrow
                if rotation < max_rotations - 1:
                    logger.info("World not found, rotating spiral map...")
                    arrow_result = self.click_spiral_arrow()
                    if not arrow_result.success:
                        return ActionResult.failure_result("Failed to click spiral arrow")
                    
                    # Wait for the map to rotate
                    time.sleep(arrow_delay)
            
            logger.error(f"Could not find {self.target_world} after {max_rotations} rotations")
            return ActionResult.failure_result(f"Could not find {self.target_world} after {max_rotations} rotations")
            
        except Exception as e:
            logger.error(f"Failed to select target world: {e}")
            return ActionResult.failure_result("Failed to select target world", error=e)
    
    def find_world_on_spiral_map(self):
        """Check if the target world is visible on the current spiral map view and return the element"""
        try:
            # Get the world template filename
            world_template = WorldConstants.WORLD_TEMPLATES.get(self.target_world)
            if not world_template:
                logger.error(f"No template found for world: {self.target_world}")
                return None
            
            # Get the full template path
            world_template_path = config.get_game_template_path(world_template)
            
            # Look for the world template on the spiral map
            element = self.ui_detector.find_element(
                ElementSearchCriteria(
                    name=self.target_world,
                    element_type=ElementType.IMAGE,
                    template_path=world_template_path,
                    confidence_threshold=0.8,
                    detection_methods=[DetectionMethod.TEMPLATE]
                )
            )
            
            return element
            
        except Exception as e:
            logger.error(f"Failed to find world on spiral map: {e}")
            return None
    
    def click_spiral_arrow(self) -> ActionResult:
        """Click the right arrow to rotate the spiral map"""
        try:
            logger.info("Clicking spiral map right arrow...")
            
            # Get the spiral arrow template path
            arrow_template_path = config.get_game_template_path(AssetPaths.GameTemplates.SPIRAL_MAP_RIGHT_ARROW)
            
            # Find the arrow element
            element = self.ui_detector.find_element(
                ElementSearchCriteria(
                    name="spiral_map_right_arrow",
                    element_type=ElementType.BUTTON,
                    template_path=arrow_template_path,
                    confidence_threshold=0.8,
                    detection_methods=[DetectionMethod.TEMPLATE]
                )
            )
            
            if element is None:
                return ActionResult.failure_result("Could not find spiral map right arrow")
            
            # Click the arrow
            pyautogui.click(element.center.x, element.center.y)
            logger.info("Successfully clicked spiral map right arrow")
            
            return ActionResult.success_result("Successfully clicked spiral map right arrow")
            
        except Exception as e:
            logger.error(f"Failed to click spiral arrow: {e}")
            return ActionResult.failure_result("Failed to click spiral arrow", error=e)
    
    def click_world(self, world_element) -> ActionResult:
        """Click on the world element to select it"""
        try:
            logger.info(f"Clicking on {self.target_world}...")
            
            # Click the center of the world element
            pyautogui.click(world_element.center.x, world_element.center.y)
            logger.info(f"Successfully clicked on {self.target_world}")
            
            return ActionResult.success_result(f"Successfully clicked on {self.target_world}")
            
        except Exception as e:
            logger.error(f"Failed to click on world: {e}")
            return ActionResult.failure_result("Failed to click on world", error=e)
    
    def click_go_to_world(self) -> ActionResult:
        """Click the go_to_world button to navigate to the selected world"""
        try:
            logger.info("Looking for go_to_world button...")
            
            # Get the go_to_world template path
            go_to_world_path = config.get_game_template_path(AssetPaths.GameTemplates.GO_TO_WORLD)
            
            # Find the go_to_world button
            element = self.ui_detector.find_element(
                ElementSearchCriteria(
                    name="go_to_world_button",
                    element_type=ElementType.BUTTON,
                    template_path=go_to_world_path,
                    confidence_threshold=0.8,
                    detection_methods=[DetectionMethod.TEMPLATE]
                )
            )
            
            if element is None:
                return ActionResult.failure_result("Could not find go_to_world button")
            
            # Click the go_to_world button
            pyautogui.click(element.center.x, element.center.y)
            logger.info("Successfully clicked go_to_world button")
            
            return ActionResult.success_result("Successfully clicked go_to_world button")
            
        except Exception as e:
            logger.error(f"Failed to click go_to_world button: {e}")
            return ActionResult.failure_result("Failed to click go_to_world button", error=e)
    
    def navigate_to_world(self, world_name: str) -> ActionResult:
        """Navigate to a specific world (placeholder for future implementation)"""
        try:
            logger.info(f"Navigating to world: {world_name}")
            
            # TODO: Implement world-specific navigation logic
            # This will be implemented based on user requirements
            
            logger.info(f"Successfully navigated to {world_name} (placeholder)")
            return ActionResult.success_result(f"Successfully navigated to {world_name}")
            
        except Exception as e:
            logger.error(f"Failed to navigate to world {world_name}: {e}")
            return ActionResult.failure_result(f"Failed to navigate to world {world_name}", error=e)
    
    def get_movement_automation(self) -> MovementAutomation:
        """Get the movement automation instance for external use"""
        return self.movement_automation
    
    def _load_world_config(self) -> dict:
        """Load world navigation configuration from world_config.yaml"""
        try:
            with open('config/world_config.yaml', 'r', encoding='utf-8') as file:
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            logger.warning("config/world_config.yaml not found, using default configuration")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config/world_config.yaml: {e}")
            return {}
