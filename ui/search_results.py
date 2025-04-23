"""
Frame for displaying search results
"""
import tkinter as tk
from tkinter import ttk

class SearchResultsFrame(ttk.LabelFrame):
    """Frame for displaying search results in a scrollable grid"""
    
    def __init__(self, parent, get_thumbnail_func, open_image_func, 
                 rename_image_func, delete_image_func):
        """Initialize the search results frame
        
        Args:
            parent: Parent widget
            get_thumbnail_func: Function to get thumbnail images
            open_image_func: Function to open images
            rename_image_func: Function to rename images
            delete_image_func: Function to delete images
        """
        super().__init__(parent, text="Search Results")
        
        # Store callback functions
        self.get_thumbnail = get_thumbnail_func
        self.open_image = open_image_func
        self.rename_image = rename_image_func
        self.delete_image = delete_image_func
        
        # Create scrolling canvas for results
        self.create_scrollable_frame()
    
    def create_scrollable_frame(self):
        """Set up the scrollable frame for results"""
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas for scrolling
        self.canvas = tk.Canvas(self, yscrollcommand=scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.canvas.yview)
        
        # Frame inside canvas for results
        self.results_container = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window(
            (0, 0), 
            window=self.results_container, 
            anchor=tk.NW
        )
        
        # Configure scrolling
        self.results_container.bind(
            "<Configure>", 
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Update canvas width when it changes size
        self.canvas.bind(
            "<Configure>", 
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )
    
    def clear(self):
        """Clear all search results"""
        for widget in self.results_container.winfo_children():
            widget.destroy()
    
    def display_results(self, results):
        """Display search results in a grid
        
        Args:
            results: List of (image_path, score) tuples to display
        """
        # Clear previous results
        self.clear()
        
        if not results:
            # Display "no results" message
            no_results = ttk.Label(
                self.results_container, 
                text="No matching images found", 
                font=("", 12),
                padding=20
            )
            no_results.pack(pady=50)
            return
        
        # Display results in a grid
        num_cols = 4
        for i, (path, score) in enumerate(results):
            row, col = divmod(i, num_cols)
            
            # Create frame for this result
            result_frame = ttk.Frame(self.results_container, padding=5)
            result_frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
            
            # Get and display the thumbnail
            photo = self.get_thumbnail(path)
            if photo:
                img_label = ttk.Label(result_frame, image=photo)
                img_label.image = photo  # Keep a reference
                img_label.pack(pady=(0, 5))
                
                # Add click event to open the image
                img_label.bind("<Double-Button-1>", lambda e, p=path: self.open_image(p))
            
            # Filename and score
            name_label = ttk.Label(result_frame, text=self._get_short_filename(path), wraplength=150)
            name_label.pack()
            
            score_label = ttk.Label(result_frame, text=f"Score: {score:.4f}")
            score_label.pack()
            
            # Add buttons for actions
            btn_frame = ttk.Frame(result_frame)
            btn_frame.pack(pady=(5, 0))
            
            open_btn = ttk.Button(
                btn_frame, 
                text="Open", 
                width=6, 
                command=lambda p=path: self.open_image(p)
            )
            open_btn.pack(side=tk.LEFT, padx=2)
            
            rename_btn = ttk.Button(
                btn_frame, 
                text="Rename", 
                width=7,
                command=lambda p=path: self.rename_image(p)
            )
            rename_btn.pack(side=tk.LEFT, padx=2)
            
            # Add delete button
            delete_btn = ttk.Button(
                btn_frame, 
                text="Delete", 
                width=6,
                command=lambda p=path: self.delete_image(p)
            )
            delete_btn.pack(side=tk.LEFT, padx=2)
    
    def _get_short_filename(self, path, max_length=25):
        """Get shortened filename for display
        
        Args:
            path: Full file path
            max_length: Maximum filename length before truncating
            
        Returns:
            str: Shortened filename
        """
        import os
        filename = os.path.basename(path)
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            return name[:max_length-3-len(ext)] + "..." + ext
        return filename 