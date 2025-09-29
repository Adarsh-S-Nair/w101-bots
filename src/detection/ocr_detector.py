"""
OCR-based detection module
"""
from typing import Optional
import cv2
import numpy as np
import pytesseract

from src.core.element import UIElement, ElementSearchCriteria, ElementType, DetectionMethod, BoundingBox, Coordinates
# from src.utils.screenshot import ScreenshotManager  # Disabled for GitHub
from src.utils.logger import logger

class OCRDetector:
    """OCR-based text detection for UI elements"""
    
    def __init__(self):
        # self.screenshot_manager = ScreenshotManager()  # Disabled for GitHub
        # Configure pytesseract if needed
        self.tesseract_available = False
        try:
            # Try to get tesseract version to verify it's working
            pytesseract.get_tesseract_version()
            self.tesseract_available = True
            logger.info("OCR detector initialized successfully")
        except Exception as e:
            logger.warning(f"OCR detector initialization warning: {e}")
            logger.warning("OCR functionality will be disabled - tesseract not available")
            self.tesseract_available = False
    def find_element(self, criteria: ElementSearchCriteria) -> Optional[UIElement]:
        """Find an element using OCR text detection"""
        if not criteria.search_text:
            logger.debug(f"No search text provided for OCR detection of '{criteria.name}'")
            return None
        
        # Check if tesseract is available
        if not self.tesseract_available:
            logger.debug(f"OCR detection skipped for '{criteria.name}' - tesseract not available")
            return None
        
        try:
            # Take current screenshot (directly)
            import pyautogui
            screenshot = pyautogui.screenshot()
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            if screenshot is None:
                logger.error("Failed to take screenshot for OCR detection")
                return None
            
            # Extract text regions from the screenshot
            text_regions = self._extract_text_regions(screenshot)
            
            # Find the specific text we're looking for
            bounding_box = self._find_text_position(text_regions, criteria.search_text)
            
            if bounding_box:
                logger.info(f"Found text '{criteria.search_text}' at {bounding_box}")
                return UIElement(
                    name=criteria.name,
                    element_type=criteria.element_type,
                    detection_method=DetectionMethod.OCR,
                    confidence=0.9,  # High confidence for exact text match
                    bounding_box=bounding_box,
                    metadata=criteria.metadata
                )
            else:
                logger.debug(f"Text '{criteria.search_text}' not found on screen")
                return None
            
        except Exception as e:
            logger.error(f"OCR detection failed for '{criteria.name}': {e}")
            return None
    
    def _extract_text_regions(self, screenshot: np.ndarray) -> list:
        """Extract text regions from screenshot using pytesseract"""
        try:
            # Convert to grayscale for better OCR
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            
            # Apply some preprocessing to improve OCR accuracy
            # Increase contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            
            # Use pytesseract to get text with bounding boxes
            # Using PSM 6 for uniform text block
            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT, config='--psm 6')
            
            # Extract text regions with their bounding boxes
            text_regions = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                if text:  # Only include non-empty text
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    conf = int(data['conf'][i])
                    
                    if conf > 30:  # Only include text with reasonable confidence
                        text_regions.append({
                            'text': text,
                            'bbox': BoundingBox(x, y, w, h),
                            'confidence': conf
                        })
            
            logger.debug(f"Extracted {len(text_regions)} text regions from screenshot")
            return text_regions
            
        except Exception as e:
            logger.error(f"Failed to extract text regions: {e}")
            return []
    
    def _find_text_position(self, text_regions: list, search_text: str) -> Optional[BoundingBox]:
        """Find position of specific text in extracted regions"""
        if not text_regions:
            return None
        
        # Try exact match first
        for region in text_regions:
            if region['text'].lower() == search_text.lower():
                logger.debug(f"Exact match found: '{region['text']}' at {region['bbox']}")
                return region['bbox']
        
        # Try partial match (contains)
        for region in text_regions:
            if search_text.lower() in region['text'].lower():
                logger.debug(f"Partial match found: '{region['text']}' contains '{search_text}' at {region['bbox']}")
                return region['bbox']
        
        # Try word-by-word matching for multi-word phrases
        search_words = search_text.lower().split()
        if len(search_words) > 1:
            # Look for consecutive regions that match the words
            for i in range(len(text_regions) - len(search_words) + 1):
                match_found = True
                for j, word in enumerate(search_words):
                    if word not in text_regions[i + j]['text'].lower():
                        match_found = False
                        break
                
                if match_found:
                    # Calculate combined bounding box
                    first_bbox = text_regions[i]['bbox']
                    last_bbox = text_regions[i + len(search_words) - 1]['bbox']
                    
                    combined_bbox = BoundingBox(
                        first_bbox.x,
                        first_bbox.y,
                        last_bbox.x + last_bbox.width - first_bbox.x,
                        max(first_bbox.height, last_bbox.height)
                    )
                    
                    logger.debug(f"Multi-word match found: '{search_text}' at {combined_bbox}")
                    return combined_bbox
        
        return None
