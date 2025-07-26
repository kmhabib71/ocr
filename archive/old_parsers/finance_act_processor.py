#!/usr/bin/env python3
"""
Efficient Finance Act Processor
Focused on complete text extraction and table parsing for legal documents
"""

import json
import re
import pdfplumber
from pathlib import Path
from typing import Dict, List, Any, Tuple
import pandas as pd
from collections import defaultdict

class FinanceActProcessor:
    """
    Efficient processor for Finance Act documents
    Focuses on completeness and accuracy
    """
    
    def __init__(self):
        # OCR error corrections for Bengali text
        self.corrections = {
            # Common encoding issues
            'evsjv‡`k': 'বাংলাদেশ',
            '†M‡RU': 'গেজেট',
            'AwZwi³': 'অতিরিক্ত',
            'Ryb': 'জুন',
            'm‡bi': 'মাসের',
            'bs': 'নং',
            'AvBb': 'আইন',
            # Add more corrections as needed
        }
        
        # Legal structure patterns
        self.section_patterns = [
            r'^(\d+[A-Z]*\.?\s*)',  # Section numbers
            r'^Section\s+(\d+[A-Z]*)',   # Section keyword  
            r'^ধারা\s+(\d+[A-Z]*)',       # Section in Bengali
            r'^অধ্যায়\s+(\d+)',          # Chapter in Bengali
        ]
        
        # Table indicators
        self.table_keywords = [
            'তালিকা', 'Table', 'Schedule', 'List', 'সূচি',
            'হার', 'Rate', 'Tax', 'কর', 'Amount', 'টাকা', 'Taka'
        ]

    def process_finance_act(self, pdf_path: str) -> Dict[str, Any]:
        """Main processing function"""
        print(f"🚀 Processing Finance Act: {pdf_path}")
        
        # Extract content efficiently
        content = self._extract_content_efficiently(pdf_path)
        
        # Parse structure
        structure = self._parse_document_structure(content)
        
        # Create final output
        result = {
            'document_info': {
                'title': 'Finance Act 2024',
                'type': 'Legal Document',
                'language': 'Bengali/English',
                'processing_date': pd.Timestamp.now().isoformat(),
                'total_pages': content['total_pages']
            },
            'legal_structure': {
                'sections': structure['sections'],
                'tables': structure['tables'],
                'cross_references': structure['references']
            },
            'content_analysis': {
                'total_text_blocks': len(content['text_blocks']),
                'total_tables': len(structure['tables']),
                'extraction_completeness': self._calculate_completeness(content, structure),
                'quality_score': self._calculate_quality_score(content, structure)
            },
            'database_ready': {
                'structured_sections': self._format_for_database(structure['sections']),
                'table_data': self._format_tables_for_database(structure['tables']),
                'searchable_content': self._create_searchable_index(content['text_blocks'])
            }
        }
        
        return result

    def _extract_content_efficiently(self, pdf_path: str) -> Dict[str, Any]:
        """Extract content efficiently without OCR"""
        text_blocks = []
        tables_raw = []
        total_pages = 0
        
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"📄 Processing {total_pages} pages...")
            
            for page_num, page in enumerate(pdf.pages, 1):
                if page_num % 10 == 0:
                    print(f"  • Page {page_num}/{total_pages}")
                
                # Extract text blocks
                page_text = page.extract_text()
                if page_text:
                    corrected_text = self._correct_text(page_text)
                    
                    # Split into logical blocks
                    blocks = self._split_into_blocks(corrected_text, page_num)
                    text_blocks.extend(blocks)
                
                # Extract tables
                page_tables = page.find_tables()
                for table in page_tables:
                    extracted_table = self._extract_table_data(table, page_num)
                    if extracted_table:
                        tables_raw.append(extracted_table)
        
        return {
            'text_blocks': text_blocks,
            'tables_raw': tables_raw,
            'total_pages': total_pages
        }

    def _correct_text(self, text: str) -> str:
        """Apply text corrections"""
        corrected = text
        for error, correction in self.corrections.items():
            corrected = corrected.replace(error, correction)
        
        # Clean up spacing
        corrected = re.sub(r'\s+', ' ', corrected)
        return corrected.strip()

    def _split_into_blocks(self, text: str, page_num: int) -> List[Dict]:
        """Split text into logical blocks"""
        blocks = []
        lines = text.split('\n')
        
        current_block = ""
        block_type = "paragraph"
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_block:
                    blocks.append({
                        'text': current_block.strip(),
                        'type': block_type,
                        'page': page_num
                    })
                    current_block = ""
                continue
            
            # Detect block type
            if any(re.match(pattern, line, re.IGNORECASE) for pattern in self.section_patterns):
                # Save previous block
                if current_block:
                    blocks.append({
                        'text': current_block.strip(),
                        'type': block_type,
                        'page': page_num
                    })
                
                # Start new section block
                current_block = line
                block_type = "section_header"
            elif any(keyword in line for keyword in self.table_keywords):
                # Table-related content
                if current_block:
                    blocks.append({
                        'text': current_block.strip(),
                        'type': block_type,
                        'page': page_num
                    })
                current_block = line
                block_type = "table_content"
            else:
                current_block += " " + line
        
        # Add final block
        if current_block:
            blocks.append({
                'text': current_block.strip(),
                'type': block_type,
                'page': page_num
            })
        
        return blocks

    def _extract_table_data(self, table, page_num: int) -> Dict:
        """Extract table data efficiently"""
        try:
            table_data = table.extract()
            if not table_data or len(table_data) < 2:
                return None
            
            # Clean table data
            cleaned_data = []
            for row in table_data:
                cleaned_row = []
                for cell in row:
                    if cell:
                        cleaned_cell = self._correct_text(str(cell))
                        cleaned_row.append(cleaned_cell)
                    else:
                        cleaned_row.append('')
                cleaned_data.append(cleaned_row)
            
            return {
                'data': cleaned_data,
                'headers': cleaned_data[0] if cleaned_data else [],
                'page': page_num,
                'type': self._classify_table(cleaned_data)
            }
        
        except Exception as e:
            print(f"⚠️ Table extraction error on page {page_num}: {e}")
            return None

    def _classify_table(self, table_data: List[List[str]]) -> str:
        """Classify table type"""
        if not table_data:
            return 'unknown'
        
        # Convert to text for analysis
        all_text = ' '.join(' '.join(row) for row in table_data).lower()
        
        if 'rate' in all_text or 'হার' in all_text:
            return 'tax_rate'
        elif 'schedule' in all_text or 'তালিকা' in all_text:
            return 'schedule'
        elif 'income' in all_text or 'আয়' in all_text:
            return 'income'
        elif 'amount' in all_text or 'টাকা' in all_text:
            return 'financial'
        else:
            return 'general'

    def _parse_document_structure(self, content: Dict) -> Dict[str, Any]:
        """Parse document into legal structure"""
        sections = []
        tables = content['tables_raw']
        references = []
        
        current_section = None
        
        for block in content['text_blocks']:
            if block['type'] == 'section_header':
                # Save previous section
                if current_section:
                    sections.append(current_section)
                
                # Start new section
                section_number = self._extract_section_number(block['text'])
                current_section = {
                    'section_number': section_number,
                    'title': block['text'][:100] + "..." if len(block['text']) > 100 else block['text'],
                    'content': [],
                    'page': block['page'],
                    'subsections': []
                }
            
            elif current_section:
                # Add content to current section
                current_section['content'].append({
                    'text': block['text'],
                    'type': block['type'],
                    'page': block['page']
                })
                
                # Extract references
                refs = re.findall(r'ধারা\s+(\d+[A-Z]*)|Section\s+(\d+[A-Z]*)', block['text'])
                for ref in refs:
                    ref_text = ref[0] or ref[1]
                    if ref_text and ref_text not in references:
                        references.append(ref_text)
        
        # Add final section
        if current_section:
            sections.append(current_section)
        
        return {
            'sections': sections,
            'tables': tables,
            'references': references
        }

    def _extract_section_number(self, text: str) -> str:
        """Extract section number"""
        for pattern in self.section_patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip() if match.groups() else text[:20]
        return text[:20] + "..." if len(text) > 20 else text

    def _calculate_completeness(self, content: Dict, structure: Dict) -> float:
        """Calculate extraction completeness"""
        text_blocks = len(content['text_blocks'])
        sections = len(structure['sections'])
        tables = len(structure['tables'])
        
        # Heuristic completeness calculation
        completeness = 0.7  # Base score
        
        if sections > 50:  # Reasonable number of sections for Finance Act
            completeness += 0.1
        
        if tables > 10:  # Good table extraction
            completeness += 0.1
        
        if text_blocks > 1000:  # Comprehensive text extraction
            completeness += 0.1
        
        return min(1.0, completeness)

    def _calculate_quality_score(self, content: Dict, structure: Dict) -> float:
        """Calculate overall quality score"""
        # Simple quality metrics
        avg_block_length = sum(len(block['text']) for block in content['text_blocks']) / len(content['text_blocks'])
        section_completeness = len(structure['sections']) / content['total_pages']  # Sections per page
        
        quality = 0.8  # Base quality
        
        if avg_block_length > 50:  # Good text extraction
            quality += 0.1
        
        if section_completeness > 0.5:  # Good structure detection
            quality += 0.1
        
        return min(1.0, quality)

    def _format_for_database(self, sections: List[Dict]) -> List[Dict]:
        """Format sections for database storage"""
        database_sections = []
        
        for section in sections:
            # Combine all content into full text
            full_content = ' '.join(item['text'] for item in section['content'])
            
            db_section = {
                'section_id': section['section_number'],
                'title': section['title'],
                'full_text': full_content,
                'page_number': section['page'],
                'word_count': len(full_content.split()),
                'subsection_count': len(section['subsections']),
                'searchable_text': full_content.lower()  # For search indexing
            }
            database_sections.append(db_section)
        
        return database_sections

    def _format_tables_for_database(self, tables: List[Dict]) -> List[Dict]:
        """Format tables for database storage"""
        database_tables = []
        
        for i, table in enumerate(tables):
            if not table or not table.get('data'):
                continue
            
            db_table = {
                'table_id': f"table_{i+1}",
                'table_type': table['type'],
                'page_number': table['page'],
                'headers': table['headers'],
                'data_rows': table['data'][1:] if len(table['data']) > 1 else [],
                'row_count': len(table['data']) - 1 if len(table['data']) > 1 else 0,
                'column_count': len(table['headers']) if table['headers'] else 0,
                'searchable_content': ' '.join(' '.join(row) for row in table['data']).lower()
            }
            database_tables.append(db_table)
        
        return database_tables

    def _create_searchable_index(self, text_blocks: List[Dict]) -> Dict[str, List[str]]:
        """Create searchable index for fast lookup"""
        index = defaultdict(list)
        
        for i, block in enumerate(text_blocks):
            text = block['text'].lower()
            words = re.findall(r'\w+', text)
            
            for word in words:
                if len(word) > 3:  # Index meaningful words only
                    index[word].append(f"block_{i}")
        
        # Convert to regular dict for JSON serialization
        return dict(index)


def main():
    """Process Finance Act 2024"""
    processor = FinanceActProcessor()
    
    pdf_path = "/mnt/c/a-ocr/bbocr/test_tax_documents/Finance_Act-2024.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    try:
        # Process the document
        result = processor.process_finance_act(pdf_path)
        
        # Save results
        output_file = "/mnt/c/a-ocr/bbocr/finance_act_2024_processed.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 FINANCE ACT 2024 - PROCESSING COMPLETE")
        print("="*60)
        
        doc_info = result['document_info']
        structure = result['legal_structure']
        analysis = result['content_analysis']
        
        print(f"📄 Document: {doc_info['title']}")
        print(f"📑 Total Pages: {doc_info['total_pages']}")
        print(f"📝 Legal Sections: {len(structure['sections'])}")
        print(f"📊 Tables Extracted: {len(structure['tables'])}")
        print(f"📋 Text Blocks: {analysis['total_text_blocks']}")
        print(f"🔗 Cross References: {len(structure['cross_references'])}")
        print(f"✅ Completeness: {analysis['extraction_completeness']*100:.1f}%")
        print(f"🎯 Quality Score: {analysis['quality_score']*100:.1f}%")
        
        print(f"\n🗄️ Database Ready Content:")
        db_ready = result['database_ready']
        print(f"  • Structured Sections: {len(db_ready['structured_sections'])}")
        print(f"  • Table Data: {len(db_ready['table_data'])}")
        print(f"  • Search Index: {len(db_ready['searchable_content'])} terms")
        
        print(f"\n📊 Sample Sections:")
        for i, section in enumerate(structure['sections'][:3]):
            print(f"  {i+1}. {section['section_number']}: {section['title'][:60]}...")
        
        print(f"\n📋 Sample Tables:")
        for i, table in enumerate(structure['tables'][:3]):
            if table:  # Check if table is not None
                print(f"  {i+1}. Page {table['page']}: {table['type']} "
                      f"({len(table['data'])}x{len(table['headers']) if table['headers'] else 0})")
        
        print(f"\n💾 Complete output saved to: {output_file}")
        print("🎉 Finance Act 2024 processing completed successfully!")
        print("\n📝 Ready for AI Tax Lawyer Integration!")
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()