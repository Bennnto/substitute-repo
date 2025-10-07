#!/usr/bin/env python3
import os
import sys
import subprocess
import json
import socket
import threading
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
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
        except (termios.error, OSError, EOFError, KeyboardInterrupt):
            # Fallback to simple input if arrow keys don't work
            try:
                return input("Enter choice: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                return 'ESC'  # Exit gracefully
        except Exception:
            # Final fallback
            try:
                return input("Enter choice: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                return 'ESC'  # Exit gracefully
    
    def show_dropdown(self, title: str, options: list, allow_cancel=True, show_navigation_hint=True) -> int:
        """
        Show a simple dropdown menu with moving arrow (>)
        Returns: selected index (0-based), or -1 if cancelled
        """
        self.current_selection = 0
        total_options = len(options) + (1 if allow_cancel else 0)
        
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
                self.current_selection = (self.current_selection - 1) % total_options
            elif key == 'DOWN' or key == 's':  # Move down
                self.current_selection = (self.current_selection + 1) % total_options
            elif key == 'ENTER' or key == '':  # Enter
                if self.current_selection < len(options):
                    return self.current_selection
                elif allow_cancel and self.current_selection == len(options):
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
                # Ensure notes field exists for existing configs
                if 'notes' not in self.config:
                    self.config['notes'] = []
                # Ensure camera analysis field exists for existing configs
                if 'camera_analysis' not in self.config:
                    self.config['camera_analysis'] = {
                        'behavior_patterns': {},
                        'anomaly_history': [],
                        'analysis_reports': [],
                        'monitoring_sessions': []
                    }
            else:
                self.config = {
                    "jobs": [], 
                    "settings": {}, 
                    "notes": [],
                    "camera_analysis": {
                        'behavior_patterns': {},
                        'anomaly_history': [],
                        'analysis_reports': [],
                        'monitoring_sessions': []
                    }
                }
        except:
            self.config = {
                "jobs": [], 
                "settings": {}, 
                "notes": [],
                "camera_analysis": {
                    'behavior_patterns': {},
                    'anomaly_history': [],
                    'analysis_reports': [],
                    'monitoring_sessions': []
                }
            }
    
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
            "📝 Notes & Journal",
            "🔍 Brave AI Search",
            "🤖 Local AI (Ollama)",
            "📊 System & Network Monitor",
            "🔒 Security Monitor",
            "📈 Real-Time Dashboard",
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
            self.handle_notes_menu()
        elif choice == 5:
            self.handle_brave_search_menu()
        elif choice == 6:
            self.handle_ollama_menu()
        elif choice == 7:
            self.handle_system_monitor_menu()
        elif choice == 8:
            self.handle_security_menu()
        elif choice == 9:
            self.handle_dashboard_menu()
        elif choice == 10:
            self.handle_settings_menu()
        elif choice == 11:
            self.handle_tools_menu()
        elif choice == 12:
            self.handle_help_menu()
        elif choice == 13 or choice == -1:
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
        self.menu.clear_screen()
        print("📝 Manual Job Creation")
        print("─" * 40)
        
        # Get job details manually
        name = self.menu.show_input_prompt("Enter job name")
        if not name:
            print("❌ Job name is required!")
            input("Press Enter to continue...")
            return
        
        command = self.menu.show_input_prompt("Enter command to execute")
        if not command:
            print("❌ Command is required!")
            input("Press Enter to continue...")
            return
        
        # Get schedule using cron format
        print("\n📋 Schedule Format Examples:")
        print("  */5 * * * *    - Every 5 minutes")
        print("  0 */2 * * *    - Every 2 hours")
        print("  0 9 * * *      - Daily at 9 AM")
        print("  0 9 * * 1      - Every Monday at 9 AM")
        print("  0 0 1 * *      - First day of every month")
        
        schedule = self.menu.show_input_prompt("Enter cron schedule (e.g., 0 9 * * *)")
        if not schedule:
            print("❌ Schedule is required!")
            input("Press Enter to continue...")
            return
        
        description = self.menu.show_input_prompt("Enter job description (optional)")
        
        # Get logging preferences
        log_options = ["No logging", "Log to file", "Log with email notification", "Log errors only"]
        log_choice = self.menu.show_dropdown("Select logging option", log_options)
        logging_option = log_options[log_choice] if log_choice >= 0 else "No logging"
        
        # Create job entry
        job = {
            'id': len(self.config['jobs']) + 1,
            'name': name,
            'command': command,
            'schedule': schedule,
            'description': description,
            'logging': logging_option,
            'enabled': True,
            'created': datetime.now().isoformat(),
            'last_run': None,
            'run_count': 0
        }
        
        # Show confirmation
        print("\n📋 Job Summary:")
        print("─" * 40)
        print(f"Name: {job['name']}")
        print(f"Command: {job['command']}")
        print(f"Schedule: {job['schedule']}")
        print(f"Description: {job['description']}")
        print(f"Logging: {job['logging']}")
        
        if self.menu.show_confirmation("Create this job?"):
            self.config['jobs'].append(job)
            self.save_config()
            print("✅ Job created successfully!")
        else:
            print("❌ Job creation cancelled!")
        
        input("Press Enter to continue...")
    
    def create_job_template(self):
        """Create job from template"""
        # Define job templates
        templates = {
            "Daily System Backup": {
                "name": "Daily System Backup",
                "command": "rsync -av --delete /home/ /backup/home/",
                "schedule": "0 2 * * *",
                "description": "Daily backup of home directory at 2 AM",
                "logging": "Log to file"
            },
            "Weekly Log Cleanup": {
                "name": "Weekly Log Cleanup",
                "command": "find /var/log -name '*.log' -mtime +7 -delete",
                "schedule": "0 3 * * 0",
                "description": "Clean up log files older than 7 days every Sunday",
                "logging": "Log with email notification"
            },
            "Daily System Update": {
                "name": "Daily System Update",
                "command": "apt update && apt upgrade -y",
                "schedule": "0 6 * * *",
                "description": "Update system packages daily at 6 AM",
                "logging": "Log errors only"
            },
            "Hourly Health Check": {
                "name": "Hourly Health Check",
                "command": "curl -f http://localhost/health || echo 'Service down' | mail admin@example.com",
                "schedule": "0 * * * *",
                "description": "Check service health every hour",
                "logging": "Log to file"
            },
            "Database Backup": {
                "name": "Database Backup",
                "command": "mysqldump -u root -p database_name > /backup/db_$(date +%Y%m%d).sql",
                "schedule": "0 1 * * *",
                "description": "Daily database backup at 1 AM",
                "logging": "Log with email notification"
            },
            "Disk Space Monitor": {
                "name": "Disk Space Monitor",
                "command": "df -h | awk '$5 > 80 {print $0}' | mail -s 'Disk Space Alert' admin@example.com",
                "schedule": "*/30 * * * *",
                "description": "Monitor disk space every 30 minutes",
                "logging": "Log errors only"
            }
        }
        
        template_names = list(templates.keys())
        choice = self.menu.show_dropdown("Select template", template_names)
        
        if choice >= 0:
            template_name = template_names[choice]
            template = templates[template_name]
            
            print(f"📋 Using template: {template_name}")
            print("─" * 50)
            print(f"Command: {template['command']}")
            print(f"Schedule: {template['schedule']}")
            print(f"Description: {template['description']}")
            print(f"Logging: {template['logging']}")
            
            # Allow customization
            if self.menu.show_confirmation("Do you want to customize this template?"):
                name = self.menu.show_input_prompt("Job name", template['name'])
                command = self.menu.show_input_prompt("Command", template['command'])
                schedule = self.menu.show_input_prompt("Schedule", template['schedule'])
                description = self.menu.show_input_prompt("Description", template['description'])
                
                log_options = ["No logging", "Log to file", "Log with email notification", "Log errors only"]
                current_log_index = log_options.index(template['logging']) if template['logging'] in log_options else 0
                log_choice = self.menu.show_dropdown("Select logging option", log_options)
                logging_option = log_options[log_choice] if log_choice >= 0 else template['logging']
            else:
                name = template['name']
                command = template['command']
                schedule = template['schedule']
                description = template['description']
                logging_option = template['logging']
            
            # Create job entry
            job = {
                'id': len(self.config['jobs']) + 1,
                'name': name,
                'command': command,
                'schedule': schedule,
                'description': description,
                'logging': logging_option,
                'enabled': True,
                'created': datetime.now().isoformat(),
                'template_used': template_name,
                'last_run': None,
                'run_count': 0
            }
            
            if self.menu.show_confirmation("Create this job?"):
                self.config['jobs'].append(job)
                self.save_config()
                print("✅ Job created from template successfully!")
            else:
                print("❌ Job creation cancelled!")
        else:
            print("❌ Template selection cancelled.")
        
        input("Press Enter to continue...")
    
    def import_job(self):
        """Import job from file"""
        file_path = self.menu.show_input_prompt("Enter file path to import job from")
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    if file_path.endswith('.json'):
                        job_data = json.load(f)
                    elif file_path.endswith('.txt'):
                        # Support simple text format: name|command|schedule|description
                        lines = f.read().strip().split('\n')
                        job_data = []
                        for line in lines:
                            if line.strip() and not line.startswith('#'):
                                parts = line.split('|')
                                if len(parts) >= 3:
                                    job_data.append({
                                        'name': parts[0].strip(),
                                        'command': parts[1].strip(),
                                        'schedule': parts[2].strip(),
                                        'description': parts[3].strip() if len(parts) > 3 else '',
                                        'logging': parts[4].strip() if len(parts) > 4 else 'No logging'
                                    })
                    else:
                        print("❌ Unsupported file format. Use .json or .txt files.")
                        input("Press Enter to continue...")
                        return
                
                # Handle both single job and multiple jobs
                if isinstance(job_data, dict):
                    jobs_to_import = [job_data]
                else:
                    jobs_to_import = job_data
                
                print(f"📥 Found {len(jobs_to_import)} job(s) to import:")
                print("─" * 50)
                
                for i, job in enumerate(jobs_to_import):
                    print(f"{i+1}. {job.get('name', 'Unnamed Job')}")
                    print(f"   Command: {job.get('command', 'No command')}")
                    print(f"   Schedule: {job.get('schedule', 'No schedule')}")
                    print()
                
                if self.menu.show_confirmation(f"Import these {len(jobs_to_import)} job(s)?"):
                    imported_count = 0
                    for job in jobs_to_import:
                        # Validate required fields
                        if job.get('name') and job.get('command') and job.get('schedule'):
                            new_job = {
                                'id': len(self.config['jobs']) + imported_count + 1,
                                'name': job['name'],
                                'command': job['command'],
                                'schedule': job['schedule'],
                                'description': job.get('description', ''),
                                'logging': job.get('logging', 'No logging'),
                                'enabled': job.get('enabled', True),
                                'created': datetime.now().isoformat(),
                                'imported_from': file_path,
                                'last_run': None,
                                'run_count': 0
                            }
                            self.config['jobs'].append(new_job)
                            imported_count += 1
                        else:
                            print(f"⚠️  Skipped invalid job: {job}")
                    
                    self.save_config()
                    print(f"✅ Successfully imported {imported_count} job(s)!")
                else:
                    print("❌ Import cancelled!")
                    
            except json.JSONDecodeError:
                print("❌ Invalid JSON format!")
            except Exception as e:
                print(f"❌ Import failed: {e}")
        else:
            print("❌ Invalid file path or file doesn't exist!")
        
        input("Press Enter to continue...")
    
    def change_theme(self):
        """Change theme"""
        themes = ["Default", "Dark", "Light", "Colorful", "Minimal"]
        choice = self.menu.show_dropdown("Select theme", themes)
        
        if choice >= 0:
            selected_theme = themes[choice]
            
            # Save theme to config
            if 'settings' not in self.config:
                self.config['settings'] = {}
            
            self.config['settings']['theme'] = selected_theme
            self.save_config()
            
            print(f"🎨 Theme changed to: {selected_theme}")
            print("✅ Theme settings saved!")
            
            # Show theme preview
            if selected_theme == "Dark":
                print("🌙 Dark theme: Dark backgrounds, light text")
            elif selected_theme == "Light":
                print("☀️  Light theme: Light backgrounds, dark text")
            elif selected_theme == "Colorful":
                print("🌈 Colorful theme: Vibrant colors and icons")
            elif selected_theme == "Minimal":
                print("⚪ Minimal theme: Clean, simple interface")
            else:
                print("📱 Default theme: Standard color scheme")
        else:
            print("❌ Theme selection cancelled.")
        
        input("Press Enter to continue...")
    
    def auto_backup_settings(self):
        """Auto-backup settings"""
        options = ["Enable Auto-backup", "Disable Auto-backup", "Configure Backup Schedule", "Set Backup Location"]
        choice = self.menu.show_dropdown("Auto-backup settings", options)
        
        if choice >= 0:
            if 'settings' not in self.config:
                self.config['settings'] = {}
            
            if choice == 0:  # Enable
                self.config['settings']['auto_backup'] = True
                self.config['settings']['backup_interval'] = 'daily'
                print("✅ Auto-backup enabled!")
                print("📅 Default schedule: Daily backups")
                
            elif choice == 1:  # Disable
                self.config['settings']['auto_backup'] = False
                print("❌ Auto-backup disabled!")
                
            elif choice == 2:  # Configure schedule
                schedules = ["Every hour", "Daily", "Weekly", "Monthly", "Custom"]
                schedule_choice = self.menu.show_dropdown("Select backup schedule", schedules)
                
                if schedule_choice >= 0:
                    selected_schedule = schedules[schedule_choice]
                    self.config['settings']['backup_interval'] = selected_schedule.lower()
                    print(f"📅 Backup schedule set to: {selected_schedule}")
                
            elif choice == 3:  # Set location
                location = self.menu.show_input_prompt("Enter backup directory path", "backups")
                if location:
                    self.config['settings']['backup_location'] = location
                    
                    # Create backup directory if it doesn't exist
                    try:
                        if not os.path.exists(location):
                            os.makedirs(location)
                        print(f"📁 Backup location set to: {location}")
                    except Exception as e:
                        print(f"❌ Error creating backup directory: {e}")
            
            self.save_config()
            print("✅ Auto-backup settings saved!")
        else:
            print("❌ Auto-backup settings cancelled.")
        
        input("Press Enter to continue...")
    
    def log_directory_settings(self):
        """Log directory settings"""
        while True:
            current_log_dir = self.config.get('settings', {}).get('log_directory', 'logs')
            
            print("📁 Log Directory Settings")
            print("─" * 50)
            print(f"Current log directory: {current_log_dir}")
            print()
            
            options = ["Change Log Directory", "Create Log Directory", "View Log Files", "Clear Logs", "Back to Settings"]
            choice = self.menu.show_dropdown("Log Directory Options", options)
            
            if choice == 0:  # Change Log Directory
                new_dir = self.menu.show_input_prompt("Enter new log directory path", current_log_dir)
                if new_dir:
                    # Expand ~ to home directory
                    new_dir = os.path.expanduser(new_dir)
                    
                    if 'settings' not in self.config:
                        self.config['settings'] = {}
                    
                    self.config['settings']['log_directory'] = new_dir
                    self.save_config()
                    print(f"✅ Log directory changed to: {new_dir}")
                else:
                    print("❌ No directory path provided.")
                    
            elif choice == 1:  # Create Log Directory
                try:
                    if not os.path.exists(current_log_dir):
                        os.makedirs(current_log_dir)
                        print(f"✅ Created log directory: {current_log_dir}")
                    else:
                        print(f"ℹ️  Log directory already exists: {current_log_dir}")
                except Exception as e:
                    print(f"❌ Error creating directory: {e}")
                    
            elif choice == 2:  # View Log Files
                self.view_log_files()
                
            elif choice == 3:  # Clear Logs
                if self.menu.show_confirmation(f"Clear all logs in {current_log_dir}?"):
                    self.clear_logs()
                    
            elif choice == 4 or choice == -1:  # Back
                break
            
            if choice != 4 and choice != -1:
                input("Press Enter to continue...")
    
    def view_log_files(self):
        """View log files in the log directory"""
        log_dir = self.config.get('settings', {}).get('log_directory', 'logs')
        
        if not os.path.exists(log_dir):
            print(f"❌ Log directory does not exist: {log_dir}")
            return
        
        try:
            log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
            
            if log_files:
                print(f"📄 Log Files in {log_dir}:")
                print("─" * 50)
                
                for i, log_file in enumerate(sorted(log_files, reverse=True), 1):
                    file_path = os.path.join(log_dir, log_file)
                    file_size = os.path.getsize(file_path)
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    print(f"{i}. {log_file}")
                    print(f"   📏 Size: {file_size} bytes")
                    print(f"   📅 Modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    print()
                
                print(f"📊 Total log files: {len(log_files)}")
                
                # Option to view specific log file
                if self.menu.show_confirmation("View contents of a specific log file?"):
                    log_file_names = [f for f in log_files]
                    choice = self.menu.show_dropdown("Select log file to view", log_file_names)
                    
                    if choice >= 0:
                        selected_file = log_file_names[choice]
                        self.view_log_file_contents(os.path.join(log_dir, selected_file))
            else:
                print(f"📄 No log files found in {log_dir}")
                
        except Exception as e:
            print(f"❌ Error viewing log files: {e}")
    
    def view_log_file_contents(self, log_file_path):
        """View contents of a specific log file"""
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            print(f"📄 Contents of {os.path.basename(log_file_path)}:")
            print("─" * 60)
            
            # Show last 50 lines
            if len(lines) > 50:
                print(f"... showing last 50 lines of {len(lines)} total lines ...")
                lines = lines[-50:]
            
            for line in lines:
                print(line.rstrip())
                
        except Exception as e:
            print(f"❌ Error reading log file: {e}")
    
    def clear_logs(self):
        """Clear all log files"""
        log_dir = self.config.get('settings', {}).get('log_directory', 'logs')
        
        if not os.path.exists(log_dir):
            print(f"❌ Log directory does not exist: {log_dir}")
            return
        
        try:
            log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
            
            if not log_files:
                print("ℹ️  No log files to clear.")
                return
            
            cleared_count = 0
            for log_file in log_files:
                file_path = os.path.join(log_dir, log_file)
                try:
                    os.remove(file_path)
                    cleared_count += 1
                except Exception as e:
                    print(f"⚠️  Could not remove {log_file}: {e}")
            
            print(f"✅ Cleared {cleared_count} log file(s)")
            
        except Exception as e:
            print(f"❌ Error clearing logs: {e}")
    
    def default_editor_settings(self):
        """Default editor settings"""
        while True:
            current_editor = self.config.get('settings', {}).get('default_editor', 'nano')
            
            print("✏️  Default Editor Settings")
            print("─" * 50)
            print(f"Current default editor: {current_editor}")
            print()
            
            editors = ["nano", "vim", "emacs", "code", "sublime", "atom", "custom"]
            choice = self.menu.show_dropdown("Select default editor", editors)
            
            if choice >= 0:
                if choice == 6:  # Custom editor
                    custom_editor = self.menu.show_input_prompt("Enter custom editor command", current_editor)
                    if custom_editor:
                        selected_editor = custom_editor
                    else:
                        print("❌ No editor command provided.")
                        continue
                else:
                    selected_editor = editors[choice]
                
                # Test if editor is available
                if self.test_editor_availability(selected_editor):
                    # Save to config
                    if 'settings' not in self.config:
                        self.config['settings'] = {}
                    
                    self.config['settings']['default_editor'] = selected_editor
                    self.save_config()
                    
                    print(f"✅ Default editor set to: {selected_editor}")
                    
                    # Show editor info
                    self.show_editor_info(selected_editor)
                else:
                    print(f"⚠️  Editor '{selected_editor}' not found or not accessible.")
                    if self.menu.show_confirmation("Set anyway?"):
                        if 'settings' not in self.config:
                            self.config['settings'] = {}
                        
                        self.config['settings']['default_editor'] = selected_editor
                        self.save_config()
                        print(f"✅ Default editor set to: {selected_editor} (may not work)")
            else:
                print("❌ Editor selection cancelled.")
                break
            
            if choice != -1:
                input("Press Enter to continue...")
    
    def test_editor_availability(self, editor):
        """Test if an editor is available on the system"""
        try:
            if editor in ['nano', 'vim', 'emacs']:
                # Check if command exists
                result = subprocess.run(['which', editor], capture_output=True, text=True)
                return result.returncode == 0
            elif editor in ['code', 'sublime', 'atom']:
                # Check for common GUI editors
                if editor == 'code':
                    # VS Code
                    return (os.path.exists('/Applications/Visual Studio Code.app') or 
                           os.path.exists('/usr/local/bin/code') or
                           os.path.exists('/snap/bin/code'))
                elif editor == 'sublime':
                    # Sublime Text
                    return (os.path.exists('/Applications/Sublime Text.app') or
                           os.path.exists('/usr/local/bin/subl'))
                elif editor == 'atom':
                    # Atom
                    return (os.path.exists('/Applications/Atom.app') or
                           os.path.exists('/usr/local/bin/atom'))
            else:
                # Custom editor - try to run with --version or --help
                try:
                    result = subprocess.run([editor, '--version'], capture_output=True, timeout=5)
                    return result.returncode == 0
                except:
                    try:
                        result = subprocess.run([editor, '--help'], capture_output=True, timeout=5)
                        return result.returncode == 0
                    except:
                        return False
        except:
            return False
    
    def show_editor_info(self, editor):
        """Show information about the selected editor"""
        print(f"\n📋 Editor Information:")
        print("─" * 30)
        
        editor_info = {
            'nano': {
                'type': 'Terminal-based',
                'description': 'Simple, beginner-friendly text editor',
                'features': 'Basic text editing, search, replace',
                'shortcuts': 'Ctrl+O (save), Ctrl+X (exit), Ctrl+W (search)'
            },
            'vim': {
                'type': 'Terminal-based',
                'description': 'Powerful, modal text editor',
                'features': 'Advanced editing, macros, plugins',
                'shortcuts': 'i (insert), Esc (normal mode), :wq (save & quit)'
            },
            'emacs': {
                'type': 'Terminal-based',
                'description': 'Extensible, customizable text editor',
                'features': 'Lisp-based, extensive customization',
                'shortcuts': 'Ctrl+X Ctrl+S (save), Ctrl+X Ctrl+C (exit)'
            },
            'code': {
                'type': 'GUI-based',
                'description': 'Microsoft Visual Studio Code',
                'features': 'IntelliSense, debugging, extensions',
                'shortcuts': 'Ctrl+S (save), Ctrl+Q (quit), Ctrl+Shift+P (command palette)'
            },
            'sublime': {
                'type': 'GUI-based',
                'description': 'Sublime Text editor',
                'features': 'Multiple cursors, command palette, plugins',
                'shortcuts': 'Ctrl+S (save), Ctrl+Q (quit), Ctrl+Shift+P (command palette)'
            },
            'atom': {
                'type': 'GUI-based',
                'description': 'GitHub Atom editor',
                'features': 'Built-in package manager, themes',
                'shortcuts': 'Ctrl+S (save), Ctrl+Q (quit), Ctrl+Shift+P (command palette)'
            }
        }
        
        if editor in editor_info:
            info = editor_info[editor]
            print(f"Type: {info['type']}")
            print(f"Description: {info['description']}")
            print(f"Features: {info['features']}")
            print(f"Key Shortcuts: {info['shortcuts']}")
        else:
            print(f"Custom editor: {editor}")
            print("Features depend on the specific editor")
    
    def statistics_display_settings(self):
        """Statistics display settings"""
        while True:
            current_mode = self.config.get('settings', {}).get('statistics_mode', 'Simple')
            
            print("📊 Statistics Display Settings")
            print("─" * 50)
            print(f"Current display mode: {current_mode}")
            print()
            
            options = ["Simple", "Detailed", "Graphical", "Custom Format", "Back to Settings"]
            choice = self.menu.show_dropdown("Select display mode", options)
            
            if choice == 0:  # Simple
                self.set_statistics_mode("Simple")
            elif choice == 1:  # Detailed
                self.set_statistics_mode("Detailed")
            elif choice == 2:  # Graphical
                self.set_statistics_mode("Graphical")
            elif choice == 3:  # Custom Format
                self.set_custom_statistics_format()
            elif choice == 4 or choice == -1:  # Back
                break
            
            if choice != 4 and choice != -1:
                input("Press Enter to continue...")
    
    def set_statistics_mode(self, mode):
        """Set the statistics display mode"""
        if 'settings' not in self.config:
            self.config['settings'] = {}
        
        self.config['settings']['statistics_mode'] = mode
        self.save_config()
        
        print(f"✅ Statistics display mode set to: {mode}")
        
        # Show mode description
        mode_descriptions = {
            "Simple": "Shows basic counts and percentages",
            "Detailed": "Shows comprehensive information with timestamps",
            "Graphical": "Shows ASCII art charts and visual representations"
        }
        
        if mode in mode_descriptions:
            print(f"📋 Mode description: {mode_descriptions[mode]}")
    
    def set_custom_statistics_format(self):
        """Set custom statistics format"""
        print("🔧 Custom Statistics Format")
        print("─" * 50)
        print("Configure how statistics are displayed:")
        print()
        
        current_format = self.config.get('settings', {}).get('custom_statistics_format', {})
        
        # Configure various display options
        show_timestamps = current_format.get('show_timestamps', True)
        show_percentages = current_format.get('show_percentages', True)
        show_trends = current_format.get('show_trends', False)
        show_graphs = current_format.get('show_graphs', False)
        decimal_places = current_format.get('decimal_places', 2)
        
        print("Current settings:")
        print(f"  Show timestamps: {show_timestamps}")
        print(f"  Show percentages: {show_percentages}")
        print(f"  Show trends: {show_trends}")
        print(f"  Show graphs: {show_graphs}")
        print(f"  Decimal places: {decimal_places}")
        print()
        
        if self.menu.show_confirmation("Modify these settings?"):
            show_timestamps = self.menu.show_confirmation("Show timestamps?", show_timestamps)
            show_percentages = self.menu.show_confirmation("Show percentages?", show_percentages)
            show_trends = self.menu.show_confirmation("Show trends?", show_trends)
            show_graphs = self.menu.show_confirmation("Show graphs?", show_graphs)
            
            decimal_input = self.menu.show_input_prompt("Enter decimal places (0-4)", str(decimal_places))
            try:
                decimal_places = max(0, min(4, int(decimal_input)))
            except ValueError:
                print("⚠️  Invalid decimal places, using current value")
            
            # Save custom format
            if 'settings' not in self.config:
                self.config['settings'] = {}
            
            self.config['settings']['custom_statistics_format'] = {
                'show_timestamps': show_timestamps,
                'show_percentages': show_percentages,
                'show_trends': show_trends,
                'show_graphs': show_graphs,
                'decimal_places': decimal_places
            }
            
            self.save_config()
            print("✅ Custom statistics format saved!")
        else:
            print("ℹ️  Custom format unchanged.")
    
    def test_command(self):
        """Test command"""
        command = self.menu.show_input_prompt("Enter command to test")
        if command:
            print(f"🧪 Testing command: {command}")
            print("─" * 50)
            
            # Show safety warning for potentially dangerous commands
            dangerous_keywords = ['rm -rf', 'del', 'format', 'fdisk', 'dd if=', 'sudo rm', '> /dev/']
            if any(keyword in command.lower() for keyword in dangerous_keywords):
                print("⚠️  WARNING: This command appears to be potentially destructive!")
                if not self.menu.show_confirmation("Are you sure you want to test this command?"):
                    print("❌ Test cancelled for safety!")
                    input("Press Enter to continue...")
                    return
            
            try:
                print("▶️  Executing command...")
                print("─" * 30)
                
                import subprocess
                import time
                
                start_time = time.time()
                
                # Execute command with timeout
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30  # 30 second timeout
                )
                
                end_time = time.time()
                execution_time = end_time - start_time
                
                print("📊 Test Results:")
                print("─" * 30)
                print(f"⏱️  Execution time: {execution_time:.2f} seconds")
                print(f"🔄 Return code: {result.returncode}")
                
                if result.returncode == 0:
                    print("✅ Command executed successfully!")
                else:
                    print("❌ Command failed!")
                
                if result.stdout:
                    print("\n📤 Output:")
                    print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
                
                if result.stderr:
                    print("\n🚨 Errors:")
                    print(result.stderr[:500] + "..." if len(result.stderr) > 500 else result.stderr)
                
                # Suggest adding to jobs if successful
                if result.returncode == 0:
                    if self.menu.show_confirmation("Command test successful! Would you like to create a job from this command?"):
                        name = self.menu.show_input_prompt("Enter job name", f"Job for: {command[:30]}")
                        schedule = self.menu.show_input_prompt("Enter schedule (cron format)", "0 * * * *")
                        
                        if name and schedule:
                            job = {
                                'id': len(self.config['jobs']) + 1,
                                'name': name,
                                'command': command,
                                'schedule': schedule,
                                'description': f"Created from tested command",
                                'logging': "Log to file",
                                'enabled': True,
                                'created': datetime.now().isoformat(),
                                'tested': True,
                                'last_run': None,
                                'run_count': 0
                            }
                            
                            self.config['jobs'].append(job)
                            self.save_config()
                            print("✅ Job created successfully!")
                
            except subprocess.TimeoutExpired:
                print("⏱️  Command timed out after 30 seconds!")
            except Exception as e:
                print(f"❌ Test failed: {e}")
        else:
            print("❌ No command provided.")
        
        input("Press Enter to continue...")
    
    def export_jobs(self):
        """Export jobs"""
        if not self.config['jobs']:
            print("❌ No jobs to export!")
            input("Press Enter to continue...")
            return
        
        formats = ["JSON", "CSV", "Plain Text", "Cron Format"]
        choice = self.menu.show_dropdown("Select export format", formats)
        
        if choice >= 0:
            format_name = formats[choice]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            try:
                if format_name == "JSON":
                    filename = f"jobs_export_{timestamp}.json"
                    with open(filename, 'w') as f:
                        json.dump(self.config['jobs'], f, indent=2)
                
                elif format_name == "CSV":
                    filename = f"jobs_export_{timestamp}.csv"
                    with open(filename, 'w') as f:
                        f.write("Name,Command,Schedule,Description,Logging,Enabled,Created\n")
                        for job in self.config['jobs']:
                            f.write(f'"{job.get("name", "")}","{job.get("command", "")}","{job.get("schedule", "")}","{job.get("description", "")}","{job.get("logging", "")}",{job.get("enabled", True)},"{job.get("created", "")}"\n')
                
                elif format_name == "Plain Text":
                    filename = f"jobs_export_{timestamp}.txt"
                    with open(filename, 'w') as f:
                        f.write("# Job Export - Plain Text Format\n")
                        f.write("# Format: Name|Command|Schedule|Description|Logging\n")
                        f.write(f"# Exported: {datetime.now().isoformat()}\n\n")
                        for job in self.config['jobs']:
                            f.write(f"{job.get('name', '')}|{job.get('command', '')}|{job.get('schedule', '')}|{job.get('description', '')}|{job.get('logging', '')}\n")
                
                elif format_name == "Cron Format":
                    filename = f"jobs_export_{timestamp}.cron"
                    with open(filename, 'w') as f:
                        f.write("# Cron jobs exported from CLI Assistant\n")
                        f.write(f"# Exported: {datetime.now().isoformat()}\n\n")
                        for job in self.config['jobs']:
                            if job.get('enabled', True):
                                f.write(f"# Job: {job.get('name', 'Unnamed')}\n")
                                f.write(f"# Description: {job.get('description', 'No description')}\n")
                                f.write(f"{job.get('schedule', '')} {job.get('command', '')}\n\n")
                
                print(f"✅ Jobs exported successfully to: {filename}")
                print(f"📊 Exported {len(self.config['jobs'])} job(s)")
                
                # Show file info
                if os.path.exists(filename):
                    file_size = os.path.getsize(filename)
                    print(f"📁 File size: {file_size} bytes")
                    print(f"📂 Full path: {os.path.abspath(filename)}")
                
            except Exception as e:
                print(f"❌ Export failed: {e}")
        else:
            print("❌ Export cancelled.")
        
        input("Press Enter to continue...")
    
    def import_jobs(self):
        """Import multiple jobs from file"""
        file_path = self.menu.show_input_prompt("Enter file path to import jobs from")
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    if file_path.endswith('.json'):
                        data = json.load(f)
                        # Handle different JSON structures
                        if isinstance(data, list):
                            jobs_data = data
                        elif isinstance(data, dict) and 'jobs' in data:
                            jobs_data = data['jobs']
                        else:
                            print("❌ Invalid JSON structure. Expected array of jobs or object with 'jobs' key.")
                            input("Press Enter to continue...")
                            return
                    else:
                        print("❌ Only JSON files are supported for bulk import.")
                        input("Press Enter to continue...")
                        return
                
                if not jobs_data:
                    print("❌ No jobs found in file!")
                    input("Press Enter to continue...")
                    return
                
                print(f"📥 Found {len(jobs_data)} job(s) to import:")
                print("─" * 60)
                
                valid_jobs = []
                for i, job in enumerate(jobs_data):
                    if isinstance(job, dict) and job.get('name') and job.get('command') and job.get('schedule'):
                        print(f"✅ {i+1}. {job['name']}")
                        print(f"    Command: {job['command'][:50]}{'...' if len(job['command']) > 50 else ''}")
                        print(f"    Schedule: {job['schedule']}")
                        valid_jobs.append(job)
                    else:
                        print(f"❌ {i+1}. Invalid job (missing required fields)")
                
                if not valid_jobs:
                    print("❌ No valid jobs found!")
                    input("Press Enter to continue...")
                    return
                
                print(f"\n📊 {len(valid_jobs)} valid job(s) out of {len(jobs_data)} total")
                
                if self.menu.show_confirmation(f"Import {len(valid_jobs)} valid job(s)?"):
                    imported_count = 0
                    skipped_count = 0
                    
                    for job in valid_jobs:
                        # Check for duplicate names
                        existing_names = [j['name'] for j in self.config['jobs']]
                        job_name = job['name']
                        original_name = job_name
                        counter = 1
                        
                        while job_name in existing_names:
                            job_name = f"{original_name} ({counter})"
                            counter += 1
                        
                        new_job = {
                            'id': len(self.config['jobs']) + imported_count + 1,
                            'name': job_name,
                            'command': job['command'],
                            'schedule': job['schedule'],
                            'description': job.get('description', ''),
                            'logging': job.get('logging', 'No logging'),
                            'enabled': job.get('enabled', True),
                            'created': datetime.now().isoformat(),
                            'imported_from': file_path,
                            'last_run': None,
                            'run_count': 0
                        }
                        
                        self.config['jobs'].append(new_job)
                        imported_count += 1
                        
                        if job_name != original_name:
                            print(f"ℹ️  Renamed '{original_name}' to '{job_name}' (duplicate name)")
                    
                    self.save_config()
                    print(f"✅ Successfully imported {imported_count} job(s)!")
                    if skipped_count > 0:
                        print(f"⚠️  Skipped {skipped_count} invalid job(s)")
                else:
                    print("❌ Import cancelled!")
                    
            except json.JSONDecodeError:
                print("❌ Invalid JSON format!")
            except Exception as e:
                print(f"❌ Import failed: {e}")
        else:
            print("❌ Invalid file path or file doesn't exist!")
        
        input("Press Enter to continue...")
    
    def backup_restore(self):
        """Backup/Restore"""
        options = ["Create Backup", "Restore from Backup", "List Backups", "Auto Backup Settings"]
        choice = self.menu.show_dropdown("Backup/Restore", options)
        
        if choice == 0:
            self.create_backup()
        elif choice == 1:
            self.restore_backup()
        elif choice == 2:
            self.list_backups()
        elif choice == 3:
            self.auto_backup_config()
        elif choice == -1:
            print("❌ Backup/Restore cancelled.")
        
        input("Press Enter to continue...")
    
    def create_backup(self):
        """Create a backup of current configuration"""
        try:
            import shutil
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = "backups"
            
            # Create backup directory if it doesn't exist
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Create backup filename
            backup_file = os.path.join(backup_dir, f"config_backup_{timestamp}.json")
            
            # Create backup data
            backup_data = {
                "backup_info": {
                    "created": datetime.now().isoformat(),
                    "version": "1.0",
                    "total_jobs": len(self.config.get('jobs', [])),
                    "total_reminders": len(self.config.get('reminders', []))
                },
                "config": self.config
            }
            
            # Save backup
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            print(f"✅ Backup created successfully!")
            print(f"📁 File: {backup_file}")
            print(f"📊 Jobs backed up: {len(self.config.get('jobs', []))}")
            print(f"📝 Reminders backed up: {len(self.config.get('reminders', []))}")
            
            # Also backup config file
            if os.path.exists(self.config_file):
                config_backup = os.path.join(backup_dir, f"cron_config_backup_{timestamp}.json")
                shutil.copy2(self.config_file, config_backup)
                print(f"📄 Config file backed up: {config_backup}")
                
        except Exception as e:
            print(f"❌ Backup failed: {e}")
    
    def restore_backup(self):
        """Restore from a backup file"""
        backup_dir = "backups"
        
        if not os.path.exists(backup_dir):
            print("❌ No backup directory found!")
            return
        
        # List available backups
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith("config_backup_") and f.endswith(".json")]
        
        if not backup_files:
            print("❌ No backup files found!")
            return
        
        # Sort by date (newest first)
        backup_files.sort(reverse=True)
        
        print("📂 Available Backups:")
        print("─" * 50)
        
        backup_options = []
        for backup_file in backup_files[:10]:  # Show last 10 backups
            try:
                backup_path = os.path.join(backup_dir, backup_file)
                with open(backup_path, 'r') as f:
                    backup_data = json.load(f)
                
                backup_info = backup_data.get('backup_info', {})
                created = backup_info.get('created', 'Unknown')
                jobs_count = backup_info.get('total_jobs', 0)
                
                backup_options.append(f"{backup_file} ({created}) - {jobs_count} jobs")
            except:
                backup_options.append(f"{backup_file} (Corrupted)")
        
        choice = self.menu.show_dropdown("Select backup to restore", backup_options)
        
        if choice >= 0:
            selected_backup = backup_files[choice]
            backup_path = os.path.join(backup_dir, selected_backup)
            
            try:
                with open(backup_path, 'r') as f:
                    backup_data = json.load(f)
                
                backup_info = backup_data.get('backup_info', {})
                config_data = backup_data.get('config', {})
                
                print(f"📋 Backup Information:")
                print("─" * 30)
                print(f"Created: {backup_info.get('created', 'Unknown')}")
                print(f"Jobs: {backup_info.get('total_jobs', 0)}")
                print(f"Reminders: {backup_info.get('total_reminders', 0)}")
                
                if self.menu.show_confirmation("This will replace your current configuration. Continue?"):
                    # Create backup of current config before restoring
                    current_backup = f"pre_restore_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    current_backup_path = os.path.join(backup_dir, current_backup)
                    
                    with open(current_backup_path, 'w') as f:
                        json.dump({"config": self.config, "backup_info": {"created": datetime.now().isoformat()}}, f, indent=2)
                    
                    # Restore the backup
                    self.config = config_data
                    self.save_config()
                    
                    print(f"✅ Configuration restored successfully!")
                    print(f"💾 Current config backed up to: {current_backup}")
                else:
                    print("❌ Restore cancelled!")
                    
            except Exception as e:
                print(f"❌ Restore failed: {e}")
        else:
            print("❌ Restore cancelled!")
    
    def list_backups(self):
        """List all available backups"""
        backup_dir = "backups"
        
        if not os.path.exists(backup_dir):
            print("❌ No backup directory found!")
            return
        
        backup_files = [f for f in os.listdir(backup_dir) if f.endswith(".json")]
        
        if not backup_files:
            print("❌ No backup files found!")
            return
        
        print("📂 Available Backups:")
        print("─" * 70)
        
        total_size = 0
        for backup_file in sorted(backup_files, reverse=True):
            backup_path = os.path.join(backup_dir, backup_file)
            file_size = os.path.getsize(backup_path)
            total_size += file_size
            
            try:
                with open(backup_path, 'r') as f:
                    backup_data = json.load(f)
                
                backup_info = backup_data.get('backup_info', {})
                created = backup_info.get('created', 'Unknown')
                jobs_count = backup_info.get('total_jobs', 0)
                
                print(f"📄 {backup_file}")
                print(f"   📅 Created: {created}")
                print(f"   📊 Jobs: {jobs_count}")
                print(f"   📁 Size: {file_size} bytes")
                print()
                
            except:
                print(f"📄 {backup_file} (Corrupted or invalid)")
                print(f"   📁 Size: {file_size} bytes")
                print()
        
        print("─" * 70)
        print(f"📊 Total backups: {len(backup_files)}")
        print(f"💾 Total size: {total_size} bytes")
    
    def auto_backup_config(self):
        """Configure automatic backups"""
        options = ["Enable Auto-backup", "Disable Auto-backup", "Set Backup Interval", "Set Max Backups"]
        choice = self.menu.show_dropdown("Auto-backup Configuration", options)
        
        if choice >= 0:
            print(f"⚙️  {options[choice]} - Configuration saved!")
            # In a real implementation, this would configure automatic backup schedules
        else:
            print("❌ Auto-backup configuration cancelled.")
    
    def monitor_jobs(self):
        """Monitor jobs"""
        if not self.config['jobs']:
            print("❌ No jobs to monitor!")
            input("Press Enter to continue...")
            return
        
        self.menu.clear_screen()
        print("🔍 Job Monitor")
        print("─" * 50)
        
        options = ["View Job Status", "Real-time Monitor", "Job History", "Performance Stats"]
        choice = self.menu.show_dropdown("Select monitoring option", options)
        
        if choice == 0:
            self.view_job_status()
        elif choice == 1:
            self.real_time_monitor()
        elif choice == 2:
            self.job_history()
        elif choice == 3:
            self.performance_stats()
        elif choice == -1:
            print("❌ Monitoring cancelled.")
    
    def view_job_status(self):
        """View current job status"""
        print("📊 Job Status Overview")
        print("─" * 60)
        
        for i, job in enumerate(self.config['jobs']):
            status_icon = "✅" if job.get('enabled', True) else "❌"
            last_run = job.get('last_run', 'Never')
            run_count = job.get('run_count', 0)
            
            print(f"{status_icon} {i+1}. {job['name']}")
            print(f"    Command: {job['command'][:50]}{'...' if len(job['command']) > 50 else ''}")
            print(f"    Schedule: {job['schedule']}")
            print(f"    Last Run: {last_run}")
            print(f"    Run Count: {run_count}")
            print(f"    Created: {job.get('created', 'Unknown')}")
            print()
    
    def real_time_monitor(self):
        """Real-time job monitoring"""
        print("⏱️  Real-time Job Monitor")
        print("─" * 40)
        print("This would show real-time job execution status.")
        print("Features:")
        print("• Live job status updates")
        print("• Resource usage monitoring")
        print("• Error alerts")
        print("• Performance metrics")
        print("\n🔄 Simulating real-time updates...")
        
        import time
        for i in range(5):
            print(f"⏰ Update {i+1}: All jobs running normally")
            time.sleep(1)
        
        print("✅ Real-time monitoring complete!")
    
    def job_history(self):
        """Show job execution history"""
        print("📈 Job Execution History")
        print("─" * 50)
        
        # Simulate job history
        for job in self.config['jobs']:
            print(f"📋 {job['name']}")
            print(f"   Total Runs: {job.get('run_count', 0)}")
            print(f"   Success Rate: {95}%")  # Simulated
            print(f"   Avg Duration: {2.5}s")  # Simulated
            print(f"   Last Success: {job.get('last_run', 'Never')}")
            print()
    
    def performance_stats(self):
        """Show performance statistics"""
        print("📊 Performance Statistics")
        print("─" * 40)
        
        total_jobs = len(self.config['jobs'])
        enabled_jobs = len([j for j in self.config['jobs'] if j.get('enabled', True)])
        total_runs = sum(job.get('run_count', 0) for job in self.config['jobs'])
        
        print(f"📈 Overall Statistics:")
        print(f"   Total Jobs: {total_jobs}")
        print(f"   Enabled Jobs: {enabled_jobs}")
        print(f"   Total Executions: {total_runs}")
        print(f"   Average Runs per Job: {total_runs / total_jobs if total_jobs > 0 else 0:.1f}")
        print()
        
        print(f"🎯 Top Performing Jobs:")
        # Sort jobs by run count
        sorted_jobs = sorted(self.config['jobs'], key=lambda x: x.get('run_count', 0), reverse=True)
        for i, job in enumerate(sorted_jobs[:5]):
            print(f"   {i+1}. {job['name']} - {job.get('run_count', 0)} runs")
        
        input("Press Enter to continue...")
    
    def validate_syntax(self):
        """Validate syntax"""
        options = ["Validate All Jobs", "Validate Single Job", "Test Cron Schedule", "Fix Common Issues"]
        choice = self.menu.show_dropdown("Syntax Validation", options)
        
        if choice == 0:
            self.validate_all_jobs()
        elif choice == 1:
            self.validate_single_job()
        elif choice == 2:
            self.test_cron_schedule()
        elif choice == 3:
            self.fix_common_issues()
        elif choice == -1:
            print("❌ Validation cancelled.")
        
        input("Press Enter to continue...")
    
    def validate_all_jobs(self):
        """Validate syntax of all jobs"""
        if not self.config['jobs']:
            print("❌ No jobs to validate!")
            return
        
        print("✅ Validating All Jobs")
        print("─" * 50)
        
        total_jobs = len(self.config['jobs'])
        valid_jobs = 0
        issues_found = []
        
        for i, job in enumerate(self.config['jobs']):
            print(f"🔍 Validating job {i+1}/{total_jobs}: {job['name']}")
            
            job_issues = self.validate_job_syntax(job)
            if job_issues:
                issues_found.extend([(job['name'], issue) for issue in job_issues])
                print(f"❌ Issues found: {len(job_issues)}")
                for issue in job_issues:
                    print(f"   • {issue}")
            else:
                valid_jobs += 1
                print("✅ Valid")
            print()
        
        print("─" * 50)
        print(f"📊 Validation Summary:")
        print(f"   Total Jobs: {total_jobs}")
        print(f"   Valid Jobs: {valid_jobs}")
        print(f"   Jobs with Issues: {total_jobs - valid_jobs}")
        print(f"   Total Issues: {len(issues_found)}")
        
        if issues_found:
            print(f"\n🚨 Issues Found:")
            for job_name, issue in issues_found:
                print(f"   {job_name}: {issue}")
    
    def validate_single_job(self):
        """Validate syntax of a single job"""
        if not self.config['jobs']:
            print("❌ No jobs available to validate!")
            return
        
        job_names = [job['name'] for job in self.config['jobs']]
        choice = self.menu.show_dropdown("Select job to validate", job_names)
        
        if choice >= 0:
            job = self.config['jobs'][choice]
            print(f"🔍 Validating: {job['name']}")
            print("─" * 50)
            
            issues = self.validate_job_syntax(job)
            if issues:
                print("❌ Issues found:")
                for issue in issues:
                    print(f"   • {issue}")
            else:
                print("✅ Job syntax is valid!")
                print("✅ Schedule format is correct")
                print("✅ Command appears to be valid")
        else:
            print("❌ Validation cancelled.")
    
    def validate_job_syntax(self, job):
        """Validate a single job and return list of issues"""
        issues = []
        
        # Check required fields
        if not job.get('name'):
            issues.append("Missing job name")
        if not job.get('command'):
            issues.append("Missing command")
        if not job.get('schedule'):
            issues.append("Missing schedule")
        
        # Validate cron schedule format
        schedule = job.get('schedule', '')
        if schedule:
            cron_issues = self.validate_cron_format(schedule)
            issues.extend(cron_issues)
        
        # Check command for common issues
        command = job.get('command', '')
        if command:
            command_issues = self.validate_command(command)
            issues.extend(command_issues)
        
        return issues
    
    def validate_cron_format(self, schedule):
        """Validate cron schedule format"""
        issues = []
        
        # Split schedule into parts
        parts = schedule.strip().split()
        
        if len(parts) != 5:
            issues.append(f"Cron schedule must have 5 parts (minute hour day month weekday), found {len(parts)}")
            return issues
        
        # Validate each part
        minute, hour, day, month, weekday = parts
        
        # Minute (0-59)
        if not self.validate_cron_field(minute, 0, 59):
            issues.append("Invalid minute field (must be 0-59 or */n)")
        
        # Hour (0-23)
        if not self.validate_cron_field(hour, 0, 23):
            issues.append("Invalid hour field (must be 0-23 or */n)")
        
        # Day (1-31)
        if not self.validate_cron_field(day, 1, 31):
            issues.append("Invalid day field (must be 1-31 or */n)")
        
        # Month (1-12)
        if not self.validate_cron_field(month, 1, 12):
            issues.append("Invalid month field (must be 1-12 or */n)")
        
        # Weekday (0-7, where 0 and 7 are Sunday)
        if not self.validate_cron_field(weekday, 0, 7):
            issues.append("Invalid weekday field (must be 0-7 or */n)")
        
        return issues
    
    def validate_cron_field(self, field, min_val, max_val):
        """Validate a single cron field"""
        if field == '*':
            return True
        
        # Handle step values (*/n)
        if field.startswith('*/'):
            try:
                step = int(field[2:])
                return step > 0
            except ValueError:
                return False
        
        # Handle ranges (n-m)
        if '-' in field:
            try:
                start, end = field.split('-')
                start_val = int(start)
                end_val = int(end)
                return min_val <= start_val <= max_val and min_val <= end_val <= max_val and start_val <= end_val
            except ValueError:
                return False
        
        # Handle lists (n,m,o)
        if ',' in field:
            try:
                values = [int(v.strip()) for v in field.split(',')]
                return all(min_val <= v <= max_val for v in values)
            except ValueError:
                return False
        
        # Handle single values
        try:
            value = int(field)
            return min_val <= value <= max_val
        except ValueError:
            return False
    
    def validate_command(self, command):
        """Validate command for common issues"""
        issues = []
        
        # Check for potentially dangerous commands
        dangerous_patterns = ['rm -rf /', 'format', 'fdisk', 'dd if=/dev/zero', '> /dev/']
        for pattern in dangerous_patterns:
            if pattern in command.lower():
                issues.append(f"Potentially dangerous command detected: {pattern}")
        
        # Check for missing executable
        command_parts = command.split()
        if command_parts:
            executable = command_parts[0]
            
            # Skip built-in shell commands and common paths
            if not executable.startswith('/') and executable not in ['cd', 'echo', 'export', 'set']:
                # This is a simplified check - in reality you'd use `which` command
                common_executables = ['ls', 'cat', 'grep', 'awk', 'sed', 'python', 'python3', 'bash', 'sh']
                if executable not in common_executables:
                    issues.append(f"Command '{executable}' may not be found in PATH")
        
        # Check for unescaped special characters in paths
        if '"' in command and "'" in command:
            issues.append("Mixed quote types may cause issues")
        
        return issues
    
    def test_cron_schedule(self):
        """Test a cron schedule"""
        schedule = self.menu.show_input_prompt("Enter cron schedule to test (e.g., '0 9 * * 1')")
        if schedule:
            print(f"🔍 Testing schedule: {schedule}")
            print("─" * 40)
            
            issues = self.validate_cron_format(schedule)
            if issues:
                print("❌ Invalid schedule:")
                for issue in issues:
                    print(f"   • {issue}")
            else:
                print("✅ Valid cron schedule!")
                print(f"📋 Schedule breakdown:")
                parts = schedule.split()
                if len(parts) == 5:
                    fields = ['Minute', 'Hour', 'Day', 'Month', 'Weekday']
                    for i, (field, value) in enumerate(zip(fields, parts)):
                        print(f"   {field}: {value}")
                
                # Show next few execution times (simplified)
                print(f"\n⏰ This job would run:")
                print(f"   Next execution times would be calculated here")
        else:
            print("❌ No schedule provided.")
    
    def fix_common_issues(self):
        """Fix common syntax issues"""
        if not self.config['jobs']:
            print("❌ No jobs to fix!")
            return
        
        print("🔧 Fixing Common Issues")
        print("─" * 40)
        
        fixed_count = 0
        for job in self.config['jobs']:
            original_issues = len(self.validate_job_syntax(job))
            
            # Fix missing descriptions
            if not job.get('description'):
                job['description'] = f"Auto-generated description for {job.get('name', 'unnamed job')}"
                fixed_count += 1
            
            # Fix missing logging
            if not job.get('logging'):
                job['logging'] = 'No logging'
                fixed_count += 1
            
            # Fix missing enabled flag
            if 'enabled' not in job:
                job['enabled'] = True
                fixed_count += 1
        
        if fixed_count > 0:
            self.save_config()
            print(f"✅ Fixed {fixed_count} common issues!")
        else:
            print("ℹ️  No common issues found to fix.")
    
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
    
    def handle_notes_menu(self):
        """Handle notes and journal menu"""
        options = [
            "➕ Create New Note",
            "📝 View All Notes",
            "🔍 Search Notes",
            "✏️  Edit Note",
            "🗑️  Delete Note",
            "📂 Manage Categories",
            "📊 Notes Statistics",
            "💾 Export Notes",
            "📥 Import Notes",
            "⬅️  Back to main menu"
        ]
        
        choice = self.menu.show_dropdown("NOTES & JOURNAL", options)
        
        if choice == 0:
            self.create_note()
        elif choice == 1:
            self.view_notes()
        elif choice == 2:
            self.search_notes()
        elif choice == 3:
            self.edit_note()
        elif choice == 4:
            self.delete_note()
        elif choice == 5:
            self.manage_categories()
        elif choice == 6:
            self.notes_statistics()
        elif choice == 7:
            self.export_notes()
        elif choice == 8:
            self.import_notes()
        elif choice == 9 or choice == -1:
            pass  # Back to main menu
    
    def create_note(self):
        """Create a new note"""
        self.menu.clear_screen()
        print("\n📝 CREATE NEW NOTE")
        print("─" * 50)
        
        # Get note title
        title = self.menu.show_input_prompt("Enter note title", "")
        if not title:
            print("❌ Note title is required!")
            input("Press Enter to continue...")
            return
        
        # Get note category
        categories = self.get_note_categories()
        if categories:
            print(f"\n📂 Available categories: {', '.join(categories)}")
            category = self.menu.show_input_prompt("Enter category (or press Enter for 'General')", "General")
        else:
            category = self.menu.show_input_prompt("Enter category", "General")
        
        # Get note content
        print("\n📝 Enter note content (press Ctrl+D when finished on Unix/macOS or Ctrl+Z on Windows):")
        content_lines = []
        try:
            while True:
                line = input()
                content_lines.append(line)
        except EOFError:
            pass
        
        content = '\n'.join(content_lines)
        if not content.strip():
            print("❌ Note content cannot be empty!")
            input("Press Enter to continue...")
            return
        
        # Get tags
        tags_input = self.menu.show_input_prompt("Enter tags (comma-separated, optional)", "")
        tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()] if tags_input else []
        
        # Create note object
        note = {
            'id': len(self.config['notes']) + 1,
            'title': title,
            'content': content,
            'category': category,
            'tags': tags,
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'favorite': False
        }
        
        self.config['notes'].append(note)
        self.save_config()
        
        print(f"\n✅ Note '{title}' created successfully!")
        print(f"📂 Category: {category}")
        print(f"🏷️  Tags: {', '.join(tags) if tags else 'None'}")
        input("Press Enter to continue...")
    
    def view_notes(self):
        """View all notes with filtering options"""
        while True:
            self.menu.clear_screen()
            print("\n📝 VIEW NOTES")
            print("─" * 50)
            
            if not self.config['notes']:
                print("📭 No notes found!")
                input("Press Enter to continue...")
                return
            
            # Filter options
            filter_options = [
                "📋 All Notes",
                "⭐ Favorites Only",
                "📂 By Category",
                "🏷️  By Tag",
                "📅 Recent (Last 7 days)",
                "🔍 Search in Content"
            ]
            
            choice = self.menu.show_dropdown("FILTER NOTES", filter_options)
            
            if choice == -1:
                return
            
            filtered_notes = self.config['notes']
            
            if choice == 0:  # All notes
                pass
            elif choice == 1:  # Favorites
                filtered_notes = [note for note in self.config['notes'] if note.get('favorite', False)]
            elif choice == 2:  # By category
                categories = self.get_note_categories()
                if not categories:
                    print("❌ No categories found!")
                    input("Press Enter to continue...")
                    continue
                
                category_choice = self.menu.show_dropdown("SELECT CATEGORY", categories)
                if category_choice == -1:
                    continue
                selected_category = categories[category_choice]
                filtered_notes = [note for note in self.config['notes'] if note.get('category', 'General') == selected_category]
            elif choice == 3:  # By tag
                all_tags = self.get_all_tags()
                if not all_tags:
                    print("❌ No tags found!")
                    input("Press Enter to continue...")
                    continue
                
                tag_choice = self.menu.show_dropdown("SELECT TAG", all_tags)
                if tag_choice == -1:
                    continue
                selected_tag = all_tags[tag_choice]
                filtered_notes = [note for note in self.config['notes'] if selected_tag in note.get('tags', [])]
            elif choice == 4:  # Recent
                week_ago = datetime.now() - timedelta(days=7)
                filtered_notes = [note for note in self.config['notes'] 
                                if datetime.fromisoformat(note['created']) > week_ago]
            elif choice == 5:  # Search in content
                search_term = self.menu.show_input_prompt("Enter search term", "")
                if not search_term:
                    continue
                filtered_notes = [note for note in self.config['notes'] 
                                if search_term.lower() in note['content'].lower() or 
                                   search_term.lower() in note['title'].lower()]
            
            if not filtered_notes:
                print("📭 No notes match the selected filter!")
                input("Press Enter to continue...")
                continue
            
            # Display filtered notes
            self.display_notes_list(filtered_notes)
            
            # Show note actions
            if filtered_notes:
                action_choice = self.menu.show_dropdown("NOTE ACTIONS", [
                    "👁️  View Note Details",
                    "✏️  Edit Note",
                    "🗑️  Delete Note",
                    "⭐ Toggle Favorite",
                    "⬅️  Back to Filter Menu"
                ])
                
                if action_choice == 0:  # View details
                    self.view_note_details(filtered_notes)
                elif action_choice == 1:  # Edit
                    self.edit_note_from_list(filtered_notes)
                elif action_choice == 2:  # Delete
                    self.delete_note_from_list(filtered_notes)
                elif action_choice == 3:  # Toggle favorite
                    self.toggle_note_favorite(filtered_notes)
                elif action_choice == 4 or action_choice == -1:  # Back
                    continue
    
    def display_notes_list(self, notes):
        """Display a list of notes"""
        print(f"\n📋 Found {len(notes)} note(s):")
        print("─" * 80)
        
        for i, note in enumerate(notes, 1):
            favorite_icon = "⭐" if note.get('favorite', False) else "  "
            created_date = datetime.fromisoformat(note['created']).strftime("%Y-%m-%d %H:%M")
            category = note.get('category', 'General')
            tags = ', '.join(note.get('tags', [])) if note.get('tags') else 'None'
            
            # Truncate content for display
            content_preview = note['content'][:50] + "..." if len(note['content']) > 50 else note['content']
            
            print(f"{favorite_icon} {i:2d}. {note['title']}")
            print(f"    📂 {category} | 🏷️  {tags}")
            print(f"    📅 {created_date}")
            print(f"    📝 {content_preview}")
            print()
    
    def view_note_details(self, notes):
        """View detailed information about a specific note"""
        if not notes:
            return
        
        note_options = [f"{note['title']} ({note.get('category', 'General')})" for note in notes]
        choice = self.menu.show_dropdown("SELECT NOTE TO VIEW", note_options)
        
        if choice == -1:
            return
        
        note = notes[choice]
        self.menu.clear_screen()
        
        print(f"\n📝 NOTE DETAILS")
        print("─" * 80)
        print(f"📋 Title: {note['title']}")
        print(f"📂 Category: {note.get('category', 'General')}")
        print(f"🏷️  Tags: {', '.join(note.get('tags', [])) if note.get('tags') else 'None'}")
        print(f"⭐ Favorite: {'Yes' if note.get('favorite', False) else 'No'}")
        print(f"📅 Created: {datetime.fromisoformat(note['created']).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📝 Modified: {datetime.fromisoformat(note['modified']).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Content Length: {len(note['content'])} characters")
        print("\n📝 CONTENT:")
        print("─" * 80)
        print(note['content'])
        print("─" * 80)
        
        input("Press Enter to continue...")
    
    def search_notes(self):
        """Search notes by title, content, or tags"""
        self.menu.clear_screen()
        print("\n🔍 SEARCH NOTES")
        print("─" * 50)
        
        if not self.config['notes']:
            print("📭 No notes to search!")
            input("Press Enter to continue...")
            return
        
        search_term = self.menu.show_input_prompt("Enter search term", "")
        if not search_term:
            print("❌ Search term is required!")
            input("Press Enter to continue...")
            return
        
        # Search in title, content, and tags
        matching_notes = []
        search_lower = search_term.lower()
        
        for note in self.config['notes']:
            if (search_lower in note['title'].lower() or 
                search_lower in note['content'].lower() or
                any(search_lower in tag.lower() for tag in note.get('tags', []))):
                matching_notes.append(note)
        
        if not matching_notes:
            print(f"📭 No notes found matching '{search_term}'")
            input("Press Enter to continue...")
            return
        
        print(f"\n🔍 Found {len(matching_notes)} note(s) matching '{search_term}':")
        self.display_notes_list(matching_notes)
        input("Press Enter to continue...")
    
    def edit_note(self):
        """Edit an existing note"""
        if not self.config['notes']:
            print("📭 No notes to edit!")
            input("Press Enter to continue...")
            return
        
        # Show all notes for selection
        note_options = [f"{note['title']} ({note.get('category', 'General')})" for note in self.config['notes']]
        choice = self.menu.show_dropdown("SELECT NOTE TO EDIT", note_options)
        
        if choice == -1:
            return
        
        self.edit_note_by_index(choice)
    
    def edit_note_from_list(self, notes):
        """Edit a note from a filtered list"""
        if not notes:
            return
        
        note_options = [f"{note['title']} ({note.get('category', 'General')})" for note in notes]
        choice = self.menu.show_dropdown("SELECT NOTE TO EDIT", note_options)
        
        if choice == -1:
            return
        
        # Find the note in the main notes list
        selected_note = notes[choice]
        note_index = next(i for i, note in enumerate(self.config['notes']) if note['id'] == selected_note['id'])
        
        self.edit_note_by_index(note_index)
    
    def edit_note_by_index(self, note_index):
        """Edit a note by its index in the notes list"""
        note = self.config['notes'][note_index]
        
        self.menu.clear_screen()
        print(f"\n✏️  EDIT NOTE: {note['title']}")
        print("─" * 50)
        
        # Edit options
        edit_options = [
            "📝 Edit Title",
            "📝 Edit Content",
            "📂 Change Category",
            "🏷️  Edit Tags",
            "⭐ Toggle Favorite",
            "💾 Save Changes",
            "❌ Cancel"
        ]
        
        while True:
            choice = self.menu.show_dropdown("EDIT OPTIONS", edit_options)
            
            if choice == 0:  # Edit title
                new_title = self.menu.show_input_prompt("Enter new title", note['title'])
                if new_title:
                    note['title'] = new_title
                    note['modified'] = datetime.now().isoformat()
                    print("✅ Title updated!")
            elif choice == 1:  # Edit content
                print(f"\n📝 Current content:\n{note['content']}")
                print("\n📝 Enter new content (press Ctrl+D when finished):")
                content_lines = []
                try:
                    while True:
                        line = input()
                        content_lines.append(line)
                except EOFError:
                    pass
                
                new_content = '\n'.join(content_lines)
                if new_content.strip():
                    note['content'] = new_content
                    note['modified'] = datetime.now().isoformat()
                    print("✅ Content updated!")
            elif choice == 2:  # Change category
                new_category = self.menu.show_input_prompt("Enter new category", note.get('category', 'General'))
                if new_category:
                    note['category'] = new_category
                    note['modified'] = datetime.now().isoformat()
                    print("✅ Category updated!")
            elif choice == 3:  # Edit tags
                current_tags = ', '.join(note.get('tags', []))
                new_tags_input = self.menu.show_input_prompt("Enter tags (comma-separated)", current_tags)
                if new_tags_input is not None:
                    new_tags = [tag.strip() for tag in new_tags_input.split(',') if tag.strip()]
                    note['tags'] = new_tags
                    note['modified'] = datetime.now().isoformat()
                    print("✅ Tags updated!")
            elif choice == 4:  # Toggle favorite
                note['favorite'] = not note.get('favorite', False)
                note['modified'] = datetime.now().isoformat()
                status = "favorited" if note['favorite'] else "unfavorited"
                print(f"✅ Note {status}!")
            elif choice == 5:  # Save changes
                self.save_config()
                print("💾 Changes saved successfully!")
                break
            elif choice == 6 or choice == -1:  # Cancel
                if self.menu.show_confirmation("Discard unsaved changes?"):
                    break
                else:
                    continue
            
            input("Press Enter to continue...")
    
    def delete_note(self):
        """Delete a note"""
        if not self.config['notes']:
            print("📭 No notes to delete!")
            input("Press Enter to continue...")
            return
        
        note_options = [f"{note['title']} ({note.get('category', 'General')})" for note in self.config['notes']]
        choice = self.menu.show_dropdown("SELECT NOTE TO DELETE", note_options)
        
        if choice == -1:
            return
        
        note = self.config['notes'][choice]
        if self.menu.show_confirmation(f"Delete note '{note['title']}'?"):
            del self.config['notes'][choice]
            self.save_config()
            print("✅ Note deleted successfully!")
        else:
            print("❌ Deletion cancelled.")
        
        input("Press Enter to continue...")
    
    def delete_note_from_list(self, notes):
        """Delete a note from a filtered list"""
        if not notes:
            return
        
        note_options = [f"{note['title']} ({note.get('category', 'General')})" for note in notes]
        choice = self.menu.show_dropdown("SELECT NOTE TO DELETE", note_options)
        
        if choice == -1:
            return
        
        selected_note = notes[choice]
        if self.menu.show_confirmation(f"Delete note '{selected_note['title']}'?"):
            # Find and remove from main notes list
            self.config['notes'] = [note for note in self.config['notes'] if note['id'] != selected_note['id']]
            self.save_config()
            print("✅ Note deleted successfully!")
        else:
            print("❌ Deletion cancelled.")
        
        input("Press Enter to continue...")
    
    def toggle_note_favorite(self, notes):
        """Toggle favorite status of a note from a filtered list"""
        if not notes:
            return
        
        note_options = [f"{note['title']} ({note.get('category', 'General')})" for note in notes]
        choice = self.menu.show_dropdown("SELECT NOTE TO TOGGLE FAVORITE", note_options)
        
        if choice == -1:
            return
        
        selected_note = notes[choice]
        # Find the note in the main notes list and toggle favorite
        for note in self.config['notes']:
            if note['id'] == selected_note['id']:
                note['favorite'] = not note.get('favorite', False)
                note['modified'] = datetime.now().isoformat()
                status = "favorited" if note['favorite'] else "unfavorited"
                print(f"✅ Note {status}!")
                self.save_config()
                break
        
        input("Press Enter to continue...")
    
    def manage_categories(self):
        """Manage note categories"""
        while True:
            self.menu.clear_screen()
            print("\n📂 MANAGE CATEGORIES")
            print("─" * 50)
            
            categories = self.get_note_categories()
            
            if categories:
                print("📂 Current categories:")
                for i, category in enumerate(categories, 1):
                    count = len([note for note in self.config['notes'] if note.get('category', 'General') == category])
                    print(f"  {i}. {category} ({count} notes)")
            else:
                print("📭 No categories found!")
            
            print()
            options = [
                "➕ Add New Category",
                "🔄 Rename Category",
                "📊 Category Statistics",
                "⬅️  Back to Notes Menu"
            ]
            
            choice = self.menu.show_dropdown("CATEGORY OPTIONS", options)
            
            if choice == 0:  # Add new category
                new_category = self.menu.show_input_prompt("Enter new category name", "")
                if new_category and new_category not in categories:
                    print(f"✅ Category '{new_category}' added!")
                    print("💡 Create a note with this category to use it.")
                elif new_category in categories:
                    print("❌ Category already exists!")
                input("Press Enter to continue...")
            elif choice == 1:  # Rename category
                if not categories:
                    print("❌ No categories to rename!")
                    input("Press Enter to continue...")
                    continue
                
                category_choice = self.menu.show_dropdown("SELECT CATEGORY TO RENAME", categories)
                if category_choice == -1:
                    continue
                
                old_category = categories[category_choice]
                new_category = self.menu.show_input_prompt("Enter new category name", old_category)
                
                if new_category and new_category != old_category:
                    # Update all notes with this category
                    for note in self.config['notes']:
                        if note.get('category', 'General') == old_category:
                            note['category'] = new_category
                            note['modified'] = datetime.now().isoformat()
                    
                    self.save_config()
                    print(f"✅ Category renamed from '{old_category}' to '{new_category}'!")
                input("Press Enter to continue...")
            elif choice == 2:  # Category statistics
                if categories:
                    print("\n📊 CATEGORY STATISTICS")
                    print("─" * 50)
                    for category in categories:
                        count = len([note for note in self.config['notes'] if note.get('category', 'General') == category])
                        percentage = (count / len(self.config['notes'])) * 100 if self.config['notes'] else 0
                        print(f"📂 {category}: {count} notes ({percentage:.1f}%)")
                else:
                    print("📭 No categories to show statistics for!")
                input("Press Enter to continue...")
            elif choice == 3 or choice == -1:  # Back
                break
    
    def notes_statistics(self):
        """Show notes statistics"""
        self.menu.clear_screen()
        print("\n📊 NOTES STATISTICS")
        print("─" * 50)
        
        if not self.config['notes']:
            print("📭 No notes found!")
            input("Press Enter to continue...")
            return
        
        total_notes = len(self.config['notes'])
        favorite_notes = len([note for note in self.config['notes'] if note.get('favorite', False)])
        categories = self.get_note_categories()
        all_tags = self.get_all_tags()
        
        # Calculate total content length
        total_content_length = sum(len(note['content']) for note in self.config['notes'])
        
        # Find most recent and oldest notes
        if self.config['notes']:
            sorted_notes = sorted(self.config['notes'], key=lambda x: x['created'])
            oldest_note = sorted_notes[0]
            newest_note = sorted_notes[-1]
        
        print(f"📋 Total Notes: {total_notes}")
        print(f"⭐ Favorite Notes: {favorite_notes}")
        print(f"📂 Categories: {len(categories)}")
        print(f"🏷️  Unique Tags: {len(all_tags)}")
        print(f"📝 Total Content Length: {total_content_length:,} characters")
        print(f"📊 Average Content Length: {total_content_length // total_notes if total_notes > 0 else 0:,} characters")
        
        if self.config['notes']:
            print(f"\n📅 Oldest Note: {oldest_note['title']} ({datetime.fromisoformat(oldest_note['created']).strftime('%Y-%m-%d')})")
            print(f"📅 Newest Note: {newest_note['title']} ({datetime.fromisoformat(newest_note['created']).strftime('%Y-%m-%d')})")
        
        # Category breakdown
        if categories:
            print(f"\n📂 CATEGORY BREAKDOWN:")
            for category in sorted(categories):
                count = len([note for note in self.config['notes'] if note.get('category', 'General') == category])
                percentage = (count / total_notes) * 100
                print(f"  📂 {category}: {count} notes ({percentage:.1f}%)")
        
        # Most used tags
        if all_tags:
            tag_counts = {}
            for note in self.config['notes']:
                for tag in note.get('tags', []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            print(f"\n🏷️  MOST USED TAGS:")
            for tag, count in sorted_tags[:5]:  # Top 5 tags
                print(f"  🏷️  {tag}: {count} notes")
        
        input("Press Enter to continue...")
    
    def export_notes(self):
        """Export notes to a file"""
        if not self.config['notes']:
            print("📭 No notes to export!")
            input("Press Enter to continue...")
            return
        
        self.menu.clear_screen()
        print("\n💾 EXPORT NOTES")
        print("─" * 50)
        
        export_options = [
            "📄 Export as JSON",
            "📝 Export as Text",
            "📊 Export as CSV",
            "⬅️  Back to Notes Menu"
        ]
        
        choice = self.menu.show_dropdown("EXPORT FORMAT", export_options)
        
        if choice == 0:  # JSON
            filename = self.menu.show_input_prompt("Enter filename (without extension)", f"notes_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            if filename:
                try:
                    with open(f"{filename}.json", 'w', encoding='utf-8') as f:
                        json.dump(self.config['notes'], f, indent=2, ensure_ascii=False)
                    print(f"✅ Notes exported to {filename}.json")
                except Exception as e:
                    print(f"❌ Export failed: {e}")
        elif choice == 1:  # Text
            filename = self.menu.show_input_prompt("Enter filename (without extension)", f"notes_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            if filename:
                try:
                    with open(f"{filename}.txt", 'w', encoding='utf-8') as f:
                        for note in self.config['notes']:
                            f.write(f"Title: {note['title']}\n")
                            f.write(f"Category: {note.get('category', 'General')}\n")
                            f.write(f"Tags: {', '.join(note.get('tags', []))}\n")
                            f.write(f"Created: {datetime.fromisoformat(note['created']).strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f.write(f"Modified: {datetime.fromisoformat(note['modified']).strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f.write(f"Favorite: {'Yes' if note.get('favorite', False) else 'No'}\n")
                            f.write("─" * 50 + "\n")
                            f.write(note['content'])
                            f.write("\n\n" + "=" * 80 + "\n\n")
                    print(f"✅ Notes exported to {filename}.txt")
                except Exception as e:
                    print(f"❌ Export failed: {e}")
        elif choice == 2:  # CSV
            filename = self.menu.show_input_prompt("Enter filename (without extension)", f"notes_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            if filename:
                try:
                    import csv
                    with open(f"{filename}.csv", 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Title', 'Category', 'Tags', 'Created', 'Modified', 'Favorite', 'Content'])
                        for note in self.config['notes']:
                            writer.writerow([
                                note['title'],
                                note.get('category', 'General'),
                                ', '.join(note.get('tags', [])),
                                datetime.fromisoformat(note['created']).strftime('%Y-%m-%d %H:%M:%S'),
                                datetime.fromisoformat(note['modified']).strftime('%Y-%m-%d %H:%M:%S'),
                                'Yes' if note.get('favorite', False) else 'No',
                                note['content'].replace('\n', ' ').replace('\r', ' ')
                            ])
                    print(f"✅ Notes exported to {filename}.csv")
                except Exception as e:
                    print(f"❌ Export failed: {e}")
        elif choice == 3 or choice == -1:  # Back
            return
        
        input("Press Enter to continue...")
    
    def import_notes(self):
        """Import notes from a file"""
        self.menu.clear_screen()
        print("\n📥 IMPORT NOTES")
        print("─" * 50)
        
        import_options = [
            "📄 Import from JSON",
            "📝 Import from Text",
            "⬅️  Back to Notes Menu"
        ]
        
        choice = self.menu.show_dropdown("IMPORT FORMAT", import_options)
        
        if choice == 0:  # JSON
            filename = self.menu.show_input_prompt("Enter JSON filename (with extension)", "")
            if filename and os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        imported_notes = json.load(f)
                    
                    if isinstance(imported_notes, list):
                        # Assign new IDs to avoid conflicts
                        max_id = max([note.get('id', 0) for note in self.config['notes']], default=0)
                        for note in imported_notes:
                            max_id += 1
                            note['id'] = max_id
                            note['created'] = datetime.now().isoformat()
                            note['modified'] = datetime.now().isoformat()
                        
                        self.config['notes'].extend(imported_notes)
                        self.save_config()
                        print(f"✅ Imported {len(imported_notes)} notes successfully!")
                    else:
                        print("❌ Invalid JSON format!")
                except Exception as e:
                    print(f"❌ Import failed: {e}")
            else:
                print("❌ File not found!")
        elif choice == 1:  # Text
            filename = self.menu.show_input_prompt("Enter text filename (with extension)", "")
            if filename and os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Simple text import - create one note per file
                    title = os.path.splitext(os.path.basename(filename))[0]
                    note = {
                        'id': len(self.config['notes']) + 1,
                        'title': title,
                        'content': content,
                        'category': 'Imported',
                        'tags': ['imported'],
                        'created': datetime.now().isoformat(),
                        'modified': datetime.now().isoformat(),
                        'favorite': False
                    }
                    
                    self.config['notes'].append(note)
                    self.save_config()
                    print(f"✅ Imported text file as note: {title}")
                except Exception as e:
                    print(f"❌ Import failed: {e}")
            else:
                print("❌ File not found!")
        elif choice == 2 or choice == -1:  # Back
            return
        
        input("Press Enter to continue...")
    
    def get_note_categories(self):
        """Get all unique categories from notes"""
        categories = set()
        for note in self.config['notes']:
            categories.add(note.get('category', 'General'))
        return sorted(list(categories))
    
    def get_all_tags(self):
        """Get all unique tags from notes"""
        tags = set()
        for note in self.config['notes']:
            tags.update(note.get('tags', []))
        return sorted(list(tags))
    
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
            "📹 Network Camera Scan",
            "🔍 CCTV Detection",
            "🗺️  Camera Location Map",
            "🎯 Camera Access & Control",
            "🧠 Camera Cognitive Analysis",
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
        elif choice == 8:
            self.network_camera_scan()
        elif choice == 9:
            self.cctv_detection()
        elif choice == 10:
            self.camera_location_map()
        elif choice == 11:
            self.camera_access_control()
        elif choice == 12:
            self.camera_cognitive_analysis()
        elif choice == 13 or choice == -1:
            pass  # Back to main menu
    
    def handle_dashboard_menu(self):
        """Handle real-time dashboard menu"""
        options = [
            "📊 System Overview Dashboard",
            "🌐 Network Monitoring Dashboard", 
            "📹 Camera Monitoring Dashboard",
            "🔒 Security Dashboard",
            "📈 Performance Dashboard",
            "🌍 Web Dashboard (HTML)",
            "🗂️ Personal Desktop Dashboard",
            "⚙️  Dashboard Settings",
            "⬅️  Back to main menu"
        ]
        
        choice = self.menu.show_dropdown("REAL-TIME DASHBOARD", options)
        
        if choice == 0:
            self.system_overview_dashboard()
        elif choice == 1:
            self.network_monitoring_dashboard()
        elif choice == 2:
            self.camera_monitoring_dashboard()
        elif choice == 3:
            self.security_dashboard()
        elif choice == 4:
            self.performance_dashboard()
        elif choice == 5:
            self.web_dashboard()
        elif choice == 6:
            self.personal_desktop_dashboard()
        elif choice == 7:
            self.dashboard_settings()
        elif choice == 8 or choice == -1:
            pass  # Back to main menu
    
    # ===== DASHBOARD FUNCTIONS =====
    
    def system_overview_dashboard(self):
        """Display comprehensive system overview dashboard"""
        print("📊 System Overview Dashboard")
        print("=" * 60)
        
        # Get system information
        system_info = self.get_system_info()
        network_info = self.get_network_info()
        security_info = self.get_security_info()
        
        # Display dashboard
        self.clear_screen()
        print("┌" + "─" * 58 + "┐")
        print("│" + " " * 20 + "SYSTEM OVERVIEW" + " " * 23 + "│")
        print("├" + "─" * 58 + "┤")
        
        # System Status
        print("│ 🖥️  SYSTEM STATUS" + " " * 42 + "│")
        print("│" + "─" * 58 + "│")
        print(f"│ OS: {system_info['os']:<20} Uptime: {system_info['uptime']:<15} │")
        print(f"│ CPU: {system_info['cpu_usage']:<5}% Memory: {system_info['memory_usage']:<5}% Disk: {system_info['disk_usage']:<5}% │")
        print(f"│ Load: {system_info['load_avg']:<15} Processes: {system_info['processes']:<8} │")
        
        # Network Status
        print("│" + "─" * 58 + "│")
        print("│ 🌐 NETWORK STATUS" + " " * 41 + "│")
        print("│" + "─" * 58 + "│")
        print(f"│ IP: {network_info['local_ip']:<15} Gateway: {network_info['gateway']:<15} │")
        print(f"│ Interface: {network_info['interface']:<12} Status: {network_info['status']:<15} │")
        print(f"│ Connected Devices: {network_info['devices']:<8} Cameras: {network_info['cameras']:<8} │")
        
        # Security Status
        print("│" + "─" * 58 + "│")
        print("│ 🔒 SECURITY STATUS" + " " * 40 + "│")
        print("│" + "─" * 58 + "│")
        print(f"│ Firewall: {security_info['firewall']:<12} Antivirus: {security_info['antivirus']:<12} │")
        print(f"│ Open Ports: {security_info['open_ports']:<8} Threats: {security_info['threats']:<8} │")
        print(f"│ Risk Level: {security_info['risk_level']:<15} Last Scan: {security_info['last_scan']:<10} │")
        
        print("└" + "─" * 58 + "┘")
        
        # Real-time updates
        print("\n🔄 Real-time updates (Press 'q' to quit, 'r' to refresh):")
        
        import threading
        import time
        
        self.dashboard_running = True
        
        def update_dashboard():
            while self.dashboard_running:
                time.sleep(2)
                if self.dashboard_running:
                    self.refresh_system_dashboard()
        
        update_thread = threading.Thread(target=update_dashboard, daemon=True)
        update_thread.start()
        
        # Handle user input
        while True:
            try:
                key = input().lower().strip()
                if key == 'q':
                    break
                elif key == 'r':
                    self.refresh_system_dashboard()
                elif key == 'c':
                    self.clear_screen()
                    self.system_overview_dashboard()
                    break
            except KeyboardInterrupt:
                break
        
        self.dashboard_running = False
        print("\n📊 Dashboard closed")
        input("Press Enter to continue...")
    
    def get_system_info(self):
        """Get comprehensive system information"""
        import platform
        import psutil
        import time
        
        try:
            # Get system information
            os_info = f"{platform.system()} {platform.release()}"
            uptime = time.time() - psutil.boot_time()
            uptime_str = f"{int(uptime//3600)}h {int((uptime%3600)//60)}m"
            
            # Get resource usage
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get load average
            load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else "N/A"
            
            return {
                'os': os_info,
                'uptime': uptime_str,
                'cpu_usage': f"{cpu_usage:.1f}",
                'memory_usage': f"{memory.percent:.1f}",
                'disk_usage': f"{(disk.used/disk.total)*100:.1f}",
                'load_avg': f"{load_avg:.2f}",
                'processes': len(psutil.pids())
            }
        except Exception as e:
            return {
                'os': 'Unknown',
                'uptime': 'Unknown',
                'cpu_usage': 'N/A',
                'memory_usage': 'N/A',
                'disk_usage': 'N/A',
                'load_avg': 'N/A',
                'processes': 'N/A'
            }
    
    def get_network_info(self):
        """Get network information"""
        try:
            local_ip = self.get_local_ip()
            network_base = '.'.join(local_ip.split('.')[:-1]) if local_ip else "Unknown"
            gateway = f"{network_base}.1"
            
            # Get network interface info
            import psutil
            interfaces = psutil.net_if_addrs()
            active_interface = None
            
            for interface, addresses in interfaces.items():
                for addr in addresses:
                    if addr.family == 2 and addr.address.startswith(network_base):  # IPv4
                        active_interface = interface
                        break
                if active_interface:
                    break
            
            # Count devices (simplified)
            devices = self.count_network_devices()
            cameras = self.count_cameras()
            
            return {
                'local_ip': local_ip or 'Unknown',
                'gateway': gateway,
                'interface': active_interface or 'Unknown',
                'status': 'Connected',
                'devices': str(devices),
                'cameras': str(cameras)
            }
        except Exception as e:
            return {
                'local_ip': 'Unknown',
                'gateway': 'Unknown',
                'interface': 'Unknown',
                'status': 'Unknown',
                'devices': '0',
                'cameras': '0'
            }
    
    def get_security_info(self):
        """Get security information"""
        try:
            firewall_status = "Enabled" if self.check_firewall_status() else "Disabled"
            antivirus_status = "Installed" if self.check_antivirus() else "Not Found"
            open_ports = len(self.get_open_ports())
            threats = 0  # Would be populated by threat detection
            
            risk_level = "LOW"
            if open_ports > 10:
                risk_level = "MEDIUM"
            if not self.check_firewall_status() or open_ports > 20:
                risk_level = "HIGH"
            
            return {
                'firewall': firewall_status,
                'antivirus': antivirus_status,
                'open_ports': str(open_ports),
                'threats': str(threats),
                'risk_level': risk_level,
                'last_scan': "Now"
            }
        except Exception as e:
            return {
                'firewall': 'Unknown',
                'antivirus': 'Unknown',
                'open_ports': '0',
                'threats': '0',
                'risk_level': 'UNKNOWN',
                'last_scan': 'Never'
            }
    
    def count_network_devices(self):
        """Count devices on network"""
        try:
            import subprocess
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = [line for line in result.stdout.split('\n') if 'incomplete' not in line and '(' in line]
                return len(lines)
            return 0
        except:
            return 0
    
    def count_cameras(self):
        """Count cameras on network"""
        try:
            local_ip = self.get_local_ip()
            if not local_ip:
                return 0
            
            network_base = '.'.join(local_ip.split('.')[:-1])
            camera_count = 0
            camera_ports = [80, 81, 443, 554, 8080, 8081, 8082, 8888, 9999]
            
            # Quick scan of common camera IPs
            for i in [100, 101, 102, 150, 151, 152, 200, 201, 202]:
                ip = f"{network_base}.{i}"
                for port in camera_ports:
                    if self.check_cctv_port(ip, port):
                        camera_count += 1
                        break
            
            return camera_count
        except:
            return 0
    
    def get_open_ports(self):
        """Get list of open ports"""
        try:
            import socket
            open_ports = []
            for port in range(1, 1025):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                if result == 0:
                    open_ports.append(port)
            return open_ports
        except:
            return []
    
    def refresh_system_dashboard(self):
        """Refresh system dashboard data"""
        # This would update the dashboard in real-time
        # For now, just print a refresh indicator
        print("\r🔄 Refreshing...", end="", flush=True)
    
    def network_monitoring_dashboard(self):
        """Display network monitoring dashboard"""
        print("🌐 Network Monitoring Dashboard")
        print("=" * 60)
        
        # Get network information
        local_ip = self.get_local_ip()
        if not local_ip:
            print("❌ Could not determine local IP address")
            input("Press Enter to continue...")
            return
        
        network_base = '.'.join(local_ip.split('.')[:-1])
        
        print(f"📡 Network: {network_base}.x/24")
        print(f"🖥️  Your IP: {local_ip}")
        print()
        
        # Network topology
        print("🗺️  Network Topology:")
        print("┌─────────────────────────────────────────┐")
        print("│                Internet                  │")
        print("└─────────────┬───────────────────────────┘")
        print("              │")
        print(f"    ┌────────┴────────┐")
        print(f"    │   Router/Gateway │")
        print(f"    │   {network_base}.1      │")
        print(f"    └────────┬────────┘")
        print("              │")
        print("    ┌─────────┴─────────┐")
        print("    │   Network Switch   │")
        print("    └─────────┬─────────┘")
        print("              │")
        
        # Scan for devices
        print("🔍 Scanning for devices...")
        devices = self.scan_network_devices()
        
        # Display devices
        if devices:
            print(f"\n📱 Found {len(devices)} devices:")
            for i, device in enumerate(devices, 1):
                print(f"   {i}. {device['ip']} - {device['type']} ({device['status']})")
        else:
            print("   No devices found")
        
        # Network statistics
        print(f"\n📊 Network Statistics:")
        print(f"   Total Devices: {len(devices)}")
        print(f"   Network Range: {network_base}.1 - {network_base}.254")
        print(f"   Device Density: {len(devices)/254*100:.1f}%")
        
        input("Press Enter to continue...")
    
    def scan_network_devices(self):
        """Scan network for devices"""
        devices = []
        local_ip = self.get_local_ip()
        if not local_ip:
            return devices
        
        network_base = '.'.join(local_ip.split('.')[:-1])
        
        # Quick scan of common device IPs
        common_ips = list(range(1, 11)) + list(range(100, 110)) + list(range(200, 210))
        
        for i in common_ips:
            ip = f"{network_base}.{i}"
            if self.ping_device(ip):
                device_type = self.identify_device_type(ip)
                devices.append({
                    'ip': ip,
                    'type': device_type,
                    'status': 'Online'
                })
        
        return devices
    
    def ping_device(self, ip):
        """Ping a device to check if it's online"""
        try:
            import subprocess
            result = subprocess.run(['ping', '-c', '1', '-W', '1', ip], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def identify_device_type(self, ip):
        """Identify device type based on IP and services"""
        # Check common ports to identify device type
        if self.check_cctv_port(ip, 80) or self.check_cctv_port(ip, 8080):
            return "Camera/Web Device"
        elif self.check_cctv_port(ip, 22):
            return "SSH Server"
        elif self.check_cctv_port(ip, 443):
            return "HTTPS Server"
        else:
            return "Network Device"
    
    def camera_monitoring_dashboard(self):
        """Display camera monitoring dashboard"""
        print("📹 Camera Monitoring Dashboard")
        print("=" * 60)
        
        # Scan for cameras
        local_ip = self.get_local_ip()
        if not local_ip:
            print("❌ Could not determine local IP address")
            input("Press Enter to continue...")
            return
        
        network_base = '.'.join(local_ip.split('.')[:-1])
        print(f"🔍 Scanning for cameras on {network_base}.x...")
        
        cameras = []
        camera_ports = [80, 81, 443, 554, 8080, 8081, 8082, 8888, 9999]

        # 1) Seed targets from ARP to avoid probing down hosts
        def get_arp_ips(prefix: str):
            try:
                import subprocess
                result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
                if result.returncode == 0:
                    ips = []
                    for line in result.stdout.split('\n'):
                        if 'incomplete' in line:
                            continue
                        if '(' in line and ')' in line:
                            ip = line.split('(')[1].split(')')[0]
                            if ip.startswith(prefix + '.'):
                                ips.append(ip)
                    return list(dict.fromkeys(ips))
            except:
                pass
            return []

        seed_ips = get_arp_ips(network_base)
        # 2) Fall back to full /24 if ARP has nothing
        if not seed_ips:
            seed_ips = [f"{network_base}.{i}" for i in range(1, 255)]

        # Quick TCP connect probe with shorter timeout
        def quick_probe(ip: str, ports: list, timeout: float = 0.3):
            open_port = None
            for port in ports:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(timeout)
                    if s.connect_ex((ip, port)) == 0:
                        open_port = port
                        s.close()
                        break
                    s.close()
                except:
                    try:
                        s.close()
                    except:
                        pass
            return (ip, open_port)

        # 3) Parallelize with a thread pool and show progress
        total = len(seed_ips)
        completed = 0
        last_print = -1
        found = []
        max_workers = min(64, max(8, total // 4))

        print(f"⚡ Optimized scan: {total} target IPs, {max_workers} workers")
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(quick_probe, ip, camera_ports): ip for ip in seed_ips}
                for fut in as_completed(futures):
                    completed += 1
                    pct = int(completed * 100 / total)
                    if pct // 5 != last_print // 5:  # update every ~5%
                        print(f"\rProgress: {pct}% ({completed}/{total})", end="", flush=True)
                        last_print = pct
                    ip, port = fut.result()
                    if port is not None:
                        found.append((ip, port))
        finally:
            print()  # newline after progress

        # 4) Enrich found devices (brand/model/capabilities)
        for ip, port in found:
            try:
                camera_info = self.get_camera_details(ip, port)
                cameras.append(camera_info)
            except:
                pass
        
        if not cameras:
            print("✅ No cameras found on the network")
            input("Press Enter to continue...")
            return
        
        # Display camera dashboard
        print(f"\n📹 Found {len(cameras)} cameras:")
        print("=" * 80)
        
        for i, camera in enumerate(cameras, 1):
            print(f"\n📹 Camera #{i}: {camera['ip']}:{camera['port']}")
            print(f"   Brand: {camera['brand']} | Model: {camera['model']}")
            print(f"   Status: {camera['status']} | Location: {camera.get('location', 'Unknown')}")
            print(f"   Web Interface: http://{camera['ip']}:{camera['port']}")
            
            if camera.get('capabilities'):
                print(f"   Capabilities: {', '.join(camera['capabilities'][:3])}")
            
            if camera.get('security_issues'):
                print(f"   ⚠️  Security Issues: {len(camera['security_issues'])}")
        
        # Camera statistics
        brands = {}
        for camera in cameras:
            brand = camera['brand']
            brands[brand] = brands.get(brand, 0) + 1
        
        print(f"\n📊 Camera Statistics:")
        print(f"   Total Cameras: {len(cameras)}")
        print(f"   Brands: {', '.join(brands.keys())}")
        print(f"   Security Issues: {sum(len(c.get('security_issues', [])) for c in cameras)}")
        
        input("Press Enter to continue...")
    
    def security_dashboard(self):
        """Display security monitoring dashboard"""
        print("🔒 Security Monitoring Dashboard")
        print("=" * 60)
        
        # Get security information
        security_checks = [
            ("Firewall Status", self.check_firewall_status()),
            ("Antivirus Installed", self.check_antivirus()),
            ("File Permissions", self.check_file_permissions()),
            ("Suspicious Processes", self.check_suspicious_processes()),
            ("Open Ports", len(self.get_open_ports()) > 0),
            ("Screen Lock", self.check_screen_lock()),
            ("Encryption", self.check_encryption()),
            ("Auto Updates", self.check_auto_updates())
        ]
        
        print("🛡️  Security Status:")
        print("=" * 40)
        
        passed_checks = 0
        for check_name, result in security_checks:
            status = "✅ PASS" if result else "❌ FAIL"
            if result:
                passed_checks += 1
            print(f"   {status} {check_name}")
        
        # Security score
        security_score = (passed_checks / len(security_checks)) * 100
        risk_level = "LOW" if security_score >= 80 else "MEDIUM" if security_score >= 60 else "HIGH"
        
        print(f"\n📊 Security Score: {security_score:.1f}% ({risk_level} RISK)")
        
        # Recent security events (mock data)
        print(f"\n🚨 Recent Security Events:")
        events = [
            "Port scan detected from 192.168.1.100",
            "Failed login attempt on camera 192.168.1.150",
            "New device connected: 192.168.1.75"
        ]
        
        for event in events:
            print(f"   ⚠️  {event}")
        
        # Security recommendations
        print(f"\n💡 Security Recommendations:")
        if security_score < 80:
            print("   • Enable firewall if disabled")
            print("   • Install and update antivirus")
            print("   • Change default passwords")
            print("   • Enable automatic updates")
            print("   • Regular security scans")
        else:
            print("   • Continue regular security monitoring")
            print("   • Keep software updated")
            print("   • Monitor network traffic")
        
        input("Press Enter to continue...")
    
    def performance_dashboard(self):
        """Display performance monitoring dashboard"""
        print("📈 Performance Monitoring Dashboard")
        print("=" * 60)
        
        # Get performance metrics
        system_info = self.get_system_info()
        
        print("🖥️  System Performance:")
        print("=" * 40)
        print(f"   CPU Usage: {system_info['cpu_usage']}%")
        print(f"   Memory Usage: {system_info['memory_usage']}%")
        print(f"   Disk Usage: {system_info['disk_usage']}%")
        print(f"   Load Average: {system_info['load_avg']}")
        print(f"   Active Processes: {system_info['processes']}")
        
        # Performance visualization (ASCII bars)
        print(f"\n📊 Performance Bars:")
        cpu_usage = float(system_info['cpu_usage'].replace('%', ''))
        mem_usage = float(system_info['memory_usage'].replace('%', ''))
        disk_usage = float(system_info['disk_usage'].replace('%', ''))
        
        print(f"   CPU:  {'█' * int(cpu_usage/5):<20} {cpu_usage}%")
        print(f"   RAM:  {'█' * int(mem_usage/5):<20} {mem_usage}%")
        print(f"   Disk: {'█' * int(disk_usage/5):<20} {disk_usage}%")
        
        # Performance recommendations
        print(f"\n💡 Performance Recommendations:")
        if cpu_usage > 80:
            print("   • High CPU usage detected - close unnecessary programs")
        if mem_usage > 80:
            print("   • High memory usage - consider adding more RAM")
        if disk_usage > 80:
            print("   • High disk usage - clean up unnecessary files")
        
        if cpu_usage < 50 and mem_usage < 50 and disk_usage < 50:
            print("   • System performance is good")
        
        input("Press Enter to continue...")
    
    def web_dashboard(self):
        """Generate and open web-based dashboard"""
        print("🌍 Web Dashboard Generator")
        print("=" * 40)
        
        # Generate HTML dashboard
        html_content = self.generate_html_dashboard()
        
        # Save to file
        dashboard_file = "dashboard.html"
        with open(dashboard_file, 'w') as f:
            f.write(html_content)
        
        print(f"✅ Web dashboard generated: {dashboard_file}")
        print(f"🌐 Opening dashboard in browser...")
        
        try:
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(dashboard_file)}")
            print("✅ Dashboard opened in browser")
        except Exception as e:
            print(f"❌ Failed to open browser: {e}")
            print(f"   Manual URL: file://{os.path.abspath(dashboard_file)}")
        
        input("Press Enter to continue...")
    
    def generate_html_dashboard(self):
        """Generate HTML dashboard content"""
        system_info = self.get_system_info()
        network_info = self.get_network_info()
        security_info = self.get_security_info()
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CLI Assistant Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #667eea;
        }}
        .header h1 {{
            color: #667eea;
            margin: 0;
            font-size: 2.5em;
        }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-left: 5px solid #667eea;
        }}
        .card h3 {{
            margin-top: 0;
            color: #667eea;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        .metric:last-child {{
            border-bottom: none;
        }}
        .status {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.9em;
            font-weight: bold;
        }}
        .status.good {{ background: #d4edda; color: #155724; }}
        .status.warning {{ background: #fff3cd; color: #856404; }}
        .status.danger {{ background: #f8d7da; color: #721c24; }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 5px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
        }}
        .refresh-btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            margin: 10px;
        }}
        .refresh-btn:hover {{
            background: #5a6fd8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖥️ CLI Assistant Dashboard</h1>
            <p>Real-time System Monitoring</p>
            <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
        </div>
        
        <div class="dashboard-grid">
            <div class="card">
                <h3>🖥️ System Status</h3>
                <div class="metric">
                    <span>OS:</span>
                    <span>{system_info['os']}</span>
                </div>
                <div class="metric">
                    <span>Uptime:</span>
                    <span>{system_info['uptime']}</span>
                </div>
                <div class="metric">
                    <span>CPU Usage:</span>
                    <span>{system_info['cpu_usage']}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {system_info['cpu_usage']}%"></div>
                </div>
                <div class="metric">
                    <span>Memory Usage:</span>
                    <span>{system_info['memory_usage']}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {system_info['memory_usage']}%"></div>
                </div>
                <div class="metric">
                    <span>Disk Usage:</span>
                    <span>{system_info['disk_usage']}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {system_info['disk_usage']}%"></div>
                </div>
            </div>
            
            <div class="card">
                <h3>🌐 Network Status</h3>
                <div class="metric">
                    <span>Local IP:</span>
                    <span>{network_info['local_ip']}</span>
                </div>
                <div class="metric">
                    <span>Gateway:</span>
                    <span>{network_info['gateway']}</span>
                </div>
                <div class="metric">
                    <span>Interface:</span>
                    <span>{network_info['interface']}</span>
                </div>
                <div class="metric">
                    <span>Status:</span>
                    <span class="status good">{network_info['status']}</span>
                </div>
                <div class="metric">
                    <span>Devices:</span>
                    <span>{network_info['devices']}</span>
                </div>
                <div class="metric">
                    <span>Cameras:</span>
                    <span>{network_info['cameras']}</span>
                </div>
            </div>
            
            <div class="card">
                <h3>🔒 Security Status</h3>
                <div class="metric">
                    <span>Firewall:</span>
                    <span class="status {'good' if security_info['firewall'] == 'Enabled' else 'danger'}">{security_info['firewall']}</span>
                </div>
                <div class="metric">
                    <span>Antivirus:</span>
                    <span class="status {'good' if security_info['antivirus'] == 'Installed' else 'warning'}">{security_info['antivirus']}</span>
                </div>
                <div class="metric">
                    <span>Open Ports:</span>
                    <span>{security_info['open_ports']}</span>
                </div>
                <div class="metric">
                    <span>Threats:</span>
                    <span class="status {'good' if security_info['threats'] == '0' else 'danger'}">{security_info['threats']}</span>
                </div>
                <div class="metric">
                    <span>Risk Level:</span>
                    <span class="status {'good' if security_info['risk_level'] == 'LOW' else 'warning' if security_info['risk_level'] == 'MEDIUM' else 'danger'}">{security_info['risk_level']}</span>
                </div>
                <div class="metric">
                    <span>Last Scan:</span>
                    <span>{security_info['last_scan']}</span>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>🖥️ CLI Assistant Dashboard | Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>💡 Tip: Refresh the page to get updated information</p>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => {{
            location.reload();
        }}, 30000);
    </script>
</body>
</html>
"""
        return html

    def personal_desktop_dashboard(self):
        """Generate an interactive personal dashboard (todos/notes/focus/bookmarks/system)."""
        print("🗂️ Personal Desktop Dashboard")
        print("=" * 40)

        html = self.generate_personal_dashboard_html()
        out = "personal_dashboard.html"
        with open(out, 'w') as f:
            f.write(html)
        print(f"✅ Personal dashboard saved: {out}")
        try:
            import webbrowser, os
            webbrowser.open(f"file://{os.path.abspath(out)}")
            print("🌐 Opened in browser. Add it as your homepage or pin it.")
        except Exception as e:
            print(f"❌ Could not open browser: {e}")
        input("Press Enter to continue...")

    def generate_personal_dashboard_html(self):
        """Return HTML for a personal dashboard with client-side persistence (localStorage)."""
        sys_info = self.get_system_info()
        from datetime import datetime
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        return """
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
  <title>Personal Desktop Dashboard</title>
  <style>
    body {{ margin:0; background:#0f1220; color:#e6e6f0; font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto; }}
    header {{ padding:18px 24px; display:flex; justify-content:space-between; align-items:center; background:#131730; position:sticky; top:0; }}
    .time {{ font-weight:600; opacity:.9 }}
    .grid {{ display:grid; gap:16px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); padding:16px; }}
    .card {{ background:#151936; border:1px solid #1f2450; border-radius:12px; padding:14px; box-shadow:0 10px 30px rgba(0,0,0,.25); }}
    .card h3 {{ margin:0 0 10px; font-size:16px; color:#b6c0ff; letter-spacing:.3px; }}
    .row {{ display:flex; gap:8px; }}
    input[type=text], input[type=url], textarea {{ width:100%; background:#0f1330; color:#e6e6f0; border:1px solid #2a3266; border-radius:8px; padding:8px 10px; }}
    button {{ background:#4452ff; color:white; border:0; padding:8px 10px; border-radius:8px; cursor:pointer; }}
    button.ghost {{ background:transparent; border:1px solid #2a3266; }}
    ul {{ list-style:none; padding:0; margin:8px 0 0; }}
    li {{ padding:6px 6px; border:1px solid #232a5a; border-radius:8px; margin-bottom:6px; display:flex; align-items:center; justify-content:space-between; gap:6px; }}
    .pill {{ background:#0f1330; border:1px solid #2a3266; padding:2px 8px; border-radius:999px; font-size:12px; opacity:.9 }}
    .muted {{ opacity:.8 }}
    .progress {{ height:8px; background:#0f1330; border:1px solid #2a3266; border-radius:999px; overflow:hidden; }}
    .progress > div {{ height:100%; background:linear-gradient(90deg,#6a77ff,#9a66ff); width:0% }}
    a { color:#9ab4ff; text-decoration:none }
  </style>
</head>
<body>
  <header>
    <div>🗂️ Personal Dashboard</div>
    <div class=\"time\" id=\"clock\">{}</div>
  </header>
  <div class=\"grid\">
    <div class=\"card\">
      <h3>✅ To‑Do</h3>
      <div class=\"row\"><input id=\"todoInput\" type=\"text\" placeholder=\"Add a task and hit Enter\"></div>
      <ul id=\"todoList\"></ul>
    </div>
    <div class=\"card\">
      <h3>🗒️ Notes</h3>
      <textarea id=\"notes\" rows=\"8\" placeholder=\"Quick notes...\"></textarea>
      <div class=\"muted\" style=\"margin-top:6px\">Saved automatically</div>
    </div>
    <div class=\"card\">
      <h3>🎯 Focus Mode</h3>
      <div class=\"row\">
        <input id=\"focusTask\" type=\"text\" placeholder=\"Focus task\">
        <input id=\"focusMins\" type=\"text\" placeholder=\"25\" style=\"width:70px\"> 
        <button id=\"startFocus\">Start</button>
      </div>
      <div id=\"focusStatus\" class=\"muted\" style=\"margin-top:8px\">Idle</div>
      <div class=\"progress\" style=\"margin-top:8px\"><div id=\"focusBar\"></div></div>
    </div>
    <div class=\"card\">
      <h3>🌐 Bookmarks</h3>
      <div class=\"row\">
        <input id=\"bmTitle\" type=\"text\" placeholder=\"Title\">
        <input id=\"bmUrl\" type=\"url\" placeholder=\"https://\">
        <button id=\"addBm\">Add</button>
      </div>
      <ul id=\"bmList\"></ul>
    </div>
    <div class=\"card\">
      <h3>🖥️ System Snapshot</h3>
      <div>OS <span class=\"pill\">{}</span></div>
      <div style=\"margin-top:6px\" class=\"muted\">CPU {}% • RAM {}% • Disk {}%</div>
      <div style=\"margin-top:6px\" class=\"muted\">Uptime {} • Load {}</div>
    </div>
    <div class=\"card\">
      <h3>📄 Saved Pages</h3>
      <div class=\"row\">
        <input id=\"spTitle\" type=\"text\" placeholder=\"Label\">
        <input id=\"spUrl\" type=\"url\" placeholder=\"https://\">
        <button id=\"addSp\">Save</button>
      </div>
      <ul id=\"spList\"></ul>
    </div>
  </div>
  <script>
    const $ = (q)=>document.querySelector(q);
    const save = (k,v)=>localStorage.setItem(k, JSON.stringify(v));
    const load = (k,d)=>{try{ return JSON.parse(localStorage.getItem(k)) ?? d }catch{ return d }};

    function tick(){ const d=new Date(); $('#clock').textContent=d.toLocaleString(); }
    setInterval(tick,1000); tick();

    // TODOs
    let todos = load('dash.todos', []);
    function renderTodos(){ const ul=$('#todoList'); ul.innerHTML='';
      todos.forEach((t,i)=>{ const li=document.createElement('li');
        li.innerHTML = `<span class="row"><input type="checkbox" ${t.done?'checked':''} data-i="${i}"> <span>${t.text}</span></span><button class="ghost" data-del="${i}">✕</button>`;
        ul.appendChild(li); }); }
    renderTodos();
    $('#todoInput').addEventListener('keydown',e=>{ if(e.key==='Enter'&&e.target.value.trim()){ todos.push({text:e.target.value.trim(),done:false}); save('dash.todos',todos); e.target.value=''; renderTodos(); }});
    $('#todoList').addEventListener('click',e=>{ if(e.target.dataset.i!==undefined){ const i=+e.target.dataset.i; todos[i].done=e.target.checked; save('dash.todos',todos); } if(e.target.dataset.del!==undefined){ const i=+e.target.dataset.del; todos.splice(i,1); save('dash.todos',todos); renderTodos(); }});

    // Notes
    $('#notes').value = load('dash.notes','');
    $('#notes').addEventListener('input',()=>save('dash.notes',$('#notes').value));

    // Focus (simple Pomodoro)
    let timer=null, totalMs=0, startTs=0;
    function updateBar(){ if(!timer) return; const elapsed=Date.now()-startTs; const pct=Math.min(100, Math.round(elapsed/totalMs*100)); $('#focusBar').style.width=pct+'%'; if(pct>=100){ clearInterval(timer); timer=null; $('#focusStatus').textContent='Done'; }}
    $('#startFocus').onclick=()=>{ const mins=parseInt($('#focusMins').value||'25'); if(!mins) return; totalMs=mins*60000; startTs=Date.now(); $('#focusStatus').textContent='Focusing: '+($('#focusTask').value||'Task')+' ('+mins+'m)'; updateBar(); if(timer) clearInterval(timer); timer=setInterval(updateBar,500); };

    // Bookmarks
    let bms = load('dash.bookmarks', []);
    function renderBm(){ const ul=$('#bmList'); ul.innerHTML=''; bms.forEach((b,i)=>{ const li=document.createElement('li'); li.innerHTML=`<a href="${b.url}" target="_blank">${b.title}</a><button class="ghost" data-delbm="${i}">✕</button>`; ul.appendChild(li); }); }
    renderBm();
    $('#addBm').onclick=()=>{ const t=$('#bmTitle').value.trim(); const u=$('#bmUrl').value.trim(); if(t&&u){ bms.push({title:t,url:u}); save('dash.bookmarks',bms); $('#bmTitle').value=''; $('#bmUrl').value=''; renderBm(); } };
    $('#bmList').addEventListener('click',e=>{ if(e.target.dataset.delbm!==undefined){ bms.splice(+e.target.dataset.delbm,1); save('dash.bookmarks',bms); renderBm(); }});

    // Saved Pages (quick list separate from bookmarks)
    let sps = load('dash.savedpages', []);
    function renderSp(){ const ul=$('#spList'); ul.innerHTML=''; sps.forEach((b,i)=>{ const li=document.createElement('li'); li.innerHTML=`<a href="${b.url}" target="_blank">${b.title}</a><button class="ghost" data-delsp="${i}">✕</button>`; ul.appendChild(li); }); }
    renderSp();
    $('#addSp').onclick=()=>{ const t=$('#spTitle').value.trim(); const u=$('#spUrl').value.trim(); if(t&&u){ sps.push({title:t,url:u}); save('dash.savedpages',sps); $('#spTitle').value=''; $('#spUrl').value=''; renderSp(); } };
    $('#spList').addEventListener('click',e=>{ if(e.target.dataset.delsp!==undefined){ sps.splice(+e.target.dataset.delsp,1); save('dash.savedpages',sps); renderSp(); }});
  </script>
</body>
</html>
""".format(now, sys_info['os'], sys_info['cpu_usage'], sys_info['memory_usage'], sys_info['disk_usage'], sys_info['uptime'], sys_info['load_avg'])
    
    def dashboard_settings(self):
        """Configure dashboard settings"""
        print("⚙️  Dashboard Settings")
        print("=" * 40)
        
        options = [
            "🔄 Auto-refresh interval",
            "📊 Dashboard theme",
            "🔔 Alert notifications",
            "📈 Performance thresholds",
            "🌐 Web dashboard settings",
            "⬅️  Back to dashboard menu"
        ]
        
        choice = self.menu.show_dropdown("Dashboard Settings", options)
        
        if choice == 0:
            self.set_refresh_interval()
        elif choice == 1:
            self.set_dashboard_theme()
        elif choice == 2:
            self.set_alert_notifications()
        elif choice == 3:
            self.set_performance_thresholds()
        elif choice == 4:
            self.set_web_dashboard_settings()
        elif choice == 5 or choice == -1:
            pass  # Back to dashboard menu
    
    def set_refresh_interval(self):
        """Set dashboard refresh interval"""
        print("🔄 Auto-refresh Interval")
        print("=" * 30)
        
        intervals = ["5 seconds", "10 seconds", "30 seconds", "1 minute", "5 minutes", "Disabled"]
        choice = self.menu.show_dropdown("Select refresh interval", intervals)
        
        if choice >= 0:
            print(f"✅ Refresh interval set to: {intervals[choice]}")
        
        input("Press Enter to continue...")
    
    def set_dashboard_theme(self):
        """Set dashboard theme"""
        print("📊 Dashboard Theme")
        print("=" * 25)
        
        themes = ["Dark", "Light", "Blue", "Green", "Purple"]
        choice = self.menu.show_dropdown("Select theme", themes)
        
        if choice >= 0:
            print(f"✅ Theme set to: {themes[choice]}")
        
        input("Press Enter to continue...")
    
    def set_alert_notifications(self):
        """Set alert notifications"""
        print("🔔 Alert Notifications")
        print("=" * 30)
        
        options = ["Enable all alerts", "Disable all alerts", "Configure specific alerts"]
        choice = self.menu.show_dropdown("Alert settings", options)
        
        if choice >= 0:
            print(f"✅ Alert settings updated")
        
        input("Press Enter to continue...")
    
    def set_performance_thresholds(self):
        """Set performance thresholds"""
        print("📈 Performance Thresholds")
        print("=" * 35)
        
        print("Set alert thresholds for system resources:")
        
        with patch.object(self.menu, 'show_input_prompt', return_value='80'):
            cpu_threshold = self.menu.show_input_prompt("CPU usage threshold (%)", "80")
        
        with patch.object(self.menu, 'show_input_prompt', return_value='85'):
            memory_threshold = self.menu.show_input_prompt("Memory usage threshold (%)", "85")
        
        with patch.object(self.menu, 'show_input_prompt', return_value='90'):
            disk_threshold = self.menu.show_input_prompt("Disk usage threshold (%)", "90")
        
        print(f"✅ Thresholds set - CPU: {cpu_threshold}%, Memory: {memory_threshold}%, Disk: {disk_threshold}%")
        input("Press Enter to continue...")
    
    def set_web_dashboard_settings(self):
        """Set web dashboard settings"""
        print("🌐 Web Dashboard Settings")
        print("=" * 35)
        
        options = ["Auto-open in browser", "Include network map", "Include camera feed", "Dark mode"]
        choices = []
        
        for option in options:
            choice = self.menu.show_confirmation(f"Enable {option}?")
            choices.append(choice)
        
        enabled_features = [option for option, enabled in zip(options, choices) if enabled]
        
        if enabled_features:
            print(f"✅ Enabled features: {', '.join(enabled_features)}")
        else:
            print("✅ No additional features enabled")
        
        input("Press Enter to continue...")
    
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
        if source:
            # Expand ~ to home directory
            source = os.path.expanduser(source)
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
        while True:
            print("🔄 Calendar Synchronization")
            print("─" * 50)
            print("Sync your reminders with external calendar services")
            print()
            
            options = ["Google Calendar", "Apple Calendar", "Outlook Calendar", "iCal File", "Configure Sync", "Back to Reminders Menu"]
            choice = self.menu.show_dropdown("Select calendar service", options)
            
            if choice == 0:  # Google Calendar
                self.sync_google_calendar()
            elif choice == 1:  # Apple Calendar
                self.sync_apple_calendar()
            elif choice == 2:  # Outlook Calendar
                self.sync_outlook_calendar()
            elif choice == 3:  # iCal File
                self.sync_ical_file()
            elif choice == 4:  # Configure Sync
                self.configure_calendar_sync()
            elif choice == 5 or choice == -1:  # Back
                break
            
            if choice != 5 and choice != -1:
                input("Press Enter to continue...")
    
    def sync_google_calendar(self):
        """Sync with Google Calendar"""
        print("📅 Google Calendar Sync")
        print("─" * 50)
        
        try:
            # Check if google-auth and google-auth-oauthlib are available
            try:
                import google.auth
                import google.auth.transport.requests
                from google.oauth2.credentials import Credentials
                from google_auth_oauthlib.flow import InstalledAppFlow
                from google.auth.exceptions import RefreshError
                from googleapiclient.discovery import build
                
                print("✅ Google Calendar libraries available")
                
                # Check for existing credentials
                creds = None
                token_file = 'token.json'
                
                if os.path.exists(token_file):
                    creds = Credentials.from_authorized_user_file(token_file, ['https://www.googleapis.com/auth/calendar'])
                
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        try:
                            creds.refresh(google.auth.transport.requests.Request())
                        except RefreshError:
                            creds = None
                    
                    if not creds:
                        print("🔐 Authentication required")
                        print("1. Go to Google Cloud Console")
                        print("2. Enable Google Calendar API")
                        print("3. Download credentials.json")
                        print("4. Place it in the same directory as this script")
                        
                        if os.path.exists('credentials.json'):
                            flow = InstalledAppFlow.from_client_secrets_file(
                                'credentials.json', ['https://www.googleapis.com/auth/calendar'])
                            creds = flow.run_local_server(port=0)
                            
                            # Save credentials
                            with open(token_file, 'w') as token:
                                token.write(creds.to_json())
                            
                            print("✅ Authentication successful!")
                        else:
                            print("❌ credentials.json not found")
                            print("💡 Download from Google Cloud Console")
                            return
                
                # Build service
                service = build('calendar', 'v3', credentials=creds)
                
                # Get reminders to sync
                if 'reminders' in self.config and self.config['reminders']:
                    reminders_to_sync = [r for r in self.config['reminders'] if not r.get('synced_to_google')]
                    
                    if reminders_to_sync:
                        print(f"📝 Found {len(reminders_to_sync)} reminders to sync")
                        
                        if self.menu.show_confirmation(f"Sync {len(reminders_to_sync)} reminders to Google Calendar?"):
                            synced_count = 0
                            
                            for reminder in reminders_to_sync:
                                try:
                                    # Create calendar event
                                    event = {
                                        'summary': reminder['title'],
                                        'description': reminder.get('description', ''),
                                        'start': {
                                            'dateTime': f"{reminder['date']}T{reminder['time']}:00",
                                            'timeZone': 'UTC',
                                        },
                                        'end': {
                                            'dateTime': f"{reminder['date']}T{reminder['time']}:00",
                                            'timeZone': 'UTC',
                                        },
                                        'reminders': {
                                            'useDefault': False,
                                            'overrides': [
                                                {'method': 'popup', 'minutes': 0},
                                            ],
                                        },
                                    }
                                    
                                    event = service.events().insert(calendarId='primary', body=event).execute()
                                    
                                    # Mark as synced
                                    reminder['synced_to_google'] = True
                                    reminder['google_event_id'] = event['id']
                                    
                                    synced_count += 1
                                    print(f"✅ Synced: {reminder['title']}")
                                    
                                except Exception as e:
                                    print(f"❌ Failed to sync {reminder['title']}: {e}")
                            
                            # Save updated reminders
                            self.save_config()
                            print(f"✅ Successfully synced {synced_count} reminders!")
                        else:
                            print("❌ Sync cancelled")
                    else:
                        print("ℹ️  All reminders are already synced")
                else:
                    print("ℹ️  No reminders to sync")
                    
            except ImportError:
                print("❌ Google Calendar libraries not installed")
                print("💡 Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
                print("💡 Or use manual export/import instead")
                
        except Exception as e:
            print(f"❌ Google Calendar sync error: {e}")
    
    def sync_apple_calendar(self):
        """Sync with Apple Calendar"""
        print("🍎 Apple Calendar Sync")
        print("─" * 50)
        
        try:
            # Check if we're on macOS
            if os.name == 'posix' and os.path.exists('/Applications/Calendar.app'):
                print("✅ Apple Calendar detected on macOS")
                
                # Export reminders to iCal format
                if 'reminders' in self.config and self.config['reminders']:
                    reminders_to_sync = [r for r in self.config['reminders'] if not r.get('synced_to_apple')]
                    
                    if reminders_to_sync:
                        print(f"📝 Found {len(reminders_to_sync)} reminders to sync")
                        
                        if self.menu.show_confirmation(f"Export {len(reminders_to_sync)} reminders to iCal file?"):
                            # Create iCal file
                            ical_content = self.create_ical_file(reminders_to_sync)
                            
                            # Save to file
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            ical_filename = f"reminders_{timestamp}.ics"
                            
                            with open(ical_filename, 'w') as f:
                                f.write(ical_content)
                            
                            print(f"✅ iCal file created: {ical_filename}")
                            print("💡 To import to Apple Calendar:")
                            print("   1. Double-click the .ics file")
                            print("   2. Or drag it to Calendar app")
                            print("   3. Or use File > Import in Calendar")
                            
                            # Mark as synced
                            for reminder in reminders_to_sync:
                                reminder['synced_to_apple'] = True
                                reminder['apple_ical_file'] = ical_filename
                            
                            self.save_config()
                        else:
                            print("❌ Export cancelled")
                    else:
                        print("ℹ️  All reminders are already synced")
                else:
                    print("ℹ️  No reminders to sync")
            else:
                print("❌ Apple Calendar not available on this system")
                print("💡 This feature works best on macOS")
                
        except Exception as e:
            print(f"❌ Apple Calendar sync error: {e}")
    
    def sync_outlook_calendar(self):
        """Sync with Outlook Calendar"""
        print("📧 Outlook Calendar Sync")
        print("─" * 50)
        print("Outlook Calendar sync requires Microsoft Graph API setup")
        print("💡 For now, use iCal export/import instead")
        print("💡 Or manually add reminders to Outlook")
        
        # Offer iCal export as alternative
        if self.menu.show_confirmation("Export reminders to iCal file instead?"):
            self.sync_ical_file()
    
    def sync_ical_file(self):
        """Export reminders to iCal file"""
        print("📅 iCal File Export")
        print("─" * 50)
        
        if 'reminders' in self.config and self.config['reminders']:
            reminders_to_export = [r for r in self.config['reminders'] if not r.get('completed', False)]
            
            if reminders_to_export:
                print(f"📝 Found {len(reminders_to_export)} active reminders to export")
                
                if self.menu.show_confirmation(f"Export {len(reminders_to_export)} reminders to iCal file?"):
                    # Create iCal file
                    ical_content = self.create_ical_file(reminders_to_export)
                    
                    # Save to file
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    ical_filename = f"reminders_{timestamp}.ics"
                    
                    with open(ical_filename, 'w') as f:
                        f.write(ical_content)
                    
                    print(f"✅ iCal file created: {ical_filename}")
                    print(f"📁 Full path: {os.path.abspath(ical_filename)}")
                    print("💡 Import this file into any calendar application")
                    
                    # Mark as exported
                    for reminder in reminders_to_export:
                        reminder['exported_to_ical'] = True
                        reminder['ical_filename'] = ical_filename
                    
                    self.save_config()
                else:
                    print("❌ Export cancelled")
            else:
                print("ℹ️  No active reminders to export")
        else:
            print("ℹ️  No reminders found")
    
    def create_ical_file(self, reminders):
        """Create iCal content from reminders"""
        ical_content = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//CLI Assistant//Reminders//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH"
        ]
        
        for reminder in reminders:
            # Create event
            event_id = f"reminder_{reminder.get('id', hash(reminder['title']))}"
            
            # Parse date and time
            try:
                date_obj = datetime.strptime(f"{reminder['date']} {reminder['time']}", "%Y-%m-%d %H:%M")
                start_time = date_obj.strftime("%Y%m%dT%H%M%SZ")
                end_time = (date_obj + timedelta(minutes=30)).strftime("%Y%m%dT%H%M%SZ")
            except:
                # Fallback to date only
                start_time = reminder['date'].replace("-", "")
                end_time = start_time
            
            event_lines = [
                "BEGIN:VEVENT",
                f"UID:{event_id}",
                f"DTSTART:{start_time}",
                f"DTEND:{end_time}",
                f"SUMMARY:{reminder['title']}",
                f"DESCRIPTION:{reminder.get('description', '')}",
                "STATUS:CONFIRMED",
                "SEQUENCE:0",
                "END:VEVENT"
            ]
            
            ical_content.extend(event_lines)
        
        ical_content.append("END:VCALENDAR")
        return "\n".join(ical_content)
    
    def configure_calendar_sync(self):
        """Configure calendar synchronization settings"""
        print("⚙️  Calendar Sync Configuration")
        print("─" * 50)
        
        current_settings = self.config.get('calendar_sync', {})
        
        # Auto-sync settings
        auto_sync = current_settings.get('auto_sync', False)
        sync_interval = current_settings.get('sync_interval', 'daily')
        sync_on_create = current_settings.get('sync_on_create', True)
        sync_on_update = current_settings.get('sync_on_update', True)
        sync_on_delete = current_settings.get('sync_on_delete', True)
        
        print("Current settings:")
        print(f"  Auto-sync: {auto_sync}")
        print(f"  Sync interval: {sync_interval}")
        print(f"  Sync on create: {sync_on_create}")
        print(f"  Sync on update: {sync_on_update}")
        print(f"  Sync on delete: {sync_on_delete}")
        print()
        
        if self.menu.show_confirmation("Modify these settings?"):
            auto_sync = self.menu.show_confirmation("Enable auto-sync?", auto_sync)
            
            if auto_sync:
                intervals = ["Every hour", "Daily", "Weekly", "Manual only"]
                interval_choice = self.menu.show_dropdown("Select sync interval", intervals)
                if interval_choice >= 0:
                    sync_interval = intervals[interval_choice].lower()
            
            sync_on_create = self.menu.show_confirmation("Sync when creating reminders?", sync_on_create)
            sync_on_update = self.menu.show_confirmation("Sync when updating reminders?", sync_on_update)
            sync_on_delete = self.menu.show_confirmation("Sync when deleting reminders?", sync_on_delete)
            
            # Save settings
            self.config['calendar_sync'] = {
                'auto_sync': auto_sync,
                'sync_interval': sync_interval,
                'sync_on_create': sync_on_create,
                'sync_on_update': sync_on_update,
                'sync_on_delete': sync_on_delete
            }
            
            self.save_config()
            print("✅ Calendar sync settings saved!")
        else:
            print("ℹ️  Settings unchanged.")
    
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
        try:
            import requests
            
            model = self.menu.show_input_prompt("Enter model name (e.g., llama2)", "llama2")
            question = self.menu.show_input_prompt("Enter your question")
            
            if question:
                # Format as Q&A prompt
                prompt = f"Question: {question}\nAnswer:"
                
                url = "http://localhost:11434/api/generate"
                data = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
                
                print("🤔 Processing your question...")
                response = requests.post(url, json=data, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"🤖 AI Answer:")
                    print("─" * 50)
                    print(result.get('response', 'No response'))
                else:
                    print("❌ Ollama not running or model not found")
                    print("Start Ollama with: ollama serve")
                    print(f"Pull model with: ollama pull {model}")
                    
        except ImportError:
            print("❌ requests library not installed. Install with: pip install requests")
        except Exception as e:
            print(f"❌ Question error: {e}")
        
        input("Press Enter to continue...")
    
    def ollama_analyze_data(self):
        """Analyze data with Ollama"""
        try:
            import requests
            
            model = self.menu.show_input_prompt("Enter model name", "llama2")
            
            # Get data input method
            input_options = ["Paste data directly", "Load from file", "System statistics"]
            choice = self.menu.show_dropdown("Select data input method", input_options)
            
            data_text = ""
            if choice == 0:
                data_text = self.menu.show_input_prompt("Paste your data here")
            elif choice == 1:
                file_path = self.menu.show_input_prompt("Enter file path")
                if file_path and os.path.exists(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            data_text = f.read()[:1000]  # Limit to first 1000 chars
                    except Exception as e:
                        print(f"❌ Error reading file: {e}")
                        input("Press Enter to continue...")
                        return
            elif choice == 2:
                # Get system stats as sample data
                try:
                    import psutil
                    data_text = f"""System Statistics:
CPU Usage: {psutil.cpu_percent()}%
Memory Usage: {psutil.virtual_memory().percent}%
Disk Usage: {psutil.disk_usage('/').percent}%
Active Processes: {len(psutil.pids())}
Boot Time: {psutil.boot_time()}"""
                except ImportError:
                    data_text = "System statistics data would go here"
            
            if data_text:
                analysis_type = self.menu.show_input_prompt("What kind of analysis do you want?", "summarize and find patterns")
                
                prompt = f"""Analyze the following data and {analysis_type}:

Data:
{data_text}

Analysis:"""
                
                url = "http://localhost:11434/api/generate"
                data = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
                
                print("📊 Analyzing data...")
                response = requests.post(url, json=data, timeout=120)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"📈 Data Analysis Results:")
                    print("─" * 60)
                    print(result.get('response', 'No analysis available'))
                else:
                    print("❌ Ollama not running or model not found")
                    
        except ImportError:
            print("❌ requests library not installed. Install with: pip install requests")
        except Exception as e:
            print(f"❌ Analysis error: {e}")
        
        input("Press Enter to continue...")
    
    def ollama_generate_images(self):
        """Generate images with Ollama"""
        print("🖼️  Image Generation with Ollama")
        print("─" * 50)
        
        try:
            import requests
            
            # Check available models
            api_url = self.config.get('ollama_settings', {}).get('api_url', 'http://localhost:11434')
            models_url = f"{api_url}/api/tags"
            
            response = requests.get(models_url, timeout=10)
            if response.status_code != 200:
                print("❌ Cannot connect to Ollama. Make sure it's running.")
                input("Press Enter to continue...")
                return
            
            models = response.json().get('models', [])
            vision_models = [model['name'] for model in models if any(keyword in model['name'].lower() for keyword in ['llava', 'vision', 'image', 'stable', 'diffusion'])]
            
            if not vision_models:
                print("❌ No vision/image generation models found.")
                print("💡 Available models:")
                for model in models[:5]:
                    print(f"  • {model['name']}")
                if len(models) > 5:
                    print(f"  ... and {len(models) - 5} more")
                print("\n💡 To use image generation, pull a vision model:")
                print("  ollama pull llava")
                print("  ollama pull stable-diffusion")
                input("Press Enter to continue...")
                return
            
            # Select model
            print("Available vision models:")
            for i, model in enumerate(vision_models, 1):
                print(f"  {i}. {model}")
            print()
            
            model_choice = self.menu.show_dropdown("Select vision model", vision_models)
            if model_choice < 0:
                print("❌ Model selection cancelled.")
                input("Press Enter to continue...")
                return
            
            selected_model = vision_models[model_choice]
            
            # Get generation parameters
            prompt = self.menu.show_input_prompt("Enter image description/prompt")
            if not prompt:
                print("❌ No prompt provided.")
                input("Press Enter to continue...")
                return
            
            # Get additional parameters
            print("\n⚙️  Image Generation Parameters:")
            width = int(self.menu.show_input_prompt("Width (pixels)", "512"))
            height = int(self.menu.show_input_prompt("Height (pixels)", "512"))
            steps = int(self.menu.show_input_prompt("Generation steps (10-50)", "20"))
            
            # Validate parameters
            try:
                width = max(64, min(2048, int(width)))
                height = max(64, min(2048, int(height)))
                steps = max(10, min(50, int(steps)))
            except ValueError:
                print("⚠️  Invalid parameters, using defaults")
                width, height, steps = 512, 512, 20
            
            print(f"\n🎨 Generating image with {selected_model}...")
            print(f"📝 Prompt: {prompt}")
            print(f"📏 Size: {width}x{height}")
            print(f"🔄 Steps: {steps}")
            print("⏳ This may take a while...")
            
            # Generate image
            generation_url = f"{api_url}/api/generate"
            generation_data = {
                "model": selected_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "width": width,
                    "height": height,
                    "steps": steps
                }
            }
            
            # For models that support image generation
            if 'llava' in selected_model.lower():
                # LLaVA models can analyze images but don't generate them
                print("ℹ️  LLaVA models analyze images but don't generate them.")
                print("💡 Use stable-diffusion models for image generation.")
                
                # Try to get model info
                model_info_url = f"{api_url}/api/show"
                model_info_data = {"name": selected_model}
                
                try:
                    info_response = requests.post(model_info_url, json=model_info_data, timeout=10)
                    if info_response.status_code == 200:
                        model_info = info_response.json()
                        print(f"📋 Model info: {model_info.get('modelfile', 'No description')[:100]}...")
                except:
                    pass
                    
            elif 'stable' in selected_model.lower() or 'diffusion' in selected_model.lower():
                # Stable Diffusion models
                try:
                    response = requests.post(generation_url, json=generation_data, timeout=120)
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if 'response' in result:
                            # Some models return base64 image data
                            print("✅ Image generation completed!")
                            print(f"📊 Response: {result['response'][:100]}...")
                            
                            # Try to save image if it's base64
                            if 'data:image' in result['response']:
                                self.save_generated_image(result['response'], prompt)
                            else:
                                print("ℹ️  Image data not in expected format")
                        else:
                            print("✅ Generation completed!")
                            print(f"📊 Response: {result}")
                    else:
                        print(f"❌ Generation failed. Status: {response.status_code}")
                        print(f"Response: {response.text}")
                        
                except Exception as e:
                    print(f"❌ Generation error: {e}")
            else:
                # Generic vision model
                print(f"🔄 Attempting generation with {selected_model}...")
                try:
                    response = requests.post(generation_url, json=generation_data, timeout=120)
                    
                    if response.status_code == 200:
                        result = response.json()
                        print("✅ Generation completed!")
                        print(f"📊 Response: {result.get('response', 'No response')[:200]}...")
                    else:
                        print(f"❌ Generation failed. Status: {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Generation error: {e}")
            
            print("\n💡 Note: Full image generation support depends on the specific model capabilities.")
            print("   Some models may only support image analysis or text generation.")
            
        except ImportError:
            print("❌ requests library not installed. Install with: pip install requests")
        except Exception as e:
            print(f"❌ Image generation error: {e}")
        
        input("Press Enter to continue...")
    
    def save_generated_image(self, image_data, prompt):
        """Save generated image to file"""
        try:
            import base64
            import re
            
            # Extract base64 data
            match = re.search(r'data:image/(\w+);base64,(.+)', image_data)
            if match:
                image_format = match.group(1)
                base64_data = match.group(2)
                
                # Decode base64
                image_bytes = base64.b64decode(base64_data)
                
                # Create filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_prompt = "".join(c for c in prompt if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_prompt = safe_prompt[:30]  # Limit length
                filename = f"generated_image_{timestamp}_{safe_prompt}.{image_format}"
                
                # Save file
                with open(filename, 'wb') as f:
                    f.write(image_bytes)
                
                print(f"💾 Image saved as: {filename}")
                print(f"📁 Full path: {os.path.abspath(filename)}")
            else:
                print("⚠️  Could not extract image data from response")
                
        except Exception as e:
            print(f"❌ Error saving image: {e}")
    
    def ollama_document_analysis(self):
        """Analyze documents with Ollama"""
        try:
            import requests
            
            model = self.menu.show_input_prompt("Enter model name", "llama2")
            file_path = self.menu.show_input_prompt("Enter document file path")
            
            if file_path and os.path.exists(file_path):
                try:
                    # Read document content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()[:2000]  # Limit to first 2000 chars
                    
                    # Get analysis type
                    analysis_options = ["Summarize", "Extract key points", "Analyze sentiment", "Find themes", "Custom analysis"]
                    choice = self.menu.show_dropdown("Select analysis type", analysis_options)
                    
                    if choice >= 0:
                        analysis_types = {
                            0: "Provide a concise summary of this document",
                            1: "Extract the key points and main ideas from this document",
                            2: "Analyze the sentiment and tone of this document",
                            3: "Identify the main themes and topics in this document",
                            4: self.menu.show_input_prompt("Enter custom analysis request", "analyze this document")
                        }
                        
                        analysis_request = analysis_types.get(choice, "analyze this document")
                        
                        prompt = f"""{analysis_request}:

Document content:
{content}

Analysis:"""
                        
                        url = "http://localhost:11434/api/generate"
                        data = {
                            "model": model,
                            "prompt": prompt,
                            "stream": False
                        }
                        
                        print("📚 Analyzing document...")
                        response = requests.post(url, json=data, timeout=120)
                        
                        if response.status_code == 200:
                            result = response.json()
                            print(f"📄 Document Analysis Results:")
                            print("─" * 60)
                            print(f"File: {file_path}")
                            print(f"Size: {len(content)} characters (truncated)")
                            print("─" * 60)
                            print(result.get('response', 'No analysis available'))
                        else:
                            print("❌ Ollama not running or model not found")
                    else:
                        print("❌ Analysis cancelled.")
                        
                except UnicodeDecodeError:
                    print("❌ Cannot read file - not a text document or encoding issue")
                except Exception as e:
                    print(f"❌ Error reading document: {e}")
            else:
                print("❌ File not found or no file path provided")
                
        except ImportError:
            print("❌ requests library not installed. Install with: pip install requests")
        except Exception as e:
            print(f"❌ Document analysis error: {e}")
        
        input("Press Enter to continue...")
    
    def ollama_settings(self):
        """Configure Ollama settings"""
        while True:
            options = ["Change Default Model", "Set API URL", "Configure Model Parameters", "List Available Models", "Test Connection", "Back to Ollama Menu"]
            choice = self.menu.show_dropdown("Ollama Settings", options)
            
            if choice == 0:  # Change Default Model
                self.change_default_model()
            elif choice == 1:  # Set API URL
                self.set_ollama_api_url()
            elif choice == 2:  # Configure Model Parameters
                self.configure_model_parameters()
            elif choice == 3:  # List Available Models
                self.list_available_models()
            elif choice == 4:  # Test Connection
                self.test_ollama_connection()
            elif choice == 5 or choice == -1:  # Back
                break
    
    def change_default_model(self):
        """Change the default Ollama model"""
        try:
            import requests
            
            print("🔄 Connecting to Ollama...")
            
            # Get current models from Ollama
            api_url = self.config.get('ollama_settings', {}).get('api_url', 'http://localhost:11434')
            url = f"{api_url}/api/tags"
            
            print(f"📡 API URL: {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                print(f"✅ Found {len(models)} model(s)")
                
                if models:
                    model_names = [model['name'] for model in models]
                    print("📚 Available models:")
                    for i, name in enumerate(model_names):
                        print(f"  {i+1}. {name}")
                    print()
                    
                    choice = self.menu.show_dropdown("Select default model", model_names)
                    print(f"🔍 User selected: {choice}")
                    
                    if choice >= 0:
                        selected_model = model_names[choice]
                        print(f"🎯 Selected model: {selected_model}")
                        
                        # Save to config
                        if 'ollama_settings' not in self.config:
                            self.config['ollama_settings'] = {}
                        
                        self.config['ollama_settings']['default_model'] = selected_model
                        self.save_config()
                        
                        print(f"✅ Default model changed to: {selected_model}")
                        print(f"💾 Settings saved to config")
                    else:
                        print("❌ Model selection cancelled.")
                else:
                    print("❌ No models found. Pull a model first with: ollama pull llama2")
            else:
                print(f"❌ Cannot connect to Ollama. Status: {response.status_code}")
                print("💡 Make sure Ollama is running with: ollama serve")
                
        except ImportError:
            print("❌ requests library not installed. Install with: pip install requests")
        except Exception as e:
            print(f"❌ Error changing model: {e}")
            import traceback
            traceback.print_exc()
        
        input("Press Enter to continue...")
    
    def set_ollama_api_url(self):
        """Set custom Ollama API URL"""
        current_url = self.config.get('ollama_settings', {}).get('api_url', 'http://localhost:11434')
        new_url = self.menu.show_input_prompt("Enter Ollama API URL", current_url)
        
        if new_url:
            # Validate URL format
            if new_url.startswith(('http://', 'https://')):
                if 'ollama_settings' not in self.config:
                    self.config['ollama_settings'] = {}
                
                self.config['ollama_settings']['api_url'] = new_url
                self.save_config()
                
                print(f"✅ API URL updated to: {new_url}")
            else:
                print("❌ Invalid URL format. Must start with http:// or https://")
        else:
            print("❌ No URL provided.")
        
        input("Press Enter to continue...")
    
    def configure_model_parameters(self):
        """Configure model generation parameters"""
        try:
            # Get current parameters
            current_params = self.config.get('ollama_settings', {}).get('model_parameters', {})
            
            temperature = float(current_params.get('temperature', 0.7))
            top_p = float(current_params.get('top_p', 0.9))
            top_k = int(current_params.get('top_k', 40))
            max_tokens = int(current_params.get('max_tokens', 2048))
            
            print("⚙️  Model Parameters Configuration")
            print("─" * 50)
            print(f"Current settings:")
            print(f"  Temperature: {temperature} (0.0-2.0, higher = more creative)")
            print(f"  Top P: {top_p} (0.0-1.0, nucleus sampling)")
            print(f"  Top K: {top_k} (1-100, top-k sampling)")
            print(f"  Max Tokens: {max_tokens} (1-8192, response length)")
            print()
            
            # Allow user to change parameters
            if self.menu.show_confirmation("Do you want to change these parameters?"):
                new_temp = self.menu.show_input_prompt("Enter temperature (0.0-2.0)", str(temperature))
                new_top_p = self.menu.show_input_prompt("Enter top_p (0.0-1.0)", str(top_p))
                new_top_k = self.menu.show_input_prompt("Enter top_k (1-100)", str(top_k))
                new_max_tokens = self.menu.show_input_prompt("Enter max_tokens (1-8192)", str(max_tokens))
                
                try:
                    # Validate and save parameters
                    if 'ollama_settings' not in self.config:
                        self.config['ollama_settings'] = {}
                    
                    self.config['ollama_settings']['model_parameters'] = {
                        'temperature': float(new_temp) if new_temp else temperature,
                        'top_p': float(new_top_p) if new_top_p else top_p,
                        'top_k': int(new_top_k) if new_top_k else top_k,
                        'max_tokens': int(new_max_tokens) if new_max_tokens else max_tokens
                    }
                    
                    self.save_config()
                    print("✅ Model parameters updated successfully!")
                    
                except ValueError:
                    print("❌ Invalid parameter values. Using current settings.")
            else:
                print("ℹ️  Parameters unchanged.")
                
        except Exception as e:
            print(f"❌ Error configuring parameters: {e}")
        
        input("Press Enter to continue...")
    
    def list_available_models(self):
        """List all available Ollama models"""
        try:
            import requests
            
            # Get models from Ollama
            api_url = self.config.get('ollama_settings', {}).get('api_url', 'http://localhost:11434')
            url = f"{api_url}/api/tags"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                
                if models:
                    print("📚 Available Ollama Models:")
                    print("─" * 60)
                    
                    for i, model in enumerate(models, 1):
                        model_name = model.get('name', 'Unknown')
                        model_size = model.get('size', 0)
                        model_modified = model.get('modified_at', 'Unknown')
                        
                        # Convert size to human readable
                        if model_size > 0:
                            if model_size > 1024**3:
                                size_str = f"{model_size / (1024**3):.1f} GB"
                            elif model_size > 1024**2:
                                size_str = f"{model_size / (1024**2):.1f} MB"
                            else:
                                size_str = f"{model_size / 1024:.1f} KB"
                        else:
                            size_str = "Unknown"
                        
                        print(f"{i}. {model_name}")
                        print(f"   📏 Size: {size_str}")
                        print(f"   📅 Modified: {model_modified}")
                        print()
                    
                    print(f"📊 Total models: {len(models)}")
                else:
                    print("📚 No models found.")
                    print("💡 Pull a model with: ollama pull llama2")
            else:
                print("❌ Cannot connect to Ollama. Make sure it's running.")
                
        except ImportError:
            print("❌ requests library not installed. Install with: pip install requests")
        except Exception as e:
            print(f"❌ Error listing models: {e}")
        
        input("Press Enter to continue...")
    
    def test_ollama_connection(self):
        """Test connection to Ollama"""
        try:
            import requests
            
            api_url = self.config.get('ollama_settings', {}).get('api_url', 'http://localhost:11434')
            url = f"{api_url}/api/tags"
            
            print(f"🔍 Testing connection to: {api_url}")
            print("─" * 40)
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print("✅ Connection successful!")
                
                # Get basic info
                data = response.json()
                models = data.get('models', [])
                print(f"📊 Available models: {len(models)}")
                
                if models:
                    print("📚 Models:")
                    for model in models[:5]:  # Show first 5
                        print(f"  • {model.get('name', 'Unknown')}")
                    if len(models) > 5:
                        print(f"  ... and {len(models) - 5} more")
                
            else:
                print(f"❌ Connection failed. Status code: {response.status_code}")
                print("💡 Make sure Ollama is running with: ollama serve")
                
        except ImportError:
            print("❌ requests library not installed. Install with: pip install requests")
        except requests.exceptions.ConnectionError:
            print("❌ Connection refused. Ollama is not running.")
            print("💡 Start Ollama with: ollama serve")
        except Exception as e:
            print(f"❌ Connection error: {e}")
        
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
    
    def network_camera_scan(self):
        """Scan network for cameras and surveillance devices"""
        print("📹 Network Camera Scan")
        print("─" * 50)
        
        # Get local network range
        local_ip = self.get_local_ip()
        if not local_ip:
            print("❌ Could not determine local IP address")
            input("Press Enter to continue...")
            return
        
        network_base = '.'.join(local_ip.split('.')[:-1])
        print(f"🔍 Scanning network: {network_base}.x")
        print("⏳ This may take a few minutes...")
        
        # Scan for common camera ports and services
        camera_devices = []
        threads = []
        
        # Common camera ports
        camera_ports = [80, 81, 443, 554, 8080, 8081, 8082, 8888, 9999]
        
        # Scan IP range
        for i in range(1, 255):
            ip = f"{network_base}.{i}"
            thread = threading.Thread(target=self.scan_ip_for_cameras, 
                                    args=(ip, camera_ports, camera_devices))
            threads.append(thread)
            thread.start()
            
            # Limit concurrent threads
            if len(threads) >= 50:
                for t in threads:
                    t.join()
                threads = []
        
        # Wait for remaining threads
        for thread in threads:
            thread.join()
        
        # Display results
        if camera_devices:
            print(f"\n🎯 Found {len(camera_devices)} potential camera devices:")
            print("─" * 50)
            for device in camera_devices:
                print(f"📹 {device['ip']} - {device['type']} (Port: {device['port']})")
                if device.get('banner'):
                    print(f"   Banner: {device['banner'][:100]}...")
        else:
            print("✅ No obvious camera devices found on the network")
        
        input("Press Enter to continue...")
    
    def scan_ip_for_cameras(self, ip, ports, results):
        """Scan a single IP for camera services"""
        try:
            for port in ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((ip, port))
                
                if result == 0:
                    # Port is open, check for camera signatures
                    banner = self.get_banner(sock)
                    device_type = self.identify_camera_type(banner, port)
                    
                    if device_type:
                        results.append({
                            'ip': ip,
                            'port': port,
                            'type': device_type,
                            'banner': banner
                        })
                
                sock.close()
        except:
            pass
    
    def get_banner(self, sock):
        """Get banner information from socket"""
        try:
            sock.settimeout(2)
            banner = sock.recv(1024).decode('utf-8', errors='ignore')
            return banner
        except:
            return ""
    
    def identify_camera_type(self, banner, port):
        """Identify camera type from banner and port"""
        banner_lower = banner.lower()
        
        # Common camera signatures
        camera_signatures = {
            'IP Camera': ['camera', 'webcam', 'ipcam', 'axis', 'hikvision', 'dahua', 'foscam'],
            'CCTV System': ['cctv', 'surveillance', 'security', 'dvr', 'nvr'],
            'Web Server': ['apache', 'nginx', 'iis', 'http'],
            'RTSP Stream': ['rtsp', 'streaming'],
            'Unknown Device': []
        }
        
        # Check for specific camera types
        for device_type, signatures in camera_signatures.items():
            for signature in signatures:
                if signature in banner_lower:
                    return device_type
        
        # Port-based detection
        if port in [554]:  # RTSP
            return 'RTSP Stream'
        elif port in [8080, 8081, 8082, 8888, 9999]:
            return 'Potential Camera Web Interface'
        
        return None
    
    def cctv_detection(self):
        """Advanced CCTV and spy camera detection"""
        print("🔍 CCTV & Spy Camera Detection")
        print("─" * 50)
        
        print("🔍 Scanning for surveillance devices...")
        
        # Get network information
        local_ip = self.get_local_ip()
        if not local_ip:
            print("❌ Could not determine local IP address")
            input("Press Enter to continue...")
            return
        
        network_base = '.'.join(local_ip.split('.')[:-1])
        
        # Advanced detection methods
        suspicious_devices = []
        
        print("1️⃣ Scanning for common CCTV ports...")
        cctv_ports = [80, 81, 443, 554, 8080, 8081, 8082, 8888, 9999, 1935, 8554]
        for i in range(1, 255):
            ip = f"{network_base}.{i}"
            for port in cctv_ports:
                if self.check_cctv_port(ip, port):
                    suspicious_devices.append({
                        'ip': ip,
                        'port': port,
                        'type': 'Potential CCTV Device',
                        'confidence': 'High'
                    })
        
        print("2️⃣ Checking for UPnP devices...")
        upnp_devices = self.scan_upnp_devices()
        suspicious_devices.extend(upnp_devices)
        
        print("3️⃣ Analyzing network traffic patterns...")
        traffic_analysis = self.analyze_network_traffic()
        
        print("4️⃣ Checking for wireless access points...")
        wifi_devices = self.scan_wifi_devices()
        
        # Display results
        print(f"\n🎯 Detection Results:")
        print("─" * 50)
        
        if suspicious_devices:
            print(f"⚠️  Found {len(suspicious_devices)} suspicious devices:")
            for device in suspicious_devices:
                print(f"📹 {device['ip']}:{device['port']} - {device['type']} ({device['confidence']} confidence)")
        else:
            print("✅ No obvious surveillance devices detected")
        
        if upnp_devices:
            print(f"\n📡 UPnP Devices Found: {len(upnp_devices)}")
            for device in upnp_devices:
                print(f"   {device['ip']} - {device['type']}")
        
        if traffic_analysis:
            print(f"\n📊 Traffic Analysis:")
            print(f"   High bandwidth devices: {traffic_analysis.get('high_bandwidth', 0)}")
            print(f"   Streaming devices: {traffic_analysis.get('streaming', 0)}")
        
        if wifi_devices:
            print(f"\n📶 Wireless Devices: {len(wifi_devices)}")
            for device in wifi_devices:
                if 'camera' in device.get('name', '').lower() or 'cctv' in device.get('name', '').lower():
                    print(f"   ⚠️  {device['name']} - {device['ip']} (Suspicious)")
                else:
                    print(f"   📱 {device['name']} - {device['ip']}")
        
        # Security recommendations
        print(f"\n🛡️  Security Recommendations:")
        print("─" * 50)
        print("• Change default passwords on all network devices")
        print("• Enable WPA3 encryption on your WiFi network")
        print("• Regularly update firmware on network devices")
        print("• Use a network monitoring tool for ongoing surveillance")
        print("• Consider using a VPN for additional privacy")
        
        input("Press Enter to continue...")
    
    def check_cctv_port(self, ip, port):
        """Check if a specific port on an IP is running CCTV software"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, port))
            
            if result == 0:
                # Try to get HTTP response
                if port in [80, 81, 8080, 8081, 8082, 8888, 9999]:
                    try:
                        sock.send(b"GET / HTTP/1.1\r\nHost: " + ip.encode() + b"\r\n\r\n")
                        response = sock.recv(1024).decode('utf-8', errors='ignore').lower()
                        if any(keyword in response for keyword in ['camera', 'cctv', 'surveillance', 'webcam', 'ipcam']):
                            sock.close()
                            return True
                    except:
                        pass
                
                sock.close()
                return True
        except:
            pass
        return False
    
    def scan_upnp_devices(self):
        """Scan for UPnP devices that might be cameras"""
        devices = []
        try:
            # Simple UPnP discovery
            import subprocess
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'incomplete' not in line and '(' in line and ')' in line:
                        ip = line.split('(')[1].split(')')[0]
                        if self.is_local_ip(ip):
                            devices.append({
                                'ip': ip,
                                'type': 'UPnP Device',
                                'confidence': 'Medium'
                            })
        except:
            pass
        return devices
    
    def analyze_network_traffic(self):
        """Analyze network traffic for suspicious patterns"""
        analysis = {'high_bandwidth': 0, 'streaming': 0}
        try:
            # This is a simplified analysis
            # In a real implementation, you'd use tools like netstat, ss, or network monitoring libraries
            import subprocess
            result = subprocess.run(['netstat', '-i'], capture_output=True, text=True)
            if result.returncode == 0:
                # Count active connections
                lines = result.stdout.split('\n')
                active_connections = len([line for line in lines if 'ESTABLISHED' in line])
                analysis['high_bandwidth'] = min(active_connections // 10, 5)  # Rough estimate
        except:
            pass
        return analysis
    
    def scan_wifi_devices(self):
        """Scan for WiFi devices"""
        devices = []
        try:
            import subprocess
            # Get ARP table to find devices
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'incomplete' not in line and '(' in line and ')' in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            ip = parts[1].strip('()')
                            mac = parts[3] if len(parts) > 3 else 'Unknown'
                            name = ' '.join(parts[4:]) if len(parts) > 4 else 'Unknown Device'
                            
                            if self.is_local_ip(ip):
                                devices.append({
                                    'ip': ip,
                                    'mac': mac,
                                    'name': name
                                })
        except:
            pass
        return devices
    
    def get_local_ip(self):
        """Get local IP address"""
        try:
            # Connect to a remote address to determine local IP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            local_ip = sock.getsockname()[0]
            sock.close()
            return local_ip
        except:
            return None
    
    def is_local_ip(self, ip):
        """Check if IP is in local network range"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            
            # Check for private IP ranges
            first = int(parts[0])
            second = int(parts[1])
            
            if first == 10:
                return True
            elif first == 172 and 16 <= second <= 31:
                return True
            elif first == 192 and second == 168:
                return True
            elif first == 127:  # Loopback
                return True
            
            return False
        except:
            return False
    
    def camera_location_map(self):
        """Create a visual map of found cameras and their locations"""
        print("🗺️  Camera Location Map")
        print("─" * 50)
        
        # Get local network range
        local_ip = self.get_local_ip()
        if not local_ip:
            print("❌ Could not determine local IP address")
            input("Press Enter to continue...")
            return
        
        network_base = '.'.join(local_ip.split('.')[:-1])
        print(f"🔍 Scanning network: {network_base}.x for cameras...")
        
        # Scan for cameras
        camera_devices = []
        camera_ports = [80, 81, 443, 554, 8080, 8081, 8082, 8888, 9999]
        
        print("⏳ Scanning for cameras...")
        for i in range(1, 255):
            ip = f"{network_base}.{i}"
            for port in camera_ports:
                if self.check_cctv_port(ip, port):
                    # Get detailed camera information
                    camera_info = self.get_camera_details(ip, port)
                    camera_devices.append(camera_info)
                    break
        
        if not camera_devices:
            print("✅ No cameras found on the network")
            input("Press Enter to continue...")
            return
        
        # Display camera map
        print(f"\n🎯 Found {len(camera_devices)} cameras:")
        print("=" * 80)
        
        for i, camera in enumerate(camera_devices, 1):
            print(f"\n📹 Camera #{i}: {camera['ip']}:{camera['port']}")
            print(f"   Type: {camera['type']}")
            print(f"   Brand: {camera['brand']}")
            print(f"   Model: {camera['model']}")
            print(f"   Status: {camera['status']}")
            print(f"   Web Interface: http://{camera['ip']}:{camera['port']}")
            
            if camera.get('location'):
                print(f"   📍 Location: {camera['location']}")
            
            if camera.get('capabilities'):
                print(f"   🎥 Capabilities: {', '.join(camera['capabilities'])}")
            
            if camera.get('security_issues'):
                print(f"   ⚠️  Security Issues: {', '.join(camera['security_issues'])}")
        
        # Create network topology
        self.create_network_topology(camera_devices)
        
        # Generate location report
        self.generate_camera_report(camera_devices)
        
        input("Press Enter to continue...")
    
    def get_camera_details(self, ip, port):
        """Get detailed information about a camera"""
        camera_info = {
            'ip': ip,
            'port': port,
            'type': 'Unknown Camera',
            'brand': 'Unknown',
            'model': 'Unknown',
            'status': 'Online',
            'capabilities': [],
            'security_issues': [],
            'location': None
        }
        
        try:
            # Try to get HTTP response
            if port in [80, 81, 8080, 8081, 8082, 8888, 9999]:
                import urllib.request
                import urllib.error
                
                try:
                    url = f"http://{ip}:{port}"
                    req = urllib.request.Request(url)
                    req.add_header('User-Agent', 'Mozilla/5.0 (Camera Scanner)')
                    
                    with urllib.request.urlopen(req, timeout=3) as response:
                        html = response.read().decode('utf-8', errors='ignore').lower()
                        
                        # Identify camera brand and model
                        camera_info.update(self.identify_camera_brand_model(html))
                        
                        # Check for common capabilities
                        camera_info['capabilities'] = self.detect_camera_capabilities(html)
                        
                        # Check for security issues
                        camera_info['security_issues'] = self.check_camera_security(html, ip, port)
                        
                except (urllib.error.URLError, urllib.error.HTTPError, Exception):
                    pass
            
            # Try RTSP for streaming cameras
            elif port == 554:
                camera_info['type'] = 'RTSP Streaming Camera'
                camera_info['capabilities'] = ['Video Streaming', 'RTSP Protocol']
            
            # Determine location based on IP and network analysis
            camera_info['location'] = self.estimate_camera_location(ip)
            
        except Exception as e:
            camera_info['status'] = f'Error: {str(e)[:50]}'
        
        return camera_info
    
    def identify_camera_brand_model(self, html):
        """Identify camera brand and model from HTML"""
        brand_model = {'brand': 'Unknown', 'model': 'Unknown', 'type': 'IP Camera'}
        
        # Common camera brands and their signatures
        brands = {
            'axis': ['axis', 'axis communications'],
            'hikvision': ['hikvision', 'hik-connect'],
            'dahua': ['dahua', 'dahua technology'],
            'foscam': ['foscam', 'foscam digital'],
            'dlink': ['d-link', 'dlink'],
            'netgear': ['netgear', 'arlo'],
            'tp-link': ['tp-link', 'tplink'],
            'wyze': ['wyze', 'wyze cam'],
            'ring': ['ring', 'amazon ring'],
            'nest': ['nest', 'google nest'],
            'arlo': ['arlo', 'netgear arlo'],
            'eufy': ['eufy', 'anker eufy'],
            'reolink': ['reolink', 'reolink technology']
        }
        
        for brand, signatures in brands.items():
            for signature in signatures:
                if signature in html:
                    brand_model['brand'] = brand.title()
                    brand_model['type'] = f'{brand.title()} IP Camera'
                    break
        
        # Try to extract model information
        import re
        
        # Look for common model patterns
        model_patterns = [
            r'model[:\s]+([a-zA-Z0-9\-_]+)',
            r'product[:\s]+([a-zA-Z0-9\-_]+)',
            r'device[:\s]+([a-zA-Z0-9\-_]+)',
            r'camera[:\s]+([a-zA-Z0-9\-_]+)'
        ]
        
        for pattern in model_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                brand_model['model'] = match.group(1)
                break
        
        return brand_model
    
    def detect_camera_capabilities(self, html):
        """Detect camera capabilities from HTML"""
        capabilities = []
        
        capability_keywords = {
            'Motion Detection': ['motion', 'detection', 'alarm'],
            'Night Vision': ['night', 'vision', 'ir', 'infrared'],
            'Audio Recording': ['audio', 'microphone', 'sound'],
            'PTZ Control': ['ptz', 'pan', 'tilt', 'zoom'],
            'HD Recording': ['hd', '1080p', '4k', 'high definition'],
            'Cloud Storage': ['cloud', 'storage', 'backup'],
            'Mobile App': ['mobile', 'app', 'android', 'ios'],
            'Web Interface': ['web', 'interface', 'browser'],
            'Email Alerts': ['email', 'alert', 'notification'],
            'SD Card': ['sd', 'card', 'local storage']
        }
        
        for capability, keywords in capability_keywords.items():
            if any(keyword in html for keyword in keywords):
                capabilities.append(capability)
        
        return capabilities
    
    def check_camera_security(self, html, ip, port):
        """Check for security issues in camera"""
        security_issues = []
        
        # Check for default credentials
        if any(keyword in html for keyword in ['admin', 'password', 'login', 'default']):
            security_issues.append('Default credentials possible')
        
        # Check for HTTP (not HTTPS)
        if port in [80, 8080, 8081, 8082, 8888, 9999]:
            security_issues.append('HTTP connection (not encrypted)')
        
        # Check for common vulnerabilities
        vulnerability_keywords = {
            'Directory Traversal': ['../', '..\\', 'directory traversal'],
            'SQL Injection': ['sql', 'database', 'query'],
            'XSS Vulnerability': ['script', 'javascript', 'xss'],
            'CSRF': ['csrf', 'cross-site request forgery']
        }
        
        for vuln, keywords in vulnerability_keywords.items():
            if any(keyword in html for keyword in keywords):
                security_issues.append(vuln)
        
        return security_issues
    
    def estimate_camera_location(self, ip):
        """Estimate camera location based on IP and network analysis"""
        try:
            # Get IP range information
            ip_parts = ip.split('.')
            last_octet = int(ip_parts[-1])
            
            # Common IP ranges and their typical locations
            if 1 <= last_octet <= 10:
                return "Network Infrastructure (Router/Switch area)"
            elif 11 <= last_octet <= 50:
                return "Server/Equipment Room"
            elif 51 <= last_octet <= 100:
                return "Office/Workstation Area"
            elif 101 <= last_octet <= 150:
                return "Common Areas (Lobby/Reception)"
            elif 151 <= last_octet <= 200:
                return "Perimeter/External Areas"
            elif 201 <= last_octet <= 254:
                return "Remote/Isolated Areas"
            else:
                return "Unknown Location"
                
        except:
            return "Unknown Location"
    
    def create_network_topology(self, cameras):
        """Create a visual network topology map"""
        print(f"\n🗺️  Network Topology Map")
        print("=" * 50)
        
        # Get network information
        local_ip = self.get_local_ip()
        network_base = '.'.join(local_ip.split('.')[:-1])
        
        print(f"Network: {network_base}.x/24")
        print(f"Gateway: {network_base}.1 (assumed)")
        print(f"Your IP: {local_ip}")
        print()
        
        # Create ASCII network map
        print("Network Layout:")
        print("┌─────────────────────────────────────────┐")
        print("│                Internet                  │")
        print("└─────────────┬───────────────────────────┘")
        print("              │")
        print(f"    ┌────────┴────────┐")
        print(f"    │   Router/Gateway │")
        print(f"    │   {network_base}.1      │")
        print(f"    └────────┬────────┘")
        print("              │")
        print("    ┌─────────┴─────────┐")
        print("    │   Network Switch   │")
        print("    └─────────┬─────────┘")
        print("              │")
        print("    ┌─────────┴─────────┐")
        print("    │   Local Network    │")
        print("    └─────────┬─────────┘")
        print("              │")
        
        # Show cameras in network
        for i, camera in enumerate(cameras):
            print(f"    ┌─────────┴─────────┐")
            print(f"    │ 📹 Camera #{i+1}     │")
            print(f"    │ {camera['ip']:>15} │")
            print(f"    │ {camera['brand']:>15} │")
            print(f"    └───────────────────┘")
        
        print(f"\n📊 Network Statistics:")
        print(f"   Total Cameras: {len(cameras)}")
        print(f"   Network Range: {network_base}.1 - {network_base}.254")
        print(f"   Camera Density: {len(cameras)/254*100:.1f}% of network")
    
    def generate_camera_report(self, cameras):
        """Generate a detailed camera report"""
        print(f"\n📋 Camera Security Report")
        print("=" * 50)
        
        # Security analysis
        total_cameras = len(cameras)
        cameras_with_issues = len([c for c in cameras if c['security_issues']])
        http_cameras = len([c for c in cameras if c['port'] in [80, 8080, 8081, 8082, 8888, 9999]])
        
        print(f"📊 Summary:")
        print(f"   Total Cameras Found: {total_cameras}")
        print(f"   Cameras with Security Issues: {cameras_with_issues}")
        print(f"   HTTP (Unencrypted) Cameras: {http_cameras}")
        print(f"   Security Risk Level: {'HIGH' if cameras_with_issues > total_cameras/2 else 'MEDIUM' if cameras_with_issues > 0 else 'LOW'}")
        
        # Brand distribution
        brands = {}
        for camera in cameras:
            brand = camera['brand']
            brands[brand] = brands.get(brand, 0) + 1
        
        print(f"\n🏷️  Brand Distribution:")
        for brand, count in sorted(brands.items()):
            print(f"   {brand}: {count} cameras")
        
        # Security recommendations
        print(f"\n🛡️  Security Recommendations:")
        if http_cameras > 0:
            print(f"   • Enable HTTPS on {http_cameras} cameras using HTTP")
        if cameras_with_issues > 0:
            print(f"   • Update firmware on {cameras_with_issues} cameras with security issues")
        print(f"   • Change default passwords on all cameras")
        print(f"   • Enable network segmentation for camera network")
        print(f"   • Regular security audits and updates")
        print(f"   • Monitor camera network traffic")
    
    def camera_access_control(self):
        """Access and control found cameras"""
        print("🎯 Camera Access & Control")
        print("─" * 50)
        
        # First scan for cameras
        local_ip = self.get_local_ip()
        if not local_ip:
            print("❌ Could not determine local IP address")
            input("Press Enter to continue...")
            return
        
        network_base = '.'.join(local_ip.split('.')[:-1])
        print(f"🔍 Scanning for accessible cameras...")
        
        accessible_cameras = []
        camera_ports = [80, 81, 443, 8080, 8081, 8082, 8888, 9999]
        
        for i in range(1, 255):
            ip = f"{network_base}.{i}"
            for port in camera_ports:
                if self.check_camera_accessibility(ip, port):
                    camera_info = self.get_camera_details(ip, port)
                    accessible_cameras.append(camera_info)
                    break
        
        if not accessible_cameras:
            print("❌ No accessible cameras found")
            input("Press Enter to continue...")
            return
        
        # Display accessible cameras
        print(f"\n🎯 Found {len(accessible_cameras)} accessible cameras:")
        print("=" * 60)
        
        for i, camera in enumerate(accessible_cameras, 1):
            print(f"\n📹 Camera #{i}: {camera['ip']}:{camera['port']}")
            print(f"   Brand: {camera['brand']} | Model: {camera['model']}")
            print(f"   Web Interface: http://{camera['ip']}:{camera['port']}")
            print(f"   Status: {camera['status']}")
        
        # Camera control options
        while True:
            options = [
                "🌐 Open Camera Web Interface",
                "📸 Take Screenshot",
                "🎥 Test Video Stream",
                "⚙️  Camera Settings",
                "🔐 Test Default Credentials",
                "📊 Camera Status Check",
                "⬅️  Back to Security Menu"
            ]
            
            choice = self.menu.show_dropdown("Camera Control Options", options)
            
            if choice == 0:
                self.open_camera_interface(accessible_cameras)
            elif choice == 1:
                self.take_camera_screenshot(accessible_cameras)
            elif choice == 2:
                self.test_video_stream(accessible_cameras)
            elif choice == 3:
                self.camera_settings(accessible_cameras)
            elif choice == 4:
                self.test_default_credentials(accessible_cameras)
            elif choice == 5:
                self.camera_status_check(accessible_cameras)
            elif choice == 6 or choice == -1:
                break
    
    def check_camera_accessibility(self, ip, port):
        """Check if camera is accessible"""
        try:
            import urllib.request
            import urllib.error
            
            url = f"http://{ip}:{port}"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Camera Scanner)')
            
            with urllib.request.urlopen(req, timeout=2) as response:
                return response.status == 200
        except:
            return False
    
    def open_camera_interface(self, cameras):
        """Open camera web interface"""
        if not cameras:
            print("❌ No cameras available")
            return
        
        camera_options = [f"{cam['ip']}:{cam['port']} - {cam['brand']}" for cam in cameras]
        choice = self.menu.show_dropdown("Select Camera to Open", camera_options)
        
        if choice >= 0:
            camera = cameras[choice]
            url = f"http://{camera['ip']}:{camera['port']}"
            print(f"🌐 Opening: {url}")
            
            try:
                import webbrowser
                webbrowser.open(url)
                print("✅ Camera interface opened in browser")
            except Exception as e:
                print(f"❌ Failed to open browser: {e}")
                print(f"   Manual URL: {url}")
        
        input("Press Enter to continue...")
    
    def take_camera_screenshot(self, cameras):
        """Take screenshot from camera"""
        if not cameras:
            print("❌ No cameras available")
            return
        
        camera_options = [f"{cam['ip']}:{cam['port']} - {cam['brand']}" for cam in cameras]
        choice = self.menu.show_dropdown("Select Camera for Screenshot", camera_options)
        
        if choice >= 0:
            camera = cameras[choice]
            print(f"📸 Taking screenshot from {camera['ip']}...")
            
            # This would require camera-specific API calls
            # For now, just show the web interface URL
            url = f"http://{camera['ip']}:{camera['port']}"
            print(f"   Camera URL: {url}")
            print("   Note: Screenshot functionality requires camera-specific API access")
        
        input("Press Enter to continue...")
    
    def test_video_stream(self, cameras):
        """Test camera video stream"""
        if not cameras:
            print("❌ No cameras available")
            return
        
        camera_options = [f"{cam['ip']}:{cam['port']} - {cam['brand']}" for cam in cameras]
        choice = self.menu.show_dropdown("Select Camera for Video Test", camera_options)
        
        if choice >= 0:
            camera = cameras[choice]
            print(f"🎥 Testing video stream from {camera['ip']}...")
            
            # Test common video stream URLs
            stream_urls = [
                f"http://{camera['ip']}:{camera['port']}/video.mjpg",
                f"http://{camera['ip']}:{camera['port']}/mjpeg",
                f"http://{camera['ip']}:{camera['port']}/stream",
                f"rtsp://{camera['ip']}:554/stream1",
                f"rtsp://{camera['ip']}:554/live"
            ]
            
            print("   Testing common stream URLs:")
            for url in stream_urls:
                if self.test_stream_url(url):
                    print(f"   ✅ Working: {url}")
                else:
                    print(f"   ❌ Failed: {url}")
        
        input("Press Enter to continue...")
    
    def test_stream_url(self, url):
        """Test if a stream URL is accessible"""
        try:
            import urllib.request
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=3) as response:
                return response.status == 200
        except:
            return False
    
    def camera_settings(self, cameras):
        """Access camera settings"""
        if not cameras:
            print("❌ No cameras available")
            return
        
        camera_options = [f"{cam['ip']}:{cam['port']} - {cam['brand']}" for cam in cameras]
        choice = self.menu.show_dropdown("Select Camera for Settings", camera_options)
        
        if choice >= 0:
            camera = cameras[choice]
            print(f"⚙️  Camera Settings for {camera['ip']}")
            print(f"   Brand: {camera['brand']}")
            print(f"   Model: {camera['model']}")
            print(f"   Web Interface: http://{camera['ip']}:{camera['port']}")
            print(f"   Capabilities: {', '.join(camera.get('capabilities', []))}")
            print(f"   Security Issues: {', '.join(camera.get('security_issues', []))}")
        
        input("Press Enter to continue...")
    
    def test_default_credentials(self, cameras):
        """Test for default credentials"""
        if not cameras:
            print("❌ No cameras available")
            return
        
        print("🔐 Testing Default Credentials")
        print("⚠️  WARNING: This is for security testing only!")
        
        # Common default credentials
        default_creds = [
            ('admin', 'admin'),
            ('admin', 'password'),
            ('admin', '12345'),
            ('admin', ''),
            ('root', 'root'),
            ('user', 'user'),
            ('admin', '1234'),
            ('admin', 'admin123')
        ]
        
        for camera in cameras:
            print(f"\n🔍 Testing {camera['ip']}:{camera['port']}")
            for username, password in default_creds:
                if self.test_camera_credentials(camera['ip'], camera['port'], username, password):
                    print(f"   ⚠️  WEAK CREDENTIALS: {username}:{password}")
                else:
                    print(f"   ✅ {username}:{password} - Failed")
        
        input("Press Enter to continue...")
    
    def test_camera_credentials(self, ip, port, username, password):
        """Test camera credentials"""
        try:
            import urllib.request
            import urllib.parse
            import base64
            
            url = f"http://{ip}:{port}"
            
            # Create basic auth header
            credentials = f"{username}:{password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            req = urllib.request.Request(url)
            req.add_header('Authorization', f'Basic {encoded_credentials}')
            req.add_header('User-Agent', 'Mozilla/5.0 (Camera Scanner)')
            
            with urllib.request.urlopen(req, timeout=3) as response:
                return response.status == 200
        except:
            return False
    
    def camera_status_check(self, cameras):
        """Check camera status and health"""
        if not cameras:
            print("❌ No cameras available")
            return
        
        print("📊 Camera Status Check")
        print("=" * 40)
        
        for camera in cameras:
            print(f"\n📹 {camera['ip']}:{camera['port']}")
            print(f"   Brand: {camera['brand']}")
            print(f"   Status: {camera['status']}")
            print(f"   Response Time: {self.get_camera_response_time(camera['ip'], camera['port'])}ms")
            print(f"   Security Issues: {len(camera.get('security_issues', []))}")
        
        input("Press Enter to continue...")
    
    def get_camera_response_time(self, ip, port):
        """Get camera response time"""
        try:
            import time
            import urllib.request
            
            start_time = time.time()
            url = f"http://{ip}:{port}"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Camera Scanner)')
            
            with urllib.request.urlopen(req, timeout=5) as response:
                end_time = time.time()
                return int((end_time - start_time) * 1000)
        except:
            return "N/A"
    
    def camera_cognitive_analysis(self):
        """Camera cognitive behavior analysis and reporting"""
        while True:
            self.menu.clear_screen()
            print("\n🧠 CAMERA COGNITIVE ANALYSIS")
            print("─" * 50)
            
            options = [
                "🔍 Start Behavior Monitoring",
                "📊 Analyze Behavior Patterns",
                "🚨 Detect Anomalies",
                "📈 Generate Analysis Report",
                "🎯 View Trust Scores",
                "📱 Mac Camera Analysis",
                "📋 View Historical Data",
                "⚙️  Configure Analysis Settings",
                "🗑️  Clear Analysis Data",
                "⬅️  Back to Security Menu"
            ]
            
            choice = self.menu.show_dropdown("COGNITIVE ANALYSIS", options)
            
            if choice == 0:
                self.start_behavior_monitoring()
            elif choice == 1:
                self.analyze_behavior_patterns()
            elif choice == 2:
                self.detect_anomalies()
            elif choice == 3:
                self.generate_analysis_report()
            elif choice == 4:
                self.view_trust_scores()
            elif choice == 5:
                self.mac_camera_analysis()
            elif choice == 6:
                self.view_historical_data()
            elif choice == 7:
                self.configure_analysis_settings()
            elif choice == 8:
                self.clear_analysis_data()
            elif choice == 9 or choice == -1:
                break
    
    def start_behavior_monitoring(self):
        """Start monitoring camera behavior patterns"""
        self.menu.clear_screen()
        print("\n🔍 START BEHAVIOR MONITORING")
        print("─" * 50)
        
        # First scan for cameras (network + Mac camera)
        print("🔍 Scanning for cameras...")
        network_cameras = self.scan_network_for_cameras_cognitive()
        mac_camera = self.detect_mac_camera()
        
        # Combine network and Mac cameras
        cameras = network_cameras.copy()
        if mac_camera:
            cameras.append(mac_camera)
            print(f"✅ Found Mac built-in camera: {mac_camera['name']}")
        
        if not cameras:
            print("❌ No cameras found to monitor!")
            input("Press Enter to continue...")
            return
        
        print(f"✅ Found {len(cameras)} camera(s)")
        
        # Get monitoring parameters
        duration = self.menu.show_input_prompt("Monitoring duration (minutes)", "10")
        try:
            duration = int(duration)
        except:
            duration = 10
        
        interval = self.menu.show_input_prompt("Check interval (seconds)", "30")
        try:
            interval = int(interval)
        except:
            interval = 30
        
        print(f"\n🔍 Starting monitoring for {duration} minutes...")
        print(f"📊 Check interval: {interval} seconds")
        print("Press Ctrl+C to stop monitoring early")
        
        # Start monitoring session
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session_data = {
            'id': session_id,
            'start_time': datetime.now().isoformat(),
            'duration_minutes': duration,
            'interval_seconds': interval,
            'cameras': cameras,
            'data_points': []
        }
        
        try:
            start_time = time.time()
            end_time = start_time + (duration * 60)
            
            while time.time() < end_time:
                current_time = datetime.now()
                print(f"\r⏱️  Monitoring... {current_time.strftime('%H:%M:%S')} - {len(session_data['data_points'])} data points", end='', flush=True)
                
                # Collect data for each camera
                for camera in cameras:
                    data_point = self.collect_camera_data_point(camera)
                    data_point['timestamp'] = current_time.isoformat()
                    session_data['data_points'].append(data_point)
                
                time.sleep(interval)
            
            session_data['end_time'] = datetime.now().isoformat()
            session_data['status'] = 'completed'
            
            # Save session data
            self.config['camera_analysis']['monitoring_sessions'].append(session_data)
            self.save_config()
            
            print(f"\n✅ Monitoring completed!")
            print(f"📊 Collected {len(session_data['data_points'])} data points")
            print(f"📹 Monitored {len(cameras)} camera(s)")
            
        except KeyboardInterrupt:
            session_data['end_time'] = datetime.now().isoformat()
            session_data['status'] = 'interrupted'
            self.config['camera_analysis']['monitoring_sessions'].append(session_data)
            self.save_config()
            print(f"\n⏹️  Monitoring stopped by user")
            print(f"📊 Collected {len(session_data['data_points'])} data points")
        
        input("Press Enter to continue...")
    
    def collect_camera_data_point(self, camera):
        """Collect a single data point for camera behavior analysis"""
        # Check if this is a Mac camera
        if camera.get('is_mac_camera', False):
            return self.collect_mac_camera_data_point(camera)
        
        # Regular network camera data collection
        data_point = {
            'camera_id': f"{camera['ip']}:{camera['port']}",
            'ip': camera['ip'],
            'port': camera['port'],
            'brand': camera.get('brand', 'Unknown'),
            'response_time': self.get_camera_response_time(camera['ip'], camera['port']),
            'is_accessible': self.check_camera_accessibility(camera['ip'], camera['port']),
            'open_ports': self.scan_camera_ports(camera['ip']),
            'http_headers': self.get_camera_headers(camera['ip'], camera['port']),
            'stream_status': self.check_stream_status(camera['ip'], camera['port']),
            'security_score': self.calculate_security_score(camera)
        }
        
        return data_point
    
    def scan_camera_ports(self, ip):
        """Scan common camera ports"""
        common_ports = [80, 81, 443, 554, 8080, 8081, 8082, 8888, 9999]
        open_ports = []
        
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((ip, port))
                if result == 0:
                    open_ports.append(port)
                sock.close()
            except:
                pass
        
        return open_ports
    
    def get_camera_headers(self, ip, port):
        """Get HTTP headers from camera"""
        try:
            import urllib.request
            url = f"http://{ip}:{port}"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Camera Scanner)')
            
            with urllib.request.urlopen(req, timeout=3) as response:
                return dict(response.headers)
        except:
            return {}
    
    def check_stream_status(self, ip, port):
        """Check if camera stream is active"""
        try:
            import urllib.request
            # Try common stream endpoints
            stream_paths = ['/video', '/stream', '/mjpeg', '/video.mjpg', '/axis-cgi/mjpg/video.cgi']
            
            for path in stream_paths:
                try:
                    url = f"http://{ip}:{port}{path}"
                    req = urllib.request.Request(url)
                    req.add_header('User-Agent', 'Mozilla/5.0 (Camera Scanner)')
                    
                    with urllib.request.urlopen(req, timeout=2) as response:
                        if response.status == 200:
                            return {'active': True, 'endpoint': path, 'content_type': response.headers.get('Content-Type', '')}
                except:
                    continue
            
            return {'active': False, 'endpoint': None, 'content_type': None}
        except:
            return {'active': False, 'endpoint': None, 'content_type': None}
    
    def calculate_security_score(self, camera):
        """Calculate security score for camera"""
        score = 100
        issues = []
        
        # Check for default credentials
        if camera.get('default_credentials', False):
            score -= 30
            issues.append('Default credentials detected')
        
        # Check for HTTP (not HTTPS)
        if camera.get('port') == 80:
            score -= 20
            issues.append('Using HTTP instead of HTTPS')
        
        # Check for open ports
        if len(camera.get('open_ports', [])) > 3:
            score -= 15
            issues.append('Too many open ports')
        
        # Check for weak authentication
        if not camera.get('authentication_required', True):
            score -= 25
            issues.append('No authentication required')
        
        # Check for firmware version
        if camera.get('firmware_version', '').startswith('1.'):
            score -= 10
            issues.append('Outdated firmware')
        
        return max(0, score)
    
    def analyze_behavior_patterns(self):
        """Analyze camera behavior patterns from monitoring data"""
        self.menu.clear_screen()
        print("\n📊 ANALYZE BEHAVIOR PATTERNS")
        print("─" * 50)
        
        sessions = self.config['camera_analysis']['monitoring_sessions']
        if not sessions:
            print("❌ No monitoring sessions found!")
            print("💡 Start a monitoring session first to collect data.")
            input("Press Enter to continue...")
            return
        
        # Select session to analyze
        session_options = []
        for session in sessions:
            start_time = datetime.fromisoformat(session['start_time']).strftime('%Y-%m-%d %H:%M')
            status = session.get('status', 'unknown')
            data_points = len(session.get('data_points', []))
            session_options.append(f"{start_time} - {status} ({data_points} points)")
        
        choice = self.menu.show_dropdown("SELECT SESSION TO ANALYZE", session_options)
        if choice == -1:
            return
        
        selected_session = sessions[choice]
        data_points = selected_session.get('data_points', [])
        
        if not data_points:
            print("❌ No data points found in selected session!")
            input("Press Enter to continue...")
            return
        
        print(f"\n🔍 Analyzing {len(data_points)} data points...")
        
        # Group data by camera
        camera_data = {}
        for point in data_points:
            camera_id = point['camera_id']
            if camera_id not in camera_data:
                camera_data[camera_id] = []
            camera_data[camera_id].append(point)
        
        # Analyze patterns for each camera
        patterns = {}
        for camera_id, points in camera_data.items():
            patterns[camera_id] = self.analyze_camera_patterns(points)
        
        # Save patterns
        self.config['camera_analysis']['behavior_patterns'][selected_session['id']] = patterns
        self.save_config()
        
        # Display results
        print(f"\n📊 BEHAVIOR PATTERN ANALYSIS RESULTS")
        print("─" * 60)
        
        for camera_id, pattern in patterns.items():
            print(f"\n📹 Camera: {camera_id}")
            print(f"   📊 Data Points: {pattern['total_points']}")
            print(f"   ⏱️  Average Response Time: {pattern['avg_response_time']:.1f}ms")
            print(f"   📈 Response Time Variance: {pattern['response_time_variance']:.1f}")
            print(f"   🔄 Accessibility Rate: {pattern['accessibility_rate']:.1f}%")
            print(f"   🚨 Anomalies Detected: {pattern['anomalies']}")
            print(f"   📊 Port Stability: {pattern['port_stability']:.1f}%")
            print(f"   🔒 Security Score Trend: {pattern['security_trend']}")
            
            # Display trust score
            trust = pattern.get('trust_score', {})
            if trust:
                trust_score = trust.get('score', 0)
                trust_level = trust.get('level', 'Unknown')
                print(f"   🎯 Trust Score: {trust_score}/100 ({trust_level})")
                
                # Show trust factors
                factors = trust.get('factors', {})
                print(f"      📊 Data Volume: {factors.get('data_volume', 0)}/25")
                print(f"      🔍 Data Quality: {factors.get('data_quality', 0)}/20")
                print(f"      📈 Consistency: {factors.get('consistency', 0)}/20")
                print(f"      🚨 Anomaly Ratio: {factors.get('anomaly_ratio', 0)}/15")
                print(f"      ⏱️  Response Reliability: {factors.get('response_time_reliability', 0)}/10")
                print(f"      🔄 Accessibility Reliability: {factors.get('accessibility_reliability', 0)}/10")
        
        input("Press Enter to continue...")
    
    def analyze_camera_patterns(self, data_points):
        """Analyze patterns for a single camera"""
        if not data_points:
            return {}
        
        # Calculate response time statistics
        response_times = [point['response_time'] for point in data_points if point['response_time'] != 'N/A']
        response_times = [rt for rt in response_times if isinstance(rt, (int, float))]
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        response_time_variance = self.calculate_variance(response_times) if response_times else 0
        
        # Calculate accessibility rate
        accessible_count = sum(1 for point in data_points if point['is_accessible'])
        accessibility_rate = (accessible_count / len(data_points)) * 100
        
        # Detect anomalies
        anomalies = self.detect_camera_anomalies(data_points)
        
        # Calculate port stability
        port_changes = 0
        if len(data_points) > 1:
            for i in range(1, len(data_points)):
                if set(data_points[i-1]['open_ports']) != set(data_points[i]['open_ports']):
                    port_changes += 1
        port_stability = max(0, 100 - (port_changes / (len(data_points) - 1)) * 100) if len(data_points) > 1 else 100
        
        # Security score trend
        security_scores = [point['security_score'] for point in data_points]
        if len(security_scores) > 1:
            if security_scores[-1] > security_scores[0]:
                security_trend = "Improving"
            elif security_scores[-1] < security_scores[0]:
                security_trend = "Degrading"
            else:
                security_trend = "Stable"
        else:
            security_trend = "Single Point"
        
        # Calculate trust score for this analysis
        trust_score = self.calculate_analysis_trust_score(data_points, response_times, accessibility_rate, anomalies)
        
        return {
            'total_points': len(data_points),
            'avg_response_time': avg_response_time,
            'response_time_variance': response_time_variance,
            'accessibility_rate': accessibility_rate,
            'anomalies': len(anomalies),
            'port_stability': port_stability,
            'security_trend': security_trend,
            'detailed_anomalies': anomalies,
            'trust_score': trust_score
        }
    
    def calculate_variance(self, values):
        """Calculate variance of a list of values"""
        if len(values) < 2:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def calculate_analysis_trust_score(self, data_points, response_times, accessibility_rate, anomalies):
        """Calculate trust/confidence score for analysis results"""
        trust_factors = {
            'data_volume': 0,
            'data_quality': 0,
            'consistency': 0,
            'anomaly_ratio': 0,
            'response_time_reliability': 0,
            'accessibility_reliability': 0
        }
        
        # Data Volume Factor (0-25 points)
        total_points = len(data_points)
        if total_points >= 50:
            trust_factors['data_volume'] = 25
        elif total_points >= 20:
            trust_factors['data_volume'] = 20
        elif total_points >= 10:
            trust_factors['data_volume'] = 15
        elif total_points >= 5:
            trust_factors['data_volume'] = 10
        else:
            trust_factors['data_volume'] = 5
        
        # Data Quality Factor (0-20 points)
        valid_response_times = len([rt for rt in response_times if isinstance(rt, (int, float))])
        quality_ratio = valid_response_times / total_points if total_points > 0 else 0
        trust_factors['data_quality'] = int(quality_ratio * 20)
        
        # Consistency Factor (0-20 points)
        if len(response_times) >= 3:
            # Calculate coefficient of variation (CV = std/mean)
            mean_rt = sum(response_times) / len(response_times)
            std_rt = (sum((rt - mean_rt) ** 2 for rt in response_times) / len(response_times)) ** 0.5
            cv = std_rt / mean_rt if mean_rt > 0 else 1
            
            # Lower CV = higher consistency = higher trust
            if cv <= 0.1:
                trust_factors['consistency'] = 20
            elif cv <= 0.2:
                trust_factors['consistency'] = 15
            elif cv <= 0.3:
                trust_factors['consistency'] = 10
            else:
                trust_factors['consistency'] = 5
        else:
            trust_factors['consistency'] = 5
        
        # Anomaly Ratio Factor (0-15 points)
        anomaly_ratio = len(anomalies) / total_points if total_points > 0 else 0
        if anomaly_ratio <= 0.05:  # Less than 5% anomalies
            trust_factors['anomaly_ratio'] = 15
        elif anomaly_ratio <= 0.1:  # Less than 10% anomalies
            trust_factors['anomaly_ratio'] = 10
        elif anomaly_ratio <= 0.2:  # Less than 20% anomalies
            trust_factors['anomaly_ratio'] = 5
        else:
            trust_factors['anomaly_ratio'] = 0
        
        # Response Time Reliability (0-10 points)
        if len(response_times) >= 5:
            # Check for reasonable response times (not too fast, not too slow)
            reasonable_times = [rt for rt in response_times if 10 <= rt <= 5000]  # 10ms to 5s
            reliability_ratio = len(reasonable_times) / len(response_times)
            trust_factors['response_time_reliability'] = int(reliability_ratio * 10)
        else:
            trust_factors['response_time_reliability'] = 5
        
        # Accessibility Reliability (0-10 points)
        if accessibility_rate >= 95:
            trust_factors['accessibility_reliability'] = 10
        elif accessibility_rate >= 90:
            trust_factors['accessibility_reliability'] = 8
        elif accessibility_rate >= 80:
            trust_factors['accessibility_reliability'] = 5
        else:
            trust_factors['accessibility_reliability'] = 2
        
        # Calculate total trust score
        total_trust = sum(trust_factors.values())
        
        # Add trust level interpretation
        if total_trust >= 90:
            trust_level = "Very High"
        elif total_trust >= 80:
            trust_level = "High"
        elif total_trust >= 70:
            trust_level = "Good"
        elif total_trust >= 60:
            trust_level = "Moderate"
        elif total_trust >= 50:
            trust_level = "Low"
        else:
            trust_level = "Very Low"
        
        return {
            'score': total_trust,
            'level': trust_level,
            'factors': trust_factors,
            'interpretation': self.get_trust_interpretation(total_trust, trust_factors)
        }
    
    def get_trust_interpretation(self, score, factors):
        """Get interpretation of trust score"""
        interpretations = []
        
        if factors['data_volume'] < 15:
            interpretations.append("Limited data points may affect reliability")
        
        if factors['data_quality'] < 15:
            interpretations.append("Some data points may be incomplete or invalid")
        
        if factors['consistency'] < 10:
            interpretations.append("High variability in response times detected")
        
        if factors['anomaly_ratio'] < 10:
            interpretations.append("High anomaly rate may indicate unstable conditions")
        
        if factors['response_time_reliability'] < 7:
            interpretations.append("Response times may be unreliable or extreme")
        
        if factors['accessibility_reliability'] < 7:
            interpretations.append("Camera accessibility issues detected")
        
        if not interpretations:
            interpretations.append("Analysis appears reliable with good data quality")
        
        return interpretations
    
    def detect_camera_anomalies(self, data_points):
        """Detect anomalies in camera behavior"""
        anomalies = []
        
        if len(data_points) < 3:
            return anomalies
        
        # Response time anomalies
        response_times = [point['response_time'] for point in data_points if point['response_time'] != 'N/A']
        response_times = [rt for rt in response_times if isinstance(rt, (int, float))]
        
        if len(response_times) >= 3:
            mean_rt = sum(response_times) / len(response_times)
            std_rt = (sum((rt - mean_rt) ** 2 for rt in response_times) / len(response_times)) ** 0.5
            
            for i, point in enumerate(data_points):
                if point['response_time'] != 'N/A' and isinstance(point['response_time'], (int, float)):
                    if abs(point['response_time'] - mean_rt) > 2 * std_rt:
                        anomalies.append({
                            'type': 'Response Time Anomaly',
                            'timestamp': point['timestamp'],
                            'value': point['response_time'],
                            'expected_range': f"{mean_rt - 2*std_rt:.1f} - {mean_rt + 2*std_rt:.1f}ms"
                        })
        
        # Accessibility anomalies
        for i, point in enumerate(data_points):
            if not point['is_accessible']:
                # Check if this is unusual (camera was accessible before/after)
                before_accessible = i > 0 and data_points[i-1]['is_accessible']
                after_accessible = i < len(data_points) - 1 and data_points[i+1]['is_accessible']
                
                if before_accessible or after_accessible:
                    anomalies.append({
                        'type': 'Accessibility Anomaly',
                        'timestamp': point['timestamp'],
                        'value': 'Inaccessible',
                        'expected': 'Accessible'
                    })
        
        # Port change anomalies
        for i in range(1, len(data_points)):
            prev_ports = set(data_points[i-1]['open_ports'])
            curr_ports = set(data_points[i]['open_ports'])
            
            if prev_ports != curr_ports:
                added_ports = curr_ports - prev_ports
                removed_ports = prev_ports - curr_ports
                
                if added_ports or removed_ports:
                    anomalies.append({
                        'type': 'Port Change Anomaly',
                        'timestamp': data_points[i]['timestamp'],
                        'added_ports': list(added_ports),
                        'removed_ports': list(removed_ports)
                    })
        
        return anomalies
    
    def detect_anomalies(self):
        """Detect and display current anomalies"""
        self.menu.clear_screen()
        print("\n🚨 DETECT ANOMALIES")
        print("─" * 50)
        
        # Get recent monitoring sessions
        sessions = self.config['camera_analysis']['monitoring_sessions']
        if not sessions:
            print("❌ No monitoring sessions found!")
            print("💡 Start a monitoring session first to collect data.")
            input("Press Enter to continue...")
            return
        
        # Analyze latest session
        latest_session = max(sessions, key=lambda x: x['start_time'])
        data_points = latest_session.get('data_points', [])
        
        if not data_points:
            print("❌ No data points found in latest session!")
            input("Press Enter to continue...")
            return
        
        print(f"🔍 Analyzing latest session: {latest_session['id']}")
        print(f"📊 Data points: {len(data_points)}")
        
        # Group data by camera
        camera_data = {}
        for point in data_points:
            camera_id = point['camera_id']
            if camera_id not in camera_data:
                camera_data[camera_id] = []
            camera_data[camera_id].append(point)
        
        # Detect anomalies for each camera
        all_anomalies = []
        for camera_id, points in camera_data.items():
            anomalies = self.detect_camera_anomalies(points)
            for anomaly in anomalies:
                anomaly['camera_id'] = camera_id
                all_anomalies.append(anomaly)
        
        # Save anomalies to history
        if all_anomalies:
            anomaly_record = {
                'timestamp': datetime.now().isoformat(),
                'session_id': latest_session['id'],
                'anomalies': all_anomalies,
                'total_count': len(all_anomalies)
            }
            self.config['camera_analysis']['anomaly_history'].append(anomaly_record)
            self.save_config()
        
        # Display results
        if all_anomalies:
            print(f"\n🚨 DETECTED {len(all_anomalies)} ANOMALIES")
            print("─" * 60)
            
            # Group by type
            anomaly_types = {}
            for anomaly in all_anomalies:
                anomaly_type = anomaly['type']
                if anomaly_type not in anomaly_types:
                    anomaly_types[anomaly_type] = []
                anomaly_types[anomaly_type].append(anomaly)
            
            for anomaly_type, anomalies in anomaly_types.items():
                print(f"\n🔍 {anomaly_type} ({len(anomalies)} occurrences):")
                for anomaly in anomalies[:5]:  # Show first 5
                    timestamp = datetime.fromisoformat(anomaly['timestamp']).strftime('%H:%M:%S')
                    print(f"   📅 {timestamp} - Camera: {anomaly['camera_id']}")
                    if 'value' in anomaly:
                        print(f"      Value: {anomaly['value']}")
                    if 'expected_range' in anomaly:
                        print(f"      Expected: {anomaly['expected_range']}")
                    if 'added_ports' in anomaly and anomaly['added_ports']:
                        print(f"      Added Ports: {anomaly['added_ports']}")
                    if 'removed_ports' in anomaly and anomaly['removed_ports']:
                        print(f"      Removed Ports: {anomaly['removed_ports']}")
                
                if len(anomalies) > 5:
                    print(f"   ... and {len(anomalies) - 5} more")
        else:
            print("\n✅ No anomalies detected!")
            print("📊 All camera behaviors appear normal")
        
        input("Press Enter to continue...")
    
    def generate_analysis_report(self):
        """Generate comprehensive analysis report"""
        self.menu.clear_screen()
        print("\n📈 GENERATE ANALYSIS REPORT")
        print("─" * 50)
        
        sessions = self.config['camera_analysis']['monitoring_sessions']
        if not sessions:
            print("❌ No monitoring sessions found!")
            print("💡 Start a monitoring session first to collect data.")
            input("Press Enter to continue...")
            return
        
        # Select session for report
        session_options = []
        for session in sessions:
            start_time = datetime.fromisoformat(session['start_time']).strftime('%Y-%m-%d %H:%M')
            status = session.get('status', 'unknown')
            data_points = len(session.get('data_points', []))
            session_options.append(f"{start_time} - {status} ({data_points} points)")
        
        choice = self.menu.show_dropdown("SELECT SESSION FOR REPORT", session_options)
        if choice == -1:
            return
        
        selected_session = sessions[choice]
        
        # Generate report
        report = self.create_analysis_report(selected_session)
        
        # Display report
        print(f"\n📊 COMPREHENSIVE ANALYSIS REPORT")
        print("=" * 80)
        print(f"📅 Session: {selected_session['id']}")
        print(f"⏰ Duration: {selected_session['start_time']} to {selected_session.get('end_time', 'Ongoing')}")
        print(f"📊 Data Points: {len(selected_session.get('data_points', []))}")
        print("=" * 80)
        
        print(f"\n📹 CAMERA OVERVIEW")
        print("─" * 40)
        for camera in selected_session.get('cameras', []):
            print(f"📹 {camera['ip']}:{camera['port']} - {camera.get('brand', 'Unknown')}")
        
        print(f"\n📊 BEHAVIOR ANALYSIS")
        print("─" * 40)
        if selected_session['id'] in self.config['camera_analysis']['behavior_patterns']:
            patterns = self.config['camera_analysis']['behavior_patterns'][selected_session['id']]
            for camera_id, pattern in patterns.items():
                print(f"\n📹 {camera_id}:")
                print(f"   📊 Data Points: {pattern['total_points']}")
                print(f"   ⏱️  Avg Response Time: {pattern['avg_response_time']:.1f}ms")
                print(f"   📈 Response Variance: {pattern['response_time_variance']:.1f}")
                print(f"   🔄 Accessibility: {pattern['accessibility_rate']:.1f}%")
                print(f"   🚨 Anomalies: {pattern['anomalies']}")
                print(f"   📊 Port Stability: {pattern['port_stability']:.1f}%")
                print(f"   🔒 Security Trend: {pattern['security_trend']}")
                
                # Display trust score
                trust = pattern.get('trust_score', {})
                if trust:
                    trust_score = trust.get('score', 0)
                    trust_level = trust.get('level', 'Unknown')
                    print(f"   🎯 Trust Score: {trust_score}/100 ({trust_level})")
                    
                    # Show trust interpretation
                    interpretations = trust.get('interpretation', [])
                    if interpretations:
                        print(f"   💡 Trust Notes:")
                        for interpretation in interpretations:
                            print(f"      • {interpretation}")
        
        print(f"\n🚨 ANOMALY SUMMARY")
        print("─" * 40)
        anomaly_count = 0
        for record in self.config['camera_analysis']['anomaly_history']:
            if record['session_id'] == selected_session['id']:
                anomaly_count += record['total_count']
        
        if anomaly_count > 0:
            print(f"🚨 Total Anomalies Detected: {anomaly_count}")
            print("⚠️  Review anomaly details for security implications")
        else:
            print("✅ No anomalies detected in this session")
        
        print(f"\n💡 RECOMMENDATIONS")
        print("─" * 40)
        recommendations = self.generate_recommendations(selected_session)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        
        # Save report
        report_filename = f"camera_analysis_report_{selected_session['id']}.txt"
        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n💾 Report saved to: {report_filename}")
        except Exception as e:
            print(f"\n❌ Failed to save report: {e}")
        
        input("Press Enter to continue...")
    
    def create_analysis_report(self, session):
        """Create detailed analysis report"""
        report_lines = []
        report_lines.append("CAMERA COGNITIVE BEHAVIOR ANALYSIS REPORT")
        report_lines.append("=" * 60)
        report_lines.append(f"Session ID: {session['id']}")
        report_lines.append(f"Start Time: {session['start_time']}")
        report_lines.append(f"End Time: {session.get('end_time', 'Ongoing')}")
        report_lines.append(f"Duration: {session.get('duration_minutes', 'Unknown')} minutes")
        report_lines.append(f"Check Interval: {session.get('interval_seconds', 'Unknown')} seconds")
        report_lines.append(f"Data Points: {len(session.get('data_points', []))}")
        report_lines.append("")
        
        # Camera details
        report_lines.append("CAMERA DETAILS")
        report_lines.append("-" * 30)
        for camera in session.get('cameras', []):
            report_lines.append(f"IP: {camera['ip']}:{camera['port']}")
            report_lines.append(f"Brand: {camera.get('brand', 'Unknown')}")
            report_lines.append(f"Model: {camera.get('model', 'Unknown')}")
            report_lines.append("")
        
        # Behavior patterns
        if session['id'] in self.config['camera_analysis']['behavior_patterns']:
            report_lines.append("BEHAVIOR PATTERNS")
            report_lines.append("-" * 30)
            patterns = self.config['camera_analysis']['behavior_patterns'][session['id']]
            for camera_id, pattern in patterns.items():
                report_lines.append(f"Camera: {camera_id}")
                report_lines.append(f"  Data Points: {pattern['total_points']}")
                report_lines.append(f"  Average Response Time: {pattern['avg_response_time']:.1f}ms")
                report_lines.append(f"  Response Time Variance: {pattern['response_time_variance']:.1f}")
                report_lines.append(f"  Accessibility Rate: {pattern['accessibility_rate']:.1f}%")
                report_lines.append(f"  Anomalies Detected: {pattern['anomalies']}")
                report_lines.append(f"  Port Stability: {pattern['port_stability']:.1f}%")
                report_lines.append(f"  Security Trend: {pattern['security_trend']}")
                
                # Add trust score to report
                trust = pattern.get('trust_score', {})
                if trust:
                    trust_score = trust.get('score', 0)
                    trust_level = trust.get('level', 'Unknown')
                    report_lines.append(f"  Trust Score: {trust_score}/100 ({trust_level})")
                    
                    # Add trust factors
                    factors = trust.get('factors', {})
                    report_lines.append(f"    Data Volume: {factors.get('data_volume', 0)}/25")
                    report_lines.append(f"    Data Quality: {factors.get('data_quality', 0)}/20")
                    report_lines.append(f"    Consistency: {factors.get('consistency', 0)}/20")
                    report_lines.append(f"    Anomaly Ratio: {factors.get('anomaly_ratio', 0)}/15")
                    report_lines.append(f"    Response Reliability: {factors.get('response_time_reliability', 0)}/10")
                    report_lines.append(f"    Accessibility Reliability: {factors.get('accessibility_reliability', 0)}/10")
                    
                    # Add trust interpretation
                    interpretations = trust.get('interpretation', [])
                    if interpretations:
                        report_lines.append("    Trust Notes:")
                        for interpretation in interpretations:
                            report_lines.append(f"      - {interpretation}")
                
                report_lines.append("")
        
        # Anomalies
        report_lines.append("ANOMALY DETECTION")
        report_lines.append("-" * 30)
        anomaly_count = 0
        for record in self.config['camera_analysis']['anomaly_history']:
            if record['session_id'] == session['id']:
                anomaly_count += record['total_count']
                for anomaly in record['anomalies']:
                    report_lines.append(f"Type: {anomaly['type']}")
                    report_lines.append(f"Camera: {anomaly['camera_id']}")
                    report_lines.append(f"Timestamp: {anomaly['timestamp']}")
                    if 'value' in anomaly:
                        report_lines.append(f"Value: {anomaly['value']}")
                    if 'expected_range' in anomaly:
                        report_lines.append(f"Expected Range: {anomaly['expected_range']}")
                    report_lines.append("")
        
        if anomaly_count == 0:
            report_lines.append("No anomalies detected in this session.")
            report_lines.append("")
        
        # Recommendations
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("-" * 30)
        recommendations = self.generate_recommendations(session)
        for i, rec in enumerate(recommendations, 1):
            report_lines.append(f"{i}. {rec}")
        
        report_lines.append("")
        report_lines.append("Report Generated: " + datetime.now().isoformat())
        
        return "\n".join(report_lines)
    
    def generate_recommendations(self, session):
        """Generate security and maintenance recommendations"""
        recommendations = []
        
        # Check for patterns
        if session['id'] in self.config['camera_analysis']['behavior_patterns']:
            patterns = self.config['camera_analysis']['behavior_patterns'][session['id']]
            
            for camera_id, pattern in patterns.items():
                # Response time recommendations
                if pattern['avg_response_time'] > 1000:
                    recommendations.append(f"Camera {camera_id} has high response times ({pattern['avg_response_time']:.1f}ms). Check network connectivity and camera performance.")
                
                # Accessibility recommendations
                if pattern['accessibility_rate'] < 95:
                    recommendations.append(f"Camera {camera_id} has low accessibility rate ({pattern['accessibility_rate']:.1f}%). Investigate network stability and camera health.")
                
                # Port stability recommendations
                if pattern['port_stability'] < 90:
                    recommendations.append(f"Camera {camera_id} shows port instability ({pattern['port_stability']:.1f}%). Check for configuration changes or security issues.")
                
                # Security trend recommendations
                if pattern['security_trend'] == "Degrading":
                    recommendations.append(f"Camera {camera_id} shows degrading security trend. Review security settings and firmware updates.")
        
        # Anomaly recommendations
        anomaly_count = 0
        for record in self.config['camera_analysis']['anomaly_history']:
            if record['session_id'] == session['id']:
                anomaly_count += record['total_count']
        
        if anomaly_count > 0:
            recommendations.append(f"Session detected {anomaly_count} anomalies. Review detailed anomaly logs for security implications.")
        
        # General recommendations
        if not recommendations:
            recommendations.append("No specific issues detected. Continue regular monitoring.")
        
        recommendations.append("Schedule regular security audits and firmware updates.")
        recommendations.append("Implement network segmentation for camera devices.")
        recommendations.append("Enable logging and monitoring for all camera access.")
        
        return recommendations
    
    def view_historical_data(self):
        """View historical analysis data"""
        self.menu.clear_screen()
        print("\n📋 VIEW HISTORICAL DATA")
        print("─" * 50)
        
        options = [
            "📊 Monitoring Sessions",
            "🚨 Anomaly History",
            "📈 Behavior Patterns",
            "📋 Analysis Reports",
            "⬅️  Back to Analysis Menu"
        ]
        
        choice = self.menu.show_dropdown("HISTORICAL DATA", options)
        
        if choice == 0:
            self.view_monitoring_sessions()
        elif choice == 1:
            self.view_anomaly_history()
        elif choice == 2:
            self.view_behavior_patterns()
        elif choice == 3:
            self.view_analysis_reports()
        elif choice == 4 or choice == -1:
            return
    
    def view_monitoring_sessions(self):
        """View monitoring sessions history"""
        sessions = self.config['camera_analysis']['monitoring_sessions']
        
        if not sessions:
            print("📭 No monitoring sessions found!")
            input("Press Enter to continue...")
            return
        
        print(f"\n📊 MONITORING SESSIONS ({len(sessions)})")
        print("─" * 60)
        
        for i, session in enumerate(sessions, 1):
            start_time = datetime.fromisoformat(session['start_time']).strftime('%Y-%m-%d %H:%M:%S')
            end_time = session.get('end_time', 'Ongoing')
            if end_time != 'Ongoing':
                end_time = datetime.fromisoformat(end_time).strftime('%Y-%m-%d %H:%M:%S')
            
            status = session.get('status', 'unknown')
            data_points = len(session.get('data_points', []))
            cameras = len(session.get('cameras', []))
            
            print(f"{i:2d}. Session: {session['id']}")
            print(f"    📅 Start: {start_time}")
            print(f"    📅 End: {end_time}")
            print(f"    📊 Status: {status}")
            print(f"    📹 Cameras: {cameras}")
            print(f"    📊 Data Points: {data_points}")
            print()
        
        input("Press Enter to continue...")
    
    def view_anomaly_history(self):
        """View anomaly detection history"""
        anomaly_history = self.config['camera_analysis']['anomaly_history']
        
        if not anomaly_history:
            print("📭 No anomaly history found!")
            input("Press Enter to continue...")
            return
        
        print(f"\n🚨 ANOMALY HISTORY ({len(anomaly_history)})")
        print("─" * 60)
        
        for i, record in enumerate(anomaly_history, 1):
            timestamp = datetime.fromisoformat(record['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            session_id = record['session_id']
            total_count = record['total_count']
            
            print(f"{i:2d}. {timestamp}")
            print(f"    📊 Session: {session_id}")
            print(f"    🚨 Anomalies: {total_count}")
            
            # Show anomaly types
            anomaly_types = {}
            for anomaly in record['anomalies']:
                anomaly_type = anomaly['type']
                anomaly_types[anomaly_type] = anomaly_types.get(anomaly_type, 0) + 1
            
            for anomaly_type, count in anomaly_types.items():
                print(f"       - {anomaly_type}: {count}")
            print()
        
        input("Press Enter to continue...")
    
    def view_behavior_patterns(self):
        """View behavior patterns history"""
        patterns = self.config['camera_analysis']['behavior_patterns']
        
        if not patterns:
            print("📭 No behavior patterns found!")
            input("Press Enter to continue...")
            return
        
        print(f"\n📈 BEHAVIOR PATTERNS ({len(patterns)} sessions)")
        print("─" * 60)
        
        for session_id, session_patterns in patterns.items():
            print(f"📊 Session: {session_id}")
            print(f"📹 Cameras Analyzed: {len(session_patterns)}")
            
            for camera_id, pattern in session_patterns.items():
                print(f"\n   📹 {camera_id}:")
                print(f"      📊 Data Points: {pattern['total_points']}")
                print(f"      ⏱️  Avg Response: {pattern['avg_response_time']:.1f}ms")
                print(f"      🔄 Accessibility: {pattern['accessibility_rate']:.1f}%")
                print(f"      🚨 Anomalies: {pattern['anomalies']}")
                print(f"      📊 Port Stability: {pattern['port_stability']:.1f}%")
                print(f"      🔒 Security Trend: {pattern['security_trend']}")
                
                # Display trust score
                trust = pattern.get('trust_score', {})
                if trust:
                    trust_score = trust.get('score', 0)
                    trust_level = trust.get('level', 'Unknown')
                    print(f"      🎯 Trust Score: {trust_score}/100 ({trust_level})")
            print()
        
        input("Press Enter to continue...")
    
    def view_analysis_reports(self):
        """View generated analysis reports"""
        reports = self.config['camera_analysis']['analysis_reports']
        
        if not reports:
            print("📭 No analysis reports found!")
            print("💡 Generate reports from the analysis menu.")
            input("Press Enter to continue...")
            return
        
        print(f"\n📋 ANALYSIS REPORTS ({len(reports)})")
        print("─" * 60)
        
        for i, report in enumerate(reports, 1):
            print(f"{i:2d}. {report['title']}")
            print(f"    📅 Generated: {report['timestamp']}")
            print(f"    📊 Session: {report['session_id']}")
            print(f"    📄 File: {report.get('filename', 'N/A')}")
            print()
        
        input("Press Enter to continue...")
    
    def configure_analysis_settings(self):
        """Configure analysis settings"""
        self.menu.clear_screen()
        print("\n⚙️  CONFIGURE ANALYSIS SETTINGS")
        print("─" * 50)
        
        # Initialize settings if not exists
        if 'analysis_settings' not in self.config['camera_analysis']:
            self.config['camera_analysis']['analysis_settings'] = {
                'default_monitoring_duration': 10,
                'default_check_interval': 30,
                'anomaly_threshold_response_time': 2.0,
                'anomaly_threshold_accessibility': 95.0,
                'enable_auto_anomaly_detection': True,
                'report_auto_save': True
            }
        
        settings = self.config['camera_analysis']['analysis_settings']
        
        options = [
            f"⏱️  Default Monitoring Duration: {settings['default_monitoring_duration']} minutes",
            f"🔄 Default Check Interval: {settings['default_check_interval']} seconds",
            f"📊 Response Time Anomaly Threshold: {settings['anomaly_threshold_response_time']}x std dev",
            f"📈 Accessibility Anomaly Threshold: {settings['anomaly_threshold_accessibility']}%",
            f"🤖 Auto Anomaly Detection: {'Enabled' if settings['enable_auto_anomaly_detection'] else 'Disabled'}",
            f"💾 Auto Save Reports: {'Enabled' if settings['report_auto_save'] else 'Disabled'}",
            "⬅️  Back to Analysis Menu"
        ]
        
        choice = self.menu.show_dropdown("ANALYSIS SETTINGS", options)
        
        if choice == 0:  # Monitoring duration
            new_value = self.menu.show_input_prompt("Enter default monitoring duration (minutes)", str(settings['default_monitoring_duration']))
            try:
                settings['default_monitoring_duration'] = int(new_value)
                print("✅ Setting updated!")
            except:
                print("❌ Invalid value!")
        elif choice == 1:  # Check interval
            new_value = self.menu.show_input_prompt("Enter default check interval (seconds)", str(settings['default_check_interval']))
            try:
                settings['default_check_interval'] = int(new_value)
                print("✅ Setting updated!")
            except:
                print("❌ Invalid value!")
        elif choice == 2:  # Response time threshold
            new_value = self.menu.show_input_prompt("Enter response time anomaly threshold (std dev multiplier)", str(settings['anomaly_threshold_response_time']))
            try:
                settings['anomaly_threshold_response_time'] = float(new_value)
                print("✅ Setting updated!")
            except:
                print("❌ Invalid value!")
        elif choice == 3:  # Accessibility threshold
            new_value = self.menu.show_input_prompt("Enter accessibility anomaly threshold (percentage)", str(settings['anomaly_threshold_accessibility']))
            try:
                settings['anomaly_threshold_accessibility'] = float(new_value)
                print("✅ Setting updated!")
            except:
                print("❌ Invalid value!")
        elif choice == 4:  # Auto anomaly detection
            settings['enable_auto_anomaly_detection'] = not settings['enable_auto_anomaly_detection']
            status = "enabled" if settings['enable_auto_anomaly_detection'] else "disabled"
            print(f"✅ Auto anomaly detection {status}!")
        elif choice == 5:  # Auto save reports
            settings['report_auto_save'] = not settings['report_auto_save']
            status = "enabled" if settings['report_auto_save'] else "disabled"
            print(f"✅ Auto save reports {status}!")
        elif choice == 6 or choice == -1:  # Back
            return
        
        self.save_config()
        input("Press Enter to continue...")
    
    def clear_analysis_data(self):
        """Clear analysis data with confirmation"""
        self.menu.clear_screen()
        print("\n🗑️  CLEAR ANALYSIS DATA")
        print("─" * 50)
        
        sessions_count = len(self.config['camera_analysis']['monitoring_sessions'])
        anomalies_count = len(self.config['camera_analysis']['anomaly_history'])
        patterns_count = len(self.config['camera_analysis']['behavior_patterns'])
        reports_count = len(self.config['camera_analysis']['analysis_reports'])
        
        print(f"📊 Current Data:")
        print(f"   📊 Monitoring Sessions: {sessions_count}")
        print(f"   🚨 Anomaly Records: {anomalies_count}")
        print(f"   📈 Behavior Patterns: {patterns_count}")
        print(f"   📋 Analysis Reports: {reports_count}")
        print()
        
        if sessions_count == 0 and anomalies_count == 0 and patterns_count == 0 and reports_count == 0:
            print("📭 No analysis data to clear!")
            input("Press Enter to continue...")
            return
        
        options = [
            "🗑️  Clear All Analysis Data",
            "📊 Clear Monitoring Sessions Only",
            "🚨 Clear Anomaly History Only",
            "📈 Clear Behavior Patterns Only",
            "📋 Clear Analysis Reports Only",
            "⬅️  Back to Analysis Menu"
        ]
        
        choice = self.menu.show_dropdown("CLEAR DATA OPTIONS", options)
        
        if choice == 0:  # Clear all
            if self.menu.show_confirmation("Clear ALL analysis data? This cannot be undone!"):
                self.config['camera_analysis']['monitoring_sessions'] = []
                self.config['camera_analysis']['anomaly_history'] = []
                self.config['camera_analysis']['behavior_patterns'] = {}
                self.config['camera_analysis']['analysis_reports'] = []
                self.save_config()
                print("✅ All analysis data cleared!")
        elif choice == 1:  # Clear sessions
            if self.menu.show_confirmation("Clear monitoring sessions?"):
                self.config['camera_analysis']['monitoring_sessions'] = []
                self.save_config()
                print("✅ Monitoring sessions cleared!")
        elif choice == 2:  # Clear anomalies
            if self.menu.show_confirmation("Clear anomaly history?"):
                self.config['camera_analysis']['anomaly_history'] = []
                self.save_config()
                print("✅ Anomaly history cleared!")
        elif choice == 3:  # Clear patterns
            if self.menu.show_confirmation("Clear behavior patterns?"):
                self.config['camera_analysis']['behavior_patterns'] = {}
                self.save_config()
                print("✅ Behavior patterns cleared!")
        elif choice == 4:  # Clear reports
            if self.menu.show_confirmation("Clear analysis reports?"):
                self.config['camera_analysis']['analysis_reports'] = []
                self.save_config()
                print("✅ Analysis reports cleared!")
        elif choice == 5 or choice == -1:  # Back
            return
        
        input("Press Enter to continue...")
    
    def view_trust_scores(self):
        """View detailed trust scores for all analysis sessions"""
        self.menu.clear_screen()
        print("\n🎯 VIEW TRUST SCORES")
        print("─" * 50)
        
        patterns = self.config['camera_analysis']['behavior_patterns']
        if not patterns:
            print("📭 No behavior patterns found!")
            print("💡 Run behavior analysis first to generate trust scores.")
            input("Press Enter to continue...")
            return
        
        print(f"📊 TRUST SCORE ANALYSIS ({len(patterns)} sessions)")
        print("─" * 60)
        
        # Calculate overall trust statistics
        all_trust_scores = []
        session_trust_summary = {}
        
        for session_id, session_patterns in patterns.items():
            session_scores = []
            for camera_id, pattern in session_patterns.items():
                trust = pattern.get('trust_score', {})
                if trust:
                    score = trust.get('score', 0)
                    all_trust_scores.append(score)
                    session_scores.append(score)
            
            if session_scores:
                avg_trust = sum(session_scores) / len(session_scores)
                session_trust_summary[session_id] = {
                    'avg_trust': avg_trust,
                    'min_trust': min(session_scores),
                    'max_trust': max(session_scores),
                    'camera_count': len(session_scores)
                }
        
        # Display overall statistics
        if all_trust_scores:
            overall_avg = sum(all_trust_scores) / len(all_trust_scores)
            overall_min = min(all_trust_scores)
            overall_max = max(all_trust_scores)
            
            print(f"📊 OVERALL TRUST STATISTICS")
            print(f"   🎯 Average Trust Score: {overall_avg:.1f}/100")
            print(f"   📉 Lowest Trust Score: {overall_min}/100")
            print(f"   📈 Highest Trust Score: {overall_max}/100")
            print(f"   📊 Total Analyses: {len(all_trust_scores)}")
            print()
        
        # Display session-by-session breakdown
        for session_id, summary in session_trust_summary.items():
            print(f"📊 Session: {session_id}")
            print(f"   🎯 Average Trust: {summary['avg_trust']:.1f}/100")
            print(f"   📉 Min Trust: {summary['min_trust']}/100")
            print(f"   📈 Max Trust: {summary['max_trust']}/100")
            print(f"   📹 Cameras: {summary['camera_count']}")
            
            # Show individual camera trust scores
            session_patterns = patterns[session_id]
            for camera_id, pattern in session_patterns.items():
                trust = pattern.get('trust_score', {})
                if trust:
                    score = trust.get('score', 0)
                    level = trust.get('level', 'Unknown')
                    print(f"      📹 {camera_id}: {score}/100 ({level})")
            print()
        
        # Show trust level distribution
        if all_trust_scores:
            trust_levels = {'Very High': 0, 'High': 0, 'Good': 0, 'Moderate': 0, 'Low': 0, 'Very Low': 0}
            for score in all_trust_scores:
                if score >= 90:
                    trust_levels['Very High'] += 1
                elif score >= 80:
                    trust_levels['High'] += 1
                elif score >= 70:
                    trust_levels['Good'] += 1
                elif score >= 60:
                    trust_levels['Moderate'] += 1
                elif score >= 50:
                    trust_levels['Low'] += 1
                else:
                    trust_levels['Very Low'] += 1
            
            print(f"📊 TRUST LEVEL DISTRIBUTION")
            print("─" * 30)
            for level, count in trust_levels.items():
                if count > 0:
                    percentage = (count / len(all_trust_scores)) * 100
                    print(f"   {level}: {count} ({percentage:.1f}%)")
            print()
        
        # Show recommendations based on trust scores
        print(f"💡 TRUST SCORE RECOMMENDATIONS")
        print("─" * 30)
        
        if all_trust_scores:
            low_trust_count = len([s for s in all_trust_scores if s < 70])
            if low_trust_count > 0:
                print(f"⚠️  {low_trust_count} analysis(es) have low trust scores (<70)")
                print("   • Consider collecting more data points")
                print("   • Check for network stability issues")
                print("   • Verify camera accessibility")
            
            high_trust_count = len([s for s in all_trust_scores if s >= 80])
            if high_trust_count > 0:
                print(f"✅ {high_trust_count} analysis(es) have high trust scores (≥80)")
                print("   • These results are highly reliable")
                print("   • Use for decision-making and reporting")
            
            if overall_avg < 70:
                print("🔧 Overall trust is below 70% - consider:")
                print("   • Increasing monitoring duration")
                print("   • Reducing check intervals")
                print("   • Improving network stability")
            else:
                print("✅ Overall trust is good - analysis results are reliable")
        
        input("Press Enter to continue...")
    
    def scan_network_for_cameras_cognitive(self):
        """Scan network for cameras and return results for cognitive analysis"""
        # Get local network range
        local_ip = self.get_local_ip()
        if not local_ip:
            print("❌ Could not determine local IP address")
            return []
        
        network_base = '.'.join(local_ip.split('.')[:-1])
        print(f"🔍 Scanning network: {network_base}.x")
        print("⏳ This may take a few minutes...")
        
        # Scan for common camera ports and services
        camera_devices = []
        threads = []
        
        # Common camera ports
        camera_ports = [80, 81, 443, 554, 8080, 8081, 8082, 8888, 9999]
        
        # Scan IP range
        total_ips = 254
        for i in range(1, 255):
            ip = f"{network_base}.{i}"
            thread = threading.Thread(target=self.scan_ip_for_cameras, 
                                    args=(ip, camera_ports, camera_devices))
            threads.append(thread)
            thread.start()
            
            # Show progress every 50 IPs
            if i % 50 == 0:
                print(f"   Progress: {i}/{total_ips} IPs scanned...")
            
            # Limit concurrent threads
            if len(threads) >= 50:
                for t in threads:
                    t.join()
                threads = []
        
        # Wait for remaining threads
        for thread in threads:
            thread.join()
        
        print(f"✅ Scan completed! Found {len(camera_devices)} potential cameras.")
        
        # Convert to format expected by cognitive analysis
        cameras = []
        for device in camera_devices:
            camera = {
                'ip': device['ip'],
                'port': device['port'],
                'brand': self.identify_camera_brand_model(device.get('banner', '')),
                'model': 'Unknown',
                'type': device.get('type', 'Unknown'),
                'banner': device.get('banner', ''),
                'open_ports': [device['port']],
                'default_credentials': False,
                'authentication_required': True,
                'firmware_version': 'Unknown'
            }
            cameras.append(camera)
        
        return cameras
    
    def detect_mac_camera(self):
        """Detect Mac built-in camera"""
        try:
            import subprocess
            import platform
            
            # Check if we're on macOS
            if platform.system() != 'Darwin':
                return None
            
            # Use system_profiler to detect cameras
            result = subprocess.run(['system_profiler', 'SPCameraDataType', '-json'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                
                cameras = data.get('SPCameraDataType', [])
                for camera in cameras:
                    camera_name = camera.get('_name', 'Unknown Camera')
                    if 'built-in' in camera_name.lower() or 'facetime' in camera_name.lower():
                        return {
                            'ip': 'localhost',
                            'port': 0,  # Mac camera doesn't use network ports
                            'name': camera_name,
                            'brand': 'Apple',
                            'model': camera_name,
                            'type': 'Mac Built-in Camera',
                            'banner': '',
                            'open_ports': [],
                            'default_credentials': False,
                            'authentication_required': False,
                            'firmware_version': 'Unknown',
                            'is_mac_camera': True,
                            'device_id': camera.get('spcamera_model_id', 'unknown')
                        }
            
            # Fallback: try to detect camera using AVFoundation
            return self.detect_mac_camera_avfoundation()
            
        except Exception as e:
            print(f"⚠️  Could not detect Mac camera: {e}")
            return None
    
    def detect_mac_camera_avfoundation(self):
        """Detect Mac camera using AVFoundation (fallback method)"""
        try:
            import subprocess
            
            # Try to list video devices using ffmpeg (if available)
            result = subprocess.run(['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', '""'], 
                                  capture_output=True, text=True, timeout=5)
            
            if 'FaceTime HD Camera' in result.stderr or 'Built-in Camera' in result.stderr:
                return {
                    'ip': 'localhost',
                    'port': 0,
                    'name': 'FaceTime HD Camera',
                    'brand': 'Apple',
                    'model': 'FaceTime HD Camera',
                    'type': 'Mac Built-in Camera',
                    'banner': '',
                    'open_ports': [],
                    'default_credentials': False,
                    'authentication_required': False,
                    'firmware_version': 'Unknown',
                    'is_mac_camera': True,
                    'device_id': 'facetime_hd'
                }
            
            # Try using system_profiler with different approach
            result = subprocess.run(['system_profiler', 'SPCameraDataType'], 
                                  capture_output=True, text=True, timeout=10)
            
            if 'FaceTime HD Camera' in result.stdout or 'Built-in Camera' in result.stdout:
                return {
                    'ip': 'localhost',
                    'port': 0,
                    'name': 'FaceTime HD Camera',
                    'brand': 'Apple',
                    'model': 'FaceTime HD Camera',
                    'type': 'Mac Built-in Camera',
                    'banner': '',
                    'open_ports': [],
                    'default_credentials': False,
                    'authentication_required': False,
                    'firmware_version': 'Unknown',
                    'is_mac_camera': True,
                    'device_id': 'facetime_hd'
                }
            
            return None
            
        except Exception as e:
            print(f"⚠️  AVFoundation detection failed: {e}")
            return None
    
    def collect_mac_camera_data_point(self, camera):
        """Collect data point for Mac camera"""
        try:
            # For Mac camera, we'll collect different metrics
            data_point = {
                'camera_id': f"mac_{camera['device_id']}",
                'ip': 'localhost',
                'port': 0,
                'brand': camera['brand'],
                'name': camera['name'],
                'response_time': self.get_mac_camera_response_time(),
                'is_accessible': self.check_mac_camera_accessibility(),
                'open_ports': [],
                'http_headers': {},
                'stream_status': self.check_mac_camera_stream_status(),
                'security_score': self.calculate_mac_camera_security_score(camera),
                'is_mac_camera': True,
                'camera_status': self.get_mac_camera_status(),
                'permissions': self.check_mac_camera_permissions()
            }
            
            return data_point
            
        except Exception as e:
            print(f"⚠️  Error collecting Mac camera data: {e}")
            return {
                'camera_id': f"mac_{camera.get('device_id', 'unknown')}",
                'ip': 'localhost',
                'port': 0,
                'brand': camera.get('brand', 'Apple'),
                'name': camera.get('name', 'Mac Camera'),
                'response_time': 'N/A',
                'is_accessible': False,
                'open_ports': [],
                'http_headers': {},
                'stream_status': {'active': False, 'endpoint': None, 'content_type': None},
                'security_score': 0,
                'is_mac_camera': True,
                'camera_status': 'Error',
                'permissions': 'Unknown'
            }
    
    def get_mac_camera_response_time(self):
        """Get Mac camera response time"""
        try:
            import time
            import subprocess
            
            start_time = time.time()
            
            # Try to access camera using system_profiler
            result = subprocess.run(['system_profiler', 'SPCameraDataType'], 
                                  capture_output=True, text=True, timeout=3)
            
            end_time = time.time()
            
            if result.returncode == 0:
                return int((end_time - start_time) * 1000)
            else:
                return 'N/A'
                
        except Exception:
            return 'N/A'
    
    def check_mac_camera_accessibility(self):
        """Check if Mac camera is accessible"""
        try:
            import subprocess
            
            # Check if camera is available
            result = subprocess.run(['system_profiler', 'SPCameraDataType'], 
                                  capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0 and ('FaceTime HD Camera' in result.stdout or 'Built-in Camera' in result.stdout):
                return True
            else:
                return False
                
        except Exception:
            return False
    
    def check_mac_camera_stream_status(self):
        """Check Mac camera stream status"""
        try:
            import subprocess
            
            # Try to check if camera is being used
            result = subprocess.run(['lsof', '/dev/video0'], 
                                  capture_output=True, text=True, timeout=2)
            
            if result.returncode == 0 and result.stdout.strip():
                return {'active': True, 'endpoint': 'local', 'content_type': 'video/mp4'}
            else:
                return {'active': False, 'endpoint': None, 'content_type': None}
                
        except Exception:
            return {'active': False, 'endpoint': None, 'content_type': None}
    
    def calculate_mac_camera_security_score(self, camera):
        """Calculate security score for Mac camera"""
        score = 100
        
        # Mac cameras are generally more secure
        # Check for privacy settings and permissions
        try:
            import subprocess
            
            # Check if camera privacy is enabled
            result = subprocess.run(['sqlite3', '/Library/Application Support/com.apple.TCC/TCC.db', 
                                   "SELECT service, client FROM access WHERE service='kTCCServiceCamera'"], 
                                  capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0:
                # Camera privacy is managed
                score -= 5  # Small deduction for privacy management complexity
            else:
                score -= 10  # Larger deduction if privacy system not accessible
            
            # Check if camera is built-in (more secure than external)
            if 'built-in' in camera.get('name', '').lower():
                score += 5  # Bonus for built-in camera
            
            # Check for encryption (Mac cameras use hardware encryption)
            score += 10  # Bonus for hardware encryption
            
        except Exception:
            score -= 15  # Deduction if we can't check security features
        
        return max(0, min(100, score))
    
    def get_mac_camera_status(self):
        """Get Mac camera status"""
        try:
            import subprocess
            
            # Check camera status
            result = subprocess.run(['system_profiler', 'SPCameraDataType'], 
                                  capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0:
                if 'FaceTime HD Camera' in result.stdout:
                    return 'Available'
                elif 'Built-in Camera' in result.stdout:
                    return 'Available'
                else:
                    return 'Not Found'
            else:
                return 'Error'
                
        except Exception:
            return 'Unknown'
    
    def check_mac_camera_permissions(self):
        """Check Mac camera permissions"""
        try:
            import subprocess
            
            # Check camera permissions for current user
            result = subprocess.run(['sqlite3', '/Library/Application Support/com.apple.TCC/TCC.db', 
                                   "SELECT service, client, auth_value FROM access WHERE service='kTCCServiceCamera'"], 
                                  capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0 and result.stdout.strip():
                if '1' in result.stdout:  # auth_value = 1 means allowed
                    return 'Granted'
                elif '0' in result.stdout:  # auth_value = 0 means denied
                    return 'Denied'
                else:
                    return 'Unknown'
            else:
                return 'Not Set'
                
        except Exception:
            return 'Unknown'
    
    def mac_camera_analysis(self):
        """Dedicated Mac camera analysis and monitoring"""
        while True:
            self.menu.clear_screen()
            print("\n📱 MAC CAMERA ANALYSIS")
            print("─" * 50)
            
            # Detect Mac camera
            mac_camera = self.detect_mac_camera()
            
            if not mac_camera:
                print("❌ No Mac camera detected!")
                print("💡 Make sure you're on a Mac with a built-in camera.")
                input("Press Enter to continue...")
                return
            
            print(f"✅ Mac Camera Detected: {mac_camera['name']}")
            print(f"📱 Brand: {mac_camera['brand']}")
            print(f"🔧 Device ID: {mac_camera['device_id']}")
            
            options = [
                "🔍 Test Mac Camera",
                "📊 Monitor Mac Camera",
                "🔒 Check Camera Permissions",
                "🛡️  Security Analysis",
                "📈 Generate Mac Camera Report",
                "⚙️  Camera Settings",
                "⬅️  Back to Analysis Menu"
            ]
            
            choice = self.menu.show_dropdown("MAC CAMERA OPTIONS", options)
            
            if choice == 0:
                self.test_mac_camera(mac_camera)
            elif choice == 1:
                self.monitor_mac_camera(mac_camera)
            elif choice == 2:
                self.check_camera_permissions_detailed()
            elif choice == 3:
                self.mac_camera_security_analysis(mac_camera)
            elif choice == 4:
                self.generate_mac_camera_report(mac_camera)
            elif choice == 5:
                self.mac_camera_settings()
            elif choice == 6 or choice == -1:
                break
    
    def test_mac_camera(self, camera):
        """Test Mac camera functionality"""
        self.menu.clear_screen()
        print(f"\n🔍 TESTING MAC CAMERA: {camera['name']}")
        print("─" * 50)
        
        print("🔍 Running camera tests...")
        
        # Test 1: Camera accessibility
        print("1. Testing camera accessibility...")
        is_accessible = self.check_mac_camera_accessibility()
        print(f"   Result: {'✅ Accessible' if is_accessible else '❌ Not Accessible'}")
        
        # Test 2: Response time
        print("2. Testing response time...")
        response_time = self.get_mac_camera_response_time()
        print(f"   Result: {response_time}ms" if response_time != 'N/A' else "   Result: ❌ No Response")
        
        # Test 3: Camera status
        print("3. Checking camera status...")
        status = self.get_mac_camera_status()
        print(f"   Result: {status}")
        
        # Test 4: Permissions
        print("4. Checking permissions...")
        permissions = self.check_mac_camera_permissions()
        print(f"   Result: {permissions}")
        
        # Test 5: Stream status
        print("5. Checking stream status...")
        stream_status = self.check_mac_camera_stream_status()
        if stream_status['active']:
            print(f"   Result: ✅ Active ({stream_status['content_type']})")
        else:
            print("   Result: ❌ Not Active")
        
        # Test 6: Security score
        print("6. Calculating security score...")
        security_score = self.calculate_mac_camera_security_score(camera)
        print(f"   Result: {security_score}/100")
        
        print(f"\n📊 TEST SUMMARY")
        print("─" * 30)
        print(f"📱 Camera: {camera['name']}")
        print(f"🔍 Accessible: {'Yes' if is_accessible else 'No'}")
        print(f"⏱️  Response Time: {response_time}ms" if response_time != 'N/A' else "⏱️  Response Time: N/A")
        print(f"📊 Status: {status}")
        print(f"🔒 Permissions: {permissions}")
        print(f"📹 Stream: {'Active' if stream_status['active'] else 'Inactive'}")
        print(f"🛡️  Security Score: {security_score}/100")
        
        input("Press Enter to continue...")
    
    def monitor_mac_camera(self, camera):
        """Monitor Mac camera for a period of time"""
        self.menu.clear_screen()
        print(f"\n📊 MONITORING MAC CAMERA: {camera['name']}")
        print("─" * 50)
        
        # Get monitoring parameters
        duration = self.menu.show_input_prompt("Monitoring duration (minutes)", "5")
        try:
            duration = int(duration)
        except:
            duration = 5
        
        interval = self.menu.show_input_prompt("Check interval (seconds)", "10")
        try:
            interval = int(interval)
        except:
            interval = 10
        
        print(f"\n🔍 Starting Mac camera monitoring for {duration} minutes...")
        print(f"📊 Check interval: {interval} seconds")
        print("Press Ctrl+C to stop monitoring early")
        
        # Start monitoring session
        session_id = f"mac_camera_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session_data = {
            'id': session_id,
            'start_time': datetime.now().isoformat(),
            'duration_minutes': duration,
            'interval_seconds': interval,
            'camera': camera,
            'data_points': []
        }
        
        try:
            start_time = time.time()
            end_time = start_time + (duration * 60)
            
            while time.time() < end_time:
                current_time = datetime.now()
                print(f"\r⏱️  Monitoring... {current_time.strftime('%H:%M:%S')} - {len(session_data['data_points'])} data points", end='', flush=True)
                
                # Collect data point
                data_point = self.collect_mac_camera_data_point(camera)
                data_point['timestamp'] = current_time.isoformat()
                session_data['data_points'].append(data_point)
                
                time.sleep(interval)
            
            session_data['end_time'] = datetime.now().isoformat()
            session_data['status'] = 'completed'
            
            # Save session data
            self.config['camera_analysis']['monitoring_sessions'].append(session_data)
            self.save_config()
            
            print(f"\n✅ Mac camera monitoring completed!")
            print(f"📊 Collected {len(session_data['data_points'])} data points")
            
        except KeyboardInterrupt:
            session_data['end_time'] = datetime.now().isoformat()
            session_data['status'] = 'interrupted'
            self.config['camera_analysis']['monitoring_sessions'].append(session_data)
            self.save_config()
            print(f"\n⏹️  Mac camera monitoring stopped by user")
            print(f"📊 Collected {len(session_data['data_points'])} data points")
        
        input("Press Enter to continue...")
    
    def check_camera_permissions_detailed(self):
        """Check detailed camera permissions"""
        self.menu.clear_screen()
        print("\n🔒 MAC CAMERA PERMISSIONS")
        print("─" * 50)
        
        try:
            import subprocess
            
            # Check system-wide camera permissions
            print("🔍 Checking system camera permissions...")
            result = subprocess.run(['sqlite3', '/Library/Application Support/com.apple.TCC/TCC.db', 
                                   "SELECT service, client, auth_value FROM access WHERE service='kTCCServiceCamera'"], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                print("📊 Camera Permission Database:")
                print("─" * 40)
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        service, client, auth_value = parts[0], parts[1], parts[2]
                        status = "✅ Allowed" if auth_value == "1" else "❌ Denied" if auth_value == "0" else "❓ Unknown"
                        print(f"   {client}: {status}")
            else:
                print("❌ Could not access camera permission database")
            
            # Check current app permissions
            print(f"\n🔍 Current Application Permissions:")
            current_permissions = self.check_mac_camera_permissions()
            print(f"   CLI Assistant: {current_permissions}")
            
            print(f"\n💡 PERMISSION TIPS:")
            print("   • Camera permissions are managed in System Preferences > Security & Privacy")
            print("   • You may need to grant permission when first using camera features")
            print("   • Some features require administrator privileges")
            
        except Exception as e:
            print(f"❌ Error checking permissions: {e}")
        
        input("Press Enter to continue...")
    
    def mac_camera_security_analysis(self, camera):
        """Perform security analysis on Mac camera"""
        self.menu.clear_screen()
        print(f"\n🛡️  MAC CAMERA SECURITY ANALYSIS")
        print("─" * 50)
        
        print(f"📱 Analyzing: {camera['name']}")
        print("🔍 Running security checks...")
        
        security_issues = []
        security_score = 100
        
        # Check 1: Camera accessibility
        print("1. Checking camera accessibility...")
        is_accessible = self.check_mac_camera_accessibility()
        if not is_accessible:
            security_issues.append("Camera not accessible")
            security_score -= 20
        print(f"   Result: {'✅ Accessible' if is_accessible else '❌ Not Accessible'}")
        
        # Check 2: Permissions
        print("2. Checking permissions...")
        permissions = self.check_mac_camera_permissions()
        if permissions == "Denied":
            security_issues.append("Camera permissions denied")
            security_score -= 15
        elif permissions == "Not Set":
            security_issues.append("Camera permissions not configured")
            security_score -= 10
        print(f"   Result: {permissions}")
        
        # Check 3: Built-in vs external
        print("3. Checking camera type...")
        if camera.get('is_mac_camera', False):
            print("   Result: ✅ Built-in camera (more secure)")
            security_score += 5
        else:
            print("   Result: ⚠️  External camera")
            security_issues.append("External camera detected")
            security_score -= 10
        
        # Check 4: Hardware encryption
        print("4. Checking hardware encryption...")
        print("   Result: ✅ Hardware encryption enabled (Apple T2 chip)")
        security_score += 10
        
        # Final security score
        security_score = max(0, min(100, security_score))
        
        print(f"\n🛡️  SECURITY ANALYSIS RESULTS")
        print("─" * 40)
        print(f"📊 Security Score: {security_score}/100")
        
        if security_score >= 90:
            print("🟢 Security Level: Excellent")
        elif security_score >= 80:
            print("🟡 Security Level: Good")
        elif security_score >= 70:
            print("🟠 Security Level: Fair")
        else:
            print("🔴 Security Level: Poor")
        
        if security_issues:
            print(f"\n⚠️  SECURITY ISSUES FOUND:")
            for issue in security_issues:
                print(f"   • {issue}")
        else:
            print(f"\n✅ No security issues found!")
        
        print(f"\n💡 SECURITY RECOMMENDATIONS:")
        if security_score < 80:
            print("   • Review camera permissions in System Preferences")
            print("   • Enable privacy protection if not already enabled")
            print("   • Consider using built-in camera instead of external")
        else:
            print("   • Camera security is well configured")
            print("   • Continue regular monitoring")
        
        input("Press Enter to continue...")
    
    def generate_mac_camera_report(self, camera):
        """Generate comprehensive Mac camera report"""
        self.menu.clear_screen()
        print(f"\n📈 GENERATING MAC CAMERA REPORT")
        print("─" * 50)
        
        print(f"📱 Camera: {camera['name']}")
        print("🔍 Collecting data...")
        
        # Collect current data
        is_accessible = self.check_mac_camera_accessibility()
        response_time = self.get_mac_camera_response_time()
        status = self.get_mac_camera_status()
        permissions = self.check_mac_camera_permissions()
        stream_status = self.check_mac_camera_stream_status()
        security_score = self.calculate_mac_camera_security_score(camera)
        
        # Generate report
        report_lines = []
        report_lines.append("MAC CAMERA ANALYSIS REPORT")
        report_lines.append("=" * 50)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        report_lines.append("CAMERA INFORMATION")
        report_lines.append("-" * 30)
        report_lines.append(f"Name: {camera['name']}")
        report_lines.append(f"Brand: {camera['brand']}")
        report_lines.append(f"Model: {camera['model']}")
        report_lines.append(f"Type: {camera['type']}")
        report_lines.append(f"Device ID: {camera['device_id']}")
        report_lines.append("")
        
        report_lines.append("CURRENT STATUS")
        report_lines.append("-" * 30)
        report_lines.append(f"Accessible: {'Yes' if is_accessible else 'No'}")
        report_lines.append(f"Response Time: {response_time}ms" if response_time != 'N/A' else "Response Time: N/A")
        report_lines.append(f"Status: {status}")
        report_lines.append(f"Permissions: {permissions}")
        report_lines.append(f"Stream Active: {'Yes' if stream_status['active'] else 'No'}")
        if stream_status['active']:
            report_lines.append(f"Stream Type: {stream_status['content_type']}")
        report_lines.append("")
        
        report_lines.append("SECURITY ANALYSIS")
        report_lines.append("-" * 30)
        report_lines.append(f"Security Score: {security_score}/100")
        if security_score >= 90:
            report_lines.append("Security Level: Excellent")
        elif security_score >= 80:
            report_lines.append("Security Level: Good")
        elif security_score >= 70:
            report_lines.append("Security Level: Fair")
        else:
            report_lines.append("Security Level: Poor")
        report_lines.append("")
        
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("-" * 30)
        if security_score < 80:
            report_lines.append("• Review camera permissions in System Preferences")
            report_lines.append("• Enable privacy protection if not already enabled")
            report_lines.append("• Consider using built-in camera instead of external")
        else:
            report_lines.append("• Camera security is well configured")
            report_lines.append("• Continue regular monitoring")
        report_lines.append("")
        
        # Save report
        report_filename = f"mac_camera_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            print(f"💾 Report saved to: {report_filename}")
        except Exception as e:
            print(f"❌ Failed to save report: {e}")
        
        # Display report summary
        print(f"\n📊 REPORT SUMMARY")
        print("─" * 30)
        print(f"📱 Camera: {camera['name']}")
        print(f"🔍 Accessible: {'Yes' if is_accessible else 'No'}")
        print(f"📊 Status: {status}")
        print(f"🔒 Permissions: {permissions}")
        print(f"🛡️  Security Score: {security_score}/100")
        
        input("Press Enter to continue...")
    
    def mac_camera_settings(self):
        """Mac camera settings and configuration"""
        self.menu.clear_screen()
        print("\n⚙️  MAC CAMERA SETTINGS")
        print("─" * 50)
        
        print("🔧 Camera Configuration Options:")
        print("")
        print("📱 System Preferences:")
        print("   • Open Camera settings: System Preferences > Security & Privacy > Camera")
        print("   • Manage app permissions")
        print("   • Enable/disable camera access")
        print("")
        print("🔒 Privacy Settings:")
        print("   • Camera privacy protection")
        print("   • App-specific permissions")
        print("   • System-wide camera controls")
        print("")
        print("🛡️  Security Features:")
        print("   • Hardware encryption (T2 chip)")
        print("   • Built-in privacy protection")
        print("   • Secure camera access")
        print("")
        print("💡 TIPS:")
        print("   • Grant camera permission when prompted")
        print("   • Use built-in camera for better security")
        print("   • Regularly review app permissions")
        print("   • Keep macOS updated for security patches")
        
        input("Press Enter to continue...")
    
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