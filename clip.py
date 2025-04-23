import os
import torch
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk, UnidentifiedImageError
from transformers import CLIPProcessor, CLIPModel
import json
import tkinter.messagebox as messagebox

class ClipImageSearch(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CLIP Image Search")
        self.geometry("900x600")
        self.minsize(800, 500)
        
        # Initialize CLIP model
        MODEL_NAME = "openai/clip-vit-base-patch32"
        self.model = CLIPModel.from_pretrained(MODEL_NAME).eval()
        self.processor = CLIPProcessor.from_pretrained(MODEL_NAME)
        
        self.image_folder = ""
        self.cache_file = "clip_embeddings.pt"
        self.config_file = "clip_config.json"
        self.image_embeddings = {}
        self.thumbnail_cache = {}
        
        self.create_widgets()
        self.load_config()
        self.load_cache()
        
        # Check for changes in the folder on startup if a folder was loaded
        if self.image_folder:
            self.after(1000, self.check_folder_on_startup)
    
    def create_widgets(self):
        # Create main frame with padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top controls frame - now contains folder and search controls
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
        
        # Search results area with scrolling
        results_frame = ttk.LabelFrame(main_frame, text="Search Results")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(results_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas for scrolling
        results_canvas = tk.Canvas(results_frame, yscrollcommand=scrollbar.set)
        results_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=results_canvas.yview)
        
        # Frame inside canvas for results
        self.results_container = ttk.Frame(results_canvas)
        results_canvas.create_window((0, 0), window=self.results_container, anchor=tk.NW)
        
        # Configure scrolling
        def configure_scroll_region(event):
            results_canvas.configure(scrollregion=results_canvas.bbox("all"))
        
        self.results_container.bind("<Configure>", configure_scroll_region)
    
    def on_frame_configure(self, event):
        # Update the scrollregion when the inner frame changes size
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_canvas_configure(self, event):
        # Update the width of the window when canvas changes size
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def load_config(self):
        """Load saved configuration including the last used folder."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                # Load saved folder path if it exists
                if 'image_folder' in config and os.path.isdir(config['image_folder']):
                    self.image_folder = config['image_folder']
                    self.folder_var.set(self.image_folder)
                    self.status_var.set(f"Loaded previous folder: {self.image_folder}")
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def save_config(self):
        """Save current configuration including the image folder path."""
        try:
            config = {
                'image_folder': self.image_folder
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Image Folder")
        if folder:
            self.image_folder = folder
            self.folder_var.set(folder)
            self.status_var.set(f"Selected folder: {folder}")
            # Save the selected folder to config
            self.save_config()
            self.process_images()
    
    def load_cache(self):
        """Load embeddings cache files."""
        if os.path.exists(self.cache_file):
            try:
                self.image_embeddings = torch.load(self.cache_file)
                self.status_var.set(f"Loaded {len(self.image_embeddings)} images from cache")
            except Exception as e:
                print(f"Error loading image embeddings: {e}")
                self.status_var.set("Error loading image cache")
                # Initialize as empty if loading fails
                self.image_embeddings = {}
        else:
            self.image_embeddings = {}
    
    def refresh_folder(self):
        """Refresh the current folder to detect added/removed files."""
        if not self.image_folder:
            self.status_var.set("No folder selected yet.")
            return
        
        self.status_var.set(f"Refreshing folder: {self.image_folder}")
        self.update()
        self.process_images()
        self.status_var.set(f"Refreshed folder")
    
    def process_images(self):
        if not self.image_folder:
            return
        
        # Collect all image file paths
        all_files = os.listdir(self.image_folder)
        image_paths = [
            os.path.join(self.image_folder, fname)
            for fname in all_files
            if fname.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        
        # Find files that have been added or removed
        current_paths_set = set(image_paths)
        cached_paths_set = set(self.image_embeddings.keys())
        
        # Files that need to be added (new files)
        new_paths = list(current_paths_set - cached_paths_set)
        
        # Files that need to be removed (deleted files)
        removed_paths = list(cached_paths_set - current_paths_set)
        
        # Remove deleted files from embeddings
        for path in removed_paths:
            if path in self.image_embeddings:
                del self.image_embeddings[path]
            if path in self.thumbnail_cache:
                del self.thumbnail_cache[path]
        
        if removed_paths:
            self.status_var.set(f"Removed {len(removed_paths)} deleted files from cache")
            self.update()
        
        # Process new files
        if new_paths:
            self.status_var.set(f"Processing {len(new_paths)} new images...")
            
            progress = ttk.Progressbar(self, mode="determinate", maximum=len(new_paths))
            progress.pack(fill=tk.X, padx=10, pady=10)
            self.update()
            
            for i, path in enumerate(new_paths):
                try:
                    # Process for CLIP embeddings
                    img = Image.open(path).convert("RGB")
                    inputs = self.processor(images=img, return_tensors="pt")
                    with torch.no_grad():
                        emb = self.model.get_image_features(**inputs).squeeze(0)
                    self.image_embeddings[path] = emb
                    
                    # Update progress
                    progress["value"] = i + 1
                    self.status_var.set(f"Processing image {i+1}/{len(new_paths)}: {os.path.basename(path)}")
                    self.update()
                    
                except UnidentifiedImageError:
                    print(f"⚠️ Skipping unreadable file: {path}")
                except Exception as e:
                    print(f"Error processing {path}: {e}")
            
            # Save the updated caches
            torch.save(self.image_embeddings, self.cache_file)
            progress.destroy()
            total_message = f"Processed {len(new_paths)} new images. "
            if removed_paths:
                total_message += f"Removed {len(removed_paths)} deleted images. "
            total_message += f"Total: {len(self.image_embeddings)}"
            self.status_var.set(total_message)
        elif removed_paths:
            # We had removals but no additions
            torch.save(self.image_embeddings, self.cache_file)
            self.status_var.set(f"Removed {len(removed_paths)} deleted images. Total: {len(self.image_embeddings)}")
        else:
            self.status_var.set(f"No changes detected. Total: {len(self.image_embeddings)}")
    
    def get_thumbnail(self, image_path, size=(150, 150)):
        if image_path in self.thumbnail_cache:
            return self.thumbnail_cache[image_path]
        
        try:
            img = Image.open(image_path).convert("RGB")
            img.thumbnail(size)
            photo = ImageTk.PhotoImage(img)
            self.thumbnail_cache[image_path] = photo
            return photo
        except:
            # Return a placeholder for failed images
            return None
    
    def open_image(self, image_path):
        """Open the image with the default system viewer."""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(image_path)
            elif os.name == 'posix':  # macOS and Linux
                if sys.platform == 'darwin':  # macOS
                    subprocess.call(('open', image_path))
                else:  # Linux
                    subprocess.call(('xdg-open', image_path))
            self.status_var.set(f"Opened: {os.path.basename(image_path)}")
        except Exception as e:
            self.status_var.set(f"Error opening file: {str(e)}")
    
    def rename_image(self, image_path):
        """Rename the selected image file."""
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
                    tk.messagebox.showerror("Error", "Please enter a valid filename")
                    return
                
                # Keep the same extension
                if '.' not in new_name and '.' in old_name:
                    extension = old_name.split('.')[-1]
                    new_name = f"{new_name}.{extension}"
                
                new_path = os.path.join(dir_name, new_name)
                
                # Check if the new filename already exists
                if os.path.exists(new_path) and new_path != image_path:
                    tk.messagebox.showerror("Error", f"File '{new_name}' already exists")
                    return
                
                try:
                    # Rename the file
                    os.rename(image_path, new_path)
                    
                    # Update the embeddings dictionaries
                    if image_path in self.image_embeddings:
                        self.image_embeddings[new_path] = self.image_embeddings.pop(image_path)
                    
                    # Update thumbnail cache if exists
                    if image_path in self.thumbnail_cache:
                        self.thumbnail_cache[new_path] = self.thumbnail_cache.pop(image_path)
                    
                    # Save the updated caches
                    torch.save(self.image_embeddings, self.cache_file)
                    
                    # Update status and close dialog
                    self.status_var.set(f"Renamed: {old_name} → {new_name}")
                    dialog.destroy()
                    
                    # Refresh search results if we're in a search
                    if self.search_var.get():
                        self.search_images()
                    
                except Exception as e:
                    tk.messagebox.showerror("Error", f"Failed to rename file: {str(e)}")
            
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
        """Delete the image file with confirmation."""
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
            if image_path in self.image_embeddings:
                del self.image_embeddings[image_path]
            
            if image_path in self.thumbnail_cache:
                del self.thumbnail_cache[image_path]
            
            # Save the updated caches
            torch.save(self.image_embeddings, self.cache_file)
            
            # Update status
            self.status_var.set(f"Deleted: {filename}")
            
            # If we're in a search view, refresh it to remove the deleted image
            if self.search_var.get():
                self.search_images()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete file: {str(e)}")
            self.status_var.set(f"Error deleting file: {str(e)}")
    
    def search_images(self):
        prompt = self.search_var.get()
        if not prompt:
            self.status_var.set("Please enter a search prompt")
            return
        
        if not self.image_embeddings:
            self.status_var.set("No images processed yet. Please select a folder first.")
            return
        
        self.status_var.set(f"Searching for: {prompt}")
        self.update()
        
        # Clear previous results
        for widget in self.results_container.winfo_children():
            widget.destroy()
        
        # Process the search prompt
        inputs = self.processor(text=[prompt], return_tensors="pt", padding=True)
        with torch.no_grad():
            text_emb = self.model.get_text_features(**inputs).squeeze(0)
        
        # Compute similarities
        sims = {}
        for path, img_emb in self.image_embeddings.items():
            sim = torch.nn.functional.cosine_similarity(text_emb, img_emb, dim=0)
            sims[path] = sim.item()
        
        # Get top 24 results
        results = sorted(sims.items(), key=lambda x: x[1], reverse=True)[:24]
        
        # Display results using common function
        self.display_results(results)
        
        self.status_var.set(f"Found {len(results)} results for: {prompt}")
    
    def display_results(self, results):
        """Display search results in a grid."""
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
            name_label = ttk.Label(result_frame, text=os.path.basename(path), wraplength=150)
            name_label.pack()
            
            score_label = ttk.Label(result_frame, text=f"Score: {score:.4f}")
            score_label.pack()
            
            # Add buttons for actions
            btn_frame = ttk.Frame(result_frame)
            btn_frame.pack(pady=(5, 0))
            
            open_btn = ttk.Button(btn_frame, text="Open", width=6, 
                                 command=lambda p=path: self.open_image(p))
            open_btn.pack(side=tk.LEFT, padx=2)
            
            rename_btn = ttk.Button(btn_frame, text="Rename", width=7,
                                   command=lambda p=path: self.rename_image(p))
            rename_btn.pack(side=tk.LEFT, padx=2)
            
            # Add delete button
            delete_btn = ttk.Button(btn_frame, text="Delete", width=6,
                                  command=lambda p=path: self.delete_image(p))
            delete_btn.pack(side=tk.LEFT, padx=2)
    
    def check_folder_on_startup(self):
        """Check for new or deleted files in the folder on application startup."""
        if self.image_folder and os.path.isdir(self.image_folder):
            self.status_var.set(f"Checking for changes in: {self.image_folder}")
            self.update()
            
            # Check for new/deleted image files
            self.process_images()
            self.status_var.set(f"Startup check complete. {len(self.image_embeddings)} images loaded.")
    
    def destroy(self):
        """Save config before destroying the window."""
        if self.image_folder:
            self.save_config()
        super().destroy()

if __name__ == "__main__":
    app = ClipImageSearch()
    app.mainloop()
