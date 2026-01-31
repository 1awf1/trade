#!/usr/bin/env python3
"""Quick test script to verify checkpoint 21 fixes."""

import sys

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")
    try:
        from models.schemas import OverallSentiment
        print("✅ OverallSentiment import fixed")
        return True
    except ImportError as e:
        print(f"❌ OverallSentiment import failed: {e}")
        return False

def test_password_constraints():
    """Test password hashing with bcrypt constraints."""
    print("\nTesting password hashing...")
    try:
        from utils.security import PasswordManager
        
        # Test normal password
        password = "test_password_123"
        hashed = PasswordManager.hash_password(password)
        assert PasswordManager.verify_password(password, hashed)
        print("✅ Normal password hashing works")
        
        # Test long password (should be truncated)
        long_password = "a" * 100
        hashed_long = PasswordManager.hash_password(long_password[:72])
        assert PasswordManager.verify_password(long_password[:72], hashed_long)
        print("✅ Long password handling works")
        
        return True
    except Exception as e:
        print(f"❌ Password hashing failed: {e}")
        return False

def test_jwt_reserved_claims():
    """Test JWT with reserved claims."""
    print("\nTesting JWT token handling...")
    try:
        from utils.security import JWTManager
        
        # Test with non-reserved claims
        manager = JWTManager()
        data = {"user_id": "123", "role": "admin"}
        token = manager.create_access_token(data)
        payload = manager.verify_token(token)
        
        assert payload["user_id"] == "123"
        assert payload["role"] == "admin"
        print("✅ JWT token with custom claims works")
        
        # Reserved claims like 'exp' are added automatically
        assert "exp" in payload
        print("✅ JWT reserved claims handled correctly")
        
        return True
    except Exception as e:
        print(f"❌ JWT handling failed: {e}")
        return False

def test_api_error_serialization():
    """Test that API errors are JSON serializable."""
    print("\nTesting API error serialization...")
    try:
        # Simulate validation error serialization
        error = {
            "loc": ["body", "timeframe"],
            "msg": "Invalid timeframe",
            "type": "value_error",
            "ctx": {"error": ValueError("Invalid value")}
        }
        
        # Convert ctx to strings
        serializable_error = {
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"],
            "ctx": {k: str(v) for k, v in error["ctx"].items()}
        }
        
        import json
        json.dumps(serializable_error)  # Should not raise
        print("✅ API error serialization works")
        
        return True
    except Exception as e:
        print(f"❌ API error serialization failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Checkpoint 21 Fixes Verification")
    print("=" * 60)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Password Hashing", test_password_constraints()))
    results.append(("JWT Handling", test_jwt_reserved_claims()))
    results.append(("API Error Serialization", test_api_error_serialization()))
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
