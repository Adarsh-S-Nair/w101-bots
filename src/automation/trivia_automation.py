"""
Trivia automation module for Wizard101 trivia bot
Handles browser navigation and trivia-specific tasks
"""
import subprocess
import sys
from urllib.parse import urlparse
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
from src.utils.trivia_matching import normalize_text, find_answer
from src.utils.foreground_browser import is_chrome_foreground
from src.utils.trivia_auth import try_auto_login

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
        """Run once, stopping on uncertain state and always finalizing tracking."""
        execution_id = self.execution_tracker.start_execution()["execution_id"]
        completed, skipped = set(), set()
        outcome = ActionResult.failure_result("Run interrupted before completion")
        try:
            for step in (self._open_chrome,
                         lambda: self._interact_with_element("W101_LOGO", action="wait"),
                         self._handle_login_if_needed):
                outcome = step()
                if not outcome.success:
                    return outcome
            if not self.trivia_database:
                outcome = ActionResult.failure_result("Trivia database is empty")
                return outcome
            for _ in range(len(self.trivia_database)):
                outcome = self._find_and_complete_single_trivia(completed, skipped)
                if not outcome.success:
                    return outcome
                if (outcome.data or {}).get("exhausted"):
                    break
                name = (outcome.data or {}).get("trivia_name")
                if not name or name in completed:
                    outcome = ActionResult.failure_result("No new verified quiz result; stopping")
                    return outcome
                completed.add(name)
            outcome = ActionResult.success_result(
                f"Finished: {len(completed)} quiz flows confirmed, {len(skipped)} already unavailable",
                data={"completed_trivias": sorted(completed), "skipped_trivias": sorted(skipped)})
            return outcome
        except (KeyboardInterrupt, SystemExit):
            outcome = ActionResult.failure_result("Trivia run interrupted")
            raise
        except Exception as error:
            logger.error("Trivia run stopped (%s)", type(error).__name__)
            outcome = ActionResult.failure_result("Trivia run stopped due to an unexpected error")
            return outcome
        finally:
            self.execution_tracker.complete_execution(
                execution_id=execution_id, success=outcome.success,
                trivia_count=len(completed),
                execution_summary={"message": outcome.message,
                                   "completed_trivias_list": sorted(completed),
                                   "skipped_trivias": len(skipped)})

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
        """Try verified UIA auto-login, otherwise offer an explicit manual fallback."""
        auth = try_auto_login(config.USERNAME, config.PASSWORD)
        if auth["authenticated"]:
            return ActionResult.success_result("Account sign-in verified through accessibility",
                                               data={"authentication_source": "verified_uia"})
        logger.info("Automatic sign-in unavailable or unconfirmed (%s); manual fallback required", auth["reason"])
        blocked = ActionResult.failure_result(
            "Manual login confirmation required; automatic sign-in did not confirm success",
            data={"needs_human": True, "authenticated": False})
        if not sys.stdin.isatty():
            return blocked
        print("\nSign in yourself in Chrome at https://www.wizard101.com/game/trivia.")
        print("Confirm your intended account is visibly signed in and no CAPTCHA or verification is pending.")
        print("Then return here and type READY. After Enter, you have 5 seconds to focus that Chrome tab.")
        print("Do not type a username or password here. Any other response cancels.")
        try:
            if input("Confirmation: ").strip() != "READY":
                return blocked
        except EOFError:
            return blocked
        time.sleep(5)
        if not self._foreground_is_trivia_page():
            return ActionResult.failure_result(
                "Foreground page is not the approved Wizard101 trivia page; stopped",
                data={"needs_human": True, "authenticated": False})
        login_criteria = ElementSearchCriteria(
            name="Login Button", element_type=ElementType.BUTTON,
            detection_methods=[DetectionMethod.TEMPLATE],
            confidence_threshold=AutomationConstants.TRIVIA_CONFIDENCE_THRESHOLD,
            template_path=config.get_trivia_template_path(AssetPaths.TriviaTemplates.LOGIN_BUTTON))
        if self.ui_detector.find_element(login_criteria):
            return blocked
        return ActionResult.success_result(
            "Operator confirmed signed-in account; foreground trivia URL checked",
            data={"authentication_source": "operator_confirmation", "url_verified": True})

    def _foreground_is_trivia_page(self) -> bool:
        """Read only the address bar, never page credentials or session cookies."""
        if not is_chrome_foreground():
            return False
        previous_clipboard = pyperclip.paste()
        try:
            pyperclip.copy("")
            pyautogui.hotkey("ctrl", "l")
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.2)
            url = urlparse(pyperclip.paste().strip())
            return (url.scheme == "https" and url.netloc == "www.wizard101.com"
                    and url.path == "/game/trivia" and not url.query and not url.fragment)
        except Exception:
            return False
        finally:
            pyautogui.press("esc")
            pyperclip.copy(previous_clipboard)

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
        """Never interpret missing UI, errors, or human checks as completed quizzes."""
        for name in self.trivia_database:
            if name in completed_trivias or name in skipped_trivias:
                continue
            result = self._navigate_to_trivia(name)
            if not result.success:
                return result
            result = self._interact_with_element("TRIVIA_BANNER", action="wait")
            if not result.success:
                return ActionResult.failure_result(
                    "Quiz page not recognized. Check login, page layout, or human verification; stopped",
                    data={"needs_human": True, "trivia_name": name})
            result = self._complete_single_trivia(name)
            if not result.success:
                return result
            return ActionResult.success_result("Quiz flow confirmed", data={"trivia_name": name})
        return ActionResult.success_result("All configured quizzes processed", data={"exhausted": True})

    def _complete_single_trivia(self, trivia_name: str) -> ActionResult:
        """Fail closed: no guessing, unchecked submissions, or success on timeout."""
        previous_question = None
        for number in range(1, 13):
            result = self._extract_trivia_content(number)
            if not result.success:
                return result
            data = result.data or {}
            question = data.get("question_text", "").splitlines()
            question = question[0].strip() if question else ""
            normalized = normalize_text(question)
            if not normalized or normalized == previous_question:
                return ActionResult.failure_result("Question empty or unchanged; stopped without submitting")
            previous_question = normalized
            answer = self._find_answer_for_question(trivia_name, question)
            if answer is None:
                return ActionResult.failure_result("Unknown or ambiguous question; manual review needed",
                                                   data={"needs_human": True})
            if "question_position" not in data:
                return ActionResult.failure_result("Question position unavailable")
            time.sleep(1.0)
            if not self._find_and_click_correct_answer(data["question_position"], answer, question):
                return ActionResult.failure_result("Answer option not found; nothing submitted")
            result = self._interact_with_element("SUBMIT_BUTTON", action="click")
            if not result.success:
                return result
            result = self._interact_with_element("SUBMIT_BUTTON", action="wait_disappear")
            if not result.success:
                return ActionResult.failure_result("Answer transition unconfirmed; stopped")
            time.sleep(1.0)
        return self._handle_reward_claiming()

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
            
            return ActionResult.failure_result(
                "Question banner not found; stopped instead of clicking a guessed location",
                data={"needs_human": True})

        except Exception as e:
            logger.error(f"Error positioning mouse for question extraction: {e}")
            return ActionResult.failure_result(f"Failed to position mouse: {e}", error=e)
    
    def _find_answer_for_question(self, trivia_name: str, question_text: str):
        questions = self.trivia_database.get(trivia_name, {}).get("questions", {})
        return find_answer(questions, question_text)

    def _questions_match(self, extracted_question: str, database_question: str) -> bool:
        return bool(normalize_text(extracted_question)) and normalize_text(extracted_question) == normalize_text(database_question)

    def _copy_text_from_position(self, x, y):
        """Move mouse to position, triple-click, and copy text to clipboard"""
        pyautogui.moveTo(x, y)
        time.sleep(0.1)  # Delay after moving mouse
        pyautogui.tripleClick()
        time.sleep(0.1)  # Delay after selection
        pyperclip.copy('')  # Prevent a failed copy from reusing stale clipboard text
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
                    return True
                else:
                    logger.info(f"[WRONG] Not the correct answer: {answer_text}")
            
            logger.warning("Could not find the correct answer among the options")
            return False
            
        except Exception as e:
            logger.error("Error finding correct answer (%s)", type(e).__name__)
            return False
    
    def _answers_match(self, extracted_answer, correct_answer):
        return bool(normalize_text(extracted_answer)) and normalize_text(extracted_answer) == normalize_text(correct_answer)

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
                return ActionResult.failure_result(
                    "Reward flow not confirmed. Complete any human verification manually; stopped",
                    data={"needs_human": True, "reward_verified": False})
            
            logger.info("Reward flow completed; currency balance was not independently verified")
            return ActionResult.success_result("Reward flow completed; balance unverified", data={"reward_flow_confirmed": True, "reward_balance_verified": False})
            
        except Exception as e:
            logger.error(f"Error in reward claiming process: {e}")
            return ActionResult.failure_result(f"Reward claiming failed: {e}", error=e)
    
    