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

**Expected Output:**
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
Network URL: http://192.168.1.xxx:8501
```

### Using the Web Interface

1. **📁 Upload Images** - Drag & drop driver packet images
2. **⚙️ Configure Settings** - Adjust processing parameters
3. **🚀 Process** - Click to analyze uploaded images
4. **📊 View Results** - See extracted data, coordinates, distances
5. **💾 Download** - Export results as JSON or CSV

### Web App Features

- ✅ **Real-time processing** - Watch extraction in progress
- ✅ **Interactive maps** - Visualize routes and locations
- ✅ **Batch processing** - Handle multiple images at once
- ✅ **Configuration validation** - Check API keys and settings
- ✅ **Error handling** - Clear error messages and troubleshooting

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

### Run Configuration Tests
```bash
# Setup test environment (first time only)
# This installs pytest and other testing dependencies from test/test_requirements.txt
python run_tests.py setup

# Run configuration tests
python run_tests.py config

# Run API validation tests (requires real API keys in .env)
python run_tests.py api

# Run all unit tests
python run_tests.py unit

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
