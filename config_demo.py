#!/usr/bin/env python3
"""
Configuration Demonstration Script
Quick way to validate and explore your configuration setup
"""

from src import Config, config

def main():
    """Demonstrate the centralized configuration system"""
    
    print("🔧 Driver Packet Configuration Demo")
    print("=" * 40)
    
    # 1. Print current configuration summary
    Config.print_configuration_summary()
    
    # 2. Show key config values for debugging
    print("\n🔍 KEY VALUES:")
    print(f"  Gemini API: {'✅ Configured' if config.GEMINI_API_KEY else '❌ Missing'}")
    print(f"  HERE API: {'✅ Configured' if config.HERE_API_KEY else '❌ Missing'}")
    print(f"  Gemini Timeout: {config.GEMINI_TIMEOUT}s")
    print(f"  Geocoding Timeout: {config.GEOCODING_TIMEOUT}s")
    print(f"  Log Level: {config.LOG_LEVEL}")
    
    # 3. Quick setup guide
    if not config.GEMINI_API_KEY:
        print("\n💡 TO GET STARTED:")
        print("1. Copy env.template to .env")
        print("2. Add your GEMINI_API_KEY")
        print("3. Optionally add HERE_API_KEY")
        print("4. Run: python run_tests.py api")

if __name__ == "__main__":
    main()
