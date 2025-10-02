#!/usr/bin/env python3
"""
Test configuration fixtures and utilities
Provides test data and utilities for configuration testing
"""

import os
import pytest
import tempfile
from unittest.mock import patch
from pathlib import Path


class TestConfigData:
    """Test data for configuration tests"""
    
    # Valid configuration sets for testing config loading and validation
    MINIMAL_VALID_CONFIG = {
        'GEMINI_API_KEY': 'test_key_minimal'  # Simple placeholder
    }
    
    FULL_VALID_CONFIG = {
        'GEMINI_API_KEY': 'test_key_full',  # Simple placeholder
        'HERE_API_KEY': 'test_here_key',    # Simple placeholder
        'GEMINI_TIMEOUT': '90',
        'GEOCODING_TIMEOUT': '10', 
        'ROUTING_TIMEOUT': '45',
        'MAX_RETRIES': '5',
        'RETRY_DELAY': '2.0',
        'LOG_LEVEL': 'DEBUG',
        'MIN_TOTAL_MILES': '25',
        'MAX_TOTAL_MILES': '20000',
        'ROUTE_SAMPLE_POINTS_MAX': '25'
    }
    
    # Invalid configuration sets
    INVALID_CONFIG_MISSING_GEMINI = {
        'HERE_API_KEY': 'test_here_key',  # Simple placeholder
        'GEMINI_TIMEOUT': '60'
    }
    
    INVALID_CONFIG_BAD_THRESHOLDS = {
        'GEMINI_API_KEY': 'test_key_thresholds',  # Simple placeholder
        'MIN_TOTAL_MILES': '20000',  # Higher than max
        'MAX_TOTAL_MILES': '15000'
    }
    
    INVALID_CONFIG_LOW_TIMEOUTS = {
        'GEMINI_API_KEY': 'test_key_timeouts',  # Simple placeholder
        'GEMINI_TIMEOUT': '5',  # Very low
        'GEOCODING_TIMEOUT': '0',  # Too low
        'MAX_RETRIES': '20'  # Too high
    }


@pytest.fixture
def clean_environment():
    """Fixture to provide clean environment for testing"""
    # Store original environment
    original_env = os.environ.copy()
    
    # Clear config-related environment variables
    config_vars = [
        'GEMINI_API_KEY', 'HERE_API_KEY', 'GEMINI_MODEL', 'GEMINI_TIMEOUT',
        'GEOCODING_TIMEOUT', 'ROUTING_TIMEOUT', 'MAX_RETRIES', 'RETRY_DELAY',
        'LOG_LEVEL', 'LOG_DIR', 'MIN_TOTAL_MILES', 'MAX_TOTAL_MILES',
        'ROUTE_SAMPLE_POINTS_MAX', 'MIN_STATE_MILES_THRESHOLD'
    ]
    
    for var in config_vars:
        if var in os.environ:
            del os.environ[var]
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def minimal_config_env():
    """Fixture with minimal valid configuration"""
    with patch.dict(os.environ, TestConfigData.MINIMAL_VALID_CONFIG):
        yield


@pytest.fixture  
def full_config_env():
    """Fixture with full valid configuration"""
    with patch.dict(os.environ, TestConfigData.FULL_VALID_CONFIG):
        yield


@pytest.fixture
def invalid_config_env():
    """Fixture with invalid configuration (missing Gemini key)"""
    with patch.dict(os.environ, TestConfigData.INVALID_CONFIG_MISSING_GEMINI):
        yield


@pytest.fixture
def temp_env_file():
    """Fixture to create temporary .env file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        env_content = f"""# Test environment file
GEMINI_API_KEY=test_key_from_file
HERE_API_KEY=test_here_key_from_file
GEMINI_TIMEOUT=90
LOG_LEVEL=DEBUG
MIN_TOTAL_MILES=25
"""
        f.write(env_content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


def create_test_env_file(content: str, temp_dir: Path) -> Path:
    """Create a temporary .env file with given content"""
    env_file = temp_dir / '.env'
    with open(env_file, 'w') as f:
        f.write(content)
    return env_file


def mock_config_with_values(**kwargs):
    """Create a mock configuration with specific values"""
    def mock_decorator(test_func):
        def wrapper(*args, **test_kwargs):
            with patch.dict(os.environ, kwargs):
                return test_func(*args, **test_kwargs)
        return wrapper
    return mock_decorator


class ConfigurationTestHelper:
    """Helper class for configuration testing"""
    
    @staticmethod
    def assert_valid_configuration(config_dict):
        """Assert that a configuration dictionary is valid"""
        assert 'is_valid' in config_dict
        assert 'warnings' in config_dict
        assert 'errors' in config_dict
        assert 'configuration_summary' in config_dict
        
        if not config_dict['is_valid']:
            print(f"Configuration errors: {config_dict['errors']}")
            print(f"Missing required: {config_dict.get('missing_required', [])}")
    
    @staticmethod
    def assert_has_warnings(config_dict, expected_warnings):
        """Assert that configuration has expected warnings"""
        warnings_text = ' '.join(config_dict['warnings'])
        for warning in expected_warnings:
            assert warning in warnings_text, f"Expected warning '{warning}' not found"
    
    @staticmethod
    def assert_has_errors(config_dict, expected_errors):
        """Assert that configuration has expected errors"""
        errors_text = ' '.join(config_dict['errors'])
        for error in expected_errors:
            assert error in errors_text, f"Expected error '{error}' not found"
    
    @staticmethod
    def print_config_debug(config_dict):
        """Print configuration for debugging"""
        print("\n=== Configuration Debug ===")
        print(f"Valid: {config_dict['is_valid']}")
        print(f"Warnings: {config_dict['warnings']}")
        print(f"Errors: {config_dict['errors']}")
        print(f"Missing: {config_dict.get('missing_required', [])}")
        print("===========================\n")
