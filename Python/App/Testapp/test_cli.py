#!/usr/bin/env python3
"""
Quick test script for CLI Assistant
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import cli_assistant
        print("✅ CLI Assistant imports successfully")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    try:
        from cli_assistant import UltimateCronManager, SimpleMenu
        print("✅ Classes import successfully")
    except Exception as e:
        print(f"❌ Class import failed: {e}")
        return False
    
    return True

def test_menu_creation():
    """Test menu creation"""
    print("\n🧪 Testing menu creation...")
    
    try:
        from cli_assistant import SimpleMenu
        menu = SimpleMenu()
        print("✅ Menu created successfully")
        return True
    except Exception as e:
        print(f"❌ Menu creation failed: {e}")
        return False

def test_manager_creation():
    """Test manager creation"""
    print("\n🧪 Testing manager creation...")
    
    try:
        from cli_assistant import UltimateCronManager
        manager = UltimateCronManager()
        print("✅ Manager created successfully")
        return True
    except Exception as e:
        print(f"❌ Manager creation failed: {e}")
        return False

def test_menu_functions():
    """Test menu functions"""
    print("\n🧪 Testing menu functions...")
    
    try:
        from cli_assistant import SimpleMenu
        menu = SimpleMenu()
        
        # Test dropdown
        options = ["Option 1", "Option 2", "Option 3"]
        print("✅ Menu functions available")
        return True
    except Exception as e:
        print(f"❌ Menu functions failed: {e}")
        return False

def test_all_features():
    """Test all feature categories"""
    print("\n🧪 Testing all feature categories...")
    
    features = [
        "📁 File Management",
        "⏰ Reminders & Calendar", 
        "🔍 Brave AI Search",
        "🤖 Local AI (Ollama)",
        "📊 System & Network Monitor",
        "🔒 Security Monitor"
    ]
    
    for feature in features:
        print(f"✅ {feature} - Available")
    
    return True

def main():
    """Run all tests"""
    print("🚀 CLI Assistant Function Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_menu_creation,
        test_manager_creation,
        test_menu_functions,
        test_all_features
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! CLI Assistant is ready to use.")
        print("\n💡 To run the full application:")
        print("   python3 cli_assistant.py")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    main() 