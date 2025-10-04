#!/usr/bin/env python3
"""
Example script demonstrating how to use the GardeningBotTracker
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.bot_execution_tracker import GardeningBotTracker
from src.utils.automation_scheduler import AutomationScheduler
from datetime import datetime

def main():
    """Demonstrate gardening bot tracking functionality"""
    print("=== Gardening Bot Tracker Example ===\n")
    
    # Create tracker instance
    tracker = GardeningBotTracker()
    scheduler = AutomationScheduler()
    
    # Check if it's time to run
    print("1. Checking if it's time to run the gardening bot:")
    is_time = tracker.is_time_to_run()
    next_run = tracker.get_next_run_time()
    print(f"   Time to run: {is_time}")
    print(f"   Next run time: {next_run}\n")
    
    # Get execution statistics
    print("2. Getting execution statistics:")
    stats = tracker.get_gardening_stats()
    print(f"   Total executions: {stats['total_executions']}")
    print(f"   Successful executions: {stats['successful_executions']}")
    print(f"   Failed executions: {stats['failed_executions']}")
    print(f"   Success rate: {stats['success_rate']}%")
    print(f"   Total harvests: {stats['total_harvests']}")
    print(f"   Total replants: {stats['total_replants']}")
    print(f"   Total needs handled: {stats['total_needs_handled']}\n")
    
    # Get recent execution history
    print("3. Recent execution history:")
    history = tracker.get_execution_history(limit=3)
    for i, execution in enumerate(history, 1):
        print(f"   Execution {i}:")
        print(f"     ID: {execution.get('execution_id', 'N/A')}")
        print(f"     Status: {execution.get('status', 'N/A')}")
        print(f"     Success: {execution.get('success', 'N/A')}")
        print(f"     Start time: {execution.get('start_time', 'N/A')}")
        print(f"     Duration: {execution.get('duration_formatted', 'N/A')}")
        actions = execution.get('execution_summary', {}).get('actions_performed', [])
        print(f"     Actions: {', '.join(actions) if actions else 'None'}")
        print()
    
    # Get plant status history
    print("4. Recent plant status history:")
    plant_history = tracker.get_plant_status_history(limit=3)
    for i, status in enumerate(plant_history, 1):
        print(f"   Status {i}:")
        print(f"     Plant: {status.get('plant_name', 'N/A')}")
        print(f"     Stage: {status.get('current_stage', 'N/A')}")
        print(f"     Time to next: {status.get('time_to_next_hours', 'N/A')} hours")
        print(f"     Timestamp: {status.get('timestamp', 'N/A')}")
        print()
    
    # Get automation status
    print("5. Automation status and recommendations:")
    automation_status = scheduler.get_automation_status()
    print(f"   Should run bot: {automation_status['should_run_bot']}")
    print(f"   Next run time: {automation_status.get('next_run_time', 'N/A')}")
    print("   Recommendations:")
    for rec in automation_status.get('recommendations', []):
        print(f"     - {rec}")
    print()
    
    # Get detailed schedule
    print("6. Detailed gardening schedule:")
    schedule = scheduler.get_plant_schedule()
    print(f"   Current time: {schedule['current_time']}")
    print(f"   Should run now: {schedule['should_run_now']}")
    print(f"   Plant status entries: {len(schedule.get('plant_status_history', []))}")
    print(f"   Execution entries: {len(schedule.get('execution_history', []))}")
    
    print("\n=== Example completed ===")

if __name__ == "__main__":
    main()
