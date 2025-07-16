#!/usr/bin/env python3
"""
Gemini API Processor for Driver Packet Extraction
Uses Google's Gemini multimodal AI for intelligent OCR and data extraction
"""

import os
import json
from typing import Dict, Optional, List, Tuple
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
import re
import requests
import time
import glob
import csv
from pathlib import Path

# Load environment variables from .env file (look in parent directory)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

class GeminiDriverPacketProcessor:
    """
    Process driver packet images using Gemini API with intelligent prompt engineering
    """
    
    def __init__(self, api_key: Optional[str] = None, here_api_key: Optional[str] = None):
        # Configure Gemini API
        if api_key:
            genai.configure(api_key=api_key)
        else:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            genai.configure(api_key=api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Configure HERE API key for geocoding
        self.here_api_key = here_api_key or os.getenv('HERE_API_KEY')
        
        # Geocoding cache to avoid repeated API calls
        self.geocoding_cache = {}
        
        self.extraction_prompt = """
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
- third_drop and forth_drop are OPTIONAL fields - leave empty if not clearly visible
- DO NOT copy values from inbound_pu or drop_off into third_drop or forth_drop
- inbound_pu and drop_off should ALWAYS have values if visible
- If third_drop or forth_drop appear to have the same value as inbound_pu, leave them empty

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
    "total_miles": "total miles driven from OFFICE USE ONLY section - extract carefully"
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
    
    def geocode_location_here(self, location: str) -> Optional[Tuple[float, float]]:
        """
        Get coordinates for a location using HERE Geocoding API
        
        Args:
            location: Location string (e.g., "Dallas, TX")
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        if not location or not location.strip():
            return None
            
        location = location.strip()
        
        # Check cache first
        if location in self.geocoding_cache:
            return self.geocoding_cache[location]
        
        if not self.here_api_key:
            print("⚠️  HERE API key not configured, skipping geocoding")
            return None
        
        try:
            # HERE Geocoding API endpoint
            url = "https://geocode.search.hereapi.com/v1/geocode"
            params = {
                'q': location,
                'apikey': self.here_api_key,
                'limit': 1
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('items') and len(data['items']) > 0:
                position = data['items'][0]['position']
                coords = (position['lat'], position['lng'])
                
                # Cache the result
                self.geocoding_cache[location] = coords
                
                return coords
            else:
                # Cache negative result to avoid repeated API calls
                self.geocoding_cache[location] = None
                return None
                
        except Exception as e:
            print(f"⚠️  Geocoding failed for '{location}': {e}")
            # Cache failure to avoid repeated attempts
            self.geocoding_cache[location] = None
            return None
    
    def geocode_location_nominatim(self, location: str) -> Optional[Tuple[float, float]]:
        """
        Get coordinates for a location using Nominatim (OpenStreetMap) - Free alternative
        
        Args:
            location: Location string (e.g., "Dallas, TX")
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        if not location or not location.strip():
            return None
            
        location = location.strip()
        
        # Check cache first
        if location in self.geocoding_cache:
            return self.geocoding_cache[location]
        
        try:
            # Nominatim API endpoint
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': location,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'us',  # Limit to US for truck routes
                'addressdetails': 1
            }
            
            headers = {
                'User-Agent': 'Driver-Packet-Processor/1.0'
            }
            
            # Rate limiting - Nominatim requires 1 request per second
            time.sleep(1)
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            if data and len(data) > 0:
                coords = (float(data[0]['lat']), float(data[0]['lon']))
                
                # Cache the result
                self.geocoding_cache[location] = coords
                
                return coords
            else:
                # Cache negative result
                self.geocoding_cache[location] = None
                return None
                
        except Exception as e:
            print(f"⚠️  Geocoding failed for '{location}': {e}")
            # Cache failure
            self.geocoding_cache[location] = None
            return None
    
    def get_coordinates_for_stops(self, extracted_data: Dict, use_here_api: bool = True) -> Dict:
        """
        Add coordinates for all stops in the extracted data
        
        Args:
            extracted_data: Dictionary with extracted trip data
            use_here_api: If True, use HERE API; if False, use Nominatim
            
        Returns:
            Dictionary with added coordinate information
        """
        # Location fields to geocode
        location_fields = [
            'trip_started_from',
            'first_drop', 
            'second_drop',
            'third_drop',
            'forth_drop',
            'inbound_pu',
            'drop_off'
        ]
        
        coordinates = {}
        geocoding_method = self.geocode_location_here if use_here_api else self.geocode_location_nominatim
        
        print("🌍 Getting coordinates for trip stops...")
        
        for field in location_fields:
            location = extracted_data.get(field, '')
            
            # Handle drop_off as array
            if field == 'drop_off' and isinstance(location, list):
                if location:
                    # Use the first drop-off location for geocoding
                    location = location[0]
                else:
                    location = ''
            
            if location and location.strip():
                print(f"   Geocoding {field}: {location}")
                coords = geocoding_method(location)
                if coords:
                    coordinates[field] = {
                        'location': location,
                        'latitude': coords[0],
                        'longitude': coords[1]
                    }
                    print(f"   ✅ Found: {coords[0]:.6f}, {coords[1]:.6f}")
                else:
                    coordinates[field] = {
                        'location': location,
                        'latitude': None,
                        'longitude': None,
                        'geocoding_failed': True
                    }
                    print(f"   ❌ Not found")
            else:
                # Empty location field
                coordinates[field] = {
                    'location': '',
                    'latitude': None,
                    'longitude': None
                }
        
        # Create result with coordinates
        result = coordinates
        
        # Add summary statistics
        successful_coords = sum(1 for coord in coordinates.values() 
                              if coord.get('latitude') is not None)
        total_locations = sum(1 for coord in coordinates.values() 
                            if coord.get('location'))
        
        result['geocoding_summary'] = {
            'total_locations': total_locations,
            'successful_geocoding': successful_coords,
            'geocoding_success_rate': successful_coords / total_locations if total_locations > 0 else 0,
            'api_used': 'HERE' if use_here_api else 'Nominatim'
        }
        
        return result

    def calculate_route_distance_here(self, origin_coords: Tuple[float, float], 
                                     destination_coords: Tuple[float, float]) -> Optional[Dict]:
        """
        Calculate distance between two coordinates using HERE Routing API (truck mode)
        
        Args:
            origin_coords: (latitude, longitude) of origin
            destination_coords: (latitude, longitude) of destination
            
        Returns:
            Dictionary with distance and duration information, or None if failed
        """
        if not self.here_api_key:
            print("⚠️  HERE API key not configured for distance calculation")
            return None
            
        if not origin_coords or not destination_coords:
            return None
            
        try:
            # HERE Routing API endpoint
            url = "https://router.hereapi.com/v8/routes"
            params = {
                'origin': f"{origin_coords[0]},{origin_coords[1]}",
                'destination': f"{destination_coords[0]},{destination_coords[1]}",
                'transportMode': 'truck',  # Use truck routing for accurate commercial vehicle routes
                'return': 'summary,polyline',
                'apikey': self.here_api_key
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('routes') and len(data['routes']) > 0:
                route = data['routes'][0]
                
                # HERE API v8 structure: routes[0] has summary directly or in sections
                if 'summary' in route:
                    summary = route['summary']
                    distance_meters = summary.get('length', 0)
                    duration_seconds = summary.get('duration', 0)
                elif 'sections' in route and len(route['sections']) > 0:
                    # Sum up all sections
                    sections = route['sections']
                    distance_meters = sum(section.get('summary', {}).get('length', 0) for section in sections)
                    duration_seconds = sum(section.get('summary', {}).get('duration', 0) for section in sections)
                else:
                    print(f"⚠️  Unexpected API response structure: {data}")
                    return None
                
                # Convert to miles and hours
                distance_miles = distance_meters / 1609.34   # convert to miles
             
                return {
                    'distance_miles': round(distance_miles, 1),
                    'api_used': 'HERE'
                }
            else:
                print(f"⚠️  No route found between coordinates")
                return None
                
        except Exception as e:
            print(f"⚠️  Distance calculation failed: {e}")
            print(f"   Request URL: {url}")
            print(f"   Origin: {origin_coords}")
            print(f"   Destination: {destination_coords}")
            return None
    
    def calculate_trip_distances(self, coordinates_data: Dict) -> Dict:
        """Calculate distances for all legs of a trip using coordinates from Step 4
        
        Args:
            coordinates_data: Dictionary with coordinate information from get_coordinates_for_stops
            
        Returns:
            Dictionary with distance calculations for each leg
        """
        try:
            if not coordinates_data:
                return {
                    'legs': [],
                    'total_legs': 0,
                    'successful_calculations': 0,
                    'total_distance_miles': 0,
                    'state_mileage': [],
                    'calculation_success': False,
                    'error': 'No coordinate data provided'
                }
            
            print("📱 Calculating trip distances (Step 6)...")
            
            # Extract coordinate fields in trip order
            trip_sequence = [
                'trip_started_from',
                'first_drop', 
                'second_drop',
                'third_drop',
                'forth_drop',
                'inbound_pu',
                'drop_off'
            ]
            
            # Get valid coordinates in order
            valid_stops = []
            for field in trip_sequence:
                coord_info = coordinates_data.get(field, {})
                # Handle the case when coord_info is a string instead of dictionary
                if isinstance(coord_info, str):
                    print(f"⚠️ Warning: Coordinate info for {field} is a string: {coord_info}")
                    continue
                
                if (coord_info.get('latitude') is not None and 
                    coord_info.get('longitude') is not None and
                    coord_info.get('location')):
                    
                    # Extract state from location (assuming format "City, ST")
                    location = coord_info['location']
                    state = ""
                    if "," in location:
                        parts = location.split(",")
                        if len(parts) > 1:
                            state = parts[1].strip()
                            if len(state) > 2:  # If it's not a two-letter code, try to find it
                                state = state.split()[0] if state.split() else ""
                    
                    valid_stops.append({
                        'stop_type': field,
                        'location': coord_info['location'],
                        'state': state,
                        'coordinates': (coord_info['latitude'], coord_info['longitude'])
                    })
            
            if len(valid_stops) < 2:
                print("❌ Need at least 2 valid coordinates to calculate distances")
                return {
                    'legs': [],
                    'total_distance_miles': 0,
                    'calculation_success': False,
                    'error': 'Insufficient valid coordinates'
                }
            
            print(f"📍 Found {len(valid_stops)} valid stops for distance calculation")
            
            # Calculate distances for each leg
            legs = []
            total_distance = 0
            state_distances = {}  # Track distances by state
            
            for i in range(len(valid_stops) - 1):
                origin = valid_stops[i]
                destination = valid_stops[i + 1]
                
                print(f"   Calculating leg {i+1}: {origin['location']} → {destination['location']}")
                
                # Calculate distance using HERE API
                distance_info = self.calculate_route_distance_here(
                    origin['coordinates'], 
                    destination['coordinates']
                )
                
                leg_data = {
                    'leg_number': i + 1,
                    'origin': {
                        'stop_type': origin['stop_type'],
                        'location': origin['location'],
                        'state': origin['state'],
                        'coordinates': origin['coordinates']
                    },
                    'destination': {
                        'stop_type': destination['stop_type'],
                        'location': destination['location'],
                        'state': destination['state'],
                        'coordinates': destination['coordinates']
                    }
                }
                
                if distance_info:
                    leg_data['distance_miles'] = distance_info['distance_miles']
                    leg_data['api_used'] = distance_info['api_used']
                    distance_miles = distance_info['distance_miles']
                    total_distance += distance_miles
                    
                    
                    # Assign mileage to states
                    origin_state = origin['state']
                    dest_state = destination['state']
                    
                    # If both stops are in the same state, assign all mileage to that state
                    if origin_state and origin_state == dest_state:
                        state_distances[origin_state] = state_distances.get(origin_state, 0) + distance_miles
                        leg_data['state_assignment'] = {origin_state: distance_miles}
                    # If different states or state info is missing, split the mileage evenly 
                    # (This is a simplification - ideally we'd have the actual path with state boundaries)
                    elif origin_state and dest_state:
                        # Split mileage between states (simplistic approach)
                        miles_per_state = distance_miles / 2
                        state_distances[origin_state] = state_distances.get(origin_state, 0) + miles_per_state
                        state_distances[dest_state] = state_distances.get(dest_state, 0) + miles_per_state
                        leg_data['state_assignment'] = {origin_state: miles_per_state, dest_state: miles_per_state}
                    # If one state is missing, assign all to the known state
                    elif origin_state:
                        state_distances[origin_state] = state_distances.get(origin_state, 0) + distance_miles
                        leg_data['state_assignment'] = {origin_state: distance_miles}
                    elif dest_state:
                        state_distances[dest_state] = state_distances.get(dest_state, 0) + distance_miles
                        leg_data['state_assignment'] = {dest_state: distance_miles}
                    # If both states unknown, mark as unassigned
                    else:
                        state_distances['UNKNOWN'] = state_distances.get('UNKNOWN', 0) + distance_miles
                        leg_data['state_assignment'] = {'UNKNOWN': distance_miles}
                    
                    print(f"   ✅ {distance_miles} miles")
                else:
                    leg_data.update({
                        'distance_miles': 0,
                        'calculation_failed': True
                    })
                    print(f"   ❌ Distance calculation failed")
                
                legs.append(leg_data)
            
            # Prepare summary
            successful_legs = sum(1 for leg in legs if not leg.get('calculation_failed', False))
            
            # Format state distances for output
            state_mileage = []
            for state, distance in state_distances.items():
                state_mileage.append({
                    'state': state,
                    'miles': round(distance, 1),
                    'percentage': round((distance / total_distance * 100) if total_distance > 0 else 0, 1)
                })
            
            # Sort state mileage by distance (descending)
            state_mileage.sort(key=lambda x: x['miles'], reverse=True)
            
            result = {
                'legs': legs,
                'total_legs': len(legs),
                'successful_calculations': successful_legs,
                'total_distance_miles': round(total_distance, 1),
                'state_mileage': state_mileage,
                'calculation_success': successful_legs > 0,
                'api_used': 'HERE'
            }
            
            print(f"📊 Distance calculation summary:")
            print(f"   Total legs: {len(legs)}")
            print(f"   Successful calculations: {successful_legs}")
            print(f"   Total distance: {result['total_distance_miles']} miles")
            
            # Print state mileage breakdown
            print(f"   State mileage breakdown:")
            for state_data in state_mileage:
                print(f"      {state_data['state']}: {state_data['miles']} miles ({state_data['percentage']}%)")
            
            return result
        
        except Exception as e:
            import sys, traceback
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = traceback.extract_tb(exc_tb)[-1][0]
            line_no = traceback.extract_tb(exc_tb)[-1][1]
            print(f"❌ Error in calculate_trip_distances: {e} at line {line_no} in {os.path.basename(fname)}")
            traceback.print_exc()
            return {
                'legs': [],
                'total_legs': 0,
                'successful_calculations': 0,
                'total_distance_miles': 0,
                'state_mileage': [],
                'error': f"Error: {str(e)} at line {line_no} in {os.path.basename(fname)}"
            }

            
    def process_image_with_distances(self, image_path: str, use_here_api: bool = True) -> Dict:
        """
        Complete processing: Extract data, get coordinates, and calculate distances (Steps 1-6)
        
        Args:
            image_path: Path to driver packet image
            use_here_api: Whether to use HERE API for geocoding and routing
            
        Returns:
            Dictionary with complete processing results including distances
        """
        try:
            print("🚛 Complete processing with distance calculation (Steps 1-6)...")
            
            # Step 1-4: Process image with coordinates
            result = self.process_image_with_coordinates(image_path, use_here_api)
        except Exception as e:
            import sys, traceback
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = traceback.extract_tb(exc_tb)[-1][0]
            line_no = traceback.extract_tb(exc_tb)[-1][1]
            print(f"❌ Error in process_image_with_distances: {e} at line {line_no} in {os.path.basename(fname)}")
            traceback.print_exc()
            return {
                'processing_success': False,
                'error': f"Error: {str(e)} at line {line_no} in {os.path.basename(fname)}",
                'source_image': os.path.basename(image_path)
            }
        
        if not result or not result.get('processing_success'):
            return result
        
        # Step 6: Calculate distances using coordinates
        if 'coordinates' in result and isinstance(result['coordinates'], dict):
            print("\n📏 Step 6: Calculating distances...")
            distance_data = self.calculate_trip_distances(result['coordinates'])
            result['distance_calculations'] = distance_data
            
            # Compare extracted miles with calculated miles (if both are available)
            extracted_miles = result.get('total_miles', '')
            calculated_miles = distance_data.get('total_distance_miles', 0)
            
            if extracted_miles and calculated_miles > 0:
                try:
                    extracted_miles_num = float(str(extracted_miles).replace(',', ''))
                    
                    # Calculate percentage difference
                    percentage_diff = abs((extracted_miles_num - calculated_miles) / calculated_miles * 100)
                    
                    # Add warning if difference is more than 5%
                    if percentage_diff > 5:
                        warning = f"Suspicious total miles: extracted ({extracted_miles_num}) differs from calculated ({calculated_miles:.1f}) by {percentage_diff:.1f}%"
                        
                        # Add to validation warnings
                        if 'validation_warnings' not in result:
                            result['validation_warnings'] = []
                        result['validation_warnings'].append(warning)
                        
                        print(f"⚠️ {warning}")
                except ValueError:
                    pass  # Skip comparison if miles can't be converted to float
        else:
            print("❌ No coordinates available for distance calculation")
            result['distance_calculations'] = {
                'calculation_success': False,
                'error': 'No coordinates available'
            }
        
        # Step 7: Validate against reference data if available
        print("\n🔍 Step 7: Validating against reference data...")
        validation_result = self.validate_against_reference(result)
        
        if validation_result.get('validation_success') and validation_result.get('reference_found'):
            result['reference_validation'] = validation_result
            
            # Add reference validation warnings to main warnings
            ref_warnings = validation_result.get('validation_warnings', [])
            if ref_warnings:
                if 'validation_warnings' not in result:
                    result['validation_warnings'] = []
                result['validation_warnings'].extend(ref_warnings)
        else:
            # No reference validation possible - check if it's because file doesn't exist
            reference_csv_path = os.path.join(os.path.dirname(__file__), '..', 'input', 'driver - Sheet1.csv')
            if not os.path.exists(reference_csv_path):
                # File doesn't exist - this is normal, just skip validation quietly
                result['reference_validation'] = {
                    'validation_success': False,
                    'reference_found': False,
                    'note': 'No reference test file available'
                }
            else:
                # File exists but validation failed for other reasons
                result['reference_validation'] = {
                    'validation_success': False,
                    'reference_found': False,
                    'note': 'Reference validation failed - no matching data found'
                }
        
        return result
    
    def _validate_extraction(self, extracted_data):
        """
        Validate extracted data for common issues like hallucinations and field swapping
        Args:
            extracted_data: Dictionary of extracted data
        Returns:
            warnings_list
        """
        warnings = []
        
        # Check for suspicious trip numbers (numbers that seem too high)
        if extracted_data.get('trip'):
            try:
                trip_num = int(extracted_data['trip'])
                if trip_num > 100:  # Reasonable upper bound for trip numbers
                    warnings.append(f"Suspicious trip number: {trip_num} (may be hallucinated)")
            except ValueError:
                pass
        
        # Check for very short or suspicious names
        if extracted_data.get('drivers_name'):
            name = extracted_data['drivers_name'].strip()
            if len(name) < 4:
                warnings.append(f"Very short driver name: '{name}' (may be incomplete)")
        
        # Check date format consistency
        date_fields = ['date_trip_started', 'date_trip_ended']
        for field in date_fields:
            if extracted_data.get(field):
                date_str = extracted_data[field]
                # Basic date format validation
                if not re.match(r'\d{1,2}[/.]\d{1,2}[/-]\d{2,4}', date_str):
                    warnings.append(f"Unusual date format in {field}: '{date_str}'")
        
        # Check for potential field swapping (common hallucination pattern)
        drop_fields = ['first_drop', 'second_drop', 'third_drop', 'forth_drop']
        filled_drops = [field for field in drop_fields if extracted_data.get(field)]
        inbound_pu = extracted_data.get('inbound_pu', '')
        
        # Check for suspicious patterns
        if inbound_pu and len(filled_drops) > 0:
            # Check if inbound_pu looks like a drop location that might be swapped
            for drop_field in filled_drops:
                if extracted_data[drop_field] == inbound_pu:
                    warnings.append(f"Possible field duplication: {drop_field} and inbound_pu have same value")
        
        # Check for gaps in drop sequence (might indicate swapping)
        if (not extracted_data.get('second_drop') and extracted_data.get('third_drop')):
            warnings.append("Suspicious: 3rd drop filled but 2nd drop empty (possible field swap)")
        
        if (not extracted_data.get('third_drop') and extracted_data.get('forth_drop')):
            warnings.append("Suspicious: 4th drop filled but 3rd drop empty (possible field swap)")
        
        # Check for duplicate locations among all stops
        all_locations = []
        for field in extracted_data:
            if extracted_data.get(field):
                value = extracted_data[field]
                # Handle both string and list values
                if isinstance(value, list):
                    all_locations.extend(value)
                elif isinstance(value, str):
                    all_locations.append(value)
        
        seen_locations = set()
        duplicate_locations = set()
        
        for loc in all_locations:
            if isinstance(loc, str) and loc.strip():  # Only check string locations
                if loc in seen_locations:
                    duplicate_locations.add(loc)
                else:
                    seen_locations.add(loc)
                
        if duplicate_locations:
            for dup_loc in duplicate_locations:
                warnings.append(f"Duplicate location found: '{dup_loc}' appears in multiple fields")
        
        # Validate office use only section
        office_data = extracted_data.get('office_use_only', {})
        if isinstance(office_data, dict):
            total_miles = office_data.get('total_miles', '')
            if total_miles:
                try:
                    miles_num = int(total_miles.replace(',', ''))
                    if miles_num > 10000:  # Unrealistic for single trip
                        warnings.append(f"Suspicious total miles: {miles_num} (verify against image)")
                except ValueError:
                    pass
        
        return warnings
    
    def _apply_comprehensive_corrections(self, extracted_data):
        """
        Apply comprehensive corrections and validations based on batch results analysis
        Args:
            extracted_data: Dictionary of extracted data
        Returns:
            corrected_data, correction_warnings
        """
        corrected_data = extracted_data.copy()
        correction_warnings = []
        
        # 1. Fix trailer number validation (200-299 range)
        if corrected_data.get('trailer'):
            trailer = str(corrected_data['trailer']).strip()
            if len(trailer) == 3 and trailer.isdigit():
                if not trailer.startswith('2'):
                    original_trailer = trailer
                    corrected_trailer = '2' + trailer[1:]
                    corrected_data['trailer'] = corrected_trailer
                    correction_warnings.append(f"Trailer number corrected: {original_trailer} → {corrected_trailer}")
        
        # 2. Fix location corrections
        location_corrections = {
            'bloomington': 'Bloomington, CA',
            'yard': 'San Bernardino, CA',
            'jaredo': 'Laredo',
            'corona': 'Fontana',
            'ffa/on': 'Jefferson City',
            'monon': 'MONONGAH',
            'jaredotx': 'Laredo, TX'
        }
        
        location_fields = ['trip_started_from', 'first_drop', 'second_drop', 'third_drop', 'forth_drop', 'inbound_pu', 'drop_off']
        
        for field in location_fields:
            if corrected_data.get(field):
                original_value = corrected_data[field]
                corrected_value = self._correct_location(original_value, location_corrections)
                if corrected_value != original_value:
                    corrected_data[field] = corrected_value
                    correction_warnings.append(f"{field} corrected: {original_value} → {corrected_value}")
        
        # 3. Fix date format standardization
        date_fields = ['date_trip_started', 'date_trip_ended']
        for field in date_fields:
            if corrected_data.get(field):
                original_date = corrected_data[field]
                corrected_date = self._standardize_date_format(original_date)
                if corrected_date != original_date:
                    corrected_data[field] = corrected_date
                    correction_warnings.append(f"{field} format corrected: {original_date} → {corrected_date}")
        
        # 4. Handle drop_off as array if it contains "to"
        if corrected_data.get('drop_off'):
            drop_off_value = corrected_data['drop_off']
            if isinstance(drop_off_value, str) and ' to ' in drop_off_value.lower():
                # Split by "to" and clean up the values
                drop_off_array = [loc.strip() for loc in drop_off_value.split(' to ') if loc.strip()]
                # Apply location corrections to each drop-off location
                corrected_drop_offs = []
                for drop_off in drop_off_array:
                    corrected_drop_off = self._correct_location(drop_off, location_corrections)
                    corrected_drop_offs.append(corrected_drop_off)
                
                corrected_data['drop_off'] = corrected_drop_offs
                correction_warnings.append(f"drop_off converted to array: {drop_off_value} → {corrected_drop_offs}")
        
        # 5. Validate and correct field value copying (third_drop and forth_drop)
        inbound_pu = corrected_data.get('inbound_pu', '')
        drop_off = corrected_data.get('drop_off', '')
        
        # If drop_off is an array, convert to string for comparison
        if isinstance(drop_off, list):
            drop_off_str = ', '.join(drop_off)
        else:
            drop_off_str = drop_off
        
        # Check if third_drop or forth_drop match inbound_pu or drop_off
        if corrected_data.get('third_drop') and corrected_data['third_drop'] in [inbound_pu, drop_off_str]:
            original_value = corrected_data['third_drop']
            corrected_data['third_drop'] = ""
            correction_warnings.append(f"third_drop cleared (matched inbound_pu/drop_off): {original_value} → empty")
        
        if corrected_data.get('forth_drop') and corrected_data['forth_drop'] in [inbound_pu, drop_off_str]:
            original_value = corrected_data['forth_drop']
            corrected_data['forth_drop'] = ""
            correction_warnings.append(f"forth_drop cleared (matched inbound_pu/drop_off): {original_value} → empty")
        
        # 6. Validate total miles for reasonableness
        if corrected_data.get('total_miles'):
            total_miles = str(corrected_data['total_miles']).replace(',', '')
            try:
                miles_num = float(total_miles)
                if miles_num < 100:
                    correction_warnings.append(f"Suspicious total miles (too low): {total_miles} - verify against image")
                elif miles_num > 15000:
                    correction_warnings.append(f"Suspicious total miles (too high): {total_miles} - verify against image")
            except ValueError:
                correction_warnings.append(f"Invalid total miles format: {total_miles}")
        
        return corrected_data, correction_warnings
    
    def _correct_location(self, location, corrections_dict):
        """
        Apply location corrections based on common patterns
        Args:
            location: Original location string or list
            corrections_dict: Dictionary of corrections
        Returns:
            Corrected location string or list
        """
        if not location:
            return location
        
        # Handle list case (for drop_off arrays)
        if isinstance(location, list):
            corrected_list = []
            for item in location:
                if item:
                    corrected_item = self._correct_location(item, corrections_dict)
                    corrected_list.append(corrected_item)
                else:
                    corrected_list.append(item)
            return corrected_list
        
        # Handle string case
        if not isinstance(location, str):
            return location
            
        location_lower = location.lower().strip()
        
        # Check for direct matches
        for wrong_name, correct_name in corrections_dict.items():
            if wrong_name in location_lower:
                if wrong_name == 'bloomington':
                    return 'Bloomington, CA'
                elif wrong_name == 'yard':
                    return 'San Bernardino, CA'
                elif wrong_name == 'jaredo':
                    # Replace Jaredo with Laredo but keep the state
                    if ',' in location:
                        parts = location.split(',')
                        state = parts[1].strip() if len(parts) > 1 else 'TX'
                        return f'Laredo, {state}'
                    else:
                        return 'Laredo, TX'
                elif wrong_name == 'corona':
                    # Replace Corona with Fontana but keep the state
                    if ',' in location:
                        parts = location.split(',')
                        state = parts[1].strip() if len(parts) > 1 else 'CA'
                        return f'Fontana, {state}'
                    else:
                        return 'Fontana, CA'
                elif wrong_name == 'jaredotx':
                    return 'Laredo, TX'
                else:
                    # For other corrections, replace in the original string
                    return location.replace(wrong_name, correct_name)
        
        return location
    
    def _standardize_date_format(self, date_string):
        """
        Standardize date format to MM/DD/YY
        Args:
            date_string: Original date string
        Returns:
            Standardized date string
        """
        if not date_string:
            return date_string
        
        # Remove any extra spaces
        date_string = date_string.strip()
        
        # Pattern: MM.DD.YYYY or MM.DD.YY
        dot_pattern = re.match(r'(\d{1,2})\.(\d{1,2})\.(\d{2,4})', date_string)
        if dot_pattern:
            month, day, year = dot_pattern.groups()
            if len(year) == 4:
                year = year[-2:]  # Convert to 2-digit year
            return f"{month.zfill(2)}/{day.zfill(2)}/{year}"
        
        # Pattern: MM-DD-YYYY or MM-DD-YY
        dash_pattern = re.match(r'(\d{1,2})-(\d{1,2})-(\d{2,4})', date_string)
        if dash_pattern:
            month, day, year = dash_pattern.groups()
            if len(year) == 4:
                year = year[-2:]  # Convert to 2-digit year
            return f"{month.zfill(2)}/{day.zfill(2)}/{year}"
        
        # Pattern: MM/DD/YYYY - convert to MM/DD/YY
        slash_pattern = re.match(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', date_string)
        if slash_pattern:
            month, day, year = slash_pattern.groups()
            if len(year) == 4:
                year = year[-2:]  # Convert to 2-digit year
            return f"{month.zfill(2)}/{day.zfill(2)}/{year}"
        
        # If no pattern matches, return original
        return date_string

    def process_image_with_coordinates(self, image_path: str, use_here_api: bool = True) -> Dict:
        """
        Extract data from driver packet image and get coordinates (Steps 1-4)
        
        Args:
            image_path: Path to driver packet image
            use_here_api: Whether to use HERE API for geocoding
            
        Returns:
            Dictionary with extracted data and coordinates
        """
        try:
            print("🚛 Processing image with extraction and coordinates (Steps 1-4)...")
            
            # Check if file exists
            if not os.path.isfile(image_path):
                return {
                    'processing_success': False,
                    'error': f"Error: File not found: {image_path}",
                    'source_image': os.path.basename(image_path)
                }
            
            # Step 1-2: Extract data from image using Gemini
            print("📝 Extracting data from image...")
            try:
                img = Image.open(image_path)
                response = self.model.generate_content([self.extraction_prompt, img])
                extracted_text = response.text
                
                # Parse JSON from the response
                try:
                    # Remove markdown code block syntax if present
                    if '```json' in extracted_text:
                        extracted_text = extracted_text.split('```json')[1]
                    if '```' in extracted_text:
                        extracted_text = extracted_text.split('```')[0]
                    
                    extracted_data = json.loads(extracted_text.strip())
                except json.JSONDecodeError as je:
                    return {
                        'processing_success': False,
                        'error': f"Error parsing JSON: {je}",
                        'source_image': os.path.basename(image_path),
                        'raw_extraction': extracted_text
                    }
                    
            except Exception as e:
                import sys, traceback
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = traceback.extract_tb(exc_tb)[-1][0]
                line_no = traceback.extract_tb(exc_tb)[-1][1]
                error_msg = f"Error in data extraction: {e} at line {line_no} in {os.path.basename(fname)}"
                print(f"❌ {error_msg}")
                traceback.print_exc()
                return {
                    'processing_success': False,
                    'error': error_msg,
                    'source_image': os.path.basename(image_path)
                }
            
            # Step 3: Apply comprehensive corrections
            print("🔧 Applying comprehensive corrections...")
            corrected_data, correction_warnings = self._apply_comprehensive_corrections(extracted_data)
            
            # Add basic processing metadata
            result = {
                'source_image': os.path.basename(image_path),
                'processing_success': True,
                'processing_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                **corrected_data
            }
            
            # Validate extraction data
            warnings = self._validate_extraction(result)
            
            # Combine validation warnings with correction warnings
            all_warnings = warnings + correction_warnings
            if all_warnings:
                result['validation_warnings'] = all_warnings
                print("⚠️ Validation and correction warnings:")
                for warning in all_warnings:
                    print(f"  - {warning}")
            
            # Print correction summary if any corrections were made
            if correction_warnings:
                print(f"✅ Applied {len(correction_warnings)} automatic corrections")
            
            # Step 4: Add coordinates for locations
            if use_here_api or True:  # Always add coordinates
                print("\n🌍 Adding coordinate information...")
                coordinates_data = self.get_coordinates_for_stops(result, use_here_api)
                if coordinates_data:
                    result['coordinates'] = coordinates_data
            
            return result
            
        except Exception as e:
            import sys, traceback
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = traceback.extract_tb(exc_tb)[-1][0]
            line_no = traceback.extract_tb(exc_tb)[-1][1]
            print(f"❌ Error in process_image_with_coordinates: {e} at line {line_no} in {os.path.basename(fname)}")
            traceback.print_exc()
            return {
                'processing_success': False,
                'error': f"Error: {str(e)} at line {line_no} in {os.path.basename(fname)}",
                'source_image': os.path.basename(image_path)
            }
        
    def process_multiple_images(self, input_folder, use_here_api: bool = True):
        """
        Process multiple driver packet images with scalable data cleaning
        Args:
            input_folder: Folder containing driver packet images
            use_here_api: Whether to use HERE API for geocoding
            
        Returns:
            List of dictionaries with processing results
        """
        try:
            results = []
            image_files = []
            
            # Find all image files in the input folder
            for ext in ['*.jpg', '*.jpeg', '*.png']:
                image_files.extend(glob.glob(os.path.join(input_folder, ext)))
            
            if not image_files:
                print(f"No image files found in {input_folder}")
                return []
            
            print(f"Found {len(image_files)} images to process")
            
            # Process each image
            for image_path in image_files:
                try:
                    print(f"\n{'='*50}")
                    print(f"Processing {os.path.basename(image_path)}...")
                    result = self.process_image_with_distances(image_path, use_here_api)
                    results.append(result)
                except Exception as e:
                    import sys, traceback
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = traceback.extract_tb(exc_tb)[-1][0]
                    line_no = traceback.extract_tb(exc_tb)[-1][1]
                    print(f"❌ Error processing {image_path}: {e} at line {line_no} in {os.path.basename(fname)}")
                    traceback.print_exc()
                    results.append({
                        'source_image': os.path.basename(image_path),
                        'processing_success': False,
                        'error': f"Error: {str(e)} at line {line_no} in {os.path.basename(fname)}"
                    })
            
            # Show summary of processing results
            successful = sum(1 for r in results if r.get('processing_success'))
            print(f"\n✅ Successfully processed {successful}/{len(image_files)} images")
            
            return results
            
        except Exception as e:
            import sys, traceback
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = traceback.extract_tb(exc_tb)[-1][0]
            line_no = traceback.extract_tb(exc_tb)[-1][1]
            print(f"\u274c Error in process_multiple_images: {e} at line {line_no} in {os.path.basename(fname)}")
            traceback.print_exc()
            return [{
                'processing_success': False,
                'error': f"Batch processing error: {str(e)} at line {line_no} in {os.path.basename(fname)}"
            }]

    def validate_against_reference(self, extracted_data: Dict, reference_csv_path: Optional[str] = None) -> Dict:
        """
        Validate extracted data against reference CSV file
        
        Args:
            extracted_data: Dictionary with extracted data including source_image
            reference_csv_path: Path to reference CSV file (defaults to input/driver - Sheet1.csv)
            
        Returns:
            Dictionary with validation results and discrepancy warnings
        """
        if not reference_csv_path:
            reference_csv_path = os.path.join(os.path.dirname(__file__), '..', 'input', 'driver - Sheet1.csv')
        
        validation_result = {
            'validation_success': False,
            'reference_found': False,
            'discrepancies': [],
            'accuracy_metrics': {},
            'validation_warnings': []
        }
        
        try:
            # Check if reference file exists
            if not os.path.exists(reference_csv_path):
                print(f"⚠️  No reference test file available (skipping validation): {os.path.basename(reference_csv_path)}")
                return validation_result
            
            # Load reference data
            reference_data = self._load_reference_data(reference_csv_path)
            if not reference_data:
                validation_result['validation_warnings'].append("Failed to load reference data")
                return validation_result
            
            # Find matching reference entry
            source_image = extracted_data.get('source_image', '')
            reference_entry = self._find_reference_entry(source_image, reference_data)
            
            if not reference_entry:
                validation_result['validation_warnings'].append(f"No reference data found for image: {source_image}")
                return validation_result
            
            validation_result['reference_found'] = True
            
            # Compare fields and generate discrepancies
            discrepancies = self._compare_extracted_vs_reference(extracted_data, reference_entry)
            validation_result['discrepancies'] = discrepancies
            
            # Calculate accuracy metrics
            accuracy_metrics = self._calculate_accuracy_metrics(extracted_data, reference_entry, discrepancies)
            validation_result['accuracy_metrics'] = accuracy_metrics
            
            # Generate validation warnings for discrepancies
            validation_warnings = self._generate_validation_warnings(discrepancies)
            validation_result['validation_warnings'] = validation_warnings
            
            validation_result['validation_success'] = True
            
            print(f"🔍 Validation completed for {source_image}:")
            print(f"   Reference found: ✅")
            print(f"   Discrepancies found: {len(discrepancies)}")
            print(f"   Field accuracy: {accuracy_metrics.get('field_accuracy', 0):.1%}")
            
            if discrepancies:
                print(f"   ⚠️  Discrepancies detected:")
                for discrepancy in discrepancies[:5]:  # Show first 5
                    print(f"      - {discrepancy['field']}: {discrepancy['extracted']} ≠ {discrepancy['reference']}")
                if len(discrepancies) > 5:
                    print(f"      ... and {len(discrepancies) - 5} more")
            
            return validation_result
            
        except Exception as e:
            validation_result['validation_warnings'].append(f"Validation error: {str(e)}")
            return validation_result
    
    def _load_reference_data(self, csv_path: str) -> List[Dict]:
        """Load reference data from CSV file"""
        try:
            reference_data = []
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    reference_data.append(row)
            return reference_data
        except Exception as e:
            print(f"❌ Error loading reference CSV: {e}")
            return []
    
    def _find_reference_entry(self, source_image: str, reference_data: List[Dict]) -> Optional[Dict]:
        """Find matching reference entry for the source image"""
        # Try exact match first
        for entry in reference_data:
            if entry.get('Image Name', '').strip() == source_image:
                return entry
        
        # Try partial match (remove extension)
        image_name_base = source_image.replace('.jpg', '').replace('.jpeg', '').replace('.png', '')
        for entry in reference_data:
            ref_name = entry.get('Image Name', '').strip()
            if ref_name == image_name_base:
                return entry
        
        # Try contains match
        for entry in reference_data:
            ref_name = entry.get('Image Name', '').strip()
            if image_name_base in ref_name or ref_name in image_name_base:
                return entry
        
        return None
    
    def _compare_extracted_vs_reference(self, extracted_data: Dict, reference_entry: Dict) -> List[Dict]:
        """Compare extracted data with reference data and return discrepancies"""
        discrepancies = []
        
        # Field mapping between extracted data and reference CSV
        field_mapping = {
            'drivers_name': 'Driver Name',
            'unit': 'Unit',
            'trailer': 'Trailer',
            'date_trip_started': 'Date Trip Started',
            'date_trip_ended': 'Date Trip Ended',
            'trip': 'Trip',
            'trip_started_from': 'Trip Started form',  # Note: typo in CSV header
            'first_drop': '1st Drop',
            'second_drop': '2nd Drop',
            'third_drop': '3rd Drop',
            'forth_drop': '4th Drop',
            'inbound_pu': 'inbound PU',
            'drop_off': 'Drop Off',
            'total_miles': 'Total Miles'
        }
        
        for extracted_field, reference_field in field_mapping.items():
            extracted_value = self._normalize_field_value(extracted_data.get(extracted_field, ''))
            reference_value = self._normalize_field_value(reference_entry.get(reference_field, ''))
            
            # Special handling for drop_off arrays
            if extracted_field == 'drop_off' and isinstance(extracted_data.get('drop_off'), list):
                # Check if reference has multiple drop offs
                drop_off_fields = ['Drop Off', 'Drop Off 2', 'Drop Off 3']
                reference_drop_offs = []
                for drop_field in drop_off_fields:
                    drop_value = self._normalize_field_value(reference_entry.get(drop_field, ''))
                    if drop_value:
                        reference_drop_offs.append(drop_value)
                
                # Compare arrays
                extracted_drop_offs = [self._normalize_field_value(v) for v in extracted_data.get('drop_off', [])]
                if set(extracted_drop_offs) != set(reference_drop_offs):
                    discrepancies.append({
                        'field': extracted_field,
                        'extracted': extracted_drop_offs,
                        'reference': reference_drop_offs,
                        'severity': 'high',
                        'type': 'array_mismatch'
                    })
                continue
            
            # Compare normalized values
            if extracted_value != reference_value:
                severity = self._determine_discrepancy_severity(extracted_field, extracted_value, reference_value)
                discrepancies.append({
                    'field': extracted_field,
                    'extracted': extracted_value,
                    'reference': reference_value,
                    'severity': severity,
                    'type': 'value_mismatch'
                })
        
        return discrepancies
    
    def _normalize_field_value(self, value) -> str:
        """Normalize field value for comparison"""
        if value is None:
            return ''
        
        # Convert to string and normalize
        value_str = str(value).strip()
        
        # Remove extra spaces
        value_str = ' '.join(value_str.split())
        
        # Normalize common variations
        value_str = value_str.replace('  ', ' ')
        
        return value_str
    
    def _determine_discrepancy_severity(self, field: str, extracted: str, reference: str) -> str:
        """Determine severity of discrepancy"""
        # Critical fields that must match exactly
        critical_fields = ['drivers_name', 'unit', 'trailer', 'total_miles']
        
        # High importance fields
        high_importance_fields = ['date_trip_started', 'date_trip_ended', 'trip_started_from', 'inbound_pu', 'drop_off']
        
        # Check if it's just a minor formatting difference
        if self._is_minor_formatting_difference(extracted, reference):
            return 'low'
        
        if field in critical_fields:
            return 'critical'
        elif field in high_importance_fields:
            return 'high'
        else:
            return 'medium'
    
    def _is_minor_formatting_difference(self, extracted: str, reference: str) -> bool:
        """Check if difference is just minor formatting"""
        # Remove common formatting differences
        extracted_clean = extracted.lower().replace('.', '').replace('-', '/').replace(' ', '')
        reference_clean = reference.lower().replace('.', '').replace('-', '/').replace(' ', '')
        
        return extracted_clean == reference_clean
    
    def _calculate_accuracy_metrics(self, extracted_data: Dict, reference_entry: Dict, discrepancies: List[Dict]) -> Dict:
        """Calculate accuracy metrics"""
        field_mapping = {
            'drivers_name': 'Driver Name',
            'unit': 'Unit',
            'trailer': 'Trailer',
            'date_trip_started': 'Date Trip Started',
            'date_trip_ended': 'Date Trip Ended',
            'trip': 'Trip',
            'trip_started_from': 'Trip Started form',
            'first_drop': '1st Drop',
            'second_drop': '2nd Drop',
            'third_drop': '3rd Drop',
            'forth_drop': '4th Drop',
            'inbound_pu': 'inbound PU',
            'drop_off': 'Drop Off',
            'total_miles': 'Total Miles'
        }
        
        total_fields = len(field_mapping)
        matching_fields = total_fields - len(discrepancies)
        
        # Calculate accuracy by severity
        critical_discrepancies = sum(1 for d in discrepancies if d['severity'] == 'critical')
        high_discrepancies = sum(1 for d in discrepancies if d['severity'] == 'high')
        medium_discrepancies = sum(1 for d in discrepancies if d['severity'] == 'medium')
        low_discrepancies = sum(1 for d in discrepancies if d['severity'] == 'low')
        
        return {
            'field_accuracy': matching_fields / total_fields,
            'total_fields': total_fields,
            'matching_fields': matching_fields,
            'total_discrepancies': len(discrepancies),
            'critical_discrepancies': critical_discrepancies,
            'high_discrepancies': high_discrepancies,
            'medium_discrepancies': medium_discrepancies,
            'low_discrepancies': low_discrepancies
        }
    
    def _generate_validation_warnings(self, discrepancies: List[Dict]) -> List[str]:
        """Generate validation warnings based on discrepancies"""
        warnings = []
        
        for discrepancy in discrepancies:
            field = discrepancy['field']
            extracted = discrepancy['extracted']
            reference = discrepancy['reference']
            severity = discrepancy['severity']
            
            if severity == 'critical':
                warnings.append(f"🔴 CRITICAL: {field} mismatch - extracted: '{extracted}' ≠ reference: '{reference}'")
            elif severity == 'high':
                warnings.append(f"🟠 HIGH: {field} mismatch - extracted: '{extracted}' ≠ reference: '{reference}'")
            elif severity == 'medium':
                warnings.append(f"🟡 MEDIUM: {field} mismatch - extracted: '{extracted}' ≠ reference: '{reference}'")
            else:
                warnings.append(f"🔵 LOW: {field} formatting difference - extracted: '{extracted}' ≠ reference: '{reference}'")
        
        return warnings