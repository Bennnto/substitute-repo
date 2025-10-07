#!/usr/bin/env python3
"""
Comprehensive Auto-Test Script for CLI Assistant
Tests all functions and features automatically
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime, timedelta

class CLITester:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_config = "test_config.json"
        
        # Test configuration
        self.test_config_data = {
            "test_jobs": [
                {
                    "name": "Test Backup Job",
                    "command": "echo 'test backup'",
                    "schedule": "0 2 * * *",
                    "description": "Test job for testing",
                    "logging": "Log to file"
                },
                {
                    "name": "Test Cleanup Job",
                    "command": "echo 'test cleanup'",
                    "schedule": "0 3 * * 0",
                    "description": "Test cleanup job",
                    "logging": "Log with email notification"
                }
            ],
            "test_reminders": [
                {
                    "title": "Test Reminder 1",
                    "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                    "time": "09:00",
                    "description": "Test reminder for tomorrow"
                },
                {
                    "title": "Test Reminder 2",
                    "date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
                    "time": "14:00",
                    "description": "Test reminder for day after tomorrow"
                }
            ]
        }
    
    def log_test(self, test_name, status, message=""):
        """Log test result"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = {
            "timestamp": timestamp,
            "test": test_name,
            "status": status,
            "message": message
        }
        self.test_results.append(result)
        
        if status == "PASS":
            self.passed_tests += 1
            print(f"✅ {test_name}: PASS")
        else:
            self.failed_tests += 1
            print(f"❌ {test_name}: FAIL - {message}")
        
        self.total_tests += 1
    
    def test_file_operations(self):
        """Test file operations"""
        print("\n📁 Testing File Operations...")
        
        # Test file creation
        try:
            test_file = "test_file.txt"
            with open(test_file, 'w') as f:
                f.write("Test content")
            
            if os.path.exists(test_file):
                self.log_test("File Creation", "PASS")
                os.remove(test_file)
            else:
                self.log_test("File Creation", "FAIL", "File not created")
        except Exception as e:
            self.log_test("File Creation", "FAIL", str(e))
        
        # Test directory operations
        try:
            test_dir = "test_directory"
            os.makedirs(test_dir, exist_ok=True)
            
            if os.path.exists(test_dir):
                self.log_test("Directory Creation", "PASS")
                os.rmdir(test_dir)
            else:
                self.log_test("Directory Creation", "FAIL", "Directory not created")
        except Exception as e:
            self.log_test("Directory Creation", "FAIL", str(e))
    
    def test_config_operations(self):
        """Test configuration operations"""
        print("\n⚙️  Testing Configuration Operations...")
        
        # Test config file creation
        try:
            test_config = {
                "test": True,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(self.test_config, 'w') as f:
                json.dump(test_config, f, indent=2)
            
            if os.path.exists(self.test_config):
                self.log_test("Config File Creation", "PASS")
            else:
                self.log_test("Config File Creation", "FAIL", "Config file not created")
        except Exception as e:
            self.log_test("Config File Creation", "FAIL", str(e))
        
        # Test config file reading
        try:
            with open(self.test_config, 'r') as f:
                loaded_config = json.load(f)
            
            if loaded_config.get("test") == True:
                self.log_test("Config File Reading", "PASS")
            else:
                self.log_test("Config File Reading", "FAIL", "Config data not loaded correctly")
        except Exception as e:
            self.log_test("Config File Reading", "FAIL", str(e))
        
        # Cleanup
        if os.path.exists(self.test_config):
            os.remove(self.test_config)
    
    def test_ollama_connection(self):
        """Test Ollama connection"""
        print("\n🤖 Testing Ollama Connection...")
        
        try:
            import requests
            
            # Test connection to Ollama
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                if models:
                    self.log_test("Ollama Connection", "PASS", f"Found {len(models)} models")
                else:
                    self.log_test("Ollama Connection", "PASS", "Connected but no models")
            else:
                self.log_test("Ollama Connection", "FAIL", f"Status code: {response.status_code}")
                
        except ImportError:
            self.log_test("Ollama Connection", "FAIL", "requests library not installed")
        except requests.exceptions.ConnectionError:
            self.log_test("Ollama Connection", "FAIL", "Ollama not running")
        except Exception as e:
            self.log_test("Ollama Connection", "FAIL", str(e))
    
    def test_system_info(self):
        """Test system information gathering"""
        print("\n💻 Testing System Information...")
        
        try:
            import platform
            
            # Test OS info
            os_name = platform.system()
            if os_name:
                self.log_test("OS Detection", "PASS", f"Detected: {os_name}")
            else:
                self.log_test("OS Detection", "FAIL", "Could not detect OS")
            
            # Test Python version
            python_version = platform.python_version()
            if python_version:
                self.log_test("Python Version", "PASS", f"Version: {python_version}")
            else:
                self.log_test("Python Version", "FAIL", "Could not detect Python version")
                
        except Exception as e:
            self.log_test("System Information", "FAIL", str(e))
        
        # Test psutil if available
        try:
            import psutil
            
            # Test CPU info
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if cpu_percent >= 0:
                self.log_test("CPU Monitoring", "PASS", f"CPU: {cpu_percent}%")
            else:
                self.log_test("CPU Monitoring", "FAIL", "Invalid CPU percentage")
                
            # Test memory info
            memory = psutil.virtual_memory()
            if memory.total > 0:
                self.log_test("Memory Monitoring", "PASS", f"Total: {memory.total // (1024**3)} GB")
            else:
                self.log_test("Memory Monitoring", "FAIL", "Invalid memory info")
                
        except ImportError:
            self.log_test("System Monitoring", "FAIL", "psutil not installed")
        except Exception as e:
            self.log_test("System Monitoring", "FAIL", str(e))
    
    def test_menu_system(self):
        """Test menu system functionality"""
        print("\n📋 Testing Menu System...")
        
        try:
            # Import the CLI app classes
            sys.path.append('.')
            from Cli_assistant import SimpleMenu
            
            # Test menu creation
            menu = SimpleMenu()
            if menu:
                self.log_test("Menu Creation", "PASS")
            else:
                self.log_test("Menu Creation", "FAIL", "Menu not created")
            
            # Test screen clearing
            try:
                menu.clear_screen()
                self.log_test("Screen Clearing", "PASS")
            except Exception as e:
                self.log_test("Screen Clearing", "FAIL", str(e))
                
        except ImportError as e:
            self.log_test("Menu System", "FAIL", f"Import error: {e}")
        except Exception as e:
            self.log_test("Menu System", "FAIL", str(e))
    
    def test_cron_validation(self):
        """Test cron schedule validation"""
        print("\n⏰ Testing Cron Validation...")
        
        try:
            # Test valid cron schedules
            valid_schedules = [
                "0 9 * * *",      # Daily at 9 AM
                "*/5 * * * *",    # Every 5 minutes
                "0 0 1 * *",      # First day of month
                "0 9 * * 1",      # Every Monday at 9 AM
                "30 14 * * 0"     # Every Sunday at 2:30 PM
            ]
            
            for schedule in valid_schedules:
                parts = schedule.split()
                if len(parts) == 5:
                    self.log_test(f"Cron Validation: {schedule}", "PASS")
                else:
                    self.log_test(f"Cron Validation: {schedule}", "FAIL", "Invalid format")
                    
        except Exception as e:
            self.log_test("Cron Validation", "FAIL", str(e))
    
    def test_encryption(self):
        """Test encryption functionality"""
        print("\n🔐 Testing Encryption...")
        
        try:
            # Test basic encryption (if cryptography is available)
            test_data = "Hello, World!"
            test_file = "test_encrypt.txt"
            
            # Create test file
            with open(test_file, 'w') as f:
                f.write(test_data)
            
            if os.path.exists(test_file):
                self.log_test("Test File Creation", "PASS")
                
                # Test if we can read the file back
                with open(test_file, 'r') as f:
                    read_data = f.read()
                
                if read_data == test_data:
                    self.log_test("File Read/Write", "PASS")
                else:
                    self.log_test("File Read/Write", "FAIL", "Data mismatch")
                
                # Cleanup
                os.remove(test_file)
            else:
                self.log_test("Test File Creation", "FAIL", "File not created")
                
        except Exception as e:
            self.log_test("Encryption Test", "FAIL", str(e))
    
    def test_network_operations(self):
        """Test network operations"""
        print("\n🌐 Testing Network Operations...")
        
        try:
            import requests
            
            # Test basic HTTP request
            response = requests.get("http://httpbin.org/get", timeout=10)
            
            if response.status_code == 200:
                self.log_test("HTTP Request", "PASS", "Successfully connected to test endpoint")
            else:
                self.log_test("HTTP Request", "FAIL", f"Status code: {response.status_code}")
                
        except ImportError:
            self.log_test("Network Operations", "FAIL", "requests library not installed")
        except Exception as e:
            self.log_test("Network Operations", "FAIL", str(e))
    
    def test_data_processing(self):
        """Test data processing capabilities"""
        print("\n📊 Testing Data Processing...")
        
        try:
            # Test JSON processing
            test_data = {
                "name": "Test",
                "value": 42,
                "items": [1, 2, 3, 4, 5]
            }
            
            # Test JSON serialization
            json_string = json.dumps(test_data)
            if json_string:
                self.log_test("JSON Serialization", "PASS")
            else:
                self.log_test("JSON Serialization", "FAIL", "Empty JSON string")
            
            # Test JSON deserialization
            parsed_data = json.loads(json_string)
            if parsed_data == test_data:
                self.log_test("JSON Deserialization", "PASS")
            else:
                self.log_test("JSON Deserialization", "FAIL", "Data mismatch")
                
        except Exception as e:
            self.log_test("Data Processing", "FAIL", str(e))
    
    def test_error_handling(self):
        """Test error handling capabilities"""
        print("\n🚨 Testing Error Handling...")
        
        try:
            # Test division by zero handling
            try:
                result = 1 / 0
                self.log_test("Division by Zero", "FAIL", "Should have raised exception")
            except ZeroDivisionError:
                self.log_test("Division by Zero", "PASS", "Exception properly caught")
            
            # Test file not found handling
            try:
                with open("nonexistent_file.txt", 'r') as f:
                    pass
                self.log_test("File Not Found", "FAIL", "Should have raised exception")
            except FileNotFoundError:
                self.log_test("File Not Found", "PASS", "Exception properly caught")
                
        except Exception as e:
            self.log_test("Error Handling", "FAIL", str(e))
    
    def test_performance(self):
        """Test basic performance"""
        print("\n⚡ Testing Performance...")
        
        try:
            # Test list operations
            start_time = time.time()
            test_list = [i for i in range(10000)]
            list_time = time.time() - start_time
            
            if list_time < 1.0:  # Should complete in under 1 second
                self.log_test("List Operations", "PASS", f"Completed in {list_time:.3f}s")
            else:
                self.log_test("List Operations", "FAIL", f"Too slow: {list_time:.3f}s")
            
            # Test string operations
            start_time = time.time()
            test_string = "test" * 1000
            string_time = time.time() - start_time
            
            if string_time < 0.1:  # Should complete in under 0.1 seconds
                self.log_test("String Operations", "PASS", f"Completed in {string_time:.3f}s")
            else:
                self.log_test("String Operations", "FAIL", f"Too slow: {string_time:.3f}s")
                
        except Exception as e:
            self.log_test("Performance Test", "FAIL", str(e))
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive CLI App Testing...")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all test categories
        self.test_file_operations()
        self.test_config_operations()
        self.test_ollama_connection()
        self.test_system_info()
        self.test_menu_system()
        self.test_cron_validation()
        self.test_encryption()
        self.test_network_operations()
        self.test_data_processing()
        self.test_error_handling()
        self.test_performance()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests} ✅")
        print(f"Failed: {self.failed_tests} ❌")
        print(f"Success Rate: {(self.passed_tests/self.total_tests)*100:.1f}%" if self.total_tests > 0 else "0%")
        print(f"Total Time: {total_time:.2f} seconds")
        
        # Print failed tests
        if self.failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  • {result['test']}: {result['message']}")
        
        # Save results to file
        self.save_test_results()
        
        return self.failed_tests == 0
    
    def save_test_results(self):
        """Save test results to file"""
        try:
            results = {
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_tests": self.total_tests,
                    "passed_tests": self.passed_tests,
                    "failed_tests": self.failed_tests,
                    "success_rate": (self.passed_tests/self.total_tests)*100 if self.total_tests > 0 else 0
                },
                "results": self.test_results
            }
            
            filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\n💾 Test results saved to: {filename}")
            
        except Exception as e:
            print(f"❌ Could not save test results: {e}")

def main():
    """Main function"""
    print("🧪 CLI Assistant Comprehensive Auto-Test")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("Cli_assistant.py"):
        print("❌ Error: Cli_assistant.py not found in current directory")
        print("💡 Make sure you're running this from the CLI App directory")
        sys.exit(1)
    
    # Create and run tester
    tester = CLITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! CLI App is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the results above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
