#!/usr/bin/env python3
"""
Test module for Gemini API model diagnostics
"""

import os
import sys
import pytest
import google.generativeai as genai
from unittest.mock import patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import config

# Mark all tests in this module as 'diagnostic' and 'api'
pytestmark = [pytest.mark.diagnostic, pytest.mark.api]


class TestGeminiModelDiagnostics:
    """
    Diagnostic tests for Gemini API models.
    These tests help identify available models and troubleshoot API issues.
    """

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Ensure config is reloaded for each test"""
        import importlib
        if 'src.config' in sys.modules:
            importlib.reload(sys.modules['src.config'])
        
        global config
        from src.config import Config
        config = Config()

    def test_list_available_models(self):
        """List all available Gemini models for diagnostic purposes"""
        if not config.GEMINI_API_KEY:
            pytest.skip("GEMINI_API_KEY not configured, skipping model listing test.")
        
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            models = list(genai.list_models())
            
            assert len(models) > 0, "No models returned from Gemini API"
            
            print(f"\n📋 Found {len(models)} available Gemini models:")
            
            # Filter and display text generation models
            text_models = []
            for model in models:
                if hasattr(model, 'supported_generation_methods'):
                    if 'generateContent' in model.supported_generation_methods:
                        text_models.append(model)
                        print(f"  ✅ {model.name}")
                        if hasattr(model, 'display_name'):
                            print(f"      Display: {model.display_name}")
            
            assert len(text_models) > 0, "No text generation models found"
            print(f"\n🎯 Total text generation models: {len(text_models)}")
            
        except Exception as e:
            pytest.fail(f"Failed to list Gemini models: {str(e)}")

    def test_model_initialization_compatibility(self):
        """Test initialization of common Gemini models"""
        if not config.GEMINI_API_KEY:
            pytest.skip("GEMINI_API_KEY not configured, skipping model initialization test.")
        
        genai.configure(api_key=config.GEMINI_API_KEY)
        
        # Test models in order of preference
        test_models = [
            'gemini-1.5-flash',        # Current default
            'gemini-1.5-flash-latest', # Latest version
            'gemini-1.5-pro',          # Pro version
            'gemini-2.5-flash',        # Newer version
            'gemini-flash-latest',     # Generic latest
            'gemini-pro-vision',       # Vision capable
            'gemini-pro'               # Basic pro
        ]
        
        successful_models = []
        failed_models = []
        
        print(f"\n🧪 Testing model initialization:")
        
        for model_name in test_models:
            try:
                model = genai.GenerativeModel(model_name)
                successful_models.append(model_name)
                print(f"  ✅ {model_name} - SUCCESS")
            except Exception as e:
                failed_models.append((model_name, str(e)))
                print(f"  ❌ {model_name} - FAILED: {e}")
        
        # Assert that at least one model works
        assert len(successful_models) > 0, f"No models could be initialized. Failures: {failed_models}"
        
        # Check if our default model works
        if config.GEMINI_MODEL in [m for m in successful_models]:
            print(f"\n✅ Default model '{config.GEMINI_MODEL}' is working correctly")
        else:
            print(f"\n⚠️  Default model '{config.GEMINI_MODEL}' failed. Consider updating config.")
            if successful_models:
                print(f"   Recommended alternatives: {successful_models[:3]}")

    def test_current_config_model(self):
        """Test that the currently configured model works"""
        if not config.GEMINI_API_KEY:
            pytest.skip("GEMINI_API_KEY not configured, skipping current model test.")
        
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            model = genai.GenerativeModel(config.GEMINI_MODEL)
            
            print(f"\n✅ Current configured model '{config.GEMINI_MODEL}' initialized successfully")
            
            # Test a simple generation to ensure it's fully functional
            test_prompt = "Say 'Hello, World!' in JSON format."
            response = model.generate_content(test_prompt)
            
            assert response.text, "Model returned empty response"
            print(f"✅ Model response test passed: {response.text[:50]}...")
            
        except Exception as e:
            pytest.fail(f"Current configured model '{config.GEMINI_MODEL}' failed: {str(e)}")


def run_diagnostic():
    """Standalone diagnostic function for command-line use"""
    print("🔧 Gemini API Model Diagnostics")
    print("=" * 40)
    
    # Configure API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment variables")
        return
    
    genai.configure(api_key=api_key)
    print("✅ Gemini API configured")
    
    # List available models
    try:
        print("\n📋 Available Gemini models:")
        models = genai.list_models()
        text_models = []
        
        for model in models:
            if hasattr(model, 'supported_generation_methods'):
                if 'generateContent' in model.supported_generation_methods:
                    text_models.append(model.name)
                    print(f"  - {model.name}")
                    if hasattr(model, 'display_name'):
                        print(f"    Display name: {model.display_name}")
        
        print(f"\n🎯 Found {len(text_models)} text generation models")
        
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        return
    
    # Test specific models
    test_models = [
        'gemini-1.5-flash',
        'gemini-1.5-flash-latest', 
        'gemini-1.5-pro',
        'gemini-2.5-flash',
        'gemini-flash-latest',
        'gemini-pro-vision',
        'gemini-pro'
    ]
    
    print("\n🧪 Testing model initialization:")
    working_models = []
    
    for model_name in test_models:
        try:
            model = genai.GenerativeModel(model_name)
            working_models.append(model_name)
            print(f"  ✅ {model_name} - SUCCESS")
        except Exception as e:
            print(f"  ❌ {model_name} - FAILED: {e}")
    
    if working_models:
        print(f"\n🎉 {len(working_models)} models are working!")
        print(f"   Recommended: {working_models[0]}")
    else:
        print("\n❌ No models are working - check your API key and network connection")


if __name__ == "__main__":
    run_diagnostic()
