#!/usr/bin/env python3
"""
Command-line utility to check plant status and automation recommendations
Usage: python check_plants.py [--export-csv] [--schedule]
"""
import argparse
import json
from src.utils.automation_scheduler import AutomationScheduler
from src.utils.logger import logger

def main():
    parser = argparse.ArgumentParser(description="Check plant status and automation recommendations")
    parser.add_argument("--export-csv", action="store_true", help="Export plant schedule to CSV")
    parser.add_argument("--schedule", action="store_true", help="Show detailed plant schedule")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    args = parser.parse_args()
    
    try:
        scheduler = AutomationScheduler()
        
        if args.schedule:
            # Show detailed schedule
            schedule = scheduler.get_plant_schedule()
            if args.json:
                print(json.dumps(schedule, indent=2))
            else:
                print_plant_schedule(schedule)
        else:
            # Show automation status
            status = scheduler.get_automation_status()
            if args.json:
                print(json.dumps(status, indent=2))
            else:
                print_automation_status(status)
        
        if args.export_csv:
            success = scheduler.export_schedule_csv()
            if success:
                print("\n✓ Plant schedule exported to data/plant_schedule.csv")
            else:
                print("\n✗ Failed to export CSV")
                
    except Exception as e:
        logger.error(f"Failed to check plants: {e}")
        print(f"Error: {e}")

def print_automation_status(status):
    """Print automation status in a readable format"""
    print("=" * 60)
    print("PLANT AUTOMATION STATUS")
    print("=" * 60)
    
    if status.get("should_run_bot"):
        print("🤖 BOT SHOULD RUN NOW")
    else:
        print("⏰ Bot should wait")
    
    print(f"\nPlants Ready: {status.get('ready_plants_count', 0)}")
    print(f"Total Plants: {status.get('total_plants', 0)}")
    
    if status.get("next_run_time"):
        print(f"Next Run Time: {status.get('next_run_time')}")
    
    if status.get("last_updated"):
        print(f"Last Updated: {status.get('last_updated')}")
    
    print("\nRECOMMENDATIONS:")
    for rec in status.get("recommendations", []):
        print(f"  • {rec}")
    
    if status.get("ready_plants"):
        print("\nREADY PLANTS:")
        for plant in status["ready_plants"]:
            print(f"  • {plant.get('plant_name')} - {plant.get('current_stage')} → {plant.get('next_stage')}")

def print_plant_schedule(schedule):
    """Print detailed plant schedule"""
    print("=" * 80)
    print("DETAILED PLANT SCHEDULE")
    print("=" * 80)
    print(f"Current Time: {schedule.get('current_time', 'Unknown')}")
    print()
    
    plants = schedule.get("plants", [])
    if not plants:
        print("No plants in schedule")
        return
    
    # Print header
    print(f"{'Plant Name':<20} {'Stage':<10} {'Next':<10} {'Hours':<8} {'Ready':<6} {'Next Check':<20}")
    print("-" * 80)
    
    for plant in plants:
        name = plant.get("plant_name", "Unknown")[:19]
        current = plant.get("current_stage", "Unknown")[:9]
        next_stage = plant.get("next_stage", "Unknown")[:9]
        hours = f"{plant.get('time_to_next_hours', 0):.1f}"[:7]
        ready = "✓" if plant.get("is_ready") else "✗"
        next_check = plant.get("next_check_time", "Unknown")[:19]
        
        print(f"{name:<20} {current:<10} {next_stage:<10} {hours:<8} {ready:<6} {next_check:<20}")

if __name__ == "__main__":
    main()
