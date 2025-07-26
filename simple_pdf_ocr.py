#!/usr/bin/env python3
"""
Simple PDF to OCR - Windows Compatible
Converts PDF to images and runs OCR with basic BBOCR functionality
"""

import os
import json
import cv2
import numpy as np
from pdf2image import convert_from_path
from pathlib import Path
import sys

# Add bbocr to path
sys.path.append(str(Path(__file__).parent))

def simple_pdf_to_images_ocr(pdf_path, output_dir="ocr_output"):
    """
    Simple function to convert PDF to images and run OCR
    """
    print(f"🚀 Starting PDF OCR: {pdf_path}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Convert PDF to images
        print("📄 Converting PDF to images...")
        images = convert_from_path(pdf_path, dpi=300)
        print(f"✅ Converted {len(images)} pages to images")
        
        # Process each page
        results = []
        
        for i, image in enumerate(images):
            print(f"🔄 Processing page {i+1}/{len(images)}...")
            
            # Convert PIL to OpenCV format
            img_array = np.array(image)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Save image temporarily
            temp_img_path = f"temp_page_{i+1}.png"
            cv2.imwrite(temp_img_path, img_bgr)
            
            # Try to use basic OCR (fallback if BBOCR doesn't work)
            try:
                # Try Tesseract as fallback
                import pytesseract
                
                # Use Tesseract with Bengali support
                custom_config = r'--oem 3 --psm 6 -l ben+eng'
                text = pytesseract.image_to_string(image, config=custom_config)
                
                results.append({
                    'page_number': i + 1,
                    'extracted_text': text.strip(),
                    'method': 'tesseract',
                    'image_path': temp_img_path
                })
                
                print(f"✅ Page {i+1} processed with Tesseract")
                
            except Exception as tesseract_error:
                print(f"⚠️ Tesseract failed for page {i+1}: {tesseract_error}")
                
                # Basic text extraction (very simple)
                results.append({
                    'page_number': i + 1,
                    'extracted_text': f"[Page {i+1} - OCR failed]",
                    'method': 'failed',
                    'image_path': temp_img_path,
                    'error': str(tesseract_error)
                })
            
            # Clean up temp file
            try:
                os.remove(temp_img_path)
            except:
                pass
        
        # Save results
        output_file = os.path.join(output_dir, "pdf_ocr_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n" + "="*60)
        print("🎉 PDF OCR COMPLETE")
        print("="*60)
        print(f"📄 Total Pages: {len(results)}")
        
        successful_pages = len([r for r in results if r['method'] != 'failed'])
        print(f"✅ Successfully Processed: {successful_pages}/{len(results)}")
        
        print(f"💾 Results saved to: {output_file}")
        
        # Show sample of first page
        if results and results[0]['extracted_text']:
            print(f"\n📝 Sample from Page 1:")
            sample_text = results[0]['extracted_text'][:200]
            print(f"   {sample_text}...")
        
        return results
        
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        return None


def main():
    """Main function"""
    pdf_path = "test_tax_documents/Finance_Act-2024.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        print("Available files:")
        if os.path.exists("test_tax_documents"):
            for f in os.listdir("test_tax_documents"):
                print(f"   - {f}")
        return
    
    # Run OCR
    results = simple_pdf_to_images_ocr(pdf_path)
    
    if results:
        print(f"\n🎯 Ready for processing! Check 'ocr_output/pdf_ocr_results.json'")
    else:
        print("❌ OCR failed")


if __name__ == "__main__":
    main()