#!/usr/bin/env python3
"""
Route analyzer module
Handles route distance calculations and trip analysis using HERE API
"""

import os
import math
import requests
from typing import Dict, List, Optional, Tuple

from .logging_utils import get_logger
from .config import config


class RouteAnalyzer:
    """
    Analyze routes and calculate distances between coordinates using HERE API
    """
    
    def __init__(self, here_api_key: Optional[str] = None):
        """
        Initialize the route analyzer
        
        Args:
            here_api_key: HERE API key (if not provided, will use config.HERE_API_KEY)
        """
        self.logger = get_logger()
        self.here_api_key = here_api_key or config.HERE_API_KEY
        
        if self.here_api_key:
            self.logger.info("HERE API key configured for route analysis")
        else:
            self.logger.warning("HERE API key not available - distance calculations will use great circle approximation")
    
    def calculate_route_distance(self, origin_coords: Tuple[float, float], 
                               destination_coords: Tuple[float, float]) -> Optional[Dict]:
        """
        Calculate distance between two coordinates using HERE Routing API
        
        Args:
            origin_coords: (latitude, longitude) of origin
            destination_coords: (latitude, longitude) of destination
            
        Returns:
            Dictionary with distance, polyline, and route information, or None if failed
        """
        if not self.here_api_key:
            self.logger.warning("HERE API key not configured - using great circle distance")
            distance_miles = self.estimate_great_circle_distance(origin_coords, destination_coords)
            return {
                'distance_miles': distance_miles,
                'api_used': 'great_circle_approximation',
                'polyline': None,
                'state_miles': {}
            }
            
        if not origin_coords or not destination_coords:
            return None
            
        try:
            # HERE Routing API with polyline for state analysis
            url = "https://router.hereapi.com/v8/routes"
            params = {
                'origin': f"{origin_coords[0]},{origin_coords[1]}",
                'destination': f"{destination_coords[0]},{destination_coords[1]}",
                'transportMode': 'truck',
                'return': 'summary,polyline',
                'apikey': self.here_api_key
            }
            
            self.logger.debug(f"HERE API routing: {origin_coords} → {destination_coords}")
            
            response = requests.get(url, params=params, timeout=config.ROUTING_TIMEOUT)
            self.logger.debug(f"HERE API response status: {response.status_code}")
            
            response.raise_for_status()
            
            data = response.json()
            self.logger.debug(f"HERE API returned {len(data.get('routes', []))} route(s)")
            
            if data.get('routes') and len(data['routes']) > 0:
                route = data['routes'][0]
                
                # Extract distance and polyline
                distance_meters = 0
                polyline_data = None
                
                if 'summary' in route:
                    summary = route['summary']
                    distance_meters = summary.get('length', 0)
                elif 'sections' in route and len(route['sections']) > 0:
                    # Sum up all sections
                    sections = route['sections']
                    distance_meters = sum(section.get('summary', {}).get('length', 0) for section in sections)
                else:
                    self.logger.warning(f"Unexpected API response structure: {data}")
                    return None
                
                # Extract polyline for route analysis
                if 'sections' in route and len(route['sections']) > 0:
                    # Collect all section polylines for complete path coverage
                    polyline_data = [section.get('polyline') for section in route['sections'] if section.get('polyline')]
                
                # Convert to miles
                distance_miles = distance_meters / 1609.34
                
                self.logger.info(f"HERE API route calculated: {distance_miles:.1f} miles")
                
                return {
                    'distance_miles': round(distance_miles, 1),
                    'polyline': polyline_data,
                    'api_used': 'HERE',
                    'state_miles': {}  # Will be populated by state analyzer
                }
            else:
                self.logger.warning("No route found between coordinates")
                return None
                
        except Exception as e:
            self.logger.error(f"HERE API distance calculation failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"HTTP Status: {e.response.status_code}")
                try:
                    error_data = e.response.json()
                    self.logger.error(f"API Error: {error_data}")
                except:
                    self.logger.error(f"Response Text: {e.response.text[:200]}")
            
            # Fallback to great circle distance
            distance_miles = self.estimate_great_circle_distance(origin_coords, destination_coords)
            return {
                'distance_miles': distance_miles,
                'api_used': 'great_circle_fallback',
                'polyline': None,
                'state_miles': {},
                'error': str(e)
            }
    
    def estimate_great_circle_distance(self, coords1: Tuple[float, float], coords2: Tuple[float, float]) -> float:
        """
        Estimate distance between two coordinates using the Haversine formula
        
        Args:
            coords1: (latitude, longitude) of first point
            coords2: (latitude, longitude) of second point
            
        Returns:
            Distance in miles
        """
        if not coords1 or not coords2:
            return 0.0
            
        try:
            lat1, lon1 = coords1
            lat2, lon2 = coords2
            
            # Convert to radians
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            
            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            # Earth radius in miles (from config)
            r = config.GREAT_CIRCLE_EARTH_RADIUS_MILES
            
            # Calculate distance
            distance = c * r
            
            return round(distance, 1)
            
        except Exception as e:
            self.logger.error(f"Distance estimation failed: {e}")
            return 0.0
    
    def calculate_trip_distances(self, coordinates_data: Dict) -> Dict:
        """
        Calculate distances for all legs of a trip using coordinates
        
        Args:
            coordinates_data: Dictionary with coordinate information from geocoding service
            
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
                    'calculation_success': False,
                    'error': 'No coordinate data provided'
                }
            
            self.logger.info("Calculating trip distances...")
            
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
                    self.logger.warning(f"Coordinate info for {field} is a string: {coord_info}")
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
                            if len(state) > 2:  # If it's not a two-letter code
                                state = state.split()[0] if state.split() else ""
                    
                    valid_stops.append({
                        'stop_type': field,
                        'location': coord_info['location'],
                        'state': state,
                        'coordinates': (coord_info['latitude'], coord_info['longitude'])
                    })
            
            if len(valid_stops) < 2:
                self.logger.error("Need at least 2 valid coordinates to calculate distances")
                return {
                    'legs': [],
                    'total_distance_miles': 0,
                    'calculation_success': False,
                    'error': 'Insufficient valid coordinates'
                }
            
            self.logger.info(f"Found {len(valid_stops)} valid stops for distance calculation")
            
            # Calculate distances for each leg
            legs = []
            total_distance = 0
            trip_polylines: List[str] = []  # Collect all polylines across legs
            
            for i in range(len(valid_stops) - 1):
                origin = valid_stops[i]
                destination = valid_stops[i + 1]
                
                self.logger.debug(f"Calculating leg {i+1}: {origin['location']} → {destination['location']}")
                
                # Calculate distance using HERE API or fallback
                distance_info = self.calculate_route_distance(
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
                    
                    # Collect polylines for trip-level analysis
                    polyline_value = distance_info.get('polyline')
                    if isinstance(polyline_value, list):
                        trip_polylines.extend([pl for pl in polyline_value if pl])
                    elif isinstance(polyline_value, str) and polyline_value:
                        trip_polylines.append(polyline_value)
                    
                    self.logger.info(f"Leg {i+1}: {distance_miles} miles")
                else:
                    leg_data.update({
                        'distance_miles': 0,
                        'calculation_failed': True,
                        'error': 'Route calculation failed'
                    })
                    self.logger.error(f"Leg {i+1}: Distance calculation failed")
                
                legs.append(leg_data)
            
            # Prepare summary
            successful_legs = sum(1 for leg in legs if not leg.get('calculation_failed', False))
            calculation_success = successful_legs > 0
            
            result = {
                'legs': legs,
                'total_legs': len(legs),
                'successful_calculations': successful_legs,
                'total_distance_miles': round(total_distance, 1),
                'calculation_success': calculation_success,
                'trip_polylines': trip_polylines  # For state analyzer
            }
            
            # Add error information if all calculations failed
            if successful_legs == 0:
                failed_legs_errors = [leg.get('error', 'Unknown error') for leg in legs if leg.get('calculation_failed')]
                result['calculation_errors'] = failed_legs_errors
                result['error_summary'] = f"All {len(legs)} distance calculations failed"
                
                if failed_legs_errors:
                    most_common_error = max(set(failed_legs_errors), key=failed_legs_errors.count)
                    result['primary_error'] = most_common_error
            
            self.logger.info(f"Distance calculation summary:")
            self.logger.info(f"  Total legs: {len(legs)}")
            self.logger.info(f"  Successful calculations: {successful_legs}")
            self.logger.info(f"  Total distance: {result['total_distance_miles']} miles")
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error in calculate_trip_distances: {e}")
            return {
                'legs': [],
                'total_legs': 0,
                'successful_calculations': 0,
                'total_distance_miles': 0,
                'calculation_success': False,
                'error': f"Error: {str(e)}"
            }
    
    def validate_distance_vs_extracted(self, extracted_miles: str, calculated_miles: float) -> Dict:
        """
        Compare extracted total miles with calculated miles
        
        Args:
            extracted_miles: Miles extracted from the document
            calculated_miles: Miles calculated from route analysis
            
        Returns:
            Dictionary with comparison results and warnings
        """
        validation_result = {
            'comparison_success': False,
            'percentage_difference': 0,
            'warnings': []
        }
        
        if not extracted_miles or calculated_miles <= 0:
            validation_result['warnings'].append("Cannot compare - missing extracted or calculated miles")
            return validation_result
        
        try:
            # Clean and convert extracted miles
            extracted_miles_str = str(extracted_miles).replace(',', '').strip()
            extracted_miles_num = float(extracted_miles_str)
            
            # Calculate percentage difference
            percentage_diff = abs((extracted_miles_num - calculated_miles) / calculated_miles * 100)
            
            validation_result['comparison_success'] = True
            validation_result['extracted_miles'] = extracted_miles_num
            validation_result['calculated_miles'] = calculated_miles
            validation_result['percentage_difference'] = round(percentage_diff, 1)
            
            # Add warnings based on difference
            if percentage_diff > 20:
                validation_result['warnings'].append(
                    f"MAJOR discrepancy: extracted ({extracted_miles_num}) vs calculated ({calculated_miles:.1f}) - {percentage_diff:.1f}% difference"
                )
            elif percentage_diff > 10:
                validation_result['warnings'].append(
                    f"Significant discrepancy: extracted ({extracted_miles_num}) vs calculated ({calculated_miles:.1f}) - {percentage_diff:.1f}% difference"
                )
            elif percentage_diff > 5:
                validation_result['warnings'].append(
                    f"Minor discrepancy: extracted ({extracted_miles_num}) vs calculated ({calculated_miles:.1f}) - {percentage_diff:.1f}% difference"
                )
            else:
                validation_result['warnings'].append(f"Miles match closely - {percentage_diff:.1f}% difference")
            
            self.logger.info(f"Distance validation: {percentage_diff:.1f}% difference between extracted and calculated miles")
            
            return validation_result
            
        except (ValueError, TypeError) as e:
            validation_result['warnings'].append(f"Cannot compare miles - invalid format: {e}")
            return validation_result
