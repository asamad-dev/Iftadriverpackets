#!/usr/bin/env python3
import os
import json
import csv
from datetime import datetime
from dotenv import load_dotenv
from gemini_processor import GeminiDriverPacketProcessor
import sys, traceback

# Load environment variables from .env file (look in parent directory)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# Removed unused test functions - keeping it simple


def show_available_images():
    """
    Show all available images in the input folder and let user select one
    Returns: Selected image path or None if cancelled
    """
    input_folder = os.path.join(os.path.dirname(__file__), "..", "input")

    if not os.path.exists(input_folder):
        print(f"❌ Input folder not found: {input_folder}")
        return None

    # Get all image files
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
    image_files = [
        f
        for f in os.listdir(input_folder)
        if os.path.splitext(f.lower())[1] in image_extensions
    ]

    if not image_files:
        print(f"❌ No image files found in: {input_folder}")
        return None

    print(f"\n📁 Available Images in Input Folder:")
    print("-" * 50)

    for i, filename in enumerate(image_files, 1):
        file_path = os.path.join(input_folder, filename)
        try:
            # Get file size for display
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"{i:2d}. {filename} ({size_mb:.1f} MB)")
        except:
            print(f"{i:2d}. {filename}")

    print(f" 0. Cancel")

    while True:
        try:
            choice = input(
                f"\nSelect image (1-{len(image_files)} or 0 to cancel): "
            ).strip()

            if choice == "0":
                return None

            choice_num = int(choice)
            if 1 <= choice_num <= len(image_files):
                selected_file = image_files[choice_num - 1]
                selected_path = os.path.join(input_folder, selected_file)
                print(f"✅ Selected: {selected_file}")
                return selected_path
            else:
                print(
                    f"❌ Please enter a number between 1 and {len(image_files)} (or 0 to cancel)"
                )

        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n👋 Cancelled by user")
            return None


def process_single_image_complete(image_path: str):
    """
    Process a single image with full extraction including coordinates and distances
    """
    print(f"\n🖼️  Processing Single Image: {os.path.basename(image_path)}")
    print("-" * 60)

    try:
        processor = GeminiDriverPacketProcessor()
        print("✅ Processor initialized")
    except Exception as e:

        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = traceback.extract_tb(exc_tb)[-1][0]
        line_no = traceback.extract_tb(exc_tb)[-1][1]
        print(
            f"❌ Failed to initialize processor: {e} at line {line_no} in {os.path.basename(fname)}"
        )
        traceback.print_exc()
        return None

    processor = GeminiDriverPacketProcessor()
    result = processor.process_image_with_distances(image_path)

    if result.get("processing_success"):
        print(f"\n✅ Processing successful!")

        # Create JSON summary for extracted fields
        print("\n💾 Saving extraction data...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"extraction_{timestamp}.json"

        # Ensure output dir exists
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(image_path)), "output"
        )
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, output_filename)

        with open(output_path, "w") as f:
            json.dump(result, f, indent=4)

        print(f"\n💾 Output saved: {output_path}")

        # Show extraction summary
        # The extracted data is directly in the result dictionary, not under 'extraction_data' key
        fields_data = result

        # Count populated fields in the result
        populated_fields = sum(
            1
            for k, v in result.items()
            if v
            and str(v).strip()
            and k not in ["source_image", "processing_success", "error"]
        )
        print(f"\n📊 Extraction Summary:")
        print(f"   Populated fields: {populated_fields}")

        # Show geocoding summary if available
        if "geocoding_summary" in result:
            summary = result["geocoding_summary"]
            successful = summary.get("successful_geocoding", 0)
            total = summary.get("total_locations", 0)
            # Calculate success rate if it's not provided
            if "success_rate" in summary:
                success_rate = summary["success_rate"]
            else:
                success_rate = successful / total if total > 0 else 0

            print(f"   Locations geocoded: {successful}/{total} ({success_rate:.1%})")

        # Show distance summary if available
        if "total_distance_miles" in result:
            print(f"   Total route distance: {result['total_distance_miles']} miles")

            # Show state mileage if available
            if "state_mileage" in result:
                print(f"\n🇺🇸 State Mileage Breakdown:")
                for state_data in result.get("state_mileage", []):
                    print(
                        f"   {state_data['state']}: {state_data['miles']} miles ({state_data['percentage']}%)"
                    )

        # Show validation results if available
        if "reference_validation" in result and result["reference_validation"].get(
            "validation_success"
        ):
            validation = result["reference_validation"]
            accuracy = validation.get("accuracy_metrics", {})

            print(f"\n📊 Reference Validation Results:")
            print(f"   Reference data found: ✅")
            print(f"   Field accuracy: {accuracy.get('field_accuracy', 0):.1%}")
            print(f"   Total discrepancies: {accuracy.get('total_discrepancies', 0)}")

            if accuracy.get("critical_discrepancies", 0) > 0:
                print(
                    f"   🔴 Critical discrepancies: {accuracy.get('critical_discrepancies', 0)}"
                )
            if accuracy.get("high_discrepancies", 0) > 0:
                print(
                    f"   🟠 High severity discrepancies: {accuracy.get('high_discrepancies', 0)}"
                )
            if accuracy.get("medium_discrepancies", 0) > 0:
                print(
                    f"   🟡 Medium severity discrepancies: {accuracy.get('medium_discrepancies', 0)}"
                )
            if accuracy.get("low_discrepancies", 0) > 0:
                print(
                    f"   🔵 Low severity discrepancies: {accuracy.get('low_discrepancies', 0)}"
                )

        # Show warnings if any
        if "validation_warnings" in result and result["validation_warnings"]:
            print(f"\n⚠️ Validation Warnings:")
            for warning in result["validation_warnings"]:
                print(f"   - {warning}")
    else:
        print(f"\n❌ Processing failed: {result.get('error', 'Unknown error')}")

    return result


def process_batch_complete():
    """
    Process all images in the input folder with extraction according to plan.md
    """
    print(f"\n📁 Batch Processing - All Images")
    print("-" * 50)

    try:
        processor = GeminiDriverPacketProcessor()
        print("✅ Processor initialized")
    except Exception as e:
        print(f"❌ Failed to initialize processor: {e}")
        return

    input_folder = os.path.join(os.path.dirname(__file__), "..", "input")

    # Check if HERE API is available
    here_available = os.environ.get("HERE_API_KEY") is not None
    api_name = (
        "HERE (with distance calculation)"
        if here_available
        else "Nominatim (coordinates only)"
    )
    print(f"🌍 Using {api_name} for all images")

    # Process all images
    results = processor.process_multiple_images(
        input_folder, use_here_api=here_available
    )

    if not results:
        print("❌ No images processed")
        return

    # Create output directory
    output_folder = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_folder, exist_ok=True)

    # Generate timestamp-based filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save detailed JSON results
    json_output_path = os.path.join(
        output_folder, f"batch_results_complete_{timestamp}.json"
    )
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Create state mileage CSV (as per plan.md)
    csv_output_path = os.path.join(
        output_folder, f"batch_state_mileage_{timestamp}.csv"
    )

    # Create detailed CSV (with all extraction data)
    detailed_csv_path = os.path.join(output_folder, f"batch_detailed_{timestamp}.csv")

    if results:
        # Create both CSV files
        create_csv_summary(results, csv_output_path)
        create_detailed_csv(results, detailed_csv_path)

    # Print summary
    print(f"\n💾 Results saved:")
    print(f"   📄 State Mileage CSV: {os.path.basename(csv_output_path)}")
    print(f"   📄 Detailed CSV: {os.path.basename(detailed_csv_path)}")
    print(f"   📄 JSON Details: {os.path.basename(json_output_path)}")
    print(f"   📂 Location: {output_folder}")

    # Print statistics
    successful_extractions = [r for r in results if r.get("processing_success")]
    if successful_extractions:
        total_geocoding_success = sum(
            r.get("geocoding_summary", {}).get("successful_geocoding", 0)
            for r in successful_extractions
        )
        total_locations = sum(
            r.get("geocoding_summary", {}).get("total_locations", 0)
            for r in successful_extractions
        )

        if total_locations > 0:
            print(
                f"   📍 Locations geocoded: {total_geocoding_success}/{total_locations} ({total_geocoding_success/total_locations:.1%})"
            )

    # Print distance calculation statistics
    distance_success = sum(
        1
        for r in results
        if "distance_calculations" in r
        and r["distance_calculations"].get("calculation_success")
    )
    if distance_success > 0:
        print(
            f"   📏 Distance calculations successful: {distance_success}/{len(results)}"
        )

    # Print validation statistics
    validation_results = [
        r
        for r in results
        if r.get("reference_validation", {}).get("validation_success")
    ]
    if validation_results:
        total_field_accuracy = sum(
            r.get("reference_validation", {})
            .get("accuracy_metrics", {})
            .get("field_accuracy", 0)
            for r in validation_results
        )
        avg_field_accuracy = total_field_accuracy / len(validation_results)

        total_discrepancies = sum(
            r.get("reference_validation", {})
            .get("accuracy_metrics", {})
            .get("total_discrepancies", 0)
            for r in validation_results
        )
        total_critical = sum(
            r.get("reference_validation", {})
            .get("accuracy_metrics", {})
            .get("critical_discrepancies", 0)
            for r in validation_results
        )
        total_high = sum(
            r.get("reference_validation", {})
            .get("accuracy_metrics", {})
            .get("high_discrepancies", 0)
            for r in validation_results
        )

        print(f"\n📊 Validation Summary:")
        print(
            f"   Images with reference data: {len(validation_results)}/{len(results)}"
        )
        print(f"   Average field accuracy: {avg_field_accuracy:.1%}")
        print(f"   Total discrepancies: {total_discrepancies}")
        if total_critical > 0:
            print(f"   🔴 Critical discrepancies: {total_critical}")
        if total_high > 0:
            print(f"   🟠 High severity discrepancies: {total_high}")

    warnings_count = sum(
        1 for r in results if "validation_warnings" in r and r["validation_warnings"]
    )
    if warnings_count > 0:
        print(f"   ⚠️  Images with warnings: {warnings_count}")

    print(f"\n💾 Output files saved:")
    print(
        f"   📄 State Mileage CSV: {os.path.basename(csv_output_path)} (as per plan.md)"
    )
    print(
        f"   📄 Detailed CSV: {os.path.basename(detailed_csv_path)} (all extraction data)"
    )
    print(f"   📄 JSON Details: {os.path.basename(json_output_path)}")
    print(f"   📂 Location: {output_folder}")

    return results, csv_output_path, json_output_path


def show_menu():
    """
    Show simplified menu with batch, single image, and validation test options
    """
    print("\n🚛 Driver Packet Processing")
    print("=" * 30)
    print("1. Process All Images (Batch)")
    print("2. Process Single Image")
    print("3. Test Validation Accuracy")
    print("0. Exit")

    choice = input("\nEnter your choice (0-3): ").strip()
    return choice


def _format_drop_off_for_csv(drop_off_value):
    """
    Format drop_off value for CSV output (handle both string and array formats)

    Args:
        drop_off_value: String or array of drop-off locations

    Returns:
        String representation for CSV
    """
    if isinstance(drop_off_value, list):
        return " | ".join(drop_off_value)
    return drop_off_value


def create_csv_summary(results, csv_output_path):
    """
    Create a CSV summary focusing on state mileage breakdown as per plan.md
    Format: source_image, State Initials, Mileage in state

    Args:
        results: List of processing results
        csv_output_path: Path to save the CSV file
    """
    if not results:
        return

    # Collect all unique states from all results
    all_states = set()
    for result in results:
        if result.get("processing_success"):
            # Check for state mileage in distance_calculations
            if (
                "distance_calculations" in result
                and "state_mileage" in result["distance_calculations"]
            ):
                for state_data in result["distance_calculations"]["state_mileage"]:
                    all_states.add(state_data["state"])
            # Also check for state_mileage at root level
            elif "state_mileage" in result:
                for state_data in result["state_mileage"]:
                    all_states.add(state_data["state"])

    # Create field order: source_image + sorted state abbreviations
    field_order = ["source_image"] + sorted(all_states)

    with open(csv_output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_order, extrasaction="ignore")
        writer.writeheader()

        for result in results:
            if not result.get("processing_success", False):
                # Add basic failure info - only source_image, states will be empty
                writer.writerow(
                    {"source_image": result.get("source_image", "PROCESSING_FAILED")}
                )
                continue

            # Initialize row data with source image
            row_data = {"source_image": result.get("source_image", "")}

            # Add state mileage data
            state_mileage_data = None

            # Check distance_calculations first
            if (
                "distance_calculations" in result
                and "state_mileage" in result["distance_calculations"]
            ):
                state_mileage_data = result["distance_calculations"]["state_mileage"]
            # Fallback to root level
            elif "state_mileage" in result:
                state_mileage_data = result["state_mileage"]

            if state_mileage_data:
                for state_data in state_mileage_data:
                    state = state_data["state"]
                    miles = state_data.get("miles", 0)
                    if state in all_states:
                        row_data[state] = miles

            writer.writerow(row_data)

    print(f"CSV summary created (state mileage format): {csv_output_path}")
    print(f"   States included: {', '.join(sorted(all_states))}")


def create_detailed_csv(results, csv_output_path):
    """
    Create a detailed CSV with all extracted fields (backup/detailed view)

    Args:
        results: List of processing results
        csv_output_path: Path to save the detailed CSV file
    """
    if not results:
        return

    # Define fields to include in detailed CSV
    field_order = [
        "source_image",
        "processing_success",
        "drivers_name",
        "unit",
        "trailer",
        "date_trip_started",
        "date_trip_ended",
        "trip",
        "trip_started_from",
        "first_drop",
        "second_drop",
        "third_drop",
        "forth_drop",
        "inbound_pu",
        "drop_off",
        "total_miles",
        "geocoded_locations",
        "total_distance_miles",
    ]

    # Add state mileage columns if present
    all_states = set()
    for result in results:
        if result.get("processing_success"):
            # Check for state mileage in distance_calculations
            if (
                "distance_calculations" in result
                and "state_mileage" in result["distance_calculations"]
            ):
                for state_data in result["distance_calculations"]["state_mileage"]:
                    all_states.add(state_data["state"])
            # Also check for state_mileage at root level
            elif "state_mileage" in result:
                for state_data in result["state_mileage"]:
                    all_states.add(state_data["state"])

    # Add states to field order
    for state in sorted(all_states):
        field_order.append(f"miles_{state}")

    with open(csv_output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_order, extrasaction="ignore")
        writer.writeheader()

        for result in results:
            if not result.get("processing_success", False):
                # Add basic failure info
                writer.writerow(
                    {
                        "source_image": result.get("source_image", ""),
                        "processing_success": False,
                    }
                )
                continue

            # Extract fields from result data (all fields are at root level)
            row_data = {
                "source_image": result.get("source_image", ""),
                "processing_success": True,
                "drivers_name": result.get("drivers_name", ""),
                "unit": result.get("unit", ""),
                "trailer": result.get("trailer", ""),
                "date_trip_started": result.get("date_trip_started", ""),
                "date_trip_ended": result.get("date_trip_ended", ""),
                "trip": result.get("trip", ""),
                "trip_started_from": result.get("trip_started_from", ""),
                "first_drop": result.get("first_drop", ""),
                "second_drop": result.get("second_drop", ""),
                "third_drop": result.get("third_drop", ""),
                "forth_drop": result.get("forth_drop", ""),
                "inbound_pu": result.get("inbound_pu", ""),
                "drop_off": _format_drop_off_for_csv(result.get("drop_off", "")),
                "total_miles": result.get("total_miles", ""),
            }

            # Add geocoding info
            if "geocoding_summary" in result:
                row_data["geocoded_locations"] = result["geocoding_summary"].get(
                    "successful_geocoding", 0
                )

            # Add distance calculations if available
            if (
                "distance_calculations" in result
                and "total_distance_miles" in result["distance_calculations"]
            ):
                row_data["total_distance_miles"] = result["distance_calculations"].get(
                    "total_distance_miles", 0
                )

                # Add state mileage breakdown
                if "state_mileage" in result["distance_calculations"]:
                    for state_data in result["distance_calculations"]["state_mileage"]:
                        state = state_data["state"]
                        miles = state_data["miles"]
                        row_data[f"miles_{state}"] = miles
            # Check root level for backwards compatibility
            elif "total_distance_miles" in result:
                row_data["total_distance_miles"] = result.get("total_distance_miles", 0)

                if "state_mileage" in result:
                    for state_data in result["state_mileage"]:
                        state = state_data["state"]
                        miles = state_data["miles"]
                        row_data[f"miles_{state}"] = miles

            writer.writerow(row_data)

    print(f"Detailed CSV created: {csv_output_path}")


def main():
    """
    Main function with enhanced menu for full/simplified extraction
    """
    print("🚛 Driver Packet Processing System")
    print("=" * 40)

    # Check required API keys
    # 1. Gemini API (required)
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not set")
        print("\n📋 Setup Instructions:")
        print("1. Get API key from: https://makersuite.google.com/app/apikey")
        print("2. Set environment variable:")
        print("   PowerShell: $env:GEMINI_API_KEY='your_api_key_here'")
        print("   Command Prompt: set GEMINI_API_KEY=your_api_key_here")
        return

    print(f"✅ Gemini API key configured: {api_key[:3]}...{api_key[-3:]}")

    # 2. HERE API (optional, enhances geocoding and enables distance calculation)
    here_key = os.environ.get("HERE_API_KEY")
    if here_key:
        print(f"✅ HERE API key configured: {here_key[:3]}...{here_key[-3:]}")
        print("   Enhanced geocoding and distance calculation enabled")
    else:
        print("⚠️  HERE API key not set (optional but recommended)")
        print("\n📋 HERE API Setup (for distance calculation):")
        print("1. Get FREE API key from: https://developer.here.com/")
        print("2. Set environment variable:")
        print("   PowerShell: $env:HERE_API_KEY='your_api_key_here'")
        print("   Command Prompt: set HERE_API_KEY=your_api_key_here")

    while True:
        try:
            choice = show_menu()

            if choice == "0":
                print("\n👋 Goodbye!")
                break
            elif choice == "1":
                # Process all images in batch
                process_batch_complete()
            elif choice == "2":
                # Process single image
                selected_image = show_available_images()
                if selected_image:
                    process_single_image_complete(selected_image)
                else:
                    print("❌ No image selected")
            elif choice == "3":
                # Test validation accuracy
                test_validation_accuracy()
            else:
                print("❌ Invalid choice. Please enter a number between 0 and 3.")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Goodbye!")
            break
        except Exception as e:

            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = traceback.extract_tb(exc_tb)[-1][0]
            line_no = traceback.extract_tb(exc_tb)[-1][1]
            print(f"❌ Error: {e} at line {line_no} in {os.path.basename(fname)}")
            # Print full traceback for detailed debugging
            traceback.print_exc()

        if choice != "0":
            input("\nPress Enter to continue...")


# Remove all the old complex functions and replace the run_interactive function
def run_interactive():
    """
    Run the simplified interactive system
    """
    main()


if __name__ == "__main__":
    import sys

    # Check if running with arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("🚛 Driver Packet Processing System")
            print("=" * 40)
            print("Usage: python gemini_example.py [option]")
            print("\nOptions:")
            print("  --help    Show this help message")
            print("  (no args) Run interactive menu")
            print("\n📋 Features:")
            print("  • Batch Processing: Process all images in input folder")
            print("  • Single Image: Select and process one image")
            print("  • Full extraction with coordinates and distance calculation")
            print("\n🔧 Requirements:")
            print(
                "  • GEMINI_API_KEY: Required (get from https://makersuite.google.com/)"
            )
            print(
                "  • HERE_API_KEY: Optional for distance calculation (get from https://developer.here.com/)"
            )
        else:
            print("❌ Unknown argument. Use --help for options.")
    else:
        # Interactive mode
        run_interactive()


def test_validation_accuracy():
    """
    Test validation accuracy against reference CSV data
    """
    print(f"\n🧪 Testing Validation Accuracy Against Reference Data")
    print("-" * 60)

    try:
        processor = GeminiDriverPacketProcessor()
        print("✅ Processor initialized")
    except Exception as e:
        print(f"❌ Failed to initialize processor: {e}")
        return

    input_folder = os.path.join(os.path.dirname(__file__), "..", "input")
    reference_csv = os.path.join(input_folder, "driver - Sheet1.csv")

    if not os.path.exists(reference_csv):
        print(f"❌ Reference CSV not found: {reference_csv}")
        return

    # Load reference data to get image list
    try:
        import csv

        with open(reference_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            reference_entries = list(reader)

        print(f"📊 Found {len(reference_entries)} reference entries")

        # Process first 5 images for testing
        test_results = []
        for i, entry in enumerate(reference_entries[:5]):
            image_name = entry.get("Image Name", "").strip()

            # Try to find corresponding image file
            image_extensions = [".jpg", ".jpeg", ".png"]
            image_path = None

            for ext in image_extensions:
                potential_path = os.path.join(input_folder, image_name + ext)
                if os.path.exists(potential_path):
                    image_path = potential_path
                    break

            if not image_path:
                print(f"⚠️  Image file not found for: {image_name}")
                continue

            print(f"\n{'='*50}")
            print(f"Testing {i+1}/5: {image_name}")

            # Process the image
            result = processor.process_image_with_distances(image_path)

            if result.get("processing_success"):
                validation = result.get("reference_validation", {})

                if validation.get("validation_success") and validation.get(
                    "reference_found"
                ):
                    accuracy = validation.get("accuracy_metrics", {})

                    test_results.append(
                        {
                            "image_name": image_name,
                            "field_accuracy": accuracy.get("field_accuracy", 0),
                            "total_discrepancies": accuracy.get(
                                "total_discrepancies", 0
                            ),
                            "critical_discrepancies": accuracy.get(
                                "critical_discrepancies", 0
                            ),
                            "high_discrepancies": accuracy.get("high_discrepancies", 0),
                            "validation_warnings": validation.get(
                                "validation_warnings", []
                            ),
                        }
                    )

                    print(f"✅ Validation completed")
                    print(f"   Field accuracy: {accuracy.get('field_accuracy', 0):.1%}")
                    print(f"   Discrepancies: {accuracy.get('total_discrepancies', 0)}")

                    if accuracy.get("critical_discrepancies", 0) > 0:
                        print(
                            f"   🔴 Critical issues: {accuracy.get('critical_discrepancies', 0)}"
                        )
                else:
                    print(f"❌ Validation failed or no reference found")
            else:
                print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")

        # Summary results
        if test_results:
            print(f"\n📊 Test Summary:")
            print(f"   Images tested: {len(test_results)}")

            avg_accuracy = sum(r["field_accuracy"] for r in test_results) / len(
                test_results
            )
            total_discrepancies = sum(r["total_discrepancies"] for r in test_results)
            total_critical = sum(r["critical_discrepancies"] for r in test_results)
            total_high = sum(r["high_discrepancies"] for r in test_results)

            print(f"   Average field accuracy: {avg_accuracy:.1%}")
            print(f"   Total discrepancies: {total_discrepancies}")
            if total_critical > 0:
                print(f"   🔴 Critical discrepancies: {total_critical}")
            if total_high > 0:
                print(f"   🟠 High severity discrepancies: {total_high}")

            # Show most problematic images
            problematic_images = [
                r
                for r in test_results
                if r["critical_discrepancies"] > 0 or r["high_discrepancies"] > 2
            ]
            if problematic_images:
                print(f"\n⚠️  Images requiring attention:")
                for img in problematic_images:
                    print(
                        f"   - {img['image_name']}: {img['field_accuracy']:.1%} accuracy, {img['total_discrepancies']} discrepancies"
                    )

        return test_results

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return None
