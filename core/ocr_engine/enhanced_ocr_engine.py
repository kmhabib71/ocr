#!/usr/bin/env python3
"""
Enhanced OCR Engine - Focus on Character-Level Accuracy
Generates plain text output with page references for Bengali legal documents
No Vision AI dependency - pure local processing with character refinement
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import json
import re
from pathlib import Path
from pdf2image import convert_from_path
from typing import Dict, List, Tuple, Optional, Any

class BengaliCharacterCorrector:
    """Advanced Bengali character-level OCR correction"""
    
    def __init__(self):
        # Character-level corrections for Bengali legal documents
        self.character_corrections = {
            # Common Bengali character misreads
            'Wo': '৩০',
            'so': '১০', 
            'OF': '৩ক',
            'Ol': '৩',
            '81': '৪',
            '5|': '৫',
            'Bl': '৬',
            '7]': '৭',
            '8]': '৮',
            '9|': '৯',
            'sl': '১',
            '১২1': '১২',
            '8৭': '৪৭',
            '89': '৪৭',
            
            # Bengali punctuation fixes
            'Wife': '।',
            '|"': '।"',
            '||': '।',
            '(cid:': '',  # Remove font encoding artifacts
            
            # Mixed character issues
            'PIS': 'মূসক',
            'PS': 'শুল্ক',
            'TAT': 'অর্পণ',
            'AGA': 'এর',
            'Praga': 'নিম্নরূপ',
            'চে)': 'চ)',
            '(b)': '(চ)',
            '(8)': '(৪)',
            
            # Word-level corrections
            'শুক্ধ': 'শুল্ক',
            'রাজন্ব': 'রাজস্ব',
            'চিহুগুলি': 'চিহ্নগুলি',
            'দীড়ি চিহ্ক': 'দাঁড়ি চিহ্ন',
            'এতদ্দারা': 'এতদ্বারা',
            'নিশ্নরূপ': 'নিম্নরূপ',
            'নৃতন': 'নূতন',
            'মুসক': 'মূসক',
            
            # Formula corrections
            '{R/(s00+ R)}': '{R/(১০০+ R)}',
            'R/(100+R)': 'R/(১০০+R)',
        }
        
        # Pattern-based corrections
        self.pattern_corrections = [
            # Section number patterns
            (r'([০-৯\d]+)\|', r'\1।'),  # Number| to Number।
            (r'([০-৯\d]+)\]', r'\1।'),  # Number] to Number।
            (r'([০-৯\d]+)\)', r'(\1)'), # Fix subsection patterns
            
            # Bengali number consistency
            (r'(\d)([০-৯])', r'\1\2'),  # Keep mixed for manual review
            (r'([০-৯])(\d)', r'\1\2'),  # Keep mixed for manual review
            
            # Punctuation fixes
            (r'\s*\|\s*$', '।'),        # End line | to ।
            (r'\s*\|\s*"', '।"'),       # | before quote to ।
            (r'\s*\|\s*।', '।'),        # |। to ।
            
            # Clause pattern fixes
            (r'\(([ক-৯]+)\)\s*', r'(\1) '), # Ensure space after clause
            (r'\(([০-৯\d]+)\)\s*', r'(\1) '), # Ensure space after subsection
            
            # Word boundary fixes
            (r'দফা\s*বে\)', 'দফা (ঝ)'),   # Common clause misread
            (r'দফা\s*\(&\)', 'দফা (ঞ)'),  # Common clause misread
            (r'দফা\s*গে\)', 'দফা (গ)'),   # Common clause misread
            
            # Spacing fixes
            (r'\s{2,}', ' '),            # Multiple spaces to single
            (r'\n\s*\n\s*\n', '\n\n'),  # Max 2 consecutive newlines
        ]
        
        # Context-aware corrections
        self.context_corrections = {
            'legal_terms': {
                'ধারা OF': 'ধারা ৩ক',
                'আইনের ধারা OF': 'আইনের ধারা ৩ক',
                'সনের 89 নং': 'সনের ৪৭ নং',
                'সনের 8৭ নং': 'সনের ৪৭ নং',
            },
            'numbers_in_context': {
                'জুন Wo': 'জুন ৩০',
                'so (দশ)': '১০ (দশ)',
                '2O (বিশ)': '২০ (বিশ)',
            }
        }
    
    def correct_characters(self, text: str) -> str:
        """Apply character-level corrections"""
        
        corrected = text
        
        # Apply direct character corrections
        for error, correction in self.character_corrections.items():
            corrected = corrected.replace(error, correction)
        
        # Apply pattern-based corrections
        for pattern, replacement in self.pattern_corrections:
            corrected = re.sub(pattern, replacement, corrected)
        
        # Apply context-aware corrections
        for category, corrections in self.context_corrections.items():
            for error, correction in corrections.items():
                corrected = corrected.replace(error, correction)
        
        return corrected.strip()
    
    def analyze_remaining_issues(self, text: str) -> Dict[str, List[str]]:
        """Analyze what character issues remain for future improvement"""
        
        issues = {
            'mixed_scripts': [],
            'unusual_patterns': [],
            'potential_errors': [],
            'encoding_artifacts': []
        }
        
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            # Mixed script detection
            if re.search(r'[a-zA-Z][অ-৯]|[অ-৯][a-zA-Z]', line):
                issues['mixed_scripts'].append(f"Line {line_num}: {line}")
            
            # Unusual character patterns
            if re.search(r'[|&@#$%^*]', line):
                issues['unusual_patterns'].append(f"Line {line_num}: {line}")
            
            # Potential OCR errors
            if re.search(r'[A-Z]{2,}(?![a-z])', line):
                issues['potential_errors'].append(f"Line {line_num}: {line}")
            
            # Encoding artifacts
            if re.search(r'\(cid:', line):
                issues['encoding_artifacts'].append(f"Line {line_num}: {line}")
        
        return issues


class EnhancedOCREngine:
    """Enhanced OCR engine focused on character accuracy"""
    
    def __init__(self):
        self.corrector = BengaliCharacterCorrector()
        
        # Optimized Tesseract configuration
        self.tesseract_configs = {
            'standard': {
                'lang': 'ben+eng',
                'config': '--oem 3 --psm 6'
            },
            'legal_optimized': {
                'lang': 'ben+eng', 
                'config': '--oem 3 --psm 6 -c tessedit_char_whitelist=০১২৩৪৫৬৭৮৯()ক-৯অ-৯া-্।,;:-'
            },
            'number_focused': {
                'lang': 'ben+eng',
                'config': '--oem 3 --psm 8 -c tessedit_char_whitelist=০১২৩৪৫৬৭৮৯।(),'
            }
        }
    
    def enhance_image(self, image: np.ndarray) -> np.ndarray:
        """Advanced image enhancement for Bengali text"""
        
        # Convert to PIL for easier manipulation
        pil_image = Image.fromarray(image)
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(pil_image)
        enhanced = enhancer.enhance(1.5)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(enhanced)
        enhanced = enhancer.enhance(2.0)
        
        # Convert back to OpenCV
        enhanced_cv = cv2.cvtColor(np.array(enhanced), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(enhanced_cv, cv2.COLOR_BGR2GRAY)
        
        # Noise reduction
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # CLAHE for contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        clahe_applied = clahe.apply(denoised)
        
        # Morphological operations to clean text
        kernel = np.ones((1,1), np.uint8)
        morph = cv2.morphologyEx(clahe_applied, cv2.MORPH_CLOSE, kernel)
        
        # Adaptive threshold
        binary = cv2.adaptiveThreshold(
            morph, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return binary
    
    def extract_text_multiple_methods(self, image: np.ndarray) -> Dict[str, str]:
        """Extract text using multiple methods and choose best"""
        
        results = {}
        
        # Method 1: Standard configuration
        try:
            config = self.tesseract_configs['standard']
            text1 = pytesseract.image_to_string(
                image, 
                lang=config['lang'], 
                config=config['config']
            )
            results['standard'] = text1
        except Exception as e:
            results['standard'] = f"Error: {e}"
        
        # Method 2: Legal optimized
        try:
            config = self.tesseract_configs['legal_optimized']
            text2 = pytesseract.image_to_string(
                image,
                lang=config['lang'],
                config=config['config']
            )
            results['legal_optimized'] = text2
        except Exception as e:
            results['legal_optimized'] = f"Error: {e}"
        
        # Method 3: Different PSM mode
        try:
            text3 = pytesseract.image_to_string(
                image,
                lang='ben+eng',
                config='--oem 3 --psm 4'  # Single column mode
            )
            results['single_column'] = text3
        except Exception as e:
            results['single_column'] = f"Error: {e}"
        
        return results
    
    def choose_best_result(self, results: Dict[str, str]) -> str:
        """Choose the best OCR result based on quality metrics"""
        
        best_text = ""
        best_score = 0
        
        for method, text in results.items():
            if text.startswith("Error:"):
                continue
            
            # Quality scoring
            score = 0
            
            # Length bonus (longer usually better for legal docs)
            score += len(text) * 0.001
            
            # Bengali character ratio
            bengali_chars = len(re.findall(r'[অ-৯]', text))
            total_chars = len(re.findall(r'[a-zA-Zঅ-৯]', text))
            if total_chars > 0:
                score += (bengali_chars / total_chars) * 10
            
            # Legal term bonus
            legal_terms = ['ধারা', 'দফা', 'আইন', 'অধ্যায়', 'তফসিল']
            for term in legal_terms:
                score += text.count(term) * 0.5
            
            # Penalty for obvious errors
            error_patterns = ['|||', '???', 'cid:', 'Wife']
            for pattern in error_patterns:
                score -= text.count(pattern) * 2
            
            if score > best_score:
                best_score = score
                best_text = text
        
        return best_text if best_text else list(results.values())[0]
    
    def process_pdf_to_text(self, pdf_path: str, output_txt: str, 
                           output_analysis: str = None) -> Dict[str, Any]:
        """Process PDF to plain text with page references"""
        
        print(f"🔍 Enhanced OCR processing: {pdf_path}")
        
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Convert PDF to images
        print("📄 Converting PDF to images...")
        images = convert_from_path(pdf_path, dpi=300)
        
        all_text_lines = []
        processing_stats = {
            'total_pages': len(images),
            'pages_processed': 0,
            'character_corrections': 0,
            'quality_issues': {},
            'method_usage': {}
        }
        
        for page_num, image in enumerate(images, 1):
            print(f"🔍 Processing page {page_num}/{len(images)}")
            
            # Convert PIL to CV2
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Enhance image
            enhanced_image = self.enhance_image(cv_image)
            
            # Extract text with multiple methods
            ocr_results = self.extract_text_multiple_methods(enhanced_image)
            
            # Choose best result
            raw_text = self.choose_best_result(ocr_results)
            
            # Apply character corrections
            corrected_text = self.corrector.correct_characters(raw_text)
            
            # Track corrections
            if raw_text != corrected_text:
                processing_stats['character_corrections'] += 1
            
            # Analyze remaining issues
            issues = self.corrector.analyze_remaining_issues(corrected_text)
            
            # Add page header and content
            page_header = f"\n{'='*50}\nPAGE {page_num}\n{'='*50}\n"
            all_text_lines.append(page_header)
            all_text_lines.append(corrected_text)
            all_text_lines.append(f"\n[END OF PAGE {page_num}]\n")
            
            # Update stats
            processing_stats['pages_processed'] += 1
            
            # Track method usage
            best_method = max(ocr_results.keys(), 
                            key=lambda k: len(ocr_results[k]) if not ocr_results[k].startswith("Error:") else 0)
            processing_stats['method_usage'][best_method] = processing_stats['method_usage'].get(best_method, 0) + 1
            
            # Store quality issues
            for issue_type, issue_list in issues.items():
                if issue_list:
                    processing_stats['quality_issues'][f"page_{page_num}_{issue_type}"] = len(issue_list)
        
        # Save plain text output
        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_text_lines))
        
        print(f"✅ Plain text saved to: {output_txt}")
        
        # Save analysis if requested
        if output_analysis:
            with open(output_analysis, 'w', encoding='utf-8') as f:
                json.dump(processing_stats, f, indent=2, ensure_ascii=False)
            print(f"📊 Analysis saved to: {output_analysis}")
        
        # Print summary
        print(f"\n📊 Processing Summary:")
        print(f"  • Pages processed: {processing_stats['pages_processed']}")
        print(f"  • Pages with corrections: {processing_stats['character_corrections']}")
        print(f"  • Correction rate: {processing_stats['character_corrections']/processing_stats['pages_processed']*100:.1f}%")
        
        method_usage = processing_stats['method_usage']
        print(f"  • Best OCR method: {max(method_usage.keys(), key=lambda k: method_usage[k])}")
        
        total_issues = sum(processing_stats['quality_issues'].values())
        print(f"  • Quality issues found: {total_issues}")
        
        return processing_stats


def main():
    """Main function to run enhanced OCR"""
    
    print("🎯 Enhanced OCR Engine - Character-Level Accuracy")
    print("=" * 60)
    
    # File paths
    pdf_path = "test_tax_documents/Finance_Act-2024.pdf"
    output_txt = "finance_act_2024_enhanced_ocr.txt"
    analysis_file = "ocr_analysis_report.json"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF not found: {pdf_path}")
        print("Available PDFs:")
        for pdf in Path(".").glob("**/*.pdf"):
            print(f"  - {pdf}")
        return
    
    try:
        # Initialize enhanced OCR
        ocr_engine = EnhancedOCREngine()
        
        # Process PDF
        stats = ocr_engine.process_pdf_to_text(
            pdf_path, 
            output_txt, 
            analysis_file
        )
        
        # Show results
        print(f"\n" + "="*60)
        print(f"🎉 ENHANCED OCR COMPLETE!")
        print(f"="*60)
        
        # File info
        txt_size = Path(output_txt).stat().st_size / 1024
        print(f"📄 Output: {output_txt} ({txt_size:.1f} KB)")
        print(f"📊 Analysis: {analysis_file}")
        
        # Quality metrics
        print(f"\n✅ Quality Improvements:")
        print(f"  • Character-level corrections applied")
        print(f"  • Multiple OCR method selection")
        print(f"  • Advanced image enhancement")
        print(f"  • Page reference preservation")
        
        # Next steps
        print(f"\n🚀 Next Steps:")
        print(f"1. Review text quality in: {output_txt}")
        print(f"2. Check analysis report: {analysis_file}")
        print(f"3. Use page references for user verification")
        print(f"4. Build structure templates from reliable text")
        
        # Show sample
        print(f"\n📝 Sample Text (first 200 chars):")
        with open(output_txt, 'r', encoding='utf-8') as f:
            sample = f.read(200)
            print(f"'{sample}...'")
        
    except Exception as e:
        print(f"❌ Enhanced OCR failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()