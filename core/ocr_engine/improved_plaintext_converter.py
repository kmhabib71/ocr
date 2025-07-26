#!/usr/bin/env python3
"""
Improved Plain Text Converter with Line Break Preservation
Converts OCR JSON to readable plain text while preserving original line structure
Enhanced readability without compromising quality or code integrity
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any

class BengaliCharacterCorrector:
    """Advanced Bengali character-level OCR correction with line preservation"""
    
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
            '8৷': '৪৷',
            '89': '৪৷',
            
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
        
        # Pattern-based corrections that preserve line structure
        self.pattern_corrections = [
            # Section number patterns
            (r'([০-৯\d]+)\|', r'\1।'),  # Number| to Number।
            (r'([০-৯\d]+)\]', r'\1।'),  # Number] to Number।
            (r'([০-৯\d]+)\)', r'(\1)'), # Fix subsection patterns
            
            # Punctuation fixes - preserve line structure
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
            
            # Excessive spacing - but preserve intentional line breaks
            (r'[ \t]{2,}', ' '),          # Multiple spaces/tabs to single space
            (r'[ \t]*\n[ \t]*', '\n'),    # Clean up around line breaks
        ]
        
        # Context-aware corrections
        self.context_corrections = {
            'legal_terms': {
                'ধারা OF': 'ধারা ৩ক',
                'আইনের ধারা OF': 'আইনের ধারা ৩ক',
                'সনের 89 নং': 'সনের ৪৷ নং',
                'সনের 8৷ নং': 'সনের ৪৷ নং',
            },
            'numbers_in_context': {
                'জুন Wo': 'জুন ৩০',
                'so (দশ)': '১০ (দশ)',
                '2O (বিশ)': '২০ (বিশ)',
            }
        }
    
    def correct_characters_preserve_lines(self, text: str) -> str:
        """Apply character-level corrections while preserving line structure"""
        
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
        
        return corrected
    
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


class ImprovedPlainTextConverter:
    """Convert OCR JSON to readable plain text with preserved line structure"""
    
    def __init__(self):
        self.corrector = BengaliCharacterCorrector()
    
    def convert_with_line_preservation(self, json_file: str, output_txt: str, 
                                     apply_corrections: bool = True) -> Dict[str, Any]:
        """Convert OCR JSON to plain text with preserved line breaks"""
        
        print(f"🔍 Converting OCR JSON to readable plain text: {json_file}")
        
        if not Path(json_file).exists():
            raise FileNotFoundError(f"OCR JSON not found: {json_file}")
        
        # Load OCR data
        with open(json_file, 'r', encoding='utf-8') as f:
            ocr_data = json.load(f)
        
        all_text_lines = []
        processing_stats = {
            'total_pages': len(ocr_data),
            'pages_processed': 0,
            'character_corrections': 0,
            'lines_preserved': 0,
            'quality_issues': {},
            'total_text_length': 0
        }
        
        for page_data in ocr_data:
            page_num = page_data.get('page_number', processing_stats['pages_processed'] + 1)
            
            # Use original_text if available (has line breaks), otherwise use extracted_text
            if 'original_text' in page_data and page_data['original_text']:
                raw_text = page_data['original_text']
                using_original = True
            else:
                raw_text = page_data.get('extracted_text', '')
                using_original = False
            
            print(f"🔍 Processing page {page_num}/{len(ocr_data)} ({'original' if using_original else 'extracted'} text)")
            
            if apply_corrections:
                # Apply character corrections while preserving line structure
                corrected_text = self.corrector.correct_characters_preserve_lines(raw_text)
                
                # Track corrections
                if raw_text != corrected_text:
                    processing_stats['character_corrections'] += 1
                
                # Analyze remaining issues
                issues = self.corrector.analyze_remaining_issues(corrected_text)
                
                # Store quality issues
                for issue_type, issue_list in issues.items():
                    if issue_list:
                        processing_stats['quality_issues'][f"page_{page_num}_{issue_type}"] = len(issue_list)
                
                final_text = corrected_text
            else:
                final_text = raw_text
            
            # Count preserved lines
            line_count = len(final_text.split('\n'))
            processing_stats['lines_preserved'] += line_count
            
            # Add page header and content with preserved formatting
            page_header = f"\n{'='*50}\nPAGE {page_num}\n{'='*50}\n"
            all_text_lines.append(page_header)
            all_text_lines.append(final_text)
            all_text_lines.append(f"\n[END OF PAGE {page_num}]\n")
            
            # Update stats
            processing_stats['pages_processed'] += 1
            processing_stats['total_text_length'] += len(final_text)
        
        # Save plain text output with preserved formatting
        full_text = '\n'.join(all_text_lines)
        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        print(f"✅ Readable plain text saved to: {output_txt}")
        
        # Print summary
        print(f"\n📊 Conversion Summary:")
        print(f"  • Pages converted: {processing_stats['pages_processed']}")
        print(f"  • Pages with corrections: {processing_stats['character_corrections']}")
        print(f"  • Lines preserved: {processing_stats['lines_preserved']:,}")
        if processing_stats['pages_processed'] > 0:
            print(f"  • Correction rate: {processing_stats['character_corrections']/processing_stats['pages_processed']*100:.1f}%")
            print(f"  • Avg lines per page: {processing_stats['lines_preserved']/processing_stats['pages_processed']:.1f}")
        
        total_issues = sum(processing_stats['quality_issues'].values())
        print(f"  • Quality issues found: {total_issues}")
        print(f"  • Total text length: {processing_stats['total_text_length']:,} characters")
        
        # File size info
        txt_size = Path(output_txt).stat().st_size / 1024
        print(f"  • Output file size: {txt_size:.1f} KB")
        
        return processing_stats
    
    def show_sample_output(self, txt_file: str, lines: int = 30):
        """Show sample of converted readable plain text"""
        
        if not Path(txt_file).exists():
            print(f"❌ Output file not found: {txt_file}")
            return
        
        print(f"\n📝 Sample Output (first {lines} lines):")
        print("="*60)
        
        with open(txt_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if i > lines:
                    print("...")
                    break
                print(f"{i:3d}: {line.rstrip()}")
        
        print("="*60)


def main():
    """Main function to convert OCR JSON to readable plain text"""
    
    print("🎯 Improved Plain Text Converter - Line Break Preservation")
    print("=" * 60)
    
    # File paths
    json_file = "ocr_output/pdf_ocr_corrected.json"
    output_txt = "document_types/act/finance_act_2024_readable.txt"
    analysis_file = "document_types/act/readable_conversion_analysis.json"
    
    # Check if corrected version exists, otherwise use original
    if not Path(json_file).exists():
        json_file = "ocr_output/pdf_ocr_results.json"
        apply_corrections = True   # Apply corrections during conversion
        print(f"📋 Using original OCR data: {json_file}")
    else:
        apply_corrections = False  # Already corrected
        print(f"📋 Using corrected OCR data: {json_file}")
    
    if not Path(json_file).exists():
        print(f"❌ OCR file not found: {json_file}")
        print("Available OCR files:")
        for ocr_file in Path(".").glob("**/pdf_ocr*.json"):
            print(f"  - {ocr_file}")
        return
    
    try:
        # Initialize improved converter
        converter = ImprovedPlainTextConverter()
        
        # Convert to readable plain text
        stats = converter.convert_with_line_preservation(
            json_file, 
            output_txt, 
            apply_corrections=apply_corrections
        )
        
        # Save analysis
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"\n" + "="*60)
        print(f"🎉 IMPROVED CONVERSION COMPLETE!")
        print(f"="*60)
        
        # Show results
        print(f"📄 Readable text output: {output_txt}")
        print(f"📊 Analysis report: {analysis_file}")
        
        # Quality improvements
        print(f"\n✅ Readability Improvements:")
        print(f"  • Line breaks preserved from original OCR")
        print(f"  • Legal structure naturally formatted")
        if apply_corrections:
            print(f"  • Character-level corrections applied")
        print(f"  • Page references maintained")
        print(f"  • Enhanced readability for user review")
        
        # Show sample
        converter.show_sample_output(output_txt, lines=25)
        
        # Next steps
        print(f"\n🚀 Next Steps:")
        print(f"1. Review improved readability: {output_txt}")
        print(f"2. Compare with original: finance_act_2024_plaintext.txt")
        print(f"3. Provide feedback on OCR quality and structure patterns")
        print(f"4. Use for Act document pattern analysis")
        
        # File comparison
        original_file = "finance_act_2024_plaintext.txt"
        if Path(original_file).exists():
            print(f"\n📈 File Comparison:")
            print(f"  • Original (paragraph format): {original_file}")
            print(f"  • Improved (line preserved): {output_txt}")
            print(f"  • Line preservation: +{stats['lines_preserved']:,} lines")
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()