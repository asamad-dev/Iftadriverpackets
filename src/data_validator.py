#!/usr/bin/env python3
"""
Data validator module
Handles comprehensive data validation and correction for extracted driver packet data
"""

import re
from typing import Dict, List, Tuple

from .logging_utils import get_logger
from .config import config


class DataValidator:
    """
    Validate and correct extracted data for common issues and inconsistencies
    """
    
    def __init__(self):
        """Initialize the data validator"""
        self.logger = get_logger()
        
        # Location corrections mapping
        self.location_corrections = {
            'bloomington': 'Bloomington, CA',
            'yard': 'San Bernardino, CA',
            'jaredo': 'Laredo',
            'corona': 'Fontana',
            'ffa/on': 'FULTON',
            'monon': 'MONONGAH',
            'jaredotx': 'Laredo, TX'
        }
        
        # State abbreviation mappings
        self.state_abbreviations = {
            'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR', 'california': 'CA',
            'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE', 'florida': 'FL', 'georgia': 'GA',
            'hawaii': 'HI', 'idaho': 'ID', 'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA',
            'kansas': 'KS', 'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
            'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS', 'missouri': 'MO',
            'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV', 'new hampshire': 'NH', 'new jersey': 'NJ',
            'new mexico': 'NM', 'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH',
            'oklahoma': 'OK', 'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
            'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT', 'vermont': 'VT',
            'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV', 'wisconsin': 'WI', 'wyoming': 'WY'
        }
    
    def validate_and_correct_data(self, extracted_data: Dict) -> Tuple[Dict, List[str]]:
        """
        Validate and correct extracted data
        
        Args:
            extracted_data: Raw extracted data dictionary
            
        Returns:
            Tuple of (corrected_data, list_of_corrections_applied)
        """
        corrected_data = extracted_data.copy()
        corrections = []
        
        self.logger.info("Starting comprehensive data validation and correction...")
        
        # 1. Fix trailer number validation (200-299 range)
        trailer_corrections = self._correct_trailer_number(corrected_data)
        corrections.extend(trailer_corrections)
        
        # 2. Fix location corrections
        location_corrections = self._correct_locations(corrected_data)
        corrections.extend(location_corrections)
        
        # 3. Fix date format standardization
        date_corrections = self._standardize_dates(corrected_data)
        corrections.extend(date_corrections)
        
        # 4. Handle drop_off as array if it contains "to"
        dropoff_corrections = self._handle_dropoff_arrays(corrected_data)
        corrections.extend(dropoff_corrections)
        
        # 5. Validate and correct field value copying
        field_corrections = self._correct_field_duplication(corrected_data)
        corrections.extend(field_corrections)
        
        # 6. Clear middle drops that match start/end locations
        middle_drop_corrections = self._clear_duplicate_middle_drops(corrected_data)
        corrections.extend(middle_drop_corrections)
        
        # 7. Process fuel purchases and aggregate by state
        fuel_corrections = self._process_fuel_data(corrected_data)
        corrections.extend(fuel_corrections)
        
        if corrections:
            self.logger.info(f"Applied {len(corrections)} corrections")
            for correction in corrections:
                self.logger.debug(f"  - {correction}")
        else:
            self.logger.info("No corrections needed")
        
        return corrected_data, corrections
    
    def validate_extracted_data(self, extracted_data: Dict) -> List[str]:
        """
        Validate extracted data for common issues like hallucinations and field swapping
        
        Args:
            extracted_data: Dictionary of extracted data
            
        Returns:
            List of validation warnings
        """
        warnings = []
        
        self.logger.debug("Validating extracted data for common issues...")
        
        # Check for suspicious trip numbers
        warnings.extend(self._check_trip_numbers(extracted_data))
        
        # Check for very short or suspicious names
        warnings.extend(self._check_driver_names(extracted_data))
        
        # Check date format consistency
        warnings.extend(self._check_date_formats(extracted_data))
        
        # Check for potential field swapping
        warnings.extend(self._check_field_swapping(extracted_data))
        
        # Check for duplicate locations
        warnings.extend(self._check_duplicate_locations(extracted_data))
        
        # Check for same city with different states
        warnings.extend(self._check_city_state_consistency(extracted_data))
        
        # Validate total miles reasonableness
        warnings.extend(self._check_total_miles(extracted_data))
        
        if warnings:
            self.logger.warning(f"Found {len(warnings)} validation warnings")
            for warning in warnings:
                self.logger.warning(f"  - {warning}")
        else:
            self.logger.debug("No validation warnings found")
        
        return warnings
    
    def _correct_trailer_number(self, data: Dict) -> List[str]:
        """Correct trailer numbers to ensure they're in 200-299 range"""
        corrections = []
        
        if data.get('trailer'):
            trailer = str(data['trailer']).strip()
            if len(trailer) == 3 and trailer.isdigit():
                if not trailer.startswith('2'):
                    original_trailer = trailer
                    corrected_trailer = '2' + trailer[1:]
                    data['trailer'] = corrected_trailer
                    corrections.append(f"Trailer number corrected: {original_trailer} → {corrected_trailer}")
        
        return corrections
    
    def _correct_locations(self, data: Dict) -> List[str]:
        """Apply location corrections based on common patterns"""
        corrections = []
        
        location_fields = ['trip_started_from', 'first_drop', 'second_drop', 'third_drop', 'forth_drop', 'inbound_pu', 'drop_off']
        
        for field in location_fields:
            if data.get(field):
                original_value = data[field]
                corrected_value = self._correct_location(original_value)
                if corrected_value != original_value:
                    data[field] = corrected_value
                    corrections.append(f"{field} corrected: {original_value} → {corrected_value}")
        
        return corrections
    
    def _correct_location(self, location) -> str:
        """Apply location corrections to a single location value"""
        if not location:
            return location
        
        # Handle list case (for drop_off arrays)
        if isinstance(location, list):
            corrected_list = []
            for item in location:
                if item:
                    corrected_item = self._correct_location(item)
                    corrected_list.append(corrected_item)
                else:
                    corrected_list.append(item)
            return corrected_list
        
        # Handle string case
        if not isinstance(location, str):
            return location
            
        location_lower = location.lower().strip()
        
        # Check for direct matches
        for wrong_name, correct_name in self.location_corrections.items():
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
    
    def _standardize_dates(self, data: Dict) -> List[str]:
        """Standardize date formats to MM/DD/YY"""
        corrections = []
        
        date_fields = ['date_trip_started', 'date_trip_ended']
        for field in date_fields:
            if data.get(field):
                original_date = data[field]
                corrected_date = self._standardize_date_format(original_date)
                if corrected_date != original_date:
                    data[field] = corrected_date
                    corrections.append(f"{field} format corrected: {original_date} → {corrected_date}")
        
        return corrections
    
    def _standardize_date_format(self, date_string: str) -> str:
        """Standardize date format to MM/DD/YY"""
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
    
    def _handle_dropoff_arrays(self, data: Dict) -> List[str]:
        """Handle drop_off field as array if it contains 'to'"""
        corrections = []
        
        if data.get('drop_off'):
            drop_off_value = data['drop_off']
            if isinstance(drop_off_value, str) and ' to ' in drop_off_value.lower():
                # Split by "to" and clean up the values
                drop_off_array = [loc.strip() for loc in drop_off_value.split(' to ') if loc.strip()]
                # Apply location corrections to each drop-off location
                corrected_drop_offs = []
                for drop_off in drop_off_array:
                    corrected_drop_off = self._correct_location(drop_off)
                    corrected_drop_offs.append(corrected_drop_off)
                
                data['drop_off'] = corrected_drop_offs
                corrections.append(f"drop_off converted to array: {drop_off_value} → {corrected_drop_offs}")
        
        return corrections
    
    def _correct_field_duplication(self, data: Dict) -> List[str]:
        """Correct field value copying between inbound_pu, drop_off and middle drops"""
        corrections = []
        
        inbound_pu = data.get('inbound_pu', '')
        drop_off = data.get('drop_off', '')
        
        # If drop_off is an array, convert to string for comparison
        if isinstance(drop_off, list):
            drop_off_str = ', '.join(drop_off)
        else:
            drop_off_str = drop_off
        
        # Check if second_drop, third_drop or forth_drop match inbound_pu or drop_off
        for field in ['second_drop', 'third_drop', 'forth_drop']:
            if data.get(field) and data[field] in [inbound_pu, drop_off_str]:
                original_value = data[field]
                data[field] = ""
                corrections.append(f"{field} cleared (matched inbound_pu/drop_off): {original_value} → empty")
        
        return corrections
    
    def _clear_duplicate_middle_drops(self, data: Dict) -> List[str]:
        """Clear middle drops that match start/end locations"""
        corrections = []
        
        start_loc = data.get('trip_started_from', '').strip()
        end_loc_value = data.get('drop_off', '')
        end_loc = ', '.join(end_loc_value) if isinstance(end_loc_value, list) else str(end_loc_value)
        end_loc = end_loc.strip()
        
        if start_loc and end_loc and start_loc == end_loc:
            for middle_field in ['second_drop', 'third_drop', 'forth_drop']:
                if data.get(middle_field) and data[middle_field].strip() == start_loc:
                    original_value = data[middle_field]
                    data[middle_field] = ""
                    corrections.append(f"{middle_field} cleared (same as start/end location {start_loc})")
        
        return corrections
    
    def _process_fuel_data(self, data: Dict) -> List[str]:
        """Process fuel purchases data and aggregate by state"""
        corrections = []
        
        if data.get('fuel_purchases'):
            processed_fuel = self._aggregate_fuel_by_state(data['fuel_purchases'])
            data['fuel_by_state'] = processed_fuel['aggregated_by_state']
            data['total_gallons'] = processed_fuel['total_gallons']
            
            if processed_fuel.get('warnings'):
                corrections.extend(processed_fuel['warnings'])
        
        return corrections
    
    def _aggregate_fuel_by_state(self, fuel_purchases: List[Dict]) -> Dict:
        """Aggregate fuel purchases by state"""
        processed_data = {
            'aggregated_by_state': {},
            'total_gallons': 0,
            'warnings': []
        }
        
        if not fuel_purchases:
            return processed_data
        
        # Valid 2-letter state codes
        valid_states = set(self.state_abbreviations.values())
        
        for purchase in fuel_purchases:
            if not isinstance(purchase, dict):
                processed_data['warnings'].append(f"Invalid fuel purchase data format: {purchase}")
                continue
                
            state = purchase.get('state', '').strip().upper()
            gallons_str = str(purchase.get('gallons', '0')).strip()
            
            # Convert state name to abbreviation if needed
            if state.lower() in self.state_abbreviations:
                state = self.state_abbreviations[state.lower()]
            
            # Validate state abbreviation
            if not state or state not in valid_states:
                processed_data['warnings'].append(f"Invalid or missing state: '{purchase.get('state', '')}' - skipping fuel entry")
                continue
            
            # Parse gallons
            try:
                # Clean gallons string - remove commas and other non-numeric characters except decimal point
                clean_gallons = ''.join(c for c in gallons_str if c.isdigit() or c == '.')
                gallons = float(clean_gallons) if clean_gallons else 0.0
                
                if gallons <= 0:
                    processed_data['warnings'].append(f"Invalid gallons amount: '{gallons_str}' for state {state} - skipping")
                    continue
                    
            except (ValueError, TypeError):
                processed_data['warnings'].append(f"Could not parse gallons: '{gallons_str}' for state {state} - skipping")
                continue
            
            # Aggregate by state
            if state in processed_data['aggregated_by_state']:
                processed_data['aggregated_by_state'][state] += gallons
            else:
                processed_data['aggregated_by_state'][state] = gallons
                
            processed_data['total_gallons'] += gallons
        
        return processed_data
    
    def _check_trip_numbers(self, data: Dict) -> List[str]:
        """Check for suspicious trip numbers"""
        warnings = []
        
        if data.get('trip'):
            try:
                trip_num = int(data['trip'])
                if trip_num > 100:  # Reasonable upper bound for trip numbers
                    warnings.append(f"Suspicious trip number: {trip_num} (may be hallucinated)")
            except ValueError:
                pass
        
        return warnings
    
    def _check_driver_names(self, data: Dict) -> List[str]:
        """Check for very short or suspicious names"""
        warnings = []
        
        if data.get('drivers_name'):
            name = data['drivers_name'].strip()
            if len(name) < 4:
                warnings.append(f"Very short driver name: '{name}' (may be incomplete)")
        
        return warnings
    
    def _check_date_formats(self, data: Dict) -> List[str]:
        """Check date format consistency"""
        warnings = []
        
        date_fields = ['date_trip_started', 'date_trip_ended']
        for field in date_fields:
            if data.get(field):
                date_str = data[field]
                # Basic date format validation
                if not re.match(r'\d{1,2}[/.]\d{1,2}[/-]\d{2,4}', date_str):
                    warnings.append(f"Unusual date format in {field}: '{date_str}'")
        
        return warnings
    
    def _check_field_swapping(self, data: Dict) -> List[str]:
        """Check for potential field swapping patterns"""
        warnings = []
        
        drop_fields = ['first_drop', 'second_drop', 'third_drop', 'forth_drop']
        filled_drops = [field for field in drop_fields if data.get(field)]
        inbound_pu = data.get('inbound_pu', '')
        
        # Check for suspicious patterns
        if inbound_pu and len(filled_drops) > 0:
            # Check if inbound_pu looks like a drop location that might be swapped
            for drop_field in filled_drops:
                if data[drop_field] == inbound_pu:
                    warnings.append(f"Possible field duplication: {drop_field} and inbound_pu have same value")
        
        # Check for gaps in drop sequence (might indicate swapping)
        if (not data.get('second_drop') and data.get('third_drop')):
            warnings.append("Suspicious: 3rd drop filled but 2nd drop empty (possible field swap)")
        
        if (not data.get('third_drop') and data.get('forth_drop')):
            warnings.append("Suspicious: 4th drop filled but 3rd drop empty (possible field swap)")
        
        return warnings
    
    def _check_duplicate_locations(self, data: Dict) -> List[str]:
        """Check for duplicate locations among all stops"""
        warnings = []
        
        all_locations = []
        location_fields = ['trip_started_from', 'first_drop', 'second_drop', 'third_drop', 'forth_drop', 'inbound_pu', 'drop_off']
        
        for field in location_fields:
            if data.get(field):
                value = data[field]
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
        
        return warnings
    
    def _check_city_state_consistency(self, data: Dict) -> List[str]:
        """Check for same city used with different states across fields"""
        warnings = []
        
        try:
            location_fields = ['trip_started_from', 'first_drop', 'second_drop', 'third_drop', 'forth_drop', 'inbound_pu', 'drop_off']
            city_to_states = {}
            city_field_examples = {}

            def extract_city_state(value_str: str):
                if not isinstance(value_str, str):
                    return None, None
                parts = [p.strip() for p in value_str.split(',')]
                if not parts or not parts[0]:
                    return None, None
                city = parts[0].strip()
                state_part = parts[1].strip() if len(parts) > 1 else ''
                if state_part:
                    # Normalize to 2-letter state code when possible
                    state_norm = state_part.upper()
                    if len(state_norm) != 2:
                        state_norm = self.state_abbreviations.get(state_part.lower(), state_part.upper()[:2])
                else:
                    state_norm = ''
                return city, state_norm

            for field in location_fields:
                value = data.get(field)
                values_to_check = []
                if isinstance(value, list):
                    values_to_check = [v for v in value if isinstance(v, str) and v.strip()]
                elif isinstance(value, str) and value.strip():
                    values_to_check = [value]

                for loc in values_to_check:
                    city, state = extract_city_state(loc)
                    if not city:
                        continue
                    city_key = city.strip().lower()
                    if city_key not in city_to_states:
                        city_to_states[city_key] = set()
                        city_field_examples[city_key] = []
                    if state:
                        city_to_states[city_key].add(state)
                    city_field_examples[city_key].append(f"{field}: {loc}")

            for city_key, states in city_to_states.items():
                if len(states) > 1:
                    city_display = city_key.title()
                    examples = '; '.join(city_field_examples.get(city_key, [])[:4])
                    warnings.append(f"City used with different states: '{city_display}' in {sorted(states)} ({examples})")
        except Exception:
            # Non-fatal; do not block extraction
            pass
        
        return warnings
    
    def _check_total_miles(self, data: Dict) -> List[str]:
        """Validate total miles for reasonableness"""
        warnings = []
        
        if data.get('total_miles'):
            total_miles = str(data['total_miles']).replace(',', '')
            try:
                miles_num = float(total_miles)
                if miles_num < config.MIN_TOTAL_MILES:
                    warnings.append(f"Suspicious total miles (too low): {total_miles} - verify against image")
                elif miles_num > config.MAX_TOTAL_MILES:
                    warnings.append(f"Suspicious total miles (too high): {total_miles} - verify against image")
            except ValueError:
                warnings.append(f"Invalid total miles format: {total_miles}")
        
        return warnings
