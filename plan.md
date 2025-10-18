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



# Different Input formats
Other then image we have few different formats that will not going to use gemini API 
ther are following 

## New format 1:
State,Country,Unit,Distance
AL,USA,1104,214 mi
AZ,USA,1104,1841 mi
CA,USA,1104,1033 mi

This is very very simple we just need to rearrange few column and we will get the output fast, 
if input file is like this then we will not calcualte gallon and not have gallon in results

## New format 2:
Card #,Tran Date,Invoice,Unit,Driver Name,Odometer,Location Name,City,State/ Prov,Fees,Item,Unit Price,Qty,Amt,DB,Currency
*0541,2025-01-09,13504,,JITENDER SINGH 10813697,0,TA ELOY,ELOY,AZ,0.00,ULSD,3.499,97.9,342.54,N,USD/Gallons
*0541,2025-01-09,13504,,JITENDER SINGH 10813697,0,TA ELOY,ELOY,AZ,0.00,DEFD,4.459,2.95,13.17,N,USD/Gallons
*0541,2025-01-10,89430,,JITENDER SINGH 10813697,0,LOVES #542 TRAVEL STOP,FT STOCKTON,TX,0.00,ULSD,3.689,101.85,375.71,N,USD/Gallons

This will me mostly same as first one but in this one we will not calculate any state miles we will onyl calcualte gallons and display results fo gallon table only

## NEW Format 3:
Account Code,Customer ID,Transaction Date,Date of Original,Transaction Time,Transaction Number Indicator,Transaction Number,Transaction Day,Comchek Card Number,Driver's Name,Employee Number,Driver's License State,Driver's License Number,Unit Number,Hubometer Reading,Previous Hub Reading,Trip Number,Year To Date MPG,MPG for this Fill Up,Purchase Order Number,Trailer Number,Trailer Hub Reading,Truck Stop Code,Service Center Chain Code,Truck Stop Name,Service Center Address,Truck Stop City,Truck Stop State,Service Center Zip Code,Truck Stop Invoice Number,Total Amount Due,Fees for Fuel & Oil & Products,Service Used,Number of Tractor Gallons,Tractor Fuel Price Per Gallon,Cost of Tractor Fuel,Tractor Fuel Billing Flag,Number of Reefer Gallons,Reefer Price Per Gallon,Cost of Reefer Fuel,Reefer Fuel Billing Flag,Number of Quarts of Oil,Total Cost of Oil,Oil Billing Flag,Cash Advance Amount,Charges for Cash Advance,Cash Billing Flag,Non-Funded Item,Product Code 1,Product Amount 1,Product 1 Billing Flag,Product Code 2,Product Amount 2,Product 2 Billing Flag,Product Code 3,Product Amount 3,Product 3 Billing Flag,Rebate Amount,Cancel flag,Rebate Indicator,Automated Transaction,Bulk Fuel Flag,Number 1 Fuel Gallons,Number 1 Fuel PPG,Other Fuel PPG,Canadian Tax Amount US Dollars,Number 1 Fuel Cost,Other Fuel Gallons,Other Fuel Cost,Canadian Tax Amount Canadian Dollars,Canadian Tax Paid Flag,Adjusted Transaction Number,Total Amount Due Comdata,#2 Diesel Gallons,#2 Diesel Cost,#2 Diesel Cost Net Cost,#1 Diesel Cost Net Cost,Reefer Cost  Net Cost,Other Fuel Cost Net Cost,Oil Cost Net Cost,#2 Diesel,#1 Diesel,Reefer Cost,Other Fuel Cost,Product 1 Net Cost,Product 2 Net Cost,Product 3 Net Cost,Billable Currency,Express Cash Billing Flag,Express Cash Load Pick Up Flag,Cost Plus Relationship Type,Rack Type,OPIS Rack City Number,OPIS Supplier Number,OPIS Rack City Description,OPIS Rack State,OPIS Supplier Name,Rack Price #1 Diesel,Rack Price #2 Diesel,Rack Date,Diesel - Federal Tax PPG,Diesel - State Tax PPG,Diesel - State Superfund Rate PPG,Diesel - LUST Rate PPG,Diesel - Sales Tax Applies to Markup,Diesel - Transportation Rate PPG,Diesel - Miscellaneous Rate PPG,Diesel - Sales Tax Applies to Rack Price,Reefer - Federal Tax PPG,Diesel - Sales Tax Applies to Federal Tax,Diesel - Sales Tax Applies to State Tax,Diesel - Sales Tax Applies to Superfund Rate,Diesel - Sales Tax Applies to LUST Rate,Diesel - Sales Tax Applies to Transportation Rate,Diesel-Sales Tax Applies to Misc Rate,Diesel - Sales Tax Rate Percent,#2 Diesel - Cost Plus Price,#1 Diesel - Cost Plus Price,Reefer - State Tax PPG,Reefer - State Superfund Rate PPG,Reefer - LUST Rate PPG,Reefer - Transportation Rate PPG,Reefer - Miscellaneous Rate PPG,Reefer - Sales Tax Applies to Rack Price,Reefer - Sales Tax Applies to State Tax,Reefer - Sales Tax Applies to Federal Tax,Reefer - Sales Tax Applies to Transportation Rate,Reefer - Sales Tax Applies to Miscellaneous Rate,Reefer - Sales Tax Applies to Markup,Reefer - Sales Tax Applies to Superfund Rate,Reefer - Cost Plus Price,Reefer - Sales Tax Applies to LUST Rate,Miscellaneous Rate Description,Truck Stop Markup PPG,#2 Diesel - Total Cost Plus Price,#1 Diesel - Total Cost Plus Price,#2 Diesel Retail PPG,#1 Diesel Retail PPG,#2 Diesel - Gross Margin ,Reefer - Retail PPG,#2 Diesel - Net Margin,#1 Diesel - Net Margin,#1 Diesel - Gross Margin,Reefer - Sales Tax Rate Percent,Reefer - Net Margin,Other Markup PPG,Reefer - Total Cost Plus Price,Reefer - Gross Margin,RFID Number,Diesel 1 Sales Tax Per Gallon,Diesel 2 Sales Tax Per Gallon,MISC 1,MISC 2,License Plate,VIN,Vehicle Description,Expanded Unit Number,Not Limited Network Flag,Card Token,Alt Card Number
JJ068,98647,04/01/2025,00/00/00,02:24,0,17836,1,560017XXXXXX5373,GARADO,RIDWAN,ACCOUNT 33,MO,177C340001,1104,0,0,,0.00,0.00,,,0 ,OH976,MU001,LOVES #892,9901 SCHUSTER WAY,ETNA,OH,43018,19842,$494.56,$0.00,S,140.14,$3.529 ,$494.560 ,D,0.00,$0.000,$0.00,,0 ,$0.00,,$0.00,$0.00,,D,,$0.00,,,$0.00,,,$0.00,,$63.89,N,C,Y,N,0.00 ,$0.00000,$0.00000,$0.00,$0.00000,0.00,$0.00,$0.00,Y,00000000,$0.00,140.14 ,$494.56000,$430.67000,$0.00000,$0.00,$0.00,$0.00,$3.07300,$0.00000,$0.00,$0.00,$0.00,$0.00,$0.00,U,,,B,P,315,007,,,,$0.00000,$2.26740,31/25/03,$0.25020,$0.47000,$0.00000,$0.00000,Y,$0.06120,$0.01430,Y,$0.00000,Y,N,N,N,Y,Y,0.000%,$3.06310,$0.01000,$0.00000,$0.00000,$0.00000,$0.00000,$0.00000,,,,,Y,,,$0.01000,,OTHER TAX,$0.01000,$3.07310,$0.00000,$3.52900,$0.00000,$0.466,$0.00000,$0.010,$0.000,$0.000,0.00000%,$0.000,$0.00000,$0.000,$0.000,,0.00,0.72,,,,,,1104,Out Of Network,393J66G4R9,
JJ068,98647,04/01/2025,00/00/00,07:46,3,324212,1,560017XXXXXX5373,COX,TYRONE LEE,ACCOUNT 33,CA,C4368668,1150,0,0,,0.00,0.00,,,0 ,OK268,MU001,LOVES #255,214 SOUTH HWY 100,WEBBERS FALL,OK,74470 0479,45766,$792.16,$0.00,B,214.53,$3.458 ,$741.910 ,D,0.00,$0.000,$0.00,,0 ,$0.00,,$50.00,$0.25,D,D,,$0.00,,,$0.00,,,$0.00,,$113.71,N,C,Y,N,0.00 ,$0.00000,$4.19100,$0.00,$0.00000,8.24,$34.53,$0.00,Y,00000000,$0.25,206.29 ,$707.38000,$593.67000,$0.00000,$0.00,$34.53,$0.00,$2.87800,$0.00000,$0.00,$34.53,$0.00,$0.00,$0.00,U,,,B,P,645,007,,,,$0.00000,$2.35390,31/25/03,$0.25020,$0.19000,$0.00000,$0.00000,Y,$0.06370,$0.01000,Y,$0.00000,Y,N,N,N,Y,Y,0.000%,$2.86780,$0.01000,$0.00000,$0.00000,$0.00000,$0.00000,$0.00000,,,,,Y,,,$0.01000,,OTHER TAX,$0.01000,$2.87780,$0.00000,$3.42900,$0.00000,$0.561,$0.00000,$0.010,$0.000,$0.000,0.00000%,$0.000,$0.00000,$0.000,$0.000,,0.00,0.44,,,,,,1150,Out Of Network,393J66G4R9,



This will be same as 2nd one it will onyl give us gallons 
we have to get "Number of Tractor Gallons" field and "Truck Stop State" mainly 

## NEW format 4
we are going to have an .csv format in which first we have to search for headers 
some times these are on 1st row but some times these are on 3rd row (for example (test\input\csvFormat4\08.2 Quantum Jan to Sept 25-For Miles Update.xlsx - Sheet1.csv) )
In this we will have some key columns like
Load No, Shipper City,Shipper State,Delivery City,Delivery State
you will see that in input file Miles are empty.
now main thing to do is take each row as single input and take these column (Shipper City,Shipper State,Delivery City) and use here API to get the route and calcualte how many miles it traveled in each state, we have to use already present function in files like [src\route_analyzer.py](src\route_analyzer.py) and [src\state_analyzer.py](src\state_analyzer.py) and any other file related to HERE API. 
The process is simple in NEW format 4 take single row as input and calcualte miles in each state.
with respect to [streamlit_app.py](streamlit_app.py) we will not use result dashboard in this and display some results in export data UI tab but the output format will be xlsx and csv both and json could be empty.
we will only work with miles here and not with fuel gallons.

### Performance Optimization Features
Based on performance analysis (5067 routes in 2h 14min = 38 routes/min):

#### 1. Progressive Export Feature
- **Auto-save every 500 routes**: System automatically downloads partial CSV results every 500 processed routes
- **Resume capability**: If processing is interrupted, user can upload the partial result and system will detect completed routes
- **Battery protection**: Prevents data loss from laptop battery issues or crashes
- **Progress persistence**: Maintains processing state across interruptions

#### 2. Smart Re-processing Mode
When user uploads a CSV that already has State column with data:
- **Detection logic**: System detects if State column exists and has valid state abbreviations (CA, TX, NY, etc.)
- **Selective processing**: Only processes routes where:
  - State column is empty/blank
  - State column contains "WARNING" or "ERROR" or "FAILED"
  - State column has invalid values (not 2-letter state codes)
  - Multiple state entries exist for same Load No (indicating incomplete processing)
- **Skip completed routes**: Routes with valid state data are preserved and skipped
- **Merge results**: Combines existing valid data with newly calculated routes
- **Validation**: Ensures each Load No has multiple state entries as expected

#### 3. Failure Handling Strategy
For routes that fail distance calculation (~1% failure rate based on logs):
- **Retry logic**: 2-3 attempts with exponential backoff
- **Fallback estimation**: Use straight-line distance × truck routing factor (1.3x)
- **Error categorization**: 
  - "No route found": Geographic/routing issues
  - "Distance calculation failed": API/service issues
  - "Missing location data": Data quality issues
- **Manual review queue**: Failed routes exported separately for manual processing

### output format for new format 4
for sample input 
Load No,PU Date,Del Date,Inv Date,Shipper City,Shipper State,Delivery City,Delivery State,Miles,Remarks
179758,11/04/24,11/10/24,01/02/25,MORENO VALLEY,CA,SAN ANTONIO ,TX,,
180442,12/06/24,12/12/24,01/02/25,MORENO VALLEY,CA,NEW BRAUNFELS ,TX,,

output will be 
Load No,PU Date,Del Date,Inv Date,Shipper City,Shipper State,Delivery City,Delivery State,State,Miles,Remarks
179758,11/04/24,11/10/24,01/02/25,MORENO VALLEY,CA,SAN ANTONIO ,TX, state 1, miles of state 1,,
179758,11/04/24,11/10/24,01/02/25,MORENO VALLEY,CA,SAN ANTONIO ,TX, state 2, miles of state 2,,
179758,11/04/24,11/10/24,01/02/25,MORENO VALLEY,CA,SAN ANTONIO ,TX, state 3, miles of state 3,,
179758,11/04/24,11/10/24,01/02/25,MORENO VALLEY,CA,SAN ANTONIO ,TX, state 4, miles of state 4,,
180442,12/06/24,12/12/24,01/02/25,MORENO VALLEY,CA,NEW BRAUNFELS ,TX, state 1, miles of state 1,,
180442,12/06/24,12/12/24,01/02/25,MORENO VALLEY,CA,NEW BRAUNFELS ,TX, state 2, miles of state 2,,
180442,12/06/24,12/12/24,01/02/25,MORENO VALLEY,CA,NEW BRAUNFELS ,TX, state 3, miles of state 3,,
180442,12/06/24,12/12/24,01/02/25,MORENO VALLEY,CA,NEW BRAUNFELS ,TX, state 4, miles of state 4,,
180442,12/06/24,12/12/24,01/02/25,MORENO VALLEY,CA,NEW BRAUNFELS ,TX, state 5, miles of state 5,,
180442,12/06/24,12/12/24,01/02/25,MORENO VALLEY,CA,NEW BRAUNFELS ,TX, state 6, miles of state 6,,

State column will be two letter for state like CA for california

### Implementation Priority
1. **Phase 1**: Progressive export every 500 routes
2. **Phase 2**: Smart re-processing mode for interrupted sessions
3. **Phase 3**: Enhanced failure handling with fallback estimation
4. **Phase 4**: Route caching and deduplication for performance

### Expected Performance Improvements
- **Progressive export**: 0% data loss from interruptions
- **Smart re-processing**: 50-90% time savings on resumed sessions
- **Failure handling**: 99.5%+ completion rate vs current 99.1%
- **Route caching**: 3-5x speed improvement for duplicate routes