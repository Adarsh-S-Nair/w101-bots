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
from config import config
from src.constants import AssetPaths, AutomationConstants

# Constants for answer positions (pixels to move from question area)
ANSWER_POSITIONS = {
    'first': {'x': -200, 'y': 50},    # First answer option
    'second': {'x': 80, 'y': 50},     # Second answer option  
    'third': {'x': -200, 'y': 90},    # Third answer option
    'fourth': {'x': 80, 'y': 90}      # Fourth answer option
}


class TriviaAutomation(AutomationBase):
    """Automation module for Wizard101 trivia bot"""
    
    def __init__(self, ui_detector):
        super().__init__(ui_detector)
        self.name = "Trivia Automation"
        self.screenshot_manager = ScreenshotManager()
        self.trivia_database = self._load_trivia_database()
    
    def _create_trivia_button_criteria(self, button_name: str, template_filename: str) -> ElementSearchCriteria:
        """Helper to create ElementSearchCriteria for a trivia button template"""
        return ElementSearchCriteria(
            name=button_name,
            element_type=ElementType.BUTTON,
            template_path=config.get_trivia_template_path(template_filename),
            confidence_threshold=AutomationConstants.TRIVIA_CONFIDENCE_THRESHOLD,
            detection_methods=[DetectionMethod.TEMPLATE]
        )
    
    def _wait_and_click_trivia_button(self, button_name: str, template_filename: str, 
                                      timeout: float = 15.0, post_click_delay: float = 1.0) -> ActionResult:
        """Helper to wait for a trivia button to appear and click it"""
        logger.info(f"Waiting for {button_name} to appear...")
        
        criteria = self._create_trivia_button_criteria(button_name, template_filename)
        result = self.wait_for_element(criteria, timeout=timeout, check_interval=0.5)
        
        if result.success:
            logger.info(f"{button_name} found")
            click_result = self.find_and_click(criteria, wait_time=1.0, retries=2)
            
            if click_result.success:
                if post_click_delay > 0:
                    time.sleep(post_click_delay)
                return ActionResult.success_result(f"{button_name} clicked successfully")
            else:
                logger.error(f"Failed to click {button_name}")
                return ActionResult.failure_result(f"Failed to click {button_name}")
        else:
            logger.warning(f"{button_name} did not appear within timeout period")
            return ActionResult.failure_result(f"{button_name} not found within timeout")
    
    def _wait_for_trivia_button(self, button_name: str, template_filename: str, 
                                timeout: float = 15.0, post_wait_delay: float = 0.0) -> ActionResult:
        """Helper to wait for a trivia button to appear (without clicking)"""
        logger.info(f"Waiting for {button_name} to appear...")
        
        criteria = self._create_trivia_button_criteria(button_name, template_filename)
        result = self.wait_for_element(criteria, timeout=timeout, check_interval=0.5)
        
        if result.success:
            logger.info(f"{button_name} found")
            if post_wait_delay > 0:
                time.sleep(post_wait_delay)
            return ActionResult.success_result(f"{button_name} found")
        else:
            logger.warning(f"{button_name} did not appear within timeout period")
            return ActionResult.failure_result(f"{button_name} not found within timeout")
    
    def execute(self) -> ActionResult:
        """Execute trivia automation workflow"""
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
                    
                    # Navigate to main trivia page
                    result = self._navigate_to_main_trivia_page()
                    if not result.success:
                        logger.error(f"Failed to navigate to main trivia page: {result.message}")
                        return result
                    
                    # Wait for W101 logo to confirm we're on the site
                    result = self._wait_for_w101_logo()
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
                time.sleep(2.0)
            
            logger.info(f"Trivia automation completed successfully. Total trivias completed: {len(completed_trivias)}")
            return ActionResult.success_result(f"Trivia automation completed successfully. Total trivias completed: {len(completed_trivias)}")
            
        except Exception as e:
            logger.error(f"Error in trivia automation: {e}")
            return ActionResult.failure_result(f"Trivia automation failed: {e}", error=e)
    
    def _open_chrome(self) -> ActionResult:
        """Open Chrome browser"""
        try:
            logger.info("Opening Chrome browser...")
            
            # Try different methods to open Chrome
            chrome_opened = False
            
            # Method 1: Try to open with default profile
            try:
                subprocess.Popen(["start", "chrome", "--profile-directory=Default"], shell=True)
                chrome_opened = True
                logger.info("Chrome opened with default profile")
            except Exception as e:
                logger.warning(f"Failed to open Chrome with default profile: {e}")
            
            # Method 2: Try opening without profile specification
            if not chrome_opened:
                try:
                    subprocess.Popen(["start", "chrome"], shell=True)
                    chrome_opened = True
                    logger.info("Chrome opened without profile specification")
                except Exception as e:
                    logger.warning(f"Failed to open Chrome without profile: {e}")
            
            # Method 3: Fallback to direct chrome.exe
            if not chrome_opened:
                try:
                    subprocess.Popen(["chrome.exe"])
                    chrome_opened = True
                    logger.info("Chrome opened successfully (fallback method)")
                except Exception as e:
                    logger.error(f"Failed to open Chrome with all methods: {e}")
                    return ActionResult.failure_result(f"Could not open Chrome browser: {e}")
            
            # Wait for Chrome to open by looking for Google search icon
            result = self._wait_for_chrome_load()
            if not result.success:
                return result
            
            return ActionResult.success_result("Chrome browser opened successfully")
            
        except Exception as e:
            logger.error(f"Error opening Chrome: {e}")
            return ActionResult.failure_result(f"Failed to open Chrome: {e}", error=e)
    
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
            time.sleep(0.5)
            
            # Type the URL
            pyautogui.write(trivia_url)
            time.sleep(0.5)
            
            # Press Enter to navigate
            pyautogui.press('enter')
            
            logger.info(f"Navigated to: {trivia_url}")
            
            # Wait for page to load and take screenshot
            time.sleep(2)
            screenshot = self.screenshot_manager.take_screenshot()
            if screenshot is not None:
                self.screenshot_manager.save_screenshot(screenshot, "trivia_page_loaded")
            
            return ActionResult.success_result(f"Successfully navigated to {trivia_name or 'main trivia'} page")
            
        except Exception as e:
            logger.error(f"Error navigating to trivia page: {e}")
            return ActionResult.failure_result(f"Failed to navigate to trivia page: {e}", error=e)
    
    def _navigate_to_main_trivia_page(self) -> ActionResult:
        """Navigate to the main trivia page"""
        try:
            logger.info("Navigating to main trivia page...")
            
            # Take a screenshot of current state
            screenshot = self.screenshot_manager.take_screenshot()
            if screenshot is not None:
                self.screenshot_manager.save_screenshot(screenshot, "chrome_before_main_trivia_navigation")
            
            # Navigate to the main trivia page
            main_trivia_url = "https://www.wizard101.com/game/trivia"
            
            # Use pyautogui to navigate to the URL
            import pyautogui
            
            # Click on address bar (Ctrl+L)
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.5)
            
            # Type the URL
            pyautogui.write(main_trivia_url)
            time.sleep(0.5)
            
            # Press Enter to navigate
            pyautogui.press('enter')
            
            logger.info(f"Navigated to: {main_trivia_url}")
            
            # Wait for page to load and take screenshot
            time.sleep(2)
            screenshot = self.screenshot_manager.take_screenshot()
            if screenshot is not None:
                self.screenshot_manager.save_screenshot(screenshot, "main_trivia_page_loaded")
            
            return ActionResult.success_result("Successfully navigated to main trivia page")
            
        except Exception as e:
            logger.error(f"Error navigating to main trivia page: {e}")
            return ActionResult.failure_result(f"Failed to navigate to main trivia page: {e}", error=e)
    
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
            time.sleep(0.2)
            pyautogui.press('delete')  # Delete selected text
            time.sleep(0.2)
            
            # Type the username with visible typing
            pyautogui.write(username, interval=0.05)  # 50ms between keystrokes
            time.sleep(0.5)
            
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
            time.sleep(0.2)
            pyautogui.press('delete')  # Delete selected text
            time.sleep(0.2)
            
            # Type the password with visible typing
            pyautogui.write(password, interval=0.05)  # 50ms between keystrokes
            time.sleep(0.5)
            
            logger.info("Password entered successfully")
            
            # Press Enter to submit login form
            logger.info("Pressing Enter to submit login form...")
            pyautogui.press('enter')
            time.sleep(1.0)  # Wait for login to process
            
            logger.info("Login form submitted")
            return ActionResult.success_result("Password entered and login form submitted")
            
        except Exception as e:
            logger.error(f"Error entering password: {e}")
            return ActionResult.failure_result(f"Failed to enter password: {e}", error=e)
    
    def _load_trivia_database(self) -> dict:
        """Load trivia database from YAML file"""
        try:
            trivia_db_path = "trivia_database.yaml"
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
                result = self._check_trivia_banner_present()
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
            
            while True:
                question_count += 1
                logger.info(f"Processing question {question_count} for {trivia_name}")
                
                # Extract question text using clipboard
                result = self._extract_trivia_content()
                if not result.success:
                    logger.warning(f"Failed to extract question {question_count}: {result.message}")
                    # Check if we've reached the end of the trivia
                    banner_result = self._check_trivia_banner_present()
                    if not banner_result.success:
                        logger.info(f"Trivia {trivia_name} appears to be complete (no more questions)")
                        break
                    continue
                
                question_text = result.data.get('question_text', 'N/A')
                logger.info(f"Question {question_count}: {question_text}")
                
                # Match question to answer in database
                answer = self._find_answer_for_question(trivia_name, question_text)
                if answer:
                    logger.info(f"Answer: {answer}")
                    
                    # Find and click the correct answer option
                    question_position = result.data.get('question_position', (0, 0))
                    self._find_and_click_correct_answer(question_position, answer, question_text)
                    
                    # Wait for and click submit answer button
                    submit_result = self._wait_for_submit_answer_button()
                    if submit_result.success:
                        logger.info(f"Successfully submitted answer for question {question_count}")
                        
                        # Wait for trivia banner to appear after submission
                        banner_result = self._wait_for_trivia_banner_after_submit()
                        if not banner_result.success:
                            logger.info(f"Trivia banner not found after question {question_count} - trivia completed, starting reward claiming")
                            # Start reward claiming flow
                            reward_result = self._handle_reward_claiming()
                            if reward_result.success:
                                logger.info("Reward claiming completed successfully")
                            else:
                                logger.warning(f"Reward claiming failed: {reward_result.message}")
                            break
                        else:
                            logger.info("Trivia banner found - continuing to next question")
                    else:
                        logger.warning(f"Failed to find submit answer button for question {question_count}")
                        # Still continue to next question
                        time.sleep(2.0)
                else:
                    logger.warning(f"No answer found for question {question_count}: {question_text}")
                    # Still try to continue to next question
                    time.sleep(2.0)
            
            logger.info(f"Completed trivia {trivia_name} with {question_count} questions")
            return ActionResult.success_result(f"Completed trivia {trivia_name} with {question_count} questions")
            
        except Exception as e:
            logger.error(f"Error completing trivia {trivia_name}: {e}")
            return ActionResult.failure_result(f"Failed to complete trivia {trivia_name}: {e}", error=e)
    
    def _check_trivia_banner_present(self) -> ActionResult:
        """Check if the trivia banner is present to determine if trivia is available"""
        try:
            return self._wait_for_trivia_button(
                "Trivia Banner",
                AssetPaths.TriviaTemplates.TRIVIA_BANNER,
                timeout=1.5
            )
        except Exception as e:
            logger.error(f"Error checking trivia banner: {e}")
            return ActionResult.failure_result(f"Failed to check trivia banner: {e}", error=e)
    
    
    
    def _extract_trivia_content(self) -> ActionResult:
        """Extract question from the trivia page using template detection and mouse positioning"""
        try:
            
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
                    
                    # Move mouse to banner center
                    center = banner_element.center
                    pyautogui.moveTo(center.x, center.y)
                    
                    # Move mouse 45 pixels down from banner
                    question_y = center.y + 45
                    pyautogui.moveTo(center.x, question_y)
                    
                    # Triple-click to select the whole question text
                    pyautogui.tripleClick()
                    time.sleep(0.2)  # Small delay for selection
                    
                    # Copy to clipboard
                    pyautogui.hotkey('ctrl', 'c')
                    time.sleep(0.2)  # Small delay for clipboard
                    
                    # Get text from clipboard
                    question_text = pyperclip.paste()
                    # Clean up any newline characters at the end
                    question_text = question_text.strip()
                    
                    return ActionResult.success_result("Question text extracted", data={
                        'question_position': (center.x, question_y),
                        'question_text': question_text
                    })
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
    
    def _wait_for_chrome_load(self) -> ActionResult:
        """Wait for Chrome to load by looking for Google search icon"""
        try:
            return self._wait_for_trivia_button(
                "Google Search Icon",
                AssetPaths.TriviaTemplates.GOOGLE_SEARCH_ICON,
                timeout=20.0
            )
        except Exception as e:
            logger.error(f"Error waiting for Chrome load: {e}")
            return ActionResult.failure_result(f"Failed to wait for Chrome load: {e}", error=e)
    
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
    
    def _check_answer_options(self, question_position):
        """Move mouse to each answer option and extract text"""
        try:
            logger.info("Moving mouse to each answer option...")
            
            question_x, question_y = question_position
            
            # Check each answer option
            for option_name, offset in ANSWER_POSITIONS.items():
                logger.info(f"Checking {option_name} answer option...")
                
                # Calculate position for this answer option
                answer_x = question_x + offset['x']
                answer_y = question_y + offset['y']
                
                # Move mouse to answer option
                pyautogui.moveTo(answer_x, answer_y)
                
                # Triple-click to select the answer text
                pyautogui.tripleClick()
                time.sleep(0.2)  # Small delay for selection
                
                # Copy to clipboard
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.2)  # Small delay for clipboard
                
                # Get text from clipboard
                answer_text = pyperclip.paste().strip()
                logger.info(f"{option_name.capitalize()} answer text: {answer_text}\n")
                
                # Move mouse 30 pixels to the left to click the checkbox
                checkbox_x = answer_x - 30
                pyautogui.moveTo(checkbox_x, answer_y)
                
                # Click the checkbox
                pyautogui.click(checkbox_x, answer_y)
                logger.info(f"Clicked checkbox for {option_name} answer")
                
                # Reset mouse back to question position
                pyautogui.moveTo(question_x, question_y)
                
                # Add delay between answer choices to prevent text mixing
                time.sleep(0.2)
            
        except Exception as e:
            logger.error(f"Error checking answer options: {e}")
    
    def _detect_question_wrapping(self, question_position):
        """Detect if the question text wraps using character width estimation"""
        try:
            question_x, question_y = question_position
            
            # Get the question text from clipboard (should already be available)
            question_text = pyperclip.paste().strip()
            
            if not question_text:
                logger.warning("No question text available for width estimation")
                return True, 0
            
            # Character width estimation for Comic Sans font (adjusted for actual font size)
            # Based on your observation: 76 chars with width 54.7 was way over threshold
            # This suggests we need much larger width values
            char_widths = {
                # Wide characters
                'W': 2.0, 'M': 2.0, 'Q': 1.8, '@': 1.8,
                # Medium-wide characters  
                'A': 1.6, 'B': 1.5, 'D': 1.5, 'G': 1.5, 'O': 1.5, 'P': 1.5, 'R': 1.5, 'U': 1.5, 'V': 1.5, 'Y': 1.5,
                'C': 1.4, 'E': 1.4, 'F': 1.4, 'H': 1.4, 'J': 1.4, 'K': 1.4, 'L': 1.4, 'N': 1.4, 'S': 1.4, 'T': 1.4, 'X': 1.4, 'Z': 1.4,
                'I': 0.8, 'l': 0.8,  # Very narrow
                # Lowercase
                'w': 1.8, 'm': 1.6, 'q': 1.4, 'a': 1.2, 'b': 1.2, 'd': 1.2, 'g': 1.2, 'o': 1.2, 'p': 1.2,
                'c': 1.1, 'e': 1.1, 'f': 1.0, 'h': 1.1, 'j': 0.8, 'k': 1.1, 'l': 0.8, 'n': 1.1, 'r': 0.8, 's': 1.0, 't': 1.0, 'u': 1.1, 'v': 1.1, 'x': 1.1, 'y': 1.1, 'z': 1.0,
                'i': 0.7,  # Very narrow
                # Numbers
                '0': 1.4, '1': 0.8, '2': 1.4, '3': 1.4, '4': 1.4, '5': 1.4, '6': 1.4, '7': 1.4, '8': 1.4, '9': 1.4,
                # Punctuation and symbols
                ' ': 0.6, '.': 0.6, ',': 0.6, '!': 0.7, '?': 1.4, ':': 0.7, ';': 0.7, "'": 0.5, '"': 0.8,
                '-': 0.8, '_': 1.1, '=': 1.4, '+': 1.4, '(': 0.8, ')': 0.8, '[': 0.8, ']': 0.8,
                '&': 1.6, '%': 1.6, '$': 1.4, '#': 1.5, '*': 1.1, '/': 0.8, '\\': 0.8, '|': 0.6,
                # Default for unknown characters
                'default': 1.1
            }
            
            # Calculate estimated width
            estimated_width = 0
            for char in question_text:
                if char in char_widths:
                    estimated_width += char_widths[char]
                else:
                    estimated_width += char_widths['default']
            
            # Estimate line width threshold (keep original threshold)
            # You mentioned 69 chars sometimes wraps, 70 chars sometimes doesn't
            # This suggests the threshold is around 69-70 character widths
            line_width_threshold = 69.5  # Conservative threshold
            
            is_single_line = estimated_width <= line_width_threshold
            
            logger.info(f"Question text: '{question_text}' ({len(question_text)} chars)")
            logger.info(f"Estimated width: {estimated_width:.1f} (threshold: {line_width_threshold})")
            logger.info(f"Question appears to be {'single line' if is_single_line else 'wrapped'}")
            
            return not is_single_line, estimated_width
            
        except Exception as e:
            logger.warning(f"Error in character width estimation: {e}")
            return True, 0  # Default to wrapped if detection fails

    def _find_and_click_correct_answer(self, question_position, correct_answer, question_text):
        """Find the correct answer option and click its checkbox"""
        try:
            
            question_x, question_y = question_position
            
            # Detect if question text wraps using visual detection
            is_wrapped, text_height = self._detect_question_wrapping(question_position)
            
            # Adjust Y positions if question text is wrapped
            y_adjustment = 0
            if is_wrapped:
                y_adjustment = 30
                logger.info(f"Question text is wrapped (height: {text_height}px), adjusting answer positions by {y_adjustment} pixels")
            else:
                logger.info(f"Question text is single line (height: {text_height}px), no Y adjustment needed")
            
            # First, check the first two answers to see if any are long
            first_two_answers_long = False
            try:
                # Check first answer length
                first_answer_x = question_x + ANSWER_POSITIONS['first']['x']
                first_answer_y = question_y + ANSWER_POSITIONS['first']['y'] + y_adjustment
                pyautogui.moveTo(first_answer_x, first_answer_y)
                pyautogui.tripleClick()
                time.sleep(0.5)  # Longer delay for selection
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.5)  # Longer delay for clipboard
                first_answer_text = pyperclip.paste().strip()
                # Clean any problematic unicode characters
                first_answer_text = first_answer_text.encode('ascii', 'ignore').decode('ascii')
                
                # Check second answer length
                second_answer_x = question_x + ANSWER_POSITIONS['second']['x']
                second_answer_y = question_y + ANSWER_POSITIONS['second']['y'] + y_adjustment
                pyautogui.moveTo(second_answer_x, second_answer_y)
                pyautogui.tripleClick()
                time.sleep(0.5)  # Longer delay for selection
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.5)  # Longer delay for clipboard
                second_answer_text = pyperclip.paste().strip()
                # Clean any problematic unicode characters
                second_answer_text = second_answer_text.encode('ascii', 'ignore').decode('ascii')
                
                # Check if either of the first two answers is longer than 26 characters
                if len(first_answer_text) > 26 or len(second_answer_text) > 26:
                    first_two_answers_long = True
                    logger.info(f"First two answers are long (first: {len(first_answer_text)} chars, second: {len(second_answer_text)} chars), will adjust last two answer positions")
                
                # Check if first answer is correct
                if self._answers_match(first_answer_text, correct_answer):
                    logger.info(f"[CORRECT] FOUND CORRECT ANSWER: {first_answer_text}")
                    checkbox_x = first_answer_x - 30
                    pyautogui.moveTo(checkbox_x, first_answer_y)
                    pyautogui.click(checkbox_x, first_answer_y)
                    logger.info(f"[CORRECT] Clicked checkbox for correct answer: {first_answer_text}\n")
                    return
                
                # Check if second answer is correct
                if self._answers_match(second_answer_text, correct_answer):
                    logger.info(f"[CORRECT] FOUND CORRECT ANSWER: {second_answer_text}")
                    checkbox_x = second_answer_x - 30
                    pyautogui.moveTo(checkbox_x, second_answer_y)
                    pyautogui.click(checkbox_x, second_answer_y)
                    logger.info(f"[CORRECT] Clicked checkbox for correct answer: {second_answer_text}\n")
                    return
                
                logger.info(f"[WRONG] First answer: {first_answer_text}")
                logger.info(f"[WRONG] Second answer: {second_answer_text}")
                
            except Exception as e:
                logger.warning(f"Could not check first two answer lengths: {e}")
            
            # Now check the last two answers with proper positioning
            for option_name in ['third', 'fourth']:
                logger.info(f"Checking {option_name} answer option...")
                
                offset = ANSWER_POSITIONS[option_name]
                answer_x = question_x + offset['x']
                answer_y = question_y + offset['y'] + y_adjustment
                
                # Add extra Y adjustment for last two answers if first two are long
                if first_two_answers_long:
                    answer_y += 20
                    logger.info(f"Adjusting {option_name} answer position by 20px due to long first two answers")
                
                # Move mouse to answer option
                pyautogui.moveTo(answer_x, answer_y)
                
                # Triple-click to select the answer text
                pyautogui.tripleClick()
                time.sleep(0.5)  # Longer delay for selection
                
                # Copy to clipboard
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.5)  # Longer delay for clipboard
                
                # Get text from clipboard and clean it
                answer_text = pyperclip.paste().strip()
                # Clean any problematic unicode characters
                answer_text = answer_text.encode('ascii', 'ignore').decode('ascii')
                logger.info(f"{option_name.capitalize()} answer text: {answer_text}")
                
                # Check if this is the correct answer
                if self._answers_match(answer_text, correct_answer):
                    logger.info(f"[CORRECT] FOUND CORRECT ANSWER: {answer_text}")
                    
                    # Move mouse 30 pixels to the left to click the checkbox
                    checkbox_x = answer_x - 30
                    pyautogui.moveTo(checkbox_x, answer_y)
                    
                    # Click the checkbox
                    pyautogui.click(checkbox_x, answer_y)
                    logger.info(f"[CORRECT] Clicked checkbox for correct answer: {answer_text}\n")
                    
                    # Stop looking - we found the correct answer
                    return
                else:
                    logger.info(f"[WRONG] Not the correct answer: {answer_text}\n")
                
                    # Reset mouse back to question position
                    pyautogui.moveTo(question_x, question_y)
                    
                    # Small delay before checking next option
                    time.sleep(0.2)
            
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
            result = self._wait_for_claim_reward_button()
            if not result.success:
                return result
            
            # Wait for and click the second claim reward button
            result = self._wait_for_second_claim_reward_button()
            if not result.success:
                return result
            
            logger.info("Reward claiming process completed successfully")
            return ActionResult.success_result("Reward claiming completed successfully")
            
        except Exception as e:
            logger.error(f"Error in reward claiming process: {e}")
            return ActionResult.failure_result(f"Reward claiming failed: {e}", error=e)
    
    def _wait_for_claim_reward_button(self) -> ActionResult:
        """Wait for and click the first claim reward button"""
        try:
            return self._wait_and_click_trivia_button(
                "Claim Your Reward Button",
                AssetPaths.TriviaTemplates.CLAIM_YOUR_REWARD_BUTTON,
                timeout=15.0,
                post_click_delay=2.0
            )
        except Exception as e:
            logger.error(f"Error waiting for claim reward button: {e}")
            return ActionResult.failure_result(f"Failed to wait for claim reward button: {e}", error=e)
    
    def _wait_for_second_claim_reward_button(self) -> ActionResult:
        """Wait for and click the second claim reward button"""
        try:
            result = self._wait_and_click_trivia_button(
                "Second Claim Your Reward Button",
                AssetPaths.TriviaTemplates.SECOND_CLAIM_YOUR_REWARD_BUTTON,
                timeout=15.0,
                post_click_delay=0.0
            )
            
            if result.success:
                # Wait for take another quiz button to confirm reward flow is complete
                wait_result = self._wait_for_take_another_quiz_button()
                if not wait_result.success:
                    logger.warning(f"Take another quiz button did not appear: {wait_result.message}")
            
            return result
                
        except Exception as e:
            logger.error(f"Error waiting for second claim reward button: {e}")
            return ActionResult.failure_result(f"Failed to wait for second claim reward button: {e}", error=e)
    
    def _wait_for_submit_answer_button(self) -> ActionResult:
        """Wait for submit answer button to appear and click it"""
        try:
            return self._wait_and_click_trivia_button(
                "Submit Answer Button",
                AssetPaths.TriviaTemplates.SUBMIT_ANSWER_BUTTON,
                timeout=10.0,
                post_click_delay=0.0
            )
        except Exception as e:
            logger.error(f"Error waiting for submit answer button: {e}")
            return ActionResult.failure_result(f"Failed to wait for submit answer button: {e}", error=e)
    
    def _wait_for_trivia_banner_after_submit(self) -> ActionResult:
        """Wait for trivia banner to appear after submitting an answer (2 second timeout)"""
        try:
            return self._wait_for_trivia_button(
                "Trivia Banner",
                AssetPaths.TriviaTemplates.TRIVIA_BANNER,
                timeout=2.0,
                post_wait_delay=0.5
            )
        except Exception as e:
            logger.error(f"Error waiting for trivia banner after submit: {e}")
            return ActionResult.failure_result(f"Failed to wait for trivia banner after submit: {e}", error=e)
    
    def _wait_for_take_another_quiz_button(self) -> ActionResult:
        """Wait for take another quiz button to appear to confirm reward flow is complete"""
        try:
            return self._wait_for_trivia_button(
                "Take Another Quiz Button",
                AssetPaths.TriviaTemplates.TAKE_ANOTHER_QUIZ_BUTTON,
                timeout=15.0
            )
        except Exception as e:
            logger.error(f"Error waiting for take another quiz button: {e}")
            return ActionResult.failure_result(f"Failed to wait for take another quiz button: {e}", error=e)
    