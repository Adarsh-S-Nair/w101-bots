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
        # Add more game templates here as needed
        # Examples:
        # GARDEN_BUTTON = "garden_button.png"
        # HARVEST_BUTTON = "harvest_button.png"
        # PLANT_BUTTON = "plant_button.png"
    
    @classmethod
    def get_launcher_template_path(cls, filename: str) -> str:
        """Get full path for a launcher template file"""
        return f"{cls.TEMPLATES_BASE}/{cls.LAUNCHER_TEMPLATES}/{filename}"
    
    @classmethod
    def get_game_template_path(cls, filename: str) -> str:
        """Get full path for a game template file"""
        return f"{cls.TEMPLATES_BASE}/{cls.GAME_TEMPLATES}/{filename}"

# Automation constants
class AutomationConstants:
    """Constants for automation behavior"""
    
    # Confidence thresholds
    DEFAULT_CONFIDENCE_THRESHOLD = 0.8
    LAUNCHER_CONFIDENCE_THRESHOLD = 0.7
    GAME_CONFIDENCE_THRESHOLD = 0.8
    
    # Timeout values (in seconds)
    DEFAULT_TIMEOUT = 30.0
    LOGIN_TIMEOUT = 60.0
    GAME_LOAD_TIMEOUT = 300.0  # 5 minutes for game loading
    
    # Check intervals (in seconds)
    DEFAULT_CHECK_INTERVAL = 2.0
    GAME_LOAD_CHECK_INTERVAL = 5.0

# Element types for UI detection
class ElementTypes:
    """Constants for UI element types"""
    
    BUTTON = "button"
    INPUT_FIELD = "input_field"
    TEXT = "text"
    IMAGE = "image"
    CONTAINER = "container"
