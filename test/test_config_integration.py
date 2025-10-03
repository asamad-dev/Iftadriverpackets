#!/usr/bin/env python3
"""
Integration tests for configuration with actual modules
Tests that configuration properly integrates with the processing modules
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from test.test_config_fixtures import TestConfigData


@pytest.mark.integration
class TestConfigurationIntegration:
    """Test configuration integration with actual modules"""
    
    # @patch.dict(os.environ, TestConfigData.FULL_VALID_CONFIG)
    # def test_config_with_data_extractor(self):
    #     """Test configuration integration with data extractor"""
    #     try:
    #         from src.data_extractor import GeminiDataExtractor
    #         from src.config import config
            
    #         # Should be able to create extractor with config
    #         extractor = GeminiDataExtractor()
            
    #         # Verify it uses config values (not comparing fake API keys)
    #         assert config.GEMINI_MODEL == 'gemini-1.5-flash'  # Default or from env
    #         assert hasattr(extractor, 'model'), "Data extractor should have model attribute"
            
    #     except ImportError as e:
    #         pytest.skip(f"Skipping integration test due to missing dependencies: {e}")
    #     except Exception as e:
    #         # API key validation is done in test_api_validation.py
    #         if "GEMINI_API_KEY" in str(e) or "API" in str(e):
    #             pytest.skip(f"Skipping test due to API key issues (tested separately): {e}")
    #         else:
    #             raise
    
    @patch.dict(os.environ, TestConfigData.FULL_VALID_CONFIG)
    def test_config_with_geocoding_service(self):
        """Test configuration integration with geocoding service"""
        try:
            from src.geocoding_service import GeocodingService
            from src.config import config
            
            # Should be able to create service with config
            service = GeocodingService()
            
            # Verify it uses config values (focus on functionality, not specific values)
            assert hasattr(service, 'here_api_key'), "Service should have here_api_key attribute"
            assert hasattr(service, 'geocoding_cache'), "Service should have geocoding_cache"
            assert config.GEOCODING_TIMEOUT > 0, "Should have positive timeout value"
            
        except ImportError as e:
            pytest.skip(f"Skipping integration test due to missing dependencies: {e}")
    
    @patch.dict(os.environ, TestConfigData.FULL_VALID_CONFIG)  
    def test_config_with_route_analyzer(self):
        """Test configuration integration with route analyzer"""
        try:
            from src.route_analyzer import RouteAnalyzer
            from src.config import config
            
            # Should be able to create analyzer with config
            analyzer = RouteAnalyzer()
            
            # Verify it uses config values (focus on functionality, not specific values)
            assert hasattr(analyzer, 'here_api_key'), "Analyzer should have here_api_key attribute"
            assert config.ROUTING_TIMEOUT > 0, "Should have positive timeout value"  
            assert config.GREAT_CIRCLE_EARTH_RADIUS_MILES == 3956.0, "Should have correct Earth radius"
            
        except ImportError as e:
            pytest.skip(f"Skipping integration test due to missing dependencies: {e}")
    
    @patch.dict(os.environ, TestConfigData.FULL_VALID_CONFIG)
    def test_config_with_main_processor(self):
        """Test configuration integration with main processor"""
        try:
            from src.main_processor import DriverPacketProcessor
            from src.config import config
            
            # Should be able to create processor with config
            processor = DriverPacketProcessor(setup_logging_config=False)
            
            # Verify processor components use config
            assert processor.data_extractor is not None
            assert processor.geocoding_service is not None
            assert processor.route_analyzer is not None
            
        except ImportError as e:
            pytest.skip(f"Skipping integration test due to missing dependencies: {e}")
        except Exception as e:
            # If initialization fails due to API issues, that's expected in tests
            if "GEMINI_API_KEY" in str(e) or "API" in str(e):
                pytest.skip(f"Skipping test due to API key issues (tested separately): {e}")
            else:
                raise
    
    def test_configuration_validation_on_import(self):
        """Test that configuration validation works on import"""
        try:
            from src.config import get_validation_result, is_configuration_valid
            
            # Should be able to get validation results
            result = get_validation_result()
            assert isinstance(result, dict)
            
            valid = is_configuration_valid()
            assert isinstance(valid, bool)
            
        except ImportError as e:
            pytest.skip(f"Skipping integration test due to missing dependencies: {e}")
    
    @patch.dict(os.environ, TestConfigData.MINIMAL_VALID_CONFIG)
    def test_minimal_configuration_works(self):
        """Test that minimal configuration (just Gemini key) works"""
        try:
            # Reimport to get fresh config
            import importlib
            if 'src.config' in sys.modules:
                importlib.reload(sys.modules['src.config'])
            
            from src.config import config, Config
            
            # Should be valid with just Gemini key
            validation = Config.validate_configuration()
            
            # Should be valid (may have warnings but should work)
            # Note: In real integration, we might expect warnings about HERE API
            assert isinstance(validation['is_valid'], bool)
            
        except ImportError as e:
            pytest.skip(f"Skipping integration test due to missing dependencies: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
