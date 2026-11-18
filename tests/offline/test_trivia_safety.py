"""Offline tests run actual class methods with all desktop imports excluded.

AST loading prevents importing pyautogui (which opens a display), config (which
loads credentials), or execution trackers (which write history) in this suite.
"""
import ast
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
from src.core.action_result import ActionResult
from src.utils.trivia_matching import normalize_text, find_answer

SOURCE = Path(__file__).resolve().parents[2] / 'src/automation/trivia_automation.py'
tree = ast.parse(SOURCE.read_text())
class_node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'TriviaAutomation')
module = ast.Module(body=[class_node], type_ignores=[])
namespace = dict(try_auto_login=Mock(return_value={'authenticated': False, 'reason': 'test'}), config=Mock(), is_chrome_foreground=Mock(return_value=True), sys=Mock(), AutomationBase=object, ActionResult=ActionResult,
                 normalize_text=normalize_text, find_answer=find_answer,
                 logger=Mock(), time=Mock(), pyautogui=Mock(),
                 ANSWER_POSITIONS={'first': {'x': -200, 'y': 50}, 'second': {'x': 80, 'y': 50},
                                   'third': {'x': -200, 'y': 90}, 'fourth': {'x': 80, 'y': 90}})
exec(compile(module, str(SOURCE), 'exec'), namespace)
TriviaAutomation = namespace['TriviaAutomation']


class MatchingTests(unittest.TestCase):
    def test_unicode_and_whitespace(self):
        self.assertEqual(normalize_text('  Wizard’s\n NAME '), "wizard's name")

    def test_no_subset_match(self):
        self.assertIsNone(find_answer({'Which school does NOT heal?': 'Death'}, 'Which school does heal?'))

    def test_empty_never_matches(self):
        self.assertIsNone(find_answer({'': 'oops'}, ''))

    def test_ambiguous_normalized_question(self):
        self.assertIsNone(find_answer({'Question': 'one', ' question ': 'two'}, 'QUESTION'))

    def test_exact_normalized_match(self):
        self.assertEqual(find_answer({'What’s this?': 'A'}, "WHAT'S  THIS?"), 'A')


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.bot = TriviaAutomation.__new__(TriviaAutomation)
        self.bot.trivia_database = {'quiz': {'questions': {'question': 'answer'}}}
        self.bot.execution_tracker = Mock()
        self.bot.execution_tracker.start_execution.return_value = {'execution_id': 'test'}
        self.bot._open_chrome = Mock(return_value=ActionResult.success_result('open'))
        self.bot._handle_login_if_needed = Mock(return_value=ActionResult.success_result('login'))
        self.bot._interact_with_element = Mock(return_value=ActionResult.success_result('ok'))
        self.bot._extract_trivia_content = Mock(return_value=ActionResult.success_result('text',
            {'question_text': 'question', 'question_position': (100, 100)}))
        self.bot._find_and_click_correct_answer = Mock(return_value=True)
        self.bot._handle_reward_claiming = Mock(return_value=ActionResult.failure_result('human check'))

    def test_failed_open_is_finalized(self):
        self.bot._open_chrome.return_value = ActionResult.failure_result('no browser')
        self.assertFalse(self.bot.execute().success)
        self.assertFalse(self.bot.execution_tracker.complete_execution.call_args.kwargs['success'])
        self.bot.execution_tracker.complete_execution.assert_called_once()

    def test_quiz_failure_not_success(self):
        self.bot._find_and_complete_single_trivia = Mock(return_value=ActionResult.failure_result('challenge'))
        self.assertFalse(self.bot.execute().success)
        self.assertFalse(self.bot.execution_tracker.complete_execution.call_args.kwargs['success'])

    def test_missing_result_data_stops(self):
        self.bot._find_and_complete_single_trivia = Mock(return_value=ActionResult.success_result('unknown'))
        self.assertFalse(self.bot.execute().success)

    def test_exception_finalizes_once(self):
        self.bot._open_chrome.side_effect = RuntimeError('secret should not appear')
        result = self.bot.execute()
        self.assertNotIn('secret', result.message)
        self.bot.execution_tracker.complete_execution.assert_called_once()

    def test_missing_answer_never_submits(self):
        self.bot.trivia_database = {}
        self.assertFalse(self.bot._complete_single_trivia('quiz').success)
        self.bot._interact_with_element.assert_not_called()

    def test_missing_choice_never_submits(self):
        self.bot._find_and_click_correct_answer.return_value = False
        self.assertFalse(self.bot._complete_single_trivia('quiz').success)
        self.bot._interact_with_element.assert_not_called()

    def test_repeated_question_stops(self):
        self.assertFalse(self.bot._complete_single_trivia('quiz').success)
        self.bot._find_and_click_correct_answer.assert_called_once()
        self.bot._handle_reward_claiming.assert_not_called()

    def test_reward_failure_propagates(self):
        self.bot._extract_trivia_content.side_effect = [ActionResult.success_result('q',
            {'question_text': f'q{i}', 'question_position': (0,0)}) for i in range(12)]
        self.bot._find_answer_for_question = Mock(return_value='answer')
        self.assertFalse(self.bot._complete_single_trivia('quiz').success)
        self.bot._handle_reward_claiming.assert_called_once()

    def test_reward_timeout_needs_human(self):
        self.bot._interact_with_element.side_effect = [ActionResult.success_result('a'),
            ActionResult.success_result('b'), ActionResult.failure_result('timeout')]
        result = TriviaAutomation._handle_reward_claiming(self.bot)
        self.assertFalse(result.success)
        self.assertTrue(result.data['needs_human'])

    def test_reward_ui_not_balance_proof(self):
        result = TriviaAutomation._handle_reward_claiming(self.bot)
        self.assertTrue(result.success)
        self.assertFalse(result.data['reward_balance_verified'])

    def test_missing_banner_not_completed(self):
        self.bot._navigate_to_trivia = Mock(return_value=ActionResult.success_result('nav'))
        self.bot._interact_with_element.return_value = ActionResult.failure_result('missing')
        skipped = set()
        result = self.bot._find_and_complete_single_trivia(set(), skipped)
        self.assertFalse(result.success)
        self.assertTrue(result.data['needs_human'])
        self.assertEqual(skipped, set())

    def test_auth_logging_has_no_password_fragment(self):
        source = SOURCE.read_text()
        self.assertNotIn('password[:', source)
        self.assertNotIn('len(password)', source)

if __name__ == '__main__':
    unittest.main()

class AuthenticationAndInterruptTests(unittest.TestCase):
    setUp = WorkflowTests.setUp
    def test_manual_fallback_cannot_type_credentials(self):
        namespace['pyautogui'].reset_mock()
        namespace['sys'].stdin.isatty.return_value = False
        result = TriviaAutomation._handle_login_if_needed(self.bot)
        self.assertFalse(result.success)
        self.assertTrue(result.data['needs_human'])
        self.assertFalse(result.data['authenticated'])
        self.assertEqual(namespace['pyautogui'].mock_calls, [])
        self.assertFalse(hasattr(TriviaAutomation, '_enter_password'))

    def test_interrupt_persisted_as_failure(self):
        self.bot._find_and_complete_single_trivia = Mock(side_effect=KeyboardInterrupt())
        with self.assertRaises(KeyboardInterrupt):
            self.bot.execute()
        self.assertFalse(self.bot.execution_tracker.complete_execution.call_args.kwargs['success'])


class ManualContinuationTests(unittest.TestCase):
    setUp = WorkflowTests.setUp
    def test_noninteractive_stops(self):
        namespace['sys'].stdin.isatty.return_value = False
        self.assertFalse(TriviaAutomation._handle_login_if_needed(self.bot).success)

    def test_declined_confirmation_stops(self):
        namespace['sys'].stdin.isatty.return_value = True
        with patch('builtins.input', return_value='cancel'), patch('builtins.print'):
            self.assertFalse(TriviaAutomation._handle_login_if_needed(self.bot).success)

    def test_wrong_foreground_page_stops(self):
        namespace['sys'].stdin.isatty.return_value = True
        self.bot._foreground_is_trivia_page = Mock(return_value=False)
        with patch('builtins.input', return_value='READY'), patch('builtins.print'):
            self.assertFalse(TriviaAutomation._handle_login_if_needed(self.bot).success)

    def test_confirmed_user_and_url_can_continue(self):
        namespace['sys'].stdin.isatty.return_value = True
        self.bot._foreground_is_trivia_page = Mock(return_value=True)
        self.bot.ui_detector = Mock()
        self.bot.ui_detector.find_element.return_value = None
        for name in ('ElementSearchCriteria', 'ElementType', 'DetectionMethod',
                     'AutomationConstants', 'AssetPaths', 'config'):
            namespace[name] = Mock()
        with patch('builtins.input', return_value='READY'), patch('builtins.print'):
            result = TriviaAutomation._handle_login_if_needed(self.bot)
        self.assertTrue(result.success)
        self.assertEqual(result.data['authentication_source'], 'operator_confirmation')

    def test_visible_login_button_still_blocks(self):
        namespace['sys'].stdin.isatty.return_value = True
        self.bot._foreground_is_trivia_page = Mock(return_value=True)
        self.bot.ui_detector = Mock()
        for name in ('ElementSearchCriteria', 'ElementType', 'DetectionMethod',
                     'AutomationConstants', 'AssetPaths', 'config'):
            namespace[name] = Mock()
        with patch('builtins.input', return_value='READY'), patch('builtins.print'):
            self.assertFalse(TriviaAutomation._handle_login_if_needed(self.bot).success)

class ForegroundURLTests(unittest.TestCase):
    def check_url(self, url):
        from urllib.parse import urlparse
        namespace['is_chrome_foreground'].return_value = True
        namespace['urlparse'] = urlparse
        namespace['pyperclip'] = Mock()
        namespace['pyperclip'].paste.side_effect = ['original clipboard', url]
        bot = TriviaAutomation.__new__(TriviaAutomation)
        result = bot._foreground_is_trivia_page()
        namespace['pyperclip'].copy.assert_called_with('original clipboard')
        return result

    def test_exact_trivia_url(self):
        self.assertTrue(self.check_url('https://www.wizard101.com/game/trivia'))

    def test_wrong_origin_and_lookalikes(self):
        for url in ['http://www.wizard101.com/game/trivia',
                    'https://www.wizard101.com.evil.test/game/trivia',
                    'https://www.wizard101.com@evil.test/game/trivia',
                    'https://www.wizard101.com/game/trivia?token=secret', '', 'terminal text']:
            with self.subTest(url=url):
                self.assertFalse(self.check_url(url))


class ForegroundGuardTests(unittest.TestCase):
    def test_wrong_process_never_gets_shortcuts(self):
        namespace['is_chrome_foreground'].return_value = False
        namespace['pyautogui'].reset_mock()
        namespace['pyperclip'] = Mock()
        bot = TriviaAutomation.__new__(TriviaAutomation)
        self.assertFalse(bot._foreground_is_trivia_page())
        self.assertEqual(namespace['pyautogui'].mock_calls, [])
        self.assertEqual(namespace['pyperclip'].mock_calls, [])

    def test_nonwindows_fails_closed(self):
        from src.utils.foreground_browser import is_chrome_foreground
        with patch('src.utils.foreground_browser.sys.platform', 'linux'):
            self.assertFalse(is_chrome_foreground())
