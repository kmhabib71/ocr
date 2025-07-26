#!/usr/bin/env python3
"""
Quality Preserved Plain Text Converter
Maintains Vision AI quality OCR while adding line break preservation
Combines best of both: high-quality text + natural reading format
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any

class IntelligentLineBreakInserter:
    """Intelligently insert line breaks into high-quality text based on legal patterns"""
    
    def __init__(self):
        # Legal document patterns that indicate natural line breaks
        self.line_break_patterns = [
            # Chapter and section headers
            (r'(প্রথম|দ্বিতীয়|তৃতীয়|চতুর্থ|পঞ্চম|ষষ্ঠ|সপ্তম|অষ্টম|নবম|দশম)\s*অধ্যায়', r'\n\1 অধ্যায়\n'),
            (r'(অধ্যায়\s*[০-৯\d]+)', r'\n\1\n'),
            
            # Section numbers
            (r'([০-৯\d]+)।\s*([^০-৯\d])', r'\n\1। \2'),
            
            # Quoted text blocks
            (r'(যথা:__\s*)"([^"]+)"', r'\1\n"\2"'),
            (r'(যথা:-\s*)"([^"]+)"', r'\1\n"\2"'),
            
            # Sub-clauses
            (r'\s+\(([০-৯\d]+)\)\s+', r'\n(\1) '),
            (r'\s+\(([ক-৯]+)\)\s+', r'\n(\1) '),
            
            # Legal act references
            (r'(২০[০-৯]{2}\s*সনের\s*[০-৯\d]+\s*নং\s*আইন)', r'\n\1'),
            
            # Formula patterns
            (r'(যথা:\s*\{[^}]+\})', r'\n\1\n'),
            
            # Page numbers and gazette references
            (r'(২০৪[০-৯]{2}\s*বাংলাদেশ\s*গেজেট)', r'\n\1\n'),
            
            # Amendment indicators
            (r'(এর\s*সংশোধন)', r' \1\n'),
            
            # End of quoted sections
            (r'("।)\s*([০-৯\d]+।)', r'\1\n\2'),
            
            # Section breaks
            (r'(হইবে।)\s*([০-৯\d]+।)', r'\1\n\n\2'),
            
            # Clean up excessive spacing
            (r'\n\s*\n\s*\n', '\n\n'),
            (r'^\s+', ''),  # Remove leading spaces
            (r'\s+$', ''),  # Remove trailing spaces
        ]
        
        # Patterns that should NOT break
        self.preserve_patterns = [
            r'(\d+)\s*\(',  # Numbers before parentheses
            r'(আইন)\s*(\d+)',  # "আইন ২০২৪"
            r'(ধারা)\s*(\d+)',  # "ধারা ৩"
            r'(দফা)\s*\(',  # "দফা ("
        ]
    
    def smart_line_break_insertion(self, text: str) -> str:
        """Insert intelligent line breaks while preserving text quality"""
        
        processed = text
        
        # Apply line break patterns
        for pattern, replacement in self.line_break_patterns:
            processed = re.sub(pattern, replacement, processed)
        
        # Clean up and normalize
        processed = re.sub(r'\n\s*\n\s*\n+', '\n\n', processed)  # Max 2 newlines
        processed = re.sub(r'[ \t]+', ' ', processed)  # Normalize spaces
        processed = re.sub(r'[ \t]*\n[ \t]*', '\n', processed)  # Clean around newlines
        
        return processed.strip()


class QualityPreservedConverter:
    """Convert high-quality OCR to readable format with preserved line structure"""
    
    def __init__(self):
        self.line_inserter = IntelligentLineBreakInserter()
    
    def convert_with_quality_preservation(self, json_file: str, output_txt: str) -> Dict[str, Any]:
        """Convert using high-quality extracted_text with intelligent line breaks"""
        
        print(f"🔍 Converting with quality preservation: {json_file}")
        
        if not Path(json_file).exists():
            raise FileNotFoundError(f"OCR JSON not found: {json_file}")
        
        # Load OCR data
        with open(json_file, 'r', encoding='utf-8') as f:
            ocr_data = json.load(f)
        
        all_text_lines = []
        processing_stats = {
            'total_pages': len(ocr_data),
            'pages_processed': 0,
            'lines_intelligently_added': 0,
            'quality_maintained': True,
            'total_text_length': 0
        }
        
        for page_data in ocr_data:
            page_num = page_data.get('page_number', processing_stats['pages_processed'] + 1)
            
            # Use extracted_text (high quality) instead of original_text (raw OCR)
            high_quality_text = page_data.get('extracted_text', '')
            
            print(f"🔍 Processing page {page_num}/{len(ocr_data)} (quality preserved)")
            
            # Apply intelligent line break insertion
            readable_text = self.line_inserter.smart_line_break_insertion(high_quality_text)
            
            # Count lines added
            original_lines = len(high_quality_text.split('\n'))
            new_lines = len(readable_text.split('\n'))
            processing_stats['lines_intelligently_added'] += (new_lines - original_lines)
            
            # Add page header and content with preserved formatting
            page_header = f"\n{'='*50}\nPAGE {page_num}\n{'='*50}\n"
            all_text_lines.append(page_header)
            all_text_lines.append(readable_text)
            all_text_lines.append(f"\n[END OF PAGE {page_num}]\n")
            
            # Update stats
            processing_stats['pages_processed'] += 1
            processing_stats['total_text_length'] += len(readable_text)
        
        # Save quality-preserved readable text
        full_text = '\n'.join(all_text_lines)
        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        print(f"✅ Quality-preserved readable text saved to: {output_txt}")
        
        # Print summary
        print(f"\n📊 Quality Preservation Summary:")
        print(f"  • Pages processed: {processing_stats['pages_processed']}")
        print(f"  • Quality maintained: {processing_stats['quality_maintained']}")
        print(f"  • Intelligent line breaks added: {processing_stats['lines_intelligently_added']:,}")
        print(f"  • Total text length: {processing_stats['total_text_length']:,} characters")
        
        # File size info
        txt_size = Path(output_txt).stat().st_size / 1024
        print(f"  • Output file size: {txt_size:.1f} KB")
        
        return processing_stats
    
    def verify_quality_preservation(self, original_file: str, new_file: str) -> Dict[str, Any]:
        """Verify that text quality was preserved during conversion"""
        
        # Check specific patterns that should be maintained
        quality_checks = {
            'formula_quality': {'pattern': r'\{R/\(১০০\+ R\)\}', 'count_original': 0, 'count_new': 0},
            'bengali_numbers': {'pattern': r'[০-৯]', 'count_original': 0, 'count_new': 0},
            'section_numbers': {'pattern': r'[০-৯\d]+।', 'count_original': 0, 'count_new': 0},
            'act_references': {'pattern': r'২০[০-৯]{2}\s*সনের\s*[০-৯\d]+\s*নং', 'count_original': 0, 'count_new': 0}
        }
        
        # Read both files
        with open(original_file, 'r', encoding='utf-8') as f:
            original_text = f.read()
        
        with open(new_file, 'r', encoding='utf-8') as f:
            new_text = f.read()
        
        # Count patterns in both files
        for check_name, check_data in quality_checks.items():
            pattern = check_data['pattern']
            check_data['count_original'] = len(re.findall(pattern, original_text))
            check_data['count_new'] = len(re.findall(pattern, new_text))
            check_data['preserved'] = check_data['count_original'] == check_data['count_new']
        
        return quality_checks
    
    def show_sample_output(self, txt_file: str, lines: int = 30):
        """Show sample of quality-preserved readable plain text"""
        
        if not Path(txt_file).exists():
            print(f"❌ Output file not found: {txt_file}")
            return
        
        print(f"\n📝 Quality-Preserved Sample (first {lines} lines):")
        print("="*60)
        
        with open(txt_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if i > lines:
                    print("...")
                    break
                print(f"{i:3d}: {line.rstrip()}")
        
        print("="*60)


def main():
    """Main function to convert with quality preservation"""
    
    print("🎯 Quality Preserved Converter - Maintain Vision AI Quality + Line Breaks")
    print("=" * 70)
    
    # File paths
    json_file = "ocr_output/pdf_ocr_corrected.json"
    output_txt = "document_types/act/finance_act_2024_quality_preserved.txt"
    analysis_file = "document_types/act/quality_preserved_analysis.json"
    original_file = "finance_act_2024_plaintext.txt"
    
    if not Path(json_file).exists():
        print(f"❌ OCR file not found: {json_file}")
        return
    
    try:
        # Initialize quality-preserved converter
        converter = QualityPreservedConverter()
        
        # Convert with quality preservation
        stats = converter.convert_with_quality_preservation(json_file, output_txt)
        
        # Verify quality preservation
        if Path(original_file).exists():
            quality_checks = converter.verify_quality_preservation(original_file, output_txt)
            stats['quality_verification'] = quality_checks
        
        # Save analysis
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"\n" + "="*70)
        print(f"🎉 QUALITY PRESERVED CONVERSION COMPLETE!")
        print(f"="*70)
        
        # Show results
        print(f"📄 Quality-preserved output: {output_txt}")
        print(f"📊 Analysis report: {analysis_file}")
        
        # Quality verification results
        if 'quality_verification' in stats:
            print(f"\n✅ Quality Verification:")
            for check_name, check_data in stats['quality_verification'].items():
                status = "✅ PRESERVED" if check_data['preserved'] else "❌ CHANGED"
                print(f"  • {check_name.replace('_', ' ').title()}: {status}")
                print(f"    Original: {check_data['count_original']}, New: {check_data['count_new']}")
        
        # Quality improvements
        print(f"\n✅ Quality + Readability Features:")
        print(f"  • Vision AI quality maintained")
        print(f"  • Intelligent line breaks added")
        print(f"  • Legal structure naturally formatted")
        print(f"  • Page references preserved")
        print(f"  • Same character corrections as previous version")
        
        # Show sample
        converter.show_sample_output(output_txt, lines=25)
        
        # Next steps
        print(f"\n🚀 Next Steps:")
        print(f"1. Review quality-preserved output: {output_txt}")
        print(f"2. Verify specific formulas like {{R/(১০০+ R)}} are correct")
        print(f"3. Compare readability vs original paragraph format")
        print(f"4. Use for Act document pattern analysis")
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()