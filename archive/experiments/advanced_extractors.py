#!/usr/bin/env python3
"""
Advanced Extractors for Legal Documents
Specialized extractors for tables, forms, math, and nested structures
"""

import cv2
import numpy as np
import re
import json
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
import pytesseract
from PIL import Image

@dataclass
class CellInfo:
    """Information about a table cell"""
    row: int
    col: int
    text: str
    bbox: Tuple[float, float, float, float]
    confidence: float
    is_header: bool = False
    is_merged: bool = False
    merge_span: Tuple[int, int] = (1, 1)  # (row_span, col_span)

@dataclass
class TableStructure:
    """Complete table structure information"""
    rows: int
    cols: int
    cells: List[List[CellInfo]]
    headers: List[str]
    table_type: str
    has_merged_cells: bool = False
    grid_lines: Dict[str, List] = None
    
    def __post_init__(self):
        if self.grid_lines is None:
            self.grid_lines = {'horizontal': [], 'vertical': []}

class AdvancedTableExtractor:
    """Advanced table extraction with cell-level precision"""
    
    def __init__(self):
        self.min_line_length = 50
        self.line_thickness_threshold = 3
        self.cell_merge_threshold = 10
        
        # Table classification patterns
        self.table_patterns = {
            'tax_rate': [
                'হার', 'Rate', '%', 'শতাংশ', 'Tax', 'কর',
                'HS Code', 'Heading', 'শিরোনাম'
            ],
            'schedule': [
                'তফসিল', 'Schedule', 'তালিকা', 'List',
                'ক্রমিক', 'Serial', 'নং', 'No.'
            ],
            'financial': [
                'টাকা', 'Taka', 'Amount', 'পরিমাণ',
                'Income', 'আয়', 'Salary', 'বেতন'
            ],
            'form': [
                'আবেদন', 'Application', 'ফর্ম', 'Form',
                'নাম', 'Name', 'ঠিকানা', 'Address'
            ]
        }
    
    def detect_table_structure(self, image: np.ndarray) -> Optional[TableStructure]:
        """Detect complete table structure using multiple methods"""
        
        # Method 1: Line-based detection
        line_structure = self._detect_by_lines(image)
        
        # Method 2: Contour-based detection  
        contour_structure = self._detect_by_contours(image)
        
        # Method 3: Text pattern-based detection
        pattern_structure = self._detect_by_patterns(image)
        
        # Merge results and choose best
        best_structure = self._merge_detection_results(
            line_structure, contour_structure, pattern_structure
        )
        
        if best_structure:
            # Extract cell contents
            self._extract_cell_contents(image, best_structure)
            
            # Classify table type
            best_structure.table_type = self._classify_table(best_structure)
        
        return best_structure
    
    def _detect_by_lines(self, image: np.ndarray) -> Optional[TableStructure]:
        """Detect table structure using line detection"""
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Detect horizontal lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
        
        # Detect vertical lines
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)
        
        # Find line coordinates
        h_lines = self._extract_line_coordinates(horizontal_lines, 'horizontal')
        v_lines = self._extract_line_coordinates(vertical_lines, 'vertical')
        
        if len(h_lines) < 2 or len(v_lines) < 2:
            return None
        
        # Create grid structure
        rows = len(h_lines) - 1
        cols = len(v_lines) - 1
        
        if rows <= 0 or cols <= 0:
            return None
        
        # Initialize cell structure
        cells = []
        for r in range(rows):
            cell_row = []
            for c in range(cols):
                # Calculate cell bbox
                x1 = v_lines[c]
                y1 = h_lines[r]
                x2 = v_lines[c + 1]
                y2 = h_lines[r + 1]
                
                cell_info = CellInfo(
                    row=r,
                    col=c,
                    text="",  # Will be filled later
                    bbox=(x1, y1, x2, y2),
                    confidence=0.9,
                    is_header=(r == 0)
                )
                cell_row.append(cell_info)
            cells.append(cell_row)
        
        return TableStructure(
            rows=rows,
            cols=cols,
            cells=cells,
            headers=[],  # Will be filled later
            table_type="unknown",
            grid_lines={'horizontal': h_lines, 'vertical': v_lines}
        )
    
    def _detect_by_contours(self, image: np.ndarray) -> Optional[TableStructure]:
        """Detect table structure using contour analysis"""
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Apply threshold
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter rectangular contours that could be cells
        cell_contours = []
        for contour in contours:
            # Approximate contour
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Check if rectangular and reasonable size
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(contour)
                if w > 30 and h > 20 and w * h > 600:  # Minimum cell size
                    cell_contours.append((x, y, w, h))
        
        if len(cell_contours) < 4:  # At least 2x2 table
            return None
        
        # Organize contours into grid
        return self._organize_contours_to_grid(cell_contours)
    
    def _detect_by_patterns(self, image: np.ndarray) -> Optional[TableStructure]:
        """Detect table structure using text patterns"""
        
        # Extract all text with positions
        data = pytesseract.image_to_data(image, lang='ben+eng', output_type=pytesseract.Output.DICT)
        
        # Group text by rows (similar y-coordinates)
        text_rows = self._group_text_by_rows(data)
        
        if len(text_rows) < 2:
            return None
        
        # Detect column structure
        column_positions = self._detect_column_positions(text_rows)
        
        if len(column_positions) < 2:
            return None
        
        # Create table structure
        rows = len(text_rows)
        cols = len(column_positions) - 1
        
        cells = []
        for r, row_data in enumerate(text_rows):
            cell_row = []
            for c in range(cols):
                # Find text in this cell
                cell_text = self._extract_cell_text_from_row(
                    row_data, column_positions[c], column_positions[c + 1]
                )
                
                cell_info = CellInfo(
                    row=r,
                    col=c,
                    text=cell_text,
                    bbox=(column_positions[c], row_data['y_min'], 
                          column_positions[c + 1], row_data['y_max']),
                    confidence=0.8,
                    is_header=(r == 0)
                )
                cell_row.append(cell_info)
            cells.append(cell_row)
        
        return TableStructure(
            rows=rows,
            cols=cols,
            cells=cells,
            headers=[cell.text for cell in cells[0]] if cells else [],
            table_type="unknown"
        )
    
    def _extract_line_coordinates(self, line_image: np.ndarray, direction: str) -> List[int]:
        """Extract line coordinates from morphological operation result"""
        
        # Find contours of lines
        contours, _ = cv2.findContours(line_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        coordinates = []
        for contour in contours:
            if cv2.contourArea(contour) > 100:  # Filter small noise
                x, y, w, h = cv2.boundingRect(contour)
                
                if direction == 'horizontal':
                    coordinates.append(y)
                else:  # vertical
                    coordinates.append(x)
        
        return sorted(list(set(coordinates)))
    
    def _organize_contours_to_grid(self, contours: List[Tuple]) -> Optional[TableStructure]:
        """Organize contours into a grid structure"""
        
        # Sort contours by position
        sorted_contours = sorted(contours, key=lambda c: (c[1], c[0]))  # Sort by y, then x
        
        # Group by rows (similar y-coordinates)
        rows = []
        current_row = []
        current_y = sorted_contours[0][1]
        y_threshold = 20
        
        for x, y, w, h in sorted_contours:
            if abs(y - current_y) < y_threshold:
                current_row.append((x, y, w, h))
            else:
                if current_row:
                    rows.append(sorted(current_row, key=lambda c: c[0]))  # Sort by x
                current_row = [(x, y, w, h)]
                current_y = y
        
        if current_row:
            rows.append(sorted(current_row, key=lambda c: c[0]))
        
        # Check if we have a valid grid
        if len(rows) < 2:
            return None
        
        cols = len(rows[0])
        if not all(len(row) == cols for row in rows):
            return None  # Irregular grid
        
        # Create cell structure
        cells = []
        for r, row in enumerate(rows):
            cell_row = []
            for c, (x, y, w, h) in enumerate(row):
                cell_info = CellInfo(
                    row=r,
                    col=c,
                    text="",  # Will be filled later
                    bbox=(x, y, x + w, y + h),
                    confidence=0.8,
                    is_header=(r == 0)
                )
                cell_row.append(cell_info)
            cells.append(cell_row)
        
        return TableStructure(
            rows=len(rows),
            cols=cols,
            cells=cells,
            headers=[],
            table_type="unknown"
        )
    
    def _group_text_by_rows(self, ocr_data: Dict) -> List[Dict]:
        """Group OCR text data by rows"""
        
        # Extract valid text elements
        text_elements = []
        for i in range(len(ocr_data['text'])):
            text = ocr_data['text'][i].strip()
            if text and int(ocr_data['conf'][i]) > 30:
                text_elements.append({
                    'text': text,
                    'x': ocr_data['left'][i],
                    'y': ocr_data['top'][i],
                    'w': ocr_data['width'][i],
                    'h': ocr_data['height'][i],
                    'conf': ocr_data['conf'][i]
                })
        
        # Group by rows (similar y-coordinates)
        y_threshold = 15
        rows = []
        
        # Sort by y-coordinate
        text_elements.sort(key=lambda x: x['y'])
        
        current_row = []
        current_y = text_elements[0]['y'] if text_elements else 0
        
        for element in text_elements:
            if abs(element['y'] - current_y) < y_threshold:
                current_row.append(element)
            else:
                if current_row:
                    rows.append({
                        'elements': sorted(current_row, key=lambda x: x['x']),
                        'y_min': min(e['y'] for e in current_row),
                        'y_max': max(e['y'] + e['h'] for e in current_row)
                    })
                current_row = [element]
                current_y = element['y']
        
        if current_row:
            rows.append({
                'elements': sorted(current_row, key=lambda x: x['x']),
                'y_min': min(e['y'] for e in current_row),
                'y_max': max(e['y'] + e['h'] for e in current_row)
            })
        
        return rows
    
    def _detect_column_positions(self, text_rows: List[Dict]) -> List[int]:
        """Detect column positions from text rows"""
        
        # Collect all x-coordinates
        all_x_coords = []
        for row in text_rows:
            for element in row['elements']:
                all_x_coords.append(element['x'])
                all_x_coords.append(element['x'] + element['w'])
        
        # Cluster x-coordinates to find column boundaries
        all_x_coords = sorted(list(set(all_x_coords)))
        
        # Simple clustering: group coordinates that are close together
        column_positions = []
        threshold = 20
        
        if all_x_coords:
            column_positions.append(all_x_coords[0])
            
            for x in all_x_coords[1:]:
                if x - column_positions[-1] > threshold:
                    column_positions.append(x)
        
        return column_positions
    
    def _extract_cell_text_from_row(self, row_data: Dict, x_start: int, x_end: int) -> str:
        """Extract text from a cell defined by x-coordinates"""
        
        cell_texts = []
        for element in row_data['elements']:
            element_center = element['x'] + element['w'] / 2
            if x_start <= element_center < x_end:
                cell_texts.append(element['text'])
        
        return ' '.join(cell_texts)
    
    def _merge_detection_results(self, *structures) -> Optional[TableStructure]:
        """Merge results from different detection methods"""
        
        valid_structures = [s for s in structures if s is not None]
        
        if not valid_structures:
            return None
        
        # Choose the structure with the most cells
        best_structure = max(valid_structures, key=lambda s: s.rows * s.cols)
        
        return best_structure
    
    def _extract_cell_contents(self, image: np.ndarray, structure: TableStructure):
        """Extract text content from each cell"""
        
        for row in structure.cells:
            for cell in row:
                # Extract cell region
                x1, y1, x2, y2 = cell.bbox
                cell_image = image[int(y1):int(y2), int(x1):int(x2)]
                
                if cell_image.size > 0:
                    # Extract text from cell
                    try:
                        cell_text = pytesseract.image_to_string(
                            cell_image, 
                            lang='ben+eng',
                            config='--psm 8'  # Single word mode
                        ).strip()
                        
                        cell.text = cell_text
                        
                        # Update confidence based on text extraction
                        if cell_text:
                            cell.confidence = min(cell.confidence + 0.1, 1.0)
                        else:
                            cell.confidence = max(cell.confidence - 0.2, 0.1)
                            
                    except Exception as e:
                        print(f"Warning: Cell text extraction failed: {e}")
                        cell.text = ""
                        cell.confidence = 0.1
        
        # Update headers
        if structure.cells:
            structure.headers = [cell.text for cell in structure.cells[0]]
    
    def _classify_table(self, structure: TableStructure) -> str:
        """Classify table type based on content"""
        
        # Extract all text from table
        all_text = []
        for row in structure.cells:
            for cell in row:
                if cell.text:
                    all_text.append(cell.text.lower())
        
        text_content = ' '.join(all_text)
        
        # Check against patterns
        for table_type, patterns in self.table_patterns.items():
            if any(pattern.lower() in text_content for pattern in patterns):
                return table_type
        
        return 'general'


class MathFormulaExtractor:
    """Extract and convert mathematical formulas"""
    
    def __init__(self):
        self.math_symbols = {
            '+': 'plus',
            '-': 'minus', 
            '×': 'multiply',
            '÷': 'divide',
            '=': 'equals',
            '<': 'less_than',
            '>': 'greater_than',
            '≤': 'less_equal',
            '≥': 'greater_equal',
            '≠': 'not_equal',
            '%': 'percent',
            '√': 'sqrt',
            '∑': 'sum',
            '∏': 'product',
            '∫': 'integral'
        }
        
        self.formula_patterns = [
            r'[A-Za-z0-9\s]*[+\-×÷=<>≤≥≠%√∑∏∫][A-Za-z0-9\s]*',
            r'\([^)]+\)\s*[+\-×÷=]\s*\([^)]+\)',
            r'\d+\s*[+\-×÷]\s*\d+\s*=\s*\d+',
            r'[A-Z]\s*=\s*[^=]+',
            r'√\d+',
            r'\d+%'
        ]
    
    def detect_formulas(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect mathematical formulas in image"""
        
        # Extract text with high precision
        text = pytesseract.image_to_string(image, lang='eng', config='--psm 6')
        
        formulas = []
        
        # Check each pattern
        for pattern in self.formula_patterns:
            matches = re.finditer(pattern, text)
            
            for match in matches:
                formula_text = match.group().strip()
                
                if self._is_valid_formula(formula_text):
                    latex_form = self._convert_to_latex(formula_text)
                    variables = self._extract_variables(formula_text)
                    
                    formulas.append({
                        'text': formula_text,
                        'latex': latex_form,
                        'variables': variables,
                        'position': match.span(),
                        'confidence': self._calculate_formula_confidence(formula_text)
                    })
        
        return formulas
    
    def _is_valid_formula(self, text: str) -> bool:
        """Check if text represents a valid mathematical formula"""
        
        # Must contain at least one math symbol
        if not any(symbol in text for symbol in self.math_symbols.keys()):
            return False
        
        # Should contain numbers or variables
        if not re.search(r'[A-Za-z0-9]', text):
            return False
        
        # Basic validation checks
        if len(text.strip()) < 3:
            return False
        
        return True
    
    def _convert_to_latex(self, formula_text: str) -> str:
        """Convert formula text to LaTeX format"""
        
        latex = formula_text
        
        # Replace symbols
        replacements = {
            '×': r' \times ',
            '÷': r' \div ',
            '≤': r' \leq ',
            '≥': r' \geq ',
            '≠': r' \neq ',
            '√': r'\sqrt{',
            '∑': r'\sum',
            '∏': r'\prod',
            '∫': r'\int'
        }
        
        for symbol, latex_symbol in replacements.items():
            latex = latex.replace(symbol, latex_symbol)
        
        # Handle square roots
        if r'\sqrt{' in latex:
            # Simple handling - assume next number/variable is under sqrt
            latex = re.sub(r'\\sqrt\{(\w+)', r'\\sqrt{\1}', latex)
        
        # Wrap in math mode
        latex = f'${latex}$'
        
        return latex
    
    def _extract_variables(self, formula_text: str) -> List[str]:
        """Extract variables from formula"""
        
        # Find single letters that could be variables
        variables = re.findall(r'\b[A-Za-z]\b', formula_text)
        
        # Remove common words
        common_words = {'a', 'an', 'is', 'or', 'if', 'of', 'to', 'in'}
        variables = [v for v in variables if v.lower() not in common_words]
        
        return list(set(variables))
    
    def _calculate_formula_confidence(self, formula_text: str) -> float:
        """Calculate confidence score for formula detection"""
        
        confidence = 0.5  # Base confidence
        
        # Boost for mathematical symbols
        symbol_count = sum(1 for symbol in self.math_symbols.keys() if symbol in formula_text)
        confidence += symbol_count * 0.1
        
        # Boost for numbers
        number_count = len(re.findall(r'\d+', formula_text))
        confidence += number_count * 0.05
        
        # Boost for parentheses (indicates structure)
        paren_count = formula_text.count('(') + formula_text.count(')')
        confidence += paren_count * 0.05
        
        return min(confidence, 1.0)


class FormExtractor:
    """Extract form structures and fields"""
    
    def __init__(self):
        self.field_patterns = [
            r'(.+?):\s*_+',  # Label: ______
            r'(.+?)\s*\[\s*\]',  # Label [ ]
            r'(.+?)\s*\(\s*\)',  # Label ( )
            r'নাম\s*[:：]\s*',  # Name in Bengali
            r'Name\s*[:：]\s*',  # Name in English
            r'ঠিকানা\s*[:：]\s*',  # Address in Bengali
            r'Address\s*[:：]\s*'  # Address in English
        ]
        
        self.form_indicators = [
            'আবেদন', 'Application', 'ফর্ম', 'Form',
            'নিবন্ধন', 'Registration', 'ঘোষণা', 'Declaration'
        ]
    
    def detect_forms(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect forms and extract field information"""
        
        # Extract text with positioning
        data = pytesseract.image_to_data(image, lang='ben+eng', output_type=pytesseract.Output.DICT)
        
        # Check if this looks like a form
        all_text = ' '.join([data['text'][i] for i in range(len(data['text'])) 
                            if int(data['conf'][i]) > 30])
        
        is_form = any(indicator in all_text for indicator in self.form_indicators)
        
        if not is_form:
            return []
        
        # Extract fields
        fields = []
        
        for pattern in self.field_patterns:
            matches = re.finditer(pattern, all_text, re.IGNORECASE)
            
            for match in matches:
                field_label = match.group(1).strip()
                
                fields.append({
                    'label': field_label,
                    'value': '',  # Empty for forms to be filled
                    'type': self._classify_field_type(field_label),
                    'required': self._is_required_field(field_label),
                    'position': match.span()
                })
        
        return [{
            'form_type': self._classify_form_type(all_text),
            'fields': fields,
            'total_fields': len(fields)
        }] if fields else []
    
    def _classify_field_type(self, label: str) -> str:
        """Classify field type based on label"""
        
        label_lower = label.lower()
        
        if any(word in label_lower for word in ['name', 'নাম']):
            return 'text'
        elif any(word in label_lower for word in ['address', 'ঠিকানা']):
            return 'address'
        elif any(word in label_lower for word in ['phone', 'mobile', 'ফোন']):
            return 'phone'
        elif any(word in label_lower for word in ['email', 'ইমেইল']):
            return 'email'
        elif any(word in label_lower for word in ['date', 'তারিখ']):
            return 'date'
        elif any(word in label_lower for word in ['amount', 'টাকা', 'money']):
            return 'currency'
        else:
            return 'text'
    
    def _is_required_field(self, label: str) -> bool:
        """Determine if field is required"""
        
        required_indicators = ['*', 'required', 'বাধ্যতামূলক', 'আবশ্যক']
        return any(indicator in label.lower() for indicator in required_indicators)
    
    def _classify_form_type(self, text: str) -> str:
        """Classify the type of form"""
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['আবেদন', 'application']):
            return 'application'
        elif any(word in text_lower for word in ['নিবন্ধন', 'registration']):
            return 'registration'
        elif any(word in text_lower for word in ['ঘোষণা', 'declaration']):
            return 'declaration'
        elif any(word in text_lower for word in ['প্রত্যয়ন', 'certificate']):
            return 'certificate'
        else:
            return 'general'


def main():
    """Test the advanced extractors"""
    print("🧪 Testing Advanced Extractors...")
    
    # Test with sample image
    test_image_path = "test_sample.png"
    
    if Path(test_image_path).exists():
        image = cv2.imread(test_image_path)
        
        # Test table extractor
        print("📊 Testing Table Extractor...")
        table_extractor = AdvancedTableExtractor()
        table_structure = table_extractor.detect_table_structure(image)
        
        if table_structure:
            print(f"✅ Table detected: {table_structure.rows}x{table_structure.cols}")
            print(f"   Type: {table_structure.table_type}")
            print(f"   Headers: {table_structure.headers}")
        else:
            print("❌ No table detected")
        
        # Test math extractor
        print("\n🔢 Testing Math Extractor...")
        math_extractor = MathFormulaExtractor()
        formulas = math_extractor.detect_formulas(image)
        
        print(f"✅ Found {len(formulas)} mathematical formulas")
        for formula in formulas[:3]:  # Show first 3
            print(f"   Formula: {formula['text']}")
            print(f"   LaTeX: {formula['latex']}")
        
        # Test form extractor
        print("\n📝 Testing Form Extractor...")
        form_extractor = FormExtractor()
        forms = form_extractor.detect_forms(image)
        
        print(f"✅ Found {len(forms)} forms")
        for form in forms:
            print(f"   Type: {form['form_type']}")
            print(f"   Fields: {form['total_fields']}")
    
    else:
        print(f"❌ Test image not found: {test_image_path}")
        print("Please ensure test image exists for testing")

if __name__ == "__main__":
    main()