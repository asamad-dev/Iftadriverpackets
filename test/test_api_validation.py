#!/usr/bin/env python3
"""
API validation tests - Test real API key connectivity
Tests that API keys from .env actually work by connecting to the services
"""

import pytest
import os
import sys
from unittest.mock import patch
import requests

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import config


@pytest.mark.api
class TestAPIValidation:
    """Test real API key validation by connecting to services"""
    
    def test_gemini_api_key_connectivity(self):
        """Test if Gemini API key from .env is valid by making a test connection"""
        if not config.GEMINI_API_KEY:
            pytest.skip("No GEMINI_API_KEY configured - skipping connectivity test")
        
        try:
            import google.generativeai as genai
            
            # Configure with the actual API key from .env
            genai.configure(api_key=config.GEMINI_API_KEY)
            
            # Try to list models to validate the key
            models = genai.list_models()
            model_list = list(models)
            
            # If we get here without exception, the API key works
            assert len(model_list) > 0, "Gemini API returned no models - key might be invalid"
            
            # Check if our configured model exists
            model_names = [model.name for model in model_list]
            expected_model = f"models/{config.GEMINI_MODEL}"
            
            # Find our model or any similar one
            found_compatible_model = any(
                config.GEMINI_MODEL in model_name or "gemini" in model_name.lower() 
                for model_name in model_names
            )
            
            assert found_compatible_model, f"No compatible model found. Available: {model_names[:5]}"
            
        except ImportError:
            pytest.skip("google-generativeai not installed - skipping Gemini API test")
        except Exception as e:
            pytest.fail(f"Gemini API key validation failed: {str(e)}")
    
    def test_here_api_key_connectivity(self):
        """Test if HERE API key from .env is valid by making a test connection"""
        if not config.HERE_API_KEY:
            pytest.skip("No HERE_API_KEY configured - skipping connectivity test")
        
        try:
            # Test HERE Geocoding API with a simple request
            url = "https://geocode.search.hereapi.com/v1/geocode"
            params = {
                'q': 'San Francisco, CA',  # Simple test query
                'apikey': config.HERE_API_KEY,
                'limit': 1
            }
            
            response = requests.get(url, params=params, timeout=config.GEOCODING_TIMEOUT)
            
            # Check if API key is valid
            if response.status_code == 401:
                pytest.fail("HERE API key is invalid (401 Unauthorized)")
            elif response.status_code == 403:
                pytest.fail("HERE API key doesn't have required permissions (403 Forbidden)")
            elif response.status_code == 429:
                pytest.skip("HERE API rate limit exceeded - key is valid but quota reached")
            
            response.raise_for_status()
            
            data = response.json()
            
            # Verify we got a valid response
            assert 'items' in data, "HERE API response missing 'items' field"
            assert len(data['items']) > 0, "HERE API returned no geocoding results"
            
            # Verify the result looks correct for San Francisco
            first_result = data['items'][0]
            assert 'position' in first_result, "HERE API result missing position data"
            assert 'lat' in first_result['position'], "HERE API result missing latitude"
            assert 'lng' in first_result['position'], "HERE API result missing longitude"
            
            # Basic sanity check - San Francisco coordinates
            lat = first_result['position']['lat']
            lng = first_result['position']['lng']
            assert 37 < lat < 38, f"San Francisco latitude seems wrong: {lat}"
            assert -123 < lng < -122, f"San Francisco longitude seems wrong: {lng}"
            
        except requests.exceptions.Timeout:
            pytest.fail(f"HERE API request timed out after {config.GEOCODING_TIMEOUT}s")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"HERE API connectivity test failed: {str(e)}")
        except Exception as e:
            pytest.fail(f"HERE API key validation failed: {str(e)}")
    
    def test_here_routing_api_connectivity(self):
        """Test if HERE API key works for routing service"""
        if not config.HERE_API_KEY:
            pytest.skip("No HERE_API_KEY configured - skipping routing connectivity test")
        
        try:
            # Test HERE Routing API with a simple route request
            url = "https://router.hereapi.com/v8/routes"
            params = {
                'origin': '37.7749,-122.4194',  # San Francisco
                'destination': '37.7849,-122.4094',  # Nearby location
                'transportMode': 'truck',
                'return': 'summary',
                'apikey': config.HERE_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=config.ROUTING_TIMEOUT)
            
            # Check if API key is valid
            if response.status_code == 401:
                pytest.fail("HERE API key is invalid for routing (401 Unauthorized)")
            elif response.status_code == 403:
                pytest.fail("HERE API key doesn't have routing permissions (403 Forbidden)")
            elif response.status_code == 429:
                pytest.skip("HERE API rate limit exceeded - key is valid but quota reached")
            
            response.raise_for_status()
            
            data = response.json()
            
            # Verify we got a valid routing response
            assert 'routes' in data, "HERE Routing API response missing 'routes' field"
            assert len(data['routes']) > 0, "HERE Routing API returned no routes"
            
            # Verify the route has expected data
            first_route = data['routes'][0]
            
            # Check if route has sections (new API structure)
            if 'sections' in first_route and len(first_route['sections']) > 0:
                # New API structure - summary is in sections
                first_section = first_route['sections'][0]
                assert 'summary' in first_section, "HERE Routing API section missing summary"
                summary = first_section['summary']
            else:
                # Old API structure - summary at route level
                assert 'summary' in first_route, "HERE Routing API route missing summary"
                summary = first_route['summary']
            
            assert 'length' in summary, "HERE Routing API summary missing length"
            assert summary['length'] > 0, "HERE Routing API returned zero-length route"
            
        except requests.exceptions.Timeout:
            pytest.fail(f"HERE Routing API request timed out after {config.ROUTING_TIMEOUT}s")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"HERE Routing API connectivity test failed: {str(e)}")
        except Exception as e:
            pytest.fail(f"HERE Routing API key validation failed: {str(e)}")

    @pytest.mark.slow
    def test_api_integration_workflow(self):
        """Test a complete workflow using both APIs"""
        if not config.GEMINI_API_KEY or not config.HERE_API_KEY:
            pytest.skip("Both API keys required for integration workflow test")
        
        try:
            # Test basic workflow: geocoding -> routing
            # This simulates what the actual system does
            
            # Step 1: Test geocoding
            url = "https://geocode.search.hereapi.com/v1/geocode"
            params = {
                'q': 'Los Angeles, CA',
                'apikey': config.HERE_API_KEY,
                'limit': 1
            }
            
            response = requests.get(url, params=params, timeout=config.GEOCODING_TIMEOUT)
            response.raise_for_status()
            
            geocode_data = response.json()
            assert len(geocode_data['items']) > 0, "Geocoding failed"
            
            origin = geocode_data['items'][0]['position']
            destination = {'lat': 32.7157, 'lng': -117.1611}  # San Diego
            
            # Step 2: Test routing between geocoded points
            routing_url = "https://router.hereapi.com/v8/routes"
            routing_params = {
                'origin': f"{origin['lat']},{origin['lng']}",
                'destination': f"{destination['lat']},{destination['lng']}",
                'transportMode': 'truck',
                'return': 'summary',
                'apikey': config.HERE_API_KEY
            }
            
            routing_response = requests.get(routing_url, params=routing_params, timeout=config.ROUTING_TIMEOUT)
            routing_response.raise_for_status()
            
            routing_data = routing_response.json()
            assert len(routing_data['routes']) > 0, "Routing failed"
            
            # Verify we got a reasonable distance (LA to San Diego ~120 miles)
            first_route = routing_data['routes'][0]
            
            # Handle both API response structures
            if 'sections' in first_route and len(first_route['sections']) > 0:
                # New API structure - summary is in sections
                route_length = first_route['sections'][0]['summary']['length']  # meters
            else:
                # Old API structure - summary at route level
                route_length = first_route['summary']['length']  # meters
                
            route_miles = route_length / 1609.34
            
            assert 100 < route_miles < 200, f"LA-SD route distance seems wrong: {route_miles} miles"
            
        except Exception as e:
            pytest.fail(f"API integration workflow failed: {str(e)}")


@pytest.mark.api
class TestAPIConfigurationIntegration:
    """Test that our modules properly use API keys from configuration"""
    
    def test_data_extractor_uses_config_api_key(self):
        """Test that GeminiDataExtractor uses API key from config"""
        if not config.GEMINI_API_KEY:
            pytest.skip("No GEMINI_API_KEY configured")
        
        try:
            from src.data_extractor import GeminiDataExtractor
            
            # Create extractor without providing API key - should use config
            extractor = GeminiDataExtractor()
            
            # Verify it has the model configured from config
            assert hasattr(extractor, 'model'), "Data extractor missing model attribute"
            
        except ImportError as e:
            pytest.skip(f"Skipping test due to missing dependencies: {e}")
        except Exception as e:
            # If API key is invalid, this will fail during initialization
            if "API" in str(e) and "key" in str(e).lower():
                pytest.fail(f"Data extractor failed to initialize with config API key: {e}")
            else:
                raise
    
    def test_geocoding_service_uses_config_api_key(self):
        """Test that GeocodingService uses API key from config"""
        try:
            from src.geocoding_service import GeocodingService
            
            # Create service without providing API key - should use config
            service = GeocodingService()
            
            # Check if it has the HERE API key (even if empty)
            assert hasattr(service, 'here_api_key'), "Geocoding service missing here_api_key attribute"
            assert service.here_api_key == config.HERE_API_KEY, "Geocoding service not using config API key"
            
        except ImportError as e:
            pytest.skip(f"Skipping test due to missing dependencies: {e}")
    
    def test_route_analyzer_uses_config_api_key(self):
        """Test that RouteAnalyzer uses API key from config"""
        try:
            from src.route_analyzer import RouteAnalyzer
            
            # Create analyzer without providing API key - should use config
            analyzer = RouteAnalyzer()
            
            # Check if it has the HERE API key (even if empty)
            assert hasattr(analyzer, 'here_api_key'), "Route analyzer missing here_api_key attribute"
            assert analyzer.here_api_key == config.HERE_API_KEY, "Route analyzer not using config API key"
            
        except ImportError as e:
            pytest.skip(f"Skipping test due to missing dependencies: {e}")
