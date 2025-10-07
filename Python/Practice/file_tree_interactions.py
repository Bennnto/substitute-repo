"""
File Tree Interactions in Python
This file demonstrates various ways to work with file trees and directory structures
"""

import os
import glob
import pathlib
from pathlib import Path
import shutil
import fnmatch

def method1_os_walk():
    """Using os.walk() - Most common method for traversing directories"""
    print("=== Method 1: Using os.walk() ===")
    
    # Walk through directory tree
    for root, dirs, files in os.walk('.'):
        level = root.replace('.', '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        
        # Print files
        sub_indent = ' ' * 2 * (level + 1)
        for file in files:
            print(f'{sub_indent}{file}')
        
        # Optional: Skip certain directories
        if '.git' in dirs:
            dirs.remove('.git')  # Don't descend into .git
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')

def method2_pathlib():
    """Using pathlib - Modern Python approach"""
    print("\n=== Method 2: Using pathlib ===")
    
    path = Path('.')
    
    # Recursive glob for all files
    print("All Python files:")
    for py_file in path.rglob('*.py'):
        print(f"  {py_file}")
    
    print("\nAll directories:")
    for directory in path.rglob('*'):
        if directory.is_dir():
            print(f"  {directory}/")

def method3_os_listdir():
    """Using os.listdir() - Basic directory listing"""
    print("\n=== Method 3: Using os.listdir() ===")
    
    def list_directory(path, level=0):
        items = os.listdir(path)
        items.sort()
        
        for item in items:
            item_path = os.path.join(path, item)
            indent = '  ' * level
            
            if os.path.isdir(item_path):
                print(f"{indent}{item}/")
                # Recursively list subdirectories (limit depth)
                if level < 2:
                    list_directory(item_path, level + 1)
            else:
                print(f"{indent}{item}")
    
    list_directory('.')

def method4_glob():
    """Using glob - Pattern matching for files"""
    print("\n=== Method 4: Using glob ===")
    
    # Find all Python files
    python_files = glob.glob('**/*.py', recursive=True)
    print("Python files found:")
    for file in python_files:
        print(f"  {file}")
    
    # Find all files starting with 'D'
    d_files = glob.glob('D*')
    print("\nFiles starting with 'D':")
    for file in d_files:
        print(f"  {file}")

def method5_file_operations():
    """Common file operations"""
    print("\n=== Method 5: File Operations ===")
    
    # Create a test directory structure
    test_dir = Path('test_structure')
    
    try:
        # Create directories
        test_dir.mkdir(exist_ok=True)
        (test_dir / 'subdir1').mkdir(exist_ok=True)
        (test_dir / 'subdir2').mkdir(exist_ok=True)
        
        # Create some test files
        (test_dir / 'file1.txt').write_text('Hello World 1')
        (test_dir / 'subdir1' / 'file2.txt').write_text('Hello World 2')
        (test_dir / 'subdir2' / 'file3.py').write_text('print("Hello from Python")')
        
        print("Created test directory structure:")
        
        # List the created structure
        for root, dirs, files in os.walk(test_dir):
            level = root.replace(str(test_dir), '').count(os.sep)
            indent = '  ' * level
            print(f'{indent}{os.path.basename(root)}/')
            sub_indent = '  ' * (level + 1)
            for file in files:
                print(f'{sub_indent}{file}')
        
        # File operations
        print(f"\nFile operations:")
        file_path = test_dir / 'file1.txt'
        print(f"File exists: {file_path.exists()}")
        print(f"File size: {file_path.stat().st_size} bytes")
        print(f"File content: {file_path.read_text()}")
        
    except Exception as e:
        print(f"Error: {e}")

def method6_advanced_filtering():
    """Advanced file filtering and searching"""
    print("\n=== Method 6: Advanced Filtering ===")
    
    def find_files_by_pattern(directory, pattern):
        """Find files matching a pattern"""
        matches = []
        for root, dirs, files in os.walk(directory):
            for filename in fnmatch.filter(files, pattern):
                matches.append(os.path.join(root, filename))
        return matches
    
    def find_files_by_size(directory, min_size=0, max_size=float('inf')):
        """Find files within size range"""
        matches = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    size = os.path.getsize(filepath)
                    if min_size <= size <= max_size:
                        matches.append((filepath, size))
                except (OSError, IOError):
                    continue
        return matches
    
    # Find Python files
    py_files = find_files_by_pattern('.', '*.py')
    print("Python files found with pattern matching:")
    for file in py_files[:5]:  # Show first 5
        print(f"  {file}")
    
    # Find files by size
    small_files = find_files_by_size('.', max_size=1000)
    print(f"\nSmall files (< 1KB): {len(small_files)} found")
    for file, size in small_files[:3]:
        print(f"  {file} ({size} bytes)")

def method7_file_tree_visualization():
    """Create a visual representation of file tree"""
    print("\n=== Method 7: File Tree Visualization ===")
    
    def print_tree(directory, prefix="", max_depth=3, current_depth=0):
        """Print directory tree structure"""
        if current_depth >= max_depth:
            return
            
        path = Path(directory)
        if not path.is_dir():
            return
            
        items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            print(f"{prefix}{current_prefix}{item.name}")
            
            if item.is_dir() and current_depth < max_depth - 1:
                extension = "    " if is_last else "│   "
                print_tree(item, prefix + extension, max_depth, current_depth + 1)
    
    print("Directory tree visualization:")
    print_tree('.', max_depth=2)

def cleanup():
    """Clean up test files"""
    test_dir = Path('test_structure')
    if test_dir.exists():
        shutil.rmtree(test_dir)
        print(f"\nCleaned up {test_dir}")

if __name__ == "__main__":
    print("File Tree Interaction Examples\n")
    
    # Run all examples
    method1_os_walk()
    method2_pathlib()
    method3_os_listdir()
    method4_glob()
    method5_file_operations()
    method6_advanced_filtering()
    method7_file_tree_visualization()
    
    # Cleanup
    cleanup()
    
    print("\n" + "="*50)
    print("SUMMARY OF METHODS:")
    print("="*50)
    print("1. os.walk() - Best for recursive directory traversal")
    print("2. pathlib - Modern, object-oriented approach")
    print("3. os.listdir() - Simple directory listing")
    print("4. glob - Pattern matching for files")
    print("5. File operations - Creating, reading, writing files")
    print("6. Advanced filtering - Custom search functions")
    print("7. Tree visualization - Pretty print directory structure")