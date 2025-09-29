"""
Example script demonstrating the new modular bot architecture
"""
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent / "src"))
sys.path.append(str(Path(__file__).parent.parent))

from src.core.modular_bot import ModularBot
from src.utils.logger import logger

def demonstrate_modular_bot():
    """Demonstrate different ways to use the modular bot"""
    
    print("=" * 60)
    print("Wizard101 Modular Bot - Example Usage")
    print("=" * 60)
    
    # Create a gardening bot
    print("\n1. Creating gardening bot...")
    bot = ModularBot("gardening")
    
    # Show available automation types
    print("\n2. Available automation types:")
    types = bot.get_available_automation_types()
    for automation_type in types:
        info = bot.get_automation_info() if automation_type == "gardening" else bot.registry.get_automation_info(automation_type)
        print(f"   - {automation_type}: {info.get('module_count', 0)} modules")
    
    # Show module status
    print("\n3. Module status:")
    status = bot.get_module_status()
    print("   Core modules:")
    for name, info in status["core_modules"].items():
        print(f"     - {name} ({info['class']})")
    print("   Custom modules:")
    for name, info in status["custom_modules"].items():
        print(f"     - {name} ({info['class']})")
    
    # Show automation info
    print("\n4. Current automation info:")
    info = bot.get_automation_info()
    print(f"   Type: {info['type']}")
    print(f"   Modules: {info['module_count']}")
    print(f"   Module names: {', '.join(info['modules'])}")
    
    print("\n5. Bot is ready to run!")
    print("   Use bot.run() to execute the complete workflow")
    print("   Use bot.run_core_only() to run only launcher/login/game startup")
    print("   Use bot.run_custom_only() to run only gardening-specific modules")
    
    return bot

def run_bot_example():
    """Example of running the bot with different modes"""
    
    bot = demonstrate_modular_bot()
    
    print("\n" + "=" * 60)
    print("Bot Execution Examples")
    print("=" * 60)
    
    # Example 1: Run complete workflow
    print("\nExample 1: Complete workflow")
    print("This would run: launcher -> login -> enter game (with crown shop handling) -> housing navigation (including red barn farm equipping and go home) -> gardening")
    print("Uncomment the line below to actually run:")
    print("# result = bot.run()")
    
    # Example 2: Run core only
    print("\nExample 2: Core workflow only")
    print("This would run: launcher -> login -> enter game (with crown shop handling)")
    print("Uncomment the line below to actually run:")
    print("# result = bot.run_core_only()")
    
    # Example 3: Run custom only
    print("\nExample 3: Custom modules only")
    print("This would run: housing navigation (including red barn farm equipping and go home) -> gardening")
    print("Uncomment the line below to actually run:")
    print("# result = bot.run_custom_only()")
    
    print("\nNote: Uncomment the lines above to actually execute the bot")
    print("The examples are commented out to prevent accidental execution")

if __name__ == "__main__":
    try:
        run_bot_example()
    except KeyboardInterrupt:
        print("\nExample interrupted by user")
    except Exception as e:
        print(f"\nError running example: {e}")
