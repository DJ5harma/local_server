"""
Authentication utilities.
"""
from ..config import Config


def verify_password(password: str) -> bool:
    """
    Verify login password.
    
    Args:
        password: Password to verify
        
    Returns:
        True if password is correct, False otherwise
    """
    return password == Config.LOGIN_PASSWORD

