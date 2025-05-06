"""
CLIP model and image processing functionality
"""
import os
# Set environment variables before importing any huggingface/transformers modules
os.environ['TRANSFORMERS_CACHE'] = os.path.join(os.path.expanduser("~"), "AppData", "Local", "CLIPImageSearch", "model")
os.environ['HF_HOME'] = os.path.join(os.path.expanduser("~"), "AppData", "Local", "CLIPImageSearch", "model")
os.environ['HUGGINGFACE_HUB_CACHE'] = os.path.join(os.path.expanduser("~"), "AppData", "Local", "CLIPImageSearch", "model")

import torch
from PIL import Image, UnidentifiedImageError
from transformers import CLIPProcessor, CLIPModel
import numpy as np

import sys


class ClipModel:
    """Handles CLIP model operations and image processing"""
    
    def __init__(self, cache_file="clip_embeddings.pt", progress_callback=None):
        """Initialize the CLIP model with progress reporting
        
        Args:
            cache_file: Path to the embeddings cache file
            progress_callback: Function to call with progress updates
        """
        # Use the application directory instead of user Documents
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            app_path = os.path.dirname(sys.executable)
        else:
            # Running in development environment
            app_path = os.path.dirname(os.path.abspath(__file__))
            app_path = os.path.dirname(app_path)  # Go up one level
        
        # Create directories for app data
        self.app_data_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "CLIPImageSearch")
        self.model_dir = os.path.join(self.app_data_dir, "model")
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Always store cache file in AppData to avoid permission issues
        self.cache_file = os.path.join(self.app_data_dir, cache_file)
        self.image_embeddings = {}
        
        # Only initialize the model when needed
        MODEL_NAME = "openai/clip-vit-base-patch32"
        
        # Report progress if callback is provided
        if progress_callback:
            progress_callback("Initializing CLIP model...")
        
        # Initialize CLIP model with explicit cache directory
        self.model = CLIPModel.from_pretrained(
            MODEL_NAME,
            cache_dir=self.model_dir
        ).eval()
        
        self.processor = CLIPProcessor.from_pretrained(
            MODEL_NAME,
            cache_dir=self.model_dir
        )
        
        # When downloading model:
        if progress_callback:
            progress_callback("Downloading model files...", 25)
        
        # After downloading:
        if progress_callback:
            progress_callback("Processing model...", 75)
        
        # When finished:
        if progress_callback:
            progress_callback("Model ready", 100)
        
        # Load cached embeddings if available
        self.load_cache()
    
    def load_cache(self):
        """Load embeddings from cache file if it exists"""
        if os.path.exists(self.cache_file):
            try:
                self.image_embeddings = torch.load(self.cache_file)
                return len(self.image_embeddings)
            except Exception as e:
                print(f"Error loading image embeddings: {e}")
                self.image_embeddings = {}
        return 0
    
    def save_cache(self):
        """Save current embeddings to cache file"""
        try:
            torch.save(self.image_embeddings, self.cache_file)
            return True
        except Exception as e:
            print(f"Error saving embeddings cache: {e}")
            return False
    
    def get_image_embedding(self, image_path):
        """Generate embedding for a single image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            torch.Tensor: Image embedding or None if processing failed
        """
        try:
            img = Image.open(image_path).convert("RGB")
            inputs = self.processor(images=img, return_tensors="pt")
            with torch.no_grad():
                embedding = self.model.get_image_features(**inputs).squeeze(0)
            return embedding
        except UnidentifiedImageError:
            print(f"⚠️ Skipping unreadable file: {image_path}")
            return None
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            return None
    
    def process_images(self, image_paths, status_callback=None):
        """Process multiple images and update embeddings
        
        Args:
            image_paths: List of image file paths to process
            status_callback: Optional callback function for progress updates
            
        Returns:
            int: Number of successfully processed images
        """
        processed_count = 0
        
        for i, path in enumerate(image_paths):
            if status_callback:
                status_callback(i, len(image_paths), os.path.basename(path))
                
            embedding = self.get_image_embedding(path)
            if embedding is not None:
                self.image_embeddings[path] = embedding
                processed_count += 1
        
        return processed_count
    
    def remove_images(self, image_paths):
        """Remove specified images from embeddings
        
        Args:
            image_paths: List of paths to remove
            
        Returns:
            int: Number of images removed
        """
        removed_count = 0
        for path in image_paths:
            if path in self.image_embeddings:
                del self.image_embeddings[path]
                removed_count += 1
        return removed_count
    
    def search(self, prompt, limit=100):
        """Search for images matching the text prompt
        
        Args:
            prompt: Text description to search for
            limit: Maximum number of results to return
            
        Returns:
            list: List of (image_path, similarity_score) tuples
        """
        if not prompt or not self.image_embeddings:
            return []
        
        # Get text embedding for the prompt
        inputs = self.processor(text=[prompt], return_tensors="pt", padding=True)
        with torch.no_grad():
            text_embedding = self.model.get_text_features(**inputs).squeeze(0)
        
        # Calculate similarities
        similarities = {}
        for path, img_emb in self.image_embeddings.items():
            sim = torch.nn.functional.cosine_similarity(text_embedding, img_emb, dim=0)
            similarities[path] = sim.item()
        
        # Sort by similarity and return top results
        results = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:limit]
        return results 