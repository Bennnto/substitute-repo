#!/usr/bin/env python3
"""
Comprehensive Test Suite for CLI Assistant
Tests all functions in cli_assistant.py
"""

import unittest
import sys
import os
import json
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock, call
from io import StringIO
import socket
import threading
import time

# Add the current directory to the path to import cli_assistant
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the modules to test
from cli_assistant import SimpleMenu, UltimateCronManager


class TestSimpleMenu(unittest.TestCase):
    """Test cases for SimpleMenu class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.menu = SimpleMenu()
    
    def test_init(self):
        """Test SimpleMenu initialization"""
        self.assertEqual(self.menu.current_selection, 0)
        self.assertEqual(self.menu.menu_stack, [])
    
    def test_clear_screen(self):
        """Test clear_screen method"""
        # This is hard to test directly, but we can ensure it doesn't crash
        try:
            self.menu.clear_screen()
        except Exception as e:
            self.fail(f"clear_screen raised an exception: {e}")
    
    @patch('sys.stdin')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setraw')
    def test_get_key_press_arrow_keys(self, mock_setraw, mock_tcsetattr, mock_tcgetattr, mock_stdin):
        """Test get_key_press with arrow keys"""
        # Mock the termios and tty modules for Unix systems
        mock_tcgetattr.return_value = [0, 0, 0, 0, 0, 0, 0]
        mock_stdin.fileno.return_value = 0
        mock_stdin.read.side_effect = ['\x1b', '[', 'A']  # UP arrow
        
        # This test is complex due to the interactive nature, so we'll test the fallback
        with patch('builtins.input', return_value='1'):
            result = self.menu.get_key_press()
            self.assertIsNotNone(result)
    
    def test_show_dropdown_basic(self):
        """Test basic dropdown functionality"""
        options = ["Option 1", "Option 2", "Option 3"]
        
        with patch('builtins.input', return_value='1'):
            with patch.object(self.menu, 'clear_screen'):
                with patch.object(self.menu, 'get_key_press', return_value='ENTER'):
                    result = self.menu.show_dropdown("Test Menu", options)
                    self.assertEqual(result, 0)  # First option selected
    
    def test_show_confirmation(self):
        """Test confirmation dialog"""
        with patch.object(self.menu, 'show_dropdown', return_value=0):
            result = self.menu.show_confirmation("Test message", default_yes=True)
            self.assertTrue(result)
        
        with patch.object(self.menu, 'show_dropdown', return_value=1):
            result = self.menu.show_confirmation("Test message", default_yes=False)
            self.assertFalse(result)
    
    def test_show_input_prompt(self):
        """Test input prompt"""
        with patch('builtins.input', return_value='test input'):
            with patch.object(self.menu, 'clear_screen'):
                result = self.menu.show_input_prompt("Enter value", "default")
                self.assertEqual(result, 'test input')
        
        with patch('builtins.input', return_value=''):
            with patch.object(self.menu, 'clear_screen'):
                result = self.menu.show_input_prompt("Enter value", "default")
                self.assertEqual(result, 'default')


class TestUltimateCronManager(unittest.TestCase):
    """Test cases for UltimateCronManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for test config files
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create a test config file
        self.test_config = {
            "jobs": [],
            "settings": {
                "theme": "dark",
                "auto_backup": False,
                "log_directory": "/tmp/logs"
            }
        }
        
        with open("cron_config.json", "w") as f:
            json.dump(self.test_config, f)
        
        self.manager = UltimateCronManager()
    
    def tearDown(self):
        """Clean up test fixtures"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    def test_init(self):
        """Test UltimateCronManager initialization"""
        self.assertIsNotNone(self.manager.menu)
        self.assertTrue(self.manager.running)
        self.assertEqual(self.manager.config_file, "cron_config.json")
        self.assertIn("jobs", self.manager.config)
        self.assertIn("settings", self.manager.config)
    
    def test_load_config(self):
        """Test config loading"""
        self.manager.load_config()
        self.assertIsInstance(self.manager.config, dict)
        self.assertIn("jobs", self.manager.config)
    
    def test_save_config(self):
        """Test config saving"""
        test_data = {"test": "data"}
        self.manager.config = test_data
        self.manager.save_config()
        
        # Verify the file was saved
        with open("cron_config.json", "r") as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data, test_data)
    
    def test_display_header(self):
        """Test header display"""
        # This is hard to test directly, but we can ensure it doesn't crash
        try:
            self.manager.display_header()
        except Exception as e:
            self.fail(f"display_header raised an exception: {e}")
    
    @patch.object(UltimateCronManager, 'handle_view_menu')
    def test_main_menu_selection(self, mock_handle_view):
        """Test main menu selection"""
        with patch.object(self.manager.menu, 'show_dropdown', return_value=0):
            self.manager.main_menu()
            mock_handle_view.assert_called_once()
    
    def test_create_job_wizard(self):
        """Test job creation wizard"""
        with patch.object(self.manager.menu, 'show_input_prompt', side_effect=[
            'Test Job', 'echo "hello"', '0 0 * * *', 'Test description'
        ]):
            with patch.object(self.manager.menu, 'show_dropdown', return_value=0):
                self.manager.create_job_wizard()
                
                # Check that a job was created
                self.assertEqual(len(self.manager.config['jobs']), 1)
                self.assertEqual(self.manager.config['jobs'][0]['name'], 'Test Job')
    
    def test_list_jobs_empty(self):
        """Test listing jobs when none exist"""
        with patch('builtins.print'):
            self.manager.list_jobs()
    
    def test_list_jobs_with_data(self):
        """Test listing jobs with data"""
        # Add a test job
        self.manager.config['jobs'] = [{
            'id': 1,
            'name': 'Test Job',
            'command': 'echo "test"',
            'schedule': '0 0 * * *',
            'enabled': True
        }]
        
        with patch('builtins.print'):
            self.manager.list_jobs()
    
    def test_search_jobs(self):
        """Test job search functionality"""
        # Add test jobs
        self.manager.config['jobs'] = [
            {'id': 1, 'name': 'Test Job 1', 'command': 'echo "test1"'},
            {'id': 2, 'name': 'Test Job 2', 'command': 'echo "test2"'}
        ]
        
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='Test'):
            with patch('builtins.print'):
                self.manager.search_jobs()
    
    def test_edit_job(self):
        """Test job editing"""
        # Add a test job
        self.manager.config['jobs'] = [{
            'id': 1,
            'name': 'Test Job',
            'command': 'echo "test"',
            'schedule': '0 0 * * *'
        }]
        
        with patch.object(self.manager.menu, 'show_dropdown', return_value=0):
            with patch.object(self.manager.menu, 'show_input_prompt', return_value='Updated Job'):
                self.manager.edit_job()
    
    def test_remove_job(self):
        """Test job removal"""
        # Add a test job
        self.manager.config['jobs'] = [{
            'id': 1,
            'name': 'Test Job',
            'command': 'echo "test"'
        }]
        
        with patch.object(self.manager.menu, 'show_dropdown', return_value=0):
            with patch.object(self.manager.menu, 'show_confirmation', return_value=True):
                self.manager.remove_job()
                self.assertEqual(len(self.manager.config['jobs']), 0)
    
    def test_toggle_job(self):
        """Test job enable/disable toggle"""
        # Add a test job
        self.manager.config['jobs'] = [{
            'id': 1,
            'name': 'Test Job',
            'command': 'echo "test"',
            'enabled': True
        }]
        
        with patch.object(self.manager.menu, 'show_dropdown', return_value=0):
            self.manager.toggle_job()
            self.assertFalse(self.manager.config['jobs'][0]['enabled'])
    
    def test_show_statistics(self):
        """Test statistics display"""
        with patch('builtins.print'):
            self.manager.show_statistics()
    
    def test_create_job_manual(self):
        """Test manual job creation"""
        with patch.object(self.manager.menu, 'show_input_prompt', side_effect=[
            'Manual Job', 'echo "manual"', '0 0 * * *', 'Manual description'
        ]):
            with patch.object(self.manager.menu, 'show_dropdown', return_value=0):
                self.manager.create_job_manual()
                self.assertEqual(len(self.manager.config['jobs']), 1)
    
    def test_import_job(self):
        """Test job import functionality"""
        # Create a test import file
        import_data = {
            'name': 'Imported Job',
            'command': 'echo "imported"',
            'schedule': '0 0 * * *'
        }
        
        with open('test_import.json', 'w') as f:
            json.dump(import_data, f)
        
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='test_import.json'):
            self.manager.import_job()
            self.assertEqual(len(self.manager.config['jobs']), 1)
    
    def test_change_theme(self):
        """Test theme changing"""
        with patch.object(self.manager.menu, 'show_dropdown', return_value=0):
            self.manager.change_theme()
    
    def test_auto_backup_settings(self):
        """Test auto backup settings"""
        with patch.object(self.manager.menu, 'show_dropdown', return_value=0):
            with patch('builtins.print'):
                self.manager.auto_backup_settings()
    
    def test_log_directory_settings(self):
        """Test log directory settings"""
        with patch.object(self.manager.menu, 'show_dropdown', return_value=0):
            with patch.object(self.manager.menu, 'show_input_prompt', return_value='/tmp/logs'):
                self.manager.log_directory_settings()
    
    def test_view_log_files(self):
        """Test log file viewing"""
        with patch('builtins.print'):
            self.manager.view_log_files()
    
    def test_clear_logs(self):
        """Test log clearing"""
        with patch.object(self.manager.menu, 'show_confirmation', return_value=True):
            with patch('builtins.print'):
                self.manager.clear_logs()
    
    def test_default_editor_settings(self):
        """Test default editor settings"""
        with patch.object(self.manager.menu, 'show_dropdown', return_value=0):
            with patch.object(self.manager.menu, 'show_input_prompt', return_value='nano'):
                self.manager.default_editor_settings()
    
    def test_test_editor_availability(self):
        """Test editor availability checking"""
        result = self.manager.test_editor_availability('nano')
        self.assertIsInstance(result, bool)
    
    def test_statistics_display_settings(self):
        """Test statistics display settings"""
        with patch.object(self.manager.menu, 'show_dropdown', return_value=0):
            self.manager.statistics_display_settings()
    
    def test_set_statistics_mode(self):
        """Test statistics mode setting"""
        self.manager.set_statistics_mode("Simple")
        # Verify the mode was set (implementation dependent)
    
    def test_test_command(self):
        """Test command testing functionality"""
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='echo "test"'):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "test"
                self.manager.test_command()
    
    def test_export_jobs(self):
        """Test job export functionality"""
        # Add a test job
        self.manager.config['jobs'] = [{
            'id': 1,
            'name': 'Test Job',
            'command': 'echo "test"'
        }]
        
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='export.json'):
            self.manager.export_jobs()
            
            # Verify export file was created
            self.assertTrue(os.path.exists('export.json'))
    
    def test_import_jobs(self):
        """Test job import functionality"""
        # Create test import file
        import_data = {
            'jobs': [{'name': 'Imported Job', 'command': 'echo "imported"'}]
        }
        
        with open('test_import.json', 'w') as f:
            json.dump(import_data, f)
        
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='test_import.json'):
            with patch.object(self.manager.menu, 'show_confirmation', return_value=True):
                self.manager.import_jobs()
    
    def test_backup_restore(self):
        """Test backup and restore functionality"""
        with patch.object(self.manager.menu, 'show_dropdown', return_value=0):
            with patch('builtins.print'):
                self.manager.backup_restore()
    
    def test_create_backup(self):
        """Test backup creation"""
        with patch('builtins.print'):
            self.manager.create_backup()
    
    def test_restore_backup(self):
        """Test backup restoration"""
        # Create a test backup
        backup_data = {
            'backup_info': {'created': '2023-01-01', 'total_jobs': 1},
            'jobs': [{'name': 'Backup Job', 'command': 'echo "backup"'}]
        }
        
        os.makedirs('backups', exist_ok=True)
        with open('backups/test_backup.json', 'w') as f:
            json.dump(backup_data, f)
        
        with patch.object(self.manager.menu, 'show_dropdown', return_value=0):
            with patch.object(self.manager.menu, 'show_confirmation', return_value=True):
                self.manager.restore_backup()
    
    def test_list_backups(self):
        """Test backup listing"""
        with patch('builtins.print'):
            self.manager.list_backups()
    
    def test_monitor_jobs(self):
        """Test job monitoring"""
        with patch('builtins.print'):
            self.manager.monitor_jobs()
    
    def test_validate_syntax(self):
        """Test syntax validation"""
        with patch('builtins.print'):
            self.manager.validate_syntax()
    
    def test_validate_all_jobs(self):
        """Test validation of all jobs"""
        with patch('builtins.print'):
            self.manager.validate_all_jobs()
    
    def test_validate_single_job(self):
        """Test single job validation"""
        with patch('builtins.print'):
            self.manager.validate_single_job()
    
    def test_validate_job_syntax(self):
        """Test job syntax validation"""
        test_job = {
            'name': 'Test Job',
            'command': 'echo "test"',
            'schedule': '0 0 * * *'
        }
        
        result = self.manager.validate_job_syntax(test_job)
        self.assertIsInstance(result, bool)
    
    def test_validate_cron_format(self):
        """Test cron format validation"""
        valid_schedule = "0 0 * * *"
        invalid_schedule = "invalid"
        
        self.assertTrue(self.manager.validate_cron_format(valid_schedule))
        self.assertFalse(self.manager.validate_cron_format(invalid_schedule))
    
    def test_validate_cron_field(self):
        """Test cron field validation"""
        self.assertTrue(self.manager.validate_cron_field("5", 0, 59))
        self.assertFalse(self.manager.validate_cron_field("70", 0, 59))
        self.assertTrue(self.manager.validate_cron_field("*", 0, 59))
    
    def test_validate_command(self):
        """Test command validation"""
        self.assertTrue(self.manager.validate_command("echo 'test'"))
        self.assertFalse(self.manager.validate_command(""))
    
    def test_test_cron_schedule(self):
        """Test cron schedule testing"""
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='0 0 * * *'):
            with patch('builtins.print'):
                self.manager.test_cron_schedule()
    
    def test_fix_common_issues(self):
        """Test common issues fixing"""
        with patch('builtins.print'):
            self.manager.fix_common_issues()
    
    # File Management Tests
    def test_encrypt_file(self):
        """Test file encryption"""
        # Create a test file
        with open('test.txt', 'w') as f:
            f.write('test content')
        
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='test.txt'):
            with patch('builtins.print'):
                self.manager.encrypt_file()
    
    def test_decrypt_file(self):
        """Test file decryption"""
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='test.txt.enc'):
            with patch('builtins.print'):
                self.manager.decrypt_file()
    
    def test_download_large_file(self):
        """Test large file download"""
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='http://example.com/file.zip'):
            with patch('builtins.print'):
                self.manager.download_large_file()
    
    def test_backup_file_directory(self):
        """Test file/directory backup"""
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='test.txt'):
            with patch('builtins.print'):
                self.manager.backup_file_directory()
    
    def test_file_browser(self):
        """Test file browser functionality"""
        with patch('builtins.print'):
            self.manager.file_browser()
    
    def test_sync_files(self):
        """Test file synchronization"""
        with patch('builtins.print'):
            self.manager.sync_files()
    
    # Reminders and Calendar Tests
    def test_add_reminder(self):
        """Test reminder addition"""
        with patch.object(self.manager.menu, 'show_input_prompt', side_effect=[
            'Test Reminder', '2023-12-31', '12:00', 'Test description'
        ]):
            with patch('builtins.print'):
                self.manager.add_reminder()
    
    def test_view_calendar(self):
        """Test calendar viewing"""
        with patch('builtins.print'):
            self.manager.view_calendar()
    
    def test_set_timer(self):
        """Test timer setting"""
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='60'):
            with patch('builtins.print'):
                self.manager.set_timer()
    
    def test_list_reminders(self):
        """Test reminder listing"""
        with patch('builtins.print'):
            self.manager.list_reminders()
    
    def test_delete_reminder(self):
        """Test reminder deletion"""
        with patch('builtins.print'):
            self.manager.delete_reminder()
    
    def test_sync_calendar(self):
        """Test calendar synchronization"""
        with patch('builtins.print'):
            self.manager.sync_calendar()
    
    # Brave Search Tests
    def test_brave_web_search(self):
        """Test Brave web search"""
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='test query'):
            with patch('builtins.print'):
                self.manager.brave_web_search()
    
    def test_brave_news_search(self):
        """Test Brave news search"""
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='test news'):
            with patch('builtins.print'):
                self.manager.brave_news_search()
    
    def test_brave_image_search(self):
        """Test Brave image search"""
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='test image'):
            with patch('builtins.print'):
                self.manager.brave_image_search()
    
    def test_brave_document_search(self):
        """Test Brave document search"""
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='test document'):
            with patch('builtins.print'):
                self.manager.brave_document_search()
    
    def test_brave_video_search(self):
        """Test Brave video search"""
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='test video'):
            with patch('builtins.print'):
                self.manager.brave_video_search()
    
    def test_brave_analytics_search(self):
        """Test Brave analytics search"""
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='test analytics'):
            with patch('builtins.print'):
                self.manager.brave_analytics_search()
    
    # Ollama AI Tests
    def test_ollama_chat(self):
        """Test Ollama chat functionality"""
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='Hello'):
            with patch('builtins.print'):
                self.manager.ollama_chat()
    
    def test_ollama_generate_text(self):
        """Test Ollama text generation"""
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='Write a story'):
            with patch('builtins.print'):
                self.manager.ollama_generate_text()
    
    def test_ollama_ask_questions(self):
        """Test Ollama question answering"""
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='What is AI?'):
            with patch('builtins.print'):
                self.manager.ollama_ask_questions()
    
    def test_ollama_analyze_data(self):
        """Test Ollama data analysis"""
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='Analyze this data'):
            with patch('builtins.print'):
                self.manager.ollama_analyze_data()
    
    def test_ollama_generate_images(self):
        """Test Ollama image generation"""
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='A beautiful sunset'):
            with patch('builtins.print'):
                self.manager.ollama_generate_images()
    
    def test_ollama_document_analysis(self):
        """Test Ollama document analysis"""
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='test.txt'):
            with patch('builtins.print'):
                self.manager.ollama_document_analysis()
    
    def test_ollama_settings(self):
        """Test Ollama settings"""
        with patch.object(self.manager.menu, 'show_dropdown', return_value=0):
            with patch('builtins.print'):
                self.manager.ollama_settings()
    
    def test_change_default_model(self):
        """Test default model changing"""
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='llama2'):
            with patch('builtins.print'):
                self.manager.change_default_model()
    
    def test_set_ollama_api_url(self):
        """Test Ollama API URL setting"""
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='http://localhost:11434'):
            with patch('builtins.print'):
                self.manager.set_ollama_api_url()
    
    def test_configure_model_parameters(self):
        """Test model parameter configuration"""
        with patch.object(self.manager.menu, 'show_input_prompt', return_value='0.7'):
            with patch('builtins.print'):
                self.manager.configure_model_parameters()
    
    def test_list_available_models(self):
        """Test available models listing"""
        with patch('builtins.print'):
            self.manager.list_available_models()
    
    def test_test_ollama_connection(self):
        """Test Ollama connection testing"""
        with patch('builtins.print'):
            self.manager.test_ollama_connection()
    
    # System Monitor Tests
    def test_system_info(self):
        """Test system information display"""
        with patch('builtins.print'):
            self.manager.system_info()
    
    def test_network_status(self):
        """Test network status checking"""
        with patch('builtins.print'):
            self.manager.network_status()
    
    def test_performance_monitor(self):
        """Test performance monitoring"""
        with patch('builtins.print'):
            self.manager.performance_monitor()
    
    def test_cpu_usage(self):
        """Test CPU usage monitoring"""
        with patch('builtins.print'):
            self.manager.cpu_usage()
    
    def test_memory_usage(self):
        """Test memory usage monitoring"""
        with patch('builtins.print'):
            self.manager.memory_usage()
    
    def test_disk_usage(self):
        """Test disk usage monitoring"""
        with patch('builtins.print'):
            self.manager.disk_usage()
    
    def test_network_traffic(self):
        """Test network traffic monitoring"""
        with patch('builtins.print'):
            self.manager.network_traffic()
    
    def test_process_monitor(self):
        """Test process monitoring"""
        with patch('builtins.print'):
            self.manager.process_monitor()
    
    # Security Tests
    def test_security_scan(self):
        """Test security scanning"""
        with patch('builtins.print'):
            self.manager.security_scan()
    
    def test_check_file_permissions(self):
        """Test file permissions checking"""
        result = self.manager.check_file_permissions()
        self.assertIsInstance(result, bool)
    
    def test_check_open_ports(self):
        """Test open ports checking"""
        result = self.manager.check_open_ports()
        self.assertIsInstance(result, bool)
    
    def test_check_suspicious_processes(self):
        """Test suspicious processes checking"""
        result = self.manager.check_suspicious_processes()
        self.assertIsInstance(result, bool)
    
    def test_check_firewall_status(self):
        """Test firewall status checking"""
        result = self.manager.check_firewall_status()
        self.assertIsInstance(result, bool)
    
    def test_threat_detection(self):
        """Test threat detection"""
        with patch('builtins.print'):
            self.manager.threat_detection()
    
    def test_password_check(self):
        """Test password checking"""
        with patch('builtins.print'):
            self.manager.password_check()
    
    def test_firewall_status(self):
        """Test firewall status display"""
        with patch('builtins.print'):
            self.manager.firewall_status()
    
    def test_security_logs(self):
        """Test security logs display"""
        with patch('builtins.print'):
            self.manager.security_logs()
    
    def test_file_permissions(self):
        """Test file permissions display"""
        with patch('builtins.print'):
            self.manager.file_permissions()
    
    def test_network_security(self):
        """Test network security checking"""
        with patch('builtins.print'):
            self.manager.network_security()
    
    def test_device_security(self):
        """Test device security checking"""
        with patch('builtins.print'):
            self.manager.device_security()
    
    def test_check_screen_lock(self):
        """Test screen lock checking"""
        result = self.manager.check_screen_lock()
        self.assertIsInstance(result, bool)
    
    def test_check_encryption(self):
        """Test encryption checking"""
        result = self.manager.check_encryption()
        self.assertIsInstance(result, bool)
    
    def test_check_auto_updates(self):
        """Test auto updates checking"""
        result = self.manager.check_auto_updates()
        self.assertIsInstance(result, bool)
    
    def test_check_antivirus(self):
        """Test antivirus checking"""
        result = self.manager.check_antivirus()
        self.assertIsInstance(result, bool)
    
    # Network Camera and CCTV Detection Tests
    def test_network_camera_scan(self):
        """Test network camera scanning"""
        with patch.object(self.manager, 'get_local_ip', return_value='192.168.1.100'):
            with patch.object(self.manager, 'scan_ip_for_cameras'):
                with patch('builtins.print'):
                    self.manager.network_camera_scan()
    
    def test_scan_ip_for_cameras(self):
        """Test IP scanning for cameras"""
        results = []
        with patch('socket.socket') as mock_socket:
            mock_sock = MagicMock()
            mock_socket.return_value = mock_sock
            mock_sock.connect_ex.return_value = 0
            mock_sock.recv.return_value = b'HTTP/1.1 200 OK\r\nServer: camera\r\n'
            
            self.manager.scan_ip_for_cameras('192.168.1.1', [80], results)
            
            # Should find a camera device
            self.assertGreater(len(results), 0)
    
    def test_get_banner(self):
        """Test banner retrieval"""
        with patch('socket.socket') as mock_socket:
            mock_sock = MagicMock()
            mock_sock.recv.return_value = b'HTTP/1.1 200 OK\r\nServer: test\r\n'
            mock_sock.settimeout = MagicMock()
            
            result = self.manager.get_banner(mock_sock)
            self.assertIsInstance(result, str)
    
    def test_identify_camera_type(self):
        """Test camera type identification"""
        # Test with camera banner
        banner = "HTTP/1.1 200 OK\r\nServer: IP Camera\r\n"
        result = self.manager.identify_camera_type(banner, 80)
        self.assertEqual(result, 'IP Camera')
        
        # Test with RTSP port
        result = self.manager.identify_camera_type("", 554)
        self.assertEqual(result, 'RTSP Stream')
        
        # Test with no camera signature
        result = self.manager.identify_camera_type("HTTP/1.1 200 OK", 80)
        self.assertIsNone(result)
    
    def test_cctv_detection(self):
        """Test CCTV detection"""
        with patch.object(self.manager, 'get_local_ip', return_value='192.168.1.100'):
            with patch.object(self.manager, 'check_cctv_port', return_value=False):
                with patch.object(self.manager, 'scan_upnp_devices', return_value=[]):
                    with patch.object(self.manager, 'analyze_network_traffic', return_value={}):
                        with patch.object(self.manager, 'scan_wifi_devices', return_value=[]):
                            with patch('builtins.print'):
                                self.manager.cctv_detection()
    
    def test_check_cctv_port(self):
        """Test CCTV port checking"""
        with patch('socket.socket') as mock_socket:
            mock_sock = MagicMock()
            mock_socket.return_value = mock_sock
            mock_sock.connect_ex.return_value = 0
            mock_sock.recv.return_value = b'HTTP/1.1 200 OK\r\nServer: CCTV System\r\n'
            
            result = self.manager.check_cctv_port('192.168.1.1', 80)
            self.assertTrue(result)
    
    def test_scan_upnp_devices(self):
        """Test UPnP device scanning"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "192.168.1.1 (aa:bb:cc:dd:ee:ff) at 192.168.1.1"
            
            result = self.manager.scan_upnp_devices()
            self.assertIsInstance(result, list)
    
    def test_analyze_network_traffic(self):
        """Test network traffic analysis"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Interface statistics\nESTABLISHED connections"
            
            result = self.manager.analyze_network_traffic()
            self.assertIsInstance(result, dict)
            self.assertIn('high_bandwidth', result)
    
    def test_scan_wifi_devices(self):
        """Test WiFi device scanning"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "192.168.1.1 (aa:bb:cc:dd:ee:ff) at 192.168.1.1 on en0"
            
            result = self.manager.scan_wifi_devices()
            self.assertIsInstance(result, list)
    
    def test_get_local_ip(self):
        """Test local IP retrieval"""
        with patch('socket.socket') as mock_socket:
            mock_sock = MagicMock()
            mock_socket.return_value = mock_sock
            mock_sock.getsockname.return_value = ('192.168.1.100', 12345)
            
            result = self.manager.get_local_ip()
            self.assertEqual(result, '192.168.1.100')
    
    def test_is_local_ip(self):
        """Test local IP checking"""
        # Test private IPs
        self.assertTrue(self.manager.is_local_ip('192.168.1.1'))
        self.assertTrue(self.manager.is_local_ip('10.0.0.1'))
        self.assertTrue(self.manager.is_local_ip('172.16.0.1'))
        self.assertTrue(self.manager.is_local_ip('127.0.0.1'))
        
        # Test public IP
        self.assertFalse(self.manager.is_local_ip('8.8.8.8'))
        
        # Test invalid IP
        self.assertFalse(self.manager.is_local_ip('invalid'))
    
    def test_run(self):
        """Test main application loop"""
        # This is hard to test due to the infinite loop, but we can test the setup
        self.manager.running = False  # Stop the loop immediately
        with patch.object(self.manager, 'display_header'):
            with patch.object(self.manager, 'main_menu'):
                self.manager.run()


class TestIntegration(unittest.TestCase):
    """Integration tests for the CLI Assistant"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
    
    def tearDown(self):
        """Clean up integration test fixtures"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    def test_full_workflow(self):
        """Test a complete workflow from start to finish"""
        manager = UltimateCronManager()
        
        # Test creating a job
        with patch.object(manager.menu, 'show_input_prompt', side_effect=[
            'Integration Test Job', 'echo "integration test"', '0 0 * * *', 'Test description'
        ]):
            with patch.object(manager.menu, 'show_dropdown', return_value=0):
                manager.create_job_wizard()
                
                # Verify job was created
                self.assertEqual(len(manager.config['jobs']), 1)
                job = manager.config['jobs'][0]
                self.assertEqual(job['name'], 'Integration Test Job')
                self.assertEqual(job['command'], 'echo "integration test"')
        
        # Test listing jobs
        with patch('builtins.print'):
            manager.list_jobs()
        
        # Test searching jobs
        with patch.object(manager.menu, 'show_input_prompt', return_value='Integration'):
            with patch('builtins.print'):
                manager.search_jobs()
        
        # Test editing job
        with patch.object(manager.menu, 'show_dropdown', return_value=0):
            with patch.object(manager.menu, 'show_input_prompt', return_value='Updated Integration Test Job'):
                manager.edit_job()
                self.assertEqual(manager.config['jobs'][0]['name'], 'Updated Integration Test Job')
        
        # Test exporting jobs
        with patch.object(manager.menu, 'show_input_prompt', return_value='integration_export.json'):
            manager.export_jobs()
            self.assertTrue(os.path.exists('integration_export.json'))
        
        # Test removing job
        with patch.object(manager.menu, 'show_dropdown', return_value=0):
            with patch.object(manager.menu, 'show_confirmation', return_value=True):
                manager.remove_job()
                self.assertEqual(len(manager.config['jobs']), 0)


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [TestSimpleMenu, TestUltimateCronManager, TestIntegration]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('\\n')[-2]}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("🧪 Starting Comprehensive CLI Assistant Test Suite")
    print("=" * 60)
    
    success = run_comprehensive_tests()
    
    if success:
        print("\n✅ All tests passed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        sys.exit(1)
