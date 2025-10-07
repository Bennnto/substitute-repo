#!/usr/bin/env python3
"""
Comprehensive Auto-Test for CLI Assistant
Tests all functions automatically without user interaction
"""

import os
import sys
import json
import time
import subprocess
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import io
from contextlib import redirect_stdout, redirect_stderr

class CLIAssistantTester:
    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0
        self.total = 0
        
        # Test configuration directory
        self.test_dir = "test_workspace"
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Setup isolated test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)
        os.chdir(self.test_dir)
    
    def cleanup_test_environment(self):
        """Cleanup test environment"""
        os.chdir("..")
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def log_test(self, test_name, status, message="", details=""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "details": details,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        self.test_results.append(result)
        
        if status == "PASS":
            print(f"✅ {test_name}")
            self.passed += 1
        else:
            print(f"❌ {test_name}: {message}")
            self.failed += 1
        
        self.total += 1
    
    def test_imports_and_classes(self):
        """Test if all classes and modules can be imported"""
        print("\n📦 Testing Imports and Class Definitions...")
        
        try:
            # Add parent directory to path
            sys.path.insert(0, '..')
            
            # Test main module import
            try:
                import Cli_assistant
                self.log_test("Main Module Import", "PASS")
            except Exception as e:
                self.log_test("Main Module Import", "FAIL", str(e))
                return
            
            # Test SimpleMenu class
            try:
                from Cli_assistant import SimpleMenu
                menu = SimpleMenu()
                self.log_test("SimpleMenu Class", "PASS")
            except Exception as e:
                self.log_test("SimpleMenu Class", "FAIL", str(e))
            
            # Test UltimateCronManager class
            try:
                from Cli_assistant import UltimateCronManager
                # Don't instantiate to avoid interactive prompts
                self.log_test("UltimateCronManager Class", "PASS")
            except Exception as e:
                self.log_test("UltimateCronManager Class", "FAIL", str(e))
        
        except Exception as e:
            self.log_test("Module Import", "FAIL", str(e))
    
    def test_menu_functions(self):
        """Test menu system functions"""
        print("\n📋 Testing Menu System Functions...")
        
        try:
            from Cli_assistant import SimpleMenu
            menu = SimpleMenu()
            
            # Test clear_screen
            try:
                menu.clear_screen()
                self.log_test("Menu Clear Screen", "PASS")
            except Exception as e:
                self.log_test("Menu Clear Screen", "FAIL", str(e))
            
            # Test show_input_prompt with mocked input
            try:
                with patch('builtins.input', return_value='test_input'):
                    result = menu.show_input_prompt("Test prompt", "default")
                    if result == 'test_input':
                        self.log_test("Menu Input Prompt", "PASS")
                    else:
                        self.log_test("Menu Input Prompt", "FAIL", f"Expected 'test_input', got '{result}'")
            except Exception as e:
                self.log_test("Menu Input Prompt", "FAIL", str(e))
            
            # Test show_confirmation
            try:
                with patch.object(menu, 'show_dropdown', return_value=0):
                    result = menu.show_confirmation("Test confirmation")
                    if isinstance(result, bool):
                        self.log_test("Menu Confirmation", "PASS")
                    else:
                        self.log_test("Menu Confirmation", "FAIL", "Should return boolean")
            except Exception as e:
                self.log_test("Menu Confirmation", "FAIL", str(e))
        
        except Exception as e:
            self.log_test("Menu System", "FAIL", str(e))
    
    def test_config_operations(self):
        """Test configuration file operations"""
        print("\n⚙️  Testing Configuration Operations...")
        
        try:
            from Cli_assistant import UltimateCronManager
            
            # Create a mock manager with minimal initialization
            with patch.object(UltimateCronManager, '__init__', lambda x: None):
                manager = UltimateCronManager()
                manager.config_file = "test_config.json"
                manager.config = {"test": True, "jobs": [], "settings": {}}
                
                # Test save_config
                try:
                    manager.save_config()
                    if os.path.exists("test_config.json"):
                        self.log_test("Config Save", "PASS")
                    else:
                        self.log_test("Config Save", "FAIL", "Config file not created")
                except Exception as e:
                    self.log_test("Config Save", "FAIL", str(e))
                
                # Test load_config
                try:
                    manager.load_config()
                    if isinstance(manager.config, dict):
                        self.log_test("Config Load", "PASS")
                    else:
                        self.log_test("Config Load", "FAIL", "Config not loaded as dict")
                except Exception as e:
                    self.log_test("Config Load", "FAIL", str(e))
        
        except Exception as e:
            self.log_test("Config Operations", "FAIL", str(e))
    
    def test_job_operations(self):
        """Test job management operations"""
        print("\n📋 Testing Job Operations...")
        
        try:
            from Cli_assistant import UltimateCronManager
            
            # Mock the manager initialization
            with patch.object(UltimateCronManager, '__init__', lambda x: None):
                manager = UltimateCronManager()
                manager.config = {"jobs": [], "settings": {}}
                manager.menu = MagicMock()
                
                # Test create_job_manual with mocked inputs
                test_job_data = {
                    "name": "Test Job",
                    "command": "echo 'test'",
                    "schedule": "0 9 * * *",
                    "description": "Test job description"
                }
                
                try:
                    with patch.object(manager.menu, 'show_input_prompt') as mock_input:
                        with patch.object(manager.menu, 'show_dropdown', return_value=0):
                            with patch.object(manager.menu, 'show_confirmation', return_value=True):
                                mock_input.side_effect = [
                                    test_job_data["name"],
                                    test_job_data["command"],
                                    test_job_data["schedule"],
                                    test_job_data["description"]
                                ]
                                
                                manager.save_config = MagicMock()
                                
                                # Call the function
                                with patch('builtins.input'):  # Mock the final input
                                    with patch('builtins.print'):  # Suppress prints
                                        manager.create_job_manual()
                                
                                # Check if job was added
                                if len(manager.config["jobs"]) > 0:
                                    self.log_test("Job Creation", "PASS")
                                else:
                                    self.log_test("Job Creation", "FAIL", "Job not added to config")
                
                except Exception as e:
                    self.log_test("Job Creation", "FAIL", str(e))
                
                # Test list_jobs
                try:
                    with patch('builtins.input'):  # Mock input for continue
                        with patch('builtins.print'):  # Suppress prints
                            manager.list_jobs()
                    self.log_test("Job Listing", "PASS")
                except Exception as e:
                    self.log_test("Job Listing", "FAIL", str(e))
        
        except Exception as e:
            self.log_test("Job Operations", "FAIL", str(e))
    
    def test_cron_validation(self):
        """Test cron schedule validation"""
        print("\n⏰ Testing Cron Validation...")
        
        try:
            from Cli_assistant import UltimateCronManager
            
            with patch.object(UltimateCronManager, '__init__', lambda x: None):
                manager = UltimateCronManager()
                
                # Test valid cron schedules
                valid_schedules = [
                    "0 9 * * *",      # Daily at 9 AM
                    "*/5 * * * *",    # Every 5 minutes
                    "0 0 1 * *",      # First day of month
                    "0 9 * * 1",      # Every Monday at 9 AM
                ]
                
                try:
                    for schedule in valid_schedules:
                        issues = manager.validate_cron_format(schedule)
                        if len(issues) == 0:
                            self.log_test(f"Cron Valid: {schedule}", "PASS")
                        else:
                            self.log_test(f"Cron Valid: {schedule}", "FAIL", f"Issues: {issues}")
                except Exception as e:
                    self.log_test("Cron Validation", "FAIL", str(e))
                
                # Test invalid cron schedules
                invalid_schedules = [
                    "invalid",        # Not a cron format
                    "60 9 * * *",     # Invalid minute
                    "0 25 * * *",     # Invalid hour
                ]
                
                try:
                    for schedule in invalid_schedules:
                        issues = manager.validate_cron_format(schedule)
                        if len(issues) > 0:
                            self.log_test(f"Cron Invalid: {schedule}", "PASS")
                        else:
                            self.log_test(f"Cron Invalid: {schedule}", "FAIL", "Should have found issues")
                except Exception as e:
                    self.log_test("Cron Invalid Tests", "FAIL", str(e))
        
        except Exception as e:
            self.log_test("Cron Validation", "FAIL", str(e))
    
    def test_system_monitor_functions(self):
        """Test system monitoring functions"""
        print("\n💻 Testing System Monitor Functions...")
        
        try:
            from Cli_assistant import UltimateCronManager
            
            with patch.object(UltimateCronManager, '__init__', lambda x: None):
                manager = UltimateCronManager()
                
                # Test system_info
                try:
                    with patch('builtins.input'):  # Mock input for continue
                        with patch('builtins.print'):  # Suppress prints
                            manager.system_info()
                    self.log_test("System Info", "PASS")
                except Exception as e:
                    self.log_test("System Info", "FAIL", str(e))
                
                # Test performance_monitor
                try:
                    with patch('builtins.input'):
                        with patch('builtins.print'):
                            manager.performance_monitor()
                    self.log_test("Performance Monitor", "PASS")
                except Exception as e:
                    self.log_test("Performance Monitor", "FAIL", str(e))
                
                # Test cpu_usage
                try:
                    with patch('builtins.input'):
                        with patch('builtins.print'):
                            manager.cpu_usage()
                    self.log_test("CPU Usage", "PASS")
                except Exception as e:
                    self.log_test("CPU Usage", "FAIL", str(e))
                
                # Test memory_usage
                try:
                    with patch('builtins.input'):
                        with patch('builtins.print'):
                            manager.memory_usage()
                    self.log_test("Memory Usage", "PASS")
                except Exception as e:
                    self.log_test("Memory Usage", "FAIL", str(e))
        
        except Exception as e:
            self.log_test("System Monitor", "FAIL", str(e))
    
    def test_file_operations(self):
        """Test file management functions"""
        print("\n📁 Testing File Operations...")
        
        try:
            from Cli_assistant import UltimateCronManager
            
            with patch.object(UltimateCronManager, '__init__', lambda x: None):
                manager = UltimateCronManager()
                manager.menu = MagicMock()
                
                # Test file browser
                try:
                    with patch('builtins.input'):
                        with patch('builtins.print'):
                            manager.file_browser()
                    self.log_test("File Browser", "PASS")
                except Exception as e:
                    self.log_test("File Browser", "FAIL", str(e))
                
                # Test backup_file_directory
                try:
                    # Create a test file to backup
                    test_file = "test_backup.txt"
                    with open(test_file, 'w') as f:
                        f.write("test content")
                    
                    with patch.object(manager.menu, 'show_input_prompt', return_value=test_file):
                        with patch('builtins.input'):
                            with patch('builtins.print'):
                                manager.backup_file_directory()
                    
                    # Check if backup was created
                    backup_files = [f for f in os.listdir('.') if f.startswith('backup_')]
                    if backup_files:
                        self.log_test("File Backup", "PASS")
                    else:
                        self.log_test("File Backup", "FAIL", "No backup file created")
                
                except Exception as e:
                    self.log_test("File Backup", "FAIL", str(e))
        
        except Exception as e:
            self.log_test("File Operations", "FAIL", str(e))
    
    def test_reminder_functions(self):
        """Test reminder and calendar functions"""
        print("\n⏰ Testing Reminder Functions...")
        
        try:
            from Cli_assistant import UltimateCronManager
            
            with patch.object(UltimateCronManager, '__init__', lambda x: None):
                manager = UltimateCronManager()
                manager.config = {"reminders": []}
                manager.menu = MagicMock()
                
                # Test add_reminder
                try:
                    test_reminder = {
                        "title": "Test Reminder",
                        "date": "2024-12-31",
                        "time": "09:00",
                        "description": "Test reminder description"
                    }
                    
                    with patch.object(manager.menu, 'show_input_prompt') as mock_input:
                        mock_input.side_effect = [
                            test_reminder["title"],
                            test_reminder["date"],
                            test_reminder["time"],
                            test_reminder["description"]
                        ]
                        
                        manager.save_config = MagicMock()
                        
                        with patch('builtins.input'):
                            with patch('builtins.print'):
                                manager.add_reminder()
                        
                        if len(manager.config["reminders"]) > 0:
                            self.log_test("Reminder Creation", "PASS")
                        else:
                            self.log_test("Reminder Creation", "FAIL", "Reminder not added")
                
                except Exception as e:
                    self.log_test("Reminder Creation", "FAIL", str(e))
                
                # Test list_reminders
                try:
                    with patch('builtins.input'):
                        with patch('builtins.print'):
                            manager.list_reminders()
                    self.log_test("Reminder Listing", "PASS")
                except Exception as e:
                    self.log_test("Reminder Listing", "FAIL", str(e))
                
                # Test view_calendar
                try:
                    with patch('builtins.input'):
                        with patch('builtins.print'):
                            manager.view_calendar()
                    self.log_test("Calendar View", "PASS")
                except Exception as e:
                    self.log_test("Calendar View", "FAIL", str(e))
        
        except Exception as e:
            self.log_test("Reminder Functions", "FAIL", str(e))
    
    def test_ollama_functions(self):
        """Test Ollama AI functions"""
        print("\n🤖 Testing Ollama Functions...")
        
        try:
            from Cli_assistant import UltimateCronManager
            
            with patch.object(UltimateCronManager, '__init__', lambda x: None):
                manager = UltimateCronManager()
                manager.config = {"ollama_settings": {"api_url": "http://localhost:11434"}}
                manager.menu = MagicMock()
                
                # Test change_default_model
                try:
                    with patch('requests.get') as mock_get:
                        # Mock successful response with models
                        mock_response = MagicMock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {
                            "models": [
                                {"name": "llama3.2:latest"},
                                {"name": "llama3.1:8b"}
                            ]
                        }
                        mock_get.return_value = mock_response
                        
                        with patch.object(manager.menu, 'show_dropdown', return_value=0):
                            manager.save_config = MagicMock()
                            
                            with patch('builtins.input'):
                                with patch('builtins.print'):
                                    manager.change_default_model()
                            
                            # Check if default model was set
                            if 'default_model' in manager.config.get('ollama_settings', {}):
                                self.log_test("Ollama Model Selection", "PASS")
                            else:
                                self.log_test("Ollama Model Selection", "FAIL", "Default model not set")
                
                except Exception as e:
                    self.log_test("Ollama Model Selection", "FAIL", str(e))
                
                # Test test_ollama_connection
                try:
                    with patch('requests.get') as mock_get:
                        mock_response = MagicMock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {"models": []}
                        mock_get.return_value = mock_response
                        
                        with patch('builtins.input'):
                            with patch('builtins.print'):
                                manager.test_ollama_connection()
                        
                        self.log_test("Ollama Connection Test", "PASS")
                
                except Exception as e:
                    self.log_test("Ollama Connection Test", "FAIL", str(e))
                
                # Test list_available_models
                try:
                    with patch('requests.get') as mock_get:
                        mock_response = MagicMock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {
                            "models": [
                                {"name": "llama3.2:latest", "size": 2000000000},
                                {"name": "llama3.1:8b", "size": 5000000000}
                            ]
                        }
                        mock_get.return_value = mock_response
                        
                        with patch('builtins.input'):
                            with patch('builtins.print'):
                                manager.list_available_models()
                        
                        self.log_test("Ollama Model Listing", "PASS")
                
                except Exception as e:
                    self.log_test("Ollama Model Listing", "FAIL", str(e))
        
        except Exception as e:
            self.log_test("Ollama Functions", "FAIL", str(e))
    
    def test_settings_functions(self):
        """Test settings and configuration functions"""
        print("\n⚙️  Testing Settings Functions...")
        
        try:
            from Cli_assistant import UltimateCronManager
            
            with patch.object(UltimateCronManager, '__init__', lambda x: None):
                manager = UltimateCronManager()
                manager.config = {"settings": {}}
                manager.menu = MagicMock()
                
                # Test change_theme
                try:
                    with patch.object(manager.menu, 'show_dropdown', return_value=1):  # Dark theme
                        manager.save_config = MagicMock()
                        
                        with patch('builtins.input'):
                            with patch('builtins.print'):
                                manager.change_theme()
                        
                        if manager.config["settings"].get("theme") == "Dark":
                            self.log_test("Theme Change", "PASS")
                        else:
                            self.log_test("Theme Change", "FAIL", "Theme not saved")
                
                except Exception as e:
                    self.log_test("Theme Change", "FAIL", str(e))
                
                # Test default_editor_settings
                try:
                    with patch.object(manager.menu, 'show_dropdown', return_value=0):  # nano
                        with patch.object(manager, 'test_editor_availability', return_value=True):
                            manager.save_config = MagicMock()
                            
                            with patch('builtins.input'):
                                with patch('builtins.print'):
                                    manager.default_editor_settings()
                        
                        self.log_test("Editor Settings", "PASS")
                
                except Exception as e:
                    self.log_test("Editor Settings", "FAIL", str(e))
                
                # Test statistics_display_settings
                try:
                    with patch.object(manager.menu, 'show_dropdown', return_value=1):  # Detailed
                        manager.save_config = MagicMock()
                        
                        with patch('builtins.input'):
                            with patch('builtins.print'):
                                manager.statistics_display_settings()
                        
                        self.log_test("Statistics Settings", "PASS")
                
                except Exception as e:
                    self.log_test("Statistics Settings", "FAIL", str(e))
        
        except Exception as e:
            self.log_test("Settings Functions", "FAIL", str(e))
    
    def test_security_functions(self):
        """Test security monitoring functions"""
        print("\n🔒 Testing Security Functions...")
        
        try:
            from Cli_assistant import UltimateCronManager
            
            with patch.object(UltimateCronManager, '__init__', lambda x: None):
                manager = UltimateCronManager()
                
                # Test password_check
                try:
                    with patch.object(manager.menu, 'show_input_prompt', return_value='TestPassword123!'):
                        with patch('builtins.input'):
                            with patch('builtins.print'):
                                manager.password_check()
                    self.log_test("Password Check", "PASS")
                except Exception as e:
                    self.log_test("Password Check", "FAIL", str(e))
                
                # Test security_scan
                try:
                    with patch('builtins.input'):
                        with patch('builtins.print'):
                            manager.security_scan()
                    self.log_test("Security Scan", "PASS")
                except Exception as e:
                    self.log_test("Security Scan", "FAIL", str(e))
                
                # Test file_permissions
                try:
                    with patch.object(manager.menu, 'show_input_prompt', return_value='.'):
                        with patch('builtins.input'):
                            with patch('builtins.print'):
                                manager.file_permissions()
                    self.log_test("File Permissions Check", "PASS")
                except Exception as e:
                    self.log_test("File Permissions Check", "FAIL", str(e))
        
        except Exception as e:
            self.log_test("Security Functions", "FAIL", str(e))
    
    def test_backup_restore_functions(self):
        """Test backup and restore functions"""
        print("\n💾 Testing Backup/Restore Functions...")
        
        try:
            from Cli_assistant import UltimateCronManager
            
            with patch.object(UltimateCronManager, '__init__', lambda x: None):
                manager = UltimateCronManager()
                manager.config = {"jobs": [], "reminders": []}
                
                # Test create_backup
                try:
                    with patch('builtins.print'):
                        manager.create_backup()
                    
                    # Check if backup directory was created
                    if os.path.exists("backups"):
                        backup_files = [f for f in os.listdir("backups") if f.startswith("config_backup_")]
                        if backup_files:
                            self.log_test("Backup Creation", "PASS")
                        else:
                            self.log_test("Backup Creation", "FAIL", "No backup files created")
                    else:
                        self.log_test("Backup Creation", "FAIL", "Backup directory not created")
                
                except Exception as e:
                    self.log_test("Backup Creation", "FAIL", str(e))
                
                # Test list_backups
                try:
                    with patch('builtins.print'):
                        manager.list_backups()
                    self.log_test("Backup Listing", "PASS")
                except Exception as e:
                    self.log_test("Backup Listing", "FAIL", str(e))
        
        except Exception as e:
            self.log_test("Backup/Restore Functions", "FAIL", str(e))
    
    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive CLI Assistant Auto-Test")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all test categories
        self.test_imports_and_classes()
        self.test_menu_functions()
        self.test_config_operations()
        self.test_job_operations()
        self.test_cron_validation()
        self.test_system_monitor_functions()
        self.test_file_operations()
        self.test_reminder_functions()
        self.test_ollama_functions()
        self.test_settings_functions()
        self.test_security_functions()
        self.test_backup_restore_functions()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Print comprehensive summary
        self.print_test_summary(total_time)
        
        # Save detailed results
        self.save_test_results()
        
        return self.failed == 0
    
    def print_test_summary(self, total_time):
        """Print detailed test summary"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.total}")
        print(f"Passed: {self.passed} ✅")
        print(f"Failed: {self.failed} ❌")
        
        if self.total > 0:
            success_rate = (self.passed / self.total) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"Total Time: {total_time:.2f} seconds")
        
        # Print failed tests details
        if self.failed > 0:
            print(f"\n❌ FAILED TESTS ({self.failed}):")
            print("-" * 40)
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  • {result['test']}: {result['message']}")
        
        # Print test categories summary
        categories = {}
        for result in self.test_results:
            category = result['test'].split(' ')[0] if ' ' in result['test'] else 'Other'
            if category not in categories:
                categories[category] = {'pass': 0, 'fail': 0}
            
            if result['status'] == 'PASS':
                categories[category]['pass'] += 1
            else:
                categories[category]['fail'] += 1
        
        print(f"\n📈 TEST CATEGORIES:")
        print("-" * 40)
        for category, counts in categories.items():
            total_cat = counts['pass'] + counts['fail']
            success_cat = (counts['pass'] / total_cat) * 100 if total_cat > 0 else 0
            print(f"  {category}: {counts['pass']}/{total_cat} ({success_cat:.1f}%)")
    
    def save_test_results(self):
        """Save detailed test results to file"""
        try:
            results = {
                "test_summary": {
                    "timestamp": datetime.now().isoformat(),
                    "total_tests": self.total,
                    "passed_tests": self.passed,
                    "failed_tests": self.failed,
                    "success_rate": (self.passed / self.total) * 100 if self.total > 0 else 0
                },
                "detailed_results": self.test_results,
                "environment": {
                    "python_version": sys.version,
                    "platform": sys.platform,
                    "working_directory": os.getcwd()
                }
            }
            
            filename = f"comprehensive_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\n💾 Detailed test results saved to: {filename}")
            
        except Exception as e:
            print(f"❌ Could not save test results: {e}")

def main():
    """Main function"""
    print("🧪 CLI Assistant Comprehensive Auto-Test Suite")
    print("=" * 50)
    
    # Check if CLI assistant exists
    if not os.path.exists("../Cli_assistant.py"):
        print("❌ Error: Cli_assistant.py not found in parent directory")
        print("💡 Make sure you're running this from the CLI App directory")
        sys.exit(1)
    
    # Create and run comprehensive tester
    tester = CLIAssistantTester()
    
    try:
        success = tester.run_all_tests()
        
        if success:
            print("\n🎉 All tests passed! CLI Assistant is fully functional.")
            exit_code = 0
        else:
            print("\n⚠️  Some tests failed. Check the detailed results above.")
            exit_code = 1
    
    except KeyboardInterrupt:
        print("\n⏸️  Test suite interrupted by user")
        exit_code = 2
    
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        exit_code = 3
    
    finally:
        # Cleanup test environment
        tester.cleanup_test_environment()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

