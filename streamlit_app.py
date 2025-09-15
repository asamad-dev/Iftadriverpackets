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
        <p>AI-Powered OCR and Distance Calculation for Driver Trip Sheets</p>
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
        company_set = st.text_input(
            "Enter Company Name (ASF Carrier ,INC)",
            type="default",
            # help="For enhanced geocoding and distance calculation. Get from: https://developer.here.com/",
            placeholder="Enter your company name..."
         )
        yard_Set = st.text_input(
            "Enter you Yard Name (San Bernardino, CA)",
            type="default",
           # help="For enhanced geocoding and distance calculation. Get from: https://developer.here.com/",
            placeholder="Enter your YArd Name..."
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
            "Use HERE API for Distance Calculation",
            value=bool(here_key),
            disabled=not bool(here_key),
            help="Enable advanced distance calculation and state mileage breakdown"
        )
        
        # Initialize processor

        if gemini_key:
            try:
                if not st.session_state.processor or not st.session_state.api_configured:
                    st.session_state.processor = GeminiDriverPacketProcessor(
                        api_key=gemini_key,
                        here_api_key=here_key if here_key else None,
                        #yard_location= yard_Set if yard_Set else 'Yard'
                    )
                    st.session_state.api_configured = True
                    st.success("✅ Processor initialized successfully!")
            except Exception as e:
                st.error(f"❌ Error initializing processor: {str(e)}")
                st.session_state.api_configured = False
        else:
            st.warning("⚠️ Please enter your Gemini API key to continue")
            st.session_state.api_configured = False

        if 'json_value_added' not in st.session_state:
            st.session_state.json_value_added = False
        if yard_Set and company_set:
            try:
                st.session_state.processor.company_name = company_set
                st.session_state.processor.yard_location = yard_Set
                st.success("✅ Processor initialized successfully!")
                if not st.session_state.json_value_added:
                    st.session_state.processor.add_yard_data(company_set, yard_Set)
                    st.session_state.json_value_added = True
                    st.success("✅ Value added to JSON successfully!")
            except Exception as e:
                st.error(f"❌ Error in add_value_in_json(): {str(e)}")
                st.session_state.api_configured = False
        else:
            if not company_set or not yard_Set:
                st.warning("⚠️ Please enter both Company Name and Yard Location.")

    
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
    
    #### 3. **Reference Data** (Optional)
    - Upload `driver - Sheet1.csv` to the input folder for validation
    - This enables accuracy comparison against known correct data
    """)

def upload_and_process_tab(processor, use_here_api):
    """Upload and process images tab"""
    st.header("📤 Upload Driver Packet Images")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose driver packet images",
        type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        help="Upload one or more driver packet images for processing"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully")
        
        # Display uploaded files
        with st.expander("📁 Uploaded Files", expanded=True):
            cols = st.columns(min(len(uploaded_files), 4))
            for i, uploaded_file in enumerate(uploaded_files):
                with cols[i % 4]:
                    st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)
        
        # Process button
        if st.button("🚀 Process Images", type="primary", use_container_width=True):
            process_images(uploaded_files, processor, use_here_api)

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
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📏 Total Extracted Miles", f"{total_miles:,.0f}")
        
        with col2:
            st.metric("🗺️ Total Calculated Distance", f"{total_distance_calculated:,.0f}")
        
        with col3:
            avg_miles = total_miles / len(successful) if successful else 0
            st.metric("📊 Average Miles per Trip", f"{avg_miles:,.0f}")

def show_result_card(result, show_validation_warnings):
    """Show individual result card"""
    with st.expander(f"📄 {result['source_image']}", expanded=False):
        if not result.get('processing_success'):
            st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
            return
        
        # Basic info
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Driver Information:**")
            st.write(f"👤 **Name:** {result.get('drivers_name', 'N/A')}")
            st.write(f"🚛 **Unit:** {result.get('unit', 'N/A')}")
            st.write(f"🚚 **Trailer:** {result.get('trailer', 'N/A')}")
            st.write(f"📅 **Trip Started:** {result.get('date_trip_started', 'N/A')}")
            st.write(f"📅 **Trip Ended:** {result.get('date_trip_ended', 'N/A')}")
        
        with col2:
            st.write("**Trip Details:**")
            st.write(f"🏁 **Started From:** {result.get('trip_started_from', 'N/A')}")
            st.write(f"📍 **1st Drop:** {result.get('first_drop', 'N/A')}")
            st.write(f"📍 **2nd Drop:** {result.get('second_drop', 'N/A')}")
            st.write(f"📍 **Inbound PU:** {result.get('inbound_pu', 'N/A')}")
            st.write(f"🏁 **Drop Off:** {result.get('drop_off', 'N/A')}")
            st.write(f"📏 **Total Miles:** {result.get('total_miles', 'N/A')}")
        
        # Distance calculations
        if 'distance_calculations' in result:
            distance_data = result['distance_calculations']
            if distance_data.get('calculation_success'):
                st.write("**🗺️ Distance Calculations:**")
                st.write(f"📊 **Calculated Distance:** {distance_data.get('total_distance_miles', 0)} miles")
                st.write(f"🔗 **Successful Legs:** {distance_data.get('successful_calculations', 0)}/{distance_data.get('total_legs', 0)}")
                
                # State mileage breakdown
                if 'state_mileage' in distance_data:
                    st.write("**🇺🇸 State Mileage Breakdown:**")
                    for state_data in distance_data['state_mileage']:
                        st.write(f"  • {state_data['state']}: {state_data['miles']} miles ({state_data['percentage']}%)")
        
        # Validation warnings
        if show_validation_warnings and result.get('validation_warnings'):
            st.write("**⚠️ Validation Warnings:**")
            for warning in result['validation_warnings']:
                st.warning(warning)

        # fuel_details
        if 'fuel_details' in result:
            st.write("**Fuel Details State by state:**")
            for fuel in result["fuel_details"]:
             city_state = fuel.get('City&State') or 'N/A'
             num_gal = fuel.get('# Gal.') or 'N/A'
             st.write(f"📍 **City and State:** {city_state}, **Number of Gal:** {num_gal}")
             #st.write(f"📍 **City and State:** {fuel['City&State']}, **Number of Gal:** {fuel['# Gal.']}")

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
            ["CSV", "JSON", "Excel"],
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
    if export_format == "CSV":
        export_data = generate_csv_export(filtered_results)
        filename = f"driver_packet_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        st.download_button(
            label="📥 Download CSV",
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
    
    elif export_format == "Excel":
        export_data = generate_excel_export(filtered_results)
        filename = f"driver_packet_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        st.download_button(
            label="📥 Download Excel",
            data=export_data,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    # Preview data
    st.subheader("👀 Data Preview")
    
    if export_format == "CSV":
        df = pd.read_csv(io.StringIO(export_data))
        st.dataframe(df, use_container_width=True)
    
    elif export_format == "JSON":
        st.json(filtered_results[:2])  # Show first 2 results as preview
    
    elif export_format == "Excel":
        # For Excel, show CSV preview
        csv_data = generate_csv_export(filtered_results)
        df = pd.read_csv(io.StringIO(csv_data))
        st.dataframe(df, use_container_width=True)

def generate_csv_export(results):
    """Generate CSV export data in state mileage format as per plan.md"""
    output = io.StringIO()
    
    # Collect all unique states from all results (as per plan.md format)
    all_states = set()
    for result in results:
        if result.get('processing_success'):
            # Check for state mileage in distance_calculations
            if 'distance_calculations' in result and 'state_mileage' in result['distance_calculations']:
                for state_data in result['distance_calculations']['state_mileage']:
                    all_states.add(state_data['state'])
            # Also check for state_mileage at root level
            elif 'state_mileage' in result:
                for state_data in result['state_mileage']:
                    all_states.add(state_data['state'])
    
    # Create field order: source_image + sorted state abbreviations (as per plan.md)
    fields = ['source_image'] + sorted(all_states)
    
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    
    for result in results:
        # Initialize row with source image
        row = {
            'source_image': result.get('source_image', 'PROCESSING_FAILED' if not result.get('processing_success') else '')
        }
        
        if result.get('processing_success'):
            # Add state mileage data
            state_mileage_data = None
            
            # Check distance_calculations first
            if 'distance_calculations' in result and 'state_mileage' in result['distance_calculations']:
                state_mileage_data = result['distance_calculations']['state_mileage']
            # Fallback to root level
            elif 'state_mileage' in result:
                state_mileage_data = result['state_mileage']
            
            if state_mileage_data:
                for state_data in state_mileage_data:
                    state = state_data['state']
                    miles = state_data.get('miles', 0)
                    if state in all_states:
                        row[state] = miles
        
        writer.writerow(row)
    
    return output.getvalue()

def generate_excel_export(results):
    """Generate Excel export data"""
    csv_data = generate_csv_export(results)
    df = pd.read_csv(io.StringIO(csv_data))

    #fuel details added in Excel different sheet Also
    #if page have multiple state it will create singel rows for that page and Plus Gallons of that state
    fuel_rows = []
    for page_num, result in enumerate(results, start=1):
        if result.get('processing_success') and 'fuel_details' in result:
            state_gal = {}
            for fuel in result['fuel_details']:
                # Extract state from City&State
                city_state = fuel.get('City&State', '')
               # state = city_state.split(',')[-1].strip() if ',' in city_state else ''
                if city_state and ',' in city_state:
                 state = city_state.split(',')[-1].strip()
                else:
                 state = ''
                gallons = fuel.get('# Gal.', 0)
                try:
                    gallons = float(gallons)
                except Exception:
                    gallons = 0
                # Sum gallons per state for this page
                state_gal[state] = state_gal.get(state, 0) + gallons
            # Add one row per state per page
            for state, total_gal in state_gal.items():
                fuel_rows.append({
                    'State': state,
                    'Gallons': total_gal,
                    'Unit': result.get('unit', ''),
                    'Trip (Page)': page_num
                })
    if fuel_rows:
        df_fuel = pd.DataFrame(fuel_rows)
    else:
        df_fuel = pd.DataFrame([{'No fuel details found': ''}])
  
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Driver Packet Results', index=False)
        #is used to creat different sheet for fuel details
        df_fuel.to_excel(writer, sheet_name='Fuel Details', index=False)
    
    return output.getvalue()

if __name__ == "__main__":
    main() 