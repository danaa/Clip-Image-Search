#!/usr/bin/env python3
"""
CLIP Image Search - Search your image collection using natural language
"""
import os
import sys
import tkinter as tk
from ui.main_window import ClipSearchWindow

def main():
    """Main application entry point"""
    # Create and start the application
    app = ClipSearchWindow()
    app.mainloop()

if __name__ == "__main__":
    main() 