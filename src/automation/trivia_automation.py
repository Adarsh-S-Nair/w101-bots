"""
Trivia automation module for Wizard101 trivia bot
Handles browser navigation and trivia-specific tasks
"""
import subprocess
import time
import pyautogui
import yaml
import os
import pyperclip
from src.core.automation_base import AutomationBase
from src.core.action_result import ActionResult
from src.core.element import ElementSearchCriteria, ElementType, DetectionMethod
from src.utils.logger import logger
from src.utils.screenshot import ScreenshotManager
from src.utils.bot_execution_tracker import TriviaBotTracker
from config import config
from src.constants import AssetPaths, AutomationConstants

# Constants for answer positions (pixels to move from question area)
ANSWER_POSITIONS = {
    'first': {'x': -200, 'y': 50},    # First answer option
    'second': {'x': 80, 'y': 50},     # Second answer option  
    'third': {'x': -200, 'y': 90},    # Third answer option
    'fourth': {'x': 80, 'y': 90}      # Fourth answer option
}

# UI Element Configuration
# Defines template paths and interaction parameters for all trivia elements
UI_ELEMENTS = {
    "W101_LOGO": {
        "name": "W101 Logo",
        "template": AssetPaths.TriviaTemplates.W101_LOGO,
        "timeout": 20.0
    },
    "LOGIN_BUTTON": {
        "name": "Login Button",
        "template": AssetPaths.TriviaTemplates.LOGIN_BUTTON,
        "timeout": 5.0,
        "confidence": AutomationConstants.TRIVIA_CONFIDENCE_THRESHOLD
    },
    "TRIVIA_BANNER": {
        "name": "Trivia Banner",
        "template": AssetPaths.TriviaTemplates.TRIVIA_BANNER,
        "timeout": 1.5,
        "confidence": AutomationConstants.TRIVIA_CONFIDENCE_THRESHOLD
    },
    "SUBMIT_BUTTON": {
        "name": "Submit Answer Button",
        "template": AssetPaths.TriviaTemplates.SUBMIT_ANSWER_BUTTON,
        "timeout": 10.0,
        "confidence": 0.95
    },
    "CLAIM_REWARD_1": {
        "name": "Claim Your Reward Button",
        "template": AssetPaths.TriviaTemplates.CLAIM_YOUR_REWARD_BUTTON,
        "timeout": 15.0,
        "post_click_delay": 0.0
    },
    "CLAIM_REWARD_2": {
        "name": "Second Claim Your Reward Button",
        "template": AssetPaths.TriviaTemplates.SECOND_CLAIM_YOUR_REWARD_BUTTON,
        "timeout": 15.0,
        "post_click_delay": 0.0
    },
    "TAKE_ANOTHER_QUIZ": {
        "name": "Take Another Quiz Button",
        "template": AssetPaths.TriviaTemplates.TAKE_ANOTHER_QUIZ_BUTTON,
        "timeout": 15.0
    },
    "GOOGLE_SEARCH_ICON": {
        "name": "Google Search Icon",
        "template": AssetPaths.TriviaTemplates.GOOGLE_SEARCH_ICON,
        "timeout": 20.0
    }
}


class TriviaAutomation(AutomationBase):
    """Automation module for Wizard101 trivia bot"""
    
    def __init__(self, ui_detector):
        super().__init__(ui_detector)
        self.name = "Trivia Automation"
        self.screenshot_manager = ScreenshotManager()
        self.trivia_database = self._load_trivia_database()
        self.execution_tracker = TriviaBotTracker()
        self.current_question_count = 0
    
    def is_time_to_run(self) -> bool:
        """Check if it's time to run the trivia bot based on the 20-hour schedule"""
        return self.execution_tracker.is_time_to_run()
    
    def get_next_run_time(self):
        """Get the next scheduled run time for the trivia bot"""
        return self.execution_tracker.get_next_run_time()
    
    def get_execution_stats(self):
        """Get trivia bot execution statistics"""
        return self.execution_tracker.get_execution_stats()
    
    def get_execution_history(self, limit: int = 10):
        """Get recent trivia bot execution history"""
        return self.execution_tracker.get_execution_history(limit)
    
    def _interact_with_element(self, element_key: str, action: str = "wait", **kwargs) -> ActionResult:
        """
        Generic method to interact with UI elements defined in UI_ELEMENTS configuration.
        
        Args:
            element_key: Key in UI_ELEMENTS dictionary
            action: "wait" (just wait to appear), "click" (wait and click), "wait_disappear"
            **kwargs: Overrides for configuration values (timeout, etc.)
        """
        if element_key not in UI_ELEMENTS:
            return ActionResult.failure_result(f"Unknown element key: {element_key}")
            
        config_data = UI_ELEMENTS[element_key]
        name = config_data.get("name", element_key)
        template = config_data.get("template")
        timeout = kwargs.get("timeout", config_data.get("timeout", 15.0))
        confidence = kwargs.get("confidence", config_data.get("confidence", AutomationConstants.TRIVIA_CONFIDENCE_THRESHOLD))
        
        # Create search criteria
        criteria = ElementSearchCriteria(
            name=name,
            element_type=ElementType.BUTTON if action != "wait_disappear" else ElementType.IMAGE,
            template_path=config.get_trivia_template_path(template),
            confidence_threshold=confidence,
            detection_methods=[DetectionMethod.TEMPLATE]
        )
        
        if action == "wait_disappear":
            logger.info(f"Waiting for {name} to disappear...")
            return self.wait_for_element_to_disappear(criteria, timeout=timeout, check_interval=0.1)
            
        logger.info(f"Waiting for {name} to appear...")
        result = self.wait_for_element(criteria, timeout=timeout, check_interval=0.1)
        
        if not result.success:
            logger.warning(f"{name} did not appear within timeout period")
            return ActionResult.failure_result(f"{name} not found within timeout")
            
        logger.info(f"{name} found")
        
        if action == "click":
            # Special handling for Submit Button to click further left
            if element_key == "SUBMIT_BUTTON":
                # Get element first to calculate custom position
                element = self.ui_detector.find_element(criteria)
                if element:
                    center = element.center
                    # Move 50 pixels to the left of center (or even more if needed)
                    # The template is only the right side, so center is already biased right
                    target_x = center.x - 50
                    target_y = center.y
                    
                    pyautogui.moveTo(target_x, target_y)
                    time.sleep(0.1)
                    pyautogui.click()
                    
                    post_delay = kwargs.get("post_click_delay", config_data.get("post_click_delay", 0.2))
                    if post_delay > 0:
                        time.sleep(post_delay)
                    return ActionResult.success_result(f"{name} clicked successfully at offset position")
            
            click_result = self.find_and_click(criteria, wait_time=0.2, retries=2)
            if click_result.success:
                post_delay = kwargs.get("post_click_delay", config_data.get("post_click_delay", 0.2))
                if post_delay > 0:
                    time.sleep(post_delay)
                return ActionResult.success_result(f"{name} clicked successfully")
            else:
                logger.error(f"Failed to click {name}")
                return ActionResult.failure_result(f"Failed to click {name}")
                
        return ActionResult.success_result(f"{name} found")

    def execute(self) -> ActionResult:
        """Execute trivia automation workflow"""
        # Start tracking execution
        execution_data = self.execution_tracker.start_execution()
        execution_id = execution_data["execution_id"]
        
        try:
            logger.info("Starting Trivia Automation...")
            
            # Keep running until no more trivias are available
            max_attempts = 50  # Prevent infinite loops
            attempt = 0
            completed_trivias = set()
            skipped_trivias = set()  # Track trivias that are already completed
            
            while attempt < max_attempts:
                attempt += 1
                logger.info(f"=== Trivia Automation Attempt {attempt}/{max_attempts} ===")
                
                # Open Chrome browser and navigate to main trivia page (only on first attempt)
                if attempt == 1:
                    result = self._open_chrome()
                    if not result.success:
                        return result
                    
                    # Wait for W101 logo to confirm we're on the site
                    result = self._interact_with_element("W101_LOGO", action="wait")
                    if not result.success:
                        logger.error(f"Failed to find W101 logo: {result.message}")
                        return result
                    
                    # Handle login on the main trivia page
                    result = self._handle_login_if_needed()
                    if not result.success:
                        logger.error(f"Login failed: {result.message}")
                        return result
                
                # Look for and complete one trivia
                result = self._find_and_complete_single_trivia(completed_trivias, skipped_trivias)
                if not result.success:
                    logger.info(f"No more trivias available on attempt {attempt}. Completed {len(completed_trivias)} trivias total, skipped {len(skipped_trivias)} already completed.")
                    break
                
                # Track completed trivia
                if hasattr(result, 'data') and 'trivia_name' in result.data:
                    completed_trivias.add(result.data['trivia_name'])
                    logger.info(f"Completed trivia: {result.data['trivia_name']}. Total completed: {len(completed_trivias)}")
                
                # Wait a bit before next attempt
                time.sleep(0.5)
            
            logger.info(f"Trivia automation completed successfully. Total trivias completed: {len(completed_trivias)}")
            
            # Complete execution tracking with success
            completion_info = self.execution_tracker.complete_execution(
                execution_id=execution_id,
                success=True,
                trivia_count=len(completed_trivias),
                execution_summary={
                    "attempts_made": attempt,
                    "skipped_trivias": len(skipped_trivias),
                    "completed_trivias_list": list(completed_trivias)
                }
            )
            
            return ActionResult.success_result(f"Trivia automation completed successfully. Total trivias completed: {len(completed_trivias)}")
            
        except Exception as e:
            logger.error(f"Error in trivia automation: {e}")
            
            # Complete execution tracking with failure
            self.execution_tracker.complete_execution(
                execution_id=execution_id,
                success=False,
                trivia_count=len(completed_trivias) if 'completed_trivias' in locals() else 0,
                execution_summary={
                    "error": str(e),
                    "attempts_made": attempt if 'attempt' in locals() else 0
                }
            )
            
            return ActionResult.failure_result(f"Trivia automation failed: {e}", error=e)
    
    def _open_chrome(self) -> ActionResult:
        """Open Chrome browser and navigate to main trivia page directly"""
        try:
            logger.info("Opening Chrome browser...")
            
            # Common Chrome paths on Windows
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
            ]
            
            found_chrome_path = None
            for path in chrome_paths:
                if os.path.exists(path):
                    found_chrome_path = path
                    break
            
            # Target URL
            target_url = "https://www.wizard101.com/game/trivia"
            
            # Method 1: Use full path if found - DIRECT NAVIGATION
            if found_chrome_path:
                try:
                    logger.info(f"Found Chrome at {found_chrome_path}")
                    # Use subprocess.Popen with the executable directly AND the URL
                    subprocess.Popen([found_chrome_path, target_url])
                    logger.info(f"Chrome opened with found executable navigating to {target_url}")
                except Exception as e:
                    logger.error(f"Failed to open Chrome with found path: {e}")
                    return ActionResult.failure_result(f"Failed to open Chrome: {e}", error=e)
            else:
                # Fallback: Try 'start' command with URL if we can't find Chrome executable
                # This lets Windows handle the default browser (which hopefully is Chrome or handles the site)
                try:
                    logger.info("Chrome executable not found in common locations, trying system default browser...")
                    subprocess.Popen(f'start {target_url}', shell=True)
                    logger.info("Opened default browser with start command")
                except Exception as e:
                    logger.error(f"Failed to open default browser: {e}")
                    return ActionResult.failure_result(f"Could not open browser: {e}")
            
            # Wait for browser to open and load
            logger.info("Waiting for browser to initialize...")
            time.sleep(0.5)
            
            return ActionResult.success_result("Browser opened successfully")
            
        except Exception as e:
            logger.error(f"Error opening browser: {e}")
            return ActionResult.failure_result(f"Failed to open browser: {e}", error=e)
    
    def _navigate_to_trivia(self, trivia_name: str = None) -> ActionResult:
        """Navigate to a specific trivia page or the main trivia page"""
        try:
            if trivia_name:
                logger.info(f"Navigating to {trivia_name} trivia page...")
                trivia_data = self.trivia_database.get(trivia_name)
                if not trivia_data:
                    return ActionResult.failure_result(f"Trivia {trivia_name} not found in database")
                
                url_path = trivia_data.get('url_path')
                if not url_path:
                    return ActionResult.failure_result(f"No url_path found for trivia {trivia_name}")
                
                trivia_url = f"https://www.wizard101.com/quiz/trivia/game/{url_path}"
            else:
                logger.info("Navigating to main trivia page...")
                # Default to KingsIsle trivia if no specific trivia requested
                trivia_url = "https://www.wizard101.com/quiz/trivia/game/kingsisle-trivia"
            
            # Take a screenshot of current state
            screenshot = self.screenshot_manager.take_screenshot()
            if screenshot is not None:
                self.screenshot_manager.save_screenshot(screenshot, "chrome_before_navigation")
            
            # Use pyautogui to navigate to the URL
            import pyautogui
            
            # Click on address bar (Ctrl+L)
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.1)
            
            # Type the URL
            pyautogui.write(trivia_url)
            time.sleep(0.1)
            
            # Press Enter to navigate
            pyautogui.press('enter')
            
            logger.info(f"Navigated to: {trivia_url}")
            
            # Wait for page to load and take screenshot
            time.sleep(1.0)
            screenshot = self.screenshot_manager.take_screenshot()
            if screenshot is not None:
                self.screenshot_manager.save_screenshot(screenshot, "trivia_page_loaded")
            
            return ActionResult.success_result(f"Successfully navigated to {trivia_name or 'main trivia'} page")
            
        except Exception as e:
            logger.error(f"Error navigating to trivia page: {e}")
            return ActionResult.failure_result(f"Failed to navigate to trivia page: {e}", error=e)
    
    def _wait_for_w101_logo(self) -> ActionResult:
        """Wait for W101 logo to confirm we're on the site"""
        try:
            return self._wait_for_trivia_button(
                "W101 Logo",
                AssetPaths.TriviaTemplates.W101_LOGO,
                timeout=20.0
            )
        except Exception as e:
            logger.error(f"Error waiting for W101 logo: {e}")
            return ActionResult.failure_result(f"Failed to wait for W101 logo: {e}", error=e)
    
    def _handle_login_if_needed(self) -> ActionResult:
        """Check if login is needed and handle authentication if required"""
        try:
            logger.info("Checking if login is needed...")
            
            # Look for login button to determine if login is needed
            login_button_criteria = ElementSearchCriteria(
                name="Login Button",
                element_type=ElementType.BUTTON,
                detection_methods=[DetectionMethod.TEMPLATE],
                confidence_threshold=AutomationConstants.TRIVIA_CONFIDENCE_THRESHOLD,
                template_path=config.get_trivia_template_path(AssetPaths.TriviaTemplates.LOGIN_BUTTON)
            )
            
            # Try to find the login button
            login_button_element = self.ui_detector.find_element(login_button_criteria)
            
            if login_button_element:
                logger.info(f"Found login button at {login_button_element.bounding_box} - login required")
                
                # Take a screenshot before login
                screenshot = self.screenshot_manager.take_screenshot()
                if screenshot is not None:
                    self.screenshot_manager.save_screenshot(screenshot, "before_login")
                
                # Move mouse to login button center
                center = login_button_element.center
                pyautogui.moveTo(center.x, center.y)
                logger.info(f"Moved mouse to login button: ({center.x}, {center.y})")
                
                # Move mouse up 80 pixels from login button
                click_y = center.y - 60
                pyautogui.moveTo(center.x, click_y)
                logger.info(f"Moved mouse up 60 pixels to click position: ({center.x}, {click_y})")
                
                # Click at the adjusted position
                pyautogui.click(center.x, click_y)
                logger.info("Clicked at adjusted position")
                
                # Clear the field and enter username
                result = self._enter_username()
                if not result.success:
                    return result
                
                # Take screenshot after entering username
                screenshot = self.screenshot_manager.take_screenshot()
                if screenshot is not None:
                    self.screenshot_manager.save_screenshot(screenshot, "after_username_entered")
                
                return ActionResult.success_result("Login completed successfully")
            else:
                logger.info("Login button not found - already logged in, skipping login step")
                return ActionResult.success_result("Already logged in - no login needed")
            
        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return ActionResult.failure_result(f"Failed to check login status: {e}", error=e)
    
    def _enter_username(self) -> ActionResult:
        """Clear the username field and enter the username from .env"""
        try:
            logger.info("Clearing username field and entering username...")
            
            # Get username from config (loaded from .env)
            username = config.USERNAME
            if not username:
                logger.error("No username found in .env file (WIZARD101_USERNAME)")
                return ActionResult.failure_result("No username configured in .env file")
            
            logger.info(f"Entering username: {username}")
            
            # Clear the field using Ctrl+A and Delete
            pyautogui.hotkey('ctrl', 'a')  # Select all text
            time.sleep(0.1)
            pyautogui.press('delete')  # Delete selected text
            time.sleep(0.1)
            
            # Type the username with visible typing
            pyautogui.write(username, interval=0.005)  # Fast typing
            time.sleep(0.2)
            
            logger.info("Username entered successfully")
            
            # Move to password field and enter password
            result = self._enter_password()
            if not result.success:
                return result
            
            return ActionResult.success_result("Username and password entered successfully")
            
        except Exception as e:
            logger.error(f"Error entering username: {e}")
            return ActionResult.failure_result(f"Failed to enter username: {e}", error=e)
    
    def _enter_password(self) -> ActionResult:
        """Enter the password in the password field"""
        try:
            logger.info("Moving to password field and entering password...")
            
            # Get password from config (loaded from .env)
            password = config.PASSWORD
            if not password:
                logger.error("No password found in .env file (WIZARD101_PASSWORD)")
                return ActionResult.failure_result("No password configured in .env file")
            
            # Obfuscate password for logging (show first 2 chars + asterisks)
            obfuscated_password = password[:2] + "*" * (len(password) - 2) if len(password) > 2 else "*" * len(password)
            logger.info(f"Entering password: {obfuscated_password}")
            
            # Press Tab to move to password field
            pyautogui.press('tab')
            time.sleep(0.3)
            
            # Clear the password field
            pyautogui.hotkey('ctrl', 'a')  # Select all text
            time.sleep(0.1)
            pyautogui.press('delete')  # Delete selected text
            time.sleep(0.1)
            
            # Type the password with visible typing
            pyautogui.write(password, interval=0.005)  # Fast typing
            time.sleep(0.2)
            
            logger.info("Password entered successfully")
            
            # Press Enter to submit login form
            logger.info("Pressing Enter to submit login form...")
            pyautogui.press('enter')
            time.sleep(0.5)  # Wait for login to process
            
            logger.info("Login form submitted")
            return ActionResult.success_result("Password entered and login form submitted")
            
        except Exception as e:
            logger.error(f"Error entering password: {e}")
            return ActionResult.failure_result(f"Failed to enter password: {e}", error=e)
    
    def _load_trivia_database(self) -> dict:
        """Load trivia database from YAML file"""
        try:
            trivia_db_path = "config/trivia_database.yaml"
            if not os.path.exists(trivia_db_path):
                logger.warning(f"Trivia database file not found: {trivia_db_path}")
                return {}
            
            with open(trivia_db_path, 'r') as file:
                data = yaml.safe_load(file)
                return data.get('trivias', {})
                
        except Exception as e:
            logger.error(f"Error loading trivia database: {e}")
            return {}
    
    def _find_and_complete_single_trivia(self, completed_trivias: set, skipped_trivias: set) -> ActionResult:
        """Find and complete a single trivia using URL-based navigation"""
        try:
            logger.info("Looking for available trivia...")
            
            if not self.trivia_database:
                logger.warning("No trivias found in database")
                return ActionResult.failure_result("No trivias found in database")
            
            # Calculate how many trivias are left to try
            total_trivias = len(self.trivia_database)
            processed_trivias = len(completed_trivias) + len(skipped_trivias)
            remaining_trivias = total_trivias - processed_trivias
            
            if remaining_trivias == 0:
                logger.info("All trivias have been processed")
                return ActionResult.failure_result("All trivias have been processed")
            
            logger.info(f"Trying trivias: {remaining_trivias} remaining out of {total_trivias} total")
            
            # Try each trivia in the database until we find one that works
            for trivia_name, trivia_data in self.trivia_database.items():
                # Skip trivias we've already completed or determined are completed
                if trivia_name in completed_trivias or trivia_name in skipped_trivias:
                    logger.debug(f"Skipping {trivia_name} - already processed")
                    continue
                
                logger.info(f"Trying trivia: {trivia_name}")
                
                # Navigate directly to this trivia's URL
                result = self._navigate_to_trivia(trivia_name)
                if not result.success:
                    logger.warning(f"Failed to navigate to {trivia_name}: {result.message}")
                    continue
                
                # Check if trivia banner is present - if not, trivia is already completed
                result = self._interact_with_element("TRIVIA_BANNER", action="wait")
                if not result.success:
                    logger.info(f"Trivia banner not found for {trivia_name} - trivia already completed, skipping to next trivia")
                    skipped_trivias.add(trivia_name)
                    continue
                
                # Try to complete this trivia
                result = self._complete_single_trivia(trivia_name)
                if result.success:
                    logger.info(f"Successfully completed trivia: {trivia_name}")
                    return ActionResult.success_result(f"Successfully completed trivia: {trivia_name}", data={'trivia_name': trivia_name})
                else:
                    logger.warning(f"Failed to complete trivia {trivia_name}: {result.message}")
                    # Continue to next trivia
                    continue
            
            logger.info("No available trivias found")
            return ActionResult.failure_result("No available trivias found")
            
        except Exception as e:
            logger.error(f"Error finding and completing trivia: {e}")
            return ActionResult.failure_result(f"Failed to find and complete trivia: {e}", error=e)
    
    
    def _complete_single_trivia(self, trivia_name: str) -> ActionResult:
        """Complete all questions in a single trivia until finished"""
        try:
            logger.info(f"Starting completion of trivia: {trivia_name}")
            question_count = 0
            
            max_questions = 12  # Limit to 12 questions maximum
            while question_count < max_questions:
                question_count += 1
                logger.info(f"\nProcessing question {question_count} for {trivia_name}")
                
                # Extract question text using clipboard with retry logic
                question_extracted = False
                max_retries = 5
                retry_count = 0
                
                while not question_extracted and retry_count < max_retries:
                    retry_count += 1
                    logger.info(f"Attempting to extract question {question_count} (attempt {retry_count}/{max_retries})")
                    
                    result = self._extract_trivia_content(question_count)
                    
                    # Special check: If extraction failed because we found the reward button, stop immediately
                    if not result.success and "Trivia completed" in result.message:
                        logger.info("Trivia completion detected during question extraction")
                        question_extracted = False # Ensure loop breaks correctly
                        break 

                    if not result.success:
                        logger.warning(f"Failed to extract question {question_count} on attempt {retry_count}: {result.message}")
                        if retry_count < max_retries:
                            logger.info(f"Sleeping for 0.5 second before retry {retry_count + 1}...")
                            time.sleep(0.5)
                        continue
                    
                    question_text = result.data.get('question_text', 'N/A')
                    
                    # Check if we got a valid question (not empty, not "N/A", not just whitespace)
                    if question_text and question_text != 'N/A' and len(question_text.strip()) > 0:
                        # Clean up question text if it captured the first answer (newline present)
                        if '\n' in question_text:
                            question_text = question_text.split('\n')[0].strip()
                        if '\r' in question_text:
                            question_text = question_text.split('\r')[0].strip()
                            
                        logger.info(f"Question {question_count}: {question_text}")
                        question_extracted = True
                    else:
                        logger.warning(f"Invalid question text extracted on attempt {retry_count}: '{question_text}'")
                        if retry_count < max_retries:
                            logger.info(f"Sleeping for 0.5 second before retry {retry_count + 1}...")
                            time.sleep(0.5)
                        continue
                
                # If we couldn't extract a valid question after all retries
                if not question_extracted:
                    # Check if it was because of completion
                    if "Trivia completed" in result.message:
                        logger.info("Trivia completed confirmed")
                        break
                        
                    logger.warning(f"Failed to extract valid question {question_count} after {max_retries} attempts")
                    # Check if we've reached the end of the trivia
                    banner_result = self._check_trivia_banner_present()
                    if not banner_result.success:
                        logger.info(f"Trivia {trivia_name} appears to be complete (no more questions)")
                        break
                    continue
                
                # Match question to answer in database
                answer = self._find_answer_for_question(trivia_name, question_text)
                if not answer:
                    logger.warning(f"No answer found for question {question_count}: {question_text}")
                    # Still try to continue to next question
                    time.sleep(2.0)
                    continue
                
                logger.info(f"Answer: {answer}")
                
                # Wait for answers to populate (they load one by one)
                # The animation takes a moment, and reading too early results in empty text
                logger.info("Waiting for answer choices to fully load...")
                time.sleep(1.0)
                
                # Find and click the correct answer option
                question_position = result.data.get('question_position', (0, 0))
                self._find_and_click_correct_answer(question_position, answer, question_text)
                
                # Wait for and click submit answer button
                submit_result = self._interact_with_element("SUBMIT_BUTTON", action="click")
                if not submit_result.success:
                    logger.warning(f"Failed to find submit answer button for question {question_count}")
                    # Still continue to next question
                    time.sleep(2.0)
                    continue
                
                # Reset mouse position by moving up 50 pixels
                current_x, current_y = pyautogui.position()
                pyautogui.moveTo(current_x, current_y - 50)

                logger.info(f"Successfully submitted answer for question {question_count}")
                
                # Wait for submit button to disappear, indicating transition to next question
                disappear_result = self._interact_with_element("SUBMIT_BUTTON", action="wait_disappear")
                if not disappear_result.success:
                    logger.warning(f"Submit button did not disappear after question {question_count}, but continuing...")
                
                # Check completion based on question count
                if question_count >= 12:
                    logger.info("12 questions completed. Expecting reward page...")
                    break
                
                # Add a delay to allow the next question to load
                logger.info("Waiting for transition...")
                time.sleep(1.0)
                
                # We used to check for reward button here, but now we rely strictly on count
                # to avoid false positives.
            
            # Check if we reached the maximum questions limit
            if question_count >= max_questions:
                logger.info(f"Reached maximum questions limit ({max_questions}) for {trivia_name}")
            
            # After the loop ends, handle reward claiming
            logger.info(f"Trivia {trivia_name} completed with {question_count} questions - starting reward claiming")
            reward_result = self._handle_reward_claiming()
            if reward_result.success:
                logger.info("Reward claiming completed successfully")
            else:
                logger.warning(f"Reward claiming failed: {reward_result.message}")
            
            logger.info(f"Completed trivia {trivia_name} with {question_count} questions")
            return ActionResult.success_result(f"Completed trivia {trivia_name} with {question_count} questions")
            
        except Exception as e:
            logger.error(f"Error completing trivia {trivia_name}: {e}")
            return ActionResult.failure_result(f"Failed to complete trivia {trivia_name}: {e}", error=e)
    
    def _check_trivia_banner_present(self) -> ActionResult:
        """Check if the trivia banner is present to determine if trivia is available"""
        try:
            return self._interact_with_element("TRIVIA_BANNER", action="wait")
        except Exception as e:
            logger.error(f"Error checking trivia banner: {e}")
            return ActionResult.failure_result(f"Failed to check trivia banner: {e}", error=e)
    
    
    
    def _extract_trivia_content(self, current_question_num: int = 0) -> ActionResult:
        """Extract question from the trivia page using template detection and mouse positioning"""
        try:
            self.current_question_count = current_question_num
            
            # Wait for trivia banner to appear with retry logic
            max_attempts = 15  # 15 seconds max wait time
            attempt = 0
            
            while attempt < max_attempts:
                attempt += 1
                
                # Look for trivia banner using template matching
                banner_criteria = ElementSearchCriteria(
                    name="Trivia Banner",
                    element_type=ElementType.BUTTON,
                    detection_methods=[DetectionMethod.TEMPLATE],
                    confidence_threshold=AutomationConstants.TRIVIA_CONFIDENCE_THRESHOLD,
                    template_path=config.get_trivia_template_path(AssetPaths.TriviaTemplates.TRIVIA_BANNER)
                )
                
                # Try to find the trivia banner
                banner_element = self.ui_detector.find_element(banner_criteria)
                
                if banner_element:
                    # Calculate question position (45 pixels down from banner center)
                    center = banner_element.center
                    question_x = center.x
                    question_y = center.y + 45
                    
                    # Extract text from the question position
                    question_text = self._copy_text_from_position(question_x, question_y)
                    
                    # Check if we got a valid question text (not empty and not just whitespace)
                    if question_text and len(question_text.strip()) > 0:
                        return ActionResult.success_result("Question text extracted", data={
                            'question_position': (center.x, question_y),
                            'question_text': question_text
                        })
                    else:
                        logger.warning(f"Empty question text extracted on attempt {attempt}, retrying...")
                        time.sleep(1)
                        continue
                else:
                    logger.info(f"Trivia banner not found on attempt {attempt}, waiting 1 second...")
                    time.sleep(1)
            
            # If we get here, banner was not found after all attempts
            logger.warning("Could not find trivia banner after all attempts - using fallback positioning")
            # Fallback to center screen positioning
            screen_width, screen_height = pyautogui.size()
            center_x = screen_width // 2
            center_y = screen_height // 2
            pyautogui.moveTo(center_x, center_y)
            logger.info(f"Fallback: Moved mouse to screen center: ({center_x}, {center_y})")
            
            return ActionResult.success_result("Mouse positioned at fallback location", data={
                'question_position': (center_x, center_y)
            })
            
        except Exception as e:
            logger.error(f"Error positioning mouse for question extraction: {e}")
            return ActionResult.failure_result(f"Failed to position mouse: {e}", error=e)
    
    def _find_answer_for_question(self, trivia_name: str, question_text: str) -> str:
        """Find the answer for a given question in the trivia database"""
        try:
            if trivia_name not in self.trivia_database:
                logger.warning(f"Trivia {trivia_name} not found in database")
                return None
            
            trivia_data = self.trivia_database[trivia_name]
            questions = trivia_data.get('questions', {})
            
            # Try exact match first
            if question_text in questions:
                return questions[question_text]
            
            # Try partial match (in case of slight differences)
            for db_question, answer in questions.items():
                # Check if the extracted question contains key parts of the database question
                if self._questions_match(question_text, db_question):
                    logger.info(f"Partial match found for question")
                    return answer
            
            logger.warning(f"No match found for question: {question_text}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding answer for question: {e}")
            return None
    
    def _questions_match(self, extracted_question: str, database_question: str) -> bool:
        """Check if two questions match (handles slight variations)"""
        try:
            # Convert to lowercase for comparison
            extracted_lower = extracted_question.lower().strip()
            database_lower = database_question.lower().strip()
            
            # Remove common punctuation and extra spaces
            import re
            extracted_clean = re.sub(r'[^\w\s]', ' ', extracted_lower)
            database_clean = re.sub(r'[^\w\s]', ' ', database_lower)
            
            # Remove extra whitespace
            extracted_clean = re.sub(r'\s+', ' ', extracted_clean).strip()
            database_clean = re.sub(r'\s+', ' ', database_clean).strip()
            
            # Check if they're the same
            if extracted_clean == database_clean:
                return True
            
            # Check if extracted question contains most of the database question
            # (useful for cases where OCR might miss some words)
            database_words = set(database_clean.split())
            extracted_words = set(extracted_clean.split())
            
            # If extracted question contains at least 80% of the database question words
            if len(database_words) > 0:
                match_ratio = len(database_words.intersection(extracted_words)) / len(database_words)
                if match_ratio >= 0.8:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error comparing questions: {e}")
            return False

    def _copy_text_from_position(self, x, y):
        """Move mouse to position, triple-click, and copy text to clipboard"""
        pyautogui.moveTo(x, y)
        time.sleep(0.1)  # Delay after moving mouse
        pyautogui.tripleClick()
        time.sleep(0.1)  # Delay after selection
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.1)  # Delay after copying
        return pyperclip.paste().strip()

    def _click_answer_checkbox(self, answer_x, answer_y, answer_text):
        """Click the checkbox for an answer option (30 pixels to the left of answer text)"""
        checkbox_x = answer_x - 30
        pyautogui.moveTo(checkbox_x, answer_y)
        pyautogui.click(checkbox_x, answer_y)
        logger.info(f"Checked correct answer: {answer_text}")

    def _find_and_click_correct_answer(self, question_position, correct_answer, question_text):
        """Find the correct answer option and click its checkbox using individual position checks"""
        try:
            question_x, question_y = question_position
            
            # Order of answer positions to check
            answer_keys = ['first', 'second', 'third', 'fourth']
            
            # Track accumulated Y adjustment for offset handling
            # This persists across iterations (e.g. if set for 'first', it applies to 'second', 'third', etc.)
            current_y_adjustment = 0
            
            for key in answer_keys:
                pos = ANSWER_POSITIONS[key]
                logger.info(f"Checking {key} answer option...")
                
                # Calculate coordinates with current adjustment
                answer_x = question_x + pos['x']
                base_y = question_y + pos['y']
                target_y = base_y + current_y_adjustment
                
                # Copy text
                answer_text = self._copy_text_from_position(answer_x, target_y)
                
                # Special Handling: Check for offsets based on specific keys
                
                # Case 1: First answer offset (Question wrapping pushes everything down)
                if key == 'first' and (answer_text == '' or answer_text == 'Next Question!'):
                    logger.info("First answer position is off - copied question/empty instead of answer, adjusting Y position by 30px")
                    offset = 30
                    current_y_adjustment += offset
                    target_y += offset # Apply to current check immediately
                    
                    # Retry reading with new adjustment
                    answer_text = self._copy_text_from_position(answer_x, target_y)
                
                # Case 2: Third answer offset (First row answers wrapping pushes second row down)
                # Note: 'Next Question!' check is likely capturing a button below the answers
                elif key == 'third' and (answer_text == '' or answer_text == 'Next Question!'):
                    logger.info("Third answer position is off - copied question/button, adjusting Y position by additional 20px")
                    offset = 20
                    current_y_adjustment += offset
                    target_y += offset # Apply to current check immediately
                    
                    # Retry reading with new adjustment
                    answer_text = self._copy_text_from_position(answer_x, target_y)
                
                logger.info(f"{key.capitalize()} answer text: {answer_text}")
                
                # Check if matches
                if self._answers_match(answer_text, correct_answer):
                    logger.info(f"Found Correct Answer: {answer_text}")
                    self._click_answer_checkbox(answer_x, target_y, answer_text)
                    return
                else:
                    logger.info(f"[WRONG] Not the correct answer: {answer_text}")
            
            logger.warning("Could not find the correct answer among the options")
            
        except Exception as e:
            logger.error(f"Error finding correct answer: {e}")
    
    def _answers_match(self, extracted_answer, correct_answer):
        """Check if the extracted answer matches the correct answer"""
        try:
            # Convert to lowercase for comparison
            extracted_lower = extracted_answer.lower().strip()
            correct_lower = correct_answer.lower().strip()
            
            # First try exact match
            if extracted_lower == correct_lower:
                return True
            
            # Clean both answers by removing all punctuation and extra spaces
            import re
            extracted_clean = re.sub(r'[^\w\s]', ' ', extracted_lower)
            correct_clean = re.sub(r'[^\w\s]', ' ', correct_lower)
            
            # Remove extra whitespace
            extracted_clean = re.sub(r'\s+', ' ', extracted_clean).strip()
            correct_clean = re.sub(r'\s+', ' ', correct_clean).strip()
            
            # Check if they're the same after cleaning
            if extracted_clean == correct_clean:
                return True
            
            # Check if extracted answer contains most of the correct answer words
            correct_words = set(correct_clean.split())
            extracted_words = set(extracted_clean.split())
            
            # If extracted answer contains at least 80% of the correct answer words
            if len(correct_words) > 0:
                match_ratio = len(correct_words.intersection(extracted_words)) / len(correct_words)
                if match_ratio >= 0.8:
                    return True
            
            # Special handling for common unicode/punctuation issues
            # Handle apostrophes and other common unicode characters
            extracted_normalized = extracted_lower.replace("'", "").replace("'", "").replace("'", "")
            correct_normalized = correct_lower.replace("'", "").replace("'", "").replace("'", "")
            
            if extracted_normalized == correct_normalized:
                return True
            
            # Clean normalized versions
            extracted_norm_clean = re.sub(r'[^\w\s]', ' ', extracted_normalized)
            correct_norm_clean = re.sub(r'[^\w\s]', ' ', correct_normalized)
            extracted_norm_clean = re.sub(r'\s+', ' ', extracted_norm_clean).strip()
            correct_norm_clean = re.sub(r'\s+', ' ', correct_norm_clean).strip()
            
            if extracted_norm_clean == correct_norm_clean:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error comparing answers: {e}")
            return False
    
    
    def _handle_reward_claiming(self) -> ActionResult:
        """Handle the reward claiming process after trivia completion"""
        try:
            logger.info("Starting reward claiming process...")
            
            # Wait for and click the first claim reward button
            result = self._interact_with_element("CLAIM_REWARD_1", action="click")
            if not result.success:
                return result
            
            # Wait for and click the second claim reward button
            result = self._interact_with_element("CLAIM_REWARD_2", action="click")
            if not result.success:
                return result
            
            # Wait for take another quiz button to confirm reward flow is complete
            wait_result = self._interact_with_element("TAKE_ANOTHER_QUIZ", action="wait")
            if not wait_result.success:
                logger.warning(f"Take another quiz button did not appear: {wait_result.message}")
            
            logger.info("Reward claiming process completed successfully")
            return ActionResult.success_result("Reward claiming completed successfully")
            
        except Exception as e:
            logger.error(f"Error in reward claiming process: {e}")
            return ActionResult.failure_result(f"Reward claiming failed: {e}", error=e)
    
    