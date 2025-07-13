#!/usr/bin/env python3
"""
Test script to verify the Voice Agent setup
"""
import sys
import os
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    try:
        from app.config import settings
        print("✓ Config module imported successfully")
        
        from app.models.schemas import TextQuery
        print("✓ Schemas module imported successfully")
        
        from app.services.knowledge_service import knowledge_service
        print("✓ Knowledge service imported successfully")
        
        from app.services.stt_service import stt_service
        print("✓ STT service imported successfully")
        
        from app.services.tts_service import tts_service
        print("✓ TTS service imported successfully")
        
        from app.services.llm_service import llm_service
        print("✓ LLM service imported successfully")
        
        from app.apis.voice_agent import router
        print("✓ Voice agent API imported successfully")
        
        from app.main import app
        print("✓ Main app imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_config():
    """Test configuration"""
    try:
        from app.config import settings
        
        print(f"✓ Config loaded:")
        print(f"  - Host: {settings.APP_HOST}")
        print(f"  - Port: {settings.APP_PORT}")
        print(f"  - Debug: {settings.DEBUG}")
        print(f"  - Knowledge Base Path: {settings.KNOWLEDGE_BASE_PATH}")
        
        if settings.DEEPGRAM_API_KEY == "your_deepgram_api_key_here":
            print("⚠️  Warning: Please set your actual Deepgram API key in .env file")
        else:
            print("✓ Deepgram API key configured")
            
        if settings.OPENAI_API_KEY == "your_openai_api_key_here":
            print("⚠️  Warning: Please set your actual OpenAI API key in .env file")
        else:
            print("✓ OpenAI API key configured")
            
        return True
        
    except Exception as e:
        print(f"✗ Config error: {e}")
        return False

def test_knowledge_base():
    """Test knowledge base directory"""
    try:
        from app.config import settings
        kb_path = Path(settings.KNOWLEDGE_BASE_PATH)
        
        if not kb_path.exists():
            print(f"⚠️  Knowledge base directory doesn't exist: {kb_path}")
            print("   Creating directory...")
            kb_path.mkdir(parents=True, exist_ok=True)
            print("✓ Knowledge base directory created")
        else:
            print(f"✓ Knowledge base directory exists: {kb_path}")
        
        pdf_files = list(kb_path.glob("*.pdf"))
        if pdf_files:
            print(f"✓ Found {len(pdf_files)} PDF files:")
            for pdf in pdf_files:
                print(f"  - {pdf.name}")
        else:
            print("⚠️  No PDF files found in knowledge base directory")
            print("   Add your PDF files to the knowledge_base/ directory")
            
        return True
        
    except Exception as e:
        print(f"✗ Knowledge base error: {e}")
        return False

def main():
    """Main test function"""
    print("Voice Agent Setup Test")
    print("=" * 30)
    
    tests = [
        ("Testing imports", test_imports),
        ("Testing configuration", test_config),
        ("Testing knowledge base", test_knowledge_base)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"✗ {test_name} failed")
    
    print(f"\n" + "=" * 30)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All tests passed! Your setup looks good.")
        print("\nNext steps:")
        print("1. Set your API keys in the .env file")
        print("2. Add PDF files to the knowledge_base/ directory")
        print("3. Run: python run.py")
        print("4. Open http://localhost:8000 in your browser")
    else:
        print("✗ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 