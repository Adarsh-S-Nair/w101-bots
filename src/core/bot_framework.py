"""
Core bot framework for Wizard101 automations
Handles common functionality: launcher, login, and game startup
"""
from typing import List, Optional, Dict, Any
from src.core.automation_base import AutomationBase
from src.core.action_result import ActionResult
from src.detection.ui_detector import UIDetector
from src.automation.launcher import LauncherAutomation
from src.automation.login import LoginAutomation
from src.automation.enter_game_automation import EnterGameAutomation
from src.utils.logger import logger
from src.utils.process_utils import ProcessUtils
from config import config

class BotFramework:
    """Core bot framework that handles common startup functionality"""
    
    def __init__(self, bot_type: str = "gardening"):
        self.bot_type = bot_type
        self.ui_detector = UIDetector()
        self.core_modules: List[AutomationBase] = []
        self.custom_modules: List[AutomationBase] = []
        
        # Initialize core modules based on bot type
        self._initialize_core_modules()
        
        logger.info(f"Bot Framework initialized for {bot_type} bot")
    
    def _initialize_core_modules(self):
        """Initialize core automation modules based on bot type"""
        if self.bot_type == "trivia":
            # Trivia bots don't need game launcher/login modules
            self.core_modules = []
            logger.info("Trivia bot: No core modules needed")
        else:
            # Game-based bots need launcher, login, and game entry
            self.core_modules = [
                LauncherAutomation(self.ui_detector),
                LoginAutomation(self.ui_detector),
                EnterGameAutomation(self.ui_detector),
            ]
            logger.info(f"Initialized {len(self.core_modules)} core automation modules")
    
    def add_custom_module(self, module: AutomationBase):
        """Add a custom automation module"""
        self.custom_modules.append(module)
        logger.info(f"Added custom module: {module.name}")
    
    def add_custom_modules(self, modules: List[AutomationBase]):
        """Add multiple custom automation modules"""
        for module in modules:
            self.add_custom_module(module)
    
    def run_core_workflow(self) -> ActionResult:
        """Run the core workflow (launcher, login, enter game)"""
        try:
            logger.info("=" * 50)
            logger.info("Starting Core Bot Workflow...")
            logger.info("=" * 50)
            
            # Validate configuration
            config.validate_config()
            config.setup_directories()
            
            logger.info("Configuration validated successfully")
            
            # Check initial state once at the beginning
            game_already_running = ProcessUtils.is_wizard101_running()
            logger.info(f"Initial game state: {'Already running' if game_already_running else 'Fresh startup required'}")
            
            # Execute core modules in sequence based on initial state
            for i, module in enumerate(self.core_modules):
                logger.info(f"Executing core module {i + 1}/{len(self.core_modules)}: {module.name}")
                
                # Pass the initial state to the module
                if hasattr(module, 'set_initial_state'):
                    module.set_initial_state(game_already_running)
                
                result = module.execute()
                
                if not result.success:
                    logger.error(f"Core module {module.name} failed: {result.message}")
                    if result.error:
                        logger.error(f"Error details: {result.error}")
                    return ActionResult.failure_result(
                        f"Core workflow failed at module: {module.name}",
                        error=result.error,
                        data={"failed_module": module.name, "module_index": i}
                    )
                
                # Check if module was skipped (e.g., game already running)
                if "skipped" in result.message.lower():
                    logger.info(f"Core module {module.name} was skipped: {result.message}")
                else:
                    logger.info(f"Core module {module.name} completed successfully")
            
            logger.info("Core workflow completed successfully!")
            return ActionResult.success_result("Core workflow completed successfully")
            
        except Exception as e:
            logger.error(f"Unexpected error during core workflow: {e}")
            return ActionResult.failure_result("Unexpected error during core workflow", error=e)
    
    def run_custom_modules(self) -> ActionResult:
        """Run all custom automation modules"""
        if not self.custom_modules:
            logger.info("No custom modules to execute")
            return ActionResult.success_result("No custom modules to execute")
        
        try:
            logger.info("=" * 50)
            logger.info("Starting Custom Modules...")
            logger.info("=" * 50)
            
            for i, module in enumerate(self.custom_modules):
                logger.info(f"Executing custom module {i + 1}/{len(self.custom_modules)}: {module.name}")
                
                result = module.execute()
                
                if not result.success:
                    logger.error(f"Custom module {module.name} failed: {result.message}")
                    if result.error:
                        logger.error(f"Error details: {result.error}")
                    return ActionResult.failure_result(
                        f"Custom module execution failed at: {module.name}",
                        error=result.error,
                        data={"failed_module": module.name, "module_index": i}
                    )
                
                logger.info(f"Custom module {module.name} completed successfully")
            
            logger.info("All custom modules completed successfully!")
            return ActionResult.success_result("All custom modules completed successfully")
            
        except Exception as e:
            logger.error(f"Unexpected error during custom module execution: {e}")
            return ActionResult.failure_result("Unexpected error during custom module execution", error=e)
    
    def run_complete_workflow(self) -> ActionResult:
        """Run the complete workflow (core + custom modules)"""
        try:
            # Run core workflow first
            core_result = self.run_core_workflow()
            if not core_result.success:
                return core_result
            
            # Run custom modules
            custom_result = self.run_custom_modules()
            if not custom_result.success:
                return custom_result
            
            logger.info("Complete workflow finished successfully!")
            return ActionResult.success_result("Complete workflow finished successfully")
            
        except Exception as e:
            logger.error(f"Unexpected error during complete workflow: {e}")
            return ActionResult.failure_result("Unexpected error during complete workflow", error=e)
    
    def get_available_modules(self) -> Dict[str, List[str]]:
        """Get list of available automation modules by category"""
        return {
            "core": [module.name for module in self.core_modules],
            "custom": [module.name for module in self.custom_modules]
        }
    
    def get_module_status(self) -> Dict[str, Any]:
        """Get status of all modules"""
        status = {
            "core_modules": {},
            "custom_modules": {}
        }
        
        for i, module in enumerate(self.core_modules):
            status["core_modules"][module.name] = {
                "index": i,
                "class": module.__class__.__name__,
                "type": "core"
            }
        
        for i, module in enumerate(self.custom_modules):
            status["custom_modules"][module.name] = {
                "index": i,
                "class": module.__class__.__name__,
                "type": "custom"
            }
        
        return status
