"""
Base automation class with reusable methods
"""
import time
import pyautogui
from typing import Optional, List, Callable, Any
from abc import ABC, abstractmethod

from src.core.action_result import ActionResult, ActionResultStatus
from src.core.element import UIElement, ElementSearchCriteria, Coordinates
from src.detection.ui_detector import UIDetector
from src.utils.logger import logger

class AutomationBase(ABC):
    """Base class for all automation modules with reusable methods"""
    
    def __init__(self, ui_detector: UIDetector):
        self.ui_detector = ui_detector
        self.name = self.__class__.__name__
        self.initial_game_state = None  # Will be set by bot framework
        
    def find_and_click(self, criteria: ElementSearchCriteria, 
                      wait_time: float = 2.0, retries: int = 3) -> ActionResult:
        """Find an element and click on it with retries"""
        for attempt in range(retries + 1):
            try:
                logger.info(f"Attempting to find and click '{criteria.name}' (attempt {attempt + 1}/{retries + 1})")
                
                # Find the element
                element = self.ui_detector.find_element(criteria)
                if not element:
                    if attempt < retries:
                        logger.warning(f"Element '{criteria.name}' not found, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    return ActionResult.failure_result(f"Element '{criteria.name}' not found after {retries + 1} attempts")
                
                # Wait a moment before clicking to ensure UI is stable
                logger.debug(f"Waiting 0.5s before clicking '{criteria.name}' to ensure UI stability...")
                time.sleep(0.5)
                
                # Click on the element
                return self.click_element(element)
                
            except Exception as e:
                if attempt < retries:
                    logger.warning(f"Error finding/clicking '{criteria.name}': {e}, retrying...")
                    time.sleep(wait_time)
                    continue
                return ActionResult.failure_result(f"Failed to find and click '{criteria.name}'", error=e)
        
        return ActionResult.failure_result(f"Failed to find and click '{criteria.name}' after all retries")
    
    def find_and_type(self, criteria: ElementSearchCriteria, text: str, 
                     wait_time: float = 2.0, retries: int = 3) -> ActionResult:
        """Find an input field and type text into it"""
        for attempt in range(retries + 1):
            try:
                logger.info(f"Attempting to find and type into '{criteria.name}' (attempt {attempt + 1}/{retries + 1})")
                
                # Find the element
                element = self.ui_detector.find_element(criteria)
                if not element:
                    if attempt < retries:
                        logger.warning(f"Element '{criteria.name}' not found, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    return ActionResult.failure_result(f"Element '{criteria.name}' not found after {retries + 1} attempts")
                
                # Wait a moment before typing to ensure UI is stable
                logger.debug(f"Waiting 0.5s before typing into '{criteria.name}' to ensure UI stability...")
                time.sleep(0.5)
                
                # Type into the element
                return self.type_into_element(element, text)
                
            except Exception as e:
                if attempt < retries:
                    logger.warning(f"Error finding/typing into '{criteria.name}': {e}, retrying...")
                    time.sleep(wait_time)
                    continue
                return ActionResult.failure_result(f"Failed to find and type into '{criteria.name}'", error=e)
        
        return ActionResult.failure_result(f"Failed to find and type into '{criteria.name}' after all retries")
    
    def wait_for_element(self, criteria: ElementSearchCriteria, 
                        timeout: float = 10.0, check_interval: float = 1.0) -> ActionResult:
        """Wait for an element to appear on screen"""
        start_time = time.time()
        attempts = 0
        
        
        while time.time() - start_time < timeout:
            attempts += 1
            try:
                element = self.ui_detector.find_element(criteria, silent=True)
                if element:
                    wait_time = time.time() - start_time
                    return ActionResult.success_result(
                        f"Element '{criteria.name}' found",
                        data={"element": element, "wait_time": wait_time, "attempts": attempts}
                    )
                
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.debug(f"Error checking for element '{criteria.name}' (attempt {attempts}): {e}")
                time.sleep(check_interval)
        
        elapsed = time.time() - start_time
        logger.warning(f"Element '{criteria.name}' not found within {timeout}s timeout ({attempts} attempts)")
        return ActionResult.failure_result(f"Element '{criteria.name}' not found within {timeout}s timeout")
    
    def wait_for_element_to_disappear(self, criteria: ElementSearchCriteria, 
                                    timeout: float = 10.0, check_interval: float = 1.0) -> ActionResult:
        """Wait for an element to disappear from screen"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                element = self.ui_detector.find_element(criteria, silent=True)
                if not element:
                    logger.info(f"Element '{criteria.name}' disappeared after {time.time() - start_time:.1f}s")
                    return ActionResult.success_result(
                        f"Element '{criteria.name}' disappeared",
                        data={"wait_time": time.time() - start_time}
                    )
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.debug(f"Error checking for element '{criteria.name}': {e}")
                time.sleep(check_interval)
        
        return ActionResult.failure_result(f"Element '{criteria.name}' still present after {timeout}s timeout")
    
    def click_element(self, element: UIElement) -> ActionResult:
        """Click on a UI element"""
        try:
            logger.info(f"Clicking on '{element.name}' at {element.center}")
            logger.debug(f"Element bounding box: {element.bounding_box}")
            logger.debug(f"Detection method: {element.detection_method}")
            logger.debug(f"Confidence: {element.confidence:.3f}")
            
            # Move mouse to element and click
            pyautogui.moveTo(element.center.x, element.center.y)
            time.sleep(0.2)  # Small delay for visual feedback and UI stability
            
            # Perform the click
            pyautogui.click()
            logger.debug(f"Click performed at ({element.center.x}, {element.center.y})")
            
            # Add a small delay after clicking to allow UI to respond
            time.sleep(0.5)
            
            return ActionResult.success_result(
                f"Successfully clicked '{element.name}'",
                data={"coordinates": element.center, "confidence": element.confidence}
            )
            
        except Exception as e:
            logger.error(f"Failed to click '{element.name}': {e}")
            return ActionResult.failure_result(f"Failed to click '{element.name}'", error=e)
    
    def type_into_element(self, element: UIElement, text: str) -> ActionResult:
        """Type text into an input element"""
        try:
            logger.info(f"Typing into '{element.name}' at {element.center}")
            
            # Click on the element first to focus it
            pyautogui.moveTo(element.center.x, element.center.y)
            pyautogui.click()
            time.sleep(0.2)
            
            # Clear the field and type new text
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.typewrite(text, interval=0.05)
            
            return ActionResult.success_result(
                f"Successfully typed into '{element.name}'",
                data={"coordinates": element.center, "text_length": len(text)}
            )
            
        except Exception as e:
            return ActionResult.failure_result(f"Failed to type into '{element.name}'", error=e)
    
    def wait_for_condition(self, condition_func: Callable[[], bool], 
                          timeout: float = 10.0, check_interval: float = 1.0,
                          condition_name: str = "custom condition") -> ActionResult:
        """Wait for a custom condition to be true"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if condition_func():
                    logger.info(f"Condition '{condition_name}' met after {time.time() - start_time:.1f}s")
                    return ActionResult.success_result(
                        f"Condition '{condition_name}' met",
                        data={"wait_time": time.time() - start_time}
                    )
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.debug(f"Error checking condition '{condition_name}': {e}")
                time.sleep(check_interval)
        
        return ActionResult.failure_result(f"Condition '{condition_name}' not met within {timeout}s timeout")
    
    def execute_with_retry(self, action_func: Callable[[], ActionResult], 
                          max_retries: int = 3, retry_delay: float = 2.0) -> ActionResult:
        """Execute an action with automatic retries"""
        for attempt in range(max_retries + 1):
            try:
                result = action_func()
                
                if result.success:
                    return result
                
                if result.should_retry and attempt < max_retries:
                    logger.warning(f"Action failed, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries + 1})")
                    time.sleep(retry_delay)
                    continue
                
                return result
                
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Action failed with exception: {e}, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue
                return ActionResult.failure_result("Action failed after all retries", error=e)
        
        return ActionResult.failure_result("Action failed after all retries")
    
    def set_initial_state(self, game_already_running: bool):
        """Set the initial game state - called by bot framework"""
        self.initial_game_state = game_already_running
        logger.debug(f"{self.name}: Initial game state set to {'already running' if game_already_running else 'fresh startup'}")
    
    @abstractmethod
    def execute(self) -> ActionResult:
        """Execute the main automation workflow - must be implemented by subclasses"""
        pass
