"""
Configuration management for CLIP Image Search
"""
import os
import json

class Config:
    """Manages application configuration settings"""
    
    def __init__(self, config_file="clip_config.json"):
        """Initialize configuration manager
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self._config = self._load_config()
    
    def _load_config(self):
        """Load configuration from file
        
        Returns:
            dict: Configuration settings
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
        
        # Return default config if file doesn't exist or has errors
        return {"image_folder": "", "max_results": 50}
    
    def _save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    @property
    def image_folder(self):
        """Get the configured image folder path"""
        return self._config.get("image_folder", "")
    
    @image_folder.setter
    def image_folder(self, value):
        """Set the image folder path and save config
        
        Args:
            value: New image folder path
        """
        self._config["image_folder"] = value
        self._save_config()
    
    @property
    def max_results(self):
        """Get the configured maximum number of search results"""
        return self._config.get("max_results", 50)
    
    @max_results.setter
    def max_results(self, value):
        """Set the maximum number of search results and save config
        
        Args:
            value: New maximum results count
        """
        self._config["max_results"] = value
        self._save_config() 