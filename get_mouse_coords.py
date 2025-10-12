"""
Quick utility script to get mouse coordinates on screen.
Press F1 to print the current mouse position.
Press ESC to exit.
"""

import pyautogui
from pynput import keyboard
from pynput.keyboard import Key
import sys

print("=" * 50)
print("Mouse Coordinate Finder")
print("=" * 50)
print("Press F1 to get mouse coordinates")
print("Press ESC to exit")
print("=" * 50)

def on_press(key):
    try:
        # Check if F1 is pressed
        if key == Key.f1:
            x, y = pyautogui.position()
            print(f"\n🎯 Mouse Position: X={x}, Y={y}")
            print(f"   Tuple format: ({x}, {y})")
        
        # Exit on ESC
        if key == Key.esc:
            print("\nExiting...")
            return False
            
    except AttributeError:
        pass

def on_release(key):
    pass

# Set up keyboard listener
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()

