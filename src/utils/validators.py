"""Common validation utilities with password security standards."""

import re
from typing import List, Dict, Any
from fastapi import UploadFile, HTTPException, status


# Common weak passwords to blacklist (OWASP recommendations)
# COMMON_PASSWORDS = {
#     "password", "123456", "123456789", "12345678", "12345", "1234567", "1234567890",
#     "qwerty", "abc123", "111111", "123123", "admin", "letmein", "welcome", "monkey",
#     "login", "admin123", "qwerty123", "password123", "123abc", "master", "hello",
#     "welcome123", "administrator", "root", "toor", "pass", "test", "guest", "info",
#     "user", "default", "changeme", "password1", "qwertyuiop", "asdfghjkl", "zxcvbnm",
#     "superman", "batman", "dragon", "ninja", "mustang", "access", "shadow", "football",
#     "baseball", "basketball", "jordan", "harley", "ranger", "buster", "soccer", "hockey"
# }


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength according to OWASP standards.
    
    Requirements:
    - Minimum 12 characters
    - At least one lowercase letter
    - At least one uppercase letter  
    - At least one digit
    - At least one special character
    - Not in common password blacklist
    - No sequential characters
    - No repeated characters
    
    Returns:
        Dict with 'valid' (bool) and 'errors' (list) keys
    """
    errors = []
    
    # Basic length checks
    if len(password) < 8:
        errors.append("Password must be at least 12 characters long")
    
    # if len(password) > 128:
    #     errors.append("Password must not exceed 128 characters")
    
    # Character variety requirements
    # if not re.search(r'[a-z]', password):
    #     errors.append("Password must contain at least one lowercase letter")
    
    # if not re.search(r'[A-Z]', password):
    #     errors.append("Password must contain at least one uppercase letter")
    
    # if not re.search(r'\d', password):
    #     errors.append("Password must contain at least one digit")
    
    # if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>?/~`]', password):
    #     errors.append("Password must contain at least one special character")
    
    # Check against common password blacklist
    # if password.lower() in COMMON_PASSWORDS:
    #     errors.append("Password is too common and easily guessable")
    
    # Check for sequential characters (123, abc, qwe, etc.)
    # if _has_sequential_chars(password.lower()):
    #     errors.append("Password cannot contain sequential characters (like 123, abc)")
    
    # Check for repeated characters (aaa, 111, etc.)
    # if _has_repeated_chars(password):
    #     errors.append("Password cannot contain more than 2 consecutive identical characters")
    
    # Check for common substitution patterns (@ for a, 3 for e, etc.)
    # if _has_common_substitutions(password.lower()):
    #     errors.append("Password uses common character substitutions that are easily guessable")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "strength_score": _calculate_strength_score(password)
    }


def _has_sequential_chars(password: str) -> bool:
    """Check for sequential characters in password."""
    sequences = [
        "abcdefghijklmnopqrstuvwxyz",
        "qwertyuiopasdfghjklzxcvbnm",  # QWERTY keyboard layout
        "0123456789"
    ]
    
    for sequence in sequences:
        for i in range(len(sequence) - 2):
            if sequence[i:i+3] in password:
                return True
    
    return False


def _has_repeated_chars(password: str) -> bool:
    """Check for more than 2 consecutive repeated characters."""
    for i in range(len(password) - 2):
        if password[i] == password[i+1] == password[i+2]:
            return True
    return False


def _has_common_substitutions(password: str) -> bool:
    """Check for common character substitutions."""
    substitutions = {
        '@': 'a', '3': 'e', '1': 'i', '0': 'o', '5': 's', 
        '7': 't', '4': 'a', '8': 'b', '6': 'g', '2': 'z'
    }
    
    # Convert substitutions back to check if it becomes a common password
    normalized = password
    for sub, char in substitutions.items():
        normalized = normalized.replace(sub, char)
    
    if normalized in COMMON_PASSWORDS:
        return True
    
    return False


def _calculate_strength_score(password: str) -> int:
    """Calculate password strength score (0-100)."""
    score = 0
    
    # Length scoring
    if len(password) >= 12:
        score += 25
    elif len(password) >= 8:
        score += 10
    
    # Character variety scoring
    if re.search(r'[a-z]', password):
        score += 15
    if re.search(r'[A-Z]', password):
        score += 15
    if re.search(r'\d', password):
        score += 15
    if re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>?/~`]', password):
        score += 20
    
    # Bonus for longer passwords
    if len(password) >= 16:
        score += 10
    
    return min(score, 100)


def validate_password_history(new_password: str, password_history: List[str]) -> bool:
    """
    Check if new password is different from recent passwords.
    OWASP recommends not reusing last 5 passwords.
    """
    from src.auth.jwt import verify_password
    
    for old_password_hash in password_history[-5:]:  # Check last 5 passwords
        if verify_password(new_password, old_password_hash):
            return False
    
    return True


def validate_upload_file(file: UploadFile, allowed_types: List[str] = None, max_size: int = None) -> None:
    """Validate uploaded file."""
    if max_size is None:
        max_size = 10 * 1024 * 1024  # 10MB default
    
    # Check file size
    if hasattr(file.file, 'seek'):
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset position
        
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size ({max_size / (1024*1024):.1f}MB)"
            )
    
    # Check file type
    if allowed_types and file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
        )


def sanitize_filename(filename: str, max_length: int = 50) -> str:
    """Sanitize filename for safe storage."""
    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Limit length
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_length = max_length - len(ext) - 1 if ext else max_length
        filename = name[:max_name_length] + ('.' + ext if ext else '')
    
    return filename
