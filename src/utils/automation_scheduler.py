"""
Automation scheduler utility for managing bot operations based on plant status
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from src.utils.bot_execution_tracker import GardeningBotTracker
from src.utils.logger import logger

class AutomationScheduler:
    """Manages automation scheduling based on plant status data"""
    
    def __init__(self):
        self.gardening_tracker = GardeningBotTracker()
    
    def get_automation_status(self) -> Dict[str, Any]:
        """Get current automation status and recommendations"""
        try:
            # Check if it's time to run the bot
            should_run = self.gardening_tracker.is_time_to_run()
            next_run_time = self.gardening_tracker.get_next_run_time()
            
            # Get recent plant status history
            plant_history = self.gardening_tracker.get_plant_status_history(limit=5)
            
            # Get execution stats
            stats = self.gardening_tracker.get_gardening_stats()
            
            # Generate recommendations
            recommendations = self._generate_recommendations(plant_history, should_run, next_run_time)
            
            return {
                "should_run_bot": should_run,
                "next_run_time": next_run_time.isoformat() if next_run_time else None,
                "recent_plant_status": plant_history,
                "execution_stats": stats,
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
    
    def _generate_recommendations(self, plant_history: List[Dict], should_run: bool, next_run_time: Optional[datetime]) -> List[str]:
        """Generate automation recommendations based on plant status"""
        recommendations = []
        
        if should_run:
            recommendations.append("Run gardening bot now - it's time for the next scheduled run")
        else:
            if next_run_time:
                hours_until_next = (next_run_time - datetime.now()).total_seconds() / 3600
                recommendations.append(f"Next gardening bot run in {hours_until_next:.1f} hours")
            else:
                recommendations.append("No scheduled gardening bot runs")
        
        # Check recent plant status
        if plant_history:
            latest_status = plant_history[0]  # Most recent
            plant_name = latest_status.get("plant_name", "Unknown")
            current_stage = latest_status.get("current_stage", "Unknown")
            time_to_next = latest_status.get("time_to_next_hours", 0)
            
            if time_to_next <= 0:
                recommendations.append(f"Plant {plant_name} is ready for harvest (stage: {current_stage})")
            else:
                recommendations.append(f"Plant {plant_name} will be ready in {time_to_next:.1f} hours (stage: {current_stage})")
        else:
            recommendations.append("No recent plant status data available")
        
        return recommendations
    
    def get_plant_schedule(self) -> Dict[str, Any]:
        """Get a detailed schedule of all plants"""
        try:
            # Get plant status history and execution history
            plant_history = self.gardening_tracker.get_plant_status_history(limit=50)
            execution_history = self.gardening_tracker.get_execution_history(limit=10)
            current_time = datetime.now()
            
            schedule = {
                "current_time": current_time.isoformat(),
                "plant_status_history": plant_history,
                "execution_history": execution_history,
                "next_run_time": self.gardening_tracker.get_next_run_time().isoformat() if self.gardening_tracker.get_next_run_time() else None,
                "should_run_now": self.gardening_tracker.is_time_to_run()
            }
            
            return schedule
            
        except Exception as e:
            logger.error(f"Failed to get plant schedule: {e}")
            return {"error": str(e), "plant_status_history": [], "execution_history": []}
    
    def export_schedule_csv(self, output_file: str = "data/gardening_schedule.csv") -> bool:
        """Export gardening schedule to CSV format"""
        try:
            import csv
            
            schedule = self.get_plant_schedule()
            if "error" in schedule:
                return False
            
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                # Export plant status history
                if schedule.get("plant_status_history"):
                    fieldnames = [
                        'timestamp', 'plant_name', 'current_stage', 'next_stage', 
                        'time_to_next_hours', 'effective_speed_percent', 'likes'
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for plant_status in schedule["plant_status_history"]:
                        row = {
                            'timestamp': plant_status.get('timestamp', ''),
                            'plant_name': plant_status.get('plant_name', ''),
                            'current_stage': plant_status.get('current_stage', ''),
                            'next_stage': plant_status.get('next_stage', ''),
                            'time_to_next_hours': plant_status.get('time_to_next_hours', ''),
                            'effective_speed_percent': plant_status.get('effective_speed_percent', ''),
                            'likes': ', '.join(plant_status.get('likes', []))
                        }
                        writer.writerow(row)
            
            logger.info(f"Gardening schedule exported to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export schedule to CSV: {e}")
            return False
