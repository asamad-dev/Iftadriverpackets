#!/usr/bin/env python3
"""
Driver Packet Processor Package
A modular system for processing driver packet images using AI-powered OCR and geographic analysis
"""

from .main_processor import DriverPacketProcessor, process_driver_packet, process_driver_packet_folder
from .data_extractor import GeminiDataExtractor
from .geocoding_service import GeocodingService
from .route_analyzer import RouteAnalyzer
from .state_analyzer import StateAnalyzer
from .data_validator import DataValidator
from .reference_validator import ReferenceValidator
from .file_processor import FileProcessor
from .logging_utils import setup_logging, get_logger
from .config import config, Config

__version__ = "1.0.0"
__author__ = "Driver Packet Processing Team"

# Main classes for external use
__all__ = [
    # Main processor
    'DriverPacketProcessor',
    
    # Convenience functions
    'process_driver_packet',
    'process_driver_packet_folder',
    
    # Individual modules (for advanced use)
    'GeminiDataExtractor',
    'GeocodingService',
    'RouteAnalyzer', 
    'StateAnalyzer',
    'DataValidator',
    'ReferenceValidator',
    'FileProcessor',
    
    # Utilities
    'setup_logging',
    'get_logger',
    
    # Configuration
    'config',
    'Config'
]

# Package-level configuration
DEFAULT_LOG_LEVEL = "INFO"
SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png']
