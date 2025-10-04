#!/usr/bin/env python3
"""
Bot Status Checker
Utility script to check the status and schedule of bot executions
"""
import sys
import os
from datetime import datetime

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.bot_execution_tracker import TriviaBotTracker
from src.utils.logger import logger

def check_trivia_bot_status():
    """Check the status of the trivia bot"""
    print("=== Trivia Bot Status ===")
    
    tracker = TriviaBotTracker()
    
    # Check if it's time to run
    is_time = tracker.is_time_to_run()
    print(f"Ready to run: {'YES' if is_time else 'NO'}")
    
    # Get next run time
    next_run = tracker.get_next_run_time()
    if next_run:
        current_time = datetime.now()
        if is_time:
            print(f"Status: Ready to run now!")
        else:
            time_until_next = next_run - current_time
            print(f"Next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Time until next run: {str(time_until_next).split('.')[0]}")
    else:
        print("Status: No previous runs found - ready to run!")
    
    # Get execution stats
    stats = tracker.get_execution_stats()
    if stats['total_executions'] > 0:
        print(f"\nExecution Statistics:")
        print(f"  Total runs: {stats['total_executions']}")
        print(f"  Successful: {stats['successful_executions']}")
        print(f"  Failed: {stats['failed_executions']}")
        print(f"  Success rate: {stats['success_rate']}%")
        print(f"  Average duration: {stats['average_duration_formatted']}")
    
    # Get recent history
    history = tracker.get_execution_history(3)
    if history:
        print(f"\nRecent Executions:")
        for i, execution in enumerate(history, 1):
            status = "[SUCCESS]" if execution.get("success") else "[FAILED]"
            duration = execution.get("duration_formatted", "N/A")
            start_time = execution.get("start_time", "N/A")
            if isinstance(start_time, str):
                try:
                    start_dt = datetime.fromisoformat(start_time)
                    start_formatted = start_dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    start_formatted = start_time
            else:
                start_formatted = start_time.strftime('%Y-%m-%d %H:%M:%S') if start_time else "N/A"
            
            print(f"  {i}. {start_formatted} {status} ({duration})")

def main():
    """Main function"""
    try:
        check_trivia_bot_status()
    except Exception as e:
        print(f"Error checking bot status: {e}")
        logger.error(f"Error checking bot status: {e}")

if __name__ == "__main__":
    main()
