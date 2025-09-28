"""
UI Element definitions and utilities
"""
from dataclasses import dataclass
from typing import Optional, Tuple, List, Any, Dict
from enum import Enum

class ElementType(Enum):
    BUTTON = "button"
    INPUT_FIELD = "input_field"
    TEXT = "text"
    IMAGE = "image"
    CONTAINER = "container"
    UNKNOWN = "unknown"

class DetectionMethod(Enum):
    TEMPLATE = "template"
    VISUAL = "visual"
    OCR = "ocr"
    COORDINATES = "coordinates"
    HYBRID = "hybrid"

@dataclass
class Coordinates:
    """Represents screen coordinates"""
    x: int
    y: int
    
    def __str__(self) -> str:
        return f"({self.x}, {self.y})"
    
    def __add__(self, other: 'Coordinates') -> 'Coordinates':
        return Coordinates(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Coordinates') -> 'Coordinates':
        return Coordinates(self.x - other.x, self.y - other.y)

@dataclass
class BoundingBox:
    """Represents a rectangular area on screen"""
    x: int
    y: int
    width: int
    height: int
    
    @property
    def center(self) -> Coordinates:
        """Get center coordinates of the bounding box"""
        return Coordinates(self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def top_left(self) -> Coordinates:
        """Get top-left coordinates"""
        return Coordinates(self.x, self.y)
    
    @property
    def bottom_right(self) -> Coordinates:
        """Get bottom-right coordinates"""
        return Coordinates(self.x + self.width, self.y + self.height)
    
    def contains(self, coords: Coordinates) -> bool:
        """Check if coordinates are within this bounding box"""
        return (self.x <= coords.x <= self.x + self.width and 
                self.y <= coords.y <= self.y + self.height)

@dataclass
class UIElement:
    """Represents a UI element that can be detected and interacted with"""
    name: str
    element_type: ElementType
    detection_method: DetectionMethod
    confidence: float
    bounding_box: BoundingBox
    template_path: Optional[str] = None
    search_text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @property
    def center(self) -> Coordinates:
        """Get center coordinates for clicking"""
        return self.bounding_box.center
    
    @property
    def clickable(self) -> bool:
        """Check if this element can be clicked"""
        return self.element_type in [ElementType.BUTTON, ElementType.INPUT_FIELD]
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if detection confidence is above threshold"""
        return self.confidence >= threshold

@dataclass
class ElementSearchCriteria:
    """Criteria for searching UI elements"""
    name: str
    element_type: ElementType
    template_path: Optional[str] = None
    search_text: Optional[str] = None
    confidence_threshold: float = 0.8
    detection_methods: List[DetectionMethod] = None
    region: Optional[BoundingBox] = None  # Search only in this region
    metadata: Optional[dict] = None  # Additional metadata
    
    def __post_init__(self):
        if self.detection_methods is None:
            self.detection_methods = [DetectionMethod.TEMPLATE, DetectionMethod.VISUAL, DetectionMethod.OCR]
