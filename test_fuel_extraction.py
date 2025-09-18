#!/usr/bin/env python3
"""
Test script for improved fuel table extraction
Tests the enhanced fuel processing capabilities on sample images
"""

import os
import sys
import json
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from gemini_processor import GeminiDriverPacketProcessor
except ImportError as e:
    print(f"❌ Could not import GeminiDriverPacketProcessor: {e}")
    print("Make sure you have the required dependencies installed and GEMINI_API_KEY set")
    sys.exit(1)

def test_fuel_extraction(image_path):
    """Test fuel extraction on a specific image"""
    
    print(f"🧪 Testing fuel extraction on: {os.path.basename(image_path)}")
    print("=" * 60)
    
    try:
        # Initialize processor
        processor = GeminiDriverPacketProcessor()
        
        # Process image
        print("📝 Processing image...")
        result = processor.process_image_with_coordinates(image_path, use_here_api=False)
        
        if not result.get('processing_success'):
            print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
            return False
        
        # Display basic info
        print("\n📋 Basic Information:")
        print(f"   Driver: {result.get('drivers_name', 'N/A')}")
        print(f"   Unit: {result.get('unit', 'N/A')}")
        print(f"   Trailer: {result.get('trailer', 'N/A')}")
        
        # Focus on fuel details
        fuel_details = result.get('fuel_details', [])
        
        if not fuel_details:
            print("\n❌ No fuel details found in extraction")
            return False
        
        print(f"\n⛽ Fuel Details Found: {len(fuel_details)} rows")
        print("-" * 50)
        
        # Display simplified fuel data and calculate totals
        state_totals = {}
        total_gallons = 0
        
        for i, fuel_row in enumerate(fuel_details, 1):
            state = fuel_row.get('state', 'N/A')
            gallons = fuel_row.get('gallons', 0)
            
            print(f"\nRow {i}:")
            print(f"   State: {state}")
            print(f"   Gallons: {gallons}")
            
            # Calculate state totals
            if state != 'N/A':
                try:
                    gallons_float = float(gallons) if gallons else 0
                    state_totals[state] = state_totals.get(state, 0) + gallons_float
                    total_gallons += gallons_float
                except (ValueError, TypeError):
                    print(f"   ⚠️ Warning: Invalid gallons value: {gallons}")
        
        # Display state summary
        print(f"\n📊 State Fuel Summary:")
        print("-" * 30)
        for state, gallons in sorted(state_totals.items()):
            print(f"   {state}: {gallons:.3f} gallons")
        print(f"\n   Total: {total_gallons:.3f} gallons")
        
        # Display validation warnings if any
        warnings = result.get('validation_warnings', [])
        if warnings:
            print(f"\n⚠️ Validation Warnings ({len(warnings)}):")
            for warning in warnings:
                print(f"   - {warning}")
        
        print(f"\n✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🚛 Fuel Table Extraction Test")
    print("Testing improved fuel processing capabilities")
    print("=" * 60)
    
    # Check for sample image
    sample_image = "input/1Q 2024 Trip Envelope Jalf Express 04.02.2024_Page_3_Image_0001.jpg"
    
    if not os.path.exists(sample_image):
        print(f"❌ Sample image not found: {sample_image}")
        print("Please ensure the test image is available in the input folder")
        return
    
    # Test the extraction
    success = test_fuel_extraction(sample_image)
    
    if success:
        print("\n🎉 All tests passed!")
        print("\nThe improved fuel extraction system includes:")
        print("✅ Enhanced Gemini prompt for better accuracy")
        print("✅ Comprehensive fuel data validation")
        print("✅ Proper handling of DEF rows and date inheritance")
        print("✅ Improved state extraction from City&State column")
        print("✅ Better error handling and correction logic")
        print("✅ Enhanced Excel output with 'Gallon Trip Env' sheet")
    else:
        print("\n❌ Tests failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
