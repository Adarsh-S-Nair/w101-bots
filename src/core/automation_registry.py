"""
Automation registry for managing different bot types and their modules
"""
from typing import Dict, List, Type, Any
from src.core.automation_base import AutomationBase
from src.detection.ui_detector import UIDetector
from src.utils.logger import logger

class AutomationRegistry:
    """Registry for managing different automation types and their modules"""
    
    def __init__(self):
        self.registered_automations: Dict[str, List[Type[AutomationBase]]] = {}
        self.ui_detector = UIDetector()
        logger.info("Automation Registry initialized")
    
    def register_automation_type(self, automation_type: str, modules: List[Type[AutomationBase]]):
        """Register a new automation type with its modules"""
        self.registered_automations[automation_type] = modules
        logger.info(f"Registered automation type '{automation_type}' with {len(modules)} modules")
    
    def get_automation_modules(self, automation_type: str) -> List[AutomationBase]:
        """Get instantiated modules for a specific automation type"""
        if automation_type not in self.registered_automations:
            raise ValueError(f"Automation type '{automation_type}' not registered")
        
        modules = []
        for module_class in self.registered_automations[automation_type]:
            try:
                module = module_class(self.ui_detector)
                modules.append(module)
            except Exception as e:
                logger.error(f"Failed to instantiate module {module_class.__name__}: {e}")
                raise
        
        return modules
    
    def get_available_automation_types(self) -> List[str]:
        """Get list of available automation types"""
        return list(self.registered_automations.keys())
    
    def get_automation_info(self, automation_type: str) -> Dict[str, Any]:
        """Get information about a specific automation type"""
        if automation_type not in self.registered_automations:
            return {"error": f"Automation type '{automation_type}' not found"}
        
        modules = self.registered_automations[automation_type]
        return {
            "type": automation_type,
            "module_count": len(modules),
            "modules": [module.__name__ for module in modules]
        }
    
    def get_all_automation_info(self) -> Dict[str, Any]:
        """Get information about all registered automation types"""
        info = {}
        for automation_type in self.registered_automations:
            info[automation_type] = self.get_automation_info(automation_type)
        return info
