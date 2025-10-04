# Configuration Files

This directory contains all configuration YAML files for the W101 Bots project.

## Configuration Files

### Core Configuration
- **`config.yaml`** - Main bot configuration file
- **`automation_config.yaml`** - General automation settings

### Bot-Specific Configuration
- **`garden_config.yaml`** - Gardening automation configuration
- **`farming_config.yaml`** - Farming automation configuration  
- **`world_config.yaml`** - World navigation configuration

### Database Files
- **`plant_database.yaml`** - Plant growth data and needs handling
- **`trivia_database.yaml`** - Trivia questions and answers

## Usage

All configuration files are automatically loaded by their respective automation modules. The files are referenced using the `config/` prefix in the code.

## File Structure

```
config/
├── README.md                 # This file
├── config.yaml              # Main configuration
├── automation_config.yaml   # Automation settings
├── garden_config.yaml       # Gardening bot config
├── farming_config.yaml      # Farming bot config
├── world_config.yaml        # World navigation config
├── plant_database.yaml      # Plant data
└── trivia_database.yaml     # Trivia data
```

## Editing Configuration

When editing configuration files:

1. **Backup first** - Always backup your config files before making changes
2. **Test changes** - Run the bot in test mode after configuration changes
3. **Validate YAML** - Ensure proper YAML syntax (use a YAML validator if needed)
4. **Check logs** - Monitor bot logs for configuration-related errors

## Migration from Root Directory

Configuration files were moved from the project root to this `config/` directory for better organization. All code references have been updated to use the new paths with the `config/` prefix.
