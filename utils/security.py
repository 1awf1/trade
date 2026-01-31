"""
Security utilities for encryption, JWT tokens, and API key management.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import jwt
import base64
import os
from utils.config import settings
from utils.errors import (
    SecurityException,
    InvalidTokenException,
    TokenExpiredException,
    AuthenticationException
)


class EncryptionManager:
    """Manager for data encryption and decryption."""
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize encryption manager.
        
        Args:
            secret_key: Secret key for encryption (uses settings.SECRET_KEY if not provided)
        """
        self.secret_key = secret_key or settings.SECRET_KEY
        self._cipher = None
    
    def _get_cipher(self) -> Fernet:
        """Get or create Fernet cipher instance."""
        if self._cipher is None:
            # Derive a key from the secret key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'crypto_analysis_salt',  # In production, use a random salt stored securely
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.secret_key.encode()))
            self._cipher = Fernet(key)
        return self._cipher
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt string data.
        
        Args:
            data: Plain text data to encrypt
            
        Returns:
            Encrypted data as base64 string
        """
        cipher = self._get_cipher()
        encrypted = cipher.encrypt(data.encode())
        return encrypted.decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt encrypted data.
        
        Args:
            encrypted_data: Encrypted data as base64 string
            
        Returns:
            Decrypted plain text data
        """
        cipher = self._get_cipher()
        try:
            decrypted = cipher.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            raise SecurityException(
                "Failed to decrypt data",
                details={"error": str(e)}
            )
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """
        Encrypt dictionary data.
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Encrypted data as base64 string
        """
        import json
        json_str = json.dumps(data)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt data to dictionary.
        
        Args:
            encrypted_data: Encrypted data as base64 string
            
        Returns:
            Decrypted dictionary
        """
        import json
        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)


class APIKeyManager:
    """Manager for secure API key storage and retrieval."""
    
    def __init__(self):
        """Initialize API key manager."""
        self.encryption_manager = EncryptionManager()
    
    def store_api_key(self, key_name: str, api_key: str) -> str:
        """
        Store API key securely (encrypted).
        
        Args:
            key_name: Name/identifier for the API key
            api_key: The API key to store
            
        Returns:
            Encrypted API key
        """
        return self.encryption_manager.encrypt(api_key)
    
    def retrieve_api_key(self, encrypted_key: str) -> str:
        """
        Retrieve and decrypt API key.
        
        Args:
            encrypted_key: Encrypted API key
            
        Returns:
            Decrypted API key
        """
        return self.encryption_manager.decrypt(encrypted_key)
    
    def mask_api_key(self, api_key: str, visible_chars: int = 4) -> str:
        """
        Mask API key for display purposes.
        
        Args:
            api_key: API key to mask
            visible_chars: Number of characters to show at the end
            
        Returns:
            Masked API key (e.g., "****abcd")
        """
        if len(api_key) <= visible_chars:
            return "*" * len(api_key)
        return "*" * (len(api_key) - visible_chars) + api_key[-visible_chars:]


class JWTManager:
    """Manager for JWT token creation and validation."""
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: Optional[str] = None,
        access_token_expire_minutes: Optional[int] = None
    ):
        """
        Initialize JWT manager.
        
        Args:
            secret_key: Secret key for JWT signing
            algorithm: JWT algorithm (default: HS256)
            access_token_expire_minutes: Token expiration time in minutes
        """
        self.secret_key = secret_key or settings.SECRET_KEY
        self.algorithm = algorithm or settings.ALGORITHM
        self.access_token_expire_minutes = (
            access_token_expire_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token.
        
        Args:
            data: Data to encode in the token
            expires_delta: Custom expiration time
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT refresh token.
        
        Args:
            data: Data to encode in the token
            expires_delta: Custom expiration time (default: 7 days)
            
        Returns:
            JWT refresh token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token payload
            
        Raises:
            InvalidTokenException: If token is invalid
            TokenExpiredException: If token has expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise TokenExpiredException("Token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenException(f"Invalid token: {str(e)}")
    
    def decode_token_without_verification(self, token: str) -> Dict[str, Any]:
        """
        Decode token without verification (for debugging/inspection only).
        
        Args:
            token: JWT token to decode
            
        Returns:
            Decoded token payload
        """
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            raise InvalidTokenException(f"Failed to decode token: {str(e)}")


class PasswordManager:
    """Manager for password hashing and verification."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        import bcrypt
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed.decode()
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            hashed_password: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        import bcrypt
        try:
            return bcrypt.checkpw(password.encode(), hashed_password.encode())
        except Exception:
            return False


# Global instances
encryption_manager = EncryptionManager()
api_key_manager = APIKeyManager()
jwt_manager = JWTManager()
password_manager = PasswordManager()


def generate_secure_key(length: int = 32) -> str:
    """
    Generate a secure random key.
    
    Args:
        length: Length of the key in bytes
        
    Returns:
        Base64-encoded random key
    """
    random_bytes = os.urandom(length)
    return base64.urlsafe_b64encode(random_bytes).decode()
