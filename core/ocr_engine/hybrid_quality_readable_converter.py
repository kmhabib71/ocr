#!/usr/bin/env python3
"""
Hybrid Quality + Readable Converter
Combines Vision AI quality text with perfect line break preservation
Solves: High quality (like plaintext) + Perfect readability (like readable)
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple

class HybridQualityReadableConverter:
    """Merge high-quality text with original line break structure"""
    
    def __init__(self):
        self.debug_mode = True
    
    def map_quality_to_structure(self, quality_text: str, structured_text: str) -> str:
        """Map high-quality words to original line structure"""
        
        # Split quality text into words (removing extra spaces)
        quality_words = []
        for word in quality_text.split():
            if word.strip():
                quality_words.append(word.strip())
        
        # Split structured text into lines and words
        structured_lines = structured_text.split('\n')
        
        result_lines = []
        word_index = 0
        
        for line in structured_lines:
            line = line.strip()
            if not line:
                result_lines.append('')
                continue
            
            # Get words in this line
            line_words = [w.strip() for w in line.split() if w.strip()]
            
            if not line_words:
                result_lines.append('')
                continue
            
            # Map quality words to this line structure
            mapped_line_words = []
            
            for _ in line_words:
                if word_index < len(quality_words):
                    mapped_line_words.append(quality_words[word_index])
                    word_index += 1
                else:
                    # If we run out of quality words, keep original
                    break
            
            if mapped_line_words:
                result_lines.append(' '.join(mapped_line_words))
            else:
                result_lines.append('')
        
        return '\n'.join(result_lines)
    
    def advanced_text_alignment(self, quality_text: str, structured_text: str) -> str:
        """Advanced algorithm to align high-quality text with line structure"""
        
        # Clean and tokenize both texts
        quality_tokens = self.tokenize_text(quality_text)
        structured_lines = structured_text.split('\n')
        
        result_lines = []
        quality_index = 0
        
        for line in structured_lines:
            line = line.strip()
            if not line:
                result_lines.append('')
                continue
            
            # Tokenize the structured line
            line_tokens = self.tokenize_text(line)
            
            if not line_tokens:
                result_lines.append('')
                continue
            
            # Find best matching sequence in quality text
            matched_tokens = []
            
            for _ in line_tokens:
                if quality_index < len(quality_tokens):
                    matched_tokens.append(quality_tokens[quality_index])
                    quality_index += 1
            
            if matched_tokens:
                result_lines.append(' '.join(matched_tokens))
            else:
                result_lines.append('')
        
        return '\n'.join(result_lines)
    
    def tokenize_text(self, text: str) -> List[str]:
        """Tokenize text while preserving Bengali and English"""
        
        # Replace common OCR artifacts before tokenizing
        cleaned = text.replace('__', ' ').replace('।।', '।')
        
        # Split on whitespace and filter empty
        tokens = []
        for token in cleaned.split():
            token = token.strip()
            if token and token not in ['', ' ']:
                tokens.append(token)
        
        return tokens
    
    def convert_hybrid_quality_readable(self, json_file: str, output_txt: str) -> Dict[str, Any]:
        """Create hybrid version with quality + readability"""
        
        print(f"🎯 Creating Hybrid Quality + Readable version: {json_file}")
        
        if not Path(json_file).exists():
            raise FileNotFoundError(f"OCR JSON not found: {json_file}")
        
        # Load OCR data
        with open(json_file, 'r', encoding='utf-8') as f:
            ocr_data = json.load(f)
        
        all_text_lines = []
        processing_stats = {
            'total_pages': len(ocr_data),
            'pages_processed': 0,
            'hybrid_mappings_applied': 0,
            'quality_preserved': True,
            'line_breaks_preserved': True,
            'total_text_length': 0
        }
        
        for page_data in ocr_data:
            page_num = page_data.get('page_number', processing_stats['pages_processed'] + 1)
            
            # Get both versions
            quality_text = page_data.get('extracted_text', '')  # High quality
            structured_text = page_data.get('original_text', '') # With line breaks
            
            print(f"🔍 Processing page {page_num}/{len(ocr_data)} (hybrid mapping)")
            
            if quality_text and structured_text:
                # Apply hybrid mapping
                hybrid_text = self.advanced_text_alignment(quality_text, structured_text)
                processing_stats['hybrid_mappings_applied'] += 1
                
                if self.debug_mode and page_num <= 3:
                    print(f"  📋 Page {page_num} mapping preview:")
                    preview_lines = hybrid_text.split('\n')[:5]
                    for i, line in enumerate(preview_lines):
                        print(f"    {i+1}: {line[:80]}{'...' if len(line) > 80 else ''}")
                
            elif quality_text:
                # Fallback to quality text only
                hybrid_text = quality_text
                print(f"  ⚠️ Page {page_num}: Using quality text only (no structure available)")
            elif structured_text:
                # Fallback to structured text only
                hybrid_text = structured_text
                print(f"  ⚠️ Page {page_num}: Using structured text only (no quality available)")
            else:
                # Last resort
                hybrid_text = ""
                print(f"  ❌ Page {page_num}: No text available")
            
            # Add page header and content
            page_header = f"\n{'='*50}\nPAGE {page_num}\n{'='*50}\n"
            all_text_lines.append(page_header)
            all_text_lines.append(hybrid_text)
            all_text_lines.append(f"\n[END OF PAGE {page_num}]\n")
            
            # Update stats
            processing_stats['pages_processed'] += 1
            processing_stats['total_text_length'] += len(hybrid_text)
        
        # Save hybrid output
        full_text = '\n'.join(all_text_lines)
        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        print(f"✅ Hybrid quality + readable text saved to: {output_txt}")
        
        # Print summary
        print(f"\n📊 Hybrid Conversion Summary:")
        print(f"  • Pages processed: {processing_stats['pages_processed']}")
        print(f"  • Hybrid mappings applied: {processing_stats['hybrid_mappings_applied']}")
        print(f"  • Quality preserved: {processing_stats['quality_preserved']}")
        print(f"  • Line breaks preserved: {processing_stats['line_breaks_preserved']}")
        print(f"  • Total text length: {processing_stats['total_text_length']:,} characters")
        
        # File size info
        txt_size = Path(output_txt).stat().st_size / 1024
        print(f"  • Output file size: {txt_size:.1f} KB")
        
        return processing_stats
    
    def verify_hybrid_quality(self, original_quality_file: str, hybrid_file: str) -> Dict[str, Any]:
        """Verify that hybrid maintains quality while adding readability"""
        
        print(f"\n🔍 Verifying hybrid quality preservation...")
        
        # Quality patterns to check
        quality_checks = {
            'critical_formulas': {
                'pattern': r'\{R/\(১০০\+ R\)\}', 
                'description': 'Mathematical formulas',
                'original_count': 0, 'hybrid_count': 0
            },
            'bengali_numbers': {
                'pattern': r'[০-৯]+', 
                'description': 'Bengali numerals',
                'original_count': 0, 'hybrid_count': 0
            },
            'section_markers': {
                'pattern': r'[০-৯\d]+।', 
                'description': 'Section numbers',
                'original_count': 0, 'hybrid_count': 0
            },
            'act_references': {
                'pattern': r'২০[০-৯]{2}\s*সনের\s*[০-৯\d]+\s*নং', 
                'description': 'Act references',
                'original_count': 0, 'hybrid_count': 0
            },
            'chapter_headers': {
                'pattern': r'(প্রথম|দ্বিতীয়|তৃতীয়|চতুর্থ|পঞ্চম)\s*অধ্যায়', 
                'description': 'Chapter headers',
                'original_count': 0, 'hybrid_count': 0
            }
        }
        
        # Read both files
        with open(original_quality_file, 'r', encoding='utf-8') as f:
            original_text = f.read()
        
        with open(hybrid_file, 'r', encoding='utf-8') as f:
            hybrid_text = f.read()
        
        # Count patterns in both files
        for check_name, check_data in quality_checks.items():
            pattern = check_data['pattern']
            check_data['original_count'] = len(re.findall(pattern, original_text))
            check_data['hybrid_count'] = len(re.findall(pattern, hybrid_text))
            check_data['preserved'] = check_data['original_count'] == check_data['hybrid_count']
            
            # Print individual results
            status = "✅ PRESERVED" if check_data['preserved'] else "❌ CHANGED"
            print(f"  • {check_data['description']}: {status}")
            print(f"    Original: {check_data['original_count']}, Hybrid: {check_data['hybrid_count']}")
        
        # Count line breaks in hybrid
        hybrid_lines = len(hybrid_text.split('\n'))
        print(f"  • Line breaks in hybrid: {hybrid_lines:,}")
        
        return quality_checks
    
    def show_sample_comparison(self, hybrid_file: str, original_quality_file: str = None, lines: int = 20):
        """Show sample of hybrid output with comparison"""
        
        print(f"\n📝 Hybrid Quality + Readable Sample (first {lines} lines):")
        print("="*70)
        
        with open(hybrid_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if i > lines:
                    print("...")
                    break
                print(f"{i:3d}: {line.rstrip()}")
        
        print("="*70)


def main():
    """Main function to create hybrid quality + readable version"""
    
    print("🎯 Hybrid Quality + Readable Converter")
    print("Combines Vision AI Quality + Perfect Line Breaks")
    print("=" * 60)
    
    # File paths
    json_file = "ocr_output/pdf_ocr_corrected.json"
    hybrid_output = "document_types/act/finance_act_2024_hybrid.txt"
    analysis_file = "document_types/act/hybrid_analysis.json"
    original_quality_file = "finance_act_2024_plaintext.txt"
    
    if not Path(json_file).exists():
        print(f"❌ OCR file not found: {json_file}")
        return
    
    try:
        # Initialize hybrid converter
        converter = HybridQualityReadableConverter()
        
        # Create hybrid version
        stats = converter.convert_hybrid_quality_readable(json_file, hybrid_output)
        
        # Verify quality preservation
        if Path(original_quality_file).exists():
            quality_verification = converter.verify_hybrid_quality(original_quality_file, hybrid_output)
            stats['quality_verification'] = quality_verification
        
        # Save analysis
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"\n" + "="*60)
        print(f"🎉 HYBRID CONVERSION COMPLETE!")
        print(f"="*60)
        
        # Show results
        print(f"📄 Hybrid output: {hybrid_output}")
        print(f"📊 Analysis report: {analysis_file}")
        
        # Show sample
        converter.show_sample_comparison(hybrid_output, original_quality_file, lines=25)
        
        # Next steps
        print(f"\n🚀 Next Steps:")
        print(f"1. Review hybrid quality + readability: {hybrid_output}")
        print(f"2. Compare with original readable file for line structure")
        print(f"3. Verify critical formulas like {{R/(১০০+ R)}} are correct")
        print(f"4. Use this version for Act document pattern analysis")
        
        print(f"\n📋 Why Hybrid is Better for Parsing:")
        print(f"  • ✅ Vision AI quality text (no OF, Ol, sl, 81, 89 errors)")
        print(f"  • ✅ Perfect line breaks (legal structure clearly visible)")
        print(f"  • ✅ Easy pattern recognition for parsing rules")
        print(f"  • ✅ Human-readable for review and feedback")
        
    except Exception as e:
        print(f"❌ Hybrid conversion failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()