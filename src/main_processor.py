#!/usr/bin/env python3
"""
Main processor module
Orchestrates all other modules to provide complete driver packet processing
"""

import os
import time
from typing import Dict, List, Optional

from .logging_utils import setup_logging, get_logger
from .data_extractor import GeminiDataExtractor
from .geocoding_service import GeocodingService
from .route_analyzer import RouteAnalyzer
from .state_analyzer import StateAnalyzer
from .data_validator import DataValidator
from .reference_validator import ReferenceValidator
from .file_processor import FileProcessor


class DriverPacketProcessor:
    """
    Main processor that orchestrates all modules for complete driver packet processing
    """

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        here_api_key: Optional[str] = None,
        reference_csv_path: Optional[str] = None,
        setup_logging_config: bool = True,
    ):
        """
        Initialize the main processor with all sub-modules

        Args:
            gemini_api_key: Gemini API key for data extraction
            here_api_key: HERE API key for geocoding and routing
            reference_csv_path: Path to reference CSV for validation
            setup_logging_config: Whether to setup logging configuration
        """
        # Setup logging
        if setup_logging_config:
            self.logger = setup_logging()
        else:
            self.logger = get_logger()

        self.logger.info("Initializing Driver Packet Processor...")

        # Initialize all sub-modules
        try:
            # Data extraction
            self.data_extractor = GeminiDataExtractor(api_key=gemini_api_key)
            self.logger.info("✅ Data extractor initialized")

            # Geocoding service
            self.geocoding_service = GeocodingService(here_api_key=here_api_key)
            self.logger.info("✅ Geocoding service initialized")

            # Route analyzer
            self.route_analyzer = RouteAnalyzer(here_api_key=here_api_key)
            self.logger.info("✅ Route analyzer initialized")

            # State analyzer
            self.state_analyzer = StateAnalyzer(
                geocoding_service=self.geocoding_service
            )
            self.logger.info("✅ State analyzer initialized")

            # Data validator
            self.data_validator = DataValidator()
            self.logger.info("✅ Data validator initialized")

            # Reference validator
            self.reference_validator = ReferenceValidator(
                reference_csv_path=reference_csv_path
            )
            self.logger.info("✅ Reference validator initialized")

            # File processor
            self.file_processor = FileProcessor(main_processor=self)
            self.logger.info("✅ File processor initialized")

            self.logger.info("🚛 Driver Packet Processor ready for processing!")

        except Exception as e:
            self.logger.error(f"❌ Error initializing processor: {e}")
            raise

    def process_single_image(self, image_path: str, use_here_api: bool = True) -> Dict:
        """
        Process a single driver packet image through all stages

        Args:
            image_path: Path to the image file
            use_here_api: Whether to use HERE API for geocoding and routing

        Returns:
            Dictionary with complete processing results
        """
        try:
            self.logger.info(
                f"🚛 Starting complete processing of: {os.path.basename(image_path)}"
            )

            # Stage 1: Extract data from image
            self.logger.info("📝 Stage 1: Extracting data from image...")
            extraction_result = self.data_extractor.extract_data(image_path)

            if not extraction_result.get("extraction_success"):
                return {
                    "processing_success": False,
                    "stage_failed": "data_extraction",
                    "error": extraction_result.get("error", "Data extraction failed"),
                    "source_image": os.path.basename(image_path),
                }

            # Stage 2: Validate and correct extracted data
            self.logger.info("🔧 Stage 2: Validating and correcting data...")
            corrected_data, corrections = self.data_validator.validate_and_correct_data(
                extraction_result
            )
            validation_warnings = self.data_validator.validate_extracted_data(
                corrected_data
            )

            # Stage 3: Get coordinates for locations
            self.logger.info("🌍 Stage 3: Getting coordinates for locations...")
            coordinates_data = self.geocoding_service.get_coordinates_for_stops(
                corrected_data, use_here_api
            )

            # Stage 4: Calculate route distances
            self.logger.info("📏 Stage 4: Calculating route distances...")
            distance_data = self.route_analyzer.calculate_trip_distances(
                coordinates_data
            )

            # Stage 5: Analyze state mileage distribution
            self.logger.info("🗺️ Stage 5: Analyzing state mileage distribution...")
            polylines = (
                distance_data.get("trip_polylines", [])
                if distance_data.get("calculation_success")
                else []
            )
            enhanced_distance_data = self.state_analyzer.add_state_mileage_to_trip_data(
                distance_data, polylines
            )

            # Stage 6: Validate against reference data (if available)
            self.logger.info("🔍 Stage 6: Validating against reference data...")
            reference_validation = self.reference_validator.validate_against_reference(
                corrected_data
            )

            # Stage 7: Compare extracted vs calculated miles
            if corrected_data.get("total_miles") and enhanced_distance_data.get(
                "total_distance_miles"
            ):
                miles_comparison = self.route_analyzer.validate_distance_vs_extracted(
                    corrected_data.get("total_miles"),
                    enhanced_distance_data.get("total_distance_miles"),
                )
                if miles_comparison.get("warnings"):
                    validation_warnings.extend(miles_comparison["warnings"])

            # Compile final result
            result = {
                "processing_success": True,
                "processing_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source_image": os.path.basename(image_path),
                # Extracted and corrected data
                **corrected_data,
                # Processing metadata
                "corrections_applied": corrections,
                "validation_warnings": validation_warnings,
                # Coordinate information
                "coordinates": coordinates_data,
                # Distance calculations
                "distance_calculations": enhanced_distance_data,
                # Reference validation
                "reference_validation": reference_validation,
            }

            # Add summary statistics
            result["processing_summary"] = self._generate_processing_summary(result)

            self.logger.info(
                f"✅ Complete processing finished for {os.path.basename(image_path)}"
            )

            return result

        except Exception as e:
            self.logger.error(f"❌ Error in complete processing: {e}")
            return {
                "processing_success": False,
                "stage_failed": "unknown",
                "error": f"Processing error: {str(e)}",
                "source_image": os.path.basename(image_path),
            }

    def process_image_with_distances(
        self, image_path: str, use_here_api: bool = True
    ) -> Dict:
        """
        Alias for process_single_image for backward compatibility
        """
        return self.process_single_image(image_path, use_here_api)

    def process_multiple_images(
        self, input_folder: str, use_here_api: bool = True
    ) -> List[Dict]:
        """
        Process multiple images in a folder

        Args:
            input_folder: Folder containing driver packet images
            use_here_api: Whether to use HERE API for geocoding and routing

        Returns:
            List of processing results
        """
        self.logger.info(f"🚛 Starting batch processing of folder: {input_folder}")

        results = self.file_processor.process_folder(input_folder, use_here_api)

        # Generate batch summary
        summary = self.file_processor.get_processing_summary(results)
        self.logger.info("📊 Batch processing completed")

        return results

    def save_results(self, results: List[Dict], output_path: str) -> bool:
        """
        Save processing results to JSON file

        Args:
            results: List of processing results
            output_path: Output directory path

        Returns:
            True if successful
        """
        return self.file_processor.save_results_to_json(results, output_path)

    def create_error_report(self, results: List[Dict], output_path: str) -> bool:
        """
        Create detailed error report for failed processing

        Args:
            results: List of processing results
            output_path: Output directory path

        Returns:
            True if successful
        """
        return self.file_processor.create_error_report(results, output_path)

    def generate_accuracy_report(self, results: List[Dict]) -> Dict:
        """
        Generate accuracy report from multiple validation results

        Args:
            results: List of processing results with reference validation

        Returns:
            Dictionary with accuracy metrics
        """
        # Extract validation results
        validation_results = []
        for result in results:
            if result.get("reference_validation"):
                validation_results.append(result["reference_validation"])

        if not validation_results:
            self.logger.warning(
                "No reference validation results found for accuracy report"
            )
            return {}

        return self.reference_validator.generate_accuracy_report(validation_results)

    def _generate_processing_summary(self, result: Dict) -> Dict:
        """Generate summary of processing stages and their success"""
        summary = {
            "data_extraction": result.get("extraction_success", False),
            "data_validation": len(result.get("corrections_applied", [])),
            "geocoding": False,
            "distance_calculation": False,
            "state_analysis": False,
            "reference_validation": False,
        }

        # Check geocoding success
        coords = result.get("coordinates", {})
        if (
            coords
            and coords.get("geocoding_summary", {}).get("successful_geocoding", 0) > 0
        ):
            summary["geocoding"] = True

        # Check distance calculation
        distances = result.get("distance_calculations", {})
        if distances and distances.get("calculation_success"):
            summary["distance_calculation"] = True

            # Check state analysis
            state_mileage = distances.get("state_mileage", [])
            if state_mileage:
                summary["state_analysis"] = True

        # Check reference validation
        ref_validation = result.get("reference_validation", {})
        if ref_validation and ref_validation.get("reference_found"):
            summary["reference_validation"] = True

        return summary

    def get_coordinates_for_stops(
        self, extracted_data: Dict, use_here_api: bool = True
    ) -> Dict:
        """
        Get coordinates for all stops in the extracted data

        Args:
            extracted_data: Dictionary with extracted trip data
            use_here_api: If True, use HERE API; if False, use Nominatim

        Returns:
            Dictionary with coordinate information for each location field
        """
        return self.geocoding_service.get_coordinates_for_stops(
            extracted_data, use_here_api
        )

    def calculate_trip_distances(self, coordinates_data: Dict) -> Dict:
        """
        Calculate distances for all legs of a trip using coordinates

        Args:
            coordinates_data: Dictionary with coordinate information from geocoding service

        Returns:
            Dictionary with distance calculations for each leg
        """
        return self.route_analyzer.calculate_trip_distances(coordinates_data)

    def get_cache_stats(self) -> Dict:
        """Get statistics about cached data across all services"""
        stats = {"geocoding_cache": self.geocoding_service.get_cache_stats()}

        return stats

    def clear_caches(self) -> None:
        """Clear all caches"""
        self.geocoding_service.clear_cache()
        self.logger.info("All caches cleared")


# Convenience function for quick processing
def process_driver_packet(
    image_path: str,
    gemini_api_key: Optional[str] = None,
    here_api_key: Optional[str] = None,
    use_here_api: bool = True,
) -> Dict:
    """
    Convenience function to process a single driver packet image

    Args:
        image_path: Path to the image file
        gemini_api_key: Gemini API key
        here_api_key: HERE API key
        use_here_api: Whether to use HERE API

    Returns:
        Processing results dictionary
    """
    processor = DriverPacketProcessor(
        gemini_api_key=gemini_api_key, here_api_key=here_api_key
    )

    return processor.process_single_image(image_path, use_here_api)


# Convenience function for batch processing
def process_driver_packet_folder(
    input_folder: str,
    output_folder: str,
    gemini_api_key: Optional[str] = None,
    here_api_key: Optional[str] = None,
    use_here_api: bool = True,
) -> List[Dict]:
    """
    Convenience function to process a folder of driver packet images

    Args:
        input_folder: Folder containing images
        output_folder: Folder for output files
        gemini_api_key: Gemini API key
        here_api_key: HERE API key
        use_here_api: Whether to use HERE API

    Returns:
        List of processing results
    """
    processor = DriverPacketProcessor(
        gemini_api_key=gemini_api_key, here_api_key=here_api_key
    )

    # Process all images
    results = processor.process_multiple_images(input_folder, use_here_api)

    # Save results
    processor.save_results(results, output_folder)

    # Create error report if there were failures
    failed_results = [r for r in results if not r.get("processing_success")]
    if failed_results:
        processor.create_error_report(results, output_folder)

    # Generate accuracy report if reference validation was performed
    accuracy_report = processor.generate_accuracy_report(results)
    if accuracy_report:
        processor.logger.info("Accuracy report generated - check logs for details")

    return results
