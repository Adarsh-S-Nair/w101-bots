"""
Automation scheduler utility for managing bot operations based on plant status
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from src.data.plant_tracker import PlantTracker
from src.utils.logger import logger

class AutomationScheduler:
    """Manages automation scheduling based on plant status data"""
    
    def __init__(self, data_file: str = "data/plant_status.json"):
        self.plant_tracker = PlantTracker(data_file)
    
    def get_automation_status(self) -> Dict[str, Any]:
        """Get current automation status and recommendations"""
        try:
            summary = self.plant_tracker.get_plant_summary()
            ready_plants = self.plant_tracker.get_ready_plants()
            
            # Determine if bot should run
            should_run = len(ready_plants) > 0
            
            # Calculate next recommended run time
            next_run_time = None
            if not should_run and summary.get("next_ready_time"):
                next_run_time = summary["next_ready_time"]
            
            # Generate recommendations
            recommendations = self._generate_recommendations(ready_plants, summary)
            
            return {
                "should_run_bot": should_run,
                "ready_plants_count": len(ready_plants),
                "ready_plants": ready_plants,
                "next_run_time": next_run_time,
                "total_plants": summary["total_plants"],
                "last_updated": summary["last_updated"],
                "recommendations": recommendations,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get automation status: {e}")
            return {
                "should_run_bot": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_recommendations(self, ready_plants: List[Dict], summary: Dict) -> List[str]:
        """Generate automation recommendations based on plant status"""
        recommendations = []
        
        if len(ready_plants) > 0:
            plant_names = [p.get("plant_name", "Unknown") for p in ready_plants]
            recommendations.append(f"Run bot now - {len(ready_plants)} plants ready: {', '.join(plant_names)}")
            
            # Check for plants that have been ready for a while
            current_time = datetime.now()
            for plant in ready_plants:
                last_checked_str = plant.get("last_checked")
                if last_checked_str:
                    try:
                        last_checked = datetime.fromisoformat(last_checked_str)
                        hours_since_check = (current_time - last_checked).total_seconds() / 3600
                        if hours_since_check > 24:
                            recommendations.append(f"URGENT: {plant.get('plant_name')} has been ready for {hours_since_check:.1f} hours")
                    except ValueError:
                        pass
        else:
            if summary.get("next_ready_time"):
                try:
                    next_time = datetime.fromisoformat(summary["next_ready_time"])
                    hours_until_ready = (next_time - datetime.now()).total_seconds() / 3600
                    recommendations.append(f"Next plant ready in {hours_until_ready:.1f} hours")
                except ValueError:
                    recommendations.append("Next plant ready time unknown")
            else:
                recommendations.append("No plants currently being tracked")
        
        return recommendations
    
    def get_plant_schedule(self) -> Dict[str, Any]:
        """Get a detailed schedule of all plants"""
        try:
            plants = self.plant_tracker.get_all_plants()
            current_time = datetime.now()
            
            schedule = {
                "current_time": current_time.isoformat(),
                "plants": []
            }
            
            for plant in plants:
                plant_schedule = {
                    "plant_name": plant.get("plant_name"),
                    "current_stage": plant.get("current_stage"),
                    "next_stage": plant.get("next_stage"),
                    "time_to_next_hours": plant.get("time_to_next_hours"),
                    "is_ready": plant.get("is_ready", False),
                    "last_checked": plant.get("last_checked"),
                    "next_check_time": plant.get("next_check_time")
                }
                
                # Calculate time until next check
                next_check_str = plant.get("next_check_time")
                if next_check_str:
                    try:
                        next_check = datetime.fromisoformat(next_check_str)
                        hours_until_check = (next_check - current_time).total_seconds() / 3600
                        plant_schedule["hours_until_check"] = max(0, hours_until_check)
                    except ValueError:
                        plant_schedule["hours_until_check"] = None
                
                schedule["plants"].append(plant_schedule)
            
            return schedule
            
        except Exception as e:
            logger.error(f"Failed to get plant schedule: {e}")
            return {"error": str(e), "plants": []}
    
    def export_schedule_csv(self, output_file: str = "data/plant_schedule.csv") -> bool:
        """Export plant schedule to CSV format"""
        try:
            import csv
            
            schedule = self.get_plant_schedule()
            if "error" in schedule:
                return False
            
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'plant_name', 'current_stage', 'next_stage', 'time_to_next_hours',
                    'is_ready', 'last_checked', 'next_check_time', 'hours_until_check'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for plant in schedule["plants"]:
                    writer.writerow(plant)
            
            logger.info(f"Plant schedule exported to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export schedule to CSV: {e}")
            return False
