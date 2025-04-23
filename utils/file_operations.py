"""
File and image handling utilities
"""
import os
import sys
import subprocess
from PIL import Image, ImageTk, UnidentifiedImageError

def get_image_files(folder_path):
    """Get all image files in a folder
    
    Args:
        folder_path: Path to folder to scan
        
    Returns:
        list: List of full paths to image files
    """
    if not os.path.isdir(folder_path):
        return []
    
    try:
        all_files = os.listdir(folder_path)
        image_paths = [
            os.path.join(folder_path, fname)
            for fname in all_files
            if fname.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))
        ]
        return image_paths
    except Exception as e:
        print(f"Error scanning folder for images: {e}")
        return []

def create_thumbnail(image_path, size=(150, 150)):
    """Create a thumbnail from an image
    
    Args:
        image_path: Path to image file
        size: Thumbnail dimensions (width, height)
        
    Returns:
        PIL.ImageTk.PhotoImage or None if creation fails
    """
    try:
        img = Image.open(image_path).convert("RGB")
        img.thumbnail(size)
        return ImageTk.PhotoImage(img)
    except UnidentifiedImageError:
        print(f"Unreadable image file: {image_path}")
        return None
    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        return None

def open_file_with_default_app(file_path):
    """Open a file with the default system application
    
    Args:
        file_path: Path to file to open
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if os.name == 'nt':  # Windows
            os.startfile(file_path)
        elif os.name == 'posix':  # macOS and Linux
            if sys.platform == 'darwin':  # macOS
                subprocess.call(('open', file_path))
            else:  # Linux
                subprocess.call(('xdg-open', file_path))
        return True
    except Exception as e:
        print(f"Error opening file: {e}")
        return False

def get_file_changes(current_files, cached_files):
    """Identify files that have been added or removed
    
    Args:
        current_files: List of current file paths
        cached_files: List of previously cached file paths
        
    Returns:
        tuple: (new_files, removed_files) lists
    """
    current_set = set(current_files)
    cached_set = set(cached_files)
    
    new_files = list(current_set - cached_set)
    removed_files = list(cached_set - current_set)
    
    return new_files, removed_files 