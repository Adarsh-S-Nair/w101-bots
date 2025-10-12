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
        self.spells_database = self._load_spells_database()
        self.movement_automation = MovementAutomation(ui_detector, config=self.farming_config)
        
        # Get target world from farming config if not provided
        if target_world is None:
            target_world = self.farming_config.get("world_navigation", {}).get("target_world", "grizzleheim")
        
        self.world_navigation = WorldNavigationAutomation(ui_detector, target_world=target_world, farming_config=self.farming_config)
        
        # Fizzle detection tracking
        self.previous_pip_count = 0
        self.last_casted_round = None
        
        # Current pip count tracking
        self.current_pip_count = 0
    
    def execute(self) -> ActionResult:
        """Execute farming automation workflow in continuous loop"""
        try:
            logger.info("Starting continuous farming automation")
            battle_count = 0
            
            while True:
                battle_count += 1
                logger.info(f"=== BATTLE #{battle_count} ===")
                logger.info("Spinning in circle until enemy detected...")

                # Reset fizzle tracking for new battle
                self.previous_pip_count = 0
                self.last_casted_round = None

                # Spin in a circle until we detect the first enemy
                self._spin_until_enemy_detected()
                
                # After stopping spin, determine what type of enemy we're facing
                enemy_data = self._detect_enemy_type()
                if enemy_data:
                    enemy_name = enemy_data.get("name", "Unknown Enemy")
                    logger.info(f"Detected enemy: {enemy_name}")
                    
                    # Execute battle strategy
                    self._execute_battle_strategy(enemy_data)
                    logger.info(f"Battle #{battle_count} completed successfully")
                else:
                    logger.warning("Could not determine enemy type, continuing to next battle...")
                
                # Small delay before starting next battle
                logger.info("Preparing for next battle...")
            
        except KeyboardInterrupt:
            logger.info("Farming automation stopped by user")
            return ActionResult.success_result("Farming automation stopped by user")
        except Exception as e:
            logger.error(f"Farming automation failed: {e}")
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
                time.sleep(0.1)  # Check every 0.5 seconds
            
            logger.info("Casting phase started")
            
            # Then, wait for either pass button to reappear OR spellbook to appear (fight over)
            logger.info("Waiting for casting phase to complete...")
            while not self._check_for_pass_button() and not self._check_for_spellbook():
                time.sleep(0.1)  # Check every 0.5 seconds
            
            if self._check_for_spellbook():
                logger.info("Fight completed!")
                return "fight_completed"
            else:
                logger.info("Round completed, back to card selection")
                return "round_completed"
            
        except Exception as e:
            logger.error(f"Error waiting for round completion: {e}")
            return "error"
    
    def _check_for_pass_button(self) -> bool:
        """Check if the pass button is currently visible on screen"""
        try:
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
        
        # Validate that all spells in the strategy exist in the spells database
        if not self.validate_strategy_spells(strategy):
            logger.error("Strategy contains unknown spells, cannot execute battle")
            return
        
        # Calculate and log strategy pip cost
        total_pip_cost = self.calculate_strategy_pip_cost(strategy)
        logger.info(f"Strategy total pip cost: {total_pip_cost}")
        
        # Track which strategy rounds we've successfully executed
        executed_strategy_rounds = 0
        battle_round_counter = 0
        second_enemy_detected = False
        
        # Main battle loop - continues until battle is complete
        while True:
            battle_round_counter += 1
            logger.info(f"Starting battle round {battle_round_counter}")
            
            # Check for second enemy only until first detection
            if not second_enemy_detected:
                logger.info("Checking for second enemy...")
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
                    logger.info("Second enemy detected! Will execute strategy from now on")
                    second_enemy_detected = True
            
            # Determine number of pips at the beginning of each round
            self.current_pip_count = self._determine_pip_count()
            logger.info(f"Current pip count: {self.current_pip_count}")
            
            # Check for fizzle if we casted a spell in the previous round
            if self.last_casted_round is not None and self.current_pip_count > self.previous_pip_count:
                logger.warning(f"FIZZLED!")
                logger.info("Retrying the most recent strategy round...")
                fight_completed = self._retry_last_strategy_round(rounds)
                
                # If fight was completed during fizzle retry, end the battle
                if fight_completed:
                    logger.info("Battle ended during fizzle retry")
                    break
                
                # Reset fizzle tracking and continue to next round
                self.last_casted_round = None
                self.previous_pip_count = self.current_pip_count
                continue
            
            # Update pip tracking
            self.previous_pip_count = self.current_pip_count
            
            # Execute strategy round (second enemy was already detected)
            logger.info("Executing strategy round")
            
            # Try to execute a strategy round
            success = self._execute_strategy_round(rounds, executed_strategy_rounds)
            
            if success:
                executed_strategy_rounds += 1
                logger.info(f"Successfully executed strategy round {executed_strategy_rounds}")
                
                # Wait for the round to complete
                result = self._wait_for_round_completion()
                if result == "fight_completed":
                    logger.info("Fight completed after strategy execution - ending battle")
                    break
                elif result == "round_completed":
                    logger.info("Round completed, continuing to next round")
                    continue
                else:
                    logger.error(f"Unexpected round completion result: {result}")
                    break
            else:
                logger.warning("Failed to execute strategy round (likely insufficient pips)")
                logger.info("Passing this round and continuing to next round")
                
                # Try to pass the round
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
    
    def _execute_strategy_round(self, rounds: list, executed_rounds: int) -> bool:
        """Execute a strategy round based on how many have been successfully executed"""
        try:
            # If we've executed all configured rounds, retry the last one
            if executed_rounds >= len(rounds):
                logger.info(f"All {len(rounds)} strategy rounds executed, retrying the last one")
                round_data = rounds[-1]  # Last round
                round_num = len(rounds)
            else:
                # Execute the next round in sequence
                round_data = rounds[executed_rounds]
                round_num = executed_rounds + 1
            
            logger.info(f"Executing strategy round {round_num}")
            
            # Track this as the last casted round for fizzle detection
            self.last_casted_round = round_data
            
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
                cast_success = self._process_cast(cast_data)
                if not cast_success:
                    logger.warning(f"Failed to cast spell in strategy round {round_num}")
                    return False
            else:
                logger.info(f"No cast data for strategy round {round_num}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing strategy round: {e}")
            return False
    
    def _retry_last_strategy_round(self, rounds: list) -> bool:
        """Retry the most recent strategy round when a fizzle is detected"""
        if not self.last_casted_round:
            logger.warning("No last casted round to retry")
            return False
        
        logger.info("Retrying the most recent strategy round due to fizzle...")
        logger.info("Note: Only retrying the cast, enchantments were already applied")
        
        # Only retry the casting part - enchantments were already successfully applied
        cast_data = self.last_casted_round.get("cast", {})
        if cast_data:
            logger.info(f"Re-casting for fizzle retry: {cast_data}")
            self._process_cast(cast_data)
        else:
            logger.warning("No cast data found in last strategy round")
        
        # Wait for the round to complete after retry casting
        result = self._wait_for_round_completion()
        if result == "fight_completed":
            logger.info("Fight completed after fizzle retry - ending battle")
            return True  # Fight completed
        else:
            logger.warning(f"Battle still active after fizzle retry (result: {result})")
            return False  # Battle continues
    
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
                pip_x = first_player_element.center.x + 60
                pip_y = first_player_element.center.y + 45
                
                total_pips = 0
                pip_num = 1
                
                # Keep checking pips until we find one that's not 'e' or 'f'
                while True:
                    # Move mouse to current pip position
                    pyautogui.moveTo(pip_x, pip_y, duration=0.1)
                    
                    # Get the color of the current pip
                    pip_color = pyautogui.pixel(pip_x, pip_y)
                    pip_hex = f"#{pip_color[0]:02x}{pip_color[1]:02x}{pip_color[2]:02x}"
                    
                    # Analyze the color to determine pip type
                    pip_type = self._analyze_pip_color(pip_color)
                    
                    
                    
                    # Check if this is a valid pip
                    if pip_type == "regular":
                        # Regular pip - counts as 1
                        total_pips += 1
                        # logger.info(f"Regular pip detected - total pips now: {total_pips}")
                    elif pip_type == "power":
                        # Power pip - counts as 2
                        total_pips += 2
                        # logger.info(f"Power pip detected - total pips now: {total_pips}")
                    else:
                        # Not a pip - stop counting
                        # logger.info(f"Non-pip color detected ({pip_type}) - stopping pip count at {total_pips}")
                        break
                    # logger.info(f"Color of {pip_num}{self._get_ordinal_suffix(pip_num)} pip: {pip_hex} (RGB: {pip_color}) - Type: {pip_type} - Pip count: {total_pips}")
                    # Move to next pip position (30px to the right)
                    pip_x += 30
                    pip_num += 1

                return total_pips
            else:
                logger.info("Could not find first player on screen")
                return 0
                
        except Exception as e:
            logger.error(f"Error determining pip count: {e}")
            return 0
    
    def _analyze_pip_color(self, rgb_color) -> str:
        """
        Analyze RGB color to determine if it's a regular pip, power pip, or not a pip.
        
        Regular pips: Mostly white with hint of yellow (high R, high G, medium B)
        Power pips: Bright yellow (high R, medium-high G, low B)
        Non-pips: Colors that don't match either pattern
        """
        r, g, b = rgb_color
        
        # Calculate color characteristics
        total_brightness = r + g + b
        
        # Basic brightness check - must be reasonably bright
        if total_brightness < 500:  # Too dark to be a pip
            return "non_pip"
        
        # Check if it's bright enough in red and green (pips are always bright in these)
        if r < 200 or g < 150:  # Too dark in red or green
            return "non_pip"
        
        # Analyze based on blue component and overall characteristics
        # Regular pips: high blue (more white/light)
        # Power pips: low blue (more yellow)
        
        if b >= 120:  # High blue - regular pip (white with hint of yellow)
            # Additional check: regular pips should be very bright overall
            if total_brightness >= 600 and r >= 220 and g >= 200:
                return "regular"
            else:
                return "non_pip"  # Too dark overall despite high blue
        elif b >= 80:  # Medium blue - need to check if it's bright enough for power pip
            # For medium blue, check if it's bright enough to be a power pip
            if r >= 220 and g >= 180:
                return "power"
            else:
                return "regular"
        elif b >= 50:  # Low blue - power pip (bright yellow)
            return "power"
        else:  # Very low blue - check if still bright enough
            if r >= 200 and g >= 150:
                return "power"
            else:
                return "non_pip"
    
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
                
                # Then click the card to enchant
                if self._click_card(card_name):
                    logger.info(f"Successfully clicked {card_name}")
                else:
                    logger.error(f"Failed to click {card_name}")
            else:
                logger.error(f"Failed to click {enchant_type}")
    
    def _process_cast(self, cast_data: dict) -> bool:
        """Process casting a spell card"""
        card_name = cast_data.get("card")
        target = cast_data.get("target")
        
        if not card_name:
            logger.warning(f"Invalid cast data: {cast_data}")
            return False
        
        logger.info(f"Casting {card_name} on target {target}")
        
        # Check if we have enough pips for this spell
        required_pips = self.get_spell_info(card_name).get("pip_cost", 0)
        
        if self.current_pip_count < required_pips:
            logger.warning(f"Not enough pips to cast {card_name}! Need {required_pips}, have {self.current_pip_count}")
            logger.info("Cannot cast due to insufficient pips")
            return False
        
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
            return True
        else:
            logger.error(f"Failed to click {card_name}")
            return False
    
    def _click_card(self, card_name: str) -> bool:
        """Click a card by its name using template matching with timeout (like trivia/gardening bots)"""
        try:
            # Move mouse to top middle of screen to reset card sizes before searching
            logger.debug(f"MOVING MOUSE TO TOP MIDDLE - About to search for card: {card_name}")
            self._move_mouse_to_top_middle()

            # Small delay to ensure UI has settled
            time.sleep(0.2)
            
            # Get the template filename from the constant
            template_filename = getattr(AssetPaths.FarmingTemplates, card_name, None)
            if not template_filename:
                logger.error(f"Template constant {card_name} not found in AssetPaths.FarmingTemplates")
                return False
            
            # Get the template path
            from config import config
            template_path = config.get_farming_template_path(template_filename)
            
            # Create search criteria
            card_criteria = ElementSearchCriteria(
                name=card_name,
                element_type=ElementType.BUTTON,
                template_path=template_path,
                confidence_threshold=0.8
            )
            
            # Wait for the card to appear with timeout (like trivia/gardening bots)
            logger.info(f"Waiting for card '{card_name}' to appear...")
            wait_result = self.wait_for_element(card_criteria, timeout=10.0, check_interval=0.1)
            
            if wait_result.success:
                card_element = wait_result.data["element"]
                logger.info(f"Found {card_name} at {card_element.center} after {wait_result.data['wait_time']:.1f}s")
                
                # Use the reliable click_element method from base class (it will move mouse to element and click)
                click_result = self.click_element(card_element)
                if click_result.success:
                    logger.info(f"Successfully clicked {card_name} at {card_element.center}")
                    
                    # Move mouse to top middle after clicking card
                    self._move_mouse_to_top_middle()                    
                    return True
                else:
                    logger.error(f"Failed to click {card_name}: {click_result.message}")
                    return False
            else:
                logger.warning(f"Could not find {card_name} within timeout period")
                return False
                
        except Exception as e:
            logger.error(f"Error clicking {card_name}: {e}")
            return False
    
    def _move_mouse_to_top_middle(self):
        """Move mouse to top middle of screen to reset hover effects"""
        screen_width, screen_height = pyautogui.size()
        top_middle_x = screen_width // 2
        top_middle_y = 50  # Near the top of the screen
        pyautogui.moveTo(top_middle_x, top_middle_y, duration=0.1)
    
    def _click_pass_button(self) -> bool:
        """Click the pass button to skip a round (with timeout like trivia/gardening bots)"""
        try:
            # Get the pass button template path
            from config import config
            pass_path = config.get_farming_template_path(AssetPaths.FarmingTemplates.PASS)
            
            # Create search criteria
            pass_criteria = ElementSearchCriteria(
                name="pass_button",
                element_type=ElementType.BUTTON,
                template_path=pass_path,
                confidence_threshold=0.8
            )
            
            # Wait for the pass button to appear with timeout
            logger.info("Waiting for pass button to appear...")
            wait_result = self.wait_for_element(pass_criteria, timeout=5.0, check_interval=0.5)
            
            if wait_result.success:
                pass_element = wait_result.data["element"]
                logger.info(f"Found pass button at {pass_element.center} after {wait_result.data['wait_time']:.1f}s")
                
                # Use the reliable click_element method from base class
                click_result = self.click_element(pass_element)
                if click_result.success:
                    logger.info(f"Successfully clicked pass button at {pass_element.center}")
                    
                    # Move mouse to top middle after clicking pass button
                    self._move_mouse_to_top_middle()
                    
                    return True
                else:
                    logger.error(f"Failed to click pass button: {click_result.message}")
                    return False
            else:
                logger.warning("Could not find pass button within timeout period")
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
    
    def _load_spells_database(self) -> dict:
        """Load spells database from spells_database.yaml"""
        try:
            with open('config/spells_database.yaml', 'r', encoding='utf-8') as file:
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            logger.warning("config/spells_database.yaml not found, using empty database")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config/spells_database.yaml: {e}")
            return {}
    
    def get_spell_info(self, spell_name: str) -> dict:
        """Get spell information from the spells database"""
        spells = self.spells_database.get("spells", {})
        return spells.get(spell_name, {})
    
    def get_template_constant(self, spell_name: str) -> str:
        """Get the template constant for a spell (same as spell name)"""
        return spell_name
    
    def validate_strategy_spells(self, strategy: dict) -> bool:
        """Validate that all spells in a strategy exist in the spells database"""
        rounds = strategy.get("rounds", [])
        
        for round_data in rounds:
            # Check enchantments
            enchantments = round_data.get("enchantments", [])
            for enchantment in enchantments:
                enchant_spell = enchantment.get("enchant")
                card_spell = enchantment.get("card")
                
                if enchant_spell and not self.get_spell_info(enchant_spell):
                    logger.warning(f"Unknown enchantment spell: {enchant_spell}")
                    return False
                    
                if card_spell and not self.get_spell_info(card_spell):
                    logger.warning(f"Unknown card spell: {card_spell}")
                    return False
            
            # Check cast spell
            cast_data = round_data.get("cast", {})
            cast_spell = cast_data.get("card")
            if cast_spell and not self.get_spell_info(cast_spell):
                logger.warning(f"Unknown cast spell: {cast_spell}")
                return False
        
        return True
    
    def calculate_strategy_pip_cost(self, strategy: dict) -> int:
        """Calculate the total pip cost for a strategy"""
        rounds = strategy.get("rounds", [])
        total_cost = 0
        
        for round_data in rounds:
            round_cost = 0
            
            # Calculate enchantment costs
            enchantments = round_data.get("enchantments", [])
            for enchantment in enchantments:
                enchant_spell = enchantment.get("enchant")
                card_spell = enchantment.get("card")
                
                if enchant_spell:
                    enchant_info = self.get_spell_info(enchant_spell)
                    round_cost += enchant_info.get("pip_cost", 0)
                    
                if card_spell:
                    card_info = self.get_spell_info(card_spell)
                    round_cost += card_info.get("pip_cost", 0)
            
            # Calculate cast cost
            cast_data = round_data.get("cast", {})
            cast_spell = cast_data.get("card")
            if cast_spell:
                cast_info = self.get_spell_info(cast_spell)
                round_cost += cast_info.get("pip_cost", 0)
            
            total_cost += round_cost
        
        return total_cost
