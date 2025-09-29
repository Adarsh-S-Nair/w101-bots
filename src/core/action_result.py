"""
Action result classes for bot operations
"""
from dataclasses import dataclass
from typing import Optional, Any, Dict
from enum import Enum

class ActionResultStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    SKIP = "skip"

@dataclass
class ActionResult:
    """Generic result for bot actions"""
    status: ActionResultStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[Exception] = None
    retry_count: int = 0
    max_retries: int = 3
    
    @property
    def success(self) -> bool:
        return self.status == ActionResultStatus.SUCCESS
    
    @property
    def should_retry(self) -> bool:
        return (self.status == ActionResultStatus.RETRY and 
                self.retry_count < self.max_retries)
    
    @classmethod
    def success_result(cls, message: str, data: Optional[Dict[str, Any]] = None) -> 'ActionResult':
        """Create a successful result"""
        return cls(
            status=ActionResultStatus.SUCCESS,
            message=message,
            data=data
        )
    
    @classmethod
    def failure_result(cls, message: str, error: Optional[Exception] = None, 
                      data: Optional[Dict[str, Any]] = None) -> 'ActionResult':
        """Create a failure result"""
        return cls(
            status=ActionResultStatus.FAILURE,
            message=message,
            error=error,
            data=data
        )
    
    @classmethod
    def retry_result(cls, message: str, retry_count: int = 0, 
                    max_retries: int = 3) -> 'ActionResult':
        """Create a retry result"""
        return cls(
            status=ActionResultStatus.RETRY,
            message=message,
            retry_count=retry_count,
            max_retries=max_retries
        )

