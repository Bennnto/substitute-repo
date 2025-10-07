#!/usr/bin/env python3
"""
Ultimate Cron Job Manager CLI Assistant
A visual terminal-based tool with dropdown-style menus for managing cron jobs
Author: Ben (Computer Programming Student @ George Brown College)
Version: 2.0 - Ultimate Edition
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import re

class UltimateCronManager:
    def __init__(self):
        self.cron_file = "/tmp/cron_jobs_backup.json"
        self.config_file = os.path.expanduser("~/cron_manager_config.json")
        self.load_cron_jobs()
        self.load_config()
    
    def load_config(self):
        """Load user preferences and configuration"""
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except:
            self.config = {
                'theme': 'default',
                'auto_backup': True,
                'log_directory': os.path.expanduser("~/cron_logs"),
                'default_editor': 'nano'
            }
    
    def save_config(self):
        """Save user configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save config: {e}")
    
    def load_cron_jobs(self):
        """Load existing cron jobs into memory"""
        try:
            result = subprocess.run(['crontab', '-l'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.jobs = self.parse_cron_jobs(result.stdout)
            else:
                self.jobs = []
        except Exception as e:
            print(f"❌ Error loading cron jobs: {e}")
            self.jobs = []
    
    def parse_cron_jobs(self, crontab_output: str) -> List[Dict]:
        """Parse crontab output into structured data"""
        jobs = []
        for line in crontab_output.strip().split('\n'):
            if line and not line.startswith('#'):
                parts = line.split()
                if len(parts) >= 6:
                    jobs.append({
                        'schedule': ' '.join(parts[:5]),
                        'command': ' '.join(parts[5:]),
                        'raw': line,
                        'enabled': True,
                        'created': datetime.now().isoformat()
                    })
        return jobs
    
    def display_header(self):
        """Display application header with enhanced styling"""
        os.system('clear' if os.name == 'posix' else 'cls')
        print("╔" + "═" * 70 + "╗")
        print("║" + " " * 20 + "🕐 ULTIMATE CRON JOB MANAGER" + " " * 20 + "║")
        print("║" + " " * 25 + "CLI ASSISTANT v2.0" + " " * 25 + "║")
        print("╠" + "═" * 70 + "╣")
        print("║ 👨‍💻 Author: Ben (Computer Programming Student)                    ║")
        print("║ 🎓 George Brown College, Toronto                                ║")
        print("║ 📧 ben.promkaew@icloud.com                                      ║")
        print("║ 🚀 Ultimate Edition - Dropdown Menus & Questionnaire Interface  ║")
        print("╚" + "═" * 70 + "╝")
    
    def show_dropdown_menu(self, title: str, options: List[Tuple[str, str]], 
                          allow_cancel: bool = True) -> Optional[int]:
        """Display a dropdown-style menu and get user selection"""
        print(f"\n📋 {title}")
        print("─" * 50)
        
        for i, (key, description) in enumerate(options, 1):
            print(f"{i:2d}. {key:<20} - {description}")
        
        if allow_cancel:
            print(f"{len(options) + 1:2d}. ❌ Cancel")
        
        print("─" * 50)
        
        while True:
            try:
                choice = input("🎯 Select option: ").strip()
                if not choice:
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(options):
                    return choice_num - 1
                elif allow_cancel and choice_num == len(options) + 1:
                    return None
                else:
                    print("❌ Invalid option! Please try again.")
            except ValueError:
                print("❌ Please enter a number!")
    
    def show_questionnaire(self, questions: List[Dict]) -> Dict:
        """Interactive questionnaire with various input types"""
        answers = {}
        
        for i, question in enumerate(questions, 1):
            print(f"\n📝 Question {i}/{len(questions)}: {question['text']}")
            
            if question['type'] == 'text':
                default = question.get('default', '')
                if default:
                    value = input(f"📝 Answer (default: {default}): ").strip()
                    answers[question['key']] = value if value else default
                else:
                    answers[question['key']] = input("📝 Answer: ").strip()
            
            elif question['type'] == 'dropdown':
                options = question['options']
                choice = self.show_dropdown_menu(question['text'], options)
                if choice is not None:
                    answers[question['key']] = options[choice][0]
                else:
                    return None
            
            elif question['type'] == 'yes_no':
                while True:
                    response = input(f"📝 {question['text']} (y/n): ").lower().strip()
                    if response in ['y', 'yes']:
                        answers[question['key']] = True
                        break
                    elif response in ['n', 'no']:
                        answers[question['key']] = False
                        break
                    else:
                        print("❌ Please enter 'y' or 'n'!")
            
            elif question['type'] == 'number':
                while True:
                    try:
                        value = input(f"📝 {question['text']}: ").strip()
                        num = int(value)
                        min_val = question.get('min', float('-inf'))
                        max_val = question.get('max', float('inf'))
                        if min_val <= num <= max_val:
                            answers[question['key']] = num
                            break
                        else:
                            print(f"❌ Number must be between {min_val} and {max_val}!")
                    except ValueError:
                        print("❌ Please enter a valid number!")
        
        return answers
    
    def display_main_menu(self):
        """Display enhanced main menu with categories"""
        main_options = [
            ("📋 View Jobs", "List and manage existing cron jobs"),
            ("➕ Create Job", "Add new cron job with wizard"),
            ("⚙️  Settings", "Configure application preferences"),
            ("📊 Analytics", "View statistics and reports"),
            ("🛠️  Tools", "Advanced tools and utilities"),
            ("❓ Help", "Documentation and examples"),
            ("🚪 Exit", "Save and exit application")
        ]
        
        return self.show_dropdown_menu("MAIN MENU", main_options)
    
    def display_view_menu(self):
        """Display view jobs submenu"""
        options = [
            ("📋 List All", "Show all cron jobs in table format"),
            ("🔍 Search", "Search jobs by command or schedule"),
            ("📊 Statistics", "View job patterns and analytics"),
            ("📄 Export", "Export jobs to file"),
            ("🔙 Back", "Return to main menu")
        ]
        
        return self.show_dropdown_menu("VIEW JOBS", options)
    
    def display_create_menu(self):
        """Display create job submenu"""
        options = [
            ("🎯 Quick Add", "Simple job creation wizard"),
            ("⚙️  Advanced", "Advanced job with custom options"),
            ("📋 Template", "Use predefined templates"),
            ("🔄 Import", "Import from file or backup"),
            ("🔙 Back", "Return to main menu")
        ]
        
        return self.show_dropdown_menu("CREATE JOB", options)
    
    def display_settings_menu(self):
        """Display settings submenu"""
        options = [
            ("🎨 Theme", "Change display theme"),
            ("💾 Auto Backup", "Configure automatic backups"),
            ("📁 Log Directory", "Set log file location"),
            ("🔧 Editor", "Choose default text editor"),
            ("🔙 Back", "Return to main menu")
        ]
        
        return self.show_dropdown_menu("SETTINGS", options)
    
    def display_tools_menu(self):
        """Display tools submenu"""
        options = [
            ("🧪 Test Command", "Test a command before adding"),
            ("📊 Monitor", "Real-time job monitoring"),
            ("🔧 Validate", "Validate cron syntax"),
            ("📤 Backup", "Backup/restore configurations"),
            ("🔙 Back", "Return to main menu")
        ]
        
        return self.show_dropdown_menu("TOOLS", options)
    
    def list_cron_jobs_enhanced(self):
        """Enhanced cron job listing with filtering and sorting"""
        if not self.jobs:
            print("\n📭 No cron jobs found.")
            print("💡 Use the Create Job option to add your first cron job!")
            return
        
        # Show filtering options
        filter_options = [
            ("📋 All Jobs", "Show all cron jobs"),
            ("⏰ By Schedule", "Filter by schedule pattern"),
            ("🔧 By Command", "Filter by command type"),
            ("📊 By Status", "Filter by enabled/disabled")
        ]
        
        filter_choice = self.show_dropdown_menu("FILTER JOBS", filter_options)
        if filter_choice is None:
            return
        
        # Apply filters
        filtered_jobs = self.jobs.copy()
        
        if filter_choice == 1:  # By Schedule
            schedule_options = [
                ("*/5 * * * *", "Every 5 minutes"),
                ("0 * * * *", "Every hour"),
                ("0 2 * * *", "Daily at 2 AM"),
                ("0 3 * * 0", "Weekly on Sunday"),
                ("Custom", "Custom schedule")
            ]
            schedule_choice = self.show_dropdown_menu("SELECT SCHEDULE PATTERN", schedule_options)
            if schedule_choice is not None:
                if schedule_choice < 4:
                    pattern = schedule_options[schedule_choice][0]
                    filtered_jobs = [job for job in filtered_jobs if job['schedule'] == pattern]
                else:
                    custom_pattern = input("🔧 Enter custom pattern: ").strip()
                    filtered_jobs = [job for job in filtered_jobs if custom_pattern in job['schedule']]
        
        elif filter_choice == 2:  # By Command
            command_type = input("🔧 Enter command type to search: ").strip()
            filtered_jobs = [job for job in filtered_jobs if command_type.lower() in job['command'].lower()]
        
        # Display filtered results
        print(f"\n📋 FOUND {len(filtered_jobs)} JOBS:")
        print("=" * 100)
        print(f"{'#':<3} {'Schedule':<20} {'Command':<50} {'Status':<10} {'Created':<15}")
        print("-" * 100)
        
        for i, job in enumerate(filtered_jobs, 1):
            schedule = job['schedule']
            command = job['command'][:47] + "..." if len(job['command']) > 50 else job['command']
            status = "✅ Active" if job.get('enabled', True) else "❌ Disabled"
            created = job.get('created', 'Unknown')[:10] if job.get('created') else 'Unknown'
            
            print(f"{i:<3} {schedule:<20} {command:<50} {status:<10} {created:<15}")
        
        print("-" * 100)
        print(f"📊 Total: {len(filtered_jobs)} jobs")
    
    def create_job_wizard(self):
        """Interactive job creation wizard with questionnaire"""
        print("\n🎯 CRON JOB CREATION WIZARD")
        print("=" * 50)
        
        questions = [
            {
                'key': 'command',
                'text': 'What command do you want to run?',
                'type': 'text',
                'default': ''
            },
            {
                'key': 'schedule_type',
                'text': 'How often should this job run?',
                'type': 'dropdown',
                'options': [
                    ("Every X minutes", "Run every few minutes"),
                    ("Every X hours", "Run every few hours"),
                    ("Daily", "Run once per day"),
                    ("Weekly", "Run once per week"),
                    ("Monthly", "Run once per month"),
                    ("Custom", "Custom cron expression")
                ]
            }
        ]
        
        answers = self.show_questionnaire(questions)
        if not answers:
            print("❌ Job creation cancelled.")
            return
        
        # Get schedule details based on type
        schedule = self.get_schedule_details(answers['schedule_type'])
        if not schedule:
            return
        
        # Additional options
        additional_questions = [
            {
                'key': 'add_logging',
                'text': 'Do you want to add logging?',
                'type': 'yes_no'
            },
            {
                'key': 'enabled',
                'text': 'Should this job be enabled immediately?',
                'type': 'yes_no'
            }
        ]
        
        additional_answers = self.show_questionnaire(additional_questions)
        if not additional_answers:
            return
        
        # Build final command
        command = answers['command']
        if additional_answers['add_logging']:
            log_file = input("📁 Log file path (default: ~/cron.log): ").strip()
            if not log_file:
                log_file = os.path.expanduser("~/cron.log")
            command += f" >> {log_file} 2>&1"
        
        # Create job object
        new_job = {
            'schedule': schedule,
            'command': command,
            'raw': f"{schedule} {command}",
            'enabled': additional_answers['enabled'],
            'created': datetime.now().isoformat()
        }
        
        # Confirm and add
        print(f"\n📋 NEW CRON JOB SUMMARY:")
        print(f"   Schedule: {schedule}")
        print(f"   Command: {command}")
        print(f"   Status: {'✅ Enabled' if additional_answers['enabled'] else '❌ Disabled'}")
        
        confirm = input("\n✅ Add this cron job? (y/n): ").lower().startswith('y')
        if confirm:
            self.jobs.append(new_job)
            self.save_cron_jobs()
            print("✅ Cron job added successfully!")
        else:
            print("❌ Job creation cancelled.")
    
    def get_schedule_details(self, schedule_type: str) -> Optional[str]:
        """Get detailed schedule based on type"""
        if schedule_type == "Every X minutes":
            questions = [
                {
                    'key': 'minutes',
                    'text': 'Every how many minutes?',
                    'type': 'number',
                    'min': 1,
                    'max': 59
                }
            ]
            answers = self.show_questionnaire(questions)
            if answers:
                return f"*/{answers['minutes']} * * * *"
        
        elif schedule_type == "Every X hours":
            questions = [
                {
                    'key': 'hours',
                    'text': 'Every how many hours?',
                    'type': 'number',
                    'min': 1,
                    'max': 23
                }
            ]
            answers = self.show_questionnaire(questions)
            if answers:
                return f"0 */{answers['hours']} * * *"
        
        elif schedule_type == "Daily":
            questions = [
                {
                    'key': 'hour',
                    'text': 'At what hour? (0-23)',
                    'type': 'number',
                    'min': 0,
                    'max': 23
                },
                {
                    'key': 'minute',
                    'text': 'At what minute? (0-59)',
                    'type': 'number',
                    'min': 0,
                    'max': 59
                }
            ]
            answers = self.show_questionnaire(questions)
            if answers:
                return f"{answers['minute']} {answers['hour']} * * *"
        
        elif schedule_type == "Weekly":
            questions = [
                {
                    'key': 'day',
                    'text': 'On which day of the week?',
                    'type': 'dropdown',
                    'options': [
                        ("0", "Sunday"),
                        ("1", "Monday"),
                        ("2", "Tuesday"),
                        ("3", "Wednesday"),
                        ("4", "Thursday"),
                        ("5", "Friday"),
                        ("6", "Saturday")
                    ]
                },
                {
                    'key': 'hour',
                    'text': 'At what hour? (0-23)',
                    'type': 'number',
                    'min': 0,
                    'max': 23
                }
            ]
            answers = self.show_questionnaire(questions)
            if answers:
                return f"0 {answers['hour']} * * {answers['day']}"
        
        elif schedule_type == "Monthly":
            questions = [
                {
                    'key': 'day',
                    'text': 'On which day of the month? (1-31)',
                    'type': 'number',
                    'min': 1,
                    'max': 31
                },
                {
                    'key': 'hour',
                    'text': 'At what hour? (0-23)',
                    'type': 'number',
                    'min': 0,
                    'max': 23
                }
            ]
            answers = self.show_questionnaire(questions)
            if answers:
                return f"0 {answers['hour']} {answers['day']} * *"
        
        elif schedule_type == "Custom":
            print("\n🔧 Enter custom cron expression:")
            print("Format: minute hour day month day_of_week")
            print("Example: */15 * * * * (every 15 minutes)")
            return input("📝 Schedule: ").strip()
        
        return None
    
    def test_command(self):
        """Test a command before adding to cron"""
        print("\n🧪 COMMAND TESTER")
        print("=" * 40)
        
        command = input("🔧 Enter command to test: ").strip()
        if not command:
            print("❌ Command cannot be empty!")
            return
        
        print(f"\n🧪 Testing: {command}")
        print("⏳ Executing...")
        
        try:
            start_time = time.time()
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            end_time = time.time()
            
            print(f"✅ Exit code: {result.returncode}")
            print(f"⏱️  Execution time: {end_time - start_time:.2f} seconds")
            
            if result.stdout:
                print(f"📤 Output:\n{result.stdout}")
            if result.stderr:
                print(f"⚠️  Errors:\n{result.stderr}")
            
            # Ask if user wants to add this command
            add_to_cron = input("\n❓ Add this command to cron? (y/n): ").lower().startswith('y')
            if add_to_cron:
                self.create_job_from_command(command)
                
        except subprocess.TimeoutExpired:
            print("⏰ Command timed out after 30 seconds")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def create_job_from_command(self, command: str):
        """Create cron job from tested command"""
        print("\n🎯 CREATE JOB FROM COMMAND")
        print("=" * 40)
        
        schedule_options = [
            ("*/5 * * * *", "Every 5 minutes"),
            ("*/15 * * * *", "Every 15 minutes"),
            ("0 * * * *", "Every hour"),
            ("0 2 * * *", "Daily at 2 AM"),
            ("Custom", "Custom schedule")
        ]
        
        choice = self.show_dropdown_menu("SELECT SCHEDULE", schedule_options)
        if choice is None:
            return
        
        if choice == 4:  # Custom
            schedule = input("🔧 Enter custom schedule: ").strip()
        else:
            schedule = schedule_options[choice][0]
        
        # Add logging
        add_logging = input("📊 Add logging? (y/n): ").lower().startswith('y')
        if add_logging:
            log_file = input("📁 Log file path (default: ~/cron.log): ").strip()
            if not log_file:
                log_file = os.path.expanduser("~/cron.log")
            command += f" >> {log_file} 2>&1"
        
        new_job = {
            'schedule': schedule,
            'command': command,
            'raw': f"{schedule} {command}",
            'enabled': True,
            'created': datetime.now().isoformat()
        }
        
        self.jobs.append(new_job)
        self.save_cron_jobs()
        print("✅ Cron job created successfully!")
    
    def show_statistics(self):
        """Show enhanced statistics"""
        print("\n📊 CRON JOB STATISTICS")
        print("=" * 50)
        
        if not self.jobs:
            print("📭 No jobs to analyze!")
            return
        
        print(f"📋 Total jobs: {len(self.jobs)}")
        print(f"✅ Active jobs: {len([j for j in self.jobs if j.get('enabled', True)])}")
        print(f"❌ Disabled jobs: {len([j for j in self.jobs if not j.get('enabled', True)])}")
        
        # Schedule analysis
        schedules = [job['schedule'] for job in self.jobs]
        unique_schedules = len(set(schedules))
        print(f"⏰ Unique schedules: {unique_schedules}")
        
        # Pattern analysis
        patterns = {
            'Every X minutes': 0,
            'Every X hours': 0,
            'Daily': 0,
            'Weekly': 0,
            'Monthly': 0,
            'Custom': 0
        }
        
        for schedule in schedules:
            if schedule.startswith('*/') and schedule.endswith(' * * * *'):
                patterns['Every X minutes'] += 1
            elif schedule.startswith('0 */') and schedule.endswith(' * * *'):
                patterns['Every X hours'] += 1
            elif schedule.endswith(' * * *'):
                patterns['Daily'] += 1
            elif schedule.endswith(' * * 0'):
                patterns['Weekly'] += 1
            elif schedule.endswith(' * *'):
                patterns['Monthly'] += 1
            else:
                patterns['Custom'] += 1
        
        print("\n📈 Schedule Patterns:")
        for pattern, count in patterns.items():
            if count > 0:
                print(f"   {pattern}: {count}")
    
    def show_help(self):
        """Show comprehensive help"""
        print("\n📚 CRON JOB MANAGER HELP")
        print("=" * 60)
        
        help_sections = [
            ("📋 Main Menu", "Navigate through different sections"),
            ("➕ Create Job", "Add new cron jobs with wizard"),
            ("📊 View Jobs", "List and manage existing jobs"),
            ("⚙️  Settings", "Configure application preferences"),
            ("🛠️  Tools", "Advanced utilities and testing"),
            ("📚 Help", "This help section")
        ]
        
        for title, description in help_sections:
            print(f"{title}: {description}")
        
        print("\n🔧 CRON SYNTAX:")
        print("Format: minute hour day month day_of_week")
        print("Examples:")
        print("  */5 * * * *     - Every 5 minutes")
        print("  0 * * * *       - Every hour")
        print("  0 2 * * *       - Daily at 2 AM")
        print("  0 3 * * 0       - Weekly on Sunday at 3 AM")
        print("  0 4 1 * *       - Monthly on 1st at 4 AM")
    
    def save_cron_jobs(self):
        """Save cron jobs to crontab"""
        try:
            crontab_content = ""
            for job in self.jobs:
                if job.get('enabled', True):
                    crontab_content += f"{job['raw']}\n"
            
            with open('/tmp/crontab_temp', 'w') as f:
                f.write(crontab_content)
            
            subprocess.run(['crontab', '/tmp/crontab_temp'], check=True)
            os.remove('/tmp/crontab_temp')
            
            # Auto backup if enabled
            if self.config.get('auto_backup', True):
                self.backup_jobs()
                
        except Exception as e:
            print(f"❌ Error saving cron jobs: {e}")
    
    def backup_jobs(self):
        """Backup current jobs"""
        try:
            with open(self.cron_file, 'w') as f:
                json.dump(self.jobs, f, indent=2)
        except Exception as e:
            print(f"⚠️  Backup failed: {e}")
    
    def run(self):
        """Main application loop"""
        while True:
            self.display_header()
            choice = self.display_main_menu()
            
            if choice is None:
                break
            
            if choice == 0:  # View Jobs
                self.handle_view_menu()
            elif choice == 1:  # Create Job
                self.handle_create_menu()
            elif choice == 2:  # Settings
                self.handle_settings_menu()
            elif choice == 3:  # Analytics
                self.show_statistics()
            elif choice == 4:  # Tools
                self.handle_tools_menu()
            elif choice == 5:  # Help
                self.show_help()
            elif choice == 6:  # Exit
                print("\n👋 Thanks for using Ultimate Cron Job Manager!")
                print("🚀 Keep learning and building amazing things!")
                self.save_config()
                break
            
            input("\n⏳ Press Enter to continue...")
    
    def handle_view_menu(self):
        """Handle view jobs submenu"""
        while True:
            choice = self.display_view_menu()
            if choice is None or choice == 4:  # Back
                break
            elif choice == 0:  # List All
                self.list_cron_jobs_enhanced()
            elif choice == 1:  # Search
                self.search_jobs()
            elif choice == 2:  # Statistics
                self.show_statistics()
            elif choice == 3:  # Export
                self.export_jobs()
    
    def handle_create_menu(self):
        """Handle create job submenu"""
        while True:
            choice = self.display_create_menu()
            if choice is None or choice == 4:  # Back
                break
            elif choice == 0:  # Quick Add
                self.create_job_wizard()
            elif choice == 1:  # Advanced
                self.create_advanced_job()
            elif choice == 2:  # Template
                self.create_from_template()
            elif choice == 3:  # Import
                self.import_jobs()
    
    def handle_settings_menu(self):
        """Handle settings submenu"""
        while True:
            choice = self.display_settings_menu()
            if choice is None or choice == 4:  # Back
                break
            elif choice == 0:  # Theme
                self.change_theme()
            elif choice == 1:  # Auto Backup
                self.toggle_auto_backup()
            elif choice == 2:  # Log Directory
                self.set_log_directory()
            elif choice == 3:  # Editor
                self.set_editor()
    
    def handle_tools_menu(self):
        """Handle tools submenu"""
        while True:
            choice = self.display_tools_menu()
            if choice is None or choice == 4:  # Back
                break
            elif choice == 0:  # Test Command
                self.test_command()
            elif choice == 1:  # Monitor
                self.monitor_jobs()
            elif choice == 2:  # Validate
                self.validate_syntax()
            elif choice == 3:  # Backup
                self.backup_restore()
    
    def search_jobs(self):
        """Search jobs by criteria"""
        print("\n🔍 SEARCH JOBS")
        print("=" * 30)
        
        search_term = input("🔍 Enter search term: ").strip()
        if not search_term:
            return
        
        results = []
        for job in self.jobs:
            if (search_term.lower() in job['command'].lower() or 
                search_term.lower() in job['schedule'].lower()):
                results.append(job)
        
        print(f"\n📋 FOUND {len(results)} MATCHES:")
        for i, job in enumerate(results, 1):
            print(f"{i}. {job['schedule']} - {job['command']}")
    
    def export_jobs(self):
        """Export jobs to file"""
        print("\n📤 EXPORT JOBS")
        print("=" * 30)
        
        filename = input("📁 Export filename (default: cron_jobs.json): ").strip()
        if not filename:
            filename = "cron_jobs.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.jobs, f, indent=2)
            print(f"✅ Jobs exported to {filename}")
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    def create_advanced_job(self):
        """Create job with advanced options"""
        print("\n⚙️  ADVANCED JOB CREATION")
        print("=" * 40)
        # Implementation for advanced job creation
        print("🔧 Advanced features coming soon!")
    
    def create_from_template(self):
        """Create job from template"""
        print("\n📋 TEMPLATE JOB CREATION")
        print("=" * 40)
        
        templates = [
            ("System Monitor", "Monitor system resources"),
            ("Backup Script", "Backup important files"),
            ("Cleanup Script", "Clean temporary files"),
            ("Custom Template", "Create your own template")
        ]
        
        choice = self.show_dropdown_menu("SELECT TEMPLATE", templates)
        if choice is not None:
            print("🔧 Template system coming soon!")
    
    def import_jobs(self):
        """Import jobs from file"""
        print("\n📥 IMPORT JOBS")
        print("=" * 30)
        
        filename = input("📁 Import filename: ").strip()
        if not filename:
            return
        
        try:
            with open(filename, 'r') as f:
                imported_jobs = json.load(f)
            
            self.jobs.extend(imported_jobs)
            self.save_cron_jobs()
            print(f"✅ Imported {len(imported_jobs)} jobs")
        except Exception as e:
            print(f"❌ Import failed: {e}")
    
    def change_theme(self):
        """Change display theme"""
        print("\n🎨 THEME SETTINGS")
        print("=" * 30)
        
        themes = [
            ("default", "Default theme"),
            ("dark", "Dark theme"),
            ("colorful", "Colorful theme"),
            ("minimal", "Minimal theme")
        ]
        
        choice = self.show_dropdown_menu("SELECT THEME", themes)
        if choice is not None:
            self.config['theme'] = themes[choice][0]
            self.save_config()
            print("✅ Theme updated!")
    
    def toggle_auto_backup(self):
        """Toggle automatic backup"""
        current = self.config.get('auto_backup', True)
        self.config['auto_backup'] = not current
        self.save_config()
        status = "enabled" if self.config['auto_backup'] else "disabled"
        print(f"✅ Auto backup {status}!")
    
    def set_log_directory(self):
        """Set log directory"""
        print("\n📁 LOG DIRECTORY SETTINGS")
        print("=" * 40)
        
        current = self.config.get('log_directory', os.path.expanduser("~/cron_logs"))
        print(f"Current: {current}")
        
        new_dir = input("New directory (press Enter to keep current): ").strip()
        if new_dir:
            self.config['log_directory'] = new_dir
            self.save_config()
            print("✅ Log directory updated!")
    
    def set_editor(self):
        """Set default text editor"""
        print("\n🔧 EDITOR SETTINGS")
        print("=" * 30)
        
        editors = [
            ("nano", "Nano (simple)"),
            ("vim", "Vim (advanced)"),
            ("code", "VS Code"),
            ("subl", "Sublime Text")
        ]
        
        choice = self.show_dropdown_menu("SELECT EDITOR", editors)
        if choice is not None:
            self.config['default_editor'] = editors[choice][0]
            self.save_config()
            print("✅ Editor updated!")
    
    def monitor_jobs(self):
        """Real-time job monitoring"""
        print("\n📊 REAL-TIME MONITORING")
        print("=" * 40)
        print("🔧 Monitoring features coming soon!")
    
    def validate_syntax(self):
        """Validate cron syntax"""
        print("\n🔧 SYNTAX VALIDATION")
        print("=" * 30)
        
        for i, job in enumerate(self.jobs, 1):
            schedule = job['schedule']
            parts = schedule.split()
            
            if len(parts) != 5:
                print(f"❌ Job {i}: Invalid format")
            else:
                print(f"✅ Job {i}: Valid syntax")
    
    def backup_restore(self):
        """Backup and restore functionality"""
        print("\n💾 BACKUP & RESTORE")
        print("=" * 30)
        
        options = [
            ("💾 Backup", "Save current jobs"),
            ("📂 Restore", "Load from backup"),
            ("📤 Export", "Export to file"),
            ("📥 Import", "Import from file")
        ]
        
        choice = self.show_dropdown_menu("BACKUP OPTIONS", options)
        if choice == 0:  # Backup
            self.backup_jobs()
            print("✅ Backup completed!")
        elif choice == 1:  # Restore
            if os.path.exists(self.cron_file):
                try:
                    with open(self.cron_file, 'r') as f:
                        self.jobs = json.load(f)
                    self.save_cron_jobs()
                    print("✅ Restore completed!")
                except Exception as e:
                    print(f"❌ Restore failed: {e}")
            else:
                print("❌ No backup file found!")

def main():
    """Main entry point"""
    try:
        manager = UltimateCronManager()
        manager.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main() 