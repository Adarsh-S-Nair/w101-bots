# Wizard101 Modular Bot Architecture

This document describes the new modular architecture that separates core functionality from specific automations, making it easy to scale and add new bot types.

## Architecture Overview

The bot is now organized into several key components:

### Core Components

1. **BotFramework** (`src/core/bot_framework.py`)
   - Handles common functionality: launcher, login, and game startup
   - Manages core modules that are consistent across all bot types
   - Provides methods to run core workflow, custom modules, or complete workflow

2. **AutomationRegistry** (`src/core/automation_registry.py`)
   - Manages different automation types and their modules
   - Allows easy registration of new automation types
   - Provides module instantiation for specific automation types

3. **ModularBot** (`src/core/modular_bot.py`)
   - Main bot class that uses the framework and registry
   - Supports switching between different automation types
   - Provides high-level interface for running different workflows

### Automation Modules

#### Core Modules (Always Required)
- **LauncherAutomation**: Handles game launcher startup
- **LoginAutomation**: Handles user login process
- **EnterGameAutomation**: Handles entering the game from any state (fresh startup or already running)

#### Custom Modules (Type-Specific)
- **HousingNavigationAutomation**: Complete housing setup including red barn farm equipping and go home
- **GardeningAutomation**: Gardening-specific tasks (placeholder for future gardening functionality)

## Usage

### Command Line Interface

The bot now supports different automation types and execution modes:

```bash
# Run gardening bot (default)
python main.py

# Run gardening bot explicitly
python main.py --type gardening

# Run only core workflow (launcher, login, game startup)
python main.py --core-only

# Run only custom modules for gardening
python main.py --custom-only

# List available automation types
python main.py --list-types
```

### Programmatic Usage

```python
from src.core.modular_bot import ModularBot

# Create a gardening bot
bot = ModularBot("gardening")

# Run complete workflow
result = bot.run()

# Run only core workflow
result = bot.run_core_only()

# Run only custom modules
result = bot.run_custom_only()

# Switch to different automation type
result = bot.switch_automation_type("fishing")
```

## Adding New Automation Types

To add a new automation type (e.g., fishing):

1. **Create the automation module**:
   ```python
   # src/automation/fishing_automation.py
   class FishingAutomation(AutomationBase):
       def execute(self):
           # Implement fishing logic
           pass
   ```

2. **Register the automation type**:
   ```python
   # In ModularBot._register_automation_types()
   self.registry.register_automation_type("fishing", [
       HousingNavigationAutomation,  # If needed
       FishingAutomation
   ])
   ```

3. **Update main.py choices**:
   ```python
   parser.add_argument(
       "--type", 
       default="gardening",
       choices=["gardening", "fishing"],  # Add new type here
       help="Type of automation to run"
   )
   ```

## File Structure

```
src/
├── core/
│   ├── bot_framework.py      # Core framework for common functionality
│   ├── automation_registry.py # Registry for managing automation types
│   ├── modular_bot.py        # Main modular bot implementation
│   └── ...                   # Other core files
├── automation/
│   ├── housing_navigation.py # Generic housing navigation
│   ├── gardening_automation.py # Gardening-specific tasks
│   └── ...                   # Other automation modules
└── ...
```

## Benefits

1. **Scalability**: Easy to add new automation types without modifying core functionality
2. **Maintainability**: Clear separation of concerns between core and custom functionality
3. **Reusability**: Core modules are shared across all bot types
4. **Flexibility**: Can run different combinations of modules as needed
5. **Extensibility**: Simple registration system for new automation types

## Migration from Old Architecture

The old `Wizard101Bot` class is still available for backward compatibility, but the new modular architecture is recommended for new development and scaling.

Key changes:
- Red barn farm equipping logic moved from `HousingNavigationAutomation` to `GardeningAutomation`
- `HousingNavigationAutomation` is now generic and reusable
- New framework handles core functionality consistently
- Easy to add new bot types without modifying existing code
