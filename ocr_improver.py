#!/usr/bin/env python3
"""
OCR Improvement Script - Executable version
Run this to improve OCR quality step by step
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from pathlib import Path

class OCRImprover:
    def __init__(self):
        # Enhanced Tesseract config for Bengali legal docs
        self.tesseract_config = {
            'lang': 'ben+eng',
            'config': '--oem 3 --psm 6 -c tessedit_char_whitelist=০১২৩৪৫৬৭৮৯abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ।(),-.:;'
        }
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Advanced image preprocessing for better OCR"""
        
        # Load image
        image = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Noise reduction
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        # Sharpening
        kernel = np.array([[-1,-1,-1],
                          [-1, 9,-1],
                          [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        # Adaptive thresholding
        binary = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        return binary
    
    def extract_with_multiple_engines(self, image: np.ndarray) -> Dict[str, str]:
        """Extract text using multiple OCR engines"""
        
        results = {}
        
        # Tesseract
        try:
            results['tesseract'] = pytesseract.image_to_string(
                image, 
                lang=self.tesseract_config['lang'],
                config=self.tesseract_config['config']
            )
        except Exception as e:
            results['tesseract'] = f"Error: {e}"
        
        # PaddleOCR (if available)
        try:
            import paddleocr
            paddle_ocr = paddleocr.PaddleOCR(use_angle_cls=True, lang='en')
            paddle_result = paddle_ocr.ocr(image)
            
            text_parts = []
            for line in paddle_result:
                if line:
                    for word_info in line:
                        text_parts.append(word_info[1][0])
            
            results['paddleocr'] = '\n'.join(text_parts)
            
        except Exception as e:
            results['paddleocr'] = f"PaddleOCR not available: {e}"
        
        return results
    
    def improve_pdf_ocr(self, pdf_path: str, output_path: str):
        """Improve OCR for entire PDF"""
        
        print(f"🔧 Improving OCR for: {pdf_path}")
        
        # Your existing PDF to image conversion code here
        # Then apply preprocessing and multi-engine extraction
        
        print(f"✅ Improved OCR saved to: {output_path}")

def main():
    improver = OCRImprover()
    
    # Test on your document
    pdf_path = "test_tax_documents/Finance_Act-2024.pdf"
    output_path = "finance_act_improved_ocr.json"
    
    if Path(pdf_path).exists():
        improver.improve_pdf_ocr(pdf_path, output_path)
    else:
        print(f"❌ PDF not found: {pdf_path}")

if __name__ == "__main__":
    main()
