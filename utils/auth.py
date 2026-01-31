"""
Authentication and authorization utilities for FastAPI.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.security import jwt_manager
from utils.errors import AuthenticationException, InvalidTokenException, TokenExpiredException


# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        User data from token payload
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token = credentials.credentials
        payload = jwt_manager.verify_token(token)
        
        # Verify token type
        if payload.get("type") != "access":
            raise AuthenticationException("Invalid token type")
        
        return payload
    
    except TokenExpiredException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    except (InvalidTokenException, AuthenticationException) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Dependency to get current user if authenticated, None otherwise.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        User data from token payload or None
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = jwt_manager.verify_token(token)
        
        if payload.get("type") != "access":
            return None
        
        return payload
    
    except (TokenExpiredException, InvalidTokenException, AuthenticationException):
        return None


def require_role(required_role: str):
    """
    Dependency factory to require specific user role.
    
    Args:
        required_role: Required role name
        
    Returns:
        Dependency function
    """
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role")
        
        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        
        return current_user
    
    return role_checker


def require_any_role(*required_roles: str):
    """
    Dependency factory to require any of the specified roles.
    
    Args:
        required_roles: List of acceptable role names
        
    Returns:
        Dependency function
    """
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role")
        
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(required_roles)}"
            )
        
        return current_user
    
    return role_checker
