#!/usr/bin/env python3
"""
Enhanced BBOCR wrapper for tax documents
Specialized for Bangla-English mixed content
"""

import cv2
import numpy as np
from pathlib import Path
from bbocr import ApsisNet, PaddleDBNet
from bbocr.modules.yolodla import YoloDLA
import json

class TaxDocumentOCR:
    def __init__(self, enable_tables=True, enable_math=False):
        """Initialize Tax Document OCR system"""
        self.enable_tables = enable_tables
        self.enable_math = enable_math
        
        # Initialize models when available
        try:
            self.layout_analyzer = YoloDLA()
            print("✅ Layout analyzer loaded")
        except Exception as e:
            print(f"⚠️  Layout analyzer not available: {e}")
            self.layout_analyzer = None
        
        try:
            self.text_recognizer = ApsisNet()
            print("✅ Text recognizer loaded")  
        except Exception as e:
            print(f"⚠️  Text recognizer not available: {e}")
            self.text_recognizer = None
    
    def process_image(self, image_path):
        """Process a single image for tax document OCR"""
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        results = {
            'image_path': str(image_path),
            'layout_regions': [],
            'text_content': [],
            'tables': [],
            'forms': [],
            'confidence': 0.0
        }
        
        # Layout analysis
        if self.layout_analyzer:
            try:
                layout_result = self.layout_analyzer.get_rois(image)
                results['layout_regions'] = self._parse_layout(layout_result)
            except Exception as e:
                print(f"Layout analysis failed: {e}")
        
        # Text recognition for each region
        for region in results['layout_regions']:
            if region['type'] in ['paragraph', 'text_box']:
                # Extract text from region
                region_image = self._crop_region(image, region['bbox'])
                if self.text_recognizer:
                    try:
                        text = self.text_recognizer.process(region_image)
                        results['text_content'].append({
                            'region_id': region['id'],
                            'text': text,
                            'bbox': region['bbox'],
                            'type': region['type']
                        })
                    except Exception as e:
                        print(f"Text recognition failed for region {region['id']}: {e}")
        
        return results
    
    def process_tax_form(self, image_path, form_type='general'):
        """Process specific tax form types"""
        results = self.process_image(image_path)
        
        # Add tax-specific processing
        if form_type == 'income_statement':
            results = self._parse_income_statement(results)
        elif form_type == 'tax_calculation':
            results = self._parse_tax_calculation(results)
        elif form_type == 'deduction_form':
            results = self._parse_deductions(results)
        
        return results
    
    def _parse_layout(self, layout_result):
        """Parse layout detection results"""
        regions = []
        # Implementation depends on YoloDLA output format
        # This is a placeholder
        return regions
    
    def _crop_region(self, image, bbox):
        """Crop image region based on bounding box"""
        x1, y1, x2, y2 = bbox
        return image[y1:y2, x1:x2]
    
    def _parse_income_statement(self, results):
        """Parse income statement specific elements"""
        # Look for salary, business income, other income
        return results
    
    def _parse_tax_calculation(self, results):
        """Parse tax calculation forms"""
        # Extract numerical calculations and formulas
        return results
    
    def _parse_deductions(self, results):
        """Parse deduction lists and nested items"""
        # Handle bullet points and nested structures
        return results

# Usage example
if __name__ == "__main__":
    # Initialize OCR system
    tax_ocr = TaxDocumentOCR(enable_tables=True, enable_math=True)
    
    # Process a tax document
    try:
        result = tax_ocr.process_tax_form('sample_tax_form.png', 'income_statement')
        print("📊 OCR Results:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Processing failed: {e}")
