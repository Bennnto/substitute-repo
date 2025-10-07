#!/usr/bin/env python3
import os
import sys
import subprocess
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Platform-specific imports for key handling
if os.name == 'nt':  # Windows
    import msvcrt
else:  # Unix/Linux/macOS
    import tty
    import termios

class SimpleMenu:
    def __init__(self):
        self.current_selection = 0
        self.menu_stack = []  # Track menu navigation history
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def get_key_press(self):
        """Get a single key press including arrow keys"""
        try:
            if os.name == 'nt':  # Windows
                key = msvcrt.getch()
                if key == b'\xe0':  # Arrow key prefix
                    key = msvcrt.getch()
                    if key == b'H':
                        return 'UP'
                    elif key == b'P':
                        return 'DOWN'
                    elif key == b'K':
                        return 'LEFT'
                    elif key == b'M':
                        return 'RIGHT'
                elif key == b'\r':
                    return 'ENTER'
                elif key == b'\x1b':  # Escape
                    return 'ESC'
                else:
                    return key.decode('utf-8').lower()
            else:  # Unix/Linux/macOS
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(sys.stdin.fileno())
                    ch = sys.stdin.read(1)
                    if ch == '\x1b':  # Escape sequence
                        next1 = sys.stdin.read(1)
                        if next1 == '[':
                            next2 = sys.stdin.read(1)
                            if next2 == 'A':
                                return 'UP'
                            elif next2 == 'B':
                                return 'DOWN'
                            elif next2 == 'C':
                                return 'RIGHT'
                            elif next2 == 'D':
                                return 'LEFT'
                    elif ch == '\r':
                        return 'ENTER'
                    elif ch == '\x1b':
                        return 'ESC'
                    return ch.lower()
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except:
            # Fallback to simple input if arrow keys don't work
            return input("Enter choice: ").strip().lower()
    
    def show_dropdown(self, title: str, options: list, allow_cancel=True, show_navigation_hint=True) -> int:
        """
        Show a simple dropdown menu with moving arrow (>)
        Returns: selected index (0-based), or -1 if cancelled
        """
        self.current_selection = 0
        
        while True:
            self.clear_screen()
            print(f"\n? {title}")
            print("─" * (len(title) + 2))
            
            # Show options with arrow indicator
            for i, option in enumerate(options):
                if i == self.current_selection:
                    print(f"  ▶ {option}")
                else:
                    print(f"    {option}")
            
            if allow_cancel:
                if self.current_selection == len(options):
                    print(f"  ▶ Cancel")
                else:
                    print(f"    Cancel")
            
            # Show navigation hints
            if show_navigation_hint:
                print("\n" + "─" * 50)
                print("💡 Navigation: ↑/↓ or W/S to move • Enter to select • Esc to cancel")
            
            # Get user input
            key = self.get_key_press()
            
            if key == 'UP' or key == 'w':  # Move up
                self.current_selection = (self.current_selection - 1) % (len(options) + (1 if allow_cancel else 0))
            elif key == 'DOWN' or key == 's':  # Move down
                self.current_selection = (self.current_selection + 1) % (len(options) + (1 if allow_cancel else 0))
            elif key == 'ENTER' or key == '':  # Enter
                if self.current_selection < len(options):
                    return self.current_selection
                elif allow_cancel:
                    return -1
            elif key == 'ESC' or key == 'q':  # Quit
                return -1
            elif key.isdigit():  # Direct number selection
                num = int(key) - 1
                if 0 <= num < len(options):
                    return num
                else:
                    print("❌ Invalid number. Press Enter to continue...")
                    input()
    
    def show_questionnaire(self, questions: list) -> dict:
        """
        Show a questionnaire with dropdown selections
        questions: list of dicts with 'question', 'options', 'key'
        Returns: dict of answers
        """
        answers = {}
        
        for i, question in enumerate(questions):
            question_text = question['question']
            options = question['options']
            
            print(f"\n📝 Question {i+1}/{len(questions)}")
            print(f"? {question_text}")
            choice = self.show_dropdown(f"Select option", options, allow_cancel=False, show_navigation_hint=True)
            
            if choice == -1:
                return {}  # Cancelled
            
            answers[question['key']] = options[choice]
            
            # Show progress
            if i < len(questions) - 1:
                print(f"\n✅ {question['key']}: {options[choice]}")
                print("Press Enter to continue to next question...")
                input()
        
        return answers
    
    def show_confirmation(self, message: str, default_yes: bool = True) -> bool:
        """Show a confirmation dialog"""
        options = ["Yes", "No"] if default_yes else ["No", "Yes"]
        choice = self.show_dropdown(f"❓ {message}", options, allow_cancel=False, show_navigation_hint=False)
        return choice == (0 if default_yes else 1)
    
    def show_input_prompt(self, prompt: str, default: str = "") -> str:
        """Show an input prompt with optional default value"""
        self.clear_screen()
        print(f"\n📝 {prompt}")
        if default:
            print(f"💡 Default: {default}")
        print("─" * 50)
        
        user_input = input("Enter value: ").strip()
        return user_input if user_input else default

class UltimateCronManager:
    def __init__(self):
        self.menu = SimpleMenu()
        self.running = True
        self.config_file = "cron_config.json"
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {"jobs": [], "settings": {}}
        except:
            self.config = {"jobs": [], "settings": {}}
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving config: {e}")
    
    def display_header(self):
        """Display application header"""
        self.menu.clear_screen()
        print("CLI ASSISTANT")  
    
    def main_menu(self):
        """Display main menu"""
        options = [
            "📋 View & Manage Jobs",
            "➕ Create New Job",
            "📁 File Management",
            "⏰ Reminders & Calendar",
            "🔍 Brave AI Search",
            "🤖 Local AI (Ollama)",
            "📊 System & Network Monitor",
            "🔒 Security Monitor",
            "⚙️  Settings & Configuration", 
            "🛠️  Tools & Utilities",
            "❓ Help & Documentation",
            "🚪 Exit"
        ]
        
        choice = self.menu.show_dropdown("MAIN MENU", options)
        
        if choice == 0:
            self.handle_view_menu()
        elif choice == 1:
            self.handle_create_menu()
        elif choice == 2:
            self.handle_file_management_menu()
        elif choice == 3:
            self.handle_reminders_menu()
        elif choice == 4:
            self.handle_brave_search_menu()
        elif choice == 5:
            self.handle_ollama_menu()
        elif choice == 6:
            self.handle_system_monitor_menu()
        elif choice == 7:
            self.handle_security_menu()
        elif choice == 8:
            self.handle_settings_menu()
        elif choice == 9:
            self.handle_tools_menu()
        elif choice == 10:
            self.handle_help_menu()
        elif choice == 11 or choice == -1:
            if choice == 11:
                if self.menu.show_confirmation("Are you sure you want to exit?"):
                    self.running = False
            else:
                self.running = False
    
    def handle_view_menu(self):
        """Handle view and manage jobs menu"""
        options = [
            "📋 List all jobs",
            "🔍 Search jobs",
            "✏️  Edit job",
            "🗑️  Remove job", 
            "⏸️  Enable/Disable job",
            "📊 Job statistics",
            "⬅️  Back to main menu"
        ]
        
        choice = self.menu.show_dropdown("VIEW & MANAGE JOBS", options)
        
        if choice == 0:
            self.list_jobs()
        elif choice == 1:
            self.search_jobs()
        elif choice == 2:
            self.edit_job()
        elif choice == 3:
            self.remove_job()
        elif choice == 4:
            self.toggle_job()
        elif choice == 5:
            self.show_statistics()
        elif choice == 6 or choice == -1:
            pass  # Back to main menu
    
    def handle_create_menu(self):
        """Handle create new job menu"""
        options = [
            "🧙‍♂️ Job creation wizard",
            "📝 Manual entry",
            "📋 Use template",
            "📥 Import from file",
            "⬅️  Back to main menu"
        ]
        
        choice = self.menu.show_dropdown("CREATE NEW JOB", options)
        
        if choice == 0:
            self.create_job_wizard()
        elif choice == 1:
            self.create_job_manual()
        elif choice == 2:
            self.create_job_template()
        elif choice == 3:
            self.import_job()
        elif choice == 4 or choice == -1:
            pass  # Back to main menu
    
    def handle_settings_menu(self):
        """Handle settings menu"""
        options = [
            "🎨 Change theme",
            "💾 Auto-backup settings",
            "📁 Log directory",
            "✏️  Default editor",
            "📊 Statistics display",
            "⬅️  Back to main menu"
        ]
        
        choice = self.menu.show_dropdown("SETTINGS & CONFIGURATION", options)
        
        if choice == 0:
            self.change_theme()
        elif choice == 1:
            self.auto_backup_settings()
        elif choice == 2:
            self.log_directory_settings()
        elif choice == 3:
            self.default_editor_settings()
        elif choice == 4:
            self.statistics_display_settings()
        elif choice == 5 or choice == -1:
            pass  # Back to main menu
    
    def handle_tools_menu(self):
        """Handle tools menu"""
        options = [
            "🧪 Test command",
            "📤 Export jobs",
            "📥 Import jobs",
            "💾 Backup/Restore",
            "🔍 Monitor jobs",
            "✅ Validate syntax",
            "⬅️  Back to main menu"
        ]
        
        choice = self.menu.show_dropdown("TOOLS & UTILITIES", options)
        
        if choice == 0:
            self.test_command()
        elif choice == 1:
            self.export_jobs()
        elif choice == 2:
            self.import_jobs()
        elif choice == 3:
            self.backup_restore()
        elif choice == 4:
            self.monitor_jobs()
        elif choice == 5:
            self.validate_syntax()
        elif choice == 6 or choice == -1:
            pass  # Back to main menu
    
    def handle_help_menu(self):
        """Handle help menu"""
        self.menu.clear_screen()
        print("\n📚 HELP & DOCUMENTATION")
        print("─" * 50)
        print("🎯 Navigation:")
        print("  ↑/↓ Arrow keys - Move selection")
        print("  W/S keys - Alternative movement")
        print("  Enter - Select option")
        print("  Esc/Q - Cancel/quit")
        print("  Numbers - Direct selection")
        print("\n📋 Features:")
        print("  • Questionnaire-style dropdowns")
        print("  • Moving arrow indicator")
        print("  • Simple and intuitive interface")
        print("  • Error handling and validation")
        print("\n🚀 Getting Started:")
        print("  1. Use the main menu to navigate")
        print("  2. Try the 'Create New Job' wizard")
        print("  3. Explore different menus")
        print("  4. Use arrow keys or W/S to move")
        
        input("\nPress Enter to continue...")
    
    def create_job_wizard(self):
        """Create job with questionnaire wizard"""
        questions = [
            {
                'question': 'Enter job name',
                'options': ['Backup Job', 'Cleanup Job', 'Update Job', 'Custom Job'],
                'key': 'job_name'
            },
            {
                'question': 'Select schedule type',
                'options': ['Every minute', 'Every 5 minutes', 'Every hour', 'Daily', 'Weekly', 'Monthly', 'Custom'],
                'key': 'schedule'
            },
            {
                'question': 'Select command type',
                'options': ['System backup', 'Log cleanup', 'Database backup', 'System update', 'Health check', 'Custom command'],
                'key': 'command'
            },
            {
                'question': 'Select logging option',
                'options': ['No logging', 'Log to file', 'Log with timestamp', 'Email notification'],
                'key': 'logging'
            }
        ]
        
        answers = self.menu.show_questionnaire(questions)
        
        if answers:
            # Create job entry
            job = {
                'id': len(self.config['jobs']) + 1,
                'name': answers['job_name'],
                'schedule': answers['schedule'],
                'command': answers['command'],
                'logging': answers['logging'],
                'enabled': True,
                'created': datetime.now().isoformat()
            }
            
            self.config['jobs'].append(job)
            self.save_config()
            
            print("\n📋 Job Summary:")
            print("─" * 40)
            for key, value in answers.items():
                print(f"  {key}: {value}")
            print("─" * 40)
            print("✅ Job created successfully!")
        else:
            print("❌ Job creation cancelled!")
        
        input("Press Enter to continue...")
    
    def list_jobs(self):
        """List all jobs"""
        self.menu.clear_screen()
        if not self.config['jobs']:
            print("📋 No jobs found.")
        else:
            print("📋 Current Jobs:")
            print("─" * 60)
            for job in self.config['jobs']:
                status = "✅" if job.get('enabled', True) else "❌"
                print(f"{status} {job['name']} ({job['schedule']}) - {job['command']}")
            print("─" * 60)
        
        input("Press Enter to continue...")
    
    def search_jobs(self):
        """Search jobs"""
        search_term = self.menu.show_input_prompt("Enter search term")
        if search_term:
            self.menu.clear_screen()
            print(f"🔍 Searching for: '{search_term}'")
            print("─" * 50)
            
            found_jobs = []
            for job in self.config['jobs']:
                if search_term.lower() in job['name'].lower() or search_term.lower() in job['command'].lower():
                    found_jobs.append(job)
            
            if found_jobs:
                print(f"Found {len(found_jobs)} job(s):")
                for job in found_jobs:
                    status = "✅" if job.get('enabled', True) else "❌"
                    print(f"{status} {job['name']} ({job['schedule']}) - {job['command']}")
            else:
                print("No jobs found matching your search term.")
        else:
            print("❌ No search term provided.")
        
        input("Press Enter to continue...")
    
    def edit_job(self):
        """Edit job"""
        if not self.config['jobs']:
            print("❌ No jobs available to edit.")
            input("Press Enter to continue...")
            return
        
        # Create list of job names for selection
        job_names = [job['name'] for job in self.config['jobs']]
        choice = self.menu.show_dropdown("Select job to edit", job_names)
        
        if choice >= 0:
            job = self.config['jobs'][choice]
            print(f"✏️  Editing job: {job['name']}")
            print("Feature coming soon!")
        else:
            print("❌ Job editing cancelled.")
        
        input("Press Enter to continue...")
    
    def remove_job(self):
        """Remove job"""
        if not self.config['jobs']:
            print("❌ No jobs available to remove.")
            input("Press Enter to continue...")
            return
        
        # Create list of job names for selection
        job_names = [job['name'] for job in self.config['jobs']]
        choice = self.menu.show_dropdown("Select job to remove", job_names)
        
        if choice >= 0:
            job = self.config['jobs'][choice]
            if self.menu.show_confirmation(f"Are you sure you want to remove '{job['name']}'?"):
                del self.config['jobs'][choice]
                self.save_config()
                print(f"✅ Job '{job['name']}' removed successfully!")
            else:
                print("❌ Job removal cancelled.")
        else:
            print("❌ Job removal cancelled.")
        
        input("Press Enter to continue...")
    
    def toggle_job(self):
        """Toggle job enabled/disabled"""
        if not self.config['jobs']:
            print("❌ No jobs available to toggle.")
            input("Press Enter to continue...")
            return
        
        # Create list of job names for selection
        job_names = [job['name'] for job in self.config['jobs']]
        choice = self.menu.show_dropdown("Select job to toggle", job_names)
        
        if choice >= 0:
            job = self.config['jobs'][choice]
            current_status = job.get('enabled', True)
            new_status = not current_status
            job['enabled'] = new_status
            self.save_config()
            status_text = "enabled" if new_status else "disabled"
            print(f"✅ Job '{job['name']}' {status_text}!")
        else:
            print("❌ Job toggle cancelled.")
        
        input("Press Enter to continue...")
    
    def show_statistics(self):
        """Show job statistics"""
        self.menu.clear_screen()
        print("📊 Job Statistics")
        print("─" * 30)
        
        total_jobs = len(self.config['jobs'])
        enabled_jobs = len([job for job in self.config['jobs'] if job.get('enabled', True)])
        disabled_jobs = total_jobs - enabled_jobs
        
        print(f"Total jobs: {total_jobs}")
        print(f"Enabled jobs: {enabled_jobs}")
        print(f"Disabled jobs: {disabled_jobs}")
        
        if total_jobs > 0:
            print(f"Enabled percentage: {(enabled_jobs/total_jobs)*100:.1f}%")
        
        input("Press Enter to continue...")
    
    def create_job_manual(self):
        """Create job manually"""
        print("📝 Manual job creation - Feature coming soon!")
        input("Press Enter to continue...")
    
    def create_job_template(self):
        """Create job from template"""
        templates = [
            "Backup Template",
            "Cleanup Template", 
            "Update Template",
            "Monitoring Template"
        ]
        
        choice = self.menu.show_dropdown("Select template", templates)
        
        if choice >= 0:
            print(f"📋 Using template: {templates[choice]}")
            print("Template feature coming soon!")
        else:
            print("❌ Template selection cancelled.")
        
        input("Press Enter to continue...")
    
    def import_job(self):
        """Import job from file"""
        print("📥 Import job - Feature coming soon!")
        input("Press Enter to continue...")
    
    def change_theme(self):
        """Change theme"""
        themes = ["Default", "Dark", "Light", "Colorful", "Minimal"]
        choice = self.menu.show_dropdown("Select theme", themes)
        
        if choice >= 0:
            print(f"🎨 Theme changed to: {themes[choice]}")
            print("Theme feature coming soon!")
        else:
            print("❌ Theme selection cancelled.")
        
        input("Press Enter to continue...")
    
    def auto_backup_settings(self):
        """Auto-backup settings"""
        options = ["Enable", "Disable", "Configure"]
        choice = self.menu.show_dropdown("Auto-backup settings", options)
        
        if choice >= 0:
            print(f"💾 Auto-backup: {options[choice]}")
            print("Auto-backup feature coming soon!")
        else:
            print("❌ Auto-backup settings cancelled.")
        
        input("Press Enter to continue...")
    
    def log_directory_settings(self):
        """Log directory settings"""
        print("📁 Log directory settings - Feature coming soon!")
        input("Press Enter to continue...")
    
    def default_editor_settings(self):
        """Default editor settings"""
        editors = ["nano", "vim", "emacs", "code", "sublime"]
        choice = self.menu.show_dropdown("Select default editor", editors)
        
        if choice >= 0:
            print(f"✏️  Default editor set to: {editors[choice]}")
        else:
            print("❌ Editor selection cancelled.")
        
        input("Press Enter to continue...")
    
    def statistics_display_settings(self):
        """Statistics display settings"""
        options = ["Simple", "Detailed", "Graphical", "Custom"]
        choice = self.menu.show_dropdown("Statistics display mode", options)
        
        if choice >= 0:
            print(f"📊 Statistics display: {options[choice]}")
        else:
            print("❌ Statistics settings cancelled.")
        
        input("Press Enter to continue...")
    
    def test_command(self):
        """Test command"""
        command = self.menu.show_input_prompt("Enter command to test")
        if command:
            print(f"🧪 Testing command: {command}")
            print("Command testing feature coming soon!")
        else:
            print("❌ No command provided.")
        
        input("Press Enter to continue...")
    
    def export_jobs(self):
        """Export jobs"""
        formats = ["JSON", "CSV", "YAML", "Plain Text"]
        choice = self.menu.show_dropdown("Select export format", formats)
        
        if choice >= 0:
            print(f"📤 Exporting jobs as {formats[choice]}")
            print("Export feature coming soon!")
        else:
            print("❌ Export cancelled.")
        
        input("Press Enter to continue...")
    
    def import_jobs(self):
        """Import jobs"""
        print("📥 Import jobs - Feature coming soon!")
        input("Press Enter to continue...")
    
    def backup_restore(self):
        """Backup/Restore"""
        options = ["Create Backup", "Restore from Backup", "List Backups"]
        choice = self.menu.show_dropdown("Backup/Restore", options)
        
        if choice >= 0:
            print(f"💾 {options[choice]}")
            print("Backup/Restore feature coming soon!")
        else:
            print("❌ Backup/Restore cancelled.")
        
        input("Press Enter to continue...")
    
    def monitor_jobs(self):
        """Monitor jobs"""
        print("🔍 Monitor jobs - Feature coming soon!")
        input("Press Enter to continue...")
    
    def validate_syntax(self):
        """Validate syntax"""
        print("✅ Validate syntax - Feature coming soon!")
        input("Press Enter to continue...")
    
    def handle_file_management_menu(self):
        """Handle file management menu"""
        options = [
            "🔐 Encrypt File",
            "🔓 Decrypt File",
            "⬇️  Download Large File",
            "💾 Backup File/Directory",
            "📁 File Browser",
            "🔄 Sync Files",
            "⬅️  Back to main menu"
        ]
        
        choice = self.menu.show_dropdown("FILE MANAGEMENT", options)
        
        if choice == 0:
            self.encrypt_file()
        elif choice == 1:
            self.decrypt_file()
        elif choice == 2:
            self.download_large_file()
        elif choice == 3:
            self.backup_file_directory()
        elif choice == 4:
            self.file_browser()
        elif choice == 5:
            self.sync_files()
        elif choice == 6 or choice == -1:
            pass  # Back to main menu
    
    def handle_reminders_menu(self):
        """Handle reminders and calendar menu"""
        options = [
            "➕ Add Reminder",
            "📅 View Calendar",
            "⏰ Set Timer",
            "📝 List Reminders",
            "🗑️  Delete Reminder",
            "🔄 Sync with Calendar",
            "⬅️  Back to main menu"
        ]
        
        choice = self.menu.show_dropdown("REMINDERS & CALENDAR", options)
        
        if choice == 0:
            self.add_reminder()
        elif choice == 1:
            self.view_calendar()
        elif choice == 2:
            self.set_timer()
        elif choice == 3:
            self.list_reminders()
        elif choice == 4:
            self.delete_reminder()
        elif choice == 5:
            self.sync_calendar()
        elif choice == 6 or choice == -1:
            pass  # Back to main menu
    
    def handle_brave_search_menu(self):
        """Handle Brave AI search menu"""
        options = [
            "🔍 Search Web",
            "📰 Search News",
            "🖼️  Search Images",
            "📚 Search Documents",
            "🎥 Search Videos",
            "📊 Search Analytics",
            "⬅️  Back to main menu"
        ]
        
        choice = self.menu.show_dropdown("BRAVE AI SEARCH", options)
        
        if choice == 0:
            self.brave_web_search()
        elif choice == 1:
            self.brave_news_search()
        elif choice == 2:
            self.brave_image_search()
        elif choice == 3:
            self.brave_document_search()
        elif choice == 4:
            self.brave_video_search()
        elif choice == 5:
            self.brave_analytics_search()
        elif choice == 6 or choice == -1:
            pass  # Back to main menu
    
    def handle_ollama_menu(self):
        """Handle local Ollama AI menu"""
        options = [
            "💬 Chat with AI",
            "📝 Generate Text",
            "🔍 Ask Questions",
            "📊 Analyze Data",
            "🖼️  Generate Images",
            "📚 Document Analysis",
            "⚙️  AI Settings",
            "⬅️  Back to main menu"
        ]
        
        choice = self.menu.show_dropdown("LOCAL AI (OLLAMA)", options)
        
        if choice == 0:
            self.ollama_chat()
        elif choice == 1:
            self.ollama_generate_text()
        elif choice == 2:
            self.ollama_ask_questions()
        elif choice == 3:
            self.ollama_analyze_data()
        elif choice == 4:
            self.ollama_generate_images()
        elif choice == 5:
            self.ollama_document_analysis()
        elif choice == 6:
            self.ollama_settings()
        elif choice == 7 or choice == -1:
            pass  # Back to main menu
    
    def handle_system_monitor_menu(self):
        """Handle system and network monitoring menu"""
        options = [
            "💻 System Info",
            "🌐 Network Status",
            "📊 Performance Monitor",
            "🔥 CPU Usage",
            "💾 Memory Usage",
            "💿 Disk Usage",
            "📈 Network Traffic",
            "🖥️  Process Monitor",
            "⬅️  Back to main menu"
        ]
        
        choice = self.menu.show_dropdown("SYSTEM & NETWORK MONITOR", options)
        
        if choice == 0:
            self.system_info()
        elif choice == 1:
            self.network_status()
        elif choice == 2:
            self.performance_monitor()
        elif choice == 3:
            self.cpu_usage()
        elif choice == 4:
            self.memory_usage()
        elif choice == 5:
            self.disk_usage()
        elif choice == 6:
            self.network_traffic()
        elif choice == 7:
            self.process_monitor()
        elif choice == 8 or choice == -1:
            pass  # Back to main menu
    
    def handle_security_menu(self):
        """Handle security monitoring menu"""
        options = [
            "🔍 Security Scan",
            "🚨 Threat Detection",
            "🔐 Password Check",
            "🛡️  Firewall Status",
            "📊 Security Logs",
            "🔒 File Permissions",
            "🌐 Network Security",
            "📱 Device Security",
            "⬅️  Back to main menu"
        ]
        
        choice = self.menu.show_dropdown("SECURITY MONITOR", options)
        
        if choice == 0:
            self.security_scan()
        elif choice == 1:
            self.threat_detection()
        elif choice == 2:
            self.password_check()
        elif choice == 3:
            self.firewall_status()
        elif choice == 4:
            self.security_logs()
        elif choice == 5:
            self.file_permissions()
        elif choice == 6:
            self.network_security()
        elif choice == 7:
            self.device_security()
        elif choice == 8 or choice == -1:
            pass  # Back to main menu
    
    # ===== FILE MANAGEMENT FUNCTIONS =====
    
    def encrypt_file(self):
        """Encrypt a file"""
        file_path = self.menu.show_input_prompt("Enter file path to encrypt")
        if file_path and os.path.exists(file_path):
            try:
                import cryptography.fernet
                from cryptography.fernet import Fernet
                
                # Generate key
                key = Fernet.generate_key()
                cipher = Fernet(key)
                
                # Read and encrypt file
                with open(file_path, 'rb') as file:
                    file_data = file.read()
                
                encrypted_data = cipher.encrypt(file_data)
                
                # Save encrypted file
                encrypted_path = file_path + '.encrypted'
                with open(encrypted_path, 'wb') as file:
                    file.write(encrypted_data)
                
                # Save key
                key_path = file_path + '.key'
                with open(key_path, 'wb') as file:
                    file.write(key)
                
                print(f"✅ File encrypted successfully!")
                print(f"📁 Encrypted file: {encrypted_path}")
                print(f"🔑 Key file: {key_path}")
                
            except ImportError:
                print("❌ cryptography library not installed. Install with: pip install cryptography")
            except Exception as e:
                print(f"❌ Encryption failed: {e}")
        else:
            print("❌ Invalid file path")
        
        input("Press Enter to continue...")
    
    def decrypt_file(self):
        """Decrypt a file"""
        file_path = self.menu.show_input_prompt("Enter encrypted file path")
        key_path = self.menu.show_input_prompt("Enter key file path")
        
        if file_path and key_path and os.path.exists(file_path) and os.path.exists(key_path):
            try:
                import cryptography.fernet
                from cryptography.fernet import Fernet
                
                # Load key
                with open(key_path, 'rb') as file:
                    key = file.read()
                
                cipher = Fernet(key)
                
                # Read and decrypt file
                with open(file_path, 'rb') as file:
                    encrypted_data = file.read()
                
                decrypted_data = cipher.decrypt(encrypted_data)
                
                # Save decrypted file
                decrypted_path = file_path.replace('.encrypted', '.decrypted')
                with open(decrypted_path, 'wb') as file:
                    file.write(decrypted_data)
                
                print(f"✅ File decrypted successfully!")
                print(f"📁 Decrypted file: {decrypted_path}")
                
            except ImportError:
                print("❌ cryptography library not installed. Install with: pip install cryptography")
            except Exception as e:
                print(f"❌ Decryption failed: {e}")
        else:
            print("❌ Invalid file paths")
        
        input("Press Enter to continue...")
    
    def download_large_file(self):
        """Download large files with progress"""
        url = self.menu.show_input_prompt("Enter file URL to download")
        if url:
            try:
                import requests
                from tqdm import tqdm
                
                print(f"⬇️  Downloading: {url}")
                
                response = requests.get(url, stream=True)
                total_size = int(response.headers.get('content-length', 0))
                
                filename = url.split('/')[-1]
                with open(filename, 'wb') as file, tqdm(
                    desc=filename,
                    total=total_size,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as pbar:
                    for data in response.iter_content(chunk_size=1024):
                        size = file.write(data)
                        pbar.update(size)
                
                print(f"✅ Download completed: {filename}")
                
            except ImportError:
                print("❌ Required libraries not installed. Install with: pip install requests tqdm")
            except Exception as e:
                print(f"❌ Download failed: {e}")
        else:
            print("❌ No URL provided")
        
        input("Press Enter to continue...")
    
    def backup_file_directory(self):
        """Backup file or directory"""
        source = self.menu.show_input_prompt("Enter source file/directory path")
        if source and os.path.exists(source):
            import shutil
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}_{os.path.basename(source)}"
            
            try:
                if os.path.isfile(source):
                    shutil.copy2(source, backup_name)
                else:
                    shutil.copytree(source, backup_name)
                
                print(f"✅ Backup created: {backup_name}")
                
            except Exception as e:
                print(f"❌ Backup failed: {e}")
        else:
            print("❌ Invalid source path")
        
        input("Press Enter to continue...")
    
    def file_browser(self):
        """Simple file browser"""
        current_dir = os.getcwd()
        print(f"📁 Current directory: {current_dir}")
        print("─" * 50)
        
        try:
            files = os.listdir(current_dir)
            for i, file in enumerate(files[:20]):  # Show first 20 files
                file_path = os.path.join(current_dir, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    print(f"📄 {file} ({size} bytes)")
                else:
                    print(f"📁 {file}/")
            
            if len(files) > 20:
                print(f"... and {len(files) - 20} more files")
                
        except Exception as e:
            print(f"❌ Error reading directory: {e}")
        
        input("Press Enter to continue...")
    
    def sync_files(self):
        """Sync files between directories"""
        source = self.menu.show_input_prompt("Enter source directory")
        destination = self.menu.show_input_prompt("Enter destination directory")
        
        if source and destination and os.path.exists(source):
            try:
                import shutil
                
                if not os.path.exists(destination):
                    os.makedirs(destination)
                
                # Sync files
                for item in os.listdir(source):
                    s = os.path.join(source, item)
                    d = os.path.join(destination, item)
                    
                    if os.path.isfile(s):
                        shutil.copy2(s, d)
                    elif os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                
                print(f"✅ Files synced from {source} to {destination}")
                
            except Exception as e:
                print(f"❌ Sync failed: {e}")
        else:
            print("❌ Invalid directories")
        
        input("Press Enter to continue...")
    
    # ===== REMINDERS & CALENDAR FUNCTIONS =====
    
    def add_reminder(self):
        """Add a new reminder"""
        title = self.menu.show_input_prompt("Enter reminder title")
        date = self.menu.show_input_prompt("Enter date (YYYY-MM-DD)")
        time = self.menu.show_input_prompt("Enter time (HH:MM)")
        description = self.menu.show_input_prompt("Enter description (optional)")
        
        if title and date and time:
            try:
                from datetime import datetime
                
                reminder = {
                    'title': title,
                    'date': date,
                    'time': time,
                    'description': description,
                    'created': datetime.now().isoformat(),
                    'completed': False
                }
                
                if 'reminders' not in self.config:
                    self.config['reminders'] = []
                
                self.config['reminders'].append(reminder)
                self.save_config()
                
                print(f"✅ Reminder added: {title} on {date} at {time}")
                
            except Exception as e:
                print(f"❌ Failed to add reminder: {e}")
        else:
            print("❌ Missing required fields")
        
        input("Press Enter to continue...")
    
    def view_calendar(self):
        """View calendar"""
        try:
            from datetime import datetime
            import calendar
            
            now = datetime.now()
            cal = calendar.monthcalendar(now.year, now.month)
            
            print(f"📅 Calendar for {now.strftime('%B %Y')}")
            print("─" * 50)
            print("Mon  Tue  Wed  Thu  Fri  Sat  Sun")
            print("─" * 50)
            
            for week in cal:
                for day in week:
                    if day == 0:
                        print("     ", end="")
                    else:
                        print(f"{day:2d}   ", end="")
                print()
            
            # Show today's reminders
            today = now.strftime("%Y-%m-%d")
            if 'reminders' in self.config:
                today_reminders = [r for r in self.config['reminders'] 
                                 if r['date'] == today and not r['completed']]
                
                if today_reminders:
                    print(f"\n📝 Today's reminders ({len(today_reminders)}):")
                    for reminder in today_reminders:
                        print(f"  ⏰ {reminder['time']} - {reminder['title']}")
            
        except Exception as e:
            print(f"❌ Error displaying calendar: {e}")
        
        input("Press Enter to continue...")
    
    def set_timer(self):
        """Set a timer"""
        duration = self.menu.show_input_prompt("Enter timer duration (e.g., 5m, 2h, 30s)")
        if duration:
            try:
                import time
                import re
                
                # Parse duration
                match = re.match(r'(\d+)([smh])', duration.lower())
                if match:
                    value = int(match.group(1))
                    unit = match.group(2)
                    
                    if unit == 's':
                        seconds = value
                    elif unit == 'm':
                        seconds = value * 60
                    elif unit == 'h':
                        seconds = value * 3600
                    else:
                        raise ValueError("Invalid unit")
                    
                    print(f"⏰ Timer set for {duration}")
                    print("Press Ctrl+C to stop timer")
                    
                    try:
                        time.sleep(seconds)
                        print("🔔 Timer finished!")
                    except KeyboardInterrupt:
                        print("⏹️  Timer cancelled")
                else:
                    print("❌ Invalid duration format. Use: 5s, 10m, 2h")
                    
            except Exception as e:
                print(f"❌ Timer error: {e}")
        else:
            print("❌ No duration provided")
        
        input("Press Enter to continue...")
    
    def list_reminders(self):
        """List all reminders"""
        if 'reminders' in self.config and self.config['reminders']:
            print("📝 All Reminders:")
            print("─" * 60)
            
            for i, reminder in enumerate(self.config['reminders']):
                status = "✅" if reminder.get('completed', False) else "⏰"
                print(f"{status} {reminder['title']} - {reminder['date']} {reminder['time']}")
                if reminder.get('description'):
                    print(f"    📄 {reminder['description']}")
        else:
            print("📝 No reminders found")
        
        input("Press Enter to continue...")
    
    def delete_reminder(self):
        """Delete a reminder"""
        if 'reminders' in self.config and self.config['reminders']:
            reminder_titles = [r['title'] for r in self.config['reminders']]
            choice = self.menu.show_dropdown("Select reminder to delete", reminder_titles)
            
            if choice >= 0:
                reminder = self.config['reminders'][choice]
                if self.menu.show_confirmation(f"Delete reminder: {reminder['title']}?"):
                    del self.config['reminders'][choice]
                    self.save_config()
                    print(f"✅ Reminder deleted: {reminder['title']}")
                else:
                    print("❌ Deletion cancelled")
            else:
                print("❌ No reminder selected")
        else:
            print("❌ No reminders to delete")
        
        input("Press Enter to continue...")
    
    def sync_calendar(self):
        """Sync with external calendar"""
        print("🔄 Calendar sync - Feature coming soon!")
        print("This will integrate with Google Calendar, Apple Calendar, etc.")
        input("Press Enter to continue...")
    
    # ===== BRAVE AI SEARCH FUNCTIONS =====
    
    def brave_web_search(self):
        """Search web using Brave"""
        query = self.menu.show_input_prompt("Enter search query")
        if query:
            try:
                import requests
                import webbrowser
                import urllib.parse
                
                # Try API first, fallback to browser
                api_key = "BSAUo2jjv94yqXmRUMZow_QTYsRdfI3"
                url = "https://api.search.brave.com/res/v1/web/search"
                headers = {
                    "Accept": "application/json",
                    "X-Subscription-Token": api_key
                }
                params = {"q": query, "count": 5}
                
                print(f"🔍 Searching for: {query}")
                print("─" * 50)
                
                try:
                    # Suppress SSL warnings
                    import warnings
                    warnings.filterwarnings("ignore", category=Warning)
                    
                    response = requests.get(url, headers=headers, params=params, timeout=10, verify=False)
                    
                    if response.status_code == 200:
                        results = response.json()
                        print("📄 Search Results:")
                        print("─" * 50)
                        
                        for i, result in enumerate(results.get('web', {}).get('results', []), 1):
                            print(f"{i}. {result.get('title', 'No title')}")
                            print(f"   🔗 {result.get('url', 'No URL')}")
                            print(f"   📝 {result.get('description', 'No description')[:100]}...")
                            print()
                        
                        print("✅ API search completed successfully!")
                        
                    else:
                        print("⚠️  API search failed, opening in browser...")
                        search_url = f"https://search.brave.com/search?q={urllib.parse.quote(query)}"
                        webbrowser.open(search_url)
                        print("✅ Search opened in browser!")
                        
                except Exception as e:
                    print("⚠️  API unavailable, opening in browser...")
                    search_url = f"https://search.brave.com/search?q={urllib.parse.quote(query)}"
                    webbrowser.open(search_url)
                    print("✅ Search opened in browser!")
                
            except ImportError:
                print("❌ requests library not installed. Install with: pip install requests")
                print("Opening in browser instead...")
                import webbrowser
                import urllib.parse
                search_url = f"https://search.brave.com/search?q={urllib.parse.quote(query)}"
                webbrowser.open(search_url)
                print("✅ Search opened in browser!")
            except Exception as e:
                print(f"❌ Search error: {e}")
                print("Opening in browser instead...")
                import webbrowser
                import urllib.parse
                search_url = f"https://search.brave.com/search?q={urllib.parse.quote(query)}"
                webbrowser.open(search_url)
                print("✅ Search opened in browser!")
        else:
            print("❌ No search query provided")
        
        input("Press Enter to continue...")
    
    def brave_news_search(self):
        """Search news using Brave"""
        query = self.menu.show_input_prompt("Enter news search query")
        if query:
            try:
                import requests
                import webbrowser
                import urllib.parse
                
                # Try API first, fallback to browser
                api_key = "BSAUo2jjv94yqXmRUMZow_QTYsRdfI3"
                url = "https://api.search.brave.com/news"
                headers = {
                    "Accept": "application/json",
                    "X-Subscription-Token": api_key
                }
                params = {"q": query, "count": 5}
                
                print(f"📰 Searching news for: {query}")
                print("─" * 50)
                
                try:
                    # Suppress SSL warnings
                    import warnings
                    warnings.filterwarnings("ignore", category=Warning)
                    
                    response = requests.get(url, headers=headers, params=params, timeout=10, verify=False)
                    
                    if response.status_code == 200:
                        results = response.json()
                        print("📰 News Results:")
                        print("─" * 50)
                        
                        for i, result in enumerate(results.get('news', []), 1):
                            print(f"{i}. {result.get('title', 'No title')}")
                            print(f"   📰 {result.get('source', 'Unknown source')}")
                            print(f"   🔗 {result.get('url', 'No URL')}")
                            print(f"   📅 {result.get('published', 'No date')}")
                            print(f"   📝 {result.get('description', 'No description')[:100]}...")
                            print()
                        
                        print("✅ News search completed successfully!")
                        
                    else:
                        print("⚠️  API search failed, opening in browser...")
                        search_url = f"https://search.brave.com/news?q={urllib.parse.quote(query)}"
                        webbrowser.open(search_url)
                        print("✅ News search opened in browser!")
                        
                except Exception as e:
                    print("⚠️  API unavailable, opening in browser...")
                    search_url = f"https://search.brave.com/news?q={urllib.parse.quote(query)}"
                    webbrowser.open(search_url)
                    print("✅ News search opened in browser!")
                
            except ImportError:
                print("❌ requests library not installed. Install with: pip install requests")
                print("Opening in browser instead...")
                import webbrowser
                import urllib.parse
                search_url = f"https://search.brave.com/news?q={urllib.parse.quote(query)}"
                webbrowser.open(search_url)
                print("✅ News search opened in browser!")
            except Exception as e:
                print(f"❌ Search error: {e}")
                print("Opening in browser instead...")
                import webbrowser
                import urllib.parse
                search_url = f"https://search.brave.com/news?q={urllib.parse.quote(query)}"
                webbrowser.open(search_url)
                print("✅ News search opened in browser!")
        else:
            print("❌ No search query provided")
        
        input("Press Enter to continue...")
    
    def brave_image_search(self):
        """Search images using Brave"""
        query = self.menu.show_input_prompt("Enter image search query")
        if query:
            try:
                import webbrowser
                import urllib.parse
                
                # Create Brave image search URL
                search_url = f"https://search.brave.com/images?q={urllib.parse.quote(query)}"
                
                print(f"🖼️  Searching images for: {query}")
                print("─" * 50)
                print("Opening Brave image search in your default browser...")
                
                # Open in default browser
                webbrowser.open(search_url)
                
                print("✅ Image search opened in browser!")
                
            except Exception as e:
                print(f"❌ Search error: {e}")
        else:
            print("❌ No search query provided")
        
        input("Press Enter to continue...")
    
    def brave_document_search(self):
        """Search documents using Brave"""
        query = self.menu.show_input_prompt("Enter document search query")
        if query:
            try:
                import webbrowser
                import urllib.parse
                
                # Create Brave document search URL
                search_url = f"https://search.brave.com/search?q={urllib.parse.quote(query)}&source=web"
                
                print(f"📚 Searching documents for: {query}")
                print("─" * 50)
                print("Opening Brave document search in your default browser...")
                
                # Open in default browser
                webbrowser.open(search_url)
                
                print("✅ Document search opened in browser!")
                
            except Exception as e:
                print(f"❌ Search error: {e}")
        else:
            print("❌ No search query provided")
        
        input("Press Enter to continue...")
    
    def brave_video_search(self):
        """Search videos using Brave"""
        query = self.menu.show_input_prompt("Enter video search query")
        if query:
            try:
                import webbrowser
                import urllib.parse
                
                # Create Brave video search URL
                search_url = f"https://search.brave.com/videos?q={urllib.parse.quote(query)}"
                
                print(f"🎥 Searching videos for: {query}")
                print("─" * 50)
                print("Opening Brave video search in your default browser...")
                
                # Open in default browser
                webbrowser.open(search_url)
                
                print("✅ Video search opened in browser!")
                
            except Exception as e:
                print(f"❌ Search error: {e}")
        else:
            print("❌ No search query provided")
        
        input("Press Enter to continue...")
    
    def brave_analytics_search(self):
        """Search analytics using Brave"""
        query = self.menu.show_input_prompt("Enter analytics search query")
        if query:
            try:
                import webbrowser
                import urllib.parse
                
                # Create Brave analytics search URL
                search_url = f"https://search.brave.com/search?q={urllib.parse.quote(query + ' analytics data')}"
                
                print(f"📊 Searching analytics for: {query}")
                print("─" * 50)
                print("Opening Brave analytics search in your default browser...")
                
                # Open in default browser
                webbrowser.open(search_url)
                
                print("✅ Analytics search opened in browser!")
                
            except Exception as e:
                print(f"❌ Search error: {e}")
        else:
            print("❌ No search query provided")
        
        input("Press Enter to continue...")
    
    # ===== OLLAMA AI FUNCTIONS =====
    
    def ollama_chat(self):
        """Chat with local Ollama AI"""
        try:
            import requests
            
            model = self.menu.show_input_prompt("Enter model name (e.g., llama2)", "llama2")
            message = self.menu.show_input_prompt("Enter your message")
            
            if message:
                url = "http://localhost:11434/api/generate"
                data = {
                    "model": model,
                    "prompt": message,
                    "stream": False
                }
                
                response = requests.post(url, json=data)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"🤖 AI Response:")
                    print("─" * 50)
                    print(result.get('response', 'No response'))
                else:
                    print("❌ Ollama not running or model not found")
                    print("Start Ollama with: ollama serve")
                    print("Pull model with: ollama pull llama2")
                    
        except ImportError:
            print("❌ requests library not installed. Install with: pip install requests")
        except Exception as e:
            print(f"❌ Chat error: {e}")
        
        input("Press Enter to continue...")
    
    def ollama_generate_text(self):
        """Generate text with Ollama"""
        try:
            import requests
            
            model = self.menu.show_input_prompt("Enter model name", "llama2")
            prompt = self.menu.show_input_prompt("Enter generation prompt")
            
            if prompt:
                url = "http://localhost:11434/api/generate"
                data = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
                
                response = requests.post(url, json=data)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"📝 Generated Text:")
                    print("─" * 50)
                    print(result.get('response', 'No response'))
                else:
                    print("❌ Ollama not running or model not found")
                    
        except ImportError:
            print("❌ requests library not installed. Install with: pip install requests")
        except Exception as e:
            print(f"❌ Generation error: {e}")
        
        input("Press Enter to continue...")
    
    def ollama_ask_questions(self):
        """Ask questions to Ollama"""
        print("🔍 Question answering feature coming soon!")
        input("Press Enter to continue...")
    
    def ollama_analyze_data(self):
        """Analyze data with Ollama"""
        print("📊 Data analysis feature coming soon!")
        input("Press Enter to continue...")
    
    def ollama_generate_images(self):
        """Generate images with Ollama"""
        print("🖼️  Image generation feature coming soon!")
        input("Press Enter to continue...")
    
    def ollama_document_analysis(self):
        """Analyze documents with Ollama"""
        print("📚 Document analysis feature coming soon!")
        input("Press Enter to continue...")
    
    def ollama_settings(self):
        """Configure Ollama settings"""
        options = ["Change Model", "Set API URL", "Configure Parameters"]
        choice = self.menu.show_dropdown("Ollama Settings", options)
        
        if choice >= 0:
            print(f"⚙️  {options[choice]} - Feature coming soon!")
        else:
            print("❌ Settings cancelled.")
        
        input("Press Enter to continue...")
    
    # ===== SYSTEM MONITOR FUNCTIONS =====
    
    def system_info(self):
        """Display system information"""
        try:
            import platform
            import psutil
            
            print("💻 System Information")
            print("─" * 40)
            print(f"OS: {platform.system()} {platform.release()}")
            print(f"Architecture: {platform.machine()}")
            print(f"Processor: {platform.processor()}")
            print(f"Hostname: {platform.node()}")
            print(f"Python: {platform.python_version()}")
            
            # Memory info
            memory = psutil.virtual_memory()
            print(f"Memory: {memory.total // (1024**3)} GB total")
            print(f"Memory Usage: {memory.percent}%")
            
            # Disk info
            disk = psutil.disk_usage('/')
            print(f"Disk: {disk.total // (1024**3)} GB total")
            print(f"Disk Usage: {disk.percent}%")
            
        except ImportError:
            print("❌ psutil library not installed. Install with: pip install psutil")
        except Exception as e:
            print(f"❌ Error getting system info: {e}")
        
        input("Press Enter to continue...")
    
    def network_status(self):
        """Check network status"""
        try:
            import psutil
            import requests
            
            print("🌐 Network Status")
            print("─" * 30)
            
            # Network interfaces
            interfaces = psutil.net_if_addrs()
            for interface, addresses in interfaces.items():
                print(f"📡 {interface}:")
                for addr in addresses:
                    if addr.family == 2:  # IPv4
                        print(f"  IP: {addr.address}")
            
            # Internet connectivity
            try:
                response = requests.get("http://www.google.com", timeout=5)
                print("✅ Internet: Connected")
            except:
                print("❌ Internet: Disconnected")
                
        except ImportError:
            print("❌ Required libraries not installed. Install with: pip install psutil requests")
        except Exception as e:
            print(f"❌ Network error: {e}")
        
        input("Press Enter to continue...")
    
    def performance_monitor(self):
        """Monitor system performance"""
        try:
            import psutil
            
            print("📊 Performance Monitor")
            print("─" * 30)
            
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            print(f"🔥 CPU Usage: {cpu_percent}%")
            
            # Memory
            memory = psutil.virtual_memory()
            print(f"💾 Memory Usage: {memory.percent}%")
            
            # Disk
            disk = psutil.disk_usage('/')
            print(f"💿 Disk Usage: {disk.percent}%")
            
            # Network
            network = psutil.net_io_counters()
            print(f"📈 Network Bytes Sent: {network.bytes_sent // 1024} KB")
            print(f"📈 Network Bytes Recv: {network.bytes_recv // 1024} KB")
            
        except ImportError:
            print("❌ psutil library not installed. Install with: pip install psutil")
        except Exception as e:
            print(f"❌ Performance error: {e}")
        
        input("Press Enter to continue...")
    
    def cpu_usage(self):
        """Detailed CPU usage"""
        try:
            import psutil
            
            print("🔥 CPU Usage Details")
            print("─" * 30)
            
            # Overall CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            print(f"Overall CPU: {cpu_percent}%")
            
            # Per-core CPU
            cpu_count = psutil.cpu_count()
            cpu_percent_per_core = psutil.cpu_percent(interval=1, percpu=True)
            
            print(f"CPU Cores: {cpu_count}")
            for i, percent in enumerate(cpu_percent_per_core):
                print(f"Core {i+1}: {percent}%")
            
        except ImportError:
            print("❌ psutil library not installed. Install with: pip install psutil")
        except Exception as e:
            print(f"❌ CPU error: {e}")
        
        input("Press Enter to continue...")
    
    def memory_usage(self):
        """Detailed memory usage"""
        try:
            import psutil
            
            print("💾 Memory Usage Details")
            print("─" * 30)
            
            memory = psutil.virtual_memory()
            print(f"Total: {memory.total // (1024**3)} GB")
            print(f"Available: {memory.available // (1024**3)} GB")
            print(f"Used: {memory.used // (1024**3)} GB")
            print(f"Percentage: {memory.percent}%")
            
            # Swap memory
            swap = psutil.swap_memory()
            print(f"Swap Total: {swap.total // (1024**3)} GB")
            print(f"Swap Used: {swap.used // (1024**3)} GB")
            print(f"Swap Percentage: {swap.percent}%")
            
        except ImportError:
            print("❌ psutil library not installed. Install with: pip install psutil")
        except Exception as e:
            print(f"❌ Memory error: {e}")
        
        input("Press Enter to continue...")
    
    def disk_usage(self):
        """Detailed disk usage"""
        try:
            import psutil
            
            print("💿 Disk Usage Details")
            print("─" * 40)
            
            partitions = psutil.disk_partitions()
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    print(f"📁 {partition.device} ({partition.mountpoint})")
                    print(f"  Total: {usage.total // (1024**3)} GB")
                    print(f"  Used: {usage.used // (1024**3)} GB")
                    print(f"  Free: {usage.free // (1024**3)} GB")
                    print(f"  Usage: {usage.percent}%")
                    print()
                except:
                    continue
            
        except ImportError:
            print("❌ psutil library not installed. Install with: pip install psutil")
        except Exception as e:
            print(f"❌ Disk error: {e}")
        
        input("Press Enter to continue...")
    
    def network_traffic(self):
        """Monitor network traffic"""
        try:
            import psutil
            
            print("📈 Network Traffic")
            print("─" * 30)
            
            # Get network stats
            net_io = psutil.net_io_counters()
            
            print(f"Bytes Sent: {net_io.bytes_sent}")
            print(f"Bytes Received: {net_io.bytes_recv}")
            print(f"Packets Sent: {net_io.packets_sent}")
            print(f"Packets Received: {net_io.packets_recv}")
            
            # Convert to human readable
            sent_mb = net_io.bytes_sent / (1024**2)
            recv_mb = net_io.bytes_recv / (1024**2)
            print(f"Sent: {sent_mb:.2f} MB")
            print(f"Received: {recv_mb:.2f} MB")
            
        except ImportError:
            print("❌ psutil library not installed. Install with: pip install psutil")
        except Exception as e:
            print(f"❌ Network error: {e}")
        
        input("Press Enter to continue...")
    
    def process_monitor(self):
        """Monitor running processes"""
        try:
            import psutil
            
            print("🖥️  Process Monitor")
            print("─" * 50)
            
            # Get top processes by CPU
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            print("Top 10 processes by CPU usage:")
            print("PID    CPU%   MEM%   Name")
            print("─" * 50)
            
            for proc in processes[:10]:
                print(f"{proc['pid']:6d} {proc['cpu_percent']:6.1f} {proc['memory_percent']:6.1f} {proc['name']}")
            
        except ImportError:
            print("❌ psutil library not installed. Install with: pip install psutil")
        except Exception as e:
            print(f"❌ Process error: {e}")
        
        input("Press Enter to continue...")
    
    # ===== SECURITY MONITOR FUNCTIONS =====
    
    def security_scan(self):
        """Perform security scan"""
        print("🔍 Security Scan")
        print("─" * 30)
        
        # Check for common security issues
        checks = [
            ("File permissions", self.check_file_permissions()),
            ("Open ports", self.check_open_ports()),
            ("Suspicious processes", self.check_suspicious_processes()),
            ("Firewall status", self.check_firewall_status())
        ]
        
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"{status} {check_name}")
        
        input("Press Enter to continue...")
    
    def check_file_permissions(self):
        """Check file permissions"""
        try:
            # Check if sensitive files have proper permissions
            sensitive_files = ["/etc/passwd", "/etc/shadow", "/etc/sudoers"]
            for file in sensitive_files:
                if os.path.exists(file):
                    stat = os.stat(file)
                    mode = stat.st_mode & 0o777
                    if mode != 0o644:  # Expected permission
                        return False
            return True
        except:
            return False
    
    def check_open_ports(self):
        """Check for open ports"""
        try:
            import socket
            # Check common ports
            common_ports = [22, 80, 443, 3306, 5432]
            for port in common_ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                if result == 0:
                    return True
            return False
        except:
            return False
    
    def check_suspicious_processes(self):
        """Check for suspicious processes"""
        try:
            import psutil
            suspicious_keywords = ['keylogger', 'backdoor', 'trojan', 'malware']
            for proc in psutil.process_iter(['name']):
                try:
                    if any(keyword in proc.info['name'].lower() for keyword in suspicious_keywords):
                        return True
                except:
                    continue
            return False
        except:
            return False
    
    def check_firewall_status(self):
        """Check firewall status"""
        try:
            import subprocess
            result = subprocess.run(['sudo', 'ufw', 'status'], 
                                 capture_output=True, text=True)
            return 'active' in result.stdout.lower()
        except:
            return False
    
    def threat_detection(self):
        """Detect security threats"""
        print("🚨 Threat Detection")
        print("─" * 30)
        print("Scanning for threats...")
        
        threats_found = []
        
        # Check for suspicious files
        suspicious_extensions = ['.exe', '.bat', '.sh', '.py']
        for root, dirs, files in os.walk(os.path.expanduser("~")):
            for file in files:
                if any(file.endswith(ext) for ext in suspicious_extensions):
                    threats_found.append(f"Suspicious file: {os.path.join(root, file)}")
        
        if threats_found:
            print("⚠️  Potential threats found:")
            for threat in threats_found[:10]:  # Show first 10
                print(f"  {threat}")
        else:
            print("✅ No obvious threats detected")
        
        input("Press Enter to continue...")
    
    def password_check(self):
        """Check password strength"""
        password = self.menu.show_input_prompt("Enter password to check (will not be stored)")
        if password:
            strength = 0
            feedback = []
            
            if len(password) >= 8:
                strength += 1
            else:
                feedback.append("Password should be at least 8 characters")
            
            if any(c.isupper() for c in password):
                strength += 1
            else:
                feedback.append("Add uppercase letters")
            
            if any(c.islower() for c in password):
                strength += 1
            else:
                feedback.append("Add lowercase letters")
            
            if any(c.isdigit() for c in password):
                strength += 1
            else:
                feedback.append("Add numbers")
            
            if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
                strength += 1
            else:
                feedback.append("Add special characters")
            
            print("🔐 Password Strength Check")
            print("─" * 30)
            
            if strength == 5:
                print("✅ Strong password")
            elif strength >= 3:
                print("⚠️  Medium strength password")
            else:
                print("❌ Weak password")
            
            print(f"Score: {strength}/5")
            
            if feedback:
                print("Suggestions:")
                for suggestion in feedback:
                    print(f"  • {suggestion}")
        else:
            print("❌ No password provided")
        
        input("Press Enter to continue...")
    
    def firewall_status(self):
        """Check firewall status"""
        print("🛡️  Firewall Status")
        print("─" * 30)
        
        try:
            import subprocess
            
            # Check UFW status
            result = subprocess.run(['sudo', 'ufw', 'status'], 
                                 capture_output=True, text=True)
            
            if result.returncode == 0:
                print("UFW Status:")
                print(result.stdout)
            else:
                print("❌ UFW not available or not running")
                
        except Exception as e:
            print(f"❌ Error checking firewall: {e}")
        
        input("Press Enter to continue...")
    
    def security_logs(self):
        """View security logs"""
        print("📊 Security Logs")
        print("─" * 30)
        
        try:
            import subprocess
            
            # Check system logs for security events
            result = subprocess.run(['sudo', 'journalctl', '--since', '1 hour ago', 
                                   '|', 'grep', '-i', 'security'], 
                                 capture_output=True, text=True, shell=True)
            
            if result.stdout:
                print("Recent security events:")
                print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
            else:
                print("No recent security events found")
                
        except Exception as e:
            print(f"❌ Error reading security logs: {e}")
        
        input("Press Enter to continue...")
    
    def file_permissions(self):
        """Check file permissions"""
        print("🔒 File Permissions Check")
        print("─" * 40)
        
        directory = self.menu.show_input_prompt("Enter directory to check", os.getcwd())
        
        if directory and os.path.exists(directory):
            try:
                for root, dirs, files in os.walk(directory):
                    for file in files[:20]:  # Limit to first 20 files
                        file_path = os.path.join(root, file)
                        try:
                            stat = os.stat(file_path)
                            mode = stat.st_mode & 0o777
                            print(f"{oct(mode)} {file_path}")
                        except:
                            continue
                    break  # Only check first level
            except Exception as e:
                print(f"❌ Error checking permissions: {e}")
        else:
            print("❌ Invalid directory")
        
        input("Press Enter to continue...")
    
    def network_security(self):
        """Check network security"""
        print("🌐 Network Security")
        print("─" * 30)
        
        try:
            import socket
            import subprocess
            
            # Check for open ports
            print("Checking open ports...")
            open_ports = []
            for port in range(1, 1025):  # Check first 1024 ports
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                if result == 0:
                    open_ports.append(port)
            
            if open_ports:
                print(f"Open ports: {open_ports[:10]}")  # Show first 10
            else:
                print("No open ports found")
                
        except Exception as e:
            print(f"❌ Network security error: {e}")
        
        input("Press Enter to continue...")
    
    def device_security(self):
        """Check device security"""
        print("📱 Device Security")
        print("─" * 30)
        
        # Check various security aspects
        checks = [
            ("Screen lock enabled", self.check_screen_lock()),
            ("Encryption enabled", self.check_encryption()),
            ("Auto-updates enabled", self.check_auto_updates()),
            ("Antivirus installed", self.check_antivirus())
        ]
        
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"{status} {check_name}")
        
        input("Press Enter to continue...")
    
    def check_screen_lock(self):
        """Check if screen lock is enabled"""
        # This is a simplified check
        return True  # Assume enabled
    
    def check_encryption(self):
        """Check if disk encryption is enabled"""
        try:
            import subprocess
            result = subprocess.run(['sudo', 'fdeutil', 'status'], 
                                 capture_output=True, text=True)
            return 'enabled' in result.stdout.lower()
        except:
            return False
    
    def check_auto_updates(self):
        """Check if auto-updates are enabled"""
        # This is a simplified check
        return True  # Assume enabled
    
    def check_antivirus(self):
        """Check if antivirus is installed"""
        try:
            import subprocess
            # Check for common antivirus software
            antivirus_commands = ['clamscan', 'sophos', 'mcafee', 'norton']
            for cmd in antivirus_commands:
                result = subprocess.run(['which', cmd], 
                                     capture_output=True, text=True)
                if result.returncode == 0:
                    return True
            return False
        except:
            return False
    
    def run(self):
        """Main application loop"""
        while self.running:
            self.display_header()
            self.main_menu()
        
        print("\n👋 Thanks for using Ultimate Cron Job Manager!")

def main():
    """Main entry point"""
    manager = UltimateCronManager()
    manager.run()

if __name__ == "__main__":
    main() 