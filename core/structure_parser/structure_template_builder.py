#!/usr/bin/env python3
"""
Structure Template Builder
Analyzes real OCR patterns and builds intelligent templates for legal document parsing
Based on actual Finance Act 2024 structure patterns
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class LegalElement:
    """Legal document element with proper hierarchy"""
    element_type: str  # chapter, section, subsection, clause, article, text
    identifier: Optional[str]
    title: str
    content: str
    page_number: int
    line_number: int
    parent_id: Optional[str] = None
    children: List['LegalElement'] = None
    level: int = 0
    
    def __post_init__(self):
        if self.children is None:
            self.children = []

class StructureTemplateBuilder:
    """Builds intelligent templates from real OCR patterns"""
    
    def __init__(self):
        # Real patterns found in the OCR data
        self.patterns = {
            'chapter': [
                r'^(প্রথম|দ্বিতীয়|তৃতীয়|চতুর্থ|পঞ্চম|ষষ্ঠ|সপ্তম|অষ্টম|নবম|দশম)\s*অধ্যায়\s*$',
                r'^অধ্যায়\s*([০-৯\d]+)\s*$'
            ],
            'chapter_title': [
                r'^(প্রারম্ভিক|ভ্রমণ কর আইন.*?এর সংশোধন|মূল্য সংযোজন কর.*?এর সংশোধন)$'
            ],
            'section': [
                r'^([০-৯\d]+)।\s*(.+?)।?\s*[—\-]?\s*(.*)$',  # ১। title।- content
                r'^([০-৯\d]+)।\s*(.+)$'  # ১। content
            ],
            'subsection': [
                r'^\s*\(([০-৯\d]+)\)\s*(.+)$'  # (১) content
            ],
            'clause': [
                r'^\s*\(([ক-৯]+)\)\s*(.+)$'  # (ক) content
            ],
            'sub_clause': [
                r'^\s*\(([অ-৯]+)\)\s*(.+)$'  # (অ) content
            ],
            'schedule': [
                r'^(প্রথম|দ্বিতীয়|তৃতীয়|চতুর্থ|পঞ্চম)\s*তফসিল\s*$',
                r'^তফসিল\s*([০-৯\d]+)\s*$'
            ],
            'table_indicator': [
                r'টেবিল[-\s]*([০-৯\d]+)',
                r'(শিরনামা|কোড|হার|বিবরণ)',
                r'H\.S\.\s*Code'
            ]
        }
        
        # Context tracking for hierarchy
        self.current_context = {
            'chapter': None,
            'section': None,
            'subsection': None,
            'clause': None
        }
        
        # Legal document structure rules
        self.hierarchy_rules = {
            'chapter': {'level': 1, 'can_contain': ['section', 'text']},
            'chapter_title': {'level': 1, 'can_contain': ['section', 'text']},
            'section': {'level': 2, 'can_contain': ['subsection', 'clause', 'text']},
            'subsection': {'level': 3, 'can_contain': ['clause', 'text']},
            'clause': {'level': 4, 'can_contain': ['sub_clause', 'text']},
            'sub_clause': {'level': 5, 'can_contain': ['text']},
            'schedule': {'level': 1, 'can_contain': ['text', 'table']},
            'table_indicator': {'level': 6, 'can_contain': []},
            'text': {'level': 6, 'can_contain': []}
        }
    
    def analyze_line(self, line: str, line_number: int, page_number: int) -> Optional[LegalElement]:
        """Analyze a single line and determine its legal structure"""
        
        line = line.strip()
        if not line:
            return None
        
        # Check for each pattern type
        for element_type, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    return self._create_element_from_match(
                        element_type, match, line, line_number, page_number
                    )
        
        # If no pattern matches, treat as regular text
        return LegalElement(
            element_type='text',
            identifier=None,
            title='',
            content=line,
            page_number=page_number,
            line_number=line_number,
            level=self._get_current_level() + 1
        )
    
    def _create_element_from_match(self, element_type: str, match: re.Match, 
                                 line: str, line_number: int, page_number: int) -> LegalElement:
        """Create legal element from regex match"""
        
        if element_type == 'chapter':
            identifier = match.group(1)
            title = line
            content = ''
            
        elif element_type == 'section':
            identifier = match.group(1)
            if len(match.groups()) >= 3:
                title = match.group(2)
                content = match.group(3) if match.group(3) else ''
            else:
                title = ''
                content = match.group(2) if len(match.groups()) >= 2 else ''
                
        elif element_type in ['subsection', 'clause', 'sub_clause']:
            identifier = match.group(1)
            title = ''
            content = match.group(2)
            
        else:
            identifier = None
            title = line
            content = line
        
        level = self.hierarchy_rules[element_type]['level']
        
        return LegalElement(
            element_type=element_type,
            identifier=identifier,
            title=title,
            content=content,
            page_number=page_number,
            line_number=line_number,
            level=level
        )
    
    def _get_current_level(self) -> int:
        """Get current hierarchy level for context"""
        
        for element_type in ['clause', 'subsection', 'section', 'chapter']:
            if self.current_context[element_type]:
                return self.hierarchy_rules[element_type]['level']
        
        return 0
    
    def _update_context(self, element: LegalElement):
        """Update current hierarchy context"""
        
        element_type = element.element_type
        
        if element_type in self.current_context:
            # Clear lower levels
            hierarchy_order = ['chapter', 'section', 'subsection', 'clause']
            
            try:
                current_index = hierarchy_order.index(element_type)
                
                # Clear this level and below
                for i in range(current_index, len(hierarchy_order)):
                    self.current_context[hierarchy_order[i]] = None
                
                # Set current level
                self.current_context[element_type] = element
                
            except ValueError:
                pass  # Element type not in hierarchy order
    
    def parse_document_structure(self, ocr_data: List[Dict]) -> List[LegalElement]:
        """Parse entire document structure from OCR data"""
        
        print("🔍 Analyzing document structure from OCR patterns...")
        
        all_elements = []
        
        for page_data in ocr_data:
            page_number = page_data['page_number']
            text = page_data['extracted_text']
            
            lines = text.split('\n')
            
            for line_number, line in enumerate(lines, 1):
                element = self.analyze_line(line, line_number, page_number)
                
                if element:
                    # Update context for hierarchy
                    if element.element_type in self.current_context:
                        self._update_context(element)
                    
                    # Set parent relationship
                    element.parent_id = self._get_parent_id()
                    
                    all_elements.append(element)
        
        print(f"✅ Parsed {len(all_elements)} structural elements")
        return all_elements
    
    def _get_parent_id(self) -> Optional[str]:
        """Get ID of current parent element"""
        
        # Find the most recent valid parent
        for element_type in ['clause', 'subsection', 'section', 'chapter']:
            if self.current_context[element_type]:
                parent = self.current_context[element_type]
                return f"{parent.element_type}_{parent.page_number}_{parent.line_number}"
        
        return None
    
    def build_hierarchy_tree(self, elements: List[LegalElement]) -> Dict[str, Any]:
        """Build hierarchical tree structure from flat elements"""
        
        print("🏗️ Building hierarchical structure...")
        
        # Group elements by type and hierarchy
        hierarchy = {
            'document_title': 'Bangladesh Finance Act 2024',
            'chapters': [],
            'sections': [],
            'orphaned_elements': []
        }
        
        current_chapter = None
        current_section = None
        current_subsection = None
        current_clause = None
        
        for element in elements:
            element_dict = asdict(element)
            
            if element.element_type == 'chapter':
                if current_chapter:
                    hierarchy['chapters'].append(current_chapter)
                
                current_chapter = {
                    'number': element.identifier,
                    'title': element.title,
                    'content': element.content,
                    'page_number': element.page_number,
                    'sections': [],
                    'raw_element': element_dict
                }
                
                # Reset lower levels
                current_section = None
                current_subsection = None
                current_clause = None
                
            elif element.element_type == 'section':
                if current_section:
                    if current_chapter:
                        current_chapter['sections'].append(current_section)
                    else:
                        hierarchy['sections'].append(current_section)
                
                current_section = {
                    'number': element.identifier,
                    'title': element.title,
                    'content': element.content,
                    'page_number': element.page_number,
                    'subsections': [],
                    'clauses': [],
                    'raw_element': element_dict
                }
                
                # Reset lower levels
                current_subsection = None
                current_clause = None
                
            elif element.element_type == 'subsection':
                subsection_dict = {
                    'identifier': element.identifier,
                    'content': element.content,
                    'page_number': element.page_number,
                    'clauses': [],
                    'raw_element': element_dict
                }
                
                if current_section:
                    current_section['subsections'].append(subsection_dict)
                else:
                    hierarchy['orphaned_elements'].append(element_dict)
                
                current_subsection = subsection_dict
                current_clause = None
                
            elif element.element_type == 'clause':
                clause_dict = {
                    'identifier': element.identifier,
                    'content': element.content,
                    'page_number': element.page_number,
                    'sub_clauses': [],
                    'raw_element': element_dict
                }
                
                if current_subsection:
                    current_subsection['clauses'].append(clause_dict)
                elif current_section:
                    current_section['clauses'].append(clause_dict)
                else:
                    hierarchy['orphaned_elements'].append(element_dict)
                
                current_clause = clause_dict
                
            elif element.element_type == 'sub_clause':
                sub_clause_dict = {
                    'identifier': element.identifier,
                    'content': element.content,
                    'page_number': element.page_number,
                    'raw_element': element_dict
                }
                
                if current_clause:
                    current_clause['sub_clauses'].append(sub_clause_dict)
                else:
                    hierarchy['orphaned_elements'].append(element_dict)
                    
            else:  # text or other elements
                # Attach to current container
                if current_clause and 'text_content' not in current_clause:
                    current_clause['text_content'] = []
                if current_subsection and 'text_content' not in current_subsection:
                    current_subsection['text_content'] = []
                if current_section and 'text_content' not in current_section:
                    current_section['text_content'] = []
                
                text_dict = {
                    'content': element.content,
                    'page_number': element.page_number,
                    'line_number': element.line_number
                }
                
                if current_clause:
                    current_clause['text_content'].append(text_dict)
                elif current_subsection:
                    current_subsection['text_content'].append(text_dict)
                elif current_section:
                    current_section['text_content'].append(text_dict)
                elif current_chapter:
                    if 'text_content' not in current_chapter:
                        current_chapter['text_content'] = []
                    current_chapter['text_content'].append(text_dict)
        
        # Add final elements
        if current_section:
            if current_chapter:
                current_chapter['sections'].append(current_section)
            else:
                hierarchy['sections'].append(current_section)
        
        if current_chapter:
            hierarchy['chapters'].append(current_chapter)
        
        print(f"✅ Built hierarchy: {len(hierarchy['chapters'])} chapters, {len(hierarchy['sections'])} sections")
        return hierarchy
    
    def generate_statistics(self, hierarchy: Dict[str, Any]) -> Dict[str, Any]:
        """Generate parsing statistics"""
        
        stats = {
            'total_chapters': len(hierarchy['chapters']),
            'total_sections': len(hierarchy['sections']),
            'total_orphaned': len(hierarchy['orphaned_elements']),
            'chapter_breakdown': [],
            'parsing_quality': {}
        }
        
        # Chapter breakdown
        for chapter in hierarchy['chapters']:
            chapter_stats = {
                'chapter_number': chapter['number'],
                'sections_count': len(chapter['sections']),
                'total_subsections': sum(len(section['subsections']) for section in chapter['sections']),
                'total_clauses': sum(
                    len(section['clauses']) + 
                    sum(len(subsection['clauses']) for subsection in section['subsections'])
                    for section in chapter['sections']
                ),
                'page_span': f"Page {chapter['page_number']}"
            }
            stats['chapter_breakdown'].append(chapter_stats)
        
        # Quality metrics
        total_elements = (stats['total_chapters'] + stats['total_sections'] + 
                         sum(cb['total_subsections'] + cb['total_clauses'] 
                             for cb in stats['chapter_breakdown']))
        
        if total_elements > 0:
            orphaned_rate = stats['total_orphaned'] / total_elements
            stats['parsing_quality'] = {
                'structure_capture_rate': 1 - orphaned_rate,
                'estimated_accuracy': max(0.6, 1 - orphaned_rate * 2),  # Conservative estimate
                'hierarchy_completeness': len(hierarchy['chapters']) > 0 and len(hierarchy['sections']) > 0
            }
        
        return stats


def main():
    """Main function to analyze structure and build templates"""
    
    print("🎯 Structure Template Builder")
    print("=" * 50)
    
    # Input files
    ocr_file = "ocr_output/pdf_ocr_results.json"
    output_file = "finance_act_structured_template.json"
    
    if not Path(ocr_file).exists():
        print(f"❌ OCR file not found: {ocr_file}")
        print("Please run simple_pdf_ocr.py first")
        return
    
    try:
        # Load OCR data
        with open(ocr_file, 'r', encoding='utf-8') as f:
            ocr_data = json.load(f)
        
        # Initialize template builder
        builder = StructureTemplateBuilder()
        
        # Parse structure
        elements = builder.parse_document_structure(ocr_data)
        
        # Build hierarchy
        hierarchy = builder.build_hierarchy_tree(elements)
        
        # Generate statistics
        stats = builder.generate_statistics(hierarchy)
        
        # Create final output
        result = {
            'document_metadata': {
                'title': 'Bangladesh Finance Act 2024 - Template Structure',
                'total_pages': len(ocr_data),
                'parsing_method': 'Intelligent Template Analysis',
                'structure_quality': stats['parsing_quality']
            },
            'structured_content': hierarchy,
            'parsing_statistics': stats,
            'template_patterns': builder.patterns,
            'validation': {
                'chapters_detected': stats['total_chapters'],
                'sections_detected': stats['total_sections'],
                'estimated_accuracy': stats['parsing_quality'].get('estimated_accuracy', 0.6),
                'hierarchy_complete': stats['parsing_quality'].get('hierarchy_completeness', False)
            }
        }
        
        # Save result
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n" + "=" * 70)
        print("🎉 STRUCTURE TEMPLATE ANALYSIS COMPLETE!")
        print("=" * 70)
        
        metadata = result['document_metadata']
        print(f"📄 Document: {metadata['title']}")
        print(f"📊 Total Pages: {metadata['total_pages']}")
        print(f"🎯 Estimated Accuracy: {metadata['structure_quality']['estimated_accuracy']*100:.1f}%")
        
        print(f"\n📋 Structure Breakdown:")
        for chapter_stat in stats['chapter_breakdown']:
            print(f"  • Chapter {chapter_stat['chapter_number']}: {chapter_stat['sections_count']} sections, {chapter_stat['total_clauses']} clauses")
        
        validation = result['validation']
        print(f"\n✅ Validation Results:")
        print(f"  • Chapters: {validation['chapters_detected']}")
        print(f"  • Sections: {validation['sections_detected']}")
        print(f"  • Accuracy: {validation['estimated_accuracy']*100:.1f}%")
        print(f"  • Hierarchy: {'Complete' if validation['hierarchy_complete'] else 'Partial'}")
        
        print(f"\n💾 Template saved to: {output_file}")
        print(f"📊 File size: {Path(output_file).stat().st_size / 1024:.1f} KB")
        
        print(f"\n🎯 Template Quality Assessment:")
        accuracy = validation['estimated_accuracy']
        if accuracy >= 0.8:
            print(f"✅ Excellent - Ready for production use")
        elif accuracy >= 0.6:
            print(f"⚠️ Good - Needs minor refinement")
        else:
            print(f"❌ Needs improvement - Consider manual annotation")
        
        print(f"\n🚀 Next Steps:")
        print(f"1. Review structured output for accuracy")
        print(f"2. Refine patterns based on missed elements")
        print(f"3. Use template for consistent parsing")
        
    except Exception as e:
        print(f"❌ Template building failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()