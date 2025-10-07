#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox

def test_gui():
    root = tk.Tk()
    root.title("GUI Test")
    root.geometry("300x200")
    
    label = tk.Label(root, text="If you can see this, GUI is working!")
    label.pack(pady=50)
    
    def show_message():
        messagebox.showinfo("Test", "GUI is working correctly!")
    
    button = tk.Button(root, text="Click Me", command=show_message)
    button.pack(pady=20)
    
    print("GUI window should appear now...")
    root.mainloop()

if __name__ == "__main__":
    test_gui() 