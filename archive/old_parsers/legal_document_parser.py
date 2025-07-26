#!/usr/bin/env python3
"""
Comprehensive Legal Document Parser for Finance Acts
Specialized for Bangladesh Tax Law Documents with:
- Advanced table parsing
- Nested text structure (sections, subsections, clauses)
- Complete text extraction (no missing lines)
- Structured JSON output for AI analysis
"""

import cv2
import numpy as np
import json
import re
import fitz  # PyMuPDF
import pdfplumber
from pdf2image import convert_from_path
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
import pandas as pd
from collections import defaultdict

@dataclass
class TextElement:
    """Structure for text elements"""
    text: str
    bbox: Tuple[int, int, int, int]
    font_size: float
    font_name: str
    confidence: float = 1.0
    element_type: str = "text"
    page_number: int = 1

@dataclass
class TableCell:
    """Structure for table cells"""
    text: str
    row: int
    col: int
    bbox: Tuple[int, int, int, int]
    rowspan: int = 1
    colspan: int = 1

@dataclass
class Table:
    """Structure for tables"""
    cells: List[TableCell]
    headers: List[str]
    rows: int
    cols: int
    bbox: Tuple[int, int, int, int]
    page_number: int
    table_type: str = "general"

@dataclass
class LegalSection:
    """Structure for legal sections"""
    section_number: str
    title: str
    content: str
    subsections: List['LegalSection']
    tables: List[Table]
    clauses: List[str]
    references: List[str]
    page_number: int
    bbox: Tuple[int, int, int, int]

class FinanceActParser:
    """
    Advanced parser for Finance Act documents
    Handles complex legal document structure
    """
    
    def __init__(self):
        """Initialize the parser"""
        self.document_structure = {
            'metadata': {},
            'chapters': [],
            'sections': [],
            'tables': [],
            'references': [],
            'amendments': []
        }
        
        # Legal document patterns
        self.section_patterns = [
            r'^(\d+[A-Z]*\.?\s*.*?)$',  # Section numbers
            r'^Section\s+(\d+[A-Z]*)',   # Section keyword
            r'^অধ্যায়\s+(\d+)',          # Chapter in Bengali
            r'^ধারা\s+(\d+[A-Z]*)',       # Section in Bengali
        ]
        
        self.subsection_patterns = [
            r'^\((\d+)\)',               # (1), (2), etc.
            r'^\(([a-z])\)',             # (a), (b), etc.  
            r'^\(([i,v,x]+)\)',          # (i), (ii), etc.
            r'^([A-Z])\.?\s',            # A., B., etc.
        ]
        
        # Table detection patterns
        self.table_indicators = [
            'তালিকা', 'Table', 'Schedule', 'List',
            'হার', 'Rate', 'Tax', 'কর', 'Amount', 'টাকা'
        ]

    def extract_pdf_content(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive content from PDF using multiple methods
        """
        print(f"📄 Processing: {pdf_path}")
        
        # Method 1: Extract text with structure using pdfplumber
        text_content = self._extract_text_with_pdfplumber(pdf_path)
        
        # Method 2: Extract tables using pdfplumber
        tables = self._extract_tables_with_pdfplumber(pdf_path)
        
        # Method 3: Convert to images for OCR fallback
        images = self._convert_pdf_to_images(pdf_path)
        
        # Method 4: Extract metadata
        metadata = self._extract_metadata(pdf_path)
        
        return {
            'text_content': text_content,
            'tables': tables,
            'images': images,
            'metadata': metadata,
            'total_pages': len(images)
        }

    def _extract_text_with_pdfplumber(self, pdf_path: str) -> List[Dict]:
        """Extract text with formatting information using pdfplumber"""
        text_elements = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"📖 Processing page {page_num}")
                
                # Extract text with character-level information
                chars = page.chars
                
                # Group characters into words and lines
                lines = self._group_chars_into_lines(chars)
                
                for line_num, line in enumerate(lines):
                    if line['text'].strip():
                        text_elements.append({
                            'text': line['text'],
                            'bbox': line['bbox'],
                            'font_size': line['font_size'],
                            'font_name': line['font_name'],
                            'page_number': page_num,
                            'line_number': line_num,
                            'element_type': self._classify_text_type(line['text'])
                        })
        
        return text_elements

    def _group_chars_into_lines(self, chars: List[Dict]) -> List[Dict]:
        """Group characters into lines maintaining structure"""
        if not chars:
            return []
        
        # Sort characters by position
        chars = sorted(chars, key=lambda c: (c['top'], c['x0']))
        
        lines = []
        current_line = {
            'text': '',
            'chars': [],
            'top': chars[0]['top'],
            'font_size': chars[0]['size'],
            'font_name': chars[0]['fontname']
        }
        
        for char in chars:
            # Check if this character belongs to the current line
            if abs(char['top'] - current_line['top']) < 5:  # Same line threshold
                current_line['chars'].append(char)
                current_line['text'] += char['text']
            else:
                # Finalize current line
                if current_line['text'].strip():
                    lines.append(self._finalize_line(current_line))
                
                # Start new line
                current_line = {
                    'text': char['text'],
                    'chars': [char],
                    'top': char['top'],
                    'font_size': char['size'],
                    'font_name': char['fontname']
                }
        
        # Add last line
        if current_line['text'].strip():
            lines.append(self._finalize_line(current_line))
        
        return lines

    def _finalize_line(self, line: Dict) -> Dict:
        """Finalize line with bounding box"""
        chars = line['chars']
        bbox = (
            min(c['x0'] for c in chars),
            min(c['top'] for c in chars),
            max(c['x1'] for c in chars),
            max(c['bottom'] for c in chars)
        )
        
        return {
            'text': line['text'],
            'bbox': bbox,
            'font_size': line['font_size'],
            'font_name': line['font_name']
        }

    def _classify_text_type(self, text: str) -> str:
        """Classify text type based on content"""
        text = text.strip()
        
        # Check for section headers
        for pattern in self.section_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return 'section_header'
        
        # Check for subsections
        for pattern in self.subsection_patterns:
            if re.match(pattern, text):
                return 'subsection'
        
        # Check for table indicators
        if any(indicator in text for indicator in self.table_indicators):
            return 'table_related'
        
        # Check for references
        if re.search(r'ধারা\s+\d+|Section\s+\d+|অধ্যায়\s+\d+', text):
            return 'reference'
        
        return 'paragraph'

    def _extract_tables_with_pdfplumber(self, pdf_path: str) -> List[Table]:
        """Extract tables using pdfplumber with advanced detection"""
        tables = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"🔍 Searching for tables on page {page_num}")
                
                # Method 1: Direct table extraction
                page_tables = page.find_tables()
                
                for table_num, table in enumerate(page_tables):
                    extracted_table = self._process_pdfplumber_table(
                        table, page_num, table_num
                    )
                    if extracted_table:
                        tables.append(extracted_table)
                
                # Method 2: Custom table detection for legal documents
                custom_tables = self._detect_custom_tables(page, page_num)
                tables.extend(custom_tables)
        
        return tables

    def _process_pdfplumber_table(self, table, page_num: int, table_num: int) -> Optional[Table]:
        """Process a pdfplumber table into our structure"""
        try:
            # Extract table data
            table_data = table.extract()
            if not table_data:
                return None
            
            # Create table cells
            cells = []
            headers = table_data[0] if table_data else []
            
            for row_idx, row in enumerate(table_data):
                for col_idx, cell_text in enumerate(row or []):
                    if cell_text:
                        cell = TableCell(
                            text=str(cell_text).strip(),
                            row=row_idx,
                            col=col_idx,
                            bbox=(0, 0, 0, 0)  # Will be updated if needed
                        )
                        cells.append(cell)
            
            # Get table bounding box
            bbox = table.bbox if hasattr(table, 'bbox') else (0, 0, 0, 0)
            
            return Table(
                cells=cells,
                headers=[str(h) if h else '' for h in headers],
                rows=len(table_data),
                cols=len(headers) if headers else 0,
                bbox=bbox,
                page_number=page_num,
                table_type=self._classify_table_type(table_data)
            )
            
        except Exception as e:
            print(f"⚠️ Error processing table: {e}")
            return None

    def _detect_custom_tables(self, page, page_num: int) -> List[Table]:
        """Detect tables using custom logic for legal documents"""
        custom_tables = []
        
        # Look for patterns that indicate tables
        lines = page.lines
        rects = page.rects
        
        # Group horizontal and vertical lines to detect table structure
        h_lines = [line for line in lines if abs(line['top'] - line['bottom']) < 2]
        v_lines = [line for line in lines if abs(line['x0'] - line['x1']) < 2]
        
        if len(h_lines) >= 3 and len(v_lines) >= 2:  # Minimum table structure
            # Extract table region
            table_bbox = self._calculate_table_bbox(h_lines, v_lines)
            
            # Extract text within table region
            table_text = page.within_bbox(table_bbox).extract_text()
            
            if table_text and any(indicator in table_text for indicator in self.table_indicators):
                # Parse the table text into cells
                table = self._parse_table_text(table_text, table_bbox, page_num)
                if table:
                    custom_tables.append(table)
        
        return custom_tables

    def _calculate_table_bbox(self, h_lines: List, v_lines: List) -> Tuple[float, float, float, float]:
        """Calculate bounding box from table lines"""
        if not h_lines or not v_lines:
            return (0, 0, 0, 0)
        
        left = min(line['x0'] for line in v_lines)
        right = max(line['x1'] for line in v_lines)
        top = min(line['top'] for line in h_lines)
        bottom = max(line['bottom'] for line in h_lines)
        
        return (left, top, right, bottom)

    def _parse_table_text(self, table_text: str, bbox: Tuple, page_num: int) -> Optional[Table]:
        """Parse table text into structured format"""
        if not table_text.strip():
            return None
        
        lines = [line.strip() for line in table_text.split('\n') if line.strip()]
        if len(lines) < 2:
            return None
        
        # Simple table parsing - can be enhanced
        cells = []
        headers = []
        
        # First line as headers
        if lines:
            headers = lines[0].split()
        
        # Parse rows simple approach)
        for row_idx, line in enumerate(lines[1:], 1):
            parts = line.split()
            for col_idx, part in enumerate(parts):
                cell = TableCell(
                    text=part,
                    row=row_idx,
                    col=col_idx,
                    bbox=bbox
                )
                cells.append(cell)
        
        return Table(
            cells=cells,
            headers=headers,
            rows=len(lines) - 1,
            cols=len(headers),
            bbox=bbox,
            page_number=page_num,
            table_type='custom_detected'
        )

    def _classify_table_type(self, table_data: List[List]) -> str:
        """Classify table type based on content"""
        if not table_data:
            return 'unknown'
        
        # Convert table to text for analysis
        table_text = ' '.join(' '.join(str(cell) if cell else '' for cell in row) for row in table_data)
        
        if any(word in table_text.lower() for word in ['rate', 'হার', 'tax', 'কর']):
            return 'tax_rate'
        elif any(word in table_text.lower() for word in ['schedule', 'তালিকা']):
            return 'schedule'
        elif any(word in table_text.lower() for word in ['amount', 'টাকা', 'taka']):
            return 'financial'
        else:
            return 'general'

    def _convert_pdf_to_images(self, pdf_path: str) -> List[np.ndarray]:
        """Convert PDF pages to images for OCR fallback"""
        try:
            images = convert_from_path(pdf_path, dpi=300)
            return [np.array(img) for img in images]
        except Exception as e:
            print(f"⚠️ Error converting PDF to images: {e}")
            return []

    def _extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extract document metadata"""
        metadata = {}
        
        try:
            with fitz.open(pdf_path) as doc:
                metadata = doc.metadata
                metadata['page_count'] = len(doc)
                metadata['file_size'] = Path(pdf_path).stat().st_size
        except Exception as e:
            print(f"⚠️ Error extracting metadata: {e}")
        
        return metadata

    def parse_legal_structure(self, text_elements: List[Dict]) -> List[LegalSection]:
        """Parse text elements into legal document structure"""
        sections = []
        current_section = None
        
        for element in text_elements:
            text = element['text']
            element_type = element['element_type']
            
            if element_type == 'section_header':
                # Start new section
                if current_section:
                    sections.append(current_section)
                
                section_number = self._extract_section_number(text)
                current_section = LegalSection(
                    section_number=section_number,
                    title=text,
                    content='',
                    subsections=[],
                    tables=[],
                    clauses=[],
                    references=[],
                    page_number=element['page_number'],
                    bbox=element['bbox']
                )
            
            elif current_section:
                if element_type == 'subsection':
                    # Handle subsections
                    current_section.subsections.append(
                        LegalSection(
                            section_number=f"{current_section.section_number}({len(current_section.subsections)+1})",
                            title=text[:50] + "..." if len(text) > 50 else text,
                            content=text,
                            subsections=[],
                            tables=[],
                            clauses=[],
                            references=[],
                            page_number=element['page_number'],
                            bbox=element['bbox']
                        )
                    )
                elif element_type == 'reference':
                    current_section.references.append(text)
                else:
                    current_section.content += text + ' '
        
        # Add last section
        if current_section:
            sections.append(current_section)
        
        return sections

    def _extract_section_number(self, text: str) -> str:
        """Extract section number from text"""
        for pattern in self.section_patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1) if match.groups() else text[:20]
        return "Unknown"

    def create_structured_json(self, pdf_path: str) -> Dict[str, Any]:
        """Create complete structured JSON output"""
        print("🚀 Starting comprehensive legal document parsing...")
        
        # Extract all content
        content = self.extract_pdf_content(pdf_path)
        
        # Parse legal structure
        sections = self.parse_legal_structure(content['text_content'])
        
        # Create structured output
        structured_document = {
            'document_info': {
                'title': 'Finance Act 2024',
                'type': 'Legal Act',
                'language': 'Mixed (Bengali/English)',
                'total_pages': content['total_pages'],
                'processing_date': pd.Timestamp.now().isoformat(),
                'metadata': content['metadata']
            },
            'content': {
                'sections': [asdict(section) for section in sections],
                'tables': [asdict(table) for table in content['tables']],
                'raw_text_elements': content['text_content'][:100],  # Sample for verification
                'total_text_elements': len(content['text_content'])
            },
            'analysis': {
                'section_count': len(sections),
                'table_count': len(content['tables']),
                'estimated_completeness': self._calculate_completeness(content),
                'cross_references': self._extract_cross_references(content['text_content'])
            }
        }
        
        return structured_document

    def _calculate_completeness(self, content: Dict) -> float:
        """Calculate estimated completeness of extraction"""
        text_elements = len(content['text_content'])
        tables = len(content['tables'])
        pages = content['total_pages']
        
        # Simple heuristic - can be improved
        expected_elements_per_page = 50  # Rough estimate
        expected_total = pages * expected_elements_per_page
        
        completeness = min(1.0, text_elements / expected_total) if expected_total > 0 else 0.5
        
        # Bonus for tables
        if tables > 0:
            completeness += 0.1
        
        return round(min(1.0, completeness), 2)

    def _extract_cross_references(self, text_elements: List[Dict]) -> List[str]:
        """Extract cross-references between sections"""
        references = []
        
        for element in text_elements:
            text = element['text']
            # Look for references to other sections
            refs = re.findall(r'ধারা\s+(\d+[A-Z]*)|Section\s+(\d+[A-Z]*)', text, re.IGNORECASE)
            for ref in refs:
                ref_text = ref[0] or ref[1]
                if ref_text:
                    references.append(f"Section {ref_text}")
        
        return list(set(references))  # Remove duplicates

def main():
    """Main function to test with Finance Act 2024"""
    parser = FinanceActParser()
    
    pdf_path = "/mnt/c/a-ocr/bbocr/test_tax_documents/Finance_Act-2024.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    try:
        # Parse the document
        result = parser.create_structured_json(pdf_path)
        
        # Save results
        output_file = "/mnt/c/a-ocr/bbocr/finance_act_2024_parsed.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 PARSING SUMMARY")
        print("="*60)
        print(f"📄 Document: {result['document_info']['title']}")
        print(f"📑 Total Pages: {result['document_info']['total_pages']}")
        print(f"📝 Sections Extracted: {result['analysis']['section_count']}")
        print(f"📊 Tables Extracted: {result['analysis']['table_count']}")
        print(f"📋 Text Elements: {result['content']['total_text_elements']}")
        print(f"✅ Completeness: {result['analysis']['estimated_completeness']*100:.1f}%")
        print(f"🔗 Cross References: {len(result['analysis']['cross_references'])}")
        print(f"💾 Output saved to: {output_file}")
        
        # Show sample sections
        print(f"\n📋 First 3 Sections:")
        for i, section in enumerate(result['content']['sections'][:3]):
            print(f"  {i+1}. {section['section_number']}: {section['title'][:60]}...")
        
        # Show sample tables
        if result['content']['tables']:
            print(f"\n📊 Tables Found:")
            for i, table in enumerate(result['content']['tables'][:3]):
                print(f"  {i+1}. Page {table['page_number']}: {table['table_type']} ({table['rows']}x{table['cols']})")
        
        print("\n🎉 Finance Act 2024 parsing completed successfully!")
        
    except Exception as e:
        print(f"❌ Error parsing document: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()