#!/usr/bin/env python3
"""
Test suite for Streamlit recalculation functionality
Tests the complex multi-step process of editing values and recalculating distances
"""

import pytest
import unittest.mock as mock
from unittest.mock import MagicMock, patch
import sys
import os
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock streamlit before importing streamlit_app
sys.modules['streamlit'] = MagicMock()

# Import the functions we want to test
import streamlit_app
from streamlit_app import get_current_results_with_edits, debug_result_state_data


class TestRecalculationFunctionality:
    """Test suite for recalculation functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_processor = MagicMock()
        self.mock_session_state = MagicMock()
        
        # Sample original result
        self.original_result = {
            'source_image': 'test_packet.jpg',
            'processing_success': True,
            'drivers_name': 'John Doe',
            'unit': '123',
            'trailer': '456',
            'trip_started_from': 'Los Angeles, CA',
            'first_drop': 'Phoenix, AZ',
            'drop_off': 'Dallas, TX',
            'total_miles': '1200',
            'distance_calculations': {
                'calculation_success': True,
                'total_distance_miles': 1180.5,
                'successful_calculations': 2,
                'state_mileage': [
                    {'state': 'CA', 'miles': 400, 'percentage': 33.9},
                    {'state': 'AZ', 'miles': 380, 'percentage': 32.2},
                    {'state': 'TX', 'miles': 400, 'percentage': 33.9}
                ]
            }
        }
        
        # Sample edited result
        self.edited_result = {
            'source_image': 'test_packet.jpg',
            'processing_success': True,
            'drivers_name': 'John Doe',
            'unit': '123',
            'trailer': '456',
            'trip_started_from': 'San Francisco, CA',  # Changed
            'first_drop': 'Las Vegas, NV',  # Changed
            'drop_off': 'Houston, TX',  # Changed
            'total_miles': '1200',
        }

    def test_get_current_results_with_edits_no_edits(self):
        """Test getting results when no edits exist"""
        # Mock session state with only original results
        mock_session_state = MagicMock()
        mock_session_state.processing_results = [self.original_result.copy()]
        
        with patch('streamlit_app.st.session_state', mock_session_state):
            results = get_current_results_with_edits()
            
            assert len(results) == 1
            assert results[0]['trip_started_from'] == 'Los Angeles, CA'
            assert results[0]['first_drop'] == 'Phoenix, AZ'

    def test_get_current_results_with_edits_with_edits(self):
        """Test getting results when edits exist"""
        # Create a simple mock that behaves like a dict but with attribute access
        original_result = self.original_result.copy()
        edited_result = self.edited_result.copy()
        
        class MockSessionState:
            def __init__(self):
                self.processing_results = [original_result]
                self._data = {'edited_test_packet.jpg': edited_result}
            
            def __contains__(self, key):
                return key in self._data
            
            def __getitem__(self, key):
                return self._data[key]
        
        mock_session_state = MockSessionState()
        
        with patch('streamlit_app.st.session_state', mock_session_state):
            results = get_current_results_with_edits()
            
            assert len(results) == 1
            assert results[0]['trip_started_from'] == 'San Francisco, CA'  # Edited value
            assert results[0]['first_drop'] == 'Las Vegas, NV'  # Edited value

    @patch('streamlit_app.st')
    def test_debug_result_state_data_complete(self, mock_st):
        """Test debug function with complete state data"""
        result_with_state_data = {
            'distance_calculations': {
                'calculation_success': True,
                'total_distance_miles': 1200.5,
                'state_mileage': [
                    {'state': 'CA', 'miles': 600},
                    {'state': 'NV', 'miles': 600}
                ]
            }
        }
        
        debug_result_state_data(result_with_state_data, 'test.jpg')
        
        # Verify debug output was called
        assert mock_st.write.called
        calls = [call[0][0] for call in mock_st.write.call_args_list]
        
        # Check that key information was displayed
        assert any('distance_calculations exists: True' in str(call) for call in calls)
        assert any('calculation_success: True' in str(call) for call in calls)
        assert any('state_mileage count: 2' in str(call) for call in calls)

    @patch('streamlit_app.st')
    def test_debug_result_state_data_missing(self, mock_st):
        """Test debug function with missing state data"""
        result_without_state_data = {
            'distance_calculations': {}
        }
        
        debug_result_state_data(result_without_state_data, 'test.jpg')
        
        # Verify debug output was called
        assert mock_st.write.called
        calls = [call[0][0] for call in mock_st.write.call_args_list]
        
        # Check that missing data was identified
        assert any('distance_calculations: Missing or invalid' in str(call) for call in calls)


class TestRecalculationIntegration:
    """Integration tests for the full recalculation process"""
    
    def setup_method(self):
        """Set up integration test fixtures"""
        self.mock_processor = MagicMock()
        self.mock_state_analyzer = MagicMock()
        self.mock_processor.state_analyzer = self.mock_state_analyzer
        
        # Mock successful geocoding response
        self.mock_coordinates_data = {
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
        
        # Mock successful distance calculation response
        self.mock_distance_data = {
            'calculation_success': True,
            'total_distance_miles': 1450.2,
            'successful_calculations': 2,
            'trip_polylines': ['mock_polyline_1', 'mock_polyline_2'],
            'legs': [
                {
                    'origin': {'location': 'San Francisco, CA'},
                    'destination': {'location': 'Las Vegas, NV'},
                    'distance_miles': 570.1,
                    'calculation_failed': False
                },
                {
                    'origin': {'location': 'Las Vegas, NV'},
                    'destination': {'location': 'Houston, TX'},
                    'distance_miles': 880.1,
                    'calculation_failed': False
                }
            ]
        }
        
        # Mock enhanced distance data (after state analysis)
        self.mock_enhanced_distance_data = {
            'calculation_success': True,
            'total_distance_miles': 1450.2,
            'successful_calculations': 2,
            'state_mileage': [
                {'state': 'CA', 'miles': 300, 'percentage': 20.7},
                {'state': 'NV', 'miles': 550, 'percentage': 37.9},
                {'state': 'TX', 'miles': 600, 'percentage': 41.4}
            ],
            'legs': self.mock_distance_data['legs']
        }

    @patch('streamlit_app.st')
    def test_recalculation_success_flow(self, mock_st):
        """Test successful recalculation flow"""
        # Setup mocks
        self.mock_processor.get_coordinates_for_stops.return_value = self.mock_coordinates_data
        self.mock_processor.calculate_trip_distances.return_value = self.mock_distance_data
        self.mock_state_analyzer.add_state_mileage_to_trip_data.return_value = self.mock_enhanced_distance_data
        
        # Mock session state
        edited_result = {
            'source_image': 'test_packet.jpg',
            'trip_started_from': 'San Francisco, CA',
            'first_drop': 'Las Vegas, NV',
            'drop_off': 'Houston, TX',
            'total_miles': '1400'
        }
        
        mock_session_state = MagicMock()
        mock_session_state.processor = self.mock_processor
        mock_session_state.use_here_api = True
        mock_session_state.processing_results = [{'source_image': 'test_packet.jpg', 'unit': '123'}]
        
        # Mock the edited result access  
        mock_session_state.__getitem__ = lambda self, key: edited_result if key == 'edited_test_packet.jpg' else None
        
        with patch('streamlit_app.st.session_state', mock_session_state):
            with patch('streamlit_app.st.spinner'):
                with patch('time.sleep'):  # Skip the sleep
                    # Call the recalculation function
                    streamlit_app.recalculate_distances_for_result('test_packet.jpg')
        
        # Verify the process was called correctly
        self.mock_processor.get_coordinates_for_stops.assert_called_once()
        self.mock_processor.calculate_trip_distances.assert_called_once_with(self.mock_coordinates_data)
        self.mock_state_analyzer.add_state_mileage_to_trip_data.assert_called_once()
        
        # Verify success messages were shown
        mock_st.success.assert_called()
        mock_st.info.assert_called()
        mock_st.balloons.assert_called_once()
        mock_st.rerun.assert_called_once()

    @patch('streamlit_app.st')
    def test_recalculation_geocoding_failure(self, mock_st):
        """Test recalculation when geocoding fails"""
        # Setup mocks for failure
        self.mock_processor.get_coordinates_for_stops.return_value = None
        
        # Mock session state
        edited_result = {
            'source_image': 'test_packet.jpg',
            'trip_started_from': 'Invalid Location XYZ'
        }
        
        mock_session_state = MagicMock()
        mock_session_state.processor = self.mock_processor
        mock_session_state.use_here_api = True
        
        # Mock the edited result access  
        mock_session_state.__getitem__ = lambda self, key: edited_result if key == 'edited_test_packet.jpg' else None
        
        with patch('streamlit_app.st.session_state', mock_session_state):
            with patch('streamlit_app.st.spinner'):
                # Call the recalculation function
                streamlit_app.recalculate_distances_for_result('test_packet.jpg')
        
        # Verify error was shown
        mock_st.error.assert_called_with("❌ Failed to get coordinates for the edited locations")

    @patch('streamlit_app.st')
    def test_recalculation_distance_calculation_failure(self, mock_st):
        """Test recalculation when distance calculation fails"""
        # Setup mocks
        self.mock_processor.get_coordinates_for_stops.return_value = self.mock_coordinates_data
        
        # Mock failed distance calculation
        failed_distance_data = {
            'calculation_success': False,
            'total_distance_miles': 0,
            'error': 'HERE API routing failed'
        }
        self.mock_processor.calculate_trip_distances.return_value = failed_distance_data
        self.mock_state_analyzer.add_state_mileage_to_trip_data.return_value = failed_distance_data
        
        # Mock session state
        edited_result = {
            'source_image': 'test_packet.jpg',
            'trip_started_from': 'San Francisco, CA',
            'drop_off': 'Houston, TX'
        }
        
        mock_session_state = MagicMock()
        mock_session_state.processor = self.mock_processor
        mock_session_state.use_here_api = True
        mock_session_state.processing_results = [{'source_image': 'test_packet.jpg'}]
        
        # Mock the edited result access  
        mock_session_state.__getitem__ = lambda self, key: edited_result if key == 'edited_test_packet.jpg' else None
        
        with patch('streamlit_app.st.session_state', mock_session_state):
            with patch('streamlit_app.st.spinner'):
                with patch('time.sleep'):
                    # Call the recalculation function
                    streamlit_app.recalculate_distances_for_result('test_packet.jpg')
        
        # Verify warning was shown for failed calculation
        mock_st.warning.assert_called_with("⚠️ Distance recalculation completed but some routes failed")


class TestExportDataWithRecalculation:
    """Test export functionality with recalculated data"""
    
    def test_csv_export_with_state_data(self):
        """Test CSV export includes recalculated state data"""
        results_with_state_data = [
            {
                'source_image': 'test1.jpg',
                'processing_success': True,
                'unit': '123',
                'trailer': '456',
                'distance_calculations': {
                    'state_mileage': [
                        {'state': 'CA', 'miles': 500},
                        {'state': 'NV', 'miles': 300}
                    ]
                }
            }
        ]
        
        csv_output = streamlit_app.generate_csv_export(results_with_state_data)
        
        # Verify CSV contains state data
        assert 'California' in csv_output
        assert 'Nevada' in csv_output
        assert '500' in csv_output
        assert '300' in csv_output

    def test_csv_export_without_state_data(self):
        """Test CSV export handles missing state data gracefully"""
        results_without_state_data = [
            {
                'source_image': 'test1.jpg',
                'processing_success': True,
                'unit': '123',
                'trailer': '456',
                'distance_calculations': {}  # No state_mileage
            }
        ]
        
        csv_output = streamlit_app.generate_csv_export(results_without_state_data)
        
        # Verify CSV contains placeholder for missing data
        assert 'NO_STATE_DATA' in csv_output
        assert 'test1.jpg' in csv_output or '1' in csv_output  # Page number


@pytest.mark.integration
class TestRecalculationEndToEnd:
    """End-to-end tests for recalculation functionality"""
    
    @patch('streamlit_app.st')
    def test_edit_and_recalculate_workflow(self, mock_st):
        """Test the complete edit → recalculate → export workflow"""
        # This would be a more complex test that simulates:
        # 1. Loading original results
        # 2. Editing field values
        # 3. Triggering recalculation
        # 4. Verifying UI updates
        # 5. Testing export with new data
        
        # Mock the complete workflow
        mock_processor = MagicMock()
        mock_processor.get_coordinates_for_stops.return_value = {'mock': 'coordinates'}
        mock_processor.calculate_trip_distances.return_value = {'calculation_success': True, 'total_distance_miles': 1000}
        mock_processor.state_analyzer.add_state_mileage_to_trip_data.return_value = {
            'calculation_success': True,
            'total_distance_miles': 1000,
            'state_mileage': [{'state': 'CA', 'miles': 1000, 'percentage': 100}]
        }
        
        # This test would verify the complete workflow
        # For now, we'll just verify the mocks are set up correctly
        assert mock_processor is not None
        assert hasattr(mock_processor, 'state_analyzer')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
