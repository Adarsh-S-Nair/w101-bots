"""
Wizard101 Modular Bot - Main Entry Point
Supports different automation types: gardening, fishing, pvp, etc.
"""
import sys
import argparse
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.modular_bot import ModularBot
from src.utils.logger import logger

def main():
    """Main function to run the bot"""
    parser = argparse.ArgumentParser(description="Wizard101 Modular Bot")
    parser.add_argument(
        "--type", 
        default="gardening",
        choices=["gardening"],  # Add more types as they're implemented
        help="Type of automation to run (default: gardening)"
    )
    parser.add_argument(
        "--core-only",
        action="store_true",
        help="Run only core workflow (launcher, login, game startup)"
    )
    parser.add_argument(
        "--custom-only",
        action="store_true",
        help="Run only custom modules for the specified automation type"
    )
    parser.add_argument(
        "--list-types",
        action="store_true",
        help="List available automation types and exit"
    )
    
    args = parser.parse_args()
    
    try:
        # List available types if requested
        if args.list_types:
            bot = ModularBot("gardening")  # Create temporary bot to access registry
            types = bot.get_available_automation_types()
            print("Available automation types:")
            for automation_type in types:
                info = bot.get_automation_info() if automation_type == "gardening" else bot.registry.get_automation_info(automation_type)
                print(f"  - {automation_type}: {info.get('module_count', 0)} modules")
            return 0
        
        # Create and run the bot
        bot = ModularBot(args.type)
        
        # Run based on arguments
        if args.core_only:
            logger.info(f"Running core workflow only for {args.type} bot...")
            result = bot.run_core_only()
        elif args.custom_only:
            logger.info(f"Running custom modules only for {args.type} bot...")
            result = bot.run_custom_only()
        else:
            logger.info(f"Running complete {args.type} bot workflow...")
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
