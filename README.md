# 🚛 Driver Packet Processor

**AI-powered driver packet processing with modular architecture and intelligent data extraction.**

## 🎯 Overview

Transform handwritten driver trip sheets into structured data using Google's Gemini AI, with automatic geocoding, route analysis, and state-by-state mileage distribution.

## ✨ Key Features

- **🤖 AI-Powered OCR** - Gemini multimodal AI for intelligent text extraction
- **🌍 Smart Geocoding** - HERE API + Nominatim fallback for location coordinates  
- **📏 Route Analysis** - Real truck routing with distance calculations
- **🗺️ State Mileage** - Automatic state-by-state mileage distribution
- **🔧 Data Validation** - Comprehensive quality checks and corrections
- **📊 Batch Processing** - Process hundreds of images efficiently
- **⚙️ Centralized Config** - 200+ customizable settings via environment variables

## 🏗️ Architecture

**Modular design** with 9 specialized components:

```
📱 Main Processor → 📝 Data Extraction → 🔧 Validation → 🌍 Geocoding
                                                          ↓
📊 File Processing ← 🔍 Reference Check ← 🗺️ State Analysis ← 📏 Route Analysis
```

**Core Modules:**
- `main_processor` - Orchestrates complete processing pipeline
- `data_extractor` - Gemini AI integration for OCR and extraction
- `geocoding_service` - Location-to-coordinate conversion
- `route_analyzer` - Distance calculations and route analysis
- `state_analyzer` - State-by-state mileage distribution with GIS
- `data_validator` - Quality validation and data correction
- `reference_validator` - Accuracy testing against reference data
- `file_processor` - Batch processing and result management
- `config` - Centralized configuration with validation

## 🚀 Quick Start

### Installation
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment  
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Setup Environment
Create `.env` file:
```bash
GEMINI_API_KEY=your_gemini_key_here
HERE_API_KEY=your_here_key_here  # Optional but recommended
```

### Basic Usage
```python
from src import process_driver_packet

# Process single image
result = process_driver_packet("input/driver_sheet.jpg")
print(f"Driver: {result['drivers_name']}")
print(f"Total Miles: {result['total_miles']}")
```

### Batch Processing
```python
from src import process_driver_packet_folder

# Process entire folder
results = process_driver_packet_folder("input/", "output/")
print(f"Processed {len(results)} images")
```

### Advanced Usage
```python
from src import DriverPacketProcessor

processor = DriverPacketProcessor()
result = processor.process_single_image("image.jpg")

# Access detailed results
print(f"Geocoding success: {result['coordinates']['geocoding_summary']}")
print(f"State mileage: {result['distance_calculations']['state_mileage']}")
```

## 📋 Configuration

**Environment Variables:**
```bash
# Core Settings
GEMINI_API_KEY=required
HERE_API_KEY=optional
GEMINI_TIMEOUT=60
GEOCODING_TIMEOUT=5

# Processing Settings  
MIN_STATE_MILES_THRESHOLD=1.0
ROUTE_SAMPLE_POINTS_MAX=20
MAX_TOTAL_MILES=15000

# Logging
LOG_LEVEL=INFO
LOG_DIR=temp
```

**View Configuration:**
```python
from src import Config
Config.print_configuration_summary()
```

## 📊 Output Format

**JSON Structure:**
```json
{
  "processing_success": true,
  "drivers_name": "JOHN DOE",
  "total_miles": "2847",
  "coordinates": {
    "trip_started_from": {
      "location": "Bloomington, CA",
      "latitude": 34.0631,
      "longitude": -117.3962
    }
  },
  "distance_calculations": {
    "total_distance_miles": 2847.3,
    "state_mileage": [
      {"state": "CA", "miles": 1823.2, "percentage": 64.0},
      {"state": "TX", "miles": 1024.1, "percentage": 36.0}
    ]
  }
}
```

## 🔧 Development

**Module Structure:**
```
src/
├── __init__.py           # Main exports
├── main_processor.py     # Orchestration
├── data_extractor.py     # Gemini AI integration
├── geocoding_service.py  # Location services
├── route_analyzer.py     # Distance calculations
├── state_analyzer.py     # State mileage analysis
├── data_validator.py     # Quality validation
├── reference_validator.py # Accuracy testing
├── file_processor.py     # Batch processing
├── logging_utils.py      # Logging infrastructure
└── config.py            # Centralized configuration
```

**Key Dependencies:**
- `google-generativeai` - Gemini AI
- `requests` - API calls
- `pillow` - Image processing
- `python-dotenv` - Environment management
- `geopandas` (optional) - Enhanced GIS analysis

## 📈 Performance

- **Batch Processing**: Hundreds of images efficiently
- **Smart Caching**: Geocoding and API result caching
- **Graceful Degradation**: Works even with limited API access
- **Error Recovery**: Robust error handling and reporting
- **Resource Optimization**: Configurable timeouts and retry logic

## 🔍 Quality Assurance

- **Data Validation**: 20+ validation rules with intelligent corrections
- **Reference Testing**: Accuracy validation against known good data
- **Comprehensive Logging**: Full audit trail of all operations
- **Error Reporting**: Detailed error analysis and categorization

## 📚 Documentation

- `ARCHITECTURE.md` - Detailed system architecture
- `CONFIGURATION.md` - Complete configuration guide  
- `RUNBOOK.md` - Common tasks and troubleshooting
- `config_demo.py` - Interactive configuration demonstration

## 🎯 Use Cases

- **Fleet Management**: Process driver trip sheets at scale
- **Compliance Reporting**: Automated state mileage reporting
- **Data Migration**: Convert paper records to digital format
- **Quality Control**: Validate extracted data against reference sources

## 🛠️ Troubleshooting

**Common Issues:**
- Missing API keys → Check `.env` file
- Geocoding failures → Verify HERE API key or use Nominatim fallback
- Processing errors → Check logs in `temp/driver_packet.log`

**Configuration Check:**
```python
python config_demo.py  # Comprehensive configuration validation
```

## 📄 License

[Your License Here]

## 🤝 Contributing

[Contributing Guidelines Here]

---

**Built with ❤️ for efficient driver packet processing**