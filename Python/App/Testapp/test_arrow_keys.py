#!/usr/bin/env python3
"""
Simple Arrow Key Test
Test arrow key navigation functionality
"""

import os
import sys

# Platform-specific imports for key handling
if os.name == 'nt':  # Windows
    import msvcrt
else:  # Unix/Linux/macOS
    import tty
    import termios

class ArrowKeyTest:
    def __init__(self):
        self.current_selection = 0
    
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
        except Exception as e:
            print(f"Error with arrow keys: {e}")
            # Fallback to simple input
            return input("Enter choice (w/s/enter/q): ").strip().lower()
    
    def test_menu(self):
        """Test menu with arrow key navigation"""
        options = ["Option 1", "Option 2", "Option 3", "Option 4", "Option 5"]
        
        while True:
            self.clear_screen()
            print("=== ARROW KEY TEST ===")
            print("Use arrow keys (↑/↓) or W/S to move, Enter to select, Q to quit")
            print()
            
            for i, option in enumerate(options):
                if i == self.current_selection:
                    print(f"> {option}")
                else:
                    print(f"  {option}")
            
            print()
            print("Current selection:", self.current_selection)
            print("Press a key...")
            
            key = self.get_key_press()
            print(f"Key pressed: '{key}'")
            
            if key == 'UP' or key == 'w':
                self.current_selection = (self.current_selection - 1) % len(options)
                print("Moving UP")
            elif key == 'DOWN' or key == 's':
                self.current_selection = (self.current_selection + 1) % len(options)
                print("Moving DOWN")
            elif key == 'ENTER' or key == '':
                print(f"Selected: {options[self.current_selection]}")
                input("Press Enter to continue...")
            elif key == 'ESC' or key == 'q':
                print("Quitting...")
                break
            else:
                print(f"Unknown key: '{key}'")
                input("Press Enter to continue...")

def main():
    """Main test function"""
    print("Starting Arrow Key Test...")
    print("This will test arrow key navigation.")
    input("Press Enter to start...")
    
    test = ArrowKeyTest()
    test.test_menu()
    
    print("Test completed!")

if __name__ == "__main__":
    main() 