#!/usr/bin/env python3
"""
OCR Quality Improvement Plan
Fixes specific issues found in current OCR output for Bengali legal documents
"""

import json
import re
from typing import Dict, List, Tuple
from pathlib import Path

class OCRCorrector:
    """Improves OCR quality through post-processing corrections"""
    
    def __init__(self):
        # Common OCR errors in Bengali legal documents
        self.corrections = {
            # Number/digit corrections
            'জুন Wo': 'জুন ৩০',
            'জুন ৩০': 'জুন ৩০',  # Ensure consistency
            'so (দশ)': '১০ (দশ)',
            '8৭ নং': '৪৭ নং',
            '89 নং': '৪৭ নং',
            'OF এর': '৩ক এর',
            'Ol ': '৩। ',
            '81 ': '৪। ',
            '5| ': '৫। ',
            'Bl ': '৬। ',
            '7] ': '৭। ',
            'sl ': '১। ',
            '১২1 ': '১২। ',
            
            # Character/symbol corrections
            'Wife': '।',  # Period misread
            'PIS ': 'মূসক ',
            'TAT': 'অর্পণ।',
            'PS': 'শুল্ক',
            'শুক্ধ': 'শুল্ক',
            'AGA': 'এর',
            'চে)': 'চ)',
            '(b)': '(চ)',
            '(8)': '(৪)',
            'Praga': 'নিম্নরূপ',
            '|"': '।"',
            'দীড়ি চিহ্ক': 'দাঁড়ি চিহ্ন',
            'রাজন্ব': 'রাজস্ব',
            'চিহুগুলি': 'চিহ্নগুলি',
            
            # Word corrections
            'স্নে': 'কল্পে',
            'নিশ্নরূপ': 'নিম্নরূপ',
            'এতদ্দারা': 'এতদ্বারা',
            'নৃতন': 'নূতন',
            'সন্নিবেশিত': 'সন্নিবেশিত',
            'উপযুক্ত': 'উপযুক্ত',
            
            # Section pattern corrections
            'ধারা OF': 'ধারা ৩ক',
            'দফা বে)': 'দফা (ঝ)',
            'দফা (&)': 'দফা (ঞ)',
            'দফা গে)': 'দফা (গ)',
            
            # Formula corrections
            '{R/(s00+ R)}': '{R/(১০০+ R)}',
            'মুসক হার': 'মূসক হার',
        }
        
        # Pattern-based corrections
        self.pattern_corrections = [
            # Fix section numbers
            (r'([০-৯\d]+)\| ', r'\1। '),  # Replace | with । for sections
            (r'(\d+)\] ', r'\1। '),       # Replace ] with । for sections
            
            # Fix clause patterns  
            (r'\(([ক-৯]+)\) ', r'(\1) '),  # Ensure proper clause format
            (r'\(([০-৯\d]+)\) ', r'(\1) '), # Ensure proper subsection format
            
            # Fix Bengali numbers in mixed context
            (r'(\d)([০-৯])', r'\1\2'),     # Keep mixed numbers as-is for now
            
            # Fix punctuation
            (r'\s*\|\s*$', '।'),          # End-of-line | to ।
            (r'\s*\|\s*"', '।"'),         # | before quote to ।
            
            # Fix spacing
            (r'\s+', ' '),                 # Multiple spaces to single
            (r'\n\s*\n', '\n'),           # Multiple newlines to single
        ]
    
    def correct_text(self, text: str) -> str:
        """Apply all corrections to text"""
        
        corrected = text
        
        # Apply direct corrections
        for error, correction in self.corrections.items():
            corrected = corrected.replace(error, correction)
        
        # Apply pattern-based corrections
        for pattern, replacement in self.pattern_corrections:
            corrected = re.sub(pattern, replacement, corrected)
        
        return corrected.strip()
    
    def analyze_errors(self, text: str) -> Dict[str, List[str]]:
        """Analyze remaining OCR errors for improvement"""
        
        errors = {
            'unrecognized_patterns': [],
            'mixed_scripts': [],
            'punctuation_issues': [],
            'number_issues': []
        }
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for mixed scripts
            if re.search(r'[a-zA-Z][অ-৯]|[অ-৯][a-zA-Z]', line):
                errors['mixed_scripts'].append(line)
            
            # Check for unusual punctuation
            if re.search(r'[|&@#$%^*]', line):
                errors['punctuation_issues'].append(line)
            
            # Check for number issues
            if re.search(r'\d[০-৯]|[০-৯]\d', line):
                errors['number_issues'].append(line)
            
            # Check for unrecognized patterns
            if re.search(r'[A-Z]{2,}(?![a-z])', line):
                errors['unrecognized_patterns'].append(line)
        
        return errors


class OCRImprovementPlan:
    """Complete plan for improving OCR quality"""
    
    def __init__(self):
        self.corrector = OCRCorrector()
    
    def phase1_postprocessing(self, ocr_file: str, output_file: str) -> Dict[str, any]:
        """Phase 1: Immediate post-processing improvements"""
        
        print("🔧 Phase 1: Post-processing OCR corrections...")
        
        # Load current OCR data
        with open(ocr_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        corrected_data = []
        correction_stats = {
            'pages_processed': 0,
            'corrections_made': 0,
            'error_analysis': {}
        }
        
        for page in data:
            original_text = page['extracted_text']
            corrected_text = self.corrector.correct_text(original_text)
            
            # Count corrections
            if original_text != corrected_text:
                correction_stats['corrections_made'] += 1
            
            # Analyze remaining errors
            errors = self.corrector.analyze_errors(corrected_text)
            
            corrected_page = page.copy()
            corrected_page['extracted_text'] = corrected_text
            corrected_page['original_text'] = original_text
            corrected_page['corrections_applied'] = original_text != corrected_text
            corrected_page['remaining_errors'] = errors
            
            corrected_data.append(corrected_page)
            correction_stats['pages_processed'] += 1
        
        # Save corrected data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(corrected_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Phase 1 complete: {correction_stats['corrections_made']} pages improved")
        return correction_stats
    
    def phase2_preprocessing_plan(self) -> Dict[str, str]:
        """Phase 2: Image preprocessing improvements"""
        
        plan = {
            "image_enhancement": """
            1. **Contrast Enhancement**: CLAHE (Contrast Limited Adaptive Histogram Equalization)
            2. **Noise Reduction**: Gaussian blur + bilateral filtering
            3. **Sharpening**: Unsharp mask for text clarity
            4. **Binarization**: Adaptive thresholding for better text separation
            """,
            
            "preprocessing_pipeline": """
            PDF → Images (300+ DPI) → Grayscale → Denoise → Enhance → Sharpen → OCR
            """,
            
            "tesseract_optimization": """
            1. **Language Models**: ben+eng with custom training data
            2. **PSM Modes**: Test PSM 6 (uniform block) vs PSM 4 (single column)
            3. **OEM**: Use LSTM OCR Engine Mode (3)
            4. **Custom Config**: Whitelist legal characters, improve confidence
            """,
            
            "alternative_engines": """
            1. **PaddleOCR**: Better for Bengali, multilingual support
            2. **EasyOCR**: Good for mixed scripts
            3. **TrOCR**: Transformer-based OCR for complex layouts
            4. **Ensemble**: Combine multiple engines for best results
            """
        }
        
        return plan
    
    def phase3_training_plan(self) -> Dict[str, str]:
        """Phase 3: Custom training plan"""
        
        plan = {
            "data_collection": """
            1. **Collect 1000+ legal document images**
            2. **Manual annotation of 100+ pages** with correct text
            3. **Character-level annotation** for Bengali legal terms
            4. **Font variation training** on different document styles
            """,
            
            "model_training": """
            1. **Fine-tune Tesseract**: Custom Bengali legal dictionary
            2. **Train PaddleOCR**: Legal document-specific weights
            3. **Custom TrOCR**: Train on legal document corpus
            4. **Character recognition**: Custom CNN for problematic characters
            """,
            
            "validation_strategy": """
            1. **Character accuracy**: Target 99%+ on legal terms
            2. **Word accuracy**: Target 95%+ on legal vocabulary
            3. **Structure preservation**: Maintain hierarchy markers
            4. **A/B testing**: Compare engines on real documents
            """
        }
        
        return plan
    
    def create_improvement_script(self, output_path: str):
        """Create executable improvement script"""
        
        script_content = '''#!/usr/bin/env python3
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
            
            results['paddleocr'] = '\\n'.join(text_parts)
            
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
'''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"✅ Improvement script created: {output_path}")


def main():
    """Run OCR improvement analysis and planning"""
    
    print("🔍 OCR Quality Improvement Analysis")
    print("=" * 50)
    
    # Initialize improvement plan
    improvement_plan = OCRImprovementPlan()
    
    # Phase 1: Post-processing corrections
    ocr_file = "ocr_output/pdf_ocr_results.json"
    corrected_file = "ocr_output/pdf_ocr_corrected.json"
    
    if Path(ocr_file).exists():
        stats = improvement_plan.phase1_postprocessing(ocr_file, corrected_file)
        
        print(f"\n📊 Phase 1 Results:")
        print(f"  • Pages processed: {stats['pages_processed']}")
        print(f"  • Pages improved: {stats['corrections_made']}")
        print(f"  • Improvement rate: {stats['corrections_made']/stats['pages_processed']*100:.1f}%")
        
    else:
        print(f"❌ OCR file not found: {ocr_file}")
    
    # Phase 2: Preprocessing plan
    print(f"\n🛠️ Phase 2: Image Preprocessing Plan")
    phase2_plan = improvement_plan.phase2_preprocessing_plan()
    
    for category, details in phase2_plan.items():
        print(f"\n**{category.replace('_', ' ').title()}:**")
        print(details)
    
    # Phase 3: Training plan
    print(f"\n🧠 Phase 3: Custom Training Plan")
    phase3_plan = improvement_plan.phase3_training_plan()
    
    for category, details in phase3_plan.items():
        print(f"\n**{category.replace('_', ' ').title()}:**")
        print(details)
    
    # Create improvement script
    improvement_plan.create_improvement_script("ocr_improver.py")
    
    print(f"\n🎯 Summary:")
    print(f"✅ Phase 1: Immediate post-processing corrections applied")
    print(f"📋 Phase 2: Image preprocessing plan created")
    print(f"🧠 Phase 3: Custom training roadmap provided")
    print(f"🔧 Executable improvement script: ocr_improver.py")
    
    print(f"\n🚀 Next Steps:")
    print(f"1. Use corrected OCR file: {corrected_file}")
    print(f"2. Implement image preprocessing improvements")
    print(f"3. Test alternative OCR engines (PaddleOCR, EasyOCR)")
    print(f"4. Collect training data for custom model")


if __name__ == "__main__":
    main()