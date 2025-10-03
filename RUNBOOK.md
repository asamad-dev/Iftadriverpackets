# 📖 Driver Packet Processor - Runbook

**Quick reference for common tasks and troubleshooting**

## 🚀 Getting Started

### 1. Initial Setup
```bash
# Clone and setup
git clone [repository]
cd Iftadriverpackets

# Create and activate virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file from template
cp .env.template .env

# Edit .env with your actual API keys
nano .env  # or code .env or notepad .env
```

### 2. Test Configuration
```bash
python config_demo.py
```
**Expected Output:** ✅ Configuration valid, API keys detected

---

## 🌐 Web Interface (Streamlit App)

### Run the Web Interface
```bash
# Ensure virtual environment is active
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Start the web app
streamlit run streamlit_app.py
```

### Troubleshooting Web App

**App won't start:**
```bash
# Install streamlit if missing
pip install streamlit

# Check if port is available
netstat -an | findstr :8501
```

**Configuration issues:**
```bash
# Validate config before starting
python config_demo.py

# Check API keys in web interface
# Go to Settings tab → API Configuration
```

**Performance issues:**
```bash
# Use optimized settings for web interface
LOG_LEVEL=WARNING
REDIRECT_STDOUT=false
OVERRIDE_PRINT=false
```

---

## 🧪 Testing

### Run Test Suites
```bash
# Setup test environment (first time only)
# This installs pytest and other testing dependencies from test/test_requirements.txt
python run_tests.py setup

# Run configuration tests
python run_tests.py config

# Run API validation tests (requires real API keys in .env)
python run_tests.py api

# Run diagnostic tests (troubleshooting)
python run_tests.py diagnose

# Run recalculation functionality tests (NEW!)
python run_tests.py recalc

# Run all unit tests
python run_tests.py unit

# Run all tests
python run_tests.py all

# Run with coverage report
python run_tests.py coverage
```

**What `test/test_requirements.txt` contains:**
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting  
- `pytest-mock` - Mocking utilities
- `mock`, `responses` - HTTP request mocking
- `black`, `flake8`, `mypy` - Code quality tools

The `setup` command automatically installs these testing dependencies.

### API Validation Tests

**New**: `test/test_api_validation.py` - **Real API key validation**:
- ✅ **Gemini API connectivity** - Tests if your GEMINI_API_KEY works
- ✅ **HERE API geocoding** - Tests if your HERE_API_KEY works for geocoding
- ✅ **HERE API routing** - Tests if your HERE_API_KEY works for routing
- ✅ **Integration workflow** - Tests complete geocoding → routing workflow

**Run only API tests:**
```bash
python run_tests.py api
```

**Note:** API tests require **real API keys** in your `.env` file and **internet connection**.

### Recalculation Tests (NEW!)

**`test/test_recalculation_core.py`** - **Core recalculation logic**:
- ✅ **Processor initialization** - Tests DriverPacketProcessor setup for recalculation
- ✅ **Coordinate retrieval** - Tests `get_coordinates_for_stops()` with edited locations
- ✅ **Distance calculation** - Tests `calculate_trip_distances()` with new coordinates
- ✅ **State analysis integration** - Tests enhanced state mileage distribution
- ✅ **Data flow validation** - Tests data transformation through recalculation chain

**`test/test_streamlit_recalculation.py`** - **Streamlit UI recalculation**:
- ✅ **Session state management** - Tests `get_current_results_with_edits()`
- ✅ **Debug functionality** - Tests `debug_result_state_data()`
- ✅ **Recalculation integration** - Tests full recalculation workflow
- ✅ **Error handling** - Tests geocoding and distance calculation failures
- ✅ **Export data integration** - Tests CSV export with recalculated data

**Run recalculation tests:**
```bash
python run_tests.py recalc
```

**What these tests validate:**
- **Edit → Recalculate workflow** works correctly
- **State mileage breakdown** appears after recalculation
- **Export data** includes recalculated results
- **Session state sync** between edited and main results
- **Error handling** for API failures during recalculation

### Manual Testing
```python
# Test configuration loading
python config_demo.py

# Test individual components
from src import Config
Config.print_configuration_summary()

# Validate configuration
validation = Config.validate_configuration()
print(f"Valid: {validation['is_valid']}")
```

---

## 🚀 Continuous Integration (CI/CD)

### GitHub Actions Workflows

**Automatic testing on every push and pull request:**

🧪 **`.github/workflows/ci.yml`** - Comprehensive testing:
- ✅ Tests on Python 3.9, 3.10, 3.11, 3.12
- ✅ Code linting (flake8), formatting (black), type checking (mypy)
- ✅ Unit tests with coverage reporting
- ✅ Security scanning (bandit, safety)
- ✅ Integration tests

🚀 **`.github/workflows/quick-test.yml`** - Fast feedback:
- ✅ Configuration tests on Python 3.11
- ✅ Import validation for all modules
- ✅ Configuration validation
- ✅ PR comments with test status

### Workflow Triggers

Both workflows run automatically on:
- **Push to main branch** - Ensures main stays stable
- **Pull requests to main** - Validates changes before merge

### Local Testing Before Push

```bash
# Run the same tests locally before pushing
python run_tests.py config
python run_tests.py unit

# Check code quality (like CI does)
black --check src/
flake8 src/ --max-line-length=88
mypy src/ --ignore-missing-imports
```

### CI Status Badges

Add to your README.md:
```markdown
![CI Tests](https://github.com/YOUR_USERNAME/Iftadriverpackets/workflows/🧪%20CI%20Tests/badge.svg)
![Quick Tests](https://github.com/YOUR_USERNAME/Iftadriverpackets/workflows/🚀%20Quick%20Tests/badge.svg)
```

---

## 🛠️ Maintenance Tasks

### Clear Caches
```python
from src import DriverPacketProcessor
processor = DriverPacketProcessor()
processor.clear_caches()
```

### Rotate Log Files
```bash
# Log files auto-rotate at 5MB, keep 3 backups
# Manual rotation:
mv temp/driver_packet.log temp/driver_packet.log.old
```

### Update Configuration
```bash
# Edit environment
nano .env

# Validate changes
python config_demo.py
```

### Backup Results
```bash
# Backup output folder
tar -czf backup_$(date +%Y%m%d).tar.gz output/

# Archive old logs
tar -czf logs_backup_$(date +%Y%m%d).tar.gz temp/*.log*
```

---

## 🚨 Emergency Procedures

### System Not Responding
1. Check API quotas/limits
2. Verify network connectivity  
3. Check log files for errors
4. Restart with minimal configuration

### Data Quality Issues
1. Enable DEBUG logging
2. Process single problem image
3. Check validation warnings
4. Compare with reference data if available

### Performance Degradation
1. Check timeout settings
2. Clear caches
3. Reduce sample point limits
4. Use great circle fallback (disable HERE API temporarily)

### Recalculation Issues (NEW!)

**Problem: State breakdown not showing after recalculation**
1. Enable "Show debug info" in Results Dashboard
2. Check if `distance_calculations.state_mileage` exists
3. Verify state analyzer is running: `enhanced_distance_data` should have state data
4. Run diagnostic: `python run_tests.py recalc`

**Problem: Export data hiding recalculated results**
1. Check if results have `processing_success: true`
2. Verify `get_current_results_with_edits()` returns edited data
3. Look for "NO_STATE_DATA" placeholder in CSV exports
4. Test with: `python -c "from streamlit_app import get_current_results_with_edits; print('Function exists')"`

**Problem: UI not refreshing after recalculation**
1. Check browser console for JavaScript errors
2. Verify `st.rerun()` is being called
3. Clear browser cache and reload
4. Check session state sync in debug info

**Problem: Recalculation taking too long**
1. Check HERE API rate limits (default: 0.1s between calls)
2. Reduce state analysis sample points in config
3. Monitor API quota usage
4. Use fallback geocoding if HERE API is slow

---

## 📈 Optimization Tips

### For Speed
```bash
# Reduce timeouts
GEOCODING_TIMEOUT=3
ROUTING_TIMEOUT=15

# Limit route analysis
ROUTE_SAMPLE_POINTS_MAX=10
HERE_RATE_LIMIT=0.05
```

### For Accuracy
```bash
# Increase timeouts  
GEOCODING_TIMEOUT=10
ROUTING_TIMEOUT=45

# More detailed analysis
ROUTE_SAMPLE_POINTS_MAX=25
MIN_STATE_MILES_THRESHOLD=0.5
```

### For Large Batches
```bash
# Optimize for throughput
LOG_LEVEL=WARNING
REDIRECT_STDOUT=false
OVERRIDE_PRINT=false
```

---

## 📞 Support Commands

### Diagnostic Information
```python
from src import Config, DriverPacketProcessor

# System info
Config.print_configuration_summary()

# Test all components
processor = DriverPacketProcessor()
print("✅ System initialized successfully")
```

### Generate Support Package
```bash
# Ensure virtual environment is active first
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Collect diagnostic info
python -c "from src import Config; Config.print_configuration_summary()" > diagnostics.txt
tail -100 temp/driver_packet.log >> diagnostics.txt
python --version >> diagnostics.txt
pip list >> diagnostics.txt
echo "Virtual env: $VIRTUAL_ENV" >> diagnostics.txt
```

---

**For additional help, check the logs in `temp/driver_packet.log` or run `python config_demo.py` for comprehensive system validation.**
