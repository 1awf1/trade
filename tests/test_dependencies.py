"""
Tests for startup dependency checks.
Includes property-based tests for dependency validation.
"""
import sys
import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import patch, MagicMock
from utils.dependencies import (
    check_dependencies,
    check_database_connection,
    check_redis_connection,
    startup_checks
)


class TestDependencyChecks:
    """Basic dependency check tests."""
    
    def test_check_dependencies_returns_tuple(self):
        """Test that check_dependencies returns a tuple."""
        result = check_dependencies()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], list)
    
    def test_check_dependencies_with_current_python(self):
        """Test dependency check with current Python version."""
        all_ok, missing = check_dependencies()
        
        # Python version should be OK (we're running the test)
        python_version_errors = [m for m in missing if 'Python' in m]
        assert len(python_version_errors) == 0, "Python version should be acceptable"
    
    def test_database_connection_returns_bool(self):
        """Test that database connection check returns boolean."""
        result = check_database_connection()
        assert isinstance(result, bool)
    
    def test_redis_connection_returns_bool(self):
        """Test that Redis connection check returns boolean."""
        result = check_redis_connection()
        assert isinstance(result, bool)
    
    def test_startup_checks_exits_on_missing_dependencies(self):
        """Test that startup_checks exits when dependencies are missing."""
        with patch('utils.dependencies.check_dependencies') as mock_check:
            mock_check.return_value = (False, ['missing-package'])
            
            with pytest.raises(SystemExit) as exc_info:
                startup_checks()
            
            assert exc_info.value.code == 1


class TestDependencyCheckPropertyBased:
    """Property-based tests for dependency checks."""
    
    @given(
        python_major=st.integers(min_value=2, max_value=4),
        python_minor=st.integers(min_value=0, max_value=20)
    )
    @settings(max_examples=20)
    def test_property_20_python_version_detection(self, python_major, python_minor):
        """
        Property 20: Başlangıç Bağımlılık Kontrolü
        
        For any Python version, the system should detect if it's below 3.10.
        
        Validates: Requirement 11.4
        """
        # Mock sys.version_info
        with patch('sys.version_info', (python_major, python_minor, 0)):
            all_ok, missing = check_dependencies()
            
            # If Python version is < 3.10, it should be detected as missing
            if python_major < 3 or (python_major == 3 and python_minor < 10):
                # Should have Python version error
                python_errors = [m for m in missing if 'Python' in m and 'required' in m]
                assert len(python_errors) > 0, \
                    f"Python {python_major}.{python_minor} should be detected as insufficient"
                assert all_ok is False, \
                    f"check_dependencies should return False for Python {python_major}.{python_minor}"
            else:
                # Should not have Python version error (but may have package errors)
                python_errors = [m for m in missing if 'Python' in m and 'required' in m]
                assert len(python_errors) == 0, \
                    f"Python {python_major}.{python_minor} should be acceptable"
    
    @given(
        package_name=st.text(
            min_size=1,
            max_size=30,
            alphabet=st.characters(
                whitelist_categories=('Ll', 'Lu', 'Nd'),
                blacklist_characters=[' ', '\n', '\t']
            )
        )
    )
    @settings(max_examples=20)
    def test_property_20_missing_package_detection(self, package_name):
        """
        Property 20: Başlangıç Bağımlılık Kontrolü
        
        For any missing package, the system should detect and report it.
        
        Validates: Requirement 11.4
        """
        # Skip if package name is empty or invalid
        assume(len(package_name) > 0)
        assume(package_name.isidentifier())
        
        # Mock __import__ to simulate missing package
        original_import = __builtins__.__import__
        
        def mock_import(name, *args, **kwargs):
            if name == package_name:
                raise ImportError(f"No module named '{package_name}'")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            # Temporarily add our package to the required list
            with patch('utils.dependencies.required_packages', [package_name]):
                all_ok, missing = check_dependencies()
                
                # The missing package should be detected
                package_errors = [m for m in missing if package_name in m]
                assert len(package_errors) > 0, \
                    f"Missing package '{package_name}' should be detected"
                assert all_ok is False, \
                    f"check_dependencies should return False when '{package_name}' is missing"
    
    @given(
        db_available=st.booleans(),
        redis_available=st.booleans()
    )
    @settings(max_examples=20)
    def test_property_20_service_availability_detection(self, db_available, redis_available):
        """
        Property 20: Başlangıç Bağımlılık Kontrolü
        
        For any service availability state, the system should correctly detect it.
        
        Validates: Requirement 11.4
        """
        # Mock database connection
        with patch('utils.dependencies.check_database_connection') as mock_db:
            mock_db.return_value = db_available
            
            # Mock Redis connection
            with patch('utils.dependencies.check_redis_connection') as mock_redis:
                mock_redis.return_value = redis_available
                
                # Check database
                db_result = check_database_connection()
                assert db_result == db_available, \
                    f"Database check should return {db_available}"
                
                # Check Redis
                redis_result = check_redis_connection()
                assert redis_result == redis_available, \
                    f"Redis check should return {redis_available}"
    
    @given(
        has_missing_deps=st.booleans(),
        num_missing=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=20)
    def test_property_20_startup_checks_behavior(self, has_missing_deps, num_missing):
        """
        Property 20: Başlangıç Bağımlılık Kontrolü
        
        For any dependency state, startup_checks should exit if dependencies are missing.
        
        Validates: Requirement 11.4
        """
        if has_missing_deps:
            # Generate fake missing dependencies
            missing_deps = [f"missing-package-{i}" for i in range(num_missing)]
            
            with patch('utils.dependencies.check_dependencies') as mock_check:
                mock_check.return_value = (False, missing_deps)
                
                # startup_checks should exit with code 1
                with pytest.raises(SystemExit) as exc_info:
                    startup_checks()
                
                assert exc_info.value.code == 1, \
                    "startup_checks should exit with code 1 when dependencies are missing"
        else:
            # No missing dependencies
            with patch('utils.dependencies.check_dependencies') as mock_check:
                mock_check.return_value = (True, [])
                
                # Mock service checks to avoid actual connections
                with patch('utils.dependencies.check_database_connection') as mock_db:
                    with patch('utils.dependencies.check_redis_connection') as mock_redis:
                        mock_db.return_value = True
                        mock_redis.return_value = True
                        
                        # startup_checks should complete without exiting
                        try:
                            startup_checks()
                            # If we get here, no exception was raised (good)
                            assert True
                        except SystemExit:
                            pytest.fail("startup_checks should not exit when all dependencies are present")


class TestDependencyCheckIntegration:
    """Integration tests for dependency checks."""
    
    def test_all_required_packages_available(self):
        """Test that all required packages are actually available."""
        all_ok, missing = check_dependencies()
        
        if not all_ok:
            pytest.fail(f"Required packages are missing: {', '.join(missing)}")
    
    def test_startup_checks_completes_successfully(self):
        """Test that startup_checks completes without errors."""
        # Mock service checks to avoid requiring actual services
        with patch('utils.dependencies.check_database_connection') as mock_db:
            with patch('utils.dependencies.check_redis_connection') as mock_redis:
                mock_db.return_value = True
                mock_redis.return_value = True
                
                try:
                    startup_checks()
                except SystemExit as e:
                    pytest.fail(f"startup_checks exited unexpectedly with code {e.code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
