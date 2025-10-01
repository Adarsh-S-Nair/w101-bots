"""
Constants for Wizard101 Gardening Bot

This module contains all the constants for asset paths and automation behavior.
To add new templates:
1. Add the filename to the appropriate class (LauncherTemplates or GameTemplates)
2. Use config.get_launcher_template_path() or config.get_game_template_path() to get full paths
3. The constants will automatically handle the directory structure

Example usage:
    from config import config
    from src.constants import AssetPaths
    
    # Get launcher template path
    login_path = config.get_launcher_template_path(AssetPaths.LauncherTemplates.LOGIN_BUTTON)
    
    # Get game template path
    play_path = config.get_game_template_path(AssetPaths.GameTemplates.PLAY_BUTTON)
"""
from pathlib import Path

# Asset directory structure constants
class AssetPaths:
    """Constants for asset directory paths"""
    
    # Base directories
    ASSETS_BASE = "assets"
    TEMPLATES_BASE = "assets/templates"
    
    # Template subdirectories
    LAUNCHER_TEMPLATES = "launcher"
    GAME_TEMPLATES = "game"
    GARDENING_TEMPLATES = "gardening"
    TRIVIA_TEMPLATES = "trivia"
    
    # Specific template files
    class LauncherTemplates:
        """Launcher-specific template files"""
        DISABLED_PLAY_BUTTON = "disabled_play_button.png"
        LAUNCHER_LOADED = "launcher_loaded.png"
        LAUNCHER_PLAY_BUTTON = "launcher_play_button.png"
        LOGIN_BUTTON = "login_button.png"
        PASSWORD_FIELD = "password_field.png"
        PASSWORD_FIELD_FOCUSED = "password_field_focused.png"
        USERNAME_FIELD = "username_field.png"
    
    class GameTemplates:
        """Game-specific template files"""
        PLAY_BUTTON = "play_button.png"
        TITLE_SCREEN = "title_screen.png"
        SPELLBOOK = "spellbook.png"
        HOUSING_NAV = "housing_nav.png"
        CASTLES = "castles.png"
        RED_BARN_FARM = "red_barn_farm.png"
        EQUIP = "equip.png"
        UNEQUIP = "unequip.png"
        GO_HOME = "go_home.png"
        CLOSE_CROWN_SHOP = "close_crown_shop.png"
        CROWN_SHOP = "crown_shop.png"
        PLACE_OBJECT = "place_object.png"
        HOUSE_START = "house_start.png"
        OUTSIDE_BUTTON = "outside_button.png"
        # Add more game templates here as needed
    
    class GardeningTemplates:
        """Gardening-specific template files"""
        ELDER_COUCH_POTATOES_READY = "elder_couch_potatoes_ready.png"
        SEEDS_GARDENING_MENU = "seeds_gardening_menu.png"
        COUCH_POTATOES_GARDENING_MENU = "couch_potatoes_gardening_menu.png"
        PLANT_FIRST_SEED = "plant_first_seed.png"
        UTILITY_GARDENING_MENU = "utility_gardening_menu.png"
        PLANT_ALL = "plant_all.png"
        PLANTED_COUCH_POTATO = "planted_couch_potato.png"
        CONFIRM_PLANT_ALL = "confirm_plant_all.png"
        PLANTS_HAVE_NEEDS = "plants_have_needs.png"
        GROWING_SPELLS = "growing_spells.png"
        PEST_SPELLS = "pest_spells.png"
        DOWNPOUR = "downpour.png"
        FLUTE_ENSEMBLE = "flute_ensemble.png"
        GUSTY_WINDS = "gusty_winds.png"
        GARDENING_MENU_RIGHT_ARROW = "gardening_menu_right_arrow.png"
        # Add more gardening templates here as needed
    
    class TriviaTemplates:
        """Trivia-specific template files"""
        # Login and authentication
        W101_LOGO = "w101_logo.png"
        LOGIN_BUTTON = "login_button.png"
        USERNAME_FIELD = "username_field.png"
        PASSWORD_FIELD = "password_field.png"
        PLAY_NOW_BUTTON = "play_now_button.png"
        
        # Trivia selection
        KINGSISLE_TRIVIA = "kingsisle_trivia.png"
        WIZARD101_TRIVIA = "wizard101_trivia.png"
        AUSTIN_TEXAS_TRIVIA = "austin_texas_trivia.png"
        TRIVIA_BANNER = "trivia_banner.png"
        GOOGLE_SEARCH_ICON = "google_search_icon.png"
        
        # Question interface
        QUESTION_TEXT = "question_text.png"
        SINGLE_LINE_QUESTION = "single_line_question.png"
        ANSWER_OPTION_A = "answer_option_a.png"
        ANSWER_OPTION_B = "answer_option_b.png"
        ANSWER_OPTION_C = "answer_option_c.png"
        ANSWER_OPTION_D = "answer_option_d.png"
        
        # Navigation and completion
        NEXT_QUESTION = "next_question.png"
        NEXT_QUESTION_BUTTON = "next_question_button.png"
        GET_MY_RESULTS_BUTTON = "get_my_results_button.png"
        SUBMIT_ANSWER = "submit_answer.png"
        SUBMIT_ANSWER_BUTTON = "submit_answer_button.png"
        CONTINUE_BUTTON = "continue_button.png"
        FINISH_BUTTON = "finish_button.png"
        
        # Rewards and results
        REWARD_POPUP = "reward_popup.png"
        CLAIM_REWARD = "claim_reward.png"
        CLAIM_YOUR_REWARD_BUTTON = "claim_your_reward_button.png"
        SECOND_CLAIM_YOUR_REWARD_BUTTON = "second_claim_your_reward_button.png"
        TAKE_ANOTHER_QUIZ_BUTTON = "take_another_quiz_button.png"
        RESULTS_SCREEN = "results_screen.png"
        
        # Add more trivia templates here as needed
    
    @classmethod
    def get_launcher_template_path(cls, filename: str) -> str:
        """Get full path for a launcher template file"""
        return f"{cls.TEMPLATES_BASE}/{cls.LAUNCHER_TEMPLATES}/{filename}"
    
    @classmethod
    def get_game_template_path(cls, filename: str) -> str:
        """Get full path for a game template file"""
        return f"{cls.TEMPLATES_BASE}/{cls.GAME_TEMPLATES}/{filename}"
    
    @classmethod
    def get_gardening_template_path(cls, filename: str) -> str:
        """Get full path for a gardening template file"""
        return f"{cls.TEMPLATES_BASE}/{cls.GARDENING_TEMPLATES}/{filename}"
    
    @classmethod
    def get_trivia_template_path(cls, filename: str) -> str:
        """Get full path for a trivia template file"""
        return f"{cls.TEMPLATES_BASE}/{cls.TRIVIA_TEMPLATES}/{filename}"

# Automation constants
class AutomationConstants:
    """Constants for automation behavior"""
    
    # Confidence thresholds
    DEFAULT_CONFIDENCE_THRESHOLD = 0.8
    LAUNCHER_CONFIDENCE_THRESHOLD = 0.7
    GAME_CONFIDENCE_THRESHOLD = 0.8
    TRIVIA_CONFIDENCE_THRESHOLD = 0.7
    
    # Timeout values (in seconds)
    DEFAULT_TIMEOUT = 30.0
    LOGIN_TIMEOUT = 60.0
    GAME_LOAD_TIMEOUT = 300.0  # 5 minutes for game loading
    TRIVIA_PAGE_LOAD_TIMEOUT = 15.0  # Trivia page load timeout
    QUESTION_LOAD_TIMEOUT = 10.0  # Question loading timeout
    
    # Check intervals (in seconds)
    DEFAULT_CHECK_INTERVAL = 2.0
    GAME_LOAD_CHECK_INTERVAL = 5.0
    TRIVIA_CHECK_INTERVAL = 1.0  # Faster checks for trivia interactions

# Element types for UI detection
class ElementTypes:
    """Constants for UI element types"""
    
    BUTTON = "button"
    INPUT_FIELD = "input_field"
    TEXT = "text"
    IMAGE = "image"
    CONTAINER = "container"
