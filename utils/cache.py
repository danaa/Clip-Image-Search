"""
Cache management utilities
"""
import os
import torch

class EmbeddingsCache:
    """Manages caching of image embeddings"""
    
    def __init__(self, cache_file="clip_embeddings.pt"):
        """Initialize the embeddings cache
        
        Args:
            cache_file: Path to the cache file
        """
        self.cache_file = cache_file
        self.embeddings = {}
        self.load()
    
    def load(self):
        """Load embeddings from cache file
        
        Returns:
            bool: True if successfully loaded, False otherwise
        """
        if os.path.exists(self.cache_file):
            try:
                self.embeddings = torch.load(self.cache_file)
                return True
            except Exception as e:
                print(f"Error loading embeddings cache: {e}")
                self.embeddings = {}
        return False
    
    def save(self):
        """Save embeddings to cache file
        
        Returns:
            bool: True if successfully saved, False otherwise
        """
        try:
            torch.save(self.embeddings, self.cache_file)
            return True
        except Exception as e:
            print(f"Error saving embeddings cache: {e}")
            return False
    
    def add(self, path, embedding):
        """Add or update an embedding
        
        Args:
            path: Image path
            embedding: Tensor embedding
        """
        self.embeddings[path] = embedding
    
    def remove(self, path):
        """Remove an embedding
        
        Args:
            path: Image path to remove
            
        Returns:
            bool: True if removed, False if not found
        """
        if path in self.embeddings:
            del self.embeddings[path]
            return True
        return False
    
    def get(self, path):
        """Get an embedding by path
        
        Args:
            path: Image path
            
        Returns:
            Tensor or None: The embedding or None if not found
        """
        return self.embeddings.get(path)
    
    def clear(self):
        """Clear all embeddings"""
        self.embeddings = {}
    
    def __len__(self):
        """Get number of cached embeddings"""
        return len(self.embeddings)
    
    def __contains__(self, path):
        """Check if path is in cache"""
        return path in self.embeddings
    
    def items(self):
        """Get all (path, embedding) pairs"""
        return self.embeddings.items() 