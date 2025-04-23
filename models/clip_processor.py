"""
CLIP model and image processing functionality
"""
import os
import torch
from PIL import Image, UnidentifiedImageError
from transformers import CLIPProcessor, CLIPModel

class ClipModel:
    """Handles CLIP model operations and image processing"""
    
    def __init__(self, cache_file="clip_embeddings.pt"):
        """Initialize the CLIP model
        
        Args:
            cache_file: Path to the embeddings cache file
        """
        self.cache_file = cache_file
        self.image_embeddings = {}
        
        # Initialize CLIP model
        MODEL_NAME = "openai/clip-vit-base-patch32"
        self.model = CLIPModel.from_pretrained(MODEL_NAME).eval()
        self.processor = CLIPProcessor.from_pretrained(MODEL_NAME)
        
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
    
    def search(self, prompt, limit=24):
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