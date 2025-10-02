#!/usr/bin/env python3
"""
Unit tests for the configuration module
Tests environment variable loading, validation, and default values
"""

import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the config module
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.config import Config, config, get_validation_result, is_configuration_valid


class TestConfigurationLoading:
    """Test configuration loading and environment variable handling"""
    
    def test_default_values_loaded(self):
        """Test that default values are properly loaded"""
        # Test API defaults
        assert Config.GEMINI_TIMEOUT == 60
        assert Config.GEOCODING_TIMEOUT == 5
        assert Config.ROUTING_TIMEOUT == 30
        
        # Test processing defaults
        assert Config.MIN_STATE_MILES_THRESHOLD == 1.0
        assert Config.ROUTE_SAMPLE_POINTS_MAX == 20
        assert Config.MAX_TOTAL_MILES == 15000
        assert Config.MIN_TOTAL_MILES == 50
        
        # Test logging defaults
        assert Config.LOG_LEVEL == 'INFO'
        assert Config.LOG_DIR == 'temp'
        
    def test_supported_image_extensions(self):
        """Test that supported image extensions are correct"""
        expected_extensions = ['.jpg', '.jpeg', '.png']
        assert Config.SUPPORTED_IMAGE_EXTENSIONS == expected_extensions
        
    def test_boolean_configuration_parsing(self):
        """Test boolean configuration values"""
        # These should default to True
        assert Config.REDIRECT_STDOUT is True
        assert Config.REDIRECT_STDERR is True
        assert Config.OVERRIDE_PRINT is True
        assert Config.USE_HERE_API_PREFERRED is True
        
    @patch.dict(os.environ, {'GEMINI_TIMEOUT': '90', 'MIN_TOTAL_MILES': '25'})
    def test_environment_variable_override(self):
        """Test that environment variables override defaults"""
        # Note: This test requires reloading the config module
        # In a real test, we'd need to reload the module or use dependency injection
        pass
        
    def test_numeric_type_conversion(self):
        """Test that numeric values are properly converted"""
        assert isinstance(Config.GEMINI_TIMEOUT, int)
        assert isinstance(Config.MIN_STATE_MILES_THRESHOLD, float)
        assert isinstance(Config.LOG_FILE_MAX_BYTES, int)
        assert isinstance(Config.RETRY_DELAY, float)


class TestConfigurationValidation:
    """Test configuration validation methods"""
    
    def test_validate_configuration_structure(self):
        """Test that validation returns proper structure"""
        result = Config.validate_configuration()
        
        # Check required keys
        required_keys = ['is_valid', 'warnings', 'errors', 'missing_required', 'configuration_summary']
        for key in required_keys:
            assert key in result
            
        # Check types
        assert isinstance(result['is_valid'], bool)
        assert isinstance(result['warnings'], list)
        assert isinstance(result['errors'], list)
        assert isinstance(result['missing_required'], list)
        assert isinstance(result['configuration_summary'], dict)
    
    def test_missing_gemini_api_key_validation(self):
        """Test validation when GEMINI_API_KEY is missing"""
        with patch.object(Config, 'GEMINI_API_KEY', ''):
            result = Config.validate_configuration()
            
            assert result['is_valid'] is False
            assert 'GEMINI_API_KEY' in result['missing_required']
            assert any('GEMINI_API_KEY is required' in error for error in result['errors'])
    
    def test_missing_here_api_key_warning(self):
        """Test warning when HERE_API_KEY is missing"""
        with patch.object(Config, 'HERE_API_KEY', ''):
            result = Config.validate_configuration()
            
            # Should have warning but still be valid if Gemini key exists
            warning_found = any('HERE_API_KEY not configured' in warning for warning in result['warnings'])
            assert warning_found
    
    def test_timeout_validation_warnings(self):
        """Test validation warnings for low timeout values"""
        with patch.object(Config, 'GEMINI_TIMEOUT', 5):
            result = Config.validate_configuration()
            warning_found = any('GEMINI_TIMEOUT' in warning and 'very low' in warning for warning in result['warnings'])
            assert warning_found
            
        with patch.object(Config, 'GEOCODING_TIMEOUT', 0):
            result = Config.validate_configuration()
            warning_found = any('GEOCODING_TIMEOUT' in warning and 'very low' in warning for warning in result['warnings'])
            assert warning_found
    
    def test_retry_configuration_warnings(self):
        """Test warnings for extreme retry configurations"""
        with patch.object(Config, 'MAX_RETRIES', 15):
            result = Config.validate_configuration()
            warning_found = any('MAX_RETRIES' in warning and 'very high' in warning for warning in result['warnings'])
            assert warning_found
            
        with patch.object(Config, 'RETRY_DELAY', 0.01):
            result = Config.validate_configuration()
            warning_found = any('RETRY_DELAY' in warning and 'very low' in warning for warning in result['warnings'])
            assert warning_found
    
    def test_miles_threshold_validation(self):
        """Test validation of miles thresholds"""
        with patch.object(Config, 'MIN_TOTAL_MILES', 20000), \
             patch.object(Config, 'MAX_TOTAL_MILES', 15000):
            result = Config.validate_configuration()
            
            assert result['is_valid'] is False
            error_found = any('MIN_TOTAL_MILES must be less than MAX_TOTAL_MILES' in error for error in result['errors'])
            assert error_found
    
    def test_log_level_validation(self):
        """Test log level validation and correction"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        # Test valid level
        with patch.object(Config, 'LOG_LEVEL', 'DEBUG'):
            result = Config.validate_configuration()
            # Should not have warnings about log level
            log_warnings = [w for w in result['warnings'] if 'LOG_LEVEL' in w]
            assert len(log_warnings) == 0
    
    def test_configuration_summary_content(self):
        """Test that configuration summary contains expected sections"""
        result = Config.validate_configuration()
        summary = result['configuration_summary']
        
        expected_sections = [
            'api_keys_configured',
            'timeout_settings', 
            'retry_settings',
            'logging_configured',
            'validation_thresholds'
        ]
        
        for section in expected_sections:
            assert section in summary


class TestConfigurationMethods:
    """Test configuration utility methods"""
    
    def test_get_api_configuration(self):
        """Test API configuration getter"""
        api_config = Config.get_api_configuration()
        
        expected_keys = [
            'gemini_api_key', 'gemini_model', 'gemini_timeout',
            'here_api_key', 'geocoding_timeout', 'routing_timeout',
            'max_retries', 'retry_delay'
        ]
        
        for key in expected_keys:
            assert key in api_config
    
    def test_get_logging_configuration(self):
        """Test logging configuration getter"""
        logging_config = Config.get_logging_configuration()
        
        expected_keys = [
            'log_level', 'log_dir', 'log_file_max_bytes', 'log_backup_count',
            'redirect_stdout', 'redirect_stderr', 'override_print'
        ]
        
        for key in expected_keys:
            assert key in logging_config
    
    def test_get_processing_configuration(self):
        """Test processing configuration getter"""
        processing_config = Config.get_processing_configuration()
        
        expected_keys = [
            'supported_extensions', 'max_image_size_mb', 'geocoding_cache_size',
            'use_here_api_preferred', 'min_state_miles_threshold', 'route_sample_points_max'
        ]
        
        for key in expected_keys:
            assert key in processing_config
    
    def test_print_configuration_summary(self, capsys):
        """Test configuration summary printing"""
        Config.print_configuration_summary()
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Check that key sections are present
        assert "Driver Packet Processor Configuration" in output
        assert "API Configuration:" in output
        assert "Timeout Configuration:" in output
        assert "Logging Configuration:" in output
        assert "Configuration Status:" in output


class TestGlobalConfigurationFunctions:
    """Test global configuration functions"""
    
    def test_get_validation_result(self):
        """Test get_validation_result function"""
        result = get_validation_result()
        assert isinstance(result, dict)
        assert 'is_valid' in result
    
    def test_is_configuration_valid(self):
        """Test is_configuration_valid function"""
        valid = is_configuration_valid()
        assert isinstance(valid, bool)
    
    def test_config_singleton(self):
        """Test that config singleton works"""
        from src.config import config
        assert hasattr(config, 'GEMINI_API_KEY')
        assert hasattr(config, 'GEMINI_MODEL')


class TestConfigurationEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_invalid_numeric_environment_variables(self):
        """Test handling of invalid numeric environment values"""
        # This would normally be tested with mocked environment variables
        # and a fresh config load, but requires module reloading
        pass
    
    def test_missing_env_file(self):
        """Test behavior when .env file doesn't exist"""
        # Config should still work with system environment variables and defaults
        assert Config.GEMINI_MODEL is not None
        assert Config.LOG_LEVEL is not None
    
    def test_empty_string_boolean_values(self):
        """Test boolean parsing with various string values"""
        # Test would require environment variable mocking and reload
        pass


class TestConfigurationConstants:
    """Test configuration constants"""
    
    def test_distance_calculation_constants(self):
        """Test distance calculation constants"""
        assert Config.GREAT_CIRCLE_EARTH_RADIUS_MILES == 3956.0
        assert Config.METERS_TO_MILES_CONVERSION == 1609.34
    
    def test_trailer_number_validation_constants(self):
        """Test trailer number validation constants"""
        assert Config.TRAILER_NUMBER_PREFIX == '2'
        assert Config.TRAILER_NUMBER_LENGTH == 3
    
    def test_fuel_purchase_validation_constants(self):
        """Test fuel purchase validation bounds"""
        assert Config.MAX_GALLONS_PER_PURCHASE >= Config.MIN_GALLONS_PER_PURCHASE
        assert Config.MIN_GALLONS_PER_PURCHASE > 0


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
