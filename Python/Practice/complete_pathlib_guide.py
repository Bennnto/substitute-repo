"""
Complete pathlib Guide - Modern File Path Handling in Python
pathlib was introduced in Python 3.4 and is the recommended way to work with file paths
"""

from pathlib import Path, PurePath
import os
import shutil
from datetime import datetime

def basic_path_creation():
    """Creating Path objects"""
    print("=== 1. Creating Path Objects ===")
    
    # Different ways to create paths
    p1 = Path('.')  # Current directory
    p2 = Path('/Users/username/Documents')  # Absolute path
    p3 = Path('folder', 'subfolder', 'file.txt')  # Join parts
    p4 = Path.home()  # User home directory
    p5 = Path.cwd()  # Current working directory
    
    print(f"Current directory: {p1}")
    print(f"Absolute path: {p2}")
    print(f"Joined path: {p3}")
    print(f"Home directory: {p4}")
    print(f"Current working directory: {p5}")
    
    # Path from string
    path_str = "/Users/username/file.txt"
    p6 = Path(path_str)
    print(f"From string: {p6}")

def path_properties():
    """Path properties and attributes"""
    print("\n=== 2. Path Properties ===")
    
    p = Path('folder/subfolder/document.txt')
    
    print(f"Full path: {p}")
    print(f"Name (filename): {p.name}")
    print(f"Stem (name without extension): {p.stem}")
    print(f"Suffix (extension): {p.suffix}")
    print(f"Suffixes (all extensions): {p.suffixes}")
    print(f"Parent directory: {p.parent}")
    print(f"All parents: {list(p.parents)}")
    print(f"Parts: {p.parts}")
    print(f"Anchor (root): {p.anchor}")
    
    # Multiple extensions example
    p2 = Path('archive.tar.gz')
    print(f"\nMultiple extensions example: {p2}")
    print(f"Stem: {p2.stem}")
    print(f"Suffix: {p2.suffix}")
    print(f"Suffixes: {p2.suffixes}")

def path_operations():
    """Path manipulation operations"""
    print("\n=== 3. Path Operations ===")
    
    p = Path('documents/projects')
    
    # Joining paths
    new_path = p / 'python' / 'script.py'
    print(f"Joined path: {new_path}")
    
    # Alternative joining
    new_path2 = p.joinpath('python', 'script.py')
    print(f"Joinpath method: {new_path2}")
    
    # Changing parts of path
    p3 = Path('folder/file.txt')
    print(f"Original: {p3}")
    print(f"With different name: {p3.with_name('newfile.txt')}")
    print(f"With different suffix: {p3.with_suffix('.py')}")
    print(f"With different stem: {p3.with_stem('newname')}")
    
    # Resolving paths
    current = Path('.')
    print(f"Relative path: {current}")
    print(f"Absolute path: {current.resolve()}")
    
    # Making relative paths
    abs_path = Path.cwd() / 'subfolder' / 'file.txt'
    relative = abs_path.relative_to(Path.cwd())
    print(f"Made relative: {relative}")

def file_system_checks():
    """Checking file system properties"""
    print("\n=== 4. File System Checks ===")
    
    # Create a test file for demonstration
    test_file = Path('test_file.txt')
    test_file.write_text('Hello World')
    
    test_dir = Path('test_directory')
    test_dir.mkdir(exist_ok=True)
    
    print(f"File exists: {test_file.exists()}")
    print(f"Is file: {test_file.is_file()}")
    print(f"Is directory: {test_file.is_dir()}")
    print(f"Is symlink: {test_file.is_symlink()}")
    
    print(f"Directory exists: {test_dir.exists()}")
    print(f"Is directory: {test_dir.is_dir()}")
    
    # File stats
    stat = test_file.stat()
    print(f"File size: {stat.st_size} bytes")
    print(f"Modified time: {datetime.fromtimestamp(stat.st_mtime)}")
    
    # Cleanup
    test_file.unlink()
    test_dir.rmdir()

def directory_operations():
    """Working with directories"""
    print("\n=== 5. Directory Operations ===")
    
    # Create directory structure
    base_dir = Path('example_project')
    base_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    (base_dir / 'src').mkdir(exist_ok=True)
    (base_dir / 'tests').mkdir(exist_ok=True)
    (base_dir / 'docs').mkdir(parents=True, exist_ok=True)
    
    # Create nested structure
    nested = base_dir / 'deep' / 'nested' / 'structure'
    nested.mkdir(parents=True, exist_ok=True)
    
    print("Created directory structure:")
    
    # List directory contents
    print(f"Contents of {base_dir}:")
    for item in base_dir.iterdir():
        if item.is_dir():
            print(f"  📁 {item.name}/")
        else:
            print(f"  📄 {item.name}")
    
    # Cleanup
    shutil.rmtree(base_dir)

def file_operations():
    """File reading and writing"""
    print("\n=== 6. File Operations ===")
    
    # Create test file
    test_file = Path('sample.txt')
    
    # Write text
    test_file.write_text('Hello World\nLine 2\nLine 3')
    print(f"Written to {test_file}")
    
    # Read text
    content = test_file.read_text()
    print(f"Content:\n{content}")
    
    # Read lines
    lines = test_file.read_text().splitlines()
    print(f"Lines: {lines}")
    
    # Write binary
    binary_file = Path('binary.dat')
    binary_file.write_bytes(b'\x00\x01\x02\x03')
    
    # Read binary
    binary_content = binary_file.read_bytes()
    print(f"Binary content: {binary_content}")
    
    # Open file (traditional way still available)
    with test_file.open('r') as f:
        first_line = f.readline()
        print(f"First line: {first_line.strip()}")
    
    # Cleanup
    test_file.unlink()
    binary_file.unlink()

def pattern_matching():
    """Finding files with patterns"""
    print("\n=== 7. Pattern Matching (glob) ===")
    
    current_dir = Path('.')
    
    # Find Python files
    python_files = list(current_dir.glob('*.py'))
    print(f"Python files: {len(python_files)}")
    for file in python_files[:3]:  # Show first 3
        print(f"  {file}")
    
    # Recursive search
    all_python = list(current_dir.rglob('*.py'))
    print(f"All Python files (recursive): {len(all_python)}")
    
    # Multiple patterns
    patterns = ['*.py', '*.txt', '*.md']
    all_files = []
    for pattern in patterns:
        all_files.extend(current_dir.glob(pattern))
    
    print(f"Files matching multiple patterns: {len(all_files)}")
    
    # Advanced patterns
    # ? matches single character
    # * matches any number of characters
    # ** matches directories recursively
    # [seq] matches any character in seq
    # [!seq] matches any character not in seq
    
    print("\nPattern examples:")
    print("*.py - All Python files in current directory")
    print("**/*.py - All Python files recursively")
    print("test_*.py - Files starting with 'test_'")
    print("*[0-9].py - Files ending with a digit")

def advanced_operations():
    """Advanced pathlib operations"""
    print("\n=== 8. Advanced Operations ===")
    
    # Create test structure
    test_dir = Path('advanced_test')
    test_dir.mkdir(exist_ok=True)
    
    # Create some files
    (test_dir / 'file1.txt').write_text('Content 1')
    (test_dir / 'file2.py').write_text('print("Hello")')
    (test_dir / 'readme.md').write_text('# Project')
    
    # Iterate with filtering
    text_files = [f for f in test_dir.iterdir() if f.suffix == '.txt']
    print(f"Text files: {[f.name for f in text_files]}")
    
    # Sort by modification time
    files_by_time = sorted(test_dir.iterdir(), key=lambda x: x.stat().st_mtime)
    print(f"Files by modification time: {[f.name for f in files_by_time]}")
    
    # Get largest file
    largest = max(test_dir.iterdir(), key=lambda x: x.stat().st_size if x.is_file() else 0)
    print(f"Largest file: {largest.name} ({largest.stat().st_size} bytes)")
    
    # Copy file
    source = test_dir / 'file1.txt'
    destination = test_dir / 'file1_copy.txt'
    destination.write_bytes(source.read_bytes())
    print(f"Copied {source.name} to {destination.name}")
    
    # Move/rename file
    old_name = test_dir / 'file2.py'
    new_name = test_dir / 'script.py'
    old_name.rename(new_name)
    print(f"Renamed {old_name.name} to {new_name.name}")
    
    # Cleanup
    shutil.rmtree(test_dir)

def path_comparison():
    """Comparing paths"""
    print("\n=== 9. Path Comparison ===")
    
    p1 = Path('folder/file.txt')
    p2 = Path('folder') / 'file.txt'
    p3 = Path('FOLDER/FILE.TXT')
    
    print(f"p1 == p2: {p1 == p2}")  # True
    print(f"p1.samefile() available: {hasattr(p1, 'samefile')}")
    
    # Check if path is relative to another
    parent = Path('folder')
    child = Path('folder/subfolder/file.txt')
    
    try:
        relative = child.relative_to(parent)
        print(f"{child} is relative to {parent}: {relative}")
    except ValueError:
        print(f"{child} is not relative to {parent}")
    
    # Check if path is subpath
    print(f"Child starts with parent: {str(child).startswith(str(parent))}")

def cross_platform_paths():
    """Cross-platform path handling"""
    print("\n=== 10. Cross-Platform Paths ===")
    
    # pathlib handles platform differences automatically
    p = Path('folder') / 'subfolder' / 'file.txt'
    print(f"Cross-platform path: {p}")
    print(f"As POSIX: {p.as_posix()}")
    print(f"As string: {str(p)}")
    
    # Pure paths (don't access filesystem)
    from pathlib import PurePath, PurePosixPath, PureWindowsPath
    
    pure_path = PurePath('folder/file.txt')
    posix_path = PurePosixPath('folder/file.txt')
    windows_path = PureWindowsPath('folder\\file.txt')
    
    print(f"Pure path: {pure_path}")
    print(f"POSIX path: {posix_path}")
    print(f"Windows path: {windows_path}")

def practical_examples():
    """Practical real-world examples"""
    print("\n=== 11. Practical Examples ===")
    
    # Example 1: Find all images in a directory
    def find_images(directory):
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
        images = []
        for file in Path(directory).rglob('*'):
            if file.suffix.lower() in image_extensions:
                images.append(file)
        return images
    
    # Example 2: Backup files with timestamp
    def backup_file(file_path):
        path = Path(file_path)
        if path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{path.stem}_{timestamp}{path.suffix}"
            backup_path = path.parent / backup_name
            backup_path.write_bytes(path.read_bytes())
            return backup_path
        return None
    
    # Example 3: Clean up old files
    def cleanup_old_files(directory, days_old=30):
        import time
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        
        for file in Path(directory).rglob('*'):
            if file.is_file() and file.stat().st_mtime < cutoff_time:
                print(f"Would delete old file: {file}")
                # file.unlink()  # Uncomment to actually delete
    
    # Example 4: Organize files by extension
    def organize_by_extension(source_dir, target_dir):
        source = Path(source_dir)
        target = Path(target_dir)
        target.mkdir(exist_ok=True)
        
        for file in source.iterdir():
            if file.is_file():
                ext_dir = target / file.suffix[1:] if file.suffix else target / 'no_extension'
                ext_dir.mkdir(exist_ok=True)
                new_location = ext_dir / file.name
                print(f"Would move {file} to {new_location}")
                # shutil.move(str(file), str(new_location))  # Uncomment to actually move
    
    print("Practical functions defined:")
    print("- find_images(): Find all image files")
    print("- backup_file(): Create timestamped backup")
    print("- cleanup_old_files(): Remove old files")
    print("- organize_by_extension(): Sort files by type")

if __name__ == "__main__":
    print("Complete pathlib Reference Guide")
    print("=" * 50)
    
    basic_path_creation()
    path_properties()
    path_operations()
    file_system_checks()
    directory_operations()
    file_operations()
    pattern_matching()
    advanced_operations()
    path_comparison()
    cross_platform_paths()
    practical_examples()
    
    print("\n" + "=" * 50)
    print("PATHLIB QUICK REFERENCE:")
    print("=" * 50)
    print("Path('.') - Current directory")
    print("Path.home() - Home directory")
    print("Path.cwd() - Current working directory")
    print("path.exists() - Check if exists")
    print("path.is_file() - Check if file")
    print("path.is_dir() - Check if directory")
    print("path.mkdir() - Create directory")
    print("path.iterdir() - List contents")
    print("path.glob() - Pattern matching")
    print("path.rglob() - Recursive pattern matching")
    print("path.read_text() - Read file as text")
    print("path.write_text() - Write text to file")
    print("path.unlink() - Delete file")
    print("path.rmdir() - Delete empty directory")
    print("path / 'subpath' - Join paths")
    print("path.parent - Parent directory")
    print("path.name - Filename")
    print("path.suffix - File extension")
    print("path.stem - Filename without extension")