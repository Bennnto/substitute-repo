#!/usr/bin/env python3
"""
Simple Test Script for CLI Assistant
Tests core functionality without complex dependencies
"""

import os
import sys
import json
import time
from datetime import datetime

def test_basic_functionality():
    """Test basic functionality"""
    print("🧪 Testing Basic Functionality...")
    
    # Test 1: File operations
    try:
        test_file = "test_basic.txt"
        with open(test_file, 'w') as f:
            f.write("test")
        
        if os.path.exists(test_file):
            print("✅ File creation: PASS")
            os.remove(test_file)
        else:
            print("❌ File creation: FAIL")
    except Exception as e:
        print(f"❌ File creation: FAIL - {e}")
    
    # Test 2: JSON operations
    try:
        test_data = {"test": True}
        json_str = json.dumps(test_data)
        parsed = json.loads(json_str)
        
        if parsed == test_data:
            print("✅ JSON operations: PASS")
        else:
            print("❌ JSON operations: FAIL")
    except Exception as e:
        print(f"❌ JSON operations: FAIL - {e}")
    
    # Test 3: Time operations
    try:
        now = datetime.now()
        if now:
            print("✅ Time operations: PASS")
        else:
            print("❌ Time operations: FAIL")
    except Exception as e:
        print(f"❌ Time operations: FAIL - {e}")

def test_cli_import():
    """Test if CLI app can be imported"""
    print("\n📋 Testing CLI App Import...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, '.')
        
        # Try to import the CLI app
        import Cli_assistant
        print("✅ CLI app import: PASS")
        
        # Test if main class exists
        if hasattr(Cli_assistant, 'UltimateCronManager'):
            print("✅ Main class found: PASS")
        else:
            print("❌ Main class not found: FAIL")
        
        # Test if SimpleMenu class exists
        if hasattr(Cli_assistant, 'SimpleMenu'):
            print("✅ Menu class found: PASS")
        else:
            print("❌ Menu class not found: FAIL")
            
    except ImportError as e:
        print(f"❌ CLI app import: FAIL - {e}")
    except Exception as e:
        print(f"❌ CLI app import: FAIL - {e}")

def test_ollama_connection():
    """Test Ollama connection"""
    print("\n🤖 Testing Ollama Connection...")
    
    try:
        import requests
        
        # Test connection
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print(f"✅ Ollama connection: PASS - Found {len(models)} models")
            
            # List models
            for model in models:
                print(f"  📚 {model.get('name', 'Unknown')}")
        else:
            print(f"❌ Ollama connection: FAIL - Status {response.status_code}")
            
    except ImportError:
        print("❌ Ollama connection: FAIL - requests library not installed")
    except requests.exceptions.ConnectionError:
        print("❌ Ollama connection: FAIL - Ollama not running")
    except Exception as e:
        print(f"❌ Ollama connection: FAIL - {e}")

def test_system_info():
    """Test system information"""
    print("\n💻 Testing System Information...")
    
    try:
        import platform
        
        # OS info
        os_name = platform.system()
        print(f"✅ OS detection: PASS - {os_name}")
        
        # Python version
        python_version = platform.python_version()
        print(f"✅ Python version: PASS - {python_version}")
        
        # Architecture
        arch = platform.machine()
        print(f"✅ Architecture: PASS - {arch}")
        
    except Exception as e:
        print(f"❌ System info: FAIL - {e}")
    
    # Test psutil if available
    try:
        import psutil
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        print(f"✅ CPU monitoring: PASS - {cpu_percent}%")
        
        # Memory
        memory = psutil.virtual_memory()
        total_gb = memory.total // (1024**3)
        print(f"✅ Memory monitoring: PASS - {total_gb} GB total")
        
    except ImportError:
        print("❌ System monitoring: FAIL - psutil not installed")
    except Exception as e:
        print(f"❌ System monitoring: FAIL - {e}")

def test_menu_system():
    """Test menu system"""
    print("\n📋 Testing Menu System...")
    
    try:
        from Cli_assistant import SimpleMenu
        
        # Create menu instance
        menu = SimpleMenu()
        if menu:
            print("✅ Menu creation: PASS")
        else:
            print("❌ Menu creation: FAIL")
        
        # Test screen clearing
        try:
            menu.clear_screen()
            print("✅ Screen clearing: PASS")
        except Exception as e:
            print(f"❌ Screen clearing: FAIL - {e}")
            
    except Exception as e:
        print(f"❌ Menu system: FAIL - {e}")

def test_config_system():
    """Test configuration system"""
    print("\n⚙️  Testing Configuration System...")
    
    try:
        # Test config file operations
        test_config = {
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "jobs": [],
            "settings": {}
        }
        
        # Write config
        with open("test_config.json", 'w') as f:
            json.dump(test_config, f, indent=2)
        
        if os.path.exists("test_config.json"):
            print("✅ Config file creation: PASS")
        else:
            print("❌ Config file creation: FAIL")
        
        # Read config
        with open("test_config.json", 'r') as f:
            loaded_config = json.load(f)
        
        if loaded_config == test_config:
            print("✅ Config file reading: PASS")
        else:
            print("❌ Config file reading: FAIL")
        
        # Cleanup
        os.remove("test_config.json")
        
    except Exception as e:
        print(f"❌ Configuration system: FAIL - {e}")

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Simple CLI App Tests...")
    print("=" * 50)
    
    start_time = time.time()
    
    # Run tests
    test_basic_functionality()
    test_cli_import()
    test_ollama_connection()
    test_system_info()
    test_menu_system()
    test_config_system()
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print("\n" + "=" * 50)
    print("📊 TEST COMPLETED")
    print("=" * 50)
    print(f"Total time: {total_time:.2f} seconds")
    print("✅ All basic tests completed!")

if __name__ == "__main__":
    run_all_tests() 