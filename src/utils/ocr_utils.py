"""
OCR utilities for reading game UI popups and text
Reusable across different automation modules
"""
import cv2
import numpy as np
import pytesseract
import pyautogui
from src.core.action_result import ActionResult
from src.utils.logger import logger


class OCRUtils:
    """Utility class for OCR operations on game UI elements"""
    
    def __init__(self):
        # Set tesseract path for Windows
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    def read_plant_popup(self) -> ActionResult:
        """Read plant popup content using targeted area OCR"""
        try:
            logger.info("Reading plant popup content...")
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screen_width, screen_height = pyautogui.size()
            
            # Define potential popup areas (left and right sides)
            popup_areas = [
                # Left side (20% width, 60% height, starting at 5% from left, 15% from top)
                {
                    'name': 'left_side',
                    'x': int(screen_width * 0.05),
                    'y': int(screen_height * 0.15),
                    'width': int(screen_width * 0.2),
                    'height': int(screen_height * 0.6)
                },
                # Right side (20% width, 60% height, starting at 75% from left, 15% from top)
                {
                    'name': 'right_side',
                    'x': int(screen_width * 0.75),
                    'y': int(screen_height * 0.15),
                    'width': int(screen_width * 0.2),
                    'height': int(screen_height * 0.6)
                }
            ]
            
            # Convert PIL to OpenCV format
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Check each area for popup content
            for area in popup_areas:
                logger.info(f"Checking {area['name']} for plant popup...")
                
                # Extract area from screenshot
                roi = screenshot_cv[
                    area['y']:area['y'] + area['height'],
                    area['x']:area['x'] + area['width']
                ]
                
                # Convert to grayscale and preprocess for better OCR
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                
                # Try multiple preprocessing approaches
                preprocessing_methods = [
                    # Method 1: Advanced preprocessing
                    lambda g: self._advanced_preprocessing(g),
                    # Method 2: Simple preprocessing (fallback)
                    lambda g: self._simple_preprocessing(g),
                    # Method 3: No preprocessing (raw grayscale)
                    lambda g: g
                ]
                
                best_text = ""
                best_score = 0
                
                for method_idx, preprocess_method in enumerate(preprocessing_methods):
                    try:
                        processed_image = preprocess_method(gray)
                        logger.debug(f"Trying preprocessing method {method_idx + 1}")
                        
                        # Try OCR with this processed image - use multiple PSM modes for better accuracy
                        psm_modes = ['--psm 4', '--psm 6', '--psm 8', '--psm 13']
                        test_text = ""
                        
                        for psm in psm_modes:
                            try:
                                temp_text = pytesseract.image_to_string(processed_image, config=psm)
                                temp_score = self._score_ocr_text(temp_text)
                                if temp_score > self._score_ocr_text(test_text):
                                    test_text = temp_text
                            except:
                                continue
                        
                        # Score this result
                        score = self._score_ocr_text(test_text)
                        
                        if score > best_score:
                            best_score = score
                            best_text = test_text
                            logger.debug(f"New best score: {score} with method {method_idx + 1}")
                            
                    except Exception as e:
                        logger.debug(f"Preprocessing method {method_idx + 1} failed: {e}")
                        continue
                
                # If we found something, use it
                if best_text.strip():
                    # Clean up common OCR errors
                    cleaned_text = self._clean_ocr_text(best_text)
                    
                    logger.info(f"Found potential plant popup in {area['name']} (score: {best_score})")
                    logger.info(f"Raw OCR text from {area['name']}:")
                    logger.info(best_text)
                    logger.info(f"Cleaned OCR text:")
                    logger.info(cleaned_text)
                    return ActionResult.success_result("Plant popup found", data=cleaned_text.strip())
                
                # If no good result found, log what we did find for debugging
                if best_text.strip():
                    logger.info(f"OCR found text in {area['name']} but score too low ({best_score}):")
                    logger.info(best_text[:200] + "..." if len(best_text) > 200 else best_text)
            
            logger.warning("No plant popup found in either side")
            return ActionResult.failure_result("No plant popup found")
            
        except Exception as e:
            logger.error(f"Failed to read plant popup: {e}")
            return ActionResult.failure_result("Failed to read plant popup", error=e)
    
    def _advanced_preprocessing(self, gray_image):
        """Advanced image preprocessing for OCR"""
        # 1. Increase contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        processed = clahe.apply(gray_image)
        
        # 2. Apply morphological operations to clean up text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
        
        # 3. Apply adaptive threshold for better text separation
        processed = cv2.adaptiveThreshold(processed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # 4. Try to invert if text is white on dark background
        if np.mean(processed) < 127:  # If mostly black, invert
            processed = cv2.bitwise_not(processed)
            
        return processed
    
    def _simple_preprocessing(self, gray_image):
        """Simple image preprocessing for OCR"""
        # 1. Increase contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        processed = clahe.apply(gray_image)
        
        # 2. Apply threshold to get cleaner text
        _, processed = cv2.threshold(processed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return processed
    
    def _score_ocr_text(self, text: str) -> int:
        """Score OCR text based on key indicators"""
        score = 0
        text_upper = text.upper()
        
        if 'COUCH POTATOES' in text_upper:
            score += 10
        if 'LIKES:' in text_upper or 'IKES:' in text_upper:
            score += 5
        if 'NEEDS:' in text_upper or 'FEDS:' in text_upper:
            score += 3
        if 'PESTS:' in text_upper or 'ESTS:' in text_upper:
            score += 3
        if 'PROGRESS' in text_upper or 'STOELLR' in text_upper:
            score += 2
        if 'YOUNG' in text_upper:
            score += 1
        if 'MATURE' in text_upper:
            score += 1
        if 'ELDER' in text_upper:
            score += 1
        if 'GARDEN' in text_upper:
            score += 1
        if 'PARSLEY' in text_upper:
            score += 1
        if 'SANDWICH' in text_upper:
            score += 1
        if 'LITTER' in text_upper:
            score += 1
        if 'HOUSE' in text_upper:
            score += 1
        if 'HARVEST' in text_upper or 'TIL HARVEST' in text_upper:
            score += 2
            
        return score
    
    def _clean_ocr_text(self, text: str) -> str:
        """Clean up common OCR errors in plant popup text"""
        try:
            import re
            
            # Common OCR error patterns and their corrections
            corrections = {
                # Progress indicators
                r'STOELLR:\s*Cj': 'PROGRESS TO ELDER:',
                r'STOELLR:\s*YOUNG': 'PROGRESS TO YOUNG:',
                r'STOELLR:\s*MATURE': 'PROGRESS TO MATURE:',
                r'STOELLR:\s*ELDER': 'PROGRESS TO ELDER:',
                r'\$ TO YOUNG:': 'PROGRESS TO YOUNG:',
                r'PROGRESS\s*TO\s*YOUNG:': 'PROGRESS TO YOUNG:',
                r'PROGRESS\s*TO\s*MATURE:': 'PROGRESS TO MATURE:',
                r'PROGRESS\s*TO\s*ELDER:': 'PROGRESS TO ELDER:',
                
                # Section headers
                r'^FEDS:': 'NEEDS:',
                r'^EDS:': 'NEEDS:',
                r'^ESTS:': 'PESTS:',
                r'^STS:': 'PESTS:',
                r'^IKES:': 'LIKES:',
                r'^KES:': 'LIKES:',
                r'^i\$:': 'LIKES:',
                r'^\$:': 'LIKES:',
                r'^ES:': 'LIKES:',
                
                # Time indicators
                r'TIL HARVEST:': 'TIME TO HARVEST:',
                
                # Clean up spacing and formatting
                r'NEEDS:\s*NONE\s*CURRENTLY': 'NEEDS: NONE CURRENTLY',
                r'PESTS:\s*NONE\s*CURRENTLY': 'PESTS: NONE CURRENTLY',
                r'LIKES:\s*GARDEN\s*GNOMES': 'LIKES: GARDEN GNOMES',
                r'LIKES:\s*KING\s*PARSLEY': 'LIKES: KING PARSLEY',
                r'LIKES:\s*SANDWICH\s*STATION': 'LIKES: SANDWICH STATION',
                r'LIKES:\s*LITTER': 'LIKES: LITTER',
                r'LIKES:\s*THIS\s*HOUSE': 'LIKES: THIS HOUSE',
            }
            
            cleaned = text
            for pattern, replacement in corrections.items():
                cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE | re.MULTILINE)
            
            # Remove extra whitespace and empty lines
            lines = [line.strip() for line in cleaned.split('\n') if line.strip()]
            cleaned = '\n'.join(lines)
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Failed to clean OCR text: {e}")
            return text  # Return original text if cleaning fails
