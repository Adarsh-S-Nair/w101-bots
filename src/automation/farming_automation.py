"""
Farming automation module
Handles farming-specific tasks in Wizard101
"""
import time
import yaml
import pyautogui
from src.core.automation_base import AutomationBase
from src.core.action_result import ActionResult
from src.core.element import ElementSearchCriteria, ElementType, DetectionMethod
from src.utils.logger import logger
from src.constants import AssetPaths
from config import config
from src.automation.movement_automation import MovementAutomation
from src.automation.world_navigation import WorldNavigationAutomation

class FarmingAutomation(AutomationBase):
    """Handles farming-specific automation tasks in Wizard101"""
    
    def __init__(self, ui_detector, target_world=None):
        super().__init__(ui_detector)
        self.farming_config = self._load_farming_config()
        self.movement_automation = MovementAutomation(ui_detector, config=self.farming_config)
        
        # Get target world from farming config if not provided
        if target_world is None:
            target_world = self.farming_config.get("world_navigation", {}).get("target_world", "grizzleheim")
        
        self.world_navigation = WorldNavigationAutomation(ui_detector, target_world=target_world, farming_config=self.farming_config)
    
    def execute(self) -> ActionResult:
        """Execute farming automation workflow"""
        try:
            logger.info("Starting farming automation - spinning in circle until enemy detected")

            # Spin in a circle until we detect the first enemy
            self._spin_until_enemy_detected()
            
            # After stopping spin, determine what type of enemy we're facing
            enemy_data = self._detect_enemy_type()
            if enemy_data:
                enemy_name = enemy_data.get("name", "Unknown Enemy")
                logger.info(f"Detected enemy: {enemy_name}")
                
                # Execute battle strategy
                self._execute_battle_strategy(enemy_data)
            else:
                logger.warning("Could not determine enemy type")
            
            logger.info("Farming automation completed successfully")
            return ActionResult.success_result("Farming automation completed successfully")
        except Exception as e:
            return ActionResult.failure_result("Farming automation failed", error=e)
    
    def _spin_until_enemy_detected(self):
        """Spin in a circle by holding 'w' and 'a' keys until first enemy is detected"""
        logger.info("Starting to spin in circle (holding 'w' and 'a' keys)")
        logger.info("Waiting for first enemy...")
        
        # Start spinning
        pyautogui.keyDown('w')
        pyautogui.keyDown('a')
        
        try:
            # Get the first enemy template path
            from config import config
            first_enemy_path = config.get_farming_template_path(AssetPaths.FarmingTemplates.FIRST_ENEMY)
            
            # Keep spinning until enemy is detected
            while True:
                # Check for first enemy (silent mode to avoid log spam)
                enemy_detected = self.ui_detector.find_element(
                    ElementSearchCriteria(
                        name="first_enemy",
                        element_type=ElementType.BUTTON,
                        template_path=first_enemy_path,
                        confidence_threshold=0.8
                    ),
                    silent=True  # This prevents the "Could not find element" spam
                )
                
                if enemy_detected:
                    logger.info("First enemy detected! Stopping spin.")
                    break
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)
                
        finally:
            # Always release the keys when done
            pyautogui.keyUp('a')
            pyautogui.keyUp('w')
            logger.info("Stopped spinning")
    
    def _detect_enemy_type(self) -> dict:
        """Detect which type of enemy is present on screen and return enemy data"""
        enemies_config = self.farming_config.get("enemies", {})
        detection_config = self.farming_config.get("detection", {})
        confidence_threshold = detection_config.get("confidence_threshold", 0.8)
        
        for enemy_name, enemy_data in enemies_config.items():
            template_constant = enemy_data.get("template")
            if not template_constant:
                continue
            
            # Get the template filename from the constant
            template_filename = getattr(AssetPaths.FarmingTemplates, template_constant, None)
            if not template_filename:
                logger.warning(f"Template constant {template_constant} not found in AssetPaths.FarmingTemplates")
                continue
            
            # Get the template path
            from config import config
            template_path = config.get_farming_template_path(template_filename)
            
            # Check for this enemy type
            enemy_detected = self.ui_detector.find_element(
                ElementSearchCriteria(
                    name=enemy_name,
                    element_type=ElementType.BUTTON,
                    template_path=template_path,
                    confidence_threshold=confidence_threshold
                ),
                silent=True  # Silent mode to avoid log spam
            )
            
            if enemy_detected:
                return enemy_data
        
        return None
    
    def _check_for_second_enemy(self) -> bool:
        """Check if there's a second enemy present on screen"""
        try:
            # Get the second enemy template path
            from config import config
            second_enemy_path = config.get_farming_template_path(AssetPaths.FarmingTemplates.SECOND_ENEMY)
            
            # Check for second enemy
            second_enemy_detected = self.ui_detector.find_element(
                ElementSearchCriteria(
                    name="second_enemy",
                    element_type=ElementType.BUTTON,
                    template_path=second_enemy_path,
                    confidence_threshold=0.8
                ),
                silent=True  # Silent mode to avoid log spam
            )
            
            return second_enemy_detected is not None
            
        except Exception as e:
            logger.error(f"Error checking for second enemy: {e}")
            return False
    
    def _wait_for_round_completion(self):
        """Wait for a round to complete by monitoring the pass button or spellbook"""
        logger.info("Waiting for round to complete...")
        
        try:
            # First, wait for the pass button to disappear (casting has started)
            logger.info("Waiting for casting phase to start...")
            while self._check_for_pass_button():
                time.sleep(0.5)  # Check every 0.5 seconds
            
            logger.info("Pass button disappeared - casting phase started")
            
            # Then, wait for either pass button to reappear OR spellbook to appear (fight over)
            logger.info("Waiting for casting phase to complete...")
            while not self._check_for_pass_button() and not self._check_for_spellbook():
                time.sleep(0.5)  # Check every 0.5 seconds
            
            if self._check_for_spellbook():
                logger.info("Spellbook appeared - fight completed!")
                return "fight_completed"
            else:
                logger.info("Pass button reappeared - round completed, back to card selection")
                return "round_completed"
            
        except Exception as e:
            logger.error(f"Error waiting for round completion: {e}")
            return "error"
    
    def _check_for_pass_button(self) -> bool:
        """Check if the pass button is currently visible on screen"""
        try:
            # Move mouse to top middle of screen to reset any hover effects
            screen_width, screen_height = pyautogui.size()
            top_middle_x = screen_width // 2
            top_middle_y = 50
            pyautogui.moveTo(top_middle_x, top_middle_y, duration=0.1)
            
            # Get the pass button template path
            from config import config
            pass_path = config.get_farming_template_path(AssetPaths.FarmingTemplates.PASS)
            
            # Check for pass button
            pass_element = self.ui_detector.find_element(
                ElementSearchCriteria(
                    name="pass_button",
                    element_type=ElementType.BUTTON,
                    template_path=pass_path,
                    confidence_threshold=0.8
                ),
                silent=True  # Silent mode to avoid log spam
            )
            
            return pass_element is not None
            
        except Exception as e:
            logger.debug(f"Error checking for pass button: {e}")
            return False
    
    def _check_for_spellbook(self) -> bool:
        """Check if the spellbook is currently visible on screen (indicates fight is over)"""
        try:
            # Move mouse to top middle of screen to reset any hover effects
            screen_width, screen_height = pyautogui.size()
            top_middle_x = screen_width // 2
            top_middle_y = 50
            pyautogui.moveTo(top_middle_x, top_middle_y, duration=0.1)
            
            # Get the spellbook template path
            from config import config
            spellbook_path = config.get_game_template_path(AssetPaths.GameTemplates.SPELLBOOK)
            
            # Check for spellbook
            spellbook_element = self.ui_detector.find_element(
                ElementSearchCriteria(
                    name="spellbook",
                    element_type=ElementType.BUTTON,
                    template_path=spellbook_path,
                    confidence_threshold=0.8
                ),
                silent=True  # Silent mode to avoid log spam
            )
            
            return spellbook_element is not None
            
        except Exception as e:
            logger.debug(f"Error checking for spellbook: {e}")
            return False
    
    def _execute_battle_strategy(self, enemy_data: dict):
        """Execute the battle strategy for the detected enemy"""
        strategy = enemy_data.get("strategy", {})
        rounds = strategy.get("rounds", [])
        
        if not rounds:
            logger.warning("No battle strategy found for this enemy")
            return
        
        logger.info(f"Executing battle strategy with {len(rounds)} round(s)")
        
        # Keep looping until second enemy appears, then execute strategy
        round_counter = 0
        while True:
            round_counter += 1
            logger.info(f"Starting round {round_counter}")
            
            # Determine number of pips at the beginning of each round
            pip_count = self._determine_pip_count()
            logger.info(f"Current pip count: {pip_count}")
            
            # Check if second enemy is present at the beginning of each round
            if not self._check_for_second_enemy():
                logger.info("Second enemy not present, passing this round")
                if self._click_pass_button():
                    logger.info("Successfully passed round")
                    # Wait for the round to complete
                    result = self._wait_for_round_completion()
                    if result == "fight_completed":
                        logger.info("Fight completed during pass round - ending battle")
                        break
                    continue
                else:
                    logger.error("Failed to click pass button")
                    break
            else:
                logger.info("Second enemy detected! Executing battle strategy")
                # Execute the configured strategy rounds
                for round_num, round_data in enumerate(rounds, 1):
                    logger.info(f"Executing strategy round {round_num}")
                    
                    # Handle enchantments at the beginning of each round
                    enchantments = round_data.get("enchantments", [])
                    if enchantments:
                        logger.info(f"Processing {len(enchantments)} enchantment(s) for strategy round {round_num}")
                        self._process_enchantments(enchantments)
                    else:
                        logger.info(f"No enchantments for strategy round {round_num}")
                    
                    # Handle casting after enchantments
                    cast_data = round_data.get("cast", {})
                    if cast_data:
                        logger.info(f"Cast data for strategy round {round_num}: {cast_data}")
                        self._process_cast(cast_data)
                    else:
                        logger.info(f"No cast data for strategy round {round_num}")
                    
                    # Wait for the round to complete after casting
                    result = self._wait_for_round_completion()
                    if result == "fight_completed":
                        logger.info("Fight completed after strategy execution - ending battle")
                        return
                
                # Strategy completed, break out of the waiting loop
                break
    
    def _determine_pip_count(self) -> int:
        """Determine the number of pips the player currently has"""
        try:
            # Get the first player template path
            from config import config
            first_player_path = config.get_farming_template_path(AssetPaths.FarmingTemplates.FIRST_PLAYER)
            
            # Find the first player element on screen
            first_player_element = self.ui_detector.find_element(
                ElementSearchCriteria(
                    name="first_player",
                    element_type=ElementType.BUTTON,
                    template_path=first_player_path,
                    confidence_threshold=0.8
                ),
                silent=True  # Silent mode to avoid log spam
            )
            
            if first_player_element:
                logger.info(f"Found first player at {first_player_element.center}")
                
                # Start at the first pip position (45px right, 50px down from first player)
                pip_x = first_player_element.center.x + 45
                pip_y = first_player_element.center.y + 50
                
                # Loop through 5 pip positions
                for pip_num in range(1, 5):
                    time.sleep(3)
                    # Move mouse to current pip position
                    pyautogui.moveTo(pip_x, pip_y, duration=0.1)
                    
                    # Get the color of the current pip
                    pip_color = pyautogui.pixel(pip_x, pip_y)
                    pip_hex = f"#{pip_color[0]:02x}{pip_color[1]:02x}{pip_color[2]:02x}"
                    logger.info(f"Color of {pip_num}{self._get_ordinal_suffix(pip_num)} pip: {pip_hex}")
                    
                    # Move to next pip position (30px to the right)
                    pip_x += 28
                
                # Sleep for 5 seconds
                time.sleep(3)
                logger.info("Finished 5-second sleep")
                
                # TODO: Implement pip counting logic here
                # For now, just return 0 as requested
                return 0
            else:
                logger.info("Could not find first player on screen")
                return 0
                
        except Exception as e:
            logger.error(f"Error determining pip count: {e}")
            return 0
    
    def _get_ordinal_suffix(self, num: int) -> str:
        """Get the ordinal suffix for a number (1st, 2nd, 3rd, etc.)"""
        if 10 <= num % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(num % 10, 'th')
        return suffix
    
    def _process_enchantments(self, enchantments: list):
        """Process a list of enchantments by clicking enchant and card"""
        for i, enchantment in enumerate(enchantments, 1):
            enchant_type = enchantment.get("enchant")
            card_name = enchantment.get("card")
            
            if not enchant_type or not card_name:
                logger.warning(f"Invalid enchantment data: {enchantment}")
                continue
            
            logger.info(f"Processing enchantment {i}: {enchant_type} + {card_name}")
            
            # Click the enchantment type first
            if self._click_card(enchant_type):
                logger.info(f"Successfully clicked {enchant_type}")
                time.sleep(0.5)  # Small delay between clicks
                
                # Then click the card to enchant
                if self._click_card(card_name):
                    logger.info(f"Successfully clicked {card_name}")
                    time.sleep(0.5)  # Small delay after enchantment
                else:
                    logger.error(f"Failed to click {card_name}")
            else:
                logger.error(f"Failed to click {enchant_type}")
    
    def _process_cast(self, cast_data: dict):
        """Process casting a spell card"""
        card_name = cast_data.get("card")
        target = cast_data.get("target")
        
        if not card_name:
            logger.warning(f"Invalid cast data: {cast_data}")
            return
        
        logger.info(f"Casting {card_name} on target {target}")
        
        # Click the cast card
        if self._click_card(card_name):
            logger.info(f"Successfully clicked {card_name}")
            # TODO: Add target selection logic here when ready
            # For now, just log the target
            if target == 0:
                logger.info("Target 0: AoE attack (no additional targeting needed)")
            elif target in [1, 2, 3, 4]:
                logger.info(f"Target {target}: Would click enemy position {target}")
            else:
                logger.warning(f"Unknown target value: {target}")
        else:
            logger.error(f"Failed to click {card_name}")
    
    def _click_card(self, card_name: str) -> bool:
        """Click a card by its name using template matching"""
        try:
            # Move mouse to top middle of screen to reset card sizes before searching
            screen_width, screen_height = pyautogui.size()
            top_middle_x = screen_width // 2
            top_middle_y = 50  # Near the top of the screen
            pyautogui.moveTo(top_middle_x, top_middle_y, duration=0.1)
            
            # Get the template filename from the constant
            template_filename = getattr(AssetPaths.FarmingTemplates, card_name, None)
            if not template_filename:
                logger.error(f"Template constant {card_name} not found in AssetPaths.FarmingTemplates")
                return False
            
            # Get the template path
            from config import config
            template_path = config.get_farming_template_path(template_filename)
            
            # Find the card on screen
            card_element = self.ui_detector.find_element(
                ElementSearchCriteria(
                    name=card_name,
                    element_type=ElementType.BUTTON,
                    template_path=template_path,
                    confidence_threshold=0.8
                )
            )
            
            if card_element:
                # Move mouse to the card coordinates before clicking
                pyautogui.moveTo(card_element.center.x, card_element.center.y, duration=0.1)
                
                # Click the card
                pyautogui.click(card_element.center.x, card_element.center.y)
                logger.debug(f"Clicked {card_name} at {card_element.center}")
                return True
            else:
                logger.warning(f"Could not find {card_name} on screen")
                return False
                
        except Exception as e:
            logger.error(f"Error clicking {card_name}: {e}")
            return False
    
    def _click_pass_button(self) -> bool:
        """Click the pass button to skip a round"""
        try:
            # Move mouse to top middle of screen to reset any hover effects
            screen_width, screen_height = pyautogui.size()
            top_middle_x = screen_width // 2
            top_middle_y = 50
            pyautogui.moveTo(top_middle_x, top_middle_y, duration=0.1)
            
            # Get the pass button template path
            from config import config
            pass_path = config.get_farming_template_path(AssetPaths.FarmingTemplates.PASS)
            
            # Find the pass button on screen
            pass_element = self.ui_detector.find_element(
                ElementSearchCriteria(
                    name="pass_button",
                    element_type=ElementType.BUTTON,
                    template_path=pass_path,
                    confidence_threshold=0.8
                )
            )
            
            if pass_element:
                # Move mouse to the pass button coordinates before clicking
                pyautogui.moveTo(pass_element.center.x, pass_element.center.y, duration=0.1)
                
                # Click the pass button
                pyautogui.click(pass_element.center.x, pass_element.center.y)
                logger.debug(f"Clicked pass button at {pass_element.center}")
                return True
            else:
                logger.warning("Could not find pass button on screen")
                return False
                
        except Exception as e:
            logger.error(f"Error clicking pass button: {e}")
            return False
    
    def get_movement_automation(self) -> MovementAutomation:
        """Get the movement automation instance for external use"""
        return self.movement_automation
    
    def get_world_navigation(self) -> WorldNavigationAutomation:
        """Get the world navigation automation instance for external use"""
        return self.world_navigation
    
    def _load_farming_config(self) -> dict:
        """Load farming configuration from farming_config.yaml"""
        try:
            with open('config/farming_config.yaml', 'r', encoding='utf-8') as file:
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            logger.warning("config/farming_config.yaml not found, using default configuration")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config/farming_config.yaml: {e}")
            return {}
