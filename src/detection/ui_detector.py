"""
Main UI detection orchestrator
"""
from typing import Optional, List
from src.core.element import UIElement, ElementSearchCriteria, DetectionMethod
from src.detection.template_matcher import TemplateMatcher
from src.detection.visual_detector import VisualDetector
from src.detection.ocr_detector import OCRDetector
from src.utils.logger import logger

class UIDetector:
    """Main UI detection orchestrator that tries multiple detection methods"""
    
    def __init__(self):
        self.template_matcher = TemplateMatcher()
        self.visual_detector = VisualDetector()
        self.ocr_detector = OCRDetector()
        
        # Priority order for detection methods
        self.method_priority = [
            DetectionMethod.TEMPLATE,
            DetectionMethod.VISUAL,
            DetectionMethod.OCR,
            DetectionMethod.COORDINATES
        ]
    
    def find_element(self, criteria: ElementSearchCriteria, silent: bool = False) -> Optional[UIElement]:
        """Find a UI element using the best available detection method"""
        logger.debug(f"Searching for element '{criteria.name}' using methods: {[m.value for m in criteria.detection_methods]}")
        
        # Try each detection method in order of preference
        for method in criteria.detection_methods:
            try:
                element = self._try_detection_method(criteria, method)
                if element and element.confidence >= criteria.confidence_threshold:
                    return element
                elif element:
                    logger.debug(f"Found '{criteria.name}' using {method.value} but confidence {element.confidence:.3f} below threshold {criteria.confidence_threshold}")
                    
            except Exception as e:
                logger.debug(f"Detection method {method.value} failed for '{criteria.name}': {e}")
                continue
        
        if not silent:
            logger.warning(f"Could not find element '{criteria.name}' using any available method")
        return None
    
    def find_elements(self, criteria_list: List[ElementSearchCriteria]) -> List[UIElement]:
        """Find multiple UI elements"""
        elements = []
        
        for criteria in criteria_list:
            element = self.find_element(criteria)
            if element:
                elements.append(element)
        
        logger.info(f"Found {len(elements)}/{len(criteria_list)} elements")
        return elements
    
    def _try_detection_method(self, criteria: ElementSearchCriteria, method: DetectionMethod) -> Optional[UIElement]:
        """Try a specific detection method"""
        if method == DetectionMethod.TEMPLATE:
            return self.template_matcher.find_element(criteria)
        elif method == DetectionMethod.VISUAL:
            return self.visual_detector.find_element(criteria)
        elif method == DetectionMethod.OCR:
            return self.ocr_detector.find_element(criteria)
        elif method == DetectionMethod.COORDINATES:
            # Fallback to coordinates if specified in metadata
            if criteria.metadata and 'coordinates' in criteria.metadata:
                coords = criteria.metadata['coordinates']
                from src.core.element import BoundingBox, Coordinates
                # Create a small bounding box around the coordinates
                bbox = BoundingBox(coords[0] - 10, coords[1] - 10, 20, 20)
                return UIElement(
                    name=criteria.name,
                    element_type=criteria.element_type,
                    detection_method=method,
                    confidence=1.0,  # Assume perfect confidence for known coordinates
                    bounding_box=bbox,
                    metadata=criteria.metadata
                )
        
        return None
    
    def is_element_present(self, criteria: ElementSearchCriteria) -> bool:
        """Check if an element is present without returning the full element"""
        element = self.find_element(criteria, silent=True)
        return element is not None and element.confidence >= criteria.confidence_threshold

