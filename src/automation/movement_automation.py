"""
Movement automation module
Handles player movement and navigation based on garden configuration
"""
import time
import yaml
import pyautogui
from pathlib import Path
from typing import Dict, List, Any, Optional
from src.core.automation_base import AutomationBase
from src.core.action_result import ActionResult
from src.core.element import ElementSearchCriteria, ElementType, DetectionMethod
from src.utils.logger import logger
from src.constants import AssetPaths
from config import config

class MovementAutomation(AutomationBase):
    """Handles player movement and navigation based on garden configuration"""
    
    def __init__(self, ui_detector, config=None):
        super().__init__(ui_detector)
        self.garden_config = None
        if config:
            self.garden_config = config
        else:
            self.load_garden_config()
    
    def load_garden_config(self) -> bool:
        """Load garden configuration from YAML file"""
        try:
            config_path = Path("config/garden_config.yaml")
            if not config_path.exists():
                logger.error("Garden configuration file not found: config/garden_config.yaml")
                return False
            
            with open(config_path, 'r') as file:
                self.garden_config = yaml.safe_load(file)
            
            logger.info("Garden configuration loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load garden configuration: {e}")
            return False
    
    def execute(self) -> ActionResult:
        """Execute movement automation workflow"""
        try:
            if not self.garden_config:
                return ActionResult.failure_result("Garden configuration not loaded")
            
            logger.info("Starting movement automation")
            
            # For now, just demonstrate the movement system
            # This will be expanded based on specific gardening needs
            
            # Example: Move to main plot
            result = self.navigate_to_section("main_plot")
            if not result.success:
                return result
            
            logger.info("Movement automation completed successfully")
            return ActionResult.success_result("Movement automation completed successfully")
            
        except Exception as e:
            return ActionResult.failure_result("Movement automation failed", error=e)
    
    def navigate_to_garden(self) -> ActionResult:
        """Navigate to the main garden area"""
        try:
            if not self.garden_config or "go_to_garden" not in self.garden_config:
                return ActionResult.failure_result("Garden movement pattern not configured")
            
            logger.info("Navigating to garden area...")
            
            # Execute the go_to_garden pattern
            result = self.execute_pattern("go_to_garden")
            if result.success:
                logger.info("Successfully navigated to garden")
                return result
            else:
                return result
            
        except Exception as e:
            logger.error(f"Failed to navigate to garden: {e}")
            return ActionResult.failure_result("Failed to navigate to garden", error=e)
    
    def execute_pattern(self, pattern_name: str) -> ActionResult:
        """Execute a movement pattern from the configuration"""
        try:
            if not self.garden_config or pattern_name not in self.garden_config:
                return ActionResult.failure_result(f"Pattern '{pattern_name}' not found in configuration")
            
            pattern = self.garden_config[pattern_name]
            logger.info(f"Executing pattern: {pattern_name}")
            
            for i, command in enumerate(pattern):
                logger.info(f"Executing command {i+1}/{len(pattern)}: {command}")
                
                result = self.execute_simple_command(command)
                if not result.success:
                    return ActionResult.failure_result(f"Pattern command failed: {command}")
                
                # Small delay between commands
                time.sleep(0.1)
            
            logger.info(f"Pattern '{pattern_name}' executed successfully")
            return ActionResult.success_result(f"Pattern '{pattern_name}' executed successfully")
            
        except Exception as e:
            logger.error(f"Failed to execute pattern {pattern_name}: {e}")
            return ActionResult.failure_result(f"Failed to execute pattern {pattern_name}", error=e)
    
    def execute_simple_command(self, command) -> ActionResult:
        """Execute a simple movement command"""
        try:
            if isinstance(command, dict) and "key" in command and "duration" in command:
                # Handle key press commands like "key: w, duration: 2.5"
                key = command["key"]
                duration = command["duration"]
                return self.press_key(key, duration)
            else:
                return ActionResult.failure_result(f"Invalid command format: {command}")
                
        except Exception as e:
            logger.error(f"Failed to execute command {command}: {e}")
            return ActionResult.failure_result(f"Failed to execute command", error=e)
    
    def press_key(self, key: str, duration: float) -> ActionResult:
        """Press and hold a key for a specified duration"""
        try:
            logger.info(f"Pressing key '{key}' for {duration} seconds")
            
            # Press and hold the key
            pyautogui.keyDown(key)
            time.sleep(duration)
            pyautogui.keyUp(key)
            
            logger.info(f"Successfully pressed key '{key}' for {duration} seconds")
            return ActionResult.success_result(f"Pressed key '{key}' for {duration} seconds")
            
        except Exception as e:
            logger.error(f"Failed to press key '{key}': {e}")
            return ActionResult.failure_result(f"Failed to press key '{key}'", error=e)
    
    
