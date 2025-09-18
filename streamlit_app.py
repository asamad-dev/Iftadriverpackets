#!/usr/bin/env python3
"""
🚛 Driver Packet Processing System - Streamlit Web Application
Modern web interface for processing driver packet images using AI-powered OCR
"""

import streamlit as st
import os
import io
import json
import csv
import pandas as pd
from datetime import datetime
import time
import sys
import traceback
from typing import Dict, List, Any
from PIL import Image
import tempfile
import zipfile

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from gemini_processor import GeminiDriverPacketProcessor
except ImportError:
    st.error("❌ Could not import GeminiDriverPacketProcessor. Please check your setup.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Driver Packet Processing System",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    
    .main-header p {
        color: #e0e0e0;
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }
    
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2a5298;
        margin: 0.5rem 0;
    }
    
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .upload-section {
        border: 2px dashed #2a5298;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    
    .stProgress .st-bo {
        background-color: #2a5298;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚛 Driver Packet Processing System</h1>
        <p>AI-Powered OCR with Enhanced Route Analysis - Now detects ALL states along truck routes!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'processing_results' not in st.session_state:
        st.session_state.processing_results = []
    if 'processor' not in st.session_state:
        st.session_state.processor = None
    if 'api_configured' not in st.session_state:
        st.session_state.api_configured = False
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Configuration
        st.subheader("🔑 API Keys")
        
        gemini_key = st.text_input(
            "Gemini API Key",
            type="password",
            help="Required for AI-powered OCR. Get from: https://makersuite.google.com/app/apikey",
            placeholder="Enter your Gemini API key..."
        )
        
        here_key = st.text_input(
            "HERE API Key (Optional)",
            type="password",
            help="For enhanced geocoding and distance calculation. Get from: https://developer.here.com/",
            placeholder="Enter your HERE API key..."
        )
        
        # Validation options
        st.subheader("🔍 Validation Options")
        
        enable_validation = st.checkbox(
            "Enable Reference Validation",
            value=True,
            help="Compare results against reference data (requires driver - Sheet1.csv)"
        )
        
        # Processing options
        st.subheader("📊 Processing Options")
        
        use_here_api = st.checkbox(
            "Use HERE API for Enhanced Route Analysis",
            value=bool(here_key),
            disabled=not bool(here_key),
            help="Enable HERE Maps API with polyline analysis to detect ALL states along truck routes"
        )
        
        if use_here_api and here_key:
            st.success("🗺️ Enhanced Route Analysis Enabled")
        elif not here_key:
            st.info("💡 **Get HERE API Key for Enhanced Analysis**")
            st.write("Without HERE API, only origin/destination states are calculated.")
        
        # Initialize processor
        if gemini_key:
            try:
                if not st.session_state.processor or not st.session_state.api_configured:
                    st.session_state.processor = GeminiDriverPacketProcessor(
                        api_key=gemini_key,
                        here_api_key=here_key if here_key else None
                    )
                    st.session_state.api_configured = True
                    st.success("✅ Processor initialized successfully!")
            except Exception as e:
                st.error(f"❌ Error initializing processor: {str(e)}")
                st.session_state.api_configured = False
        else:
            st.warning("⚠️ Please enter your Gemini API key to continue")
            st.session_state.api_configured = False
    
    # Main content
    if not st.session_state.api_configured:
        st.info("👈 Please configure your API keys in the sidebar to get started.")
        show_setup_instructions()
        return
    
    # Tabs for different functions
    tab1, tab2, tab3, tab4 = st.tabs([
        "📤 Upload & Process", 
        "📊 Results Dashboard", 
        "📋 Validation Report", 
        "💾 Export Data"
    ])
    
    with tab1:
        upload_and_process_tab(st.session_state.processor, use_here_api)
    
    with tab2:
        results_dashboard_tab()
    
    with tab3:
        validation_report_tab()
    
    with tab4:
        export_data_tab()

def show_setup_instructions():
    """Show setup instructions for API keys"""
    st.markdown("""
    ### 🚀 Quick Setup Guide
    
    #### 1. **Gemini API Key** (Required)
    - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
    - Click "Create API Key"
    - Copy the key and paste it in the sidebar
    
    #### 2. **HERE API Key** (Optional but Recommended)
    - Visit [HERE Developer Portal](https://developer.here.com/)
    - Sign up for a free account
    - Create a new project and get your API key
    - Enables advanced distance calculation and state mileage breakdown
    """)

def upload_and_process_tab(processor, use_here_api):
    """Upload and process images/CSV tab"""
    st.header("📤 Upload Driver Packet Data")
    
    # Input type selection
    input_type = st.radio(
        "Select Input Type:",
        ["Images (Driver Packets)", "CSV Files (Pre-processed Data)"],
        help="Choose whether to upload images for AI processing or CSV files for direct processing"
    )
    
    if input_type == "Images (Driver Packets)":
        st.subheader("🖼️ Upload Driver Packet Images")
        # File uploader for images
        uploaded_files = st.file_uploader(
            "Choose driver packet images",
            type=['png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            help="Upload one or more driver packet images for AI processing"
        )
    else:
        st.subheader("📊 Upload CSV Files")
        # File uploader for CSV
        uploaded_files = st.file_uploader(
            "Choose CSV files",
            type=['csv'],
            accept_multiple_files=True,
            help="Upload CSV files with distance or fuel data"
        )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully")
        
        # Display uploaded files
        if input_type == "Images (Driver Packets)":
            with st.expander("📁 Uploaded Files", expanded=True):
                cols = st.columns(min(len(uploaded_files), 4))
                for i, uploaded_file in enumerate(uploaded_files):
                    with cols[i % 4]:
                        st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)
        else:
            with st.expander("📁 Uploaded CSV Files", expanded=True):
                st.info("📋 **Supported CSV Formats:**")
                st.write("• **Format 1**: `State,Country,Unit,Distance` - Simple distance data")
                st.write("• **Format 2**: `Card #,Tran Date,Invoice,Unit,Driver Name,...,State/ Prov,...,Qty,...` - Fuel transactions")
                st.write("• **Format 3**: `Account Code,...,Unit Number,...,Truck Stop State,...,Number of Tractor Gallons,...` - Complex fuel data")
                st.write("")
                
                for uploaded_file in uploaded_files:
                    st.write(f"📄 {uploaded_file.name}")
        
        # Process button
        button_text = "🚀 Process Images" if input_type == "Images (Driver Packets)" else "🚀 Process CSV Files"
        if st.button(button_text, type="primary", use_container_width=True):
            # Store use_here_api setting in session state for later use
            st.session_state['use_here_api'] = use_here_api
            if input_type == "Images (Driver Packets)":
                process_images(uploaded_files, processor, use_here_api)
            else:
                process_csv_files(uploaded_files)

def process_images(uploaded_files, processor, use_here_api):
    """Process uploaded images"""
    st.header("🔄 Processing Images...")
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        # Update progress
        progress = (i + 1) / len(uploaded_files)
        progress_bar.progress(progress)
        status_text.text(f"Processing {uploaded_file.name}... ({i + 1}/{len(uploaded_files)})")
        
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # Process image
            result = processor.process_image_with_distances(tmp_file_path, use_here_api)
            result['source_image'] = uploaded_file.name  # Update source image name
            results.append(result)
            
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
        except Exception as e:
            st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
            results.append({
                'source_image': uploaded_file.name,
                'processing_success': False,
                'error': str(e)
            })
    
    # Complete processing
    progress_bar.progress(1.0)
    status_text.text("✅ Processing complete!")
    
    # Store results in session state
    st.session_state.processing_results = results
    
    # Show summary
    successful = sum(1 for r in results if r.get('processing_success'))
    failed = len(results) - successful
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Total Images", len(results))
    with col2:
        st.metric("✅ Successful", successful)
    with col3:
        st.metric("❌ Failed", failed)
    
    if successful > 0:
        st.success(f"🎉 Successfully processed {successful} out of {len(results)} images!")
    
    if failed > 0:
        st.error(f"⚠️ {failed} images failed to process. Check the Results Dashboard for details.")

def process_csv_files(uploaded_files):
    """Process uploaded CSV files"""
    st.header("🔄 Processing CSV Files...")
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        # Update progress
        progress = (i + 1) / len(uploaded_files)
        progress_bar.progress(progress)
        status_text.text(f"Processing {uploaded_file.name}... ({i + 1}/{len(uploaded_files)})")
        
        try:
            # Read CSV file
            csv_content = uploaded_file.getvalue().decode('utf-8')
            
            # Detect format and process
            result = detect_and_process_csv(csv_content, uploaded_file.name)
            results.append(result)
            
            # Show processing summary
            if result.get('processing_success'):
                if result.get('fuel_by_state'):
                    states = list(result['fuel_by_state'].keys())
                    st.success(f"✅ {uploaded_file.name}: Found fuel data for {len(states)} states: {', '.join(states[:3])}")
                elif result.get('distance_calculations', {}).get('state_mileage'):
                    state_mileage = result['distance_calculations']['state_mileage']
                    states = [s['state'] for s in state_mileage]
                    st.success(f"✅ {uploaded_file.name}: Found distance data for {len(states)} states: {', '.join(states[:3])}")
                else:
                    st.success(f"✅ {uploaded_file.name}: Processed successfully")
            
        except Exception as e:
            st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
            results.append({
                'source_image': uploaded_file.name,
                'processing_success': False,
                'error': str(e)
            })
    
    # Complete processing
    progress_bar.progress(1.0)
    status_text.text("✅ Processing complete!")
    
    # Store results in session state
    st.session_state.processing_results = results
    
    # Show summary
    successful = sum(1 for r in results if r.get('processing_success'))
    failed = len(results) - successful
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Total Files", len(results))
    with col2:
        st.metric("✅ Successful", successful)
    with col3:
        st.metric("❌ Failed", failed)
    
    if successful > 0:
        st.success(f"🎉 Successfully processed {successful} out of {len(results)} CSV files!")
    
    if failed > 0:
        st.error(f"⚠️ {failed} files failed to process. Check the Results Dashboard for details.")

def detect_and_process_csv(csv_content, filename):
    """Detect CSV format and process accordingly"""
    try:
        # Parse CSV
        import io
        import csv
        
        # Read first few lines to detect format
        lines = csv_content.strip().split('\n')
        if not lines:
            raise ValueError("Empty CSV file")
        
        header = lines[0].lower()
        
        # Detect format based on headers (case insensitive, flexible matching)
        header_clean = header.replace(' ', '').replace('_', '')
        
        # Format 1: State,Country,Unit,Distance
        if all(col in header_clean for col in ['state', 'country', 'unit', 'distance']):
            st.info(f"🔍 Detected Format 1 (Distance Data): {filename}")
            return process_format1_csv(csv_content, filename)
        
        # Format 2: Fuel card transactions (Card #, State/ Prov, Qty)
        elif ('card#' in header_clean or 'cardno' in header_clean) and ('state/prov' in header_clean or 'stateprov' in header_clean) and 'qty' in header_clean:
            st.info(f"🔍 Detected Format 2 (Fuel Transactions): {filename}")
            return process_format2_csv(csv_content, filename)
        
        # Format 3: Complex fuel data (Truck Stop State, Number of Tractor Gallons)
        elif 'truckstopstate' in header_clean and 'numberoftractorgallons' in header_clean:
            st.info(f"🔍 Detected Format 3 (Complex Fuel Data): {filename}")
            return process_format3_csv(csv_content, filename)
        
        # Additional detection patterns for variations
        elif 'unit' in header_clean and 'distance' in header_clean and len([col for col in ['state', 'miles', 'mi'] if col in header_clean]) > 0:
            return process_format1_csv(csv_content, filename)
        
        else:
            # Show available columns for debugging
            available_cols = header.split(',')[:10]  # Show first 10 columns
            raise ValueError(f"Unknown CSV format. Available columns: {', '.join(available_cols)}... Please ensure your CSV matches one of the supported formats.")
            
    except Exception as e:
        return {
            'source_image': filename,
            'processing_success': False,
            'error': f"CSV detection failed: {str(e)}"
        }

def process_format1_csv(csv_content, filename):
    """Process Format 1: State,Country,Unit,Distance"""
    try:
        import io
        import csv
        import re
        
        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        
        # Extract data
        state_mileage = {}
        unit = None
        
        for row in reader:
            state = row.get('State', '').strip().upper()
            distance_str = row.get('Distance', '').strip()
            unit_val = row.get('Unit', '').strip()
            
            if not unit:
                unit = unit_val
            
            # Parse distance (remove 'mi' and convert to int)
            distance_match = re.search(r'(\d+(?:\.\d+)?)', distance_str)
            if distance_match and state:
                miles = float(distance_match.group(1))
                
                if state in state_mileage:
                    state_mileage[state] += miles
                else:
                    state_mileage[state] = miles
        
        # Convert to expected format
        state_mileage_list = []
        total_miles = 0
        for state, miles in state_mileage.items():
            miles_int = int(round(miles))
            state_mileage_list.append({
                'state': state,
                'miles': miles_int,
                'percentage': 0  # Calculate if needed
            })
            total_miles += miles_int
        
        # Calculate percentages
        for state_data in state_mileage_list:
            if total_miles > 0:
                state_data['percentage'] = round((state_data['miles'] / total_miles) * 100, 1)
        
        return {
            'source_image': filename,
            'processing_success': True,
            'processing_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'unit': unit,
            'total_miles': str(total_miles),
            'distance_calculations': {
                'calculation_success': True,
                'total_distance_miles': total_miles,
                'state_mileage': state_mileage_list
            }
        }
        
    except Exception as e:
        return {
            'source_image': filename,
            'processing_success': False,
            'error': f"Format 1 processing failed: {str(e)}"
        }

def process_format2_csv(csv_content, filename):
    """Process Format 2: Fuel card transactions"""
    try:
        import io
        import csv
        
        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        
        # Extract fuel data
        fuel_purchases = []
        unit = None
        
        for row in reader:
            state = row.get('State/ Prov', '').strip().upper()
            qty_str = row.get('Qty', '').strip()
            unit_val = row.get('Unit', '').strip()
            
            if not unit:
                unit = unit_val
            
            # Parse quantity (gallons)
            try:
                gallons = float(qty_str) if qty_str else 0
                if gallons > 0 and state:
                    fuel_purchases.append({
                        'state': state,
                        'gallons': gallons
                    })
            except ValueError:
                continue
        
        # Process fuel data (aggregate by state)
        fuel_by_state = {}
        total_gallons = 0
        
        for purchase in fuel_purchases:
            state = purchase['state']
            gallons = purchase['gallons']
            
            if state in fuel_by_state:
                fuel_by_state[state] += gallons
            else:
                fuel_by_state[state] = gallons
            
            total_gallons += gallons
        
        return {
            'source_image': filename,
            'processing_success': True,
            'processing_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'unit': unit,
            'fuel_purchases': fuel_purchases,
            'fuel_by_state': fuel_by_state,
            'total_gallons': total_gallons
        }
        
    except Exception as e:
        return {
            'source_image': filename,
            'processing_success': False,
            'error': f"Format 2 processing failed: {str(e)}"
        }

def process_format3_csv(csv_content, filename):
    """Process Format 3: Complex fuel data"""
    try:
        import io
        import csv
        
        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        
        # Extract fuel data
        fuel_purchases = []
        unit = None
        
        for row in reader:
            state = row.get('Truck Stop State', '').strip().upper()
            gallons_str = row.get('Number of Tractor Gallons', '').strip()
            unit_val = row.get('Unit Number', '').strip()
            
            if not unit:
                unit = unit_val
            
            # Parse gallons
            try:
                gallons = float(gallons_str) if gallons_str else 0
                if gallons > 0 and state:
                    fuel_purchases.append({
                        'state': state,
                        'gallons': gallons
                    })
            except ValueError:
                continue
        
        # Process fuel data (aggregate by state)
        fuel_by_state = {}
        total_gallons = 0
        
        for purchase in fuel_purchases:
            state = purchase['state']
            gallons = purchase['gallons']
            
            if state in fuel_by_state:
                fuel_by_state[state] += gallons
            else:
                fuel_by_state[state] = gallons
            
            total_gallons += gallons
        
        return {
            'source_image': filename,
            'processing_success': True,
            'processing_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'unit': unit,
            'fuel_purchases': fuel_purchases,
            'fuel_by_state': fuel_by_state,
            'total_gallons': total_gallons
        }
        
    except Exception as e:
        return {
            'source_image': filename,
            'processing_success': False,
            'error': f"Format 3 processing failed: {str(e)}"
        }

def results_dashboard_tab():
    """Results dashboard tab"""
    st.header("📊 Results Dashboard")
    
    if not st.session_state.processing_results:
        st.info("No results available. Please process some images first.")
        return
    
    results = st.session_state.processing_results
    
    # Summary metrics
    show_summary_metrics(results)
    
    # Detailed results
    st.subheader("📋 Detailed Results")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        show_only_successful = st.checkbox("Show only successful", value=True)
    with col2:
        show_validation_warnings = st.checkbox("Show validation warnings", value=True)
    
    # Display results
    filtered_results = [r for r in results if r.get('processing_success')] if show_only_successful else results
    
    for result in filtered_results:
        show_result_card(result, show_validation_warnings)

def show_summary_metrics(results):
    """Show summary metrics"""
    successful = [r for r in results if r.get('processing_success')]
    failed = [r for r in results if not r.get('processing_success')]
    
    # Basic metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Images", len(results))
    
    with col2:
        st.metric("✅ Successful", len(successful))
    
    with col3:
        st.metric("❌ Failed", len(failed))
    
    with col4:
        success_rate = (len(successful) / len(results)) * 100 if results else 0
        st.metric("📈 Success Rate", f"{success_rate:.1f}%")
    
    # Advanced metrics for successful results
    if successful:
        st.subheader("🚛 Trip Summary")
        
        # Calculate totals with safe conversion
        def safe_float_conversion(value):
            try:
                if value is None or value == '':
                    return 0.0
                # Remove common non-numeric characters
                clean_value = str(value).replace(',', '').replace('$', '').replace(' ', '').strip()
                # Handle cases like "2435B" by extracting numeric part
                import re
                numeric_part = re.search(r'^[\d.]+', clean_value)
                if numeric_part:
                    return float(numeric_part.group())
                return 0.0
            except (ValueError, TypeError, AttributeError):
                return 0.0
        
        total_miles = sum(safe_float_conversion(r.get('total_miles')) for r in successful if r.get('total_miles'))
        total_distance_calculated = sum(safe_float_conversion(r.get('distance_calculations', {}).get('total_distance_miles', 0)) for r in successful)
        
        # Count distance calculation success and enhanced analysis usage
        distance_calc_success_count = 0
        here_api_count = 0
        route_analysis_count = 0
        total_unique_states = set()
        
        for result in successful:
            distance_data = result.get('distance_calculations', {})
            
            # Count successful distance calculations
            if distance_data.get('calculation_success'):
                distance_calc_success_count += 1
            
            # Count HERE API usage and route analysis usage
            uses_here_api = False
            uses_route_analysis = False
            
            if distance_data.get('legs'):
                for leg in distance_data['legs']:
                    if leg.get('api_used') == 'HERE':
                        uses_here_api = True
                    if leg.get('route_analysis_used'):
                        uses_route_analysis = True
                        
            if uses_here_api:
                here_api_count += 1
            if uses_route_analysis:
                route_analysis_count += 1
            
            # Collect all unique states found (only from successful calculations)
            if distance_data.get('state_mileage') and distance_data.get('calculation_success'):
                for state_data in distance_data['state_mileage']:
                    total_unique_states.add(state_data['state'])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📏 Total Extracted Miles", f"{total_miles:,.0f}")
        
        with col2:
            st.metric("🗺️ Total Calculated Distance", f"{total_distance_calculated:,.0f}")
        
        with col3:
            avg_miles = total_miles / len(successful) if successful else 0
            st.metric("📊 Average Miles per Trip", f"{avg_miles:,.0f}")
        
        with col4:
            st.metric("🇺🇸 Unique States Found", len(total_unique_states))
        
        # Show enhanced analysis metrics
        if route_analysis_count > 0:
            st.subheader("🗺️ Enhanced Route Analysis Summary")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🛣️ Enhanced Analysis Used", f"{route_analysis_count}/{len(successful)}")
            
            with col2:
                here_api_rate = (here_api_count / len(successful)) * 100 if successful else 0
                st.metric("📡 HERE API Usage", f"{here_api_rate:.1f}%")
                
            with col3:
                route_analysis_rate = (route_analysis_count / len(successful)) * 100 if successful else 0
                st.metric("🎯 Full Route Coverage", f"{route_analysis_rate:.1f}%")
            
            st.success("🎉 **Feature1.md Implemented!** The system now detects ALL states along truck routes, including intermediate states like Nevada, Arizona, and New Mexico between California and Texas.")
            
        else:
            # Show distance calculation issues if any
            if distance_calc_success_count < len(successful):
                failed_distance_count = len(successful) - distance_calc_success_count
                st.warning(f"⚠️ **Distance Calculation Issues:** {failed_distance_count} out of {len(successful)} trips failed distance calculation.")
            
            # Show HERE API usage info
            if here_api_count > 0:
                here_api_rate = (here_api_count / len(successful)) * 100 if successful else 0
                st.info(f"✅ HERE Maps API used for {here_api_count} out of {len(successful)} trips ({here_api_rate:.1f}%) for accurate routing.")
                st.warning("⚠️ Route analysis unavailable - install required GIS dependencies (geopandas, shapely, flexpolyline) for full state detection.")

def show_result_card(result, show_validation_warnings):
    """Show individual result card with editable fields"""
    source_image = result['source_image']
    
    with st.expander(f"📄 {source_image}", expanded=False):
        if not result.get('processing_success'):
            st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
            return
        
        # Initialize session state for this result if not exists
        if f"edited_{source_image}" not in st.session_state:
            st.session_state[f"edited_{source_image}"] = result.copy()
        
        if f"original_{source_image}" not in st.session_state:
            st.session_state[f"original_{source_image}"] = result.copy()
        
        # Get current edited values
        edited_result = st.session_state[f"edited_{source_image}"]
        original_result = st.session_state[f"original_{source_image}"]
        
        st.markdown("### ✏️ Editable Gemini Extracted Fields")
        st.info("💡 Edit any field below and click 'Recalculate Distances' to update HERE API calculations")
        
        # Define all fields from Gemini extraction prompt
        gemini_fields = {
            'drivers_name': {'label': '👤 Driver Name', 'type': 'text'},
            'unit': {'label': '🚛 Unit #', 'type': 'text'},
            'trailer': {'label': '🚚 Trailer #', 'type': 'text'},
            'date_trip_started': {'label': '📅 Date Trip Started', 'type': 'text'},
            'date_trip_ended': {'label': '📅 Date Trip Ended', 'type': 'text'},
            'trip': {'label': '🆔 Trip #', 'type': 'text'},
            'trip_started_from': {'label': '🏁 Trip Started From', 'type': 'text'},
            'first_drop': {'label': '📍 1st Drop', 'type': 'text'},
            'second_drop': {'label': '📍 2nd Drop', 'type': 'text'},
            'third_drop': {'label': '📍 3rd Drop', 'type': 'text'},
            'forth_drop': {'label': '📍 4th Drop', 'type': 'text'},
            'inbound_pu': {'label': '📍 Inbound PU', 'type': 'text'},
            'drop_off': {'label': '🏁 Drop Off', 'type': 'text'},
            'total_miles': {'label': '📏 Total Miles', 'type': 'text'}
        }
        
        # Create editable form
        col1, col2 = st.columns(2)
        has_changes = False
        
        with col1:
            st.markdown("**Driver & Trip Information:**")
            for field in ['drivers_name', 'unit', 'trailer', 'date_trip_started', 'date_trip_ended', 'trip', 'total_miles']:
                field_info = gemini_fields[field]
                current_value = str(edited_result.get(field, '')) if edited_result.get(field) else ''
                original_value = str(original_result.get(field, '')) if original_result.get(field) else ''
                
                new_value = st.text_input(
                    field_info['label'],
                    value=current_value,
                    key=f"{source_image}_{field}",
                    placeholder=f"Enter {field_info['label'].split(' ', 1)[1].lower()}" if ' ' in field_info['label'] else "Enter value"
                )
                
                # Update session state if changed
                if new_value != current_value:
                    st.session_state[f"edited_{source_image}"][field] = new_value
                    has_changes = True
                
                # Check if this field was changed from original
                if new_value != original_value and new_value.strip():
                    has_changes = True
        
        with col2:
            st.markdown("**Location Information:**")
            for field in ['trip_started_from', 'first_drop', 'second_drop', 'third_drop', 'forth_drop', 'inbound_pu', 'drop_off']:
                field_info = gemini_fields[field]
                current_value = edited_result.get(field, '')
                original_value = original_result.get(field, '')
                
                # Handle drop_off as list or string
                if isinstance(current_value, list):
                    current_value = ', '.join(current_value) if current_value else ''
                else:
                    current_value = str(current_value) if current_value else ''
                
                if isinstance(original_value, list):
                    original_value = ', '.join(original_value) if original_value else ''
                else:
                    original_value = str(original_value) if original_value else ''
                
                new_value = st.text_input(
                    field_info['label'],
                    value=current_value,
                    key=f"{source_image}_{field}",
                    placeholder=f"Enter {field_info['label'].split(' ', 1)[1].lower()}" if ' ' in field_info['label'] else "Enter location"
                )
                
                # Update session state if changed
                if new_value != current_value:
                    # Handle drop_off conversion back to array if needed
                    if field == 'drop_off' and ' to ' in new_value.lower():
                        st.session_state[f"edited_{source_image}"][field] = [loc.strip() for loc in new_value.split(' to ') if loc.strip()]
                    else:
                        st.session_state[f"edited_{source_image}"][field] = new_value
                    has_changes = True
                
                # Check if this field was changed from original
                if new_value != original_value and new_value.strip():
                    has_changes = True
        
        # Check if any field has been modified from the original
        current_edited = st.session_state[f"edited_{source_image}"]
        for field in gemini_fields.keys():
            original_val = str(original_result.get(field, '')) if original_result.get(field) else ''
            current_val = str(current_edited.get(field, '')) if current_edited.get(field) else ''
            
            # Special handling for drop_off arrays
            if field == 'drop_off':
                if isinstance(original_result.get(field), list):
                    original_val = ', '.join(original_result.get(field, []))
                if isinstance(current_edited.get(field), list):
                    current_val = ', '.join(current_edited.get(field, []))
            
            if current_val != original_val:
                has_changes = True
                break
        
        # Recalculate button
        st.markdown("---")
        col_btn1, col_btn2 = st.columns([1, 1])
        
        with col_btn1:
            if st.button(
                "🔄 Recalculate Distances", 
                disabled=not has_changes,
                key=f"recalc_{source_image}",
                help="Recalculate HERE API distances with updated values" if has_changes else "Make changes to fields above to enable recalculation"
            ):
                recalculate_distances_for_result(source_image)
        
        with col_btn2:
            if st.button(
                "↶ Reset to Original", 
                key=f"reset_{source_image}",
                help="Reset all fields to original Gemini extracted values"
            ):
                st.session_state[f"edited_{source_image}"] = original_result.copy()
                st.rerun()
        
        # Show changes indicator
        if has_changes:
            st.success("✅ Fields have been modified. Click 'Recalculate Distances' to update calculations.")
        
        # Distance calculations - Enhanced version from main_branch
        st.markdown("---")
        if 'distance_calculations' in current_edited:
            distance_data = current_edited['distance_calculations']
            
            st.write("**🗺️ Distance Calculations:**")
            st.write(f"📊 **Calculated Distance:** {distance_data.get('total_distance_miles', 0)} miles")
            st.write(f"🔗 **Successful Legs:** {distance_data.get('successful_calculations', 0)}/{distance_data.get('total_legs', 0)}")
            
            if distance_data.get('calculation_success'):
                # Enhanced route analysis info
                uses_here_api = any(leg.get('api_used') == 'HERE' for leg in distance_data.get('legs', []))
                uses_route_analysis = any(leg.get('route_analysis_used') for leg in distance_data.get('legs', []))
                
                if uses_here_api and uses_route_analysis:
                    st.success("🗺️ Using HERE Maps with polyline analysis to detect ALL states along the route")
                elif uses_here_api:
                    st.success("✅ **HERE API Routing** - Using HERE Maps routing service for accurate distances")
                    st.warning("⚠️ Route analysis unavailable - showing origin/destination states only")
                else:
                    st.info("ℹ️ **Basic Route Analysis** - Simple distance calculation")
                
                if 'state_mileage' in distance_data and distance_data['state_mileage']:
                    if uses_route_analysis:
                        st.write("**🗺️ Complete Route State Analysis:**")
                        st.caption("This includes ALL states the truck passes through, not just origin/destination")
                    else:
                        st.write("**🇺🇸 State Mileage Breakdown:**")
                    
                    for state_data in distance_data['state_mileage']:
                        if uses_route_analysis:
                            st.write(f"  🛣️ **{state_data['state']}:** {state_data['miles']} miles ({state_data['percentage']}%)")
                        else:
                            st.write(f"  📍 **{state_data['state']}:** {state_data['miles']} miles ({state_data['percentage']}%)")
                            
                    # Show route analysis details
                    if uses_route_analysis:
                        with st.expander("🔍 Route Analysis Details", expanded=False):
                            for i, leg in enumerate(distance_data.get('legs', [])):
                                if leg.get('route_analysis_used') and leg.get('state_assignment'):
                                    st.write(f"**Leg {i+1}:** {leg['origin']['location']} → {leg['destination']['location']}")
                                    st.write(f"  • Distance: {leg.get('distance_miles', 0)} miles")
                                    st.write(f"  • States traversed:")
                                    for state, miles in leg['state_assignment'].items():
                                        st.write(f"    - {state}: {miles} miles")
                                    st.write("---")
            else:
                # Show distance calculation errors
                st.error("❌ **Distance Calculation Failed**")
                
                if distance_data.get('error_summary'):
                    st.write(f"**Error:** {distance_data['error_summary']}")
                
                if distance_data.get('primary_error'):
                    st.write(f"**Primary Issue:** {distance_data['primary_error']}")
                
                # Show detailed errors for each leg
                if distance_data.get('legs'):
                    with st.expander("🔍 Detailed Error Information", expanded=True):
                        for i, leg in enumerate(distance_data['legs']):
                            if leg.get('calculation_failed'):
                                st.write(f"**❌ Leg {i+1}:** {leg['origin']['location']} → {leg['destination']['location']}")
                                if leg.get('error'):
                                    st.write(f"  • Error: {leg['error']}")
                            else:
                                st.write(f"**✅ Leg {i+1}:** {leg['origin']['location']} → {leg['destination']['location']}")
                
                # Show troubleshooting help
                st.info("""
                **💡 Troubleshooting Distance Calculation Issues:**
                
                - **Check HERE API Key:** Ensure your HERE API key is valid and has routing permissions
                - **API Limits:** You might have exceeded your API quota or rate limits
                - **Coordinate Issues:** Verify that geocoding found valid coordinates for all stops
                - **Service Status:** HERE API services might be temporarily unavailable
                
                **What happens now:** The system will still show extracted data, but without calculated distances and enhanced state analysis.
                """)
        
        # Fuel data display
        if current_edited.get('fuel_by_state') or current_edited.get('fuel_purchases'):
            st.markdown("---")
            st.markdown("**⛽ Fuel Purchases Summary:**")
            
            fuel_by_state = current_edited.get('fuel_by_state', {})
            total_gallons = current_edited.get('total_gallons', 0)
            
            if fuel_by_state:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write("**Gallons by State:**")
                    for state, gallons in sorted(fuel_by_state.items()):
                        st.write(f"  🌎 **{state}:** {gallons:.1f} gallons")
                
                with col2:
                    st.metric("🚛 Total Gallons", f"{total_gallons:.1f}")
                
                # Show raw fuel purchases if available
                if current_edited.get('fuel_purchases'):
                    with st.expander("🔍 Raw Fuel Purchase Details", expanded=False):
                        for i, purchase in enumerate(current_edited['fuel_purchases'], 1):
                            st.write(f"**Purchase {i}:** {purchase.get('gallons', 0)} gallons in {purchase.get('state', 'Unknown')}")
            else:
                st.info("No fuel purchase data found in this driver packet")
        
        # Validation warnings
        if show_validation_warnings and current_edited.get('validation_warnings'):
            st.markdown("---")
            st.markdown("**⚠️ Validation Warnings:**")
            for warning in current_edited['validation_warnings']:
                st.warning(warning)

def recalculate_distances_for_result(source_image):
    """Recalculate distances for a specific result using edited values"""
    if not st.session_state.processor:
        st.error("❌ Processor not initialized")
        return
    
    # Get edited result from session state
    edited_result = st.session_state[f"edited_{source_image}"]
    
    try:
        with st.spinner(f"🔄 Recalculating distances for {source_image}..."):
            # Step 4: Get coordinates for the edited locations
            use_here_api = st.session_state.get('use_here_api', True)
            coordinates_data = st.session_state.processor.get_coordinates_for_stops(edited_result, use_here_api)
            
            if coordinates_data:
                # Update coordinates in the edited result
                edited_result['coordinates'] = coordinates_data
                
                # Step 6: Calculate distances using new coordinates
                distance_data = st.session_state.processor.calculate_trip_distances(coordinates_data)
                edited_result['distance_calculations'] = distance_data
                
                # Compare extracted miles with new calculated miles
                extracted_miles = edited_result.get('total_miles', '')
                calculated_miles = distance_data.get('total_distance_miles', 0)
                
                if extracted_miles and calculated_miles > 0:
                    try:
                        extracted_miles_num = float(str(extracted_miles).replace(',', ''))
                        percentage_diff = abs((extracted_miles_num - calculated_miles) / calculated_miles * 100)
                        
                        # Update validation warnings
                        if 'validation_warnings' not in edited_result:
                            edited_result['validation_warnings'] = []
                        
                        # Remove old distance warnings
                        edited_result['validation_warnings'] = [
                            w for w in edited_result['validation_warnings'] 
                            if not w.startswith("Suspicious total miles:")
                        ]
                        
                        # Add new warning if needed
                        if percentage_diff > 5:
                            warning = f"Suspicious total miles: extracted ({extracted_miles_num}) differs from calculated ({calculated_miles:.1f}) by {percentage_diff:.1f}%"
                            edited_result['validation_warnings'].append(warning)
                    except ValueError:
                        pass
                
                # Update session state
                st.session_state[f"edited_{source_image}"] = edited_result
                
                # Also update the main processing results
                for i, result in enumerate(st.session_state.processing_results):
                    if result.get('source_image') == source_image:
                        st.session_state.processing_results[i] = edited_result.copy()
                        break
                
                st.success(f"✅ Distances recalculated successfully for {source_image}!")
                st.balloons()
                
                # Display summary of new calculations
                if distance_data.get('calculation_success'):
                    st.info(f"📊 New calculated distance: **{calculated_miles} miles** with {distance_data.get('successful_calculations', 0)} successful route calculations")
                    
                    # Show state mileage summary
                    if distance_data.get('state_mileage'):
                        state_summary = ", ".join([f"{s['state']}: {s['miles']}mi" for s in distance_data['state_mileage'][:3]])
                        if len(distance_data['state_mileage']) > 3:
                            state_summary += f" + {len(distance_data['state_mileage']) - 3} more states"
                        st.info(f"🇺🇸 State breakdown: {state_summary}")
                else:
                    st.warning("⚠️ Distance recalculation completed but some routes failed")
            else:
                st.error("❌ Failed to get coordinates for the edited locations")
                
    except Exception as e:
        st.error(f"❌ Error recalculating distances: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

def validation_report_tab():
    """Validation report tab"""
    st.header("🔍 Validation Report")
    
    if not st.session_state.processing_results:
        st.info("No results available. Please process some images first.")
        return
    
    results = st.session_state.processing_results
    successful_results = [r for r in results if r.get('processing_success')]
    
    # Validation summary
    validated_results = [r for r in successful_results if r.get('reference_validation', {}).get('validation_success')]
    
    if not validated_results:
        st.warning("⚠️ No validation data available. Make sure you have the reference CSV file.")
        return
    
    st.subheader("📊 Validation Summary")
    
    # Calculate validation metrics
    total_validated = len(validated_results)
    total_discrepancies = sum(len(r.get('reference_validation', {}).get('discrepancies', [])) for r in validated_results)
    avg_accuracy = sum(r.get('reference_validation', {}).get('accuracy_metrics', {}).get('field_accuracy', 0) for r in validated_results) / total_validated if total_validated > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("✅ Validated Images", total_validated)
    
    with col2:
        st.metric("📊 Average Accuracy", f"{avg_accuracy:.1%}")
    
    with col3:
        st.metric("⚠️ Total Discrepancies", total_discrepancies)
    
    # Detailed validation results
    st.subheader("📋 Detailed Validation Results")
    
    for result in validated_results:
        validation = result.get('reference_validation', {})
        accuracy = validation.get('accuracy_metrics', {})
        
        with st.expander(f"📄 {result['source_image']} - {accuracy.get('field_accuracy', 0):.1%} accuracy"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Accuracy Metrics:**")
                st.write(f"📊 **Field Accuracy:** {accuracy.get('field_accuracy', 0):.1%}")
                st.write(f"✅ **Matching Fields:** {accuracy.get('matching_fields', 0)}/{accuracy.get('total_fields', 0)}")
                st.write(f"📊 **Total Discrepancies:** {accuracy.get('total_discrepancies', 0)}")
            
            with col2:
                st.write("**Discrepancy Breakdown:**")
                st.write(f"🔴 **Critical:** {accuracy.get('critical_discrepancies', 0)}")
                st.write(f"🟠 **High:** {accuracy.get('high_discrepancies', 0)}")
                st.write(f"🟡 **Medium:** {accuracy.get('medium_discrepancies', 0)}")
                st.write(f"🔵 **Low:** {accuracy.get('low_discrepancies', 0)}")
            
            # Show discrepancies
            discrepancies = validation.get('discrepancies', [])
            if discrepancies:
                st.write("**Discrepancies Found:**")
                for discrepancy in discrepancies:
                    severity_color = {
                        'critical': '🔴',
                        'high': '🟠',
                        'medium': '🟡',
                        'low': '🔵'
                    }.get(discrepancy['severity'], '⚪')
                    
                    st.write(f"{severity_color} **{discrepancy['field']}:** `{discrepancy['extracted']}` ≠ `{discrepancy['reference']}`")

def export_data_tab():
    """Export data tab"""
    st.header("💾 Export Data")
    
    if not st.session_state.processing_results:
        st.info("No results available. Please process some images first.")
        return
    
    results = st.session_state.processing_results
    
    # Export options
    col1, col2 = st.columns(2)
    
    with col1:
        export_format = st.selectbox(
            "Export Format",
            ["Excel", "CSV (Distance)", "CSV (Fuel)", "JSON"],
            help="Choose the format for exporting results"
        )
    
    with col2:
        include_failed = st.checkbox(
            "Include Failed Results",
            value=False,
            help="Include images that failed to process"
        )
    
    # Filter results
    filtered_results = results if include_failed else [r for r in results if r.get('processing_success')]
    
    if not filtered_results:
        st.warning("No results to export with current filters.")
        return
    
    # Generate export data
    if export_format == "Excel":
        export_data = generate_excel_export(filtered_results)
        filename = f"driver_packet_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        st.download_button(
            label="📥 Download Excel (Both Sheets)",
            data=export_data,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    elif export_format == "CSV (Distance)":
        export_data = generate_csv_export(filtered_results)
        filename = f"driver_packet_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        st.download_button(
            label="📥 Download Distance Data CSV",
            data=export_data,
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )
    
    elif export_format == "CSV (Fuel)":
        export_data = generate_fuel_csv_export(filtered_results)
        filename = f"gallon_trip_env_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        st.download_button(
            label="📥 Download Fuel Data CSV",
            data=export_data,
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )
    
    elif export_format == "JSON":
        export_data = json.dumps(filtered_results, indent=2, ensure_ascii=False)
        filename = f"driver_packet_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        st.download_button(
            label="📥 Download JSON",
            data=export_data,
            file_name=filename,
            mime="application/json",
            use_container_width=True
        )
    
    # Preview data
    st.subheader("👀 Data Preview")
    
    if export_format == "Excel":
        # For Excel, show previews of both sheets
        distance_csv_data = generate_csv_export(filtered_results)
        df_distance = pd.read_csv(io.StringIO(distance_csv_data))
        st.write("**Driver Packet Results Sheet Preview:**")
        st.dataframe(df_distance, use_container_width=True)
        
        fuel_csv_data = generate_fuel_csv_export(filtered_results)
        df_fuel = pd.read_csv(io.StringIO(fuel_csv_data))
        if not df_fuel.empty:
            st.write("**Gallon Trip Env Sheet Preview:**")
            st.dataframe(df_fuel, use_container_width=True)
        else:
            st.write("**Gallon Trip Env Sheet:** No fuel data available in processed results")
    
    elif export_format == "CSV (Distance)":
        df = pd.read_csv(io.StringIO(export_data))
        st.dataframe(df, use_container_width=True)
    
    elif export_format == "CSV (Fuel)":
        df = pd.read_csv(io.StringIO(export_data))
        st.dataframe(df, use_container_width=True)
    
    elif export_format == "JSON":
        st.json(filtered_results[:2])  # Show first 2 results as preview

def generate_csv_export(results):
    """Generate CSV export.

    Columns: State, Envelop (Page No.), Truck, Trailer, State2, Total Miles
    """
    output = io.StringIO()

    # Header as per expected_output.csv
    fields = ['State', 'Envelop (Page No.)', 'Truck', 'Trailer', 'State2', 'Total Miles']
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()

    # State abbreviation to full name mapping
    state_full_names = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California', 'CO': 'Colorado',
        'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
        'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana',
        'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota',
        'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire',
        'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota',
        'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island',
        'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
        'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'
    }

    grand_total = 0

    for idx, result in enumerate(results, start=1):
        if not result.get('processing_success'):
            continue

        # Pull truck/unit and trailer from extracted data
        truck = result.get('unit', '')
        trailer = result.get('trailer', '')
        
        # Extract page number from image filename if available
        source_image = result.get('source_image', '')
        page_number = idx  # Default to sequential numbering
        
        # Try to extract page number from filename (e.g., "Page_8", "Page 8", or any number)
        import re
        page_match = re.search(r'[Pp]age[_\s]*(\d+)', source_image)
        if not page_match:
            # Try to find any number in the filename as fallback
            page_match = re.search(r'(\d+)', source_image)
        
        if page_match:
            try:
                page_number = int(page_match.group(1))
            except ValueError:
                pass  # Use default sequential numbering

        # Determine state mileage list
        state_mileage_data = None
        dc = result.get('distance_calculations', {})
        if isinstance(dc, dict) and dc.get('state_mileage'):
            state_mileage_data = dc['state_mileage']
        elif result.get('state_mileage'):
            state_mileage_data = result['state_mileage']
        else:
            state_mileage_data = []

        # Write one row per state
        for state_item in state_mileage_data:
            abbr = state_item.get('state', '')
            miles = state_item.get('miles', 0) or 0
            try:
                miles_int = int(round(float(miles)))
            except Exception:
                miles_int = 0

            full_name = state_full_names.get(abbr, abbr)

            writer.writerow({
                'State': full_name,
                'Envelop (Page No.)': page_number,
                'Truck': truck,
                'Trailer': trailer,
                'State2': abbr,
                'Total Miles': miles_int
            })

            grand_total += miles_int

    # Final total row with only Total Miles populated
    writer.writerow({'State': '', 'Envelop (Page No.)': '', 'Truck': '', 'Trailer': '', 'State2': '', 'Total Miles': grand_total})

    return output.getvalue()

def generate_fuel_csv_export(results):
    """Generate Gallon Trip Env CSV export.
    
    Columns: State, Gallons, Unit, Trip (Page No.)
    """
    output = io.StringIO()
    
    # Header as per plan requirements
    fields = ['State', 'Gallons', 'Unit', 'Trip (Page No.)']
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    
    for idx, result in enumerate(results, start=1):
        if not result.get('processing_success'):
            continue
        
        # Get unit and trip info
        unit = result.get('unit', '')
        
        # Extract page number from image filename if available
        source_image = result.get('source_image', '')
        page_number = idx  # Default to sequential numbering
        
        # Try to extract page number from filename (e.g., "Page_8", "Page 8", or any number)
        import re
        page_match = re.search(r'[Pp]age[_\s]*(\d+)', source_image)
        if not page_match:
            # Try to find any number in the filename as fallback
            page_match = re.search(r'(\d+)', source_image)
        
        if page_match:
            try:
                page_number = int(page_match.group(1))
            except ValueError:
                pass  # Use default sequential numbering
        
        # Get fuel data
        fuel_by_state = result.get('fuel_by_state', {})
        
        # Write one row per state with fuel purchases
        for state_abbr, gallons in fuel_by_state.items():
            writer.writerow({
                'State': state_abbr,
                'Gallons': round(gallons, 1),  # Round to 1 decimal place
                'Unit': unit,
                'Trip (Page No.)': page_number
            })
    
    return output.getvalue()

def generate_excel_export(results):
    """Generate Excel export data with multiple sheets"""
    output = io.BytesIO()
    
    # Generate both CSV data
    distance_csv_data = generate_csv_export(results)
    fuel_csv_data = generate_fuel_csv_export(results)
    
    # Create dataframes
    distance_df = pd.read_csv(io.StringIO(distance_csv_data))
    fuel_df = pd.read_csv(io.StringIO(fuel_csv_data))
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        distance_df.to_excel(writer, sheet_name='Driver Packet Results', index=False)
        if not fuel_df.empty:
            fuel_df.to_excel(writer, sheet_name='Gallon Trip Env', index=False)
    
    return output.getvalue()

if __name__ == "__main__":
    main() 