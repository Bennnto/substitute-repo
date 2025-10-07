#!/usr/bin/env python3
"""
Simple Menu System with Questionnaire-Style Dropdown Selector
Author: Ben
"""

import os
import sys

class SimpleMenu:
    def __init__(self):
        self.current_selection = 0
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def show_dropdown(self, title: str, options: list, allow_cancel=True) -> int:
        """
        Show a simple dropdown menu with moving arrow
        Returns: selected index (0-based), or -1 if cancelled
        """
        self.current_selection = 0
        
        while True:
            self.clear_screen()
            print(f"\n📋 {title}")
            print("─" * 50)
            
            # Show options with arrow indicator
            for i, option in enumerate(options):
                if i == self.current_selection:
                    print(f"  ▶️  {option}")
                else:
                    print(f"     {option}")
            
            if allow_cancel:
                if self.current_selection == len(options):
                    print(f"  ▶️  ❌ Cancel")
                else:
                    print(f"     ❌ Cancel")
            
            print("─" * 50)
            print("W/S: Move arrow, Enter: Select, Q: Cancel")
            
            # Get user input
            key = input("🎯 ").strip().lower()
            
            if key == "w":  # Move up
                self.current_selection = (self.current_selection - 1) % (len(options) + (1 if allow_cancel else 0))
            elif key == "s":  # Move down
                self.current_selection = (self.current_selection + 1) % (len(options) + (1 if allow_cancel else 0))
            elif key == "":  # Enter
                if self.current_selection < len(options):
                    return self.current_selection
                elif allow_cancel:
                    return -1
            elif key == "q":  # Quit
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
        
        for question in questions:
            question_text = question['question']
            options = question['options']
            
            print(f"\n❓ {question_text}")
            choice = self.show_dropdown(f"Select option", options, allow_cancel=False)
            
            if choice == -1:
                return {}  # Cancelled
            
            answers[question['key']] = options[choice]
        
        return answers

def main():
    """Demo the simple menu system"""
    menu = SimpleMenu()
    
    # Example 1: Simple dropdown
    print("=== Simple Dropdown Example ===")
    options = ["Option 1", "Option 2", "Option 3", "Option 4"]
    choice = menu.show_dropdown("Select an option", options)
    
    if choice == -1:
        print("Cancelled!")
    else:
        print(f"Selected: {options[choice]}")
    
    # Example 2: Questionnaire
    print("\n=== Questionnaire Example ===")
    questions = [
        {
            'question': 'What is your favorite color?',
            'options': ['Red', 'Blue', 'Green', 'Yellow'],
            'key': 'color'
        },
        {
            'question': 'What is your favorite food?',
            'options': ['Pizza', 'Burger', 'Salad', 'Pasta'],
            'key': 'food'
        },
        {
            'question': 'What is your favorite animal?',
            'options': ['Dog', 'Cat', 'Bird', 'Fish'],
            'key': 'animal'
        }
    ]
    
    answers = menu.show_questionnaire(questions)
    
    if answers:
        print("\n📋 Your answers:")
        for key, value in answers.items():
            print(f"  {key}: {value}")
    else:
        print("Questionnaire cancelled!")

if __name__ == "__main__":
    main() 