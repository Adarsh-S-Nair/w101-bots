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
from src.constants import AssetPaths
from config import config
from src.automation.movement_automation import MovementAutomation
from src.utils.bot_execution_tracker import GardeningBotTracker

class GardeningAutomation(AutomationBase):
    """Handles gardening-specific automation tasks in Wizard101"""
    
    def __init__(self, ui_detector):
        super().__init__(ui_detector)
        self.movement_automation = MovementAutomation(ui_detector)
        self.garden_config = self._load_garden_config()
        self.execution_tracker = GardeningBotTracker()
    
    def execute(self) -> ActionResult:
        """Execute gardening automation workflow"""
        # Start tracking execution
        execution_data = self.execution_tracker.start_execution()
        execution_id = execution_data["execution_id"]
        actions_performed = []
        plant_data = None
        
        try:
            logger.info("Starting gardening automation")

            # First, navigate to the main garden area
            # Note: Housing navigation is already handled by the modular bot framework
            nav_result = self.navigate_to_garden()
            if not nav_result.success:
                raise RuntimeError("Failed to navigate to garden area")

            # Check if elder couch potatoes are ready
            readiness_result = self.check_couch_potatoes_ready()
            if not readiness_result.success:
                raise RuntimeError("Failed to check couch potatoes status")

            couch_potatoes_ready = bool(readiness_result.data and readiness_result.data.get('couch_potatoes_ready', False))
            if couch_potatoes_ready:
                # Harvest and replant flow
                logger.info("Couch potatoes are elder and ready! Starting harvest and replant cycle...")
                harvest_result = self.harvest_couch_potatoes()
                if not harvest_result.success:
                    raise RuntimeError("Harvest failed")
                actions_performed.append("harvest")

                logger.info("Starting replanting process...")
                replant_result = self.replant_couch_potatoes()
                if not replant_result.success:
                    raise RuntimeError("Replanting failed")
                actions_performed.append("replant")
            else:
                # Not ready: check for needs and handle them if present
                logger.info("Couch potatoes not ready. Checking for plant needs...")
                needs_result = self.check_plant_needs()
                if needs_result.success and needs_result.data and needs_result.data.get('needs_detected', False):
                    logger.info("Plant needs detected! Handling needs...")
                    handle_result = self.handle_plant_needs()
                    if handle_result.success:
                        actions_performed.append("needs_handling")
                else:
                    logger.info("No plant needs detected")

            # Update plant status only after successful navigation/workflow
            logger.info("Updating plant status at end of gardening run...")
            status_result = self.update_plant_status()
            if status_result.success and status_result.data:
                plant_data = status_result.data
                # Update plant status in tracker
                self.execution_tracker.update_plant_status(plant_data)
            else:
                logger.warning("Plant status update encountered an issue at end of run")

            logger.info("Gardening automation completed successfully")
            
            # Complete execution tracking with success
            completion_info = self.execution_tracker.complete_execution(
                execution_id=execution_id,
                success=True,
                plant_data=plant_data,
                actions_performed=actions_performed,
                execution_summary={
                    "actions_count": len(actions_performed),
                    "plant_ready": couch_potatoes_ready
                }
            )
            
            return ActionResult.success_result("Gardening automation completed successfully")
        except Exception as e:
            logger.error(f"Error in gardening automation: {e}")
            
            # Complete execution tracking with failure
            self.execution_tracker.complete_execution(
                execution_id=execution_id,
                success=False,
                plant_data=plant_data,
                actions_performed=actions_performed,
                execution_summary={
                    "error": str(e),
                    "actions_count": len(actions_performed)
                }
            )
            
            return ActionResult.failure_result("Gardening automation failed", error=e)
    
    def navigate_to_garden(self) -> ActionResult:
        """Navigate to the main garden area"""
        try:
            logger.info("Navigating to garden area...")
            
            # Wait 1.5 seconds after housing navigation (handled by modular bot)
            logger.info("Waiting 1.5 seconds after housing navigation...")
            time.sleep(1.5)
            
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
    
    def is_time_to_run(self) -> bool:
        """Check if it's time to run the gardening bot based on the schedule"""
        return self.execution_tracker.is_time_to_run()
    
    def get_next_run_time(self):
        """Get the next scheduled run time for the gardening bot"""
        return self.execution_tracker.get_next_run_time()
    
    def get_execution_stats(self):
        """Get gardening bot execution statistics"""
        return self.execution_tracker.get_gardening_stats()
    
    def get_execution_history(self, limit: int = 10):
        """Get recent gardening bot execution history"""
        return self.execution_tracker.get_execution_history(limit)
    
    def get_plant_status_history(self, limit: int = 10):
        """Get recent plant status history"""
        return self.execution_tracker.get_plant_status_history(limit)
    
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
    
    def check_plant_needs(self) -> ActionResult:
        """Check if plants have needs that require attention"""
        try:
            logger.info("Checking if plants have needs...")
            
            # Define search criteria for plants have needs indicator
            needs_criteria = ElementSearchCriteria(
                name="plants_have_needs",
                element_type=ElementType.IMAGE,
                template_path=config.get_gardening_template_path(AssetPaths.GardeningTemplates.PLANTS_HAVE_NEEDS),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Plants have needs indicator"}
            )
            
            # Check if plants have needs image is present
            if self.ui_detector.is_element_present(needs_criteria):
                logger.info("Plants have needs detected!")
                return ActionResult.success_result("Plants have needs detected", data={'needs_detected': True})
            else:
                logger.info("No plant needs detected")
                return ActionResult.success_result("No plant needs detected", data={'needs_detected': False})
                
        except Exception as e:
            logger.error(f"Failed to check plant needs: {e}")
            return ActionResult.failure_result("Failed to check plant needs", error=e)
    
    def handle_plant_needs(self) -> ActionResult:
        """Handle plant needs based on configured plot plant type and plant database steps.
        This opens the gardening menu, selects the category, then selects the spell, and returns without casting.
        """
        try:
            # Determine plant type from garden config
            plot_plant_type = (self.garden_config or {}).get('plot_plant_type')
            if not plot_plant_type:
                logger.warning("plot_plant_type not set in config/garden_config.yaml")
                return ActionResult.failure_result("plot_plant_type not set in config/garden_config.yaml")

            # Use the lowercase key directly (must match plant_database keys)
            plant_key = str(plot_plant_type).strip()

            # Load plant database
            with open('config/plant_database.yaml', 'r', encoding='utf-8') as file:
                plant_db = yaml.safe_load(file) or {}
            plant_data = (plant_db.get('plants') or {}).get(plant_key)
            if not plant_data:
                logger.warning(f"Plant '{plant_key}' not found in config/plant_database.yaml")
                return ActionResult.failure_result(f"Plant '{plant_key}' not found in config/plant_database.yaml")

            needs = ((plant_data.get('needs_handling') or {}).get('steps')) or []
            if not needs:
                logger.info("No needs_handling steps configured for this plant")
                return ActionResult.success_result("No needs to handle")

            # Execute each needs step in sequence
            for index, step in enumerate(needs):
                is_last_step = index == (len(needs) - 1)

                # Open the gardening menu at the beginning of each step
                open_result = self._toggle_gardening_menu()
                if not open_result.success:
                    return open_result

                category_const = step.get('category')
                spell_const = step.get('spell')
                if not category_const or not spell_const:
                    return ActionResult.failure_result("Invalid needs_handling step; missing category or spell")

                # Resolve constants to template filenames in AssetPaths.GardeningTemplates
                category_filename = getattr(AssetPaths.GardeningTemplates, category_const, None)
                spell_filename = getattr(AssetPaths.GardeningTemplates, spell_const, None)
                if not category_filename or not spell_filename:
                    return ActionResult.failure_result("Category or spell constant not found in AssetPaths.GardeningTemplates")

                # Find and click the category
                select_category_result = self._select_gardening_category(category_const, category_filename)
                if not select_category_result.success:
                    return select_category_result

                # Reset mouse after category click to avoid tooltip
                self._reset_mouse_after_category_click()

                # Find and click the spell with pagination
                select_spell_result = self._select_spell_with_pagination(spell_const, spell_filename)
                if not select_spell_result.success:
                    return select_spell_result

                # Move mouse to configured coordinates and wait (for testing)
                self._position_mouse_for_spell_casting()

                # Close the gardening menu after each step (except the last one)
                if not is_last_step:
                    logger.info("Step completed. Closing gardening menu...")
                    close_result = self._toggle_gardening_menu()
                    if not close_result.success:
                        logger.warning("Failed to close gardening menu, but continuing...")
                    
                    logger.info("Navigating back to the front of the house and then back to garden before next step...")
                    nav_result = self._navigate_house_front_and_back_to_garden()
                    if not nav_result.success:
                        return nav_result

            logger.info("All needs steps processed. Stopping here (not casting yet).")
            return ActionResult.success_result("All needs steps processed")

        except Exception as e:
            logger.error(f"Failed to handle plant needs: {e}")
            return ActionResult.failure_result("Failed to handle plant needs", error=e)

    def _toggle_gardening_menu(self) -> ActionResult:
        """Toggle the gardening menu by pressing 'g' and waiting briefly."""
        try:
            logger.info("Toggling gardening menu...")
            pyautogui.press('g')
            time.sleep(1.0)
            return ActionResult.success_result("Gardening menu toggled")
        except Exception as e:
            logger.error(f"Failed to toggle gardening menu: {e}")
            return ActionResult.failure_result("Failed to toggle gardening menu", error=e)

    def _select_gardening_category(self, category_const: str, category_filename: str) -> ActionResult:
        """Find and click a gardening category by constant/filename."""
        try:
            logger.info(f"Selecting category '{category_const}'...")
            category_criteria = ElementSearchCriteria(
                name=f"{category_const.lower()}",
                element_type=ElementType.IMAGE,
                template_path=config.get_gardening_template_path(category_filename),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": f"Category {category_const}"}
            )
            category_element = self.ui_detector.find_element(category_criteria)
            if not category_element:
                return ActionResult.failure_result(f"Category '{category_const}' not found on screen")
            click_result = self.click_element(category_element)
            if not click_result.success:
                return ActionResult.failure_result(f"Failed to click category '{category_const}'")
            time.sleep(1.0)
            return ActionResult.success_result("Category selected")
        except Exception as e:
            logger.error(f"Failed to select gardening category: {e}")
            return ActionResult.failure_result("Failed to select gardening category", error=e)

    def _reset_mouse_after_category_click(self):
        """Move mouse up to avoid tooltip/context bubble obstructing spells."""
        try:
            current_x, current_y = pyautogui.position()
            target_y = max(0, current_y - 100)
            logger.info(f"Resetting mouse to avoid tooltip: moving from ({current_x}, {current_y}) to ({current_x}, {target_y})")
            pyautogui.moveTo(current_x, target_y)
            time.sleep(0.3)
        except Exception as move_err:
            logger.warning(f"Failed to reposition mouse after category click: {move_err}")

    def _select_spell_with_pagination(self, spell_const: str, spell_filename: str) -> ActionResult:
        """Find and click the spell. If not present, paginate right until found or no more pages."""
        try:
            logger.info(f"Selecting spell '{spell_const}' with pagination if needed...")
            arrow_criteria = ElementSearchCriteria(
                name="gardening_menu_right_arrow",
                element_type=ElementType.IMAGE,
                template_path=config.get_gardening_template_path(AssetPaths.GardeningTemplates.GARDENING_MENU_RIGHT_ARROW),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": "Gardening menu right arrow for pagination"}
            )

            while True:
                spell_criteria = ElementSearchCriteria(
                    name=f"{spell_const.lower()}",
                    element_type=ElementType.IMAGE,
                    template_path=config.get_gardening_template_path(spell_filename),
                    confidence_threshold=0.8,
                    detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                    metadata={"description": f"Spell {spell_const}"}
                )
                spell_element = self.ui_detector.find_element(spell_criteria)
                if spell_element:
                    click_result = self.click_element(spell_element)
                    if not click_result.success:
                        return ActionResult.failure_result(f"Failed to click spell '{spell_const}'")
                    return ActionResult.success_result("Spell selected")

                # Not found; check if there's a next page
                right_arrow = self.ui_detector.find_element(arrow_criteria)
                if not right_arrow:
                    return ActionResult.failure_result(f"Spell '{spell_const}' not found and no more pages available")

                # Click the right arrow to go to the next page
                logger.info("Spell not found on this page. Clicking right arrow to paginate...")
                arrow_click = self.click_element(right_arrow)
                if not arrow_click.success:
                    return ActionResult.failure_result("Failed to click gardening menu right arrow")
                time.sleep(0.5)
        except Exception as e:
            logger.error(f"Failed during spell selection: {e}")
            return ActionResult.failure_result("Failed during spell selection", error=e)

    def _position_mouse_for_spell_casting(self):
        """Move mouse to configured coordinates, click to cast, then wait for post-cast lag."""
        try:
            spell_config = self.garden_config.get('spell_casting', {})
            target_x = spell_config.get('target_x', 960)  # Default to center
            target_y = spell_config.get('target_y', 540)  # Default to center
            wait_time = spell_config.get('wait_after_positioning', 60)
            wait_after_cast = spell_config.get('wait_after_casting', 50)
            
            logger.info(f"Moving mouse naturally to spell casting position at ({target_x}, {target_y}) and waiting {wait_time} seconds before casting...")
            # Move mouse naturally over 1 second instead of teleporting
            pyautogui.moveTo(target_x, target_y, duration=5.0)
            time.sleep(wait_time)
            
            # Click to cast the spell
            logger.info("Casting spell with left click...")
            pyautogui.click(button='left')
            
            # Wait after casting to allow for game lag/animation
            logger.info(f"Waiting {wait_after_cast} seconds after casting to allow for animations/lag...")
            time.sleep(wait_after_cast)
            logger.info("Finished post-cast wait")
        except Exception as e:
            logger.warning(f"Failed to position mouse for spell casting: {e}")

    def _load_garden_config(self) -> dict:
        """Load garden configuration from garden_config.yaml"""
        try:
            with open('config/garden_config.yaml', 'r', encoding='utf-8') as file:
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            logger.warning("config/garden_config.yaml not found, using default configuration")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config/garden_config.yaml: {e}")
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
            
            # Wait 1.5 seconds after navigating to house start
            logger.info("Waiting 1.5 seconds after house navigation...")
            time.sleep(1.5)
            
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
            
            # Step 1: Plant the first seed
            logger.info("Step 1: Planting first seed...")
            first_seed_result = self.plant_first_seed()
            if not first_seed_result.success:
                return first_seed_result
            
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
            
            # Extract plant status using template matching (no OCR needed)
            logger.info("Starting plant status extraction with template matching...")
            plant_status = self._extract_plant_status_with_template_matching()
            if plant_status:
                self._log_plant_status(plant_status)
                logger.info("Successfully extracted plant status using template matching")
                return ActionResult.success_result("Successfully extracted plant status using template matching", data=plant_status)
            else:
                logger.warning("Failed to extract plant status using template matching")
            
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
    
    def _extract_plant_status_with_template_matching(self) -> dict:
        """Extract plant status using template matching (no OCR needed)"""
        try:
            import yaml
            
            # Load plant database
            with open('config/plant_database.yaml', 'r', encoding='utf-8') as file:
                plant_db = yaml.safe_load(file)
            
            # For now, assume couch potatoes (can be made configurable later)
            plant_name = 'couch_potatoes'
            
            # Get plant data from database
            plant_data = plant_db['plants'].get(plant_name)
            if not plant_data:
                logger.warning(f"Plant '{plant_name}' not found in database")
                return None
            
            # Extract likes using template matching
            likes = self._extract_likes_with_template_matching(plant_name)
            
            # Calculate growth modifiers
            modifiers = self._calculate_growth_modifiers(likes, plant_data['growth_modifiers'])
            
            # For now, assume mature stage (can be enhanced with stage detection later)
            current_stage = 'mature'
            
            # Determine next stage and time to next stage
            next_stage, time_to_next = self._calculate_next_stage(current_stage, plant_data['stages'], modifiers)
            
            # Calculate effective growth speed (multiplicative)
            # Each modifier reduces time by its percentage
            effective_speed_percent = 100
            for percent in modifiers.values():
                effective_speed_percent *= (1 - percent / 100)
            effective_speed_percent = 100 - (effective_speed_percent * 100)
            
            return {
                'plant_name': plant_data['name'],
                'current_stage': current_stage,
                'next_stage': next_stage,
                'time_to_next_hours': time_to_next,
                'modifiers': modifiers,
                'effective_speed_percent': effective_speed_percent
            }
            
        except Exception as e:
            logger.error(f"Failed to extract plant status with template matching: {e}")
            return None
    
    def _extract_likes_with_template_matching(self, plant_key: str) -> list:
        """Extract likes using template matching instead of OCR"""
        try:
            # Load plant database to get modifiers for this plant
            with open('config/plant_database.yaml', 'r', encoding='utf-8') as file:
                plant_db = yaml.safe_load(file)
            
            plant_data = plant_db['plants'].get(plant_key)
            if not plant_data:
                logger.warning(f"Plant '{plant_key}' not found in database")
                return []
            
            growth_modifiers = plant_data.get('growth_modifiers', {})
            detected_likes = []
            checked_templates = set()  # Track which templates we've already checked
            
            logger.info("=" * 60)
            logger.info("CHECKING FOR PLANT LIKES WITH TEMPLATE MATCHING")
            logger.info("=" * 60)
            
            # Check each modifier category and look for corresponding templates
            house_modifier_found = False
            for modifier_percent, items in growth_modifiers.items():
                logger.info(f"Checking {modifier_percent} modifiers:")
                for item in items:
                    logger.info(f"  Checking for: {item}")
                    
                    # Skip house modifiers if we've already found one
                    house_modifiers = ["Botanical Gardens", "Country Cottage", "Everafter Village", "Outback Ranch", "Red Barn Farm"]
                    if house_modifier_found and item in house_modifiers:
                        logger.info(f"  [SKIP] House modifier already found, skipping {item}")
                        continue
                    
                    # Get the template filename for this item
                    template_filename = self._get_template_filename(item)
                    if not template_filename:
                        logger.info(f"  [SKIP] No template for {item}")
                        continue
                    
                    # Skip if we've already checked this template
                    if template_filename in checked_templates:
                        logger.info(f"  [SKIP] Already checked template {template_filename} for {item}")
                        continue
                    
                    # Check if we should look for this item using template matching
                    template_found = self._check_like_template(item)
                    checked_templates.add(template_filename)
                    
                    if template_found:
                        detected_likes.append(item)
                        logger.info(f"  [FOUND] {item} ({modifier_percent})")
                        
                        # Special handling: if we found a house-related modifier, mark it
                        if item in house_modifiers:
                            house_modifier_found = True
                            logger.info(f"  -> Found house modifier '{item}', will skip other house modifiers")
                    else:
                        logger.info(f"  [NOT FOUND] {item}")
                
            
            logger.info("=" * 60)
            logger.info(f"TEMPLATE MATCHING COMPLETE - Found {len(detected_likes)} likes:")
            for like in detected_likes:
                logger.info(f"  - {like}")
            logger.info("=" * 60)
            
            return detected_likes
            
        except Exception as e:
            logger.error(f"Failed to extract likes with template matching: {e}")
            return []
    
    def _get_template_filename(self, item: str) -> str:
        """Get the template filename for a given item"""
        template_mapping = {
            "King Parsley": AssetPaths.GardeningTemplates.LIKES_KING_PARSLEY,
            "Litter": AssetPaths.GardeningTemplates.LIKES_LITTER,
            "Pixie": AssetPaths.GardeningTemplates.LIKES_PIXIE,
            "Sandwich Station": AssetPaths.GardeningTemplates.LIKES_SANDWICH_STATION,
            "Botanical Gardens": AssetPaths.GardeningTemplates.LIKES_THIS_HOUSE,
            "Country Cottage": AssetPaths.GardeningTemplates.LIKES_THIS_HOUSE,
            "Everafter Village": AssetPaths.GardeningTemplates.LIKES_THIS_HOUSE,
            "Outback Ranch": AssetPaths.GardeningTemplates.LIKES_THIS_HOUSE,
            "Red Barn Farm": AssetPaths.GardeningTemplates.LIKES_THIS_HOUSE,
            "Tropical Garden Gnome": AssetPaths.GardeningTemplates.LIKES_GARDEN_GNOMES,
            "Stinkweed": None  # Negative modifier - no template needed
        }
        return template_mapping.get(item)
    
    def _check_like_template(self, item: str) -> bool:
        """Check if a like template is present on screen for the given item"""
        try:
            template_filename = self._get_template_filename(item)
            if not template_filename:
                logger.debug(f"    No template mapping found for item: {item}")
                return False
            
            logger.debug(f"    Using template: {template_filename}")
            
            # Define search criteria for the like template
            like_criteria = ElementSearchCriteria(
                name=f"likes_{item.lower().replace(' ', '_')}",
                element_type=ElementType.IMAGE,
                template_path=config.get_gardening_template_path(template_filename),
                confidence_threshold=0.8,
                detection_methods=[DetectionMethod.TEMPLATE, DetectionMethod.VISUAL],
                metadata={"description": f"Like template for {item}"}
            )
            
            # Check if the template is present
            is_present = self.ui_detector.is_element_present(like_criteria)
            if is_present:
                logger.debug(f"    Template match found for: {item}")
            else:
                logger.debug(f"    Template match not found for: {item}")
            
            return is_present
            
        except Exception as e:
            logger.error(f"Failed to check like template for '{item}': {e}")
            return False
    
    def _calculate_growth_modifiers(self, likes: list, plant_modifiers: dict) -> dict:
        """Calculate growth modifiers based on likes (now using exact template matches)"""
        modifiers = {}
        
        for like in likes:
            for modifier_percent, items in plant_modifiers.items():
                if like in items:
                    # Convert percentage string to float
                    percent = float(modifier_percent.replace('%', '').replace('+', ''))
                    modifiers[like] = percent
                    break
        
        return modifiers
    
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
            
            # Apply modifiers multiplicatively (positive modifiers make growth faster = less time)
            # Each modifier reduces time by its percentage
            modified_time = base_time
            for item, percent in modifiers.items():
                # Apply each modifier: reduce time by the percentage
                modified_time = modified_time * (1 - percent / 100)
            
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
        logger.info(f"Time to Next Stage: {status['time_to_next_hours']:.4f} hours")
        logger.info("")
        logger.info("GROWTH MODIFIERS:")
        if status['modifiers']:
            for item, percent in status['modifiers'].items():
                sign = "+" if percent > 0 else ""
                logger.info(f"  {item}: {sign}{percent:.0f}%")
        else:
            logger.info("  No growth modifiers found")
        logger.info(f"")
        logger.info(f"EFFECTIVE GROWTH SPEED: {status['effective_speed_percent']:.2f}% of base time (multiplicative)")
        logger.info(f"TIME REDUCTION: {100 - status['effective_speed_percent']:.2f}%")
        logger.info("=" * 50)
    
    
