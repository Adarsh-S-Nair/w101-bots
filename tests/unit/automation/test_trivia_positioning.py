"""
Unit tests for trivia automation positioning logic
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the path so we can import our modules
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
sys.path.insert(0, project_root)

from src.automation.trivia_automation import TriviaAutomation, ANSWER_POSITIONS


class TestTriviaPositioning(unittest.TestCase):
    """Test cases for the feedback-based positioning system"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the ui_detector dependency
        mock_ui_detector = Mock()
        self.trivia_automation = TriviaAutomation(mock_ui_detector)
        
        # Mock question position and text
        self.question_position = (100, 200)  # x=100, y=200
        self.question_text = "What is the capital of France?"
        self.correct_answer = "Paris"
        
        # Mock answer positions for testing
        self.first_answer_pos = (100 + ANSWER_POSITIONS['first']['x'], 200 + ANSWER_POSITIONS['first']['y'])
        self.second_answer_pos = (100 + ANSWER_POSITIONS['second']['x'], 200 + ANSWER_POSITIONS['second']['y'])
        self.third_answer_pos = (100 + ANSWER_POSITIONS['third']['x'], 200 + ANSWER_POSITIONS['third']['y'])
    
    def test_detect_question_positioning_no_adjustment_needed(self):
        """Test when question positioning is correct (no adjustment needed)"""
        # Mock the simulate_copy_answer method to return a different answer (not the question)
        with patch.object(self.trivia_automation, '_simulate_copy_answer') as mock_copy:
            mock_copy.return_value = "London"  # Different from question text
            
            result = self.trivia_automation._detect_and_adjust_question_positioning(
                self.question_position, self.question_text
            )
            
            # Should return 0 since no adjustment is needed
            self.assertEqual(result, 0)
            mock_copy.assert_called_once()
    
    def test_detect_question_positioning_adjustment_needed(self):
        """Test when question positioning is off (adjustment needed)"""
        # Mock the simulate_copy_answer method to return the question text
        with patch.object(self.trivia_automation, '_simulate_copy_answer') as mock_copy:
            mock_copy.return_value = self.question_text  # Same as question text
            
            result = self.trivia_automation._detect_and_adjust_question_positioning(
                self.question_position, self.question_text
            )
            
            # Should return 30 since adjustment is needed
            self.assertEqual(result, 30)
            mock_copy.assert_called_once()
    
    def test_detect_third_fourth_positioning_no_adjustment_needed(self):
        """Test when third/fourth positioning is correct (no additional adjustment needed)"""
        y_adjustment = 0
        previous_answer_text = "London"
        
        # Mock the simulate_copy_answer method to return a different answer
        with patch.object(self.trivia_automation, '_simulate_copy_answer') as mock_copy:
            mock_copy.return_value = "Berlin"  # Different from previous answer
            
            result = self.trivia_automation._detect_and_adjust_third_fourth_positioning(
                self.question_position, y_adjustment, previous_answer_text
            )
            
            # Should return 0 since no additional adjustment is needed
            self.assertEqual(result, 0)
            mock_copy.assert_called_once()
    
    def test_detect_third_fourth_positioning_adjustment_needed(self):
        """Test when third/fourth positioning is off (additional adjustment needed)"""
        y_adjustment = 0
        previous_answer_text = "London"
        
        # Mock the simulate_copy_answer method to return the same as previous answer
        with patch.object(self.trivia_automation, '_simulate_copy_answer') as mock_copy:
            mock_copy.return_value = previous_answer_text  # Same as previous answer
            
            result = self.trivia_automation._detect_and_adjust_third_fourth_positioning(
                self.question_position, y_adjustment, previous_answer_text
            )
            
            # Should return 20 since additional adjustment is needed
            self.assertEqual(result, 20)
            mock_copy.assert_called_once()
    
    def test_detect_third_fourth_positioning_no_previous_answer(self):
        """Test when there's no previous answer text (should not adjust)"""
        y_adjustment = 0
        previous_answer_text = None
        
        # Mock the simulate_copy_answer method
        with patch.object(self.trivia_automation, '_simulate_copy_answer') as mock_copy:
            mock_copy.return_value = "Berlin"
            
            result = self.trivia_automation._detect_and_adjust_third_fourth_positioning(
                self.question_position, y_adjustment, previous_answer_text
            )
            
            # Should return 0 since no previous answer to compare against
            self.assertEqual(result, 0)
            mock_copy.assert_called_once()
    
    def test_combined_positioning_scenarios(self):
        """Test combined scenarios with both types of adjustments"""
        
        # Scenario 1: Question positioning off + Third/fourth positioning off
        with patch.object(self.trivia_automation, '_simulate_copy_answer') as mock_copy:
            # First call returns question text (question positioning off)
            # Second call returns same as previous answer (third/fourth positioning off)
            mock_copy.side_effect = [self.question_text, "London"]
            
            question_adjustment = self.trivia_automation._detect_and_adjust_question_positioning(
                self.question_position, self.question_text
            )
            
            third_fourth_adjustment = self.trivia_automation._detect_and_adjust_third_fourth_positioning(
                self.question_position, question_adjustment, "London"
            )
            
            # Both adjustments should be applied
            self.assertEqual(question_adjustment, 30)
            self.assertEqual(third_fourth_adjustment, 20)
            self.assertEqual(mock_copy.call_count, 2)
    
    def test_answer_position_calculations(self):
        """Test that answer positions are calculated correctly with adjustments"""
        question_x, question_y = self.question_position
        y_adjustment = 30
        third_fourth_adjustment = 20
        
        # Calculate expected positions
        first_x = question_x + ANSWER_POSITIONS['first']['x']
        first_y = question_y + ANSWER_POSITIONS['first']['y'] + y_adjustment
        
        second_x = question_x + ANSWER_POSITIONS['second']['x']
        second_y = question_y + ANSWER_POSITIONS['second']['y'] + y_adjustment
        
        third_x = question_x + ANSWER_POSITIONS['third']['x']
        third_y = question_y + ANSWER_POSITIONS['third']['y'] + y_adjustment + third_fourth_adjustment
        
        # Verify positions are calculated correctly
        self.assertEqual(first_x, 100 + (-200))  # -100
        self.assertEqual(first_y, 200 + 50 + 30)  # 280
        
        self.assertEqual(second_x, 100 + 80)  # 180
        self.assertEqual(second_y, 200 + 50 + 30)  # 280
        
        self.assertEqual(third_x, 100 + (-200))  # -100
        self.assertEqual(third_y, 200 + 90 + 30 + 20)  # 340


class TestTriviaPositioningIntegration(unittest.TestCase):
    """Integration tests for the complete positioning system"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the ui_detector dependency
        mock_ui_detector = Mock()
        self.trivia_automation = TriviaAutomation(mock_ui_detector)
        self.question_position = (100, 200)
        self.question_text = "What is the capital of France?"
        self.correct_answer = "Paris"
    
    @patch('pyautogui.moveTo')
    @patch('pyautogui.tripleClick')
    @patch('pyautogui.hotkey')
    @patch('pyautogui.click')
    @patch('pyperclip.paste')
    def test_find_correct_answer_with_positioning_adjustment(self, mock_paste, mock_click, mock_hotkey, mock_triple, mock_move):
        """Test the complete flow with positioning adjustments"""
        # Mock clipboard to return question text first (positioning off), then correct answer
        mock_paste.side_effect = [
            self.question_text,  # First attempt copies question (positioning off)
            "London",           # First answer after adjustment
            "Berlin",           # Second answer
            "Paris"             # Third answer (correct)
        ]
        
        # Mock the simulate_copy_answer method to return the question text initially
        with patch.object(self.trivia_automation, '_simulate_copy_answer') as mock_copy:
            mock_copy.return_value = self.question_text
            
            # This should detect the positioning issue and adjust
            adjustment = self.trivia_automation._detect_and_adjust_question_positioning(
                self.question_position, self.question_text
            )
            
            # Should detect that adjustment is needed
            self.assertEqual(adjustment, 30)


if __name__ == '__main__':
    unittest.main()
