#!/usr/bin/env python3
"""
Simple test script for bbocr project
"""

import cv2
import numpy as np
from pathlib import Path

def test_basic_imports():
    """Test if the basic imports work"""
    print("Testing basic imports...")
    try:
        from bbocr import ApsisNet, PaddleDBNet
        print("✓ Successfully imported ApsisNet and PaddleDBNet")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_module_initialization():
    """Test if modules can be initialized (without models)"""
    print("\nTesting module initialization...")
    try:
        from bbocr.modules.yolodla import YoloDLA
        from bbocr.modules.apsisnet import ApsisNet
        from bbocr.modules.paddledbnet import PaddleDBNet
        
        print("✓ Successfully imported individual modules")
        
        # Test if classes can be inspected without initialization
        print(f"✓ YoloDLA class available with methods: {[m for m in dir(YoloDLA) if not m.startswith('_')]}")
        print(f"✓ ApsisNet class available with methods: {[m for m in dir(ApsisNet) if not m.startswith('_')]}")
        print(f"✓ PaddleDBNet class available with methods: {[m for m in dir(PaddleDBNet) if not m.startswith('_')]}")
        
        return True
    except Exception as e:
        print(f"✗ Module initialization test failed: {e}")
        return False

def test_image_processing_utils():
    """Test image processing utilities"""
    print("\nTesting image processing utilities...")
    try:
        from bbocr.modules.apsisnet import padWordImage, correctPadding
        
        # Create a test image
        test_img = np.ones((50, 100, 3), dtype=np.uint8) * 255
        
        # Test padding
        padded_img = padWordImage(test_img, "lr", 150, 255)
        print(f"✓ padWordImage works - original: {test_img.shape}, padded: {padded_img.shape}")
        
        # Test correct padding
        corrected_img, mask = correctPadding(test_img, (32, 256))
        print(f"✓ correctPadding works - result shape: {corrected_img.shape}, mask: {mask}")
        
        return True
    except Exception as e:
        print(f"✗ Image processing utils test failed: {e}")
        return False

def create_sample_image():
    """Create a sample image for testing"""
    print("\nCreating sample test image...")
    
    # Create a simple image with text-like rectangles
    img = np.ones((300, 400, 3), dtype=np.uint8) * 255
    
    # Add some rectangles to simulate text regions
    cv2.rectangle(img, (50, 50), (350, 100), (0, 0, 0), 2)
    cv2.rectangle(img, (50, 120), (350, 170), (0, 0, 0), 2)
    cv2.rectangle(img, (50, 190), (350, 240), (0, 0, 0), 2)
    
    # Add some text
    cv2.putText(img, "Sample Bengali Text Region 1", (60, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    cv2.putText(img, "Sample Bengali Text Region 2", (60, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    cv2.putText(img, "Sample Bengali Text Region 3", (60, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    
    # Save the test image
    test_img_path = "test_sample.png"
    cv2.imwrite(test_img_path, img)
    print(f"✓ Created sample image: {test_img_path}")
    
    return test_img_path

def test_dependencies():
    """Test if all required dependencies are available"""
    print("\nTesting dependencies...")
    dependencies = [
        'cv2', 'numpy', 'onnxruntime', 'bnunicodenormalizer', 
        'gdown', 'matplotlib', 'pandas', 'tqdm'
    ]
    
    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✓ {dep} is available")
        except ImportError:
            print(f"✗ {dep} is missing")
            missing.append(dep)
    
    if missing:
        print(f"\nMissing dependencies: {missing}")
        return False
    else:
        print("✓ All dependencies are available")
        return True

def main():
    """Run all tests"""
    print("=" * 50)
    print("BBOCR Project Test Suite")
    print("=" * 50)
    
    tests = [
        test_dependencies,
        test_basic_imports,
        test_module_initialization,
        test_image_processing_utils,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    # Create sample image
    sample_img = create_sample_image()
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The bbocr project is ready to use.")
        print(f"📸 Sample image created: {sample_img}")
        print("\nNext steps:")
        print("1. Download required model weights (YOLO for layout, ONNX for recognition)")
        print("2. Set up proper paths in pipeline configuration")
        print("3. Run the full OCR pipeline on your images")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)