# Driver Packet Processing System - Comprehensive Plan

## 📋 **Overview**
This system processes driver trip sheet images using Google's Gemini AI for intelligent OCR and data extraction, with comprehensive validation, correction, geocoding, and distance calculation capabilities.

## 🎯 **Core Processing Steps**

### **Step 1: Image Analysis & Data Extraction**
- **Input**: Driver packet images from `@input` folder
- **Process**: Use Gemini API to extract handwritten text data
- **Technology**: Google Gemini 1.5-flash multimodal AI
- **Output**: Raw JSON data with extracted fields

### **Step 2: Comprehensive Data Validation & Correction**
- **Trailer Number Validation**: Ensure 200-299 range (fix hundreds digit)
- **Location Corrections**: Apply standardized location mappings
- **Date Format Standardization**: Convert all dates to MM/DD/YY format
- **Field Duplication Prevention**: Avoid copying values between fields
- **Drop-off Array Handling**: Parse multiple drop-offs separated by "to"
- **Total Miles Validation**: Check for reasonable values

### **Step 3: Geocoding (GPS Coordinates)**
- **Primary**: HERE Geocoding API (if available)
- **Fallback**: OpenStreetMap Nominatim API
- **Caching**: Avoid repeated API calls for same locations
- **Output**: Latitude/longitude coordinates for all locations

### **Step 4: Distance Calculations**
- **Method**: HERE Routing API (truck routing mode)
- **Process**: Calculate distances between consecutive stops
- **State Mileage**: Track mileage within each state
- **Route Analysis**: Full trip analysis with leg-by-leg breakdown

### **Step 5: Output Generation**
- **JSON Files**: Detailed results with all metadata
- **CSV Files**: Small table for each image with distance traveled in each state.
- **Timestamps**: Processing metadata for tracking

### **Step 6: Reporting & Validation**
- **Automatic Corrections**: Report all applied fixes
- **Validation Warnings**: Flag suspicious data
- **Success Metrics**: Geocoding and distance calculation success rates

## 📊 **Data Fields Extracted**

### **Driver Information (Row 1)**
- `drivers_name`: Full driver name with intelligent spelling correction
- `unit`: Unit number (if clearly visible)
- `trailer`: Trailer number (validated to 200-299 range)

### **Trip Timing (Row 2)**
- `date_trip_started`: Trip start date (MM/DD/YY format)
- `date_trip_ended`: Trip end date (MM/DD/YY format)
- `trip`: Trip number/ID (only if explicitly visible)

### **Trip Locations (Rows 3-5)**
- `trip_started_from`: Origin location (City, State format)
- `first_drop`: First drop location (City, State format)
- `second_drop`: Second drop location (City, State format)
- `third_drop`: Third drop location (optional, City, State format)
- `forth_drop`: Fourth drop location (optional, City, State format)
- `inbound_pu`: Inbound pickup location (City, State format)
- `drop_off`: Final drop-off location(s) - can be array if multiple

### **Trip Metrics**
- `total_miles`: Total miles from "OFFICE USE ONLY" section

## 🔧 **Automatic Corrections Applied**

### **Location Standardization**
- `"Bloomington"` (any state) → `"Bloomington, CA"`
- `"Yard"` or `"yard"` → `"San Bernardino, CA"`
- `"Jaredo"` → `"Laredo"`
- `"Corona"` → `"Fontana"`
- `"Jaredotx"` → `"Laredo, TX"`
- Additional intelligent spelling corrections

### **Data Validation Rules**
- **Trailer Numbers**: Auto-correct to 200-299 range (e.g., "786" → "286")
- **Date Formats**: Standardize to MM/DD/YY (e.g., "11-28-2022" → "11/28/22")
- **Field Isolation**: Prevent third_drop/forth_drop from copying other field values
- **Drop-off Arrays**: Handle multiple destinations separated by "to"
- **Miles Validation**: Flag unreasonable values (too high/low)

## 🌍 **Geocoding & Distance Features**

### **Geocoding Process**
- **Location Format**: "City, State" format required
- **API Integration**: HERE Geocoding API (primary), Nominatim (fallback)
- **Caching**: Intelligent caching to avoid repeated API calls
- **Success Tracking**: Report geocoding success rates

### **Distance Calculation**
- **Routing Mode**: Truck routing for commercial vehicles
- **Consecutive Stops**: Calculate distance between all consecutive locations
- **State Mileage**: Track mileage within each state boundary
- **Route Summary**: Total distance and state-by-state breakdown

## 📁 **File Structure & Outputs**

### **Input Files**
- **Location**: `@input` folder
- **Formats**: .jpg, .jpeg, .png, .bmp, .tiff
- **Processing**: Batch processing of all images

### **Output Files**
- **JSON**: `batch_results_complete_TIMESTAMP.json` (detailed results)
- **CSV**: `batch_results.csv` (summary with state mileage)
- **Location**: `@output` folder
- **Encoding**: UTF-8 for international character support

### **CSV Field Structure**
```
source_image, State Initials, Milage in state.
```

## 🔍 **Quality Assurance Features**

### **Validation Warnings**
- Suspicious trip numbers (too high)
- Very short driver names (incomplete)
- Unusual date formats
- Field duplication detection
- Gap detection in drop sequence
- Duplicate locations across fields

### **Correction Reporting**
- All automatic corrections are logged
- Original → Corrected value tracking
- Correction type classification
- Warning severity levels

### **Success Metrics**
- Processing success rate
- Geocoding success rate
- Distance calculation success rate
- Field population completeness

## 🚀 **System Capabilities**

### **Processing Modes**
- **Batch Processing**: Process all images in input folder
- **Single Image**: Process individual selected image
- **Interactive Menu**: User-friendly interface
- **Error Recovery**: Graceful handling of processing failures

### **API Integration**
- **Required**: GEMINI_API_KEY for text extraction
- **Optional**: HERE_API_KEY for enhanced geocoding and distance calculation
- **Fallback**: OpenStreetMap Nominatim for basic geocoding

### **Performance Features**
- **Caching**: Geocoding results cached to avoid repeated API calls
- **Progress Tracking**: Real-time processing status
- **Error Handling**: Comprehensive error reporting and recovery
- **Memory Management**: Efficient handling of large image batches

## 📈 **Verification & Testing**

### **Data Accuracy Checks**
- Compare extracted miles with calculated route distances
- Validate location coordinates against known addresses
- Check date format consistency
- Verify trailer number ranges

### **System Validation**
- Process sample images and verify output structure
- Test geocoding accuracy with known addresses
- Validate distance calculations against mapping services
- Check CSV output format and completeness

### **Error Handling Tests**
- Invalid image formats
- Missing API keys
- Network failures
- Malformed OCR results

## 🔧 **Configuration Requirements**

### **Environment Variables**
- `GEMINI_API_KEY`: Required for text extraction
- `HERE_API_KEY`: Optional for enhanced features

### **System Requirements**
- Python 3.8+
- PIL (Pillow) for image processing
- Google Generative AI library
- HERE API access (optional)
- Internet connection for API calls

### **File Permissions**
- Read access to input folder
- Write access to output folder
- Temporary file creation for processing

## 🎯 **Future Enhancements**

### **Planned Features**
- API rate limiting for large batches
- Persistent geocoding cache
- Batch geocoding requests
- Enhanced error recovery
- Configuration file support
- Progress indicators for large batches

### **Optimization Opportunities**
- Reduce API calls through better caching
- Improve processing speed with parallel processing
- Enhanced validation rules based on real-world data
- Better handling of edge cases in handwritten text

This comprehensive plan serves as the definitive guide for system verification and ensures all components work together to deliver accurate, reliable driver packet processing.




# Fuel Table Extraction
UPDATE Prompt for GEMINI using following information related to fuel details table:

It should read fuel table the heading of table is "FUEL DETAILS", and extract Fuel Gallons and in which state it was filled.
It has following columns:
1. "Data/Invoice" or "Data/ Invoice"
2. "Vendor"
3. "City&State" or "City & State"
4. "# Gal."
5. "Price"
6. "Amount"
7. "CashAdv." or "Cash Adv."

Columns explanations
### 1. "Data/Invoice" or "Data/ Invoice"
It will be a date in which we are not interested, but some rows will be filed by three letters "DEF" if that is the case then we will take same date from one row above.
### 2. "Vendor"
Ignore this column.
### 3. "City&State" or "City & State"
We are very interested in State. Mostly there will be Initials of USA States but some times we might have full state name. If state name is not clear we can get the idea from city name or from the row above or below it. If no city and state is mentioned and any of other column show "DEF" then use the state from the above row. 
### 4. "# Gal."
It will be a number/quantity and we have to be very very accurate about reading it.
### 5. "Price"
Ignore this column.
### 6. "Amount"
Ignore this column.
### 7. "CashAdv." or "Cash Adv."
Ignore this column.

## Results 
A new sheet named "Gallon Trip Env" with following columns
1. "State" : State initials (two letters)
2. "Gallons" : Cumulative Sum of gallon per state
3. "Unit" : It is unit number whic is already extracted from image
4. "Trip (Page No.)" : Image number 

Basically we are calculating gallon per state for all different states in fuel details table.
