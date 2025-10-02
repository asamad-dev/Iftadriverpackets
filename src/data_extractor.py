#!/usr/bin/env python3
"""
Core data extraction module using Gemini API
Handles OCR and intelligent data extraction from driver packet images
"""

import os
import json
import time
from typing import Dict, Optional
from PIL import Image
import google.generativeai as genai

from .logging_utils import get_logger
from .config import config


class GeminiDataExtractor:
    """
    Extract data from driver packet images using Google's Gemini multimodal AI
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini data extractor
        
        Args:
            api_key: Gemini API key (if not provided, will use config.GEMINI_API_KEY)
        """
        self.logger = get_logger()
        
        # Configure Gemini API
        if api_key:
            genai.configure(api_key=api_key)
        else:
            api_key = config.GEMINI_API_KEY
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in configuration. Please set it in .env file or pass it directly.")
            genai.configure(api_key=api_key)
        
        # Initialize the model using configuration with fallback
        self.model = self._initialize_model_with_fallback()
        
        # Define the extraction prompt
        self.extraction_prompt = self._build_extraction_prompt()
    
    def _initialize_model_with_fallback(self):
        """Initialize Gemini model with automatic fallback to working alternatives"""
        # Try models in order of preference
        model_candidates = [
            config.GEMINI_MODEL,           # User's configured model
            'gemini-1.5-pro',              # Stable pro model
            'gemini-1.5-flash-latest',     # Latest flash model
            'gemini-2.5-flash',            # Newer version
            'gemini-flash-latest',         # Generic latest
            'gemini-pro-latest',           # Generic pro latest
            'gemini-1.5-flash',            # Original flash model
            'gemini-pro-vision',           # Vision capable
            'gemini-pro'                   # Basic pro
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_models = []
        for model in model_candidates:
            if model not in seen:
                seen.add(model)
                unique_models.append(model)
        
        last_error = None
        for model_name in unique_models:
            try:
                self.logger.info(f"Trying Gemini model: {model_name}")
                model = genai.GenerativeModel(model_name)
                
                # Test the model with a simple request to ensure it works
                test_response = model.generate_content("Test")
                if test_response and test_response.text:
                    self.logger.info(f"✅ Successfully initialized Gemini model: {model_name}")
                    if model_name != config.GEMINI_MODEL:
                        self.logger.warning(f"⚠️  Using fallback model '{model_name}' instead of configured '{config.GEMINI_MODEL}'")
                    return model
                else:
                    self.logger.warning(f"Model {model_name} initialized but failed test generation")
                    
            except Exception as e:
                last_error = e
                self.logger.warning(f"Failed to initialize model '{model_name}': {e}")
                continue
        
        # If all models failed, raise the last error
        raise ValueError(f"Failed to initialize any Gemini model. Last error: {last_error}")
    
    def _build_extraction_prompt(self) -> str:
        """Build the comprehensive extraction prompt for Gemini"""
        return """
You are an expert at extracting data from handwritten driver trip sheets. 
Analyze this ASF Carrier Inc driver packet image and extract ONLY the information that is CLEARLY VISIBLE.

FORM's FIELD LOCATIONS AND FORMAT GUIDELINES:
- Driver's Name (Row 1)
- Unit # (Row 1)
- Trailer # (Row 1)
- Date Trip Started (Row 2) (below Driver's Name)
- Date Trip Ended (Row 2)
- Trip # (Row 2)
- Trip Started From (Row 3) (below Date Trip Started)
- 1st. Drop (Row 3) (below Date Trip Ended)
- 2nd. Drop (Row 3) (below Trip #)
- 3rd. Drop (Row 4) (below Trip Started From)
- 4th. Drop (Row 4) (below 1st. Drop)
- Inbound PU (Row 5) (below 3rd. Drop)
- Drop Off (Row 5) - CAN HAVE MULTIPLE VALUES separated by "to" keyword
- Total Miles (Under "OFFICE USE ONLY" section at the bottom)

TRAILER NUMBER VALIDATION:
- Trailer numbers are ALWAYS between 200-299 (hundreds digit must be 2)
- If you detect a trailer number with hundreds digit other than 2, change it to 2
- Example: "786" should be "286", "711" should be "211", etc.

LOCATION FORMAT AND CORRECTIONS:
- Format for "Trip Started From", "1st. Drop", "2nd. Drop", "3rd. Drop", "4th. Drop", "Inbound PU" and "Drop Off" must be "City, State" 
- Example: "Bloomington, TX" (Full City name and State abbreviation)
- Always include the comma between city and state

CRITICAL LOCATION CORRECTIONS:
- "Bloomington" (any state) → Always "Bloomington, CA"
- "Yard" or "yard" → Always "San Bernardino, CA"
- "Jaredo" → "Laredo"
- "Corona" → "Fontana"
- "FFA/ON" → "FULTON"
- "MONON" → "MONONGAH"
- "Jaredotx" → "Laredo, TX"
- Apply intelligent spelling corrections for city names

DATE FORMAT STANDARDIZATION:
- ALL dates must be in MM/DD/YY format
- Convert these formats to MM/DD/YY:
  - 11.29.2022 → 11/29/22
  - 11-28-2022 → 11/28/22
  - 12-09-23 → 12/09/23
  - 12/25/2022 → 12/25/22
- Keep only 2-digit year format

FIELD VALIDATION RULES:
- second_drop, third_drop and forth_drop are OPTIONAL fields - leave empty if not clearly visible
- DO NOT copy values from inbound_pu or drop_off into second_drop, third_drop or forth_drop
- inbound_pu and drop_off should ALWAYS have values if visible
- If second_drop, third_drop or forth_drop appear to have the same value as inbound_pu, leave them empty
- If the trip starts and ends at the SAME city/state, DO NOT place that same city/state in any middle drop; leave that middle drop empty

DROP OFF ARRAY HANDLING:
- drop_off can have multiple values separated by "to"
- If single value: return as single string
- If multiple values: split by "to" and return as array
- Example: "Ontario, CA to San Bernardino, CA" → ["Ontario, CA", "San Bernardino, CA"]

TOTAL MILES EXTRACTION:
- Look carefully in the "OFFICE USE ONLY" section at the bottom of the form
- Total miles should be a reasonable number (typically 1000-6000 for long trips)
- If extracted number seems unreasonable (too high like 23513 or too low like 220), double-check the image
- Extract the number exactly as written

FUEL DETAILS TABLE EXTRACTION:
- Look for a table with the heading "FUEL DETAILS" on the form
- Extract fuel purchase information with these column mappings:
  1. "Data/Invoice" or "Data/ Invoice" - Date column (not needed for extraction)
  2. "Vendor" - Ignore this column
  3. "City&State" or "City & State" - Extract state abbreviation (2 letters)
  4. "# Gal." - Extract gallons quantity (must be very accurate)
  5. "Price" - Ignore this column
  6. "Amount" - Ignore this column  
  7. "CashAdv." or "Cash Adv." - Ignore this column

FUEL TABLE EXTRACTION RULES:
- If "Data/Invoice" shows "DEF", use the date from the row above
- For state extraction from "City&State":
  * Usually contains state abbreviations (TX, CA, NV, etc.)
  * Sometimes full state names - convert to 2-letter abbreviations
  * If state unclear, infer from city name or adjacent rows
  * If "DEF" appears in other columns and no city/state shown, use state from row above
- For gallons ("# Gal."), be EXTREMELY accurate with number reading
- Extract each row as separate fuel purchase
- Group and sum gallons by state

IMPORTANT: Return ONLY a valid JSON object with these exact field names:
{
    "drivers_name": "driver's full name - EXACTLY as written, apply common sense spelling corrections",
    "unit": "unit number - only if clearly visible", 
    "trailer": "trailer number - MUST be 2XX format (200-299)",
    "date_trip_started": "trip start date - MM/DD/YY format",
    "date_trip_ended": "trip end date - MM/DD/YY format", 
    "trip": "trip number or ID - ONLY if explicitly written and visible, do NOT guess",
    "trip_started_from": "origin city name and state abbreviation with comma (e.g., Bloomington, CA)",
    "first_drop": "first drop city name and state abbreviation with comma (e.g., San Bernardino, CA)",
    "second_drop": "second drop city name and state abbreviation with comma (e.g., San Bernardino, CA)", 
    "third_drop": "third drop city name and state abbreviation with comma - OPTIONAL, leave empty if not clearly visible",
    "forth_drop": "fourth drop city name and state abbreviation with comma - OPTIONAL, leave empty if not clearly visible",
    "inbound_pu": "inbound pickup city name and state abbreviation with comma (e.g., San Bernardino, CA)",
    "drop_off": "final drop off - can be string or array if multiple values separated by 'to'",
    "total_miles": "total miles driven from OFFICE USE ONLY section - extract carefully",
    "fuel_purchases": [
        {
            "state": "2-letter state abbreviation where fuel was purchased",
            "gallons": "precise number of gallons purchased"
        }
    ]
}

CRITICAL RULES:
1. DO NOT HALLUCINATE OR GUESS any information
2. If a field is not clearly visible or readable, use empty string ""
3. DO NOT copy values from one field to another - each field must be extracted independently
4. If you see an empty line or box on the form, that field should be empty string ""
5. DO NOT swap field values - pay careful attention to field positioning on the form
6. Apply trailer number validation (200-299 range)
7. Apply location corrections (Bloomington→CA, Yard→San Bernardino, etc.)
8. Apply date format standardization (MM/DD/YY)
9. Handle drop_off as potential array
10. Extract total_miles carefully from OFFICE USE ONLY section

SPELLING AND LOCATION GUIDELINES:
- For city and state names use standard spellings. there is a chance of wrong spelling due to handwritten text.
- Use standard state abbreviations: TX, CA, FL, GA, AR, AZ, NC, PA, OK, LA, etc.
- Capitalize city names properly: "dallas" → "Dallas", "phoenix" → "Phoenix"
- Read handwritten text letter by letter carefully
- When unsure about spelling, prefer the most phonetically similar common spelling

NAME ACCURACY GUIDELINES:
- Read names letter by letter carefully from the handwritten text.
- Look for standard First Name + Last Name patterns in CAPITAL letters.
- If name appears incomplete or unclear, extract what is clearly visible
- Do not guess missing letters - leave partial if necessary
- Apply common sense spelling corrections for clearly misread letters (e.g., 'O' vs '0', 'I' vs '1')

FIELD POSITIONING RULES (CRITICAL FOR ACCURACY):
- Look at the EXACT position of each field on the form
- Do NOT assume field order - read labels carefully
- "Drop" fields typically appear in sequence: 1st Drop, 2nd Drop, 3rd Drop, 4th Drop
- "Inbound PU" (pickup) is usually separate from drop locations
- If a field line is empty or has no text, that field should be empty string ""
- Do NOT fill empty fields with data from other fields

DATA VALIDATION FINAL CHECK:
- Only extract data that is 100% visible and readable
- Apply intelligent spell checking to names and locations
- When in doubt about spelling, use the most common/standard spelling
- Verify numbers are actually numbers, not similar-looking letters
- Do NOT fabricate trip numbers - they must be clearly written
- NEVER copy a value from one field to fill another empty field
- NEVER assume field content based on other fields
- If a field line is blank or empty, the JSON value MUST be empty string ""
- Double-check field labels to avoid assigning values to wrong fields
- Validate trailer numbers are in 200-299 range
- Apply location corrections and date format standardization

Return ONLY the JSON object, no additional text or explanation.

Analyze the image carefully and extract all CLEARLY VISIBLE information with intelligent validation:
"""
    
    def extract_data(self, image_path: str) -> Dict:
        """
        Extract data from a driver packet image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with extracted data or error information
        """
        try:
            self.logger.info(f"Starting data extraction from: {os.path.basename(image_path)}")
            
            # Check if file exists
            if not os.path.isfile(image_path):
                return {
                    'extraction_success': False,
                    'error': f"File not found: {image_path}",
                    'source_image': os.path.basename(image_path)
                }
            
            # Load image with proper resource management
            try:
                with Image.open(image_path) as img:
                    self.logger.info(f"Image loaded: {img.size}")
                    
                    # # Convert to RGB if necessary (some formats need this)
                    # if img.mode != 'RGB':
                    #     img = img.convert('RGB')
                    
                    # Generate content using Gemini
                    try:
                        self.logger.info("Sending image to Gemini API...")
                        response = self.model.generate_content([self.extraction_prompt, img])
                        extracted_text = response.text
                        self.logger.info("✅ Received response from Gemini API")
                        
                        # Image is automatically closed when exiting the 'with' block
                        
                    except Exception as e:
                        self.logger.error(f"Gemini API error: {e}")
                        return {
                            'extraction_success': False,
                            'error': f"Gemini API error: {e}",
                            'source_image': os.path.basename(image_path)
                        }
                        
            except Exception as e:
                return {
                    'extraction_success': False,
                    'error': f"Error loading image: {e}",
                    'source_image': os.path.basename(image_path)
                }
            
            # Parse JSON response
            try:
                # Clean up response text
                if '```json' in extracted_text:
                    extracted_text = extracted_text.split('```json')[1]
                if '```' in extracted_text:
                    extracted_text = extracted_text.split('```')[0]
                
                extracted_data = json.loads(extracted_text.strip())
                
                # Return raw extracted data with basic metadata
                result = {
                    'extraction_success': True,
                    'extraction_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'source_image': os.path.basename(image_path),
                    **extracted_data
                }
                
                self.logger.info(f"Successfully extracted data from {os.path.basename(image_path)}")
                return result
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parsing error: {e}")
                return {
                    'extraction_success': False,
                    'error': f"JSON parsing error: {e}",
                    'source_image': os.path.basename(image_path),
                    'raw_response': extracted_text
                }
                
        except Exception as e:
            self.logger.error(f"Unexpected error in data extraction: {e}")
            return {
                'extraction_success': False,
                'error': f"Unexpected error: {e}",
                'source_image': os.path.basename(image_path)
            }
    
    
