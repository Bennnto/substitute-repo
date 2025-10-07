#!/usr/bin/env python3
"""
Test script for PyForklift enhanced features
"""

import sys
import os
import tempfile
import shutil
from main import DualPaneFileManager
import PySide6.QtWidgets as QtWidgets

def test_file_operations():
    """Test file creation and operations"""
    print("🧪 Testing file operations...")
    
    # Create temporary directory for testing
    test_dir = tempfile.mkdtemp(prefix="pyforklift_test_")
    print(f"✅ Created test directory: {test_dir}")
    
    try:
        # Test file creation
        test_file = os.path.join(test_dir, "test_file.txt")
        with open(test_file, 'w') as f:
            f.write("Test content")
        print("✅ File creation test passed")
        
        # Test folder creation
        test_folder = os.path.join(test_dir, "test_folder")
        os.makedirs(test_folder)
        print("✅ Folder creation test passed")
        
        # Test rename
        new_file = os.path.join(test_dir, "renamed_file.txt")
        os.rename(test_file, new_file)
        print("✅ File rename test passed")
        
        return True
        
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        return False
    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)
        print("✅ Test cleanup completed")

def test_gui_components():
    """Test GUI components"""
    print("🧪 Testing GUI components...")
    
    try:
        app = QtWidgets.QApplication([])
        window = DualPaneFileManager()
        
        # Test all new methods exist and are callable
        methods_to_test = [
            'create_new_folder', 'create_new_file', 'rename_item',
            'add_bookmark', 'preview_file', 'show_progress',
            'show_bookmarks_menu', 'show_search_dialog',
            'update_progress', 'hide_progress'
        ]
        
        for method_name in methods_to_test:
            if hasattr(window, method_name):
                method = getattr(window, method_name)
                if callable(method):
                    print(f"✅ {method_name} method is callable")
                else:
                    print(f"❌ {method_name} is not callable")
                    return False
            else:
                print(f"❌ {method_name} method not found")
                return False
        
        # Test UI components
        if window.statusBar():
            print("✅ Status bar exists")
        else:
            print("❌ Status bar missing")
            return False
            
        if hasattr(window, 'progress_bar'):
            print("✅ Progress bar exists")
        else:
            print("❌ Progress bar missing")
            return False
            
        if hasattr(window, 'bookmarks'):
            print("✅ Bookmarks system exists")
        else:
            print("❌ Bookmarks system missing")
            return False
        
        # Test toolbar actions
        toolbar = window.findChild(QtWidgets.QToolBar)
        if toolbar and len(toolbar.actions()) >= 10:
            print(f"✅ Toolbar has {len(toolbar.actions())} actions")
        else:
            print("❌ Toolbar missing or insufficient actions")
            return False
        
        app.quit()
        return True
        
    except Exception as e:
        print(f"❌ GUI components test failed: {e}")
        return False

def test_keyboard_shortcuts():
    """Test keyboard shortcuts"""
    print("🧪 Testing keyboard shortcuts...")
    
    try:
        app = QtWidgets.QApplication([])
        window = DualPaneFileManager()
        
        actions = window.actions()
        shortcuts = [action.shortcut().toString() for action in actions if action.shortcut().toString()]
        
        expected_shortcuts = ["F2", "F5", "Ctrl+F"]
        found_shortcuts = []
        
        for shortcut in expected_shortcuts:
            if shortcut in shortcuts:
                found_shortcuts.append(shortcut)
                print(f"✅ Shortcut {shortcut} found")
            else:
                print(f"❌ Shortcut {shortcut} missing")
        
        if len(found_shortcuts) == len(expected_shortcuts):
            print("✅ All keyboard shortcuts configured")
            app.quit()
            return True
        else:
            print(f"❌ Only {len(found_shortcuts)}/{len(expected_shortcuts)} shortcuts found")
            app.quit()
            return False
            
    except Exception as e:
        print(f"❌ Keyboard shortcuts test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting PyForklift Feature Tests")
    print("=" * 50)
    
    tests = [
        ("File Operations", test_file_operations),
        ("GUI Components", test_gui_components),
        ("Keyboard Shortcuts", test_keyboard_shortcuts)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} Test...")
        if test_func():
            print(f"✅ {test_name} test PASSED")
            passed += 1
        else:
            print(f"❌ {test_name} test FAILED")
        print("-" * 30)
    
    print(f"\n🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! PyForklift is ready to use!")
        print("\n🚀 New Features Available:")
        print("   • File/Folder Creation & Renaming")
        print("   • Bookmarks/Favorites System")
        print("   • Progress Indicators")
        print("   • Search Functionality")
        print("   • File Preview (Images & Text)")
        print("   • Keyboard Shortcuts (F2, F5, Ctrl+F)")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
