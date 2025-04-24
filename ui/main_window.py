"""
Main application window and UI components
"""
import os
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk


class SplashScreen(tk.Toplevel):
    """Splash screen with loading progress bar"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title("CLIP Image Search")
        self.geometry("500x300")
        self.resizable(False, False)
        
        # Remove window decorations
        self.overrideredirect(True)
        
        # Center on screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 500) // 2
        y = (screen_height - 300) // 2
        self.geometry(f"500x300+{x}+{y}")
        
        # Make splash screen appear on top
        self.attributes('-topmost', True)
        
        # Create content frame with border
        self.frame = tk.Frame(self, bg='white', borderwidth=2, relief='ridge')
        self.frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        # App title
        title = tk.Label(
            self.frame, 
            text="CLIP Image Search", 
            font=('Arial', 20, 'bold'),
            bg='white'
        )
        title.pack(pady=(30, 20))
        
        # Loading message
        self.message = tk.Label(
            self.frame,
            text="Starting application...",
            font=('Arial', 12),
            wraplength=450,
            justify='center',
            bg='white'
        )
        self.message.pack(pady=10)
        
        # First run notice
        first_run_message = tk.Label(
            self.frame,
            text="Note: On first run, the application needs to download the CLIP model (approximately 600MB). "
                 "This will only happen once and might take a few minutes depending on your internet connection.",
            font=('Arial', 10),
            wraplength=450,
            justify='center',
            fg='#555555',
            bg='white'
        )
        first_run_message.pack(pady=10)
        
        # Progress bar - always in indeterminate mode
        self.progress = ttk.Progressbar(
            self.frame,
            orient='horizontal',
            length=400,
            mode='indeterminate'
        )
        self.progress.pack(pady=20)
        
        # Start the progress bar animation with faster speed
        # Use a faster interval for more visible animation
        self.progress.start(10)
        
        # Force immediate UI update
        self.update_idletasks()
        self.update()
        
        # Schedule recurring UI updates to keep animation smooth
        self._schedule_updates()
        
        # Flag to track if this splash screen is valid
        self.is_valid = True
    
    def _schedule_updates(self):
        """Schedule regular UI updates to keep animations smooth"""
        if self.winfo_exists():
            self.update_idletasks()
            self.after(50, self._schedule_updates)
    
    def update_message(self, message):
        """Update the loading message"""
        if not self.is_valid:
            return
        try:
            self.message.config(text=message)
            self.update_idletasks()
            self.update()
        except tk.TclError:
            self.is_valid = False
            
    # Keep the progress bar in indeterminate mode always
    def set_progress(self, value=None):
        """This is now just a placeholder to maintain compatibility"""
        pass
    
    def switch_to_determinate(self, value=None):
        """This is now just a placeholder to maintain compatibility"""
        pass


class ClipSearchWindow(tk.Tk):
    """Main application window for CLIP Image Search"""
    
    def __init__(self):
        # Initialize the main Tk window
        super().__init__()
        
        # Hide main window during initialization
        self.withdraw()
        
        # Create splash screen
        self.splash = SplashScreen(self)
        
        # Give time for splash screen to fully initialize
        self.after(100, self._continue_initialization)
    
    def _continue_initialization(self):
        """Continue initialization after splash screen appears"""
        # Set window properties
        self.title("CLIP Image Search")
        self.geometry("900x600")
        self.minsize(800, 500)
        
        # Initialize configuration
        self.splash.update_message("Loading configuration...")
        
        # Now we import the modules we need
        # This is done here to show the splash screen first
        from models.clip_processor import ClipModel
        from utils.config import Config
        from ui.search_results import SearchResultsFrame
        
        self.config_manager = Config()
        
        # UI state variables
        self.image_folder = self.config_manager.image_folder
        self.thumbnail_cache = {}
        self.processing_thread = None
        
        # Import the SearchResultsFrame class
        self.SearchResultsFrame = SearchResultsFrame
        
        # Create UI components
        self.splash.update_message("Creating user interface...")
        self.create_widgets()
        
        # Store ClipModel class for later use
        self.ClipModel = ClipModel
        
        # Initialize model in background thread
        threading.Thread(target=self.initialize_model, daemon=True).start()
    
    def initialize_model(self):
        """Initialize CLIP model in background thread"""
        try:
            model_dir = os.path.join(os.path.expanduser("~"), "Documents", "CLIPImageSearch", "model")
            model_path = os.path.join(model_dir, "models--openai--clip-vit-base-patch32")
            
            # Check if model already exists
            if os.path.exists(model_path):
                self.splash.update_message("Loading CLIP model...")
            else:
                # First indicate downloading will begin
                self.splash.update_message("Downloading CLIP model (this may take several minutes)...")
                
                # After a few seconds, update the message with more information
                self.after(5000, lambda: self.update_download_message("Downloading model files (1/4)..."))
                self.after(15000, lambda: self.update_download_message("Processing model components (2/4)..."))
                self.after(30000, lambda: self.update_download_message("Preparing model tokenizer (3/4)..."))
                self.after(45000, lambda: self.update_download_message("Finalizing model setup (4/4)..."))
            
            # Initialize CLIP model with progress callback
            def progress_callback(message, progress=None):
                self.splash.update_message(message)
                # Progress parameter is ignored as we're using indeterminate mode
            
            self.clip_model = self.ClipModel(progress_callback=progress_callback)
            
            # Close splash and show main window
            self.splash.update_message("Ready!")
            self.after(1000, self.show_main_window)
            
        except Exception as e:
            try:
                self.splash.update_message(f"Error: {str(e)}")
                messagebox.showerror("Error", f"Failed to initialize CLIP model: {str(e)}")
                self.after(3000, self.destroy)
            except tk.TclError:
                # If splash is already gone, just show error
                messagebox.showerror("Error", f"Failed to initialize CLIP model: {str(e)}")
                self.destroy()
    
    def update_download_message(self, message):
        """Update download message if the splash screen is still active"""
        if hasattr(self, 'splash') and self.splash.is_valid:
            self.splash.update_message(message)
    
    def show_main_window(self):
        """Close splash screen and show main window"""
        try:
            if hasattr(self, 'splash') and self.splash.is_valid:
                self.splash.destroy()
        except tk.TclError:
            pass  # Splash already destroyed
        
        self.deiconify()
        
        # Check for changes in the folder on startup if a folder was loaded
        if self.image_folder:
            self.folder_var.set(self.image_folder)
            self.after(1000, self.check_folder_on_startup)
    
    def create_widgets(self):
        """Create and arrange all UI components"""
        # Create main frame with padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top controls frame
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create a top row for folder selection
        folder_frame = ttk.Frame(controls_frame)
        folder_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Folder selection in the top row
        ttk.Label(folder_frame, text="Image Folder:").pack(side=tk.LEFT, padx=(0, 5))
        self.folder_var = tk.StringVar()
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var, width=50)
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(folder_frame, text="Browse", command=self.select_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(folder_frame, text="Refresh", command=self.refresh_folder).pack(side=tk.LEFT)
        
        # Text search setup
        search_frame = ttk.Frame(controls_frame)
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="Search Query:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=50)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        search_entry.bind("<Return>", lambda e: self.search_images())
        
        ttk.Button(search_frame, text="Search", command=self.search_images).pack(side=tk.LEFT)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Progress bar (hidden by default)
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            main_frame, 
            variable=self.progress_var, 
            mode="determinate", 
            maximum=100
        )
        
        # Search results area
        self.results_frame = self.SearchResultsFrame(
            main_frame, 
            get_thumbnail_func=self.get_thumbnail,
            open_image_func=self.open_image,
            rename_image_func=self.rename_image,
            delete_image_func=self.delete_image
        )
        self.results_frame.pack(fill=tk.BOTH, expand=True)
    
    def select_folder(self):
        """Open dialog to select image folder"""
        folder = filedialog.askdirectory(title="Select Image Folder")
        if folder:
            self.image_folder = folder
            self.folder_var.set(folder)
            self.status_var.set(f"Selected folder: {folder}")
            
            # Save the selected folder to config
            self.config_manager.image_folder = folder
            
            # Process images in the folder
            self.process_images_threaded()
    
    def refresh_folder(self):
        """Refresh the current folder to detect added/removed files"""
        if not self.image_folder:
            self.status_var.set("No folder selected yet.")
            return
        
        self.status_var.set(f"Refreshing folder: {self.image_folder}")
        self.update()
        self.process_images_threaded()
    
    def get_thumbnail(self, image_path, size=(150, 150)):
        """Get or create a thumbnail for an image
        
        Args:
            image_path: Path to the image
            size: Thumbnail dimensions
            
        Returns:
            ImageTk.PhotoImage or None if generation fails
        """
        if image_path in self.thumbnail_cache:
            return self.thumbnail_cache[image_path]
        
        try:
            img = Image.open(image_path).convert("RGB")
            img.thumbnail(size)
            photo = ImageTk.PhotoImage(img)
            self.thumbnail_cache[image_path] = photo
            return photo
        except Exception as e:
            print(f"Error creating thumbnail for {image_path}: {e}")
            return None
    
    def open_image(self, image_path):
        """Open the image with the default system viewer"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(image_path)
            elif os.name == 'posix':  # macOS and Linux
                import subprocess
                import sys
                if sys.platform == 'darwin':  # macOS
                    subprocess.call(('open', image_path))
                else:  # Linux
                    subprocess.call(('xdg-open', image_path))
            self.status_var.set(f"Opened: {os.path.basename(image_path)}")
        except Exception as e:
            self.status_var.set(f"Error opening file: {str(e)}")
    
    def rename_image(self, image_path):
        """Rename the selected image file"""
        try:
            # Get current filename and directory
            dir_name = os.path.dirname(image_path)
            old_name = os.path.basename(image_path)
            
            # Create a dialog to get the new filename
            dialog = tk.Toplevel(self)
            dialog.title("Rename Image")
            dialog.geometry("400x120")
            dialog.resizable(False, False)
            dialog.transient(self)  # Make dialog modal
            
            # Center the dialog
            dialog.geometry(f"+{self.winfo_rootx() + 50}+{self.winfo_rooty() + 50}")
            
            # Create and place widgets
            ttk.Label(dialog, text="Current name:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
            ttk.Label(dialog, text=old_name).grid(row=0, column=1, sticky="w", padx=10, pady=5)
            
            ttk.Label(dialog, text="New name:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
            new_name_var = tk.StringVar(value=old_name)
            name_entry = ttk.Entry(dialog, textvariable=new_name_var, width=30)
            name_entry.grid(row=1, column=1, sticky="we", padx=10, pady=5)
            name_entry.select_range(0, len(old_name.split('.')[0]))  # Select name without extension
            
            # Buttons frame
            btn_frame = ttk.Frame(dialog)
            btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
            
            # Function to handle rename
            def do_rename():
                new_name = new_name_var.get().strip()
                if not new_name:
                    messagebox.showerror("Error", "Please enter a valid filename")
                    return
                
                # Keep the same extension
                if '.' not in new_name and '.' in old_name:
                    extension = old_name.split('.')[-1]
                    new_name = f"{new_name}.{extension}"
                
                new_path = os.path.join(dir_name, new_name)
                
                # Check if the new filename already exists
                if os.path.exists(new_path) and new_path != image_path:
                    messagebox.showerror("Error", f"File '{new_name}' already exists")
                    return
                
                try:
                    # Rename the file
                    os.rename(image_path, new_path)
                    
                    # Update the embeddings dictionaries
                    if image_path in self.clip_model.image_embeddings:
                        self.clip_model.image_embeddings[new_path] = self.clip_model.image_embeddings.pop(image_path)
                    
                    # Update thumbnail cache if exists
                    if image_path in self.thumbnail_cache:
                        self.thumbnail_cache[new_path] = self.thumbnail_cache.pop(image_path)
                    
                    # Save the updated caches
                    self.clip_model.save_cache()
                    
                    # Update status and close dialog
                    self.status_var.set(f"Renamed: {old_name} → {new_name}")
                    dialog.destroy()
                    
                    # Refresh search results if we're in a search
                    if self.search_var.get():
                        self.search_images()
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to rename file: {str(e)}")
            
            # Add buttons
            ttk.Button(btn_frame, text="Rename", command=do_rename).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            
            # Make Enter key submit the dialog
            name_entry.bind("<Return>", lambda e: do_rename())
            
            # Set focus to the entry
            name_entry.focus_set()
            
            # Wait for the dialog to close
            dialog.grab_set()
            
        except Exception as e:
            self.status_var.set(f"Error preparing to rename: {str(e)}")
    
    def delete_image(self, image_path):
        """Delete the image file with confirmation"""
        try:
            # Get filename for display
            filename = os.path.basename(image_path)
            
            # Ask for confirmation
            confirm = messagebox.askyesno(
                "Confirm Deletion",
                f"Are you sure you want to delete '{filename}'?\n\nThis action cannot be undone.",
                icon="warning"
            )
            
            if not confirm:
                self.status_var.set("Deletion cancelled.")
                return
            
            # Perform the deletion
            os.remove(image_path)
            
            # Remove from our data structures
            if image_path in self.clip_model.image_embeddings:
                del self.clip_model.image_embeddings[image_path]
            
            if image_path in self.thumbnail_cache:
                del self.thumbnail_cache[image_path]
            
            # Save the updated caches
            self.clip_model.save_cache()
            
            # Update status
            self.status_var.set(f"Deleted: {filename}")
            
            # If we're in a search view, refresh it to remove the deleted image
            if self.search_var.get():
                self.search_images()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete file: {str(e)}")
            self.status_var.set(f"Error deleting file: {str(e)}")
    
    def process_images_threaded(self):
        """Process images in a separate thread to avoid UI freezing"""
        if self.processing_thread and self.processing_thread.is_alive():
            self.status_var.set("Already processing images. Please wait...")
            return
            
        self.processing_thread = threading.Thread(target=self._process_images_worker)
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def _process_images_worker(self):
        """Worker function to process images in background thread"""
        if not self.image_folder:
            return
        
        # Collect all image file paths
        try:
            all_files = os.listdir(self.image_folder)
            image_paths = [
                os.path.join(self.image_folder, fname)
                for fname in all_files
                if fname.lower().endswith((".jpg", ".jpeg", ".png"))
            ]
            
            # Find files that have been added or removed
            current_paths_set = set(image_paths)
            cached_paths_set = set(self.clip_model.image_embeddings.keys())
            
            # Files that need to be added (new files)
            new_paths = list(current_paths_set - cached_paths_set)
            
            # Files that need to be removed (deleted files)
            removed_paths = list(cached_paths_set - current_paths_set)
            
            # Show progress bar for processing
            if new_paths:
                self.progress_bar.pack(fill=tk.X, padx=10, pady=5, before=self.results_frame)
                self.progress_var.set(0)
                self.update_idletasks()
            
            # Remove deleted files from embeddings
            removed_count = self.clip_model.remove_images(removed_paths)
            
            if removed_count:
                self.status_var.set(f"Removed {removed_count} deleted files from cache")
                self.update_idletasks()
            
            # Process new files
            if new_paths:
                def update_status(current, total, filename):
                    progress = (current + 1) / total * 100
                    self.progress_var.set(progress)
                    self.status_var.set(f"Processing image {current+1}/{total}: {filename}")
                    self.update_idletasks()
                
                processed_count = self.clip_model.process_images(new_paths, update_status)
                
                # Save the updated embeddings
                self.clip_model.save_cache()
                
                # Hide progress bar when done
                self.progress_bar.pack_forget()
                
                # Update status with results
                total_message = f"Processed {processed_count} new images. "
                if removed_count:
                    total_message += f"Removed {removed_count} deleted images. "
                total_message += f"Total: {len(self.clip_model.image_embeddings)}"
                self.status_var.set(total_message)
            
            elif removed_count:
                # We had removals but no additions
                self.clip_model.save_cache()
                self.status_var.set(f"Removed {removed_count} deleted images. Total: {len(self.clip_model.image_embeddings)}")
            
            else:
                self.status_var.set(f"No changes detected. Total: {len(self.clip_model.image_embeddings)}")
            
        except Exception as e:
            self.status_var.set(f"Error processing folder: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Hide progress bar on error
            if hasattr(self, 'progress_bar'):
                self.progress_bar.pack_forget()
    
    def search_images(self):
        """Search for images matching the text prompt"""
        prompt = self.search_var.get()
        if not prompt:
            self.status_var.set("Please enter a search prompt")
            return
        
        if not self.clip_model.image_embeddings:
            self.status_var.set("No images processed yet. Please select a folder first.")
            return
        
        self.status_var.set(f"Searching for: {prompt}")
        self.update_idletasks()
        
        # Perform the search
        results = self.clip_model.search(prompt)
        
        # Display results
        self.results_frame.display_results(results)
        
        self.status_var.set(f"Found {len(results)} results for: {prompt}")
    
    def check_folder_on_startup(self):
        """Check for new or deleted files in the folder on application startup"""
        if self.image_folder and os.path.isdir(self.image_folder):
            self.status_var.set(f"Checking for changes in: {self.image_folder}")
            self.update_idletasks()
            
            # Process images in background thread
            self.process_images_threaded()
    
    def destroy(self):
        """Save any necessary data before closing the application"""
        # Make sure config is saved 
        if self.image_folder:
            self.config_manager.image_folder = self.image_folder
        
        super().destroy() 