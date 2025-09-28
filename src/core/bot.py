"""
Main bot controller
"""
from typing import List, Optional
from src.core.automation_base import AutomationBase
from src.core.action_result import ActionResult
from src.detection.ui_detector import UIDetector
from src.automation.launcher import LauncherAutomation
from src.automation.login import LoginAutomation
from src.utils.logger import logger
from config import config

class Wizard101Bot:
    """Main bot controller that orchestrates all automation modules"""
    
    def __init__(self):
        self.ui_detector = UIDetector()
        self.automation_modules: List[AutomationBase] = []
        self.current_module_index = 0
        
        # Initialize automation modules
        self._initialize_modules()
        
        logger.info("Wizard101 Bot initialized")
    
    def _initialize_modules(self):
        """Initialize all automation modules"""
        self.automation_modules = [
            LauncherAutomation(self.ui_detector),
            LoginAutomation(self.ui_detector),
            # Future modules will be added here:
            # CharacterAutomation(self.ui_detector),
            # GardeningAutomation(self.ui_detector),
        ]
        
        logger.info(f"Initialized {len(self.automation_modules)} automation modules")
    
    def run(self) -> ActionResult:
        """Run the complete bot workflow"""
        try:
            logger.info("=" * 50)
            logger.info("Wizard101 Gardening Bot Starting...")
            logger.info("=" * 50)
            
            # Validate configuration
            config.validate_config()
            config.setup_directories()
            
            logger.info("Configuration validated successfully")
            
            # Execute each automation module in sequence
            for i, module in enumerate(self.automation_modules):
                logger.info(f"Executing module {i + 1}/{len(self.automation_modules)}: {module.name}")
                
                result = module.execute()
                
                if not result.success:
                    logger.error(f"Module {module.name} failed: {result.message}")
                    if result.error:
                        logger.error(f"Error details: {result.error}")
                    return ActionResult.failure_result(
                        f"Bot execution failed at module: {module.name}",
                        error=result.error,
                        data={"failed_module": module.name, "module_index": i}
                    )
                
                logger.info(f"Module {module.name} completed successfully")
            
            logger.info("All automation modules completed successfully!")
            logger.info("Bot execution completed successfully")
            
            return ActionResult.success_result("Bot execution completed successfully")
            
        except KeyboardInterrupt:
            logger.info("Bot execution interrupted by user")
            return ActionResult.success_result("Bot execution interrupted by user")
            
        except Exception as e:
            logger.error(f"Unexpected error during bot execution: {e}")
            return ActionResult.failure_result("Unexpected error during bot execution", error=e)
    
    def run_single_module(self, module_name: str) -> ActionResult:
        """Run a specific automation module"""
        try:
            # Find the module by name
            module = None
            for m in self.automation_modules:
                if m.name.lower() == module_name.lower():
                    module = m
                    break
            
            if not module:
                return ActionResult.failure_result(f"Module '{module_name}' not found")
            
            logger.info(f"Running single module: {module.name}")
            
            result = module.execute()
            
            if result.success:
                logger.info(f"Module {module.name} completed successfully")
            else:
                logger.error(f"Module {module.name} failed: {result.message}")
            
            return result
            
        except Exception as e:
            return ActionResult.failure_result(f"Failed to run module '{module_name}'", error=e)
    
    def get_available_modules(self) -> List[str]:
        """Get list of available automation modules"""
        return [module.name for module in self.automation_modules]
    
    def get_module_status(self) -> dict:
        """Get status of all modules"""
        status = {}
        for i, module in enumerate(self.automation_modules):
            status[module.name] = {
                "index": i,
                "class": module.__class__.__name__,
                "completed": i < self.current_module_index
            }
        return status
