#!/usr/bin/env python3
"""
Test runner for Driver Packet Processor
Provides convenient way to run different types of tests
"""

import sys
import os
import subprocess
from pathlib import Path


def run_config_tests():
    """Run configuration tests only"""
    print("🧪 Running Configuration Tests...")
    cmd = [sys.executable, "-m", "pytest", "test/test_config.py", "-v", "-x"]
    return subprocess.run(cmd).returncode


def run_api_tests():
    """Run API validation tests that check real connectivity"""
    print("🧪 Running API Validation Tests...")
    cmd = [sys.executable, "-m", "pytest", "test/test_api_validation.py", "-v", "-x"]
    return subprocess.run(cmd).returncode


def run_diagnostic_tests():
    """Run diagnostic tests for troubleshooting"""
    print("🔧 Running Diagnostic Tests...")
    cmd = [sys.executable, "-m", "pytest", "test/test_gemini_diagnostics.py", "-v", "-s"]
    return subprocess.run(cmd).returncode


def run_unit_tests():
    """Run all unit tests"""
    print("🧪 Running Unit Tests...")
    cmd = [sys.executable, "-m", "pytest", "test/", "-v", "-m", "unit or not integration"]
    return subprocess.run(cmd).returncode


def run_all_tests():
    """Run all tests"""  
    print("🧪 Running All Tests...")
    cmd = [sys.executable, "-m", "pytest", "test/", "-v"]
    return subprocess.run(cmd).returncode


def run_tests_with_coverage():
    """Run tests with coverage report"""
    print("🧪 Running Tests with Coverage...")
    cmd = [
        sys.executable, "-m", "pytest", 
        "test/", 
        "--cov=src", 
        "--cov-report=html", 
        "--cov-report=term-missing",
        "-v"
    ]
    return subprocess.run(cmd).returncode


def setup_test_environment():
    """Setup test environment"""
    print("🔧 Setting up test environment...")
    
    # Install test requirements
    cmd = [sys.executable, "-m", "pip", "install", "-r", "test/test_requirements.txt"]
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("❌ Failed to install test requirements")
        return False
        
    print("✅ Test environment setup complete")
    return True


def main():
    """Main test runner"""
    if len(sys.argv) < 2:
        print("🧪 Driver Packet Processor Test Runner")
        print("Usage: python run_tests.py <command>")
        print("\nCommands:")
        print("  setup     - Setup test environment")
        print("  config    - Run configuration tests only")
        print("  api       - Run API validation tests (real connectivity)")
        print("  diagnose  - Run diagnostic tests (troubleshooting)")
        print("  unit      - Run unit tests")
        print("  all       - Run all tests")
        print("  coverage  - Run tests with coverage")
        print("\nExamples:")
        print("  python run_tests.py setup")
        print("  python run_tests.py config")
        print("  python run_tests.py api")
        print("  python run_tests.py diagnose")
        print("  python run_tests.py coverage")
        return 1
    
    command = sys.argv[1].lower()
    
    # Change to project root directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    if command == "setup":
        return 0 if setup_test_environment() else 1
    elif command == "config":
        return run_config_tests()
    elif command == "api":
        return run_api_tests()
    elif command == "diagnose":
        return run_diagnostic_tests()
    elif command == "unit":
        return run_unit_tests()
    elif command == "all":
        return run_all_tests()  
    elif command == "coverage":
        return run_tests_with_coverage()
    else:
        print(f"❌ Unknown command: {command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
