"""
Configuration management for Wizard101 Gardening Bot
"""
import os
import yaml
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, Any
from src.constants import AssetPaths

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the bot"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = config_file
        self._config_data = self._load_config()
        
        # Load credentials from .env
        self.USERNAME = os.getenv('WIZARD101_USERNAME', '')
        self.PASSWORD = os.getenv('WIZARD101_PASSWORD', '')
        
        # Override config with environment variables if present
        self._apply_env_overrides()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file '{self.config_file}' not found")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides"""
        # Allow environment variables to override YAML settings
        if os.getenv('WIZARD101_LAUNCHER_PATH'):
            self._config_data['launcher']['path'] = os.getenv('WIZARD101_LAUNCHER_PATH')
        
        if os.getenv('WIZARD101_DEBUG_MODE'):
            self._config_data['bot']['debug_mode'] = os.getenv('WIZARD101_DEBUG_MODE').lower() == 'true'
    
    # Convenience properties for easy access
    @property
    def LAUNCHER_PATH(self) -> str:
        return self._config_data['launcher']['path']
    
    @property
    def WAIT_TIMEOUT(self) -> int:
        return self._config_data['launcher']['wait_timeout']
    
    @property
    def LOAD_DELAY(self) -> float:
        return self._config_data['launcher']['load_delay']
    
    @property
    def CLICK_DELAY(self) -> float:
        return self._config_data['automation']['click_delay']
    
    @property
    def TYPE_DELAY(self) -> float:
        return self._config_data['automation']['type_delay']
    
    @property
    def WAIT_DELAY(self) -> float:
        return self._config_data['automation']['wait_delay']
    
    @property
    def SCREENSHOT_DELAY(self) -> float:
        # Screenshots disabled for GitHub repository
        return 0.0
    
    @property
    def SCREENSHOT_DIR(self) -> Path:
        # Screenshots disabled for GitHub repository
        return Path("screenshots_disabled")
    
    @property
    def LOGS_DIR(self) -> Path:
        return Path(self._config_data['paths']['logs'])
    
    @property
    def DATABASE_PATH(self) -> Path:
        return Path(self._config_data['paths']['database'])
    
    @property
    def ASSETS_DIR(self) -> Path:
        return Path(self._config_data['paths']['assets'])
    
    @property
    def TEMPLATES_DIR(self) -> Path:
        return Path(self._config_data['paths']['templates'])
    
    @property
    def LAUNCHER_TEMPLATES_DIR(self) -> Path:
        """Get launcher templates directory path"""
        return self.TEMPLATES_DIR / AssetPaths.LAUNCHER_TEMPLATES
    
    @property
    def GAME_TEMPLATES_DIR(self) -> Path:
        """Get game templates directory path"""
        return self.TEMPLATES_DIR / AssetPaths.GAME_TEMPLATES
    
    @property
    def GARDENING_TEMPLATES_DIR(self) -> Path:
        """Get gardening templates directory path"""
        return self.TEMPLATES_DIR / AssetPaths.GARDENING_TEMPLATES
    
    @property
    def TRIVIA_TEMPLATES_DIR(self) -> Path:
        """Get trivia templates directory path"""
        return self.TEMPLATES_DIR / AssetPaths.TRIVIA_TEMPLATES
    
    @property
    def DEBUG_MODE(self) -> bool:
        return self._config_data['bot']['debug_mode']
    
    @property
    def SAVE_SCREENSHOTS(self) -> bool:
        return self._config_data['bot']['save_screenshots']
    
    @property
    def MAX_RETRIES(self) -> int:
        return self._config_data['bot']['max_retries']
    
    @property
    def RETRY_DELAY(self) -> float:
        return self._config_data['bot']['retry_delay']
    
    @property
    def LOG_LEVEL(self) -> str:
        return self._config_data['logging']['level']
    
    @property
    def CONSOLE_COLORS(self) -> bool:
        return self._config_data['logging']['console_colors']
    
    @property
    def FILE_LOGGING(self) -> bool:
        return self._config_data['logging']['file_logging']
    
    @property
    def PASSWORD_FIELD_COORDS(self) -> tuple:
        """Get calibrated password field coordinates"""
        coords = self._config_data.get('coordinates', {})
        return (coords.get('password_field_x', 960), coords.get('password_field_y', 1000))
    
    @property
    def LOGIN_BUTTON_COORDS(self) -> tuple:
        """Get calibrated login button coordinates"""
        coords = self._config_data.get('coordinates', {})
        return (coords.get('login_button_x', 1200), coords.get('login_button_y', 1000))
    
    def validate_config(self):
        """Validate that required configuration is present"""
        # Check credentials
        if not self.USERNAME or not self.PASSWORD:
            raise ValueError("Wizard101 credentials not found in .env file")
        
        # Check launcher path
        if not os.path.exists(self.LAUNCHER_PATH):
            raise FileNotFoundError(f"Wizard101 launcher not found at: {self.LAUNCHER_PATH}")
        
        return True
    
    def setup_directories(self):
        """Create necessary directories"""
        # self.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)  # Disabled for GitHub
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        self.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        self.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    def get_gardening_config(self) -> Dict[str, Any]:
        """Get gardening-specific configuration"""
        return self._config_data.get('gardening', {})
    
    def get_raw_config(self) -> Dict[str, Any]:
        """Get the raw configuration data"""
        return self._config_data.copy()
    
    def get_launcher_template_path(self, filename: str) -> str:
        """Get full path for a launcher template file"""
        return str(self.LAUNCHER_TEMPLATES_DIR / filename)
    
    def get_game_template_path(self, filename: str) -> str:
        """Get full path for a game template file"""
        return str(self.GAME_TEMPLATES_DIR / filename)
    
    def get_gardening_template_path(self, filename: str) -> str:
        """Get full path for a gardening template file"""
        return str(self.GARDENING_TEMPLATES_DIR / filename)
    
    def get_trivia_template_path(self, filename: str) -> str:
        """Get full path for a trivia template file"""
        return str(self.TRIVIA_TEMPLATES_DIR / filename)

# Create a global config instance
config = Config()
