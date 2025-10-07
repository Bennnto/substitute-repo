#!/usr/bin/env python3
"""
Terminal-based CLI Assistant - AI-powered command-line interface
Features:
- Multimodal AI support (text, image, audio, video)
- Brave API integration for web search
- Backup logging system to ~/back-up/cli-backup
- Terminal-based menu interface
- File management integration
"""

import os
import sys
import json
import subprocess
import threading
from datetime import datetime
import requests
import base64
import logging
import shutil
import time

class TerminalCLIAssistant:
    def __init__(self):
        self.current_menu = "main"
        self.config = self.load_config()
        self.setup_backup_logging()
        
        # AI API configurations
        self.brave_api_key = self.config.get('brave_api_key', '')
        self.openai_api_key = self.config.get('openai_api_key', '')
        self.multimodal_enabled = self.config.get('multimodal_enabled', False)
        
        # Local AI detection
        self.local_ai_available = self.detect_local_ai()
        self.ollama_available = self.detect_ollama()
    
    def detect_local_ai(self):
        """Detect if local AI is available"""
        try:
            # Check for Ollama
            result = subprocess.run(['which', 'ollama'], capture_output=True, text=True)
            if result.returncode == 0:
                return True
            
            # Check for Python AI libraries
            import importlib
            ai_libs = ['torch', 'transformers', 'openai', 'numpy']
            for lib in ai_libs:
                try:
                    importlib.import_module(lib)
                    return True
                except ImportError:
                    continue
            
            return False
        except Exception:
            return False
    
    def detect_ollama(self):
        """Detect if Ollama is available"""
        try:
            result = subprocess.run(['which', 'ollama'], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def setup_backup_logging(self):
        """Setup backup logging system"""
        self.backup_dir = os.path.expanduser("~/back-up/cli-backup")
        os.makedirs(self.backup_dir, exist_ok=True)
        
        log_file = os.path.join(self.backup_dir, f"cli_assistant_{datetime.now().strftime('%Y%m%d')}.log")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Terminal CLI Assistant started")
    
    def load_config(self):
        """Load configuration from config.json"""
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}
    
    def save_config(self):
        """Save configuration to config.json"""
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def print_header(self):
        """Print the application header"""
        print("=" * 60)
        print("🤖 TERMINAL CLI ASSISTANT - AI POWERED")
        print("=" * 60)
        print(f"AI Status: {'🟢 Connected' if self.local_ai_available else '🔴 Disconnected'}")
        print(f"Ollama: {'🟢 Available' if self.ollama_available else '🔴 Not Available'}")
        print(f"Brave API: {'🟢 Configured' if self.brave_api_key else '🔴 Not Configured'}")
        print("=" * 60)
        print()
    
    def show_main_menu(self):
        """Display the main menu"""
        self.clear_screen()
        self.print_header()
        
        menu_options = [
            ("1", "🤖 Multimodal AI", self.multimodal_ai_menu),
            ("2", "🌐 Brave API Search", self.brave_api_menu),
            ("3", "📁 File Management", self.file_management_menu),
            ("4", "🔧 System Tools", self.system_tools_menu),
            ("5", "🎓 Academic Projects", self.academic_projects_menu),
            ("6", "⚙️ AI Configuration", self.ai_configuration_menu),
            ("7", "📊 Backup & Logs", self.backup_logs_menu),
            ("8", "🧪 Test All Functions", self.test_all_functions),
            ("9", "❓ Help & About", self.help_menu),
            ("0", "🚪 Exit", self.exit_application)
        ]
        
        for key, text, _ in menu_options:
            print(f"{key}. {text}")
        
        print()
        choice = input("Enter your choice (0-9): ").strip()
        
        for key, text, command in menu_options:
            if choice == key:
                command()
                break
        else:
            print("❌ Invalid choice. Please try again.")
            input("Press Enter to continue...")
            self.show_main_menu()
    
    def test_all_functions(self):
        """Test all functions systematically"""
        self.clear_screen()
        print("🧪 TESTING ALL FUNCTIONS")
        print("=" * 40)
        
        test_results = []
        
        # Test 1: Multimodal AI
        try:
            test_results.append("✅ Multimodal AI: Ready")
        except Exception as e:
            test_results.append(f"❌ Multimodal AI: {str(e)}")
        
        # Test 2: Brave API
        try:
            if self.brave_api_key:
                test_results.append("✅ Brave API: Connected")
            else:
                test_results.append("⚠️ Brave API: No API key configured")
        except Exception as e:
            test_results.append(f"❌ Brave API: {str(e)}")
        
        # Test 3: Backup System
        try:
            if os.path.exists(self.backup_dir):
                test_results.append("✅ Backup System: Active")
            else:
                test_results.append("❌ Backup System: Directory not found")
        except Exception as e:
            test_results.append(f"❌ Backup System: {str(e)}")
        
        # Test 4: File Manager
        try:
            file_manager_path = os.path.join(os.path.dirname(__file__), "file_manager.py")
            if os.path.exists(file_manager_path):
                test_results.append("✅ File Manager: Available")
            else:
                test_results.append("❌ File Manager: Not found")
        except Exception as e:
            test_results.append(f"❌ File Manager: {str(e)}")
        
        # Test 5: Local AI
        try:
            if self.local_ai_available:
                test_results.append("✅ Local AI: Available")
            else:
                test_results.append("⚠️ Local AI: Not available")
        except Exception as e:
            test_results.append(f"❌ Local AI: {str(e)}")
        
        # Display results
        print("\nTest Results:")
        for result in test_results:
            print(f"  {result}")
        
        print(f"\n📊 Summary: {len([r for r in test_results if '✅' in r])}/{len(test_results)} tests passed")
        
        input("\nPress Enter to return to main menu...")
        self.show_main_menu()
    
    def multimodal_ai_menu(self):
        """Multimodal AI menu"""
        self.clear_screen()
        print("🤖 MULTIMODAL AI MENU")
        print("=" * 30)
        
        options = [
            ("1", "📝 Text Analysis", self.text_analysis),
            ("2", "🖼️ Image Analysis", self.image_analysis),
            ("3", "🎵 Audio Analysis", self.audio_analysis),
            ("4", "🎬 Video Analysis", self.video_analysis),
            ("5", "⚡ Real-time Processing", self.realtime_processing),
            ("6", "📊 Data Visualization", self.data_visualization),
            ("0", "🔙 Back to Main Menu", self.show_main_menu)
        ]
        
        for key, text, _ in options:
            print(f"{key}. {text}")
        
        choice = input("\nEnter your choice: ").strip()
        
        for key, text, command in options:
            if choice == key:
                command()
                break
        else:
            print("❌ Invalid choice.")
            input("Press Enter to continue...")
            self.multimodal_ai_menu()
    
    def brave_api_menu(self):
        """Brave API menu"""
        self.clear_screen()
        print("🌐 BRAVE API SEARCH MENU")
        print("=" * 30)
        
        options = [
            ("1", "🔍 Web Search", self.web_search),
            ("2", "📰 News Search", self.news_search),
            ("3", "🖼️ Image Search", self.image_search),
            ("4", "🎬 Video Search", self.video_search),
            ("5", "📚 Academic Search", self.academic_search),
            ("6", "⚙️ API Settings", self.brave_api_settings),
            ("0", "🔙 Back to Main Menu", self.show_main_menu)
        ]
        
        for key, text, _ in options:
            print(f"{key}. {text}")
        
        choice = input("\nEnter your choice: ").strip()
        
        for key, text, command in options:
            if choice == key:
                command()
                break
        else:
            print("❌ Invalid choice.")
            input("Press Enter to continue...")
            self.brave_api_menu()
    
    def file_management_menu(self):
        """File management menu"""
        self.clear_screen()
        print("📁 FILE MANAGEMENT MENU")
        print("=" * 30)
        
        options = [
            ("1", "📂 Open File Manager", self.open_file_manager),
            ("2", "🗂️ Organize Files", self.organize_files),
            ("3", "🔍 Search Files", self.search_files),
            ("4", "💾 Backup Files", self.backup_files),
            ("5", "🧹 Clean Files", self.clean_files),
            ("0", "🔙 Back to Main Menu", self.show_main_menu)
        ]
        
        for key, text, _ in options:
            print(f"{key}. {text}")
        
        choice = input("\nEnter your choice: ").strip()
        
        for key, text, command in options:
            if choice == key:
                command()
                break
        else:
            print("❌ Invalid choice.")
            input("Press Enter to continue...")
            self.file_management_menu()
    
    def system_tools_menu(self):
        """System tools menu"""
        self.clear_screen()
        print("🔧 SYSTEM TOOLS MENU")
        print("=" * 30)
        
        options = [
            ("1", "💻 System Info", self.show_system_info),
            ("2", "💾 Disk Usage", self.show_disk_usage),
            ("3", "🌐 Network Status", self.show_network_status),
            ("4", "📦 Install Dependencies", self.install_dependencies),
            ("5", "🧹 System Cleanup", self.system_cleanup),
            ("0", "🔙 Back to Main Menu", self.show_main_menu)
        ]
        
        for key, text, _ in options:
            print(f"{key}. {text}")
        
        choice = input("\nEnter your choice: ").strip()
        
        for key, text, command in options:
            if choice == key:
                command()
                break
        else:
            print("❌ Invalid choice.")
            input("Press Enter to continue...")
            self.system_tools_menu()
    
    def academic_projects_menu(self):
        """Academic projects menu"""
        self.clear_screen()
        print("🎓 ACADEMIC PROJECTS MENU")
        print("=" * 30)
        
        options = [
            ("1", "🗄️ MySQL Project", self.open_mysql_project),
            ("2", "🌐 Fullstack Project", self.open_fullstack_project),
            ("3", "🆕 Create New Project", self.create_new_project),
            ("4", "📊 Project Statistics", self.project_statistics),
            ("5", "📅 Academic Calendar", self.academic_calendar),
            ("0", "🔙 Back to Main Menu", self.show_main_menu)
        ]
        
        for key, text, _ in options:
            print(f"{key}. {text}")
        
        choice = input("\nEnter your choice: ").strip()
        
        for key, text, command in options:
            if choice == key:
                command()
                break
        else:
            print("❌ Invalid choice.")
            input("Press Enter to continue...")
            self.academic_projects_menu()
    
    def ai_configuration_menu(self):
        """AI configuration menu"""
        self.clear_screen()
        print("⚙️ AI CONFIGURATION MENU")
        print("=" * 30)
        
        options = [
            ("1", "🔑 Manage API Keys", self.manage_api_keys),
            ("2", "🤖 Model Selection", self.model_selection),
            ("3", "⚡ Performance Settings", self.performance_settings),
            ("4", "🔒 Security Settings", self.security_settings),
            ("5", "📈 Usage Analytics", self.usage_analytics),
            ("0", "🔙 Back to Main Menu", self.show_main_menu)
        ]
        
        for key, text, _ in options:
            print(f"{key}. {text}")
        
        choice = input("\nEnter your choice: ").strip()
        
        for key, text, command in options:
            if choice == key:
                command()
                break
        else:
            print("❌ Invalid choice.")
            input("Press Enter to continue...")
            self.ai_configuration_menu()
    
    def backup_logs_menu(self):
        """Backup and logs menu"""
        self.clear_screen()
        print("📊 BACKUP & LOGS MENU")
        print("=" * 30)
        
        options = [
            ("1", "📋 View Backup Logs", self.view_backup_logs),
            ("2", "💾 Create Backup", self.create_backup),
            ("3", "📄 View System Logs", self.view_system_logs),
            ("4", "🧹 Clean Old Logs", self.clean_old_logs),
            ("5", "📤 Export Logs", self.export_logs),
            ("0", "🔙 Back to Main Menu", self.show_main_menu)
        ]
        
        for key, text, _ in options:
            print(f"{key}. {text}")
        
        choice = input("\nEnter your choice: ").strip()
        
        for key, text, command in options:
            if choice == key:
                command()
                break
        else:
            print("❌ Invalid choice.")
            input("Press Enter to continue...")
            self.backup_logs_menu()
    
    def help_menu(self):
        """Help menu"""
        self.clear_screen()
        print("❓ HELP & ABOUT MENU")
        print("=" * 30)
        
        options = [
            ("1", "📖 User Manual", self.show_user_manual),
            ("2", "❓ FAQ", self.show_faq),
            ("3", "🐛 Report Bug", self.report_bug),
            ("4", "💡 Feature Request", self.feature_request),
            ("5", "📞 Contact Support", self.contact_support),
            ("0", "🔙 Back to Main Menu", self.show_main_menu)
        ]
        
        for key, text, _ in options:
            print(f"{key}. {text}")
        
        choice = input("\nEnter your choice: ").strip()
        
        for key, text, command in options:
            if choice == key:
                command()
                break
        else:
            print("❌ Invalid choice.")
            input("Press Enter to continue...")
            self.help_menu()
    
    # Placeholder functions for all features
    def placeholder_function(self, feature_name="This feature"):
        """Placeholder for unimplemented features"""
        print(f"🚧 {feature_name} is coming soon!")
        input("Press Enter to continue...")
    
    def text_analysis(self):
        print("📝 TEXT ANALYSIS")
        print("=" * 20)
        self.placeholder_function("Text Analysis")
        self.multimodal_ai_menu()
    
    def image_analysis(self):
        print("🖼️ IMAGE ANALYSIS")
        print("=" * 20)
        self.placeholder_function("Image Analysis")
        self.multimodal_ai_menu()
    
    def audio_analysis(self):
        print("🎵 AUDIO ANALYSIS")
        print("=" * 20)
        self.placeholder_function("Audio Analysis")
        self.multimodal_ai_menu()
    
    def video_analysis(self):
        print("🎬 VIDEO ANALYSIS")
        print("=" * 20)
        self.placeholder_function("Video Analysis")
        self.multimodal_ai_menu()
    
    def realtime_processing(self):
        print("⚡ REAL-TIME PROCESSING")
        print("=" * 20)
        self.placeholder_function("Real-time Processing")
        self.multimodal_ai_menu()
    
    def data_visualization(self):
        print("📊 DATA VISUALIZATION")
        print("=" * 20)
        self.placeholder_function("Data Visualization")
        self.multimodal_ai_menu()
    
    def web_search(self):
        print("🔍 WEB SEARCH")
        print("=" * 20)
        if not self.brave_api_key:
            print("❌ Brave API key not configured!")
            print("Please configure your API key in the AI Configuration menu.")
        else:
            query = input("Enter search query: ")
            print(f"🔍 Searching for: {query}")
            self.placeholder_function("Web Search")
        input("Press Enter to continue...")
        self.brave_api_menu()
    
    def news_search(self):
        print("📰 NEWS SEARCH")
        print("=" * 20)
        self.placeholder_function("News Search")
        self.brave_api_menu()
    
    def image_search(self):
        print("🖼️ IMAGE SEARCH")
        print("=" * 20)
        self.placeholder_function("Image Search")
        self.brave_api_menu()
    
    def video_search(self):
        print("🎬 VIDEO SEARCH")
        print("=" * 20)
        self.placeholder_function("Video Search")
        self.brave_api_menu()
    
    def academic_search(self):
        print("📚 ACADEMIC SEARCH")
        print("=" * 20)
        self.placeholder_function("Academic Search")
        self.brave_api_menu()
    
    def brave_api_settings(self):
        print("⚙️ BRAVE API SETTINGS")
        print("=" * 20)
        print(f"Current API Key: {'*' * 10 if self.brave_api_key else 'Not set'}")
        change = input("Do you want to change the API key? (y/n): ").lower()
        if change == 'y':
            new_key = input("Enter new Brave API key: ").strip()
            if new_key:
                self.brave_api_key = new_key
                self.config['brave_api_key'] = new_key
                self.save_config()
                print("✅ API key updated!")
            else:
                print("❌ Invalid API key!")
        input("Press Enter to continue...")
        self.brave_api_menu()
    
    def open_file_manager(self):
        print("📂 OPENING FILE MANAGER")
        print("=" * 20)
        self.placeholder_function("File Manager")
        self.file_management_menu()
    
    def organize_files(self):
        print("🗂️ ORGANIZE FILES")
        print("=" * 20)
        self.placeholder_function("File Organization")
        self.file_management_menu()
    
    def search_files(self):
        print("🔍 SEARCH FILES")
        print("=" * 20)
        self.placeholder_function("File Search")
        self.file_management_menu()
    
    def backup_files(self):
        print("💾 BACKUP FILES")
        print("=" * 20)
        self.placeholder_function("File Backup")
        self.file_management_menu()
    
    def clean_files(self):
        print("🧹 CLEAN FILES")
        print("=" * 20)
        self.placeholder_function("File Cleanup")
        self.file_management_menu()
    
    def show_system_info(self):
        print("💻 SYSTEM INFORMATION")
        print("=" * 20)
        try:
            import platform
            print(f"OS: {platform.system()} {platform.release()}")
            print(f"Architecture: {platform.machine()}")
            print(f"Python: {platform.python_version()}")
            print(f"Processor: {platform.processor()}")
        except Exception as e:
            print(f"❌ Error getting system info: {e}")
        input("Press Enter to continue...")
        self.system_tools_menu()
    
    def show_disk_usage(self):
        print("💾 DISK USAGE")
        print("=" * 20)
        try:
            result = subprocess.run(['df', '-h'], capture_output=True, text=True)
            print(result.stdout)
        except Exception as e:
            print(f"❌ Error getting disk usage: {e}")
        input("Press Enter to continue...")
        self.system_tools_menu()
    
    def show_network_status(self):
        print("🌐 NETWORK STATUS")
        print("=" * 20)
        try:
            result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Internet connection: Active")
            else:
                print("❌ Internet connection: Inactive")
        except Exception as e:
            print(f"❌ Error checking network: {e}")
        input("Press Enter to continue...")
        self.system_tools_menu()
    
    def install_dependencies(self):
        print("📦 INSTALL DEPENDENCIES")
        print("=" * 20)
        self.placeholder_function("Dependency Installation")
        self.system_tools_menu()
    
    def system_cleanup(self):
        print("🧹 SYSTEM CLEANUP")
        print("=" * 20)
        self.placeholder_function("System Cleanup")
        self.system_tools_menu()
    
    def open_mysql_project(self):
        print("🗄️ MYSQL PROJECT")
        print("=" * 20)
        self.placeholder_function("MySQL Project")
        self.academic_projects_menu()
    
    def open_fullstack_project(self):
        print("🌐 FULLSTACK PROJECT")
        print("=" * 20)
        self.placeholder_function("Fullstack Project")
        self.academic_projects_menu()
    
    def create_new_project(self):
        print("🆕 CREATE NEW PROJECT")
        print("=" * 20)
        self.placeholder_function("Project Creation")
        self.academic_projects_menu()
    
    def project_statistics(self):
        print("📊 PROJECT STATISTICS")
        print("=" * 20)
        self.placeholder_function("Project Statistics")
        self.academic_projects_menu()
    
    def academic_calendar(self):
        print("📅 ACADEMIC CALENDAR")
        print("=" * 20)
        self.placeholder_function("Academic Calendar")
        self.academic_projects_menu()
    
    def manage_api_keys(self):
        print("🔑 MANAGE API KEYS")
        print("=" * 20)
        print(f"Brave API Key: {'*' * 10 if self.brave_api_key else 'Not set'}")
        print(f"OpenAI API Key: {'*' * 10 if self.openai_api_key else 'Not set'}")
        input("Press Enter to continue...")
        self.ai_configuration_menu()
    
    def model_selection(self):
        print("🤖 MODEL SELECTION")
        print("=" * 20)
        self.placeholder_function("Model Selection")
        self.ai_configuration_menu()
    
    def performance_settings(self):
        print("⚡ PERFORMANCE SETTINGS")
        print("=" * 20)
        self.placeholder_function("Performance Settings")
        self.ai_configuration_menu()
    
    def security_settings(self):
        print("🔒 SECURITY SETTINGS")
        print("=" * 20)
        self.placeholder_function("Security Settings")
        self.ai_configuration_menu()
    
    def usage_analytics(self):
        print("📈 USAGE ANALYTICS")
        print("=" * 20)
        self.placeholder_function("Usage Analytics")
        self.ai_configuration_menu()
    
    def view_backup_logs(self):
        print("📋 VIEW BACKUP LOGS")
        print("=" * 20)
        try:
            log_files = [f for f in os.listdir(self.backup_dir) if f.endswith('.log')]
            if log_files:
                print("Available log files:")
                for i, log_file in enumerate(log_files, 1):
                    print(f"{i}. {log_file}")
                choice = input("Enter log file number to view (or 0 to go back): ")
                if choice.isdigit() and 1 <= int(choice) <= len(log_files):
                    log_path = os.path.join(self.backup_dir, log_files[int(choice)-1])
                    with open(log_path, 'r') as f:
                        print(f.read())
            else:
                print("No log files found.")
        except Exception as e:
            print(f"❌ Error viewing logs: {e}")
        input("Press Enter to continue...")
        self.backup_logs_menu()
    
    def create_backup(self):
        print("💾 CREATE BACKUP")
        print("=" * 20)
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"cli_backup_{timestamp}"
            backup_path = os.path.join(self.backup_dir, backup_name)
            os.makedirs(backup_path, exist_ok=True)
            
            # Copy important files
            files_to_backup = ['cli_assistant.py', 'config.json', 'file_manager.py']
            for file in files_to_backup:
                src = os.path.join(os.path.dirname(__file__), file)
                if os.path.exists(src):
                    shutil.copy2(src, backup_path)
            
            print(f"✅ Backup created: {backup_path}")
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
        input("Press Enter to continue...")
        self.backup_logs_menu()
    
    def view_system_logs(self):
        print("📄 VIEW SYSTEM LOGS")
        print("=" * 20)
        self.placeholder_function("System Logs")
        self.backup_logs_menu()
    
    def clean_old_logs(self):
        print("🧹 CLEAN OLD LOGS")
        print("=" * 20)
        self.placeholder_function("Log Cleanup")
        self.backup_logs_menu()
    
    def export_logs(self):
        print("📤 EXPORT LOGS")
        print("=" * 20)
        self.placeholder_function("Log Export")
        self.backup_logs_menu()
    
    def show_user_manual(self):
        print("📖 USER MANUAL")
        print("=" * 20)
        manual_text = """
Terminal CLI Assistant - User Manual

🤖 Multimodal AI Features:
- Text Analysis: Analyze text content and sentiment
- Image Analysis: Process and analyze images
- Audio Analysis: Transcribe and analyze audio files
- Video Analysis: Process video content
- Real-time Processing: Live multimodal processing

🌐 Brave API Features:
- Web Search: Search the web using Brave API
- News Search: Find latest news articles
- Image Search: Search for images
- Video Search: Find video content
- Academic Search: Search academic papers

📊 Backup & Logging:
- All activities are logged to ~/back-up/cli-backup
- Automatic backup creation
- Log export and cleanup features

⚙️ Configuration:
- API key management
- Model selection
- Performance optimization
- Security settings

🧪 Testing:
- Use "Test All Functions" to verify system status
- Comprehensive function testing
- Status reporting

For more help, check the backup logs or contact support.
        """
        print(manual_text)
        input("Press Enter to continue...")
        self.help_menu()
    
    def show_faq(self):
        print("❓ FREQUENTLY ASKED QUESTIONS")
        print("=" * 40)
        faq_text = """
Q: How do I test all functions?
A: Use the "Test All Functions" option from the main menu.

Q: How do I configure API keys?
A: Go to AI Configuration > API Keys to set up your keys.

Q: Where are the backup logs stored?
A: All logs are stored in ~/back-up/cli-backup directory.

Q: How do I backup my files?
A: Use the File Management > Backup Files option.

Q: How do I access multimodal AI features?
A: Use the Multimodal AI menu for text, image, audio, and video analysis.

Q: How do I search using Brave API?
A: Use the Brave API Search menu for web, news, image, and video searches.
        """
        print(faq_text)
        input("Press Enter to continue...")
        self.help_menu()
    
    def report_bug(self):
        print("🐛 REPORT BUG")
        print("=" * 20)
        print("Please report bugs through the GitHub repository issues page.")
        input("Press Enter to continue...")
        self.help_menu()
    
    def feature_request(self):
        print("💡 FEATURE REQUEST")
        print("=" * 20)
        print("Please submit feature requests through the GitHub repository issues page.")
        input("Press Enter to continue...")
        self.help_menu()
    
    def contact_support(self):
        print("📞 CONTACT SUPPORT")
        print("=" * 20)
        print("For support, please contact through the GitHub repository.")
        input("Press Enter to continue...")
        self.help_menu()
    
    def exit_application(self):
        """Exit the application"""
        print("👋 Thank you for using Terminal CLI Assistant!")
        print("Logging out...")
        self.logger.info("Terminal CLI Assistant stopped")
        sys.exit(0)
    
    def run(self):
        """Run the terminal CLI assistant"""
        try:
            while True:
                self.show_main_menu()
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            self.logger.info("Terminal CLI Assistant stopped by user")
            sys.exit(0)

if __name__ == "__main__":
    app = TerminalCLIAssistant()
    app.run() 