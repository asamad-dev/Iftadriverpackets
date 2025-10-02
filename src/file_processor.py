#!/usr/bin/env python3
"""
File processor module
Handles batch processing of multiple driver packet images
"""

import os
import glob
import time
import json
from typing import List, Dict
from pathlib import Path

from .logging_utils import get_logger


class FileProcessor:
    """
    Process multiple driver packet images in batch with scalable data cleaning
    """

    def __init__(self, main_processor=None):
        """
        Initialize the file processor

        Args:
            main_processor: Main processor instance for processing individual images
        """
        self.logger = get_logger()
        self.main_processor = main_processor

        # Supported image extensions
        self.supported_extensions = ["*.jpg", "*.jpeg", "*.png"]

    def process_folder(
        self, input_folder: str, use_here_api: bool = True
    ) -> List[Dict]:
        """
        Process all images in a folder

        Args:
            input_folder: Folder containing driver packet images
            use_here_api: Whether to use HERE API for geocoding and routing

        Returns:
            List of dictionaries with processing results
        """
        try:
            results = []
            image_files = []

            # Find all image files in the input folder
            for ext in self.supported_extensions:
                image_files.extend(glob.glob(os.path.join(input_folder, ext)))

            if not image_files:
                self.logger.warning(f"No image files found in {input_folder}")
                return []

            self.logger.info(f"Found {len(image_files)} images to process")

            # Process each image
            for i, image_path in enumerate(image_files, 1):
                try:
                    self.logger.info(f"\n{'='*50}")
                    self.logger.info(
                        f"Processing {i}/{len(image_files)}: {os.path.basename(image_path)}..."
                    )

                    if self.main_processor:
                        result = self.main_processor.process_image_with_distances(
                            image_path, use_here_api
                        )
                    else:
                        self.logger.error("No main processor available")
                        result = {
                            "source_image": os.path.basename(image_path),
                            "processing_success": False,
                            "error": "No main processor available",
                        }

                    results.append(result)

                except Exception as e:
                    self.logger.error(f"Error processing {image_path}: {e}")
                    results.append(
                        {
                            "source_image": os.path.basename(image_path),
                            "processing_success": False,
                            "error": f"Processing error: {str(e)}",
                        }
                    )

            # Show summary of processing results
            successful = sum(1 for r in results if r.get("processing_success"))
            self.logger.info(
                f"\n✅ Successfully processed {successful}/{len(image_files)} images"
            )

            return results

        except Exception as e:
            self.logger.error(f"Error in process_folder: {e}")
            return [
                {
                    "processing_success": False,
                    "error": f"Batch processing error: {str(e)}",
                }
            ]

    def save_results_to_json(self, results: List[Dict], output_path: str) -> bool:
        """
        Save processing results to JSON file with timestamp

        Args:
            results: List of processing results
            output_path: Path to output directory

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create output directory if it doesn't exist
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"driver_packet_results_{timestamp}.json"
            filepath = output_dir / filename

            # Write results to JSON file
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Results saved to: {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving results to JSON: {e}")
            return False

    def filter_successful_results(self, results: List[Dict]) -> List[Dict]:
        """
        Filter out failed processing results

        Args:
            results: List of processing results

        Returns:
            List of successful results only
        """
        successful_results = [r for r in results if r.get("processing_success", False)]

        self.logger.info(
            f"Filtered {len(successful_results)} successful results from {len(results)} total"
        )

        return successful_results

    def get_processing_summary(self, results: List[Dict]) -> Dict:
        """
        Generate processing summary statistics

        Args:
            results: List of processing results

        Returns:
            Dictionary with summary statistics
        """
        summary = {
            "total_images": len(results),
            "successful_processing": 0,
            "failed_processing": 0,
            "geocoding_success": 0,
            "distance_calculations": 0,
            "reference_validations": 0,
            "common_errors": {},
            "validation_warnings_count": 0,
        }

        error_counts = {}

        for result in results:
            if result.get("processing_success"):
                summary["successful_processing"] += 1

                # Check geocoding success
                coords = result.get("coordinates", {})
                if (
                    coords
                    and coords.get("geocoding_summary", {}).get(
                        "successful_geocoding", 0
                    )
                    > 0
                ):
                    summary["geocoding_success"] += 1

                # Check distance calculations
                distances = result.get("distance_calculations", {})
                if distances and distances.get("calculation_success"):
                    summary["distance_calculations"] += 1

                # Check reference validation
                ref_validation = result.get("reference_validation", {})
                if ref_validation and ref_validation.get("reference_found"):
                    summary["reference_validations"] += 1

                # Count validation warnings
                warnings = result.get("validation_warnings", [])
                summary["validation_warnings_count"] += len(warnings)

            else:
                summary["failed_processing"] += 1

                # Track error types
                error = result.get("error", "Unknown error")
                error_type = self._categorize_error(error)
                error_counts[error_type] = error_counts.get(error_type, 0) + 1

        # Sort errors by frequency
        summary["common_errors"] = dict(
            sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        )

        # Calculate success rates
        if summary["total_images"] > 0:
            summary["processing_success_rate"] = (
                summary["successful_processing"] / summary["total_images"]
            )

            if summary["successful_processing"] > 0:
                summary["geocoding_success_rate"] = (
                    summary["geocoding_success"] / summary["successful_processing"]
                )
                summary["distance_calculation_rate"] = (
                    summary["distance_calculations"] / summary["successful_processing"]
                )
                summary["reference_validation_rate"] = (
                    summary["reference_validations"] / summary["successful_processing"]
                )

        self.logger.info(f"Processing Summary:")
        self.logger.info(f"  Total images: {summary['total_images']}")
        self.logger.info(
            f"  Successful processing: {summary['successful_processing']} ({summary.get('processing_success_rate', 0):.1%})"
        )
        self.logger.info(
            f"  Geocoding success: {summary['geocoding_success']} ({summary.get('geocoding_success_rate', 0):.1%})"
        )
        self.logger.info(
            f"  Distance calculations: {summary['distance_calculations']} ({summary.get('distance_calculation_rate', 0):.1%})"
        )
        self.logger.info(
            f"  Reference validations: {summary['reference_validations']} ({summary.get('reference_validation_rate', 0):.1%})"
        )

        if summary["common_errors"]:
            self.logger.warning(f"  Common errors:")
            for error_type, count in list(summary["common_errors"].items())[:5]:
                self.logger.warning(f"    {error_type}: {count}")

        return summary

    def _categorize_error(self, error_message: str) -> str:
        """Categorize error messages into types"""
        error_lower = error_message.lower()

        if "json" in error_lower or "parsing" in error_lower:
            return "JSON Parsing Error"
        elif "gemini" in error_lower or "api" in error_lower:
            return "Gemini API Error"
        elif "file" in error_lower and "not found" in error_lower:
            return "File Not Found"
        elif "geocoding" in error_lower:
            return "Geocoding Error"
        elif "distance" in error_lower or "route" in error_lower:
            return "Distance Calculation Error"
        elif "image" in error_lower:
            return "Image Processing Error"
        elif "timeout" in error_lower:
            return "Timeout Error"
        else:
            return "Other Error"

    def create_error_report(self, results: List[Dict], output_path: str) -> bool:
        """
        Create detailed error report for failed processing attempts

        Args:
            results: List of processing results
            output_path: Path to output directory

        Returns:
            True if successful, False otherwise
        """
        try:
            failed_results = [
                r for r in results if not r.get("processing_success", False)
            ]

            if not failed_results:
                self.logger.info("No errors to report - all processing was successful")
                return True

            # Create output directory if it doesn't exist
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate error report filename with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"processing_errors_{timestamp}.json"
            filepath = output_dir / filename

            # Create detailed error report
            error_report = {
                "report_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_errors": len(failed_results),
                "error_summary": self._get_error_summary(failed_results),
                "detailed_errors": failed_results,
            }

            # Write error report to JSON file
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(error_report, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Error report saved to: {filepath}")
            self.logger.info(f"Total errors reported: {len(failed_results)}")

            return True

        except Exception as e:
            self.logger.error(f"Error creating error report: {e}")
            return False

    def _get_error_summary(self, failed_results: List[Dict]) -> Dict:
        """Generate summary of error types and frequencies"""
        error_summary = {}

        for result in failed_results:
            error = result.get("error", "Unknown error")
            error_type = self._categorize_error(error)

            if error_type not in error_summary:
                error_summary[error_type] = {"count": 0, "examples": []}

            error_summary[error_type]["count"] += 1

            # Keep up to 3 examples of each error type
            if len(error_summary[error_type]["examples"]) < 3:
                error_summary[error_type]["examples"].append(
                    {"image": result.get("source_image", "Unknown"), "error": error}
                )

        # Sort by frequency
        sorted_summary = dict(
            sorted(error_summary.items(), key=lambda x: x[1]["count"], reverse=True)
        )

        return sorted_summary
