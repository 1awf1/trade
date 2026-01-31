"""
Secure configuration management for sensitive data.
"""
from typing import Optional, Dict, Any
import os
from pathlib import Path
from utils.security import encryption_manager, api_key_manager
from utils.logger import get_logger

logger = get_logger(__name__)


class SecureConfigManager:
    """Manager for secure storage and retrieval of sensitive configuration."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize secure config manager.
        
        Args:
            config_file: Path to encrypted config file
        """
        self.config_file = config_file or ".secure_config.enc"
        self._config_cache: Optional[Dict[str, Any]] = None
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """
        Save configuration securely (encrypted).
        
        Args:
            config: Configuration dictionary to save
        """
        try:
            encrypted_data = encryption_manager.encrypt_dict(config)
            
            with open(self.config_file, 'w') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions (owner read/write only)
            os.chmod(self.config_file, 0o600)
            
            self._config_cache = config
            logger.info("Secure configuration saved successfully")
        
        except Exception as e:
            logger.error(f"Failed to save secure configuration: {e}")
            raise
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from encrypted file.
        
        Returns:
            Configuration dictionary
        """
        if self._config_cache is not None:
            return self._config_cache
        
        if not Path(self.config_file).exists():
            logger.warning(f"Secure config file not found: {self.config_file}")
            return {}
        
        try:
            with open(self.config_file, 'r') as f:
                encrypted_data = f.read()
            
            config = encryption_manager.decrypt_dict(encrypted_data)
            self._config_cache = config
            
            logger.info("Secure configuration loaded successfully")
            return config
        
        except Exception as e:
            logger.error(f"Failed to load secure configuration: {e}")
            return {}
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        config = self.load_config()
        return config.get(key, default)
    
    def set_value(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        config = self.load_config()
        config[key] = value
        self.save_config(config)
    
    def delete_value(self, key: str) -> None:
        """
        Delete configuration value.
        
        Args:
            key: Configuration key to delete
        """
        config = self.load_config()
        if key in config:
            del config[key]
            self.save_config(config)
    
    def clear_cache(self) -> None:
        """Clear configuration cache."""
        self._config_cache = None


class APIKeyStore:
    """Secure storage for API keys."""
    
    def __init__(self):
        """Initialize API key store."""
        self.config_manager = SecureConfigManager(".api_keys.enc")
    
    def store_api_key(self, service_name: str, api_key: str) -> None:
        """
        Store API key securely.
        
        Args:
            service_name: Name of the service (e.g., 'binance', 'openai')
            api_key: API key to store
        """
        encrypted_key = api_key_manager.store_api_key(service_name, api_key)
        self.config_manager.set_value(service_name, encrypted_key)
        logger.info(f"API key stored for service: {service_name}")
    
    def retrieve_api_key(self, service_name: str) -> Optional[str]:
        """
        Retrieve API key.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Decrypted API key or None if not found
        """
        encrypted_key = self.config_manager.get_value(service_name)
        
        if not encrypted_key:
            logger.warning(f"API key not found for service: {service_name}")
            return None
        
        try:
            api_key = api_key_manager.retrieve_api_key(encrypted_key)
            return api_key
        except Exception as e:
            logger.error(f"Failed to retrieve API key for {service_name}: {e}")
            return None
    
    def delete_api_key(self, service_name: str) -> None:
        """
        Delete API key.
        
        Args:
            service_name: Name of the service
        """
        self.config_manager.delete_value(service_name)
        logger.info(f"API key deleted for service: {service_name}")
    
    def list_services(self) -> list:
        """
        List all services with stored API keys.
        
        Returns:
            List of service names
        """
        config = self.config_manager.load_config()
        return list(config.keys())
    
    def get_masked_key(self, service_name: str) -> Optional[str]:
        """
        Get masked API key for display.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Masked API key or None if not found
        """
        api_key = self.retrieve_api_key(service_name)
        
        if not api_key:
            return None
        
        return api_key_manager.mask_api_key(api_key)


# Global instances
secure_config_manager = SecureConfigManager()
api_key_store = APIKeyStore()
