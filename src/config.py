#!/usr/bin/env python3
"""
Centralized configuration module for the Driver Packet Processing system
Handles environment variables, default values, and configuration validation
"""

import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables once at module level
_env_loaded = False


def _load_environment():
    """Load environment variables from .env file once"""
    global _env_loaded
    if not _env_loaded:
        # Look for .env file in project root (parent of src directory)
        env_path = Path(__file__).parent.parent / ".env"
        load_dotenv(dotenv_path=env_path)
        _env_loaded = True


# Load environment on module import
_load_environment()


class Config:
    """
    Centralized configuration class with validation and default values
    """

    # =============================================================================
    # API CONFIGURATION
    # =============================================================================

    # Gemini API Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # HERE API Configuration
    HERE_API_KEY: str = os.getenv("HERE_API_KEY", "")

    # =============================================================================
    # TIMEOUT AND RETRY CONFIGURATION
    # =============================================================================

    # API Timeouts (seconds)
    GEMINI_TIMEOUT: int = int(os.getenv("GEMINI_TIMEOUT", "60"))
    GEOCODING_TIMEOUT: int = int(os.getenv("GEOCODING_TIMEOUT", "5"))
    ROUTING_TIMEOUT: int = int(os.getenv("ROUTING_TIMEOUT", "30"))
    REVERSE_GEOCODING_TIMEOUT: int = int(os.getenv("REVERSE_GEOCODING_TIMEOUT", "5"))

    # Retry Configuration
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: float = float(os.getenv("RETRY_DELAY", "1.0"))

    # Rate Limiting
    NOMINATIM_RATE_LIMIT: float = float(
        os.getenv("NOMINATIM_RATE_LIMIT", "1.0")
    )  # seconds between requests
    HERE_RATE_LIMIT: float = float(
        os.getenv("HERE_RATE_LIMIT", "0.1")
    )  # seconds between requests

    # =============================================================================
    # LOGGING CONFIGURATION
    # =============================================================================

    # Logging Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_DIR: str = os.getenv("LOG_DIR", "temp")
    LOG_FILE_MAX_BYTES: int = int(
        os.getenv("LOG_FILE_MAX_BYTES", str(5 * 1024 * 1024))
    )  # 5MB
    LOG_BACKUP_COUNT: int = int(
        os.getenv("LOG_BACKUP_COUNT", "7")
    )  # Keep 7 days of daily logs

    # Session Logging Settings
    LOG_SESSION_ENABLED: bool = (
        os.getenv("LOG_SESSION_ENABLED", "true").lower() == "true"
    )
    LOG_DAILY_ROTATION: bool = (
        os.getenv("LOG_DAILY_ROTATION", "false").lower() == "true"
    )  # Disabled by default
    LOG_SIZE_ROTATION: bool = (
        os.getenv("LOG_SIZE_ROTATION", "false").lower() == "true"
    )  # Disabled by default

    # Log Cleanup Settings
    LOG_SESSION_CLEANUP_DAYS: int = int(
        os.getenv("LOG_SESSION_CLEANUP_DAYS", "30")
    )  # Keep session logs for 30 days
    LOG_AUTO_CLEANUP: bool = os.getenv("LOG_AUTO_CLEANUP", "true").lower() == "true"

    # Console/Stream Redirection
    REDIRECT_STDOUT: bool = os.getenv("REDIRECT_STDOUT", "true").lower() == "true"
    REDIRECT_STDERR: bool = os.getenv("REDIRECT_STDERR", "true").lower() == "true"
    OVERRIDE_PRINT: bool = os.getenv("OVERRIDE_PRINT", "true").lower() == "true"

    # =============================================================================
    # PROCESSING CONFIGURATION
    # =============================================================================

    # Image Processing
    SUPPORTED_IMAGE_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png"]
    MAX_IMAGE_SIZE_MB: int = int(os.getenv("MAX_IMAGE_SIZE_MB", "50"))

    # Geocoding Configuration
    GEOCODING_CACHE_SIZE: int = int(os.getenv("GEOCODING_CACHE_SIZE", "1000"))
    USE_HERE_API_PREFERRED: bool = (
        os.getenv("USE_HERE_API_PREFERRED", "true").lower() == "true"
    )

    # Route Analysis Configuration
    MIN_STATE_MILES_THRESHOLD: float = float(
        os.getenv("MIN_STATE_MILES_THRESHOLD", "1.0")
    )
    ROUTE_SAMPLE_POINTS_MAX: int = int(os.getenv("ROUTE_SAMPLE_POINTS_MAX", "20"))

    # Distance Calculation
    GREAT_CIRCLE_EARTH_RADIUS_MILES: float = 3956.0
    METERS_TO_MILES_CONVERSION: float = 1609.34

    # =============================================================================
    # FILE AND PATH CONFIGURATION
    # =============================================================================

    # Default Paths
    DEFAULT_INPUT_DIR: str = os.getenv("DEFAULT_INPUT_DIR", "input")
    DEFAULT_OUTPUT_DIR: str = os.getenv("DEFAULT_OUTPUT_DIR", "output")
    DEFAULT_REFERENCE_CSV: str = os.getenv(
        "DEFAULT_REFERENCE_CSV", "input/driver - Sheet1.csv"
    )

    # State Boundary Data
    STATE_SHAPEFILE_PATH: str = os.getenv(
        "STATE_SHAPEFILE_PATH", "src/cb_2024_us_state_500k.shp"
    )

    # =============================================================================
    # VALIDATION AND QUALITY CONTROL
    # =============================================================================

    # Data Validation Thresholds
    MIN_DRIVER_NAME_LENGTH: int = int(os.getenv("MIN_DRIVER_NAME_LENGTH", "4"))
    MAX_TRIP_NUMBER: int = int(os.getenv("MAX_TRIP_NUMBER", "100"))
    MIN_TOTAL_MILES: int = int(os.getenv("MIN_TOTAL_MILES", "50"))
    MAX_TOTAL_MILES: int = int(os.getenv("MAX_TOTAL_MILES", "15000"))

    # Trailer Number Validation
    TRAILER_NUMBER_PREFIX: str = "2"  # Must start with 2 (200-299 range)
    TRAILER_NUMBER_LENGTH: int = 3

    # Fuel Purchase Validation
    MAX_GALLONS_PER_PURCHASE: float = float(
        os.getenv("MAX_GALLONS_PER_PURCHASE", "500.0")
    )
    MIN_GALLONS_PER_PURCHASE: float = float(
        os.getenv("MIN_GALLONS_PER_PURCHASE", "0.1")
    )

    # =============================================================================
    # OUTPUT CONFIGURATION
    # =============================================================================

    # Output Format Settings
    JSON_INDENT: int = int(os.getenv("JSON_INDENT", "2"))
    JSON_ENSURE_ASCII: bool = os.getenv("JSON_ENSURE_ASCII", "false").lower() == "true"

    # CSV Export Settings
    CSV_DELIMITER: str = os.getenv("CSV_DELIMITER", ",")
    CSV_ENCODING: str = os.getenv("CSV_ENCODING", "utf-8")

    @classmethod
    def validate_configuration(cls) -> Dict[str, Any]:
        """
        Validate the current configuration and return validation results

        Returns:
            Dictionary with validation status and any issues found
        """
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "missing_required": [],
            "configuration_summary": {},
        }

        # Check required API keys
        if not cls.GEMINI_API_KEY:
            validation_result["missing_required"].append("GEMINI_API_KEY")
            validation_result["errors"].append(
                "GEMINI_API_KEY is required for data extraction"
            )
            validation_result["is_valid"] = False

        if not cls.HERE_API_KEY:
            validation_result["warnings"].append(
                "HERE_API_KEY not configured - geocoding will use Nominatim fallback"
            )

        # Validate timeout values
        if cls.GEMINI_TIMEOUT < 10:
            validation_result["warnings"].append(
                f"GEMINI_TIMEOUT ({cls.GEMINI_TIMEOUT}s) is very low, may cause timeouts"
            )

        if cls.GEOCODING_TIMEOUT < 1:
            validation_result["warnings"].append(
                f"GEOCODING_TIMEOUT ({cls.GEOCODING_TIMEOUT}s) is very low"
            )

        # Validate retry configuration
        if cls.MAX_RETRIES > 10:
            validation_result["warnings"].append(
                f"MAX_RETRIES ({cls.MAX_RETRIES}) is very high"
            )

        if cls.RETRY_DELAY < 0.1:
            validation_result["warnings"].append(
                f"RETRY_DELAY ({cls.RETRY_DELAY}s) is very low"
            )

        # Validate thresholds
        if cls.MIN_TOTAL_MILES >= cls.MAX_TOTAL_MILES:
            validation_result["errors"].append(
                "MIN_TOTAL_MILES must be less than MAX_TOTAL_MILES"
            )
            validation_result["is_valid"] = False

        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if cls.LOG_LEVEL not in valid_log_levels:
            validation_result["warnings"].append(
                f'LOG_LEVEL "{cls.LOG_LEVEL}" not recognized, using INFO'
            )
            cls.LOG_LEVEL = "INFO"

        # Check file paths exist (for required files)
        required_paths = []  # Add paths that must exist
        for path_name, path_value in []:  # No required paths currently
            if not Path(path_value).exists():
                validation_result["warnings"].append(
                    f"{path_name} path does not exist: {path_value}"
                )

        # Configuration summary
        validation_result["configuration_summary"] = {
            "api_keys_configured": {
                "gemini": bool(cls.GEMINI_API_KEY),
                "here": bool(cls.HERE_API_KEY),
            },
            "timeout_settings": {
                "gemini": cls.GEMINI_TIMEOUT,
                "geocoding": cls.GEOCODING_TIMEOUT,
                "routing": cls.ROUTING_TIMEOUT,
            },
            "retry_settings": {
                "max_retries": cls.MAX_RETRIES,
                "retry_delay": cls.RETRY_DELAY,
            },
            "logging_configured": {
                "level": cls.LOG_LEVEL,
                "directory": cls.LOG_DIR,
                "max_file_size_mb": cls.LOG_FILE_MAX_BYTES / (1024 * 1024),
            },
            "validation_thresholds": {
                "total_miles_range": f"{cls.MIN_TOTAL_MILES}-{cls.MAX_TOTAL_MILES}",
                "min_driver_name_length": cls.MIN_DRIVER_NAME_LENGTH,
                "max_trip_number": cls.MAX_TRIP_NUMBER,
            },
        }

        return validation_result

    @classmethod
    def get_api_configuration(cls) -> Dict[str, Any]:
        """Get API-related configuration"""
        return {
            "gemini_api_key": cls.GEMINI_API_KEY,
            "gemini_model": cls.GEMINI_MODEL,
            "gemini_timeout": cls.GEMINI_TIMEOUT,
            "here_api_key": cls.HERE_API_KEY,
            "geocoding_timeout": cls.GEOCODING_TIMEOUT,
            "routing_timeout": cls.ROUTING_TIMEOUT,
            "max_retries": cls.MAX_RETRIES,
            "retry_delay": cls.RETRY_DELAY,
        }

    @classmethod
    def get_logging_configuration(cls) -> Dict[str, Any]:
        """Get logging-related configuration"""
        return {
            "log_level": cls.LOG_LEVEL,
            "log_dir": cls.LOG_DIR,
            "log_file_max_bytes": cls.LOG_FILE_MAX_BYTES,
            "log_backup_count": cls.LOG_BACKUP_COUNT,
            "redirect_stdout": cls.REDIRECT_STDOUT,
            "redirect_stderr": cls.REDIRECT_STDERR,
            "override_print": cls.OVERRIDE_PRINT,
        }

    @classmethod
    def get_processing_configuration(cls) -> Dict[str, Any]:
        """Get processing-related configuration"""
        return {
            "supported_extensions": cls.SUPPORTED_IMAGE_EXTENSIONS,
            "max_image_size_mb": cls.MAX_IMAGE_SIZE_MB,
            "geocoding_cache_size": cls.GEOCODING_CACHE_SIZE,
            "use_here_api_preferred": cls.USE_HERE_API_PREFERRED,
            "min_state_miles_threshold": cls.MIN_STATE_MILES_THRESHOLD,
            "route_sample_points_max": cls.ROUTE_SAMPLE_POINTS_MAX,
        }

    @classmethod
    def print_configuration_summary(cls) -> None:
        """Print a human-readable configuration summary"""
        validation = cls.validate_configuration()

        print("🔧 Driver Packet Processor Configuration")
        print("=" * 50)

        # API Configuration
        print("\n📡 API Configuration:")
        print(
            f"  Gemini API: {'✅ Configured' if cls.GEMINI_API_KEY else '❌ Missing'}"
        )
        print(
            f"  HERE API: {'✅ Configured' if cls.HERE_API_KEY else '⚠️ Not configured (will use fallback)'}"
        )
        print(f"  Gemini Model: {cls.GEMINI_MODEL}")

        # Timeout Configuration
        print("\n⏱️ Timeout Configuration:")
        print(f"  Gemini: {cls.GEMINI_TIMEOUT}s")
        print(f"  Geocoding: {cls.GEOCODING_TIMEOUT}s")
        print(f"  Routing: {cls.ROUTING_TIMEOUT}s")
        print(f"  Max Retries: {cls.MAX_RETRIES}")

        # Logging Configuration
        print("\n📝 Logging Configuration:")
        print(f"  Level: {cls.LOG_LEVEL}")
        print(f"  Directory: {cls.LOG_DIR}")
        print(f"  Max File Size: {cls.LOG_FILE_MAX_BYTES / (1024*1024):.1f}MB")

        # Validation Status
        print(
            f"\n✅ Configuration Status: {'Valid' if validation['is_valid'] else 'Invalid'}"
        )

        if validation["errors"]:
            print("\n❌ Errors:")
            for error in validation["errors"]:
                print(f"  - {error}")

        if validation["warnings"]:
            print("\n⚠️ Warnings:")
            for warning in validation["warnings"]:
                print(f"  - {warning}")

        if validation["missing_required"]:
            print("\n🔑 Missing Required Configuration:")
            for missing in validation["missing_required"]:
                print(f"  - {missing}")


# Create a singleton instance for easy access
config = Config()

# Validate configuration on import and store results
_validation_result = Config.validate_configuration()


# Expose validation result for other modules
def get_validation_result() -> Dict[str, Any]:
    """Get the configuration validation result"""
    return _validation_result


def is_configuration_valid() -> bool:
    """Check if the current configuration is valid"""
    return _validation_result["is_valid"]


def get_configuration_warnings() -> List[str]:
    """Get list of configuration warnings"""
    return _validation_result["warnings"]


def get_configuration_errors() -> List[str]:
    """Get list of configuration errors"""
    return _validation_result["errors"]
