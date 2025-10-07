"""
Simple File Tree Operations - Common Use Cases
"""

import os
from pathlib import Path
import shutil

def basic_directory_listing():
    """List all files and directories in current folder"""
    print("Current directory contents:")
    for item in os.listdir('.'):
        if os.path.isdir(item):
            print(f"📁 {item}/")
        else:
            print(f"📄 {item}")

def find_specific_files():
    """Find specific types of files"""
    # Using pathlib (recommended)
    current_dir = Path('.')
    
    # Find all Python files
    python_files = list(current_dir.glob('*.py'))
    print(f"\nPython files ({len(python_files)}):")
    for file in python_files:
        print(f"  🐍 {file.name}")
    
    # Find all Jupyter notebooks
    notebooks = list(current_dir.glob('*.ipynb'))
    print(f"\nJupyter notebooks ({len(notebooks)}):")
    for nb in notebooks:
        print(f"  📓 {nb.name}")

def traverse_subdirectories():
    """Walk through all subdirectories"""
    print("\nDirectory tree structure:")
    
    for root, dirs, files in os.walk('.'):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        level = root.replace('.', '').count(os.sep)
        indent = '  ' * level
        folder_name = os.path.basename(root) or '.'
        print(f'{indent}📁 {folder_name}/')
        
        # Show files in this directory
        sub_indent = '  ' * (level + 1)
        for file in files:
            if not file.startswith('.'):  # Skip hidden files
                print(f'{sub_indent}📄 {file}')

def file_information():
    """Get information about files"""
    print("\nFile information for Python files:")
    
    for file_path in Path('.').glob('*.py'):
        stat = file_path.stat()
        size = stat.st_size
        print(f"📄 {file_path.name}")
        print(f"   Size: {size} bytes")
        print(f"   Lines: {len(file_path.read_text().splitlines())} lines")
        print()

def create_and_organize_files():
    """Example of creating and organizing files"""
    # Create a test directory
    test_dir = Path('example_project')
    test_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    (test_dir / 'src').mkdir(exist_ok=True)
    (test_dir / 'tests').mkdir(exist_ok=True)
    (test_dir / 'docs').mkdir(exist_ok=True)
    
    # Create some example files
    (test_dir / 'README.md').write_text('# Example Project')
    (test_dir / 'src' / 'main.py').write_text('print("Hello World")')
    (test_dir / 'tests' / 'test_main.py').write_text('def test_main(): pass')
    (test_dir / 'docs' / 'guide.txt').write_text('User guide')
    
    print(f"Created example project structure:")
    
    # Show the created structure
    for root, dirs, files in os.walk(test_dir):
        level = root.replace(str(test_dir), '').count(os.sep)
        indent = '  ' * level
        folder_name = os.path.basename(root)
        print(f'{indent}📁 {folder_name}/')
        
        sub_indent = '  ' * (level + 1)
        for file in files:
            print(f'{sub_indent}📄 {file}')
    
    # Clean up
    shutil.rmtree(test_dir)
    print(f"\nCleaned up {test_dir}")

if __name__ == "__main__":
    print("=== Simple File Tree Operations ===\n")
    
    basic_directory_listing()
    find_specific_files()
    traverse_subdirectories()
    file_information()
    create_and_organize_files()