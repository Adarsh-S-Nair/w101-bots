"""
Process detection utilities
"""
import psutil
from typing import List, Optional
from src.utils.logger import logger

class ProcessUtils:
    """Utilities for detecting and managing running processes"""
    
    @staticmethod
    def is_process_running(process_name: str) -> bool:
        """
        Check if a process with the given name is currently running
        
        Args:
            process_name: Name of the process to check for
            
        Returns:
            True if the process is running, False otherwise
        """
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if process_name.lower() in proc.info['name'].lower():
                        logger.info(f"Found running process: {proc.info['name']} (PID: {proc.info['pid']})")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Process may have terminated or we don't have access
                    continue
            
            logger.info(f"No running process found with name containing: {process_name}")
            return False
            
        except Exception as e:
            logger.error(f"Error checking for running process '{process_name}': {e}")
            return False
    
    @staticmethod
    def get_processes_by_name(process_name: str) -> List[psutil.Process]:
        """
        Get all processes that match the given name
        
        Args:
            process_name: Name of the process to search for
            
        Returns:
            List of matching processes
        """
        matching_processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if process_name.lower() in proc.info['name'].lower():
                        matching_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            logger.error(f"Error searching for processes with name '{process_name}': {e}")
        
        return matching_processes
    
    @staticmethod
    def is_wizard101_running() -> bool:
        """
        Check if Wizard101GraphicalClient is currently running
        
        Returns:
            True if Wizard101GraphicalClient is running, False otherwise
        """
        # Check for various possible process names
        wizard101_names = [
            "Wizard101GraphicalClient",
            "WizardGraphicalClient", 
            "Wizard101",
            "Wizard101.exe",
            "WizardGraphicalClient.exe"
        ]
        
        for name in wizard101_names:
            if ProcessUtils.is_process_running(name):
                return True
        
        return False
    
    @staticmethod
    def get_wizard101_processes() -> List[psutil.Process]:
        """
        Get all Wizard101GraphicalClient processes
        
        Returns:
            List of Wizard101GraphicalClient processes
        """
        all_processes = []
        wizard101_names = [
            "Wizard101GraphicalClient",
            "WizardGraphicalClient", 
            "Wizard101",
            "Wizard101.exe",
            "WizardGraphicalClient.exe"
        ]
        
        for name in wizard101_names:
            processes = ProcessUtils.get_processes_by_name(name)
            all_processes.extend(processes)
        
        # Remove duplicates based on PID
        unique_processes = []
        seen_pids = set()
        for proc in all_processes:
            if proc.pid not in seen_pids:
                unique_processes.append(proc)
                seen_pids.add(proc.pid)
        
        return unique_processes
