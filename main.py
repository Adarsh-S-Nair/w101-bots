"""
Wizard101 Gardening Bot - Main Entry Point
"""
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.bot import Wizard101Bot
from src.utils.logger import logger

def main():
    """Main function to run the bot"""
    try:
        # Create and run the bot
        bot = Wizard101Bot()
        result = bot.run()
        
        if result.success:
            logger.info("Bot execution completed successfully!")
            input("Press Enter to exit...")
            return 0
        else:
            logger.error(f"Bot execution failed: {result.message}")
            if result.error:
                logger.error(f"Error details: {result.error}")
            input("Press Enter to exit...")
            return 1
        
    except KeyboardInterrupt:
        logger.info("Bot execution interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        input("Press Enter to exit...")
        return 1

if __name__ == "__main__":
    sys.exit(main())
