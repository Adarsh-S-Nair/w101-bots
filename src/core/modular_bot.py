"""
Modular bot implementation using the bot framework
Supports different automation types and easy scaling
"""
from typing import List, Optional, Dict, Any
from src.core.bot_framework import BotFramework
from src.core.automation_registry import AutomationRegistry
from src.core.action_result import ActionResult
from src.automation.housing_navigation import HousingNavigationAutomation
from src.automation.gardening_automation import GardeningAutomation
from src.utils.logger import logger

class ModularBot:
    """Modular bot that can handle different automation types"""
    
    def __init__(self, automation_type: str = "gardening"):
        self.automation_type = automation_type
        self.framework = BotFramework(automation_type)
        self.registry = AutomationRegistry()
        
        # Register automation types
        self._register_automation_types()
        
        # Load modules for the specified automation type
        self._load_automation_modules()
        
        logger.info(f"Modular Bot initialized for automation type: {automation_type}")
    
    def _register_automation_types(self):
        """Register all available automation types"""
        # Gardening automation
        self.registry.register_automation_type("gardening", [
            HousingNavigationAutomation,
            GardeningAutomation
        ])
        
        # Trivia automation
        from src.automation.trivia_automation import TriviaAutomation
        self.registry.register_automation_type("trivia", [
            TriviaAutomation
        ])
        
        # Future automation types can be added here
        # self.registry.register_automation_type("fishing", [
        #     HousingNavigationAutomation,
        #     FishingAutomation
        # ])
        
        # self.registry.register_automation_type("pvp", [
        #     PvPAutomation
        # ])
        
        logger.info(f"Registered {len(self.registry.get_available_automation_types())} automation types")
    
    def _load_automation_modules(self):
        """Load modules for the current automation type"""
        try:
            modules = self.registry.get_automation_modules(self.automation_type)
            self.framework.add_custom_modules(modules)
            logger.info(f"Loaded {len(modules)} modules for automation type: {self.automation_type}")
        except ValueError as e:
            logger.error(f"Failed to load automation modules: {e}")
            raise
    
    def run(self) -> ActionResult:
        """Run the complete bot workflow"""
        try:
            logger.info("=" * 60)
            logger.info(f"Starting {self.automation_type.title()} Bot...")
            logger.info("=" * 60)
            
            # Run the complete workflow (core + custom modules)
            result = self.framework.run_complete_workflow()
            
            if result.success:
                logger.info(f"{self.automation_type.title()} Bot execution completed successfully!")
            else:
                logger.error(f"{self.automation_type.title()} Bot execution failed: {result.message}")
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error during {self.automation_type} bot execution: {e}")
            return ActionResult.failure_result(f"Unexpected error during {self.automation_type} bot execution", error=e)
    
    def run_core_only(self) -> ActionResult:
        """Run only the core workflow (launcher, login, game startup)"""
        return self.framework.run_core_workflow()
    
    def run_custom_only(self) -> ActionResult:
        """Run only the custom modules for the current automation type"""
        return self.framework.run_custom_modules()
    
    def switch_automation_type(self, new_type: str) -> ActionResult:
        """Switch to a different automation type"""
        try:
            if new_type not in self.registry.get_available_automation_types():
                return ActionResult.failure_result(f"Automation type '{new_type}' not available")
            
            # Clear existing custom modules
            self.framework.custom_modules.clear()
            
            # Load new modules
            self.automation_type = new_type
            self._load_automation_modules()
            
            logger.info(f"Switched to automation type: {new_type}")
            return ActionResult.success_result(f"Switched to automation type: {new_type}")
            
        except Exception as e:
            return ActionResult.failure_result(f"Failed to switch automation type: {e}")
    
    def get_available_automation_types(self) -> List[str]:
        """Get list of available automation types"""
        return self.registry.get_available_automation_types()
    
    def get_automation_info(self) -> Dict[str, Any]:
        """Get information about the current automation type"""
        return self.registry.get_automation_info(self.automation_type)
    
    def get_all_automation_info(self) -> Dict[str, Any]:
        """Get information about all available automation types"""
        return self.registry.get_all_automation_info()
    
    def get_module_status(self) -> Dict[str, Any]:
        """Get status of all modules"""
        return self.framework.get_module_status()
