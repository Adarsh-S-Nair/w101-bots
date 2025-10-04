#!/usr/bin/env python3
"""
Example of how to use the trivia bot with execution tracking
This example shows how to check if it's time to run and execute the bot with tracking
"""
import sys
import os

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.automation.trivia_automation import TriviaAutomation
from src.detection.ui_detector import UIDetector
from src.utils.logger import logger

def run_trivia_bot_with_tracking():
    """Run the trivia bot with execution tracking"""
    
    # Initialize the UI detector and trivia automation
    ui_detector = UIDetector()
    trivia_bot = TriviaAutomation(ui_detector)
    
    # Check if it's time to run the bot
    if not trivia_bot.is_time_to_run():
        next_run = trivia_bot.get_next_run_time()
        if next_run:
            print(f"Trivia bot is not ready to run yet.")
            print(f"Next run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Show time until next run
            from datetime import datetime
            current_time = datetime.now()
            time_until_next = next_run - current_time
            print(f"Time until next run: {str(time_until_next).split('.')[0]}")
        else:
            print("No previous execution found - ready to run!")
        return
    
    print("Trivia bot is ready to run!")
    
    # Show execution statistics before running
    stats = trivia_bot.get_execution_stats()
    if stats['total_executions'] > 0:
        print(f"\nPrevious execution stats:")
        print(f"  Total runs: {stats['total_executions']}")
        print(f"  Success rate: {stats['success_rate']}%")
        print(f"  Average duration: {stats['average_duration_formatted']}")
    
    # Run the trivia bot (this will automatically track execution)
    print(f"\nStarting trivia bot execution...")
    result = trivia_bot.execute()
    
    if result.success:
        print(f"Trivia bot completed successfully!")
        print(f"Result: {result.message}")
        
        # Show when the next run will be
        next_run = trivia_bot.get_next_run_time()
        if next_run:
            print(f"Next trivia bot run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"Trivia bot failed: {result.message}")
        if result.error:
            print(f"Error details: {result.error}")

if __name__ == "__main__":
    try:
        run_trivia_bot_with_tracking()
    except Exception as e:
        print(f"Error running trivia bot: {e}")
        logger.error(f"Error running trivia bot: {e}")
