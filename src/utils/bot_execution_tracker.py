"""
Bot execution tracker module for managing bot run times and scheduling
Tracks execution times and calculates next run times for different bot types
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from src.utils.logger import logger


class BotExecutionTracker:
    """Tracks bot execution times and schedules next runs"""
    
    def __init__(self, bot_type: str, tracking_dir: str = "bot_tracking"):
        """
        Initialize the bot execution tracker
        
        Args:
            bot_type: Type of bot (e.g., 'trivia', 'gardening', 'housing')
            tracking_dir: Directory to store tracking files
        """
        self.bot_type = bot_type
        self.tracking_dir = tracking_dir
        self.tracking_file = os.path.join(tracking_dir, f"{bot_type}_execution.json")
        
        # Create tracking directory if it doesn't exist
        os.makedirs(tracking_dir, exist_ok=True)
        
        # Load existing tracking data
        self.tracking_data = self._load_tracking_data()
    
    def _load_tracking_data(self) -> Dict[str, Any]:
        """Load existing tracking data from JSON file"""
        try:
            if os.path.exists(self.tracking_file):
                with open(self.tracking_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Loaded tracking data for {self.bot_type} bot")
                    return data
            else:
                logger.info(f"No existing tracking data found for {self.bot_type} bot")
                return {}
        except Exception as e:
            logger.error(f"Error loading tracking data for {self.bot_type} bot: {e}")
            return {}
    
    def reload_tracking_data(self) -> bool:
        """Reload tracking data from file (useful when reusing tracker instance)"""
        try:
            self.tracking_data = self._load_tracking_data()
            logger.info(f"Reloaded tracking data for {self.bot_type} bot")
            return True
        except Exception as e:
            logger.error(f"Error reloading tracking data for {self.bot_type} bot: {e}")
            return False
    
    def _save_tracking_data(self) -> bool:
        """Save tracking data to JSON file"""
        try:
            with open(self.tracking_file, 'w') as f:
                json.dump(self.tracking_data, f, indent=2, default=str)
            logger.info(f"Saved tracking data for {self.bot_type} bot")
            return True
        except Exception as e:
            logger.error(f"Error saving tracking data for {self.bot_type} bot: {e}")
            return False
    
    def start_execution(self, additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Record the start of bot execution
        
        Args:
            additional_data: Any additional data to track (e.g., trivia count, plant count)
            
        Returns:
            Dict containing execution info
        """
        start_time = datetime.now()
        execution_id = f"{self.bot_type}_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        execution_data = {
            "execution_id": execution_id,
            "bot_type": self.bot_type,
            "start_time": start_time,
            "status": "running",
            "additional_data": additional_data or {}
        }
        
        # Preserve previous executions and add the current one
        # Note: We do NOT save to file here - only save on successful completion
        existing_executions = self.tracking_data.get("executions", [])
        # Don't add current execution yet - it will be added when completed
        self.tracking_data["executions"] = existing_executions  # Keep previous executions
        self.tracking_data["last_execution"] = execution_data
        
        logger.info(f"Started {self.bot_type} bot execution: {execution_id} (keeping {len(existing_executions)} previous executions)")
        return execution_data
    
    def complete_execution(self, execution_id: str, success: bool = True, 
                          execution_summary: Optional[Dict[str, Any]] = None,
                          next_run_interval_hours: float = 20.0) -> Dict[str, Any]:
        """
        Record the completion of bot execution and calculate next run time
        
        Args:
            execution_id: ID of the execution to complete
            success: Whether the execution was successful
            execution_summary: Summary of what was accomplished
            next_run_interval_hours: Hours until next run (default 20.0 for trivia)
            
        Returns:
            Dict containing completion info and next run time
        """
        end_time = datetime.now()
        next_run_time = end_time + timedelta(hours=next_run_interval_hours)
        
        # Get the execution record to complete from last_execution
        execution_to_complete = self.tracking_data.get("last_execution")
        
        if not execution_to_complete or execution_to_complete.get("execution_id") != execution_id:
            logger.error(f"Execution ID {execution_id} not found in tracking data or doesn't match last execution")
            return {}
        
        # Complete the execution
        execution_to_complete["end_time"] = end_time
        execution_to_complete["duration_seconds"] = (end_time - execution_to_complete["start_time"]).total_seconds()
        execution_to_complete["duration_formatted"] = str(end_time - execution_to_complete["start_time"]).split('.')[0]  # Remove microseconds
        execution_to_complete["status"] = "completed" if success else "failed"
        execution_to_complete["success"] = success
        execution_to_complete["execution_summary"] = execution_summary or {}
        execution_to_complete["next_run_time"] = next_run_time
        
        # Add completed execution to the list (keeping history)
        existing_executions = self.tracking_data.get("executions", [])
        existing_executions.append(execution_to_complete)
        
        self.tracking_data = {
            "executions": existing_executions,
            "last_execution": execution_to_complete,
            "next_run_time": next_run_time
        }
        
        logger.info(f"Completed execution {execution_id}. Total executions in history: {len(existing_executions)}")
        
        # Only save to file if execution was successful
        if success:
            self._save_tracking_data()
            logger.info(f"Saved tracking data for successful {self.bot_type} bot execution: {execution_id}")
        else:
            logger.info(f"Not saving tracking data for failed {self.bot_type} bot execution: {execution_id}")
        
        completion_info = {
            "execution_id": execution_id,
            "end_time": end_time,
            "next_run_time": next_run_time,
            "success": success,
            "execution_summary": execution_summary or {}
        }
        
        status_text = "completed successfully" if success else "failed"
        logger.info(f"{self.bot_type} bot execution {status_text}: {execution_id}")
        if success:
            logger.info(f"Next {self.bot_type} bot run scheduled for: {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return completion_info
    
    def get_last_execution_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the last execution"""
        return self.tracking_data.get("last_execution")
    
    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled run time"""
        next_run_str = self.tracking_data.get("next_run_time")
        if next_run_str:
            if isinstance(next_run_str, str):
                return datetime.fromisoformat(next_run_str)
            return next_run_str
        return None
    
    def is_time_to_run(self) -> bool:
        """Check if it's time to run the bot based on the next run time"""
        next_run = self.get_next_run_time()
        if not next_run:
            logger.info(f"No previous {self.bot_type} bot execution found - time to run!")
            return True
        
        current_time = datetime.now()
        is_ready = current_time >= next_run
        
        if is_ready:
            logger.info(f"It's time to run the {self.bot_type} bot (scheduled for {next_run.strftime('%Y-%m-%d %H:%M:%S')})")
        else:
            time_until_next = next_run - current_time
            logger.info(f"{self.bot_type} bot not ready to run yet. Next run in: {str(time_until_next).split('.')[0]}")
        
        return is_ready
    
    def get_execution_history(self, limit: int = 10) -> list:
        """Get recent execution history"""
        executions = self.tracking_data.get("executions", [])
        return executions[-limit:] if limit > 0 else executions
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        executions = self.tracking_data.get("executions", [])
        
        if not executions:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "success_rate": 0.0,
                "average_duration_seconds": 0.0
            }
        
        total = len(executions)
        successful = sum(1 for e in executions if e.get("success", False))
        failed = total - successful
        success_rate = (successful / total * 100) if total > 0 else 0.0
        
        # Calculate average duration for completed executions
        completed_executions = [e for e in executions if e.get("duration_seconds") is not None]
        avg_duration = sum(e["duration_seconds"] for e in completed_executions) / len(completed_executions) if completed_executions else 0.0
        
        return {
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": round(success_rate, 2),
            "average_duration_seconds": round(avg_duration, 2),
            "average_duration_formatted": str(timedelta(seconds=int(avg_duration))).split('.')[0]
        }


class TriviaBotTracker(BotExecutionTracker):
    """Specialized tracker for trivia bot with 20-hour intervals"""
    
    def __init__(self, tracking_dir: str = "bot_tracking"):
        super().__init__("trivia", tracking_dir)
    
    def complete_execution(self, execution_id: str, success: bool = True, 
                          trivia_count: int = 0, execution_summary: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Complete trivia bot execution with trivia-specific data
        
        Args:
            execution_id: ID of the execution to complete
            success: Whether the execution was successful
            trivia_count: Number of trivias completed
            execution_summary: Additional execution summary data
            
        Returns:
            Dict containing completion info and next run time
        """
        summary = execution_summary or {}
        summary["trivias_completed"] = trivia_count
        
        return super().complete_execution(
            execution_id=execution_id,
            success=success,
            execution_summary=summary,
            next_run_interval_hours=20
        )


class GardeningBotTracker(BotExecutionTracker):
    """Specialized tracker for gardening bot with plant-specific data"""
    
    def __init__(self, tracking_dir: str = "bot_tracking"):
        super().__init__("gardening", tracking_dir)
    
    def complete_execution(self, execution_id: str, success: bool = True, 
                          plant_data: Optional[Dict[str, Any]] = None, 
                          actions_performed: Optional[List[str]] = None,
                          execution_summary: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Complete gardening bot execution with gardening-specific data
        
        Args:
            execution_id: ID of the execution to complete
            success: Whether the execution was successful
            plant_data: Current plant status data
            actions_performed: List of actions performed (e.g., ['harvest', 'replant', 'needs_handling'])
            execution_summary: Additional execution summary data
            
        Returns:
            Dict containing completion info and next run time
        """
        summary = execution_summary or {}
        summary["plant_data"] = plant_data or {}
        summary["actions_performed"] = actions_performed or []
        
        # Calculate next run time based on plant status
        next_run_interval_hours = self._calculate_next_run_interval(plant_data)
        
        return super().complete_execution(
            execution_id=execution_id,
            success=success,
            execution_summary=summary,
            next_run_interval_hours=next_run_interval_hours
        )
    
    def _calculate_next_run_interval(self, plant_data: Optional[Dict[str, Any]]) -> float:
        """
        Calculate next run interval based on plant status
        
        Args:
            plant_data: Current plant status data
            
        Returns:
            Hours until next run (using exact time_to_next_hours)
        """
        if not plant_data:
            # Default to 6 hours if no plant data
            return 6.0
        
        time_to_next = plant_data.get('time_to_next_hours', 0)
        
        if time_to_next <= 0:
            # Plant is ready, check again in 1 hour
            return 1.0
        else:
            # Use the exact time_to_next_hours from plant data
            # Add a small buffer (0.5 hours) to ensure we don't miss the timing
            return max(0.5, time_to_next + 0.5)
    
    def update_plant_status(self, plant_status: Dict[str, Any]) -> bool:
        """
        Update plant status in the current execution
        
        Args:
            plant_status: Plant status data to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the current execution
            current_execution = self.tracking_data.get("last_execution")
            if not current_execution or current_execution.get("status") != "running":
                logger.warning("No active gardening execution to update plant status")
                return False
            
            # Add plant status to execution summary
            if "execution_summary" not in current_execution:
                current_execution["execution_summary"] = {}
            
            if "plant_status_updates" not in current_execution["execution_summary"]:
                current_execution["execution_summary"]["plant_status_updates"] = []
            
            # Add timestamp to plant status
            plant_status_with_timestamp = {
                **plant_status,
                "timestamp": datetime.now().isoformat()
            }
            
            current_execution["execution_summary"]["plant_status_updates"].append(plant_status_with_timestamp)
            
            # Note: We do NOT save to file here - only save on successful completion
            # The plant status will be saved when complete_execution() is called with success=True
            logger.info(f"Updated plant status in memory for {self.bot_type} execution")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update plant status in tracker: {e}")
            return False
    
    def get_plant_status_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent plant status history from executions
        
        Args:
            limit: Maximum number of status updates to return
            
        Returns:
            List of plant status updates
        """
        try:
            all_updates = []
            
            executions = self.tracking_data.get("executions", [])
            logger.debug(f"Found {len(executions)} executions in tracking data")
            
            # Get plant status updates from all executions
            for execution in executions:
                execution_summary = execution.get("execution_summary", {})
                
                # Check for plant_status_updates array (newer format)
                plant_updates = execution_summary.get("plant_status_updates", [])
                if plant_updates:
                    logger.debug(f"Found {len(plant_updates)} plant_status_updates in execution")
                all_updates.extend(plant_updates)
                
                # Also check for plant_data directly (for backward compatibility)
                plant_data = execution_summary.get("plant_data")
                if plant_data and isinstance(plant_data, dict):
                    logger.debug(f"Found plant_data in execution: {plant_data.get('current_stage', 'N/A')}")
                    # Add timestamp if not present
                    if "timestamp" not in plant_data:
                        plant_data_with_timestamp = {
                            **plant_data,
                            "timestamp": execution.get("end_time", execution.get("start_time", ""))
                        }
                    else:
                        plant_data_with_timestamp = plant_data
                    all_updates.append(plant_data_with_timestamp)
            
            logger.debug(f"Total plant status updates found: {len(all_updates)}")
            
            # Sort by timestamp (most recent first)
            all_updates.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return all_updates[:limit] if limit > 0 else all_updates
            
        except Exception as e:
            logger.error(f"Failed to get plant status history: {e}")
            return []
    
    def get_gardening_stats(self) -> Dict[str, Any]:
        """
        Get gardening-specific statistics
        
        Returns:
            Dict containing gardening statistics
        """
        try:
            base_stats = self.get_execution_stats()
            
            # Add gardening-specific stats
            total_harvests = 0
            total_replants = 0
            total_needs_handled = 0
            
            for execution in self.tracking_data.get("executions", []):
                actions = execution.get("execution_summary", {}).get("actions_performed", [])
                total_harvests += actions.count("harvest")
                total_replants += actions.count("replant")
                total_needs_handled += actions.count("needs_handling")
            
            gardening_stats = {
                **base_stats,
                "total_harvests": total_harvests,
                "total_replants": total_replants,
                "total_needs_handled": total_needs_handled,
                "average_actions_per_run": (total_harvests + total_replants + total_needs_handled) / max(base_stats["total_executions"], 1)
            }
            
            return gardening_stats
            
        except Exception as e:
            logger.error(f"Failed to get gardening stats: {e}")
            return self.get_execution_stats()