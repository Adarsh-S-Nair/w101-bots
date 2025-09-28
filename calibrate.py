"""
Interactive calibration script for Wizard101 Gardening Bot
This script helps you find the correct coordinates for UI elements
"""
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from config import config
from src.logger import logger
from src.vision import VisionDetector
import pyautogui
import time

def main():
    """Run the calibration process"""
    try:
        logger.info("=" * 60)
        logger.info("Wizard101 Gardening Bot - Coordinate Calibration")
        logger.info("=" * 60)
        
        # Setup
        config.setup_directories()
        vision = VisionDetector()
        
        logger.info("This script will help you calibrate the coordinates for UI elements.")
        logger.info("Make sure Wizard101 launcher is open and visible on your screen.")
        
        input("\nPress Enter when you're ready to start calibration...")
        
        # Take initial screenshot (debug saving disabled)
        screenshot = vision.take_screenshot()
        # vision.save_debug_image(screenshot, "calibration_full_screen")  # Disabled for GitHub
        
        # Calibrate coordinates
        coordinates = vision.calibrate_coordinates()
        
        # Save coordinates to config
        logger.info("Saving calibrated coordinates...")
        
        # Create a coordinates config file
        coords_config = f"""# Calibrated coordinates for Wizard101 launcher
# Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}

password_field_x: {coordinates['password_field'][0]}
password_field_y: {coordinates['password_field'][1]}
login_button_x: {coordinates['login_button'][0]}
login_button_y: {coordinates['login_button'][1]}

# Screen resolution: {pyautogui.size()[0]}x{pyautogui.size()[1]}
"""
        
        with open('coordinates.yaml', 'w') as f:
            f.write(coords_config)
        
        logger.info("✅ Calibration complete!")
        logger.info(f"📁 Coordinates saved to: coordinates.yaml")
        logger.info(f"🎯 Password field: ({coordinates['password_field'][0]}, {coordinates['password_field'][1]})")
        logger.info(f"🔘 Login button: ({coordinates['login_button'][0]}, {coordinates['login_button'][1]})")
        
        logger.info("\nYou can now run the main bot with: python main.py")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Calibration cancelled by user")
        return 0
    except Exception as e:
        logger.error(f"Calibration failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
