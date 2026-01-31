"""
Tests for security utilities including encryption, JWT, and API key management.
"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
import json

from utils.security import (
    EncryptionManager,
    APIKeyManager,
    JWTManager,
    PasswordManager,
    generate_secure_key
)
from utils.errors import (
    SecurityException,
    InvalidTokenException,
    TokenExpiredException
)


# ============================================================================
# Unit Tests
# ============================================================================

class TestEncryptionManager:
    """Unit tests for EncryptionManager."""
    
    def test_encrypt_decrypt_string(self):
        """Test basic string encryption and decryption."""
        manager = EncryptionManager()
        original = "sensitive data"
        
        encrypted = manager.encrypt(original)
        assert encrypted != original
        
        decrypted = manager.decrypt(encrypted)
        assert decrypted == original
    
    def test_encrypt_decrypt_dict(self):
        """Test dictionary encryption and decryption."""
        manager = EncryptionManager()
        original = {"api_key": "secret123", "user": "test"}
        
        encrypted = manager.encrypt_dict(original)
        assert isinstance(encrypted, str)
        
        decrypted = manager.decrypt_dict(encrypted)
        assert decrypted == original
    
    def test_decrypt_invalid_data(self):
        """Test decryption of invalid data raises exception."""
        manager = EncryptionManager()
        
        with pytest.raises(SecurityException):
            manager.decrypt("invalid_encrypted_data")


class TestAPIKeyManager:
    """Unit tests for APIKeyManager."""
    
    def test_store_retrieve_api_key(self):
        """Test storing and retrieving API key."""
        manager = APIKeyManager()
        api_key = "sk-test123456789"
        
        encrypted = manager.store_api_key("test_service", api_key)
        assert encrypted != api_key
        
        retrieved = manager.retrieve_api_key(encrypted)
        assert retrieved == api_key
    
    def test_mask_api_key(self):
        """Test API key masking."""
        manager = APIKeyManager()
        api_key = "sk-test123456789"
        
        masked = manager.mask_api_key(api_key, visible_chars=4)
        assert masked.endswith("6789")
        assert masked.startswith("*")
        assert len(masked) == len(api_key)
    
    def test_mask_short_api_key(self):
        """Test masking of short API key."""
        manager = APIKeyManager()
        api_key = "abc"
        
        masked = manager.mask_api_key(api_key, visible_chars=4)
        assert masked == "***"


class TestJWTManager:
    """Unit tests for JWTManager."""
    
    def test_create_verify_access_token(self):
        """Test creating and verifying access token."""
        manager = JWTManager()
        data = {"user_id": "123", "email": "test@example.com"}
        
        token = manager.create_access_token(data)
        assert isinstance(token, str)
        
        payload = manager.verify_token(token)
        assert payload["user_id"] == "123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"
    
    def test_create_refresh_token(self):
        """Test creating refresh token."""
        manager = JWTManager()
        data = {"user_id": "123"}
        
        token = manager.create_refresh_token(data)
        payload = manager.verify_token(token)
        
        assert payload["user_id"] == "123"
        assert payload["type"] == "refresh"
    
    def test_expired_token(self):
        """Test expired token raises exception."""
        manager = JWTManager()
        data = {"user_id": "123"}
        
        # Create token that expires immediately
        token = manager.create_access_token(
            data,
            expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(TokenExpiredException):
            manager.verify_token(token)
    
    def test_invalid_token(self):
        """Test invalid token raises exception."""
        manager = JWTManager()
        
        with pytest.raises(InvalidTokenException):
            manager.verify_token("invalid.token.here")
    
    def test_decode_without_verification(self):
        """Test decoding token without verification."""
        manager = JWTManager()
        data = {"user_id": "123", "role": "admin"}
        
        token = manager.create_access_token(data)
        payload = manager.decode_token_without_verification(token)
        
        assert payload["user_id"] == "123"
        assert payload["role"] == "admin"


class TestPasswordManager:
    """Unit tests for PasswordManager."""
    
    def test_hash_verify_password(self):
        """Test password hashing and verification."""
        password = "SecurePassword123!"
        
        hashed = PasswordManager.hash_password(password)
        assert hashed != password
        assert isinstance(hashed, str)
        
        # Correct password should verify
        assert PasswordManager.verify_password(password, hashed) is True
        
        # Wrong password should not verify
        assert PasswordManager.verify_password("WrongPassword", hashed) is False
    
    def test_different_hashes_for_same_password(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "TestPassword123"
        
        hash1 = PasswordManager.hash_password(password)
        hash2 = PasswordManager.hash_password(password)
        
        assert hash1 != hash2
        assert PasswordManager.verify_password(password, hash1) is True
        assert PasswordManager.verify_password(password, hash2) is True


class TestSecureKeyGeneration:
    """Unit tests for secure key generation."""
    
    def test_generate_secure_key(self):
        """Test secure key generation."""
        key = generate_secure_key()
        assert isinstance(key, str)
        assert len(key) > 0
    
    def test_generate_keys_are_unique(self):
        """Test that generated keys are unique."""
        key1 = generate_secure_key()
        key2 = generate_secure_key()
        assert key1 != key2


# ============================================================================
# Property-Based Tests
# ============================================================================

class TestEncryptionProperties:
    """
    Feature: crypto-analysis-system, Property 29: Veri Şifreleme
    Herhangi bir saklanan kullanıcı verisi için, şifreli olarak depolanmalıdır.
    """
    
    @given(st.text(min_size=1, max_size=1000))
    @settings(max_examples=100)
    def test_property_29_encryption_decryption_roundtrip(self, data: str):
        """
        Property: Encryption and decryption should be reversible.
        Any data encrypted and then decrypted should return the original data.
        """
        manager = EncryptionManager()
        
        # Encrypt the data
        encrypted = manager.encrypt(data)
        
        # Encrypted data should be different from original
        assert encrypted != data
        
        # Decrypt should return original
        decrypted = manager.decrypt(encrypted)
        assert decrypted == data
    
    @given(st.dictionaries(
        keys=st.text(min_size=1, max_size=50),
        values=st.one_of(
            st.text(max_size=100),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.booleans(),
            st.none()
        ),
        min_size=1,
        max_size=20
    ))
    @settings(max_examples=100)
    def test_property_29_dict_encryption_preserves_structure(self, data: dict):
        """
        Property: Dictionary encryption should preserve data structure.
        Any dictionary encrypted and decrypted should maintain its structure and values.
        """
        manager = EncryptionManager()
        
        # Encrypt the dictionary
        encrypted = manager.encrypt_dict(data)
        
        # Should be a string
        assert isinstance(encrypted, str)
        
        # Decrypt should return original dictionary
        decrypted = manager.decrypt_dict(encrypted)
        assert decrypted == data
        assert type(decrypted) == dict
    
    @given(st.text(min_size=1, max_size=500))
    @settings(max_examples=100)
    def test_property_29_encrypted_data_is_different(self, data: str):
        """
        Property: Encrypted data should always be different from original.
        For any non-empty data, encryption should produce different output.
        """
        manager = EncryptionManager()
        
        encrypted = manager.encrypt(data)
        
        # Encrypted should be different from original
        assert encrypted != data
        
        # Encrypted should be non-empty
        assert len(encrypted) > 0
    
    @given(st.text(min_size=1, max_size=500))
    @settings(max_examples=100)
    def test_property_29_encryption_is_deterministic_per_instance(self, data: str):
        """
        Property: Same data encrypted twice with same key should be decryptable.
        While encryption may produce different ciphertexts, both should decrypt correctly.
        """
        manager = EncryptionManager()
        
        encrypted1 = manager.encrypt(data)
        encrypted2 = manager.encrypt(data)
        
        # Both should decrypt to original
        assert manager.decrypt(encrypted1) == data
        assert manager.decrypt(encrypted2) == data


class TestAPIKeySecurityProperties:
    """
    Feature: crypto-analysis-system, Property 30: API Anahtarı Güvenliği
    Herhangi bir API anahtarı için, düz metin olarak saklanmamalı ve 
    güvenli şekilde yönetilmelidir.
    """
    
    @given(st.text(min_size=10, max_size=100, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='-_'
    )))
    @settings(max_examples=100)
    def test_property_30_api_keys_not_stored_plaintext(self, api_key: str):
        """
        Property: API keys should never be stored in plaintext.
        Any API key stored should be encrypted and different from original.
        """
        manager = APIKeyManager()
        
        # Store the API key (encrypted)
        encrypted = manager.store_api_key("test_service", api_key)
        
        # Encrypted version should be different from original
        assert encrypted != api_key
        
        # Should not contain the original key
        assert api_key not in encrypted
        
        # Should be retrievable
        retrieved = manager.retrieve_api_key(encrypted)
        assert retrieved == api_key
    
    @given(st.text(min_size=10, max_size=100, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='-_'
    )))
    @settings(max_examples=100)
    def test_property_30_api_key_masking_hides_sensitive_data(self, api_key: str):
        """
        Property: Masked API keys should hide sensitive information.
        Masked keys should not reveal the full key but show only last few characters.
        """
        manager = APIKeyManager()
        
        masked = manager.mask_api_key(api_key, visible_chars=4)
        
        # Masked should be same length
        assert len(masked) == len(api_key)
        
        # Should contain asterisks
        assert '*' in masked
        
        # Should show last 4 characters if key is long enough
        if len(api_key) > 4:
            assert masked.endswith(api_key[-4:])
            # Most of the key should be masked
            assert masked.count('*') >= len(api_key) - 4
    
    @given(st.text(min_size=20, max_size=100, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='-_'
    )))
    @settings(max_examples=100)
    def test_property_30_api_key_encryption_is_reversible(self, api_key: str):
        """
        Property: API key encryption should be reversible.
        Any encrypted API key should be decryptable to original value.
        """
        manager = APIKeyManager()
        
        encrypted = manager.store_api_key("service", api_key)
        retrieved = manager.retrieve_api_key(encrypted)
        
        assert retrieved == api_key
        assert encrypted != api_key


class TestJWTSecurityProperties:
    """Property tests for JWT token security."""
    
    # Reserved JWT claims that should be excluded from property tests
    RESERVED_CLAIMS = {'exp', 'iat', 'nbf', 'iss', 'aud', 'sub', 'jti'}
    
    @given(st.dictionaries(
        keys=st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='_'
        )).filter(lambda k: k not in {'exp', 'iat', 'nbf', 'iss', 'aud', 'sub', 'jti'}),
        values=st.one_of(st.text(max_size=50), st.integers(), st.booleans()),
        min_size=1,
        max_size=10
    ))
    @settings(max_examples=100)
    def test_property_jwt_token_contains_original_data(self, data: dict):
        """
        Property: JWT tokens should preserve original data.
        Any data encoded in a JWT should be retrievable after verification.
        Note: Reserved JWT claims (exp, iat, etc.) are excluded from this test.
        """
        manager = JWTManager()
        
        token = manager.create_access_token(data)
        payload = manager.verify_token(token)
        
        # All original data should be in payload
        for key, value in data.items():
            assert key in payload
            assert payload[key] == value
    
    @given(st.dictionaries(
        keys=st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='_'
        )),
        values=st.text(max_size=50),
        min_size=1,
        max_size=5
    ))
    @settings(max_examples=100)
    def test_property_jwt_tokens_have_expiration(self, data: dict):
        """
        Property: All JWT tokens should have expiration time.
        Any created token should include 'exp' and 'iat' claims.
        """
        manager = JWTManager()
        
        token = manager.create_access_token(data)
        payload = manager.verify_token(token)
        
        # Should have expiration and issued-at times
        assert 'exp' in payload
        assert 'iat' in payload
        assert payload['exp'] > payload['iat']


class TestPasswordSecurityProperties:
    """Property tests for password security."""
    
    @given(st.text(
        min_size=8, 
        max_size=50,  # Reduced from 100 to stay well under bcrypt's 72 byte limit
        alphabet=st.characters(min_codepoint=32, max_codepoint=126)  # ASCII printable only
    ))
    @settings(max_examples=100, deadline=1000)  # Increased deadline for bcrypt
    def test_property_password_hashing_is_one_way(self, password: str):
        """
        Property: Password hashing should be one-way.
        Hashed passwords should be different from original and not reversible.
        Note: Bcrypt has a 72 byte limit, so we limit password length.
        """
        # Ensure password doesn't exceed bcrypt's 72 byte limit
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password = password[:50]  # Truncate to safe length
        
        hashed = PasswordManager.hash_password(password)
        
        # Hash should be different from password
        assert hashed != password
        
        # Should verify correctly
        assert PasswordManager.verify_password(password, hashed) is True
        
        # Wrong password should not verify
        if len(password) > 1:
            wrong_password = password[:-1] + ('x' if password[-1] != 'x' else 'y')
            assert PasswordManager.verify_password(wrong_password, hashed) is False
    
    @given(st.text(
        min_size=8, 
        max_size=50,  # Reduced from 100 to stay well under bcrypt's 72 byte limit
        alphabet=st.characters(min_codepoint=32, max_codepoint=126)  # ASCII printable only
    ))
    @settings(max_examples=50, deadline=1000)  # Increased deadline for bcrypt
    def test_property_password_hashes_are_unique(self, password: str):
        """
        Property: Same password should produce different hashes (salted).
        Multiple hashes of the same password should be different due to salt.
        Note: Bcrypt has a 72 byte limit, so we limit password length.
        """
        # Ensure password doesn't exceed bcrypt's 72 byte limit
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password = password[:50]  # Truncate to safe length
        
        hash1 = PasswordManager.hash_password(password)
        hash2 = PasswordManager.hash_password(password)
        
        # Hashes should be different (due to salt)
        assert hash1 != hash2
        
        # But both should verify the same password
        assert PasswordManager.verify_password(password, hash1) is True
        assert PasswordManager.verify_password(password, hash2) is True
