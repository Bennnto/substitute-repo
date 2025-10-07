#!/usr/bin/env python3
"""
Enhanced CLI Assistant with improved iCloud Drive support
"""
import os
import sys
import subprocess
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import glob
import time

class iCloudDriveHelper:
    """Helper class for iCloud Drive operations"""
    
    def __init__(self):
        self.icloud_base = os.path.expanduser("~/Library/Mobile Documents")
        self.main_drive = os.path.join(self.icloud_base, "com~apple~CloudDocs")
        
    def get_icloud_paths(self):
        """Get all available iCloud Drive paths"""
        paths = {}
        try:
            # Main iCloud Drive
            if os.path.exists(self.main_drive):
                paths["📁 iCloud Drive (Main)"] = self.main_drive
                
            # App-specific iCloud folders
            for folder in os.listdir(self.icloud_base):
                if folder.startswith("iCloud~"):
                    full_path = os.path.join(self.icloud_base, folder)
                    if os.path.isdir(full_path):
                        # Clean up app name for display
                        app_name = folder.replace("iCloud~", "").replace("~", " - ")
                        # Add emoji for common apps
                        if "obsidian" in folder.lower():
                            emoji = "🧠"
                        elif "apple" in folder.lower():
                            emoji = "🍎"
                        elif "microsoft" in folder.lower():
                            emoji = "📊"
                        else:
                            emoji = "📱"
                        paths[f"{emoji} iCloud ({app_name})"] = full_path
                        
        except (OSError, PermissionError):
            pass
            
        return paths
    
    def force_download_file(self, file_path):
        """Force download of iCloud file if not locally available"""
        print(f"🔄 Attempting to download iCloud file: {os.path.basename(file_path)}")
        try:
            # Try using brctl to download the file
            result = subprocess.run(['brctl', 'download', file_path], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ File downloaded successfully")
                return True
            else:
                print(f"⚠️  brctl failed: {result.stderr}")
        except FileNotFoundError:
            print("📱 brctl not available, trying alternative method...")
            
        # Alternative method: try to access the file
        try:
            if os.path.exists(file_path):
                # Check if file is actually available (not just a placeholder)
                stat_info = os.stat(file_path)
                if stat_info.st_size > 0:
                    print("✅ File is already available locally")
                    return True
                else:
                    print("⏳ File exists but may still be downloading...")
                    # Wait a moment and check again
                    time.sleep(2)
                    stat_info = os.stat(file_path)
                    return stat_info.st_size > 0
        except OSError as e:
            print(f"❌ Error accessing file: {e}")
            
        return False
    
    def show_icloud_browser(self):
        """Interactive iCloud Drive browser"""
        paths = self.get_icloud_paths()
        
        if not paths:
            print("❌ No iCloud Drive folders found")
            return None
            
        print("\n🌤️  iCloud Drive Browser")
        print("=" * 50)
        
        # Show available iCloud locations
        for i, (name, path) in enumerate(paths.items(), 1):
            print(f"{i}. {name}")
            print(f"   📂 {path}")
            # Show folder size info
            try:
                items = len(os.listdir(path))
                print(f"   📊 {items} items")
            except:
                print("   ❌ Access denied")
            print()
        
        try:
            choice = int(input("Select iCloud location (number): ")) - 1
            if 0 <= choice < len(paths):
                selected_path = list(paths.values())[choice]
                print(f"\n📁 Selected: {selected_path}")
                return selected_path
            else:
                print("❌ Invalid selection")
                return None
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Cancelled")
            return None

# Test the enhanced iCloud functionality
if __name__ == "__main__":
    print("🌤️  Enhanced CLI Assistant - iCloud Drive Test")
    print("=" * 50)
    
    # Test iCloud helper
    icloud = iCloudDriveHelper()
    
    print("\n1. Testing iCloud Drive detection...")
    paths = icloud.get_icloud_paths()
    print(f"Found {len(paths)} iCloud Drive locations:")
    for name, path in paths.items():
        print(f"  {name}: {path}")
    
    print("\n2. Testing iCloud browser...")
    selected = icloud.show_icloud_browser()
    if selected:
        print(f"✅ You selected: {selected}")
    else:
        print("❌ No selection made")
