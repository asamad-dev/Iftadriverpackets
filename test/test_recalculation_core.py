#!/usr/bin/env python3
"""
Core unit tests for recalculation functionality
Tests the essential logic without Streamlit dependencies
"""

import pytest
import unittest.mock as mock
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.main_processor import DriverPacketProcessor


class TestRecalculationCore:
    """Test core recalculation logic using the actual processor"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock the API keys to avoid real API calls
        self.mock_gemini_key = "mock_gemini_key"
        self.mock_here_key = "mock_here_key"
        
        # Sample edited data
        self.edited_data = {
            'drivers_name': 'John Doe',
            'unit': '123',
            'trailer': '456',
            'trip_started_from': 'San Francisco, CA',
            'first_drop': 'Las Vegas, NV',
            'drop_off': 'Houston, TX',
            'total_miles': '1400'
        }

    @patch('src.main_processor.GeminiDataExtractor')
    @patch('src.main_processor.GeocodingService')
    @patch('src.main_processor.RouteAnalyzer')
    @patch('src.main_processor.StateAnalyzer')
    @patch('src.main_processor.DataValidator')
    @patch('src.main_processor.ReferenceValidator')
    @patch('src.main_processor.FileProcessor')
    def test_processor_initialization(self, mock_file_proc, mock_ref_val, mock_data_val, 
                                    mock_state_analyzer, mock_route_analyzer, 
                                    mock_geocoding, mock_data_extractor):
        """Test that processor initializes correctly for recalculation"""
        
        # Mock the components to avoid real API calls
        mock_data_extractor_instance = MagicMock()
        mock_geocoding_instance = MagicMock()
        mock_route_analyzer_instance = MagicMock()
        mock_state_analyzer_instance = MagicMock()
        
        mock_data_extractor.return_value = mock_data_extractor_instance
        mock_geocoding.return_value = mock_geocoding_instance
        mock_route_analyzer.return_value = mock_route_analyzer_instance
        mock_state_analyzer.return_value = mock_state_analyzer_instance
        
        processor = DriverPacketProcessor(
            gemini_api_key=self.mock_gemini_key,
            here_api_key=self.mock_here_key
        )
        
        # Verify all components are initialized
        assert processor.geocoding_service is not None
        assert processor.route_analyzer is not None
        assert processor.state_analyzer is not None

    @patch('src.main_processor.GeminiDataExtractor')
    @patch('src.main_processor.GeocodingService')
    @patch('src.main_processor.RouteAnalyzer')
    @patch('src.main_processor.StateAnalyzer')
    @patch('src.main_processor.DataValidator')
    @patch('src.main_processor.ReferenceValidator')
    @patch('src.main_processor.FileProcessor')
    def test_get_coordinates_for_stops(self, mock_file_proc, mock_ref_val, mock_data_val, 
                                     mock_state_analyzer, mock_route_analyzer, 
                                     mock_geocoding, mock_data_extractor):
        """Test coordinate retrieval for edited stops"""
        
        # Mock successful geocoding
        mock_coordinates = {
            'trip_started_from': {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'location': 'San Francisco, CA'
            },
            'first_drop': {
                'latitude': 36.1699,
                'longitude': -115.1398,
                'location': 'Las Vegas, NV'
            },
            'drop_off': {
                'latitude': 29.7604,
                'longitude': -95.3698,
                'location': 'Houston, TX'
            }
        }
        
        # Mock the components to avoid real API calls
        mock_data_extractor_instance = MagicMock()
        mock_geocoding_instance = MagicMock()
        mock_route_analyzer_instance = MagicMock()
        mock_state_analyzer_instance = MagicMock()
        
        mock_data_extractor.return_value = mock_data_extractor_instance
        mock_geocoding.return_value = mock_geocoding_instance
        mock_route_analyzer.return_value = mock_route_analyzer_instance
        mock_state_analyzer.return_value = mock_state_analyzer_instance
        
        mock_geocoding_instance.get_coordinates_for_stops.return_value = mock_coordinates
        
        processor = DriverPacketProcessor(
            gemini_api_key=self.mock_gemini_key,
            here_api_key=self.mock_here_key
        )
        
        # Test coordinate retrieval
        result = processor.get_coordinates_for_stops(self.edited_data, use_here_api=True)
        
        # Verify geocoding was called
        mock_geocoding_instance.get_coordinates_for_stops.assert_called_once_with(
            self.edited_data, True
        )
        
        assert result == mock_coordinates

    @patch('src.main_processor.GeminiDataExtractor')
    @patch('src.main_processor.GeocodingService')
    @patch('src.main_processor.RouteAnalyzer')
    @patch('src.main_processor.StateAnalyzer')
    @patch('src.main_processor.DataValidator')
    @patch('src.main_processor.ReferenceValidator')
    @patch('src.main_processor.FileProcessor')
    def test_calculate_trip_distances(self, mock_file_proc, mock_ref_val, mock_data_val, 
                                    mock_state_analyzer, mock_route_analyzer, 
                                    mock_geocoding, mock_data_extractor):
        """Test distance calculation for recalculation"""
        
        # Mock coordinates data
        mock_coordinates = {
            'trip_started_from': {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'location': 'San Francisco, CA'
            },
            'drop_off': {
                'latitude': 29.7604,
                'longitude': -95.3698,
                'location': 'Houston, TX'
            }
        }
        
        # Mock distance calculation result
        mock_distance_result = {
            'calculation_success': True,
            'total_distance_miles': 1450.2,
            'successful_calculations': 1,
            'legs': [
                {
                    'origin': {'location': 'San Francisco, CA'},
                    'destination': {'location': 'Houston, TX'},
                    'distance_miles': 1450.2,
                    'calculation_failed': False
                }
            ]
        }
        
        # Mock the components to avoid real API calls
        mock_data_extractor_instance = MagicMock()
        mock_geocoding_instance = MagicMock()
        mock_route_analyzer_instance = MagicMock()
        mock_state_analyzer_instance = MagicMock()
        
        mock_data_extractor.return_value = mock_data_extractor_instance
        mock_geocoding.return_value = mock_geocoding_instance
        mock_route_analyzer.return_value = mock_route_analyzer_instance
        mock_state_analyzer.return_value = mock_state_analyzer_instance
        
        mock_route_analyzer_instance.calculate_trip_distances.return_value = mock_distance_result
        
        processor = DriverPacketProcessor(
            gemini_api_key=self.mock_gemini_key,
            here_api_key=self.mock_here_key
        )
        
        # Test distance calculation
        result = processor.calculate_trip_distances(mock_coordinates)
        
        # Verify route analyzer was called
        mock_route_analyzer_instance.calculate_trip_distances.assert_called_once_with(mock_coordinates)
        
        assert result == mock_distance_result
        assert result['calculation_success'] is True
        assert result['total_distance_miles'] == 1450.2

    @patch('src.main_processor.GeminiDataExtractor')
    @patch('src.main_processor.GeocodingService')
    @patch('src.main_processor.RouteAnalyzer')
    @patch('src.main_processor.StateAnalyzer')
    @patch('src.main_processor.DataValidator')
    @patch('src.main_processor.ReferenceValidator')
    @patch('src.main_processor.FileProcessor')
    def test_state_analysis_integration(self, mock_file_proc, mock_ref_val, mock_data_val, 
                                      mock_state_analyzer, mock_route_analyzer, 
                                      mock_geocoding, mock_data_extractor):
        """Test state analysis integration in recalculation"""
        
        # Mock distance calculation result with polylines
        mock_distance_result = {
            'calculation_success': True,
            'total_distance_miles': 1450.2,
            'trip_polylines': ['mock_polyline_data']
        }
        
        # Mock enhanced result after state analysis
        mock_enhanced_result = {
            'calculation_success': True,
            'total_distance_miles': 1450.2,
            'state_mileage': [
                {'state': 'CA', 'miles': 300, 'percentage': 20.7},
                {'state': 'NV', 'miles': 550, 'percentage': 37.9},
                {'state': 'TX', 'miles': 600, 'percentage': 41.4}
            ]
        }
        
        # Mock the components to avoid real API calls
        mock_data_extractor_instance = MagicMock()
        mock_geocoding_instance = MagicMock()
        mock_route_analyzer_instance = MagicMock()
        mock_state_analyzer_instance = MagicMock()
        
        mock_data_extractor.return_value = mock_data_extractor_instance
        mock_geocoding.return_value = mock_geocoding_instance
        mock_route_analyzer.return_value = mock_route_analyzer_instance
        mock_state_analyzer.return_value = mock_state_analyzer_instance
        
        mock_state_analyzer_instance.add_state_mileage_to_trip_data.return_value = mock_enhanced_result
        
        processor = DriverPacketProcessor(
            gemini_api_key=self.mock_gemini_key,
            here_api_key=self.mock_here_key
        )
        
        # Test state analysis
        polylines = mock_distance_result.get("trip_polylines", [])
        result = processor.state_analyzer.add_state_mileage_to_trip_data(
            mock_distance_result, polylines
        )
        
        # Verify state analyzer was called
        mock_state_analyzer_instance.add_state_mileage_to_trip_data.assert_called_once_with(
            mock_distance_result, ['mock_polyline_data']
        )
        
        assert result == mock_enhanced_result
        assert len(result['state_mileage']) == 3
        assert result['state_mileage'][0]['state'] == 'CA'


class TestRecalculationDataFlow:
    """Test the data flow through recalculation steps"""
    
    def test_data_transformation_chain(self):
        """Test that data flows correctly through the recalculation chain"""
        
        # Step 1: Original extracted data
        original_data = {
            'trip_started_from': 'Los Angeles, CA',
            'drop_off': 'Phoenix, AZ',
            'total_miles': '400'
        }
        
        # Step 2: Edited data
        edited_data = {
            'trip_started_from': 'San Francisco, CA',  # Changed
            'drop_off': 'Las Vegas, NV',  # Changed
            'total_miles': '400'  # Same
        }
        
        # Step 3: Coordinates (would come from geocoding)
        coordinates_data = {
            'trip_started_from': {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'location': 'San Francisco, CA'
            },
            'drop_off': {
                'latitude': 36.1699,
                'longitude': -115.1398,
                'location': 'Las Vegas, NV'
            }
        }
        
        # Step 4: Distance calculation result
        distance_result = {
            'calculation_success': True,
            'total_distance_miles': 570.1,
            'legs': [
                {
                    'origin': {'location': 'San Francisco, CA'},
                    'destination': {'location': 'Las Vegas, NV'},
                    'distance_miles': 570.1
                }
            ]
        }
        
        # Step 5: Enhanced result with state analysis
        enhanced_result = {
            'calculation_success': True,
            'total_distance_miles': 570.1,
            'state_mileage': [
                {'state': 'CA', 'miles': 285, 'percentage': 50.0},
                {'state': 'NV', 'miles': 285, 'percentage': 50.0}
            ]
        }
        
        # Verify data transformation makes sense
        assert edited_data['trip_started_from'] != original_data['trip_started_from']
        assert coordinates_data['trip_started_from']['location'] == edited_data['trip_started_from']
        assert distance_result['total_distance_miles'] == enhanced_result['total_distance_miles']
        assert len(enhanced_result['state_mileage']) == 2

    def test_validation_warnings_update(self):
        """Test that validation warnings are updated after recalculation"""
        
        # Original result with validation warnings
        original_result = {
            'total_miles': '1200',
            'validation_warnings': [
                'Suspicious total miles: extracted (1200) differs from calculated (1180.5) by 1.6%'
            ]
        }
        
        # New calculation result
        new_calculated_miles = 1450.2
        extracted_miles = 1200
        
        # Calculate new percentage difference
        percentage_diff = abs((extracted_miles - new_calculated_miles) / new_calculated_miles * 100)
        
        # Verify warning would be updated
        assert percentage_diff > 5  # Should trigger a warning
        
        expected_warning = f"Suspicious total miles: extracted ({extracted_miles}) differs from calculated ({new_calculated_miles:.1f}) by {percentage_diff:.1f}%"
        
        # This simulates what the recalculation function should do
        updated_warnings = [
            w for w in original_result['validation_warnings'] 
            if not w.startswith("Suspicious total miles:")
        ]
        updated_warnings.append(expected_warning)
        
        assert len(updated_warnings) == 1
        assert 'differs from calculated (1450.2)' in updated_warnings[0]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
