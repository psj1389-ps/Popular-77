"""
File utility functions for the image converter service
"""

import os
from typing import List

def ensure_dirs(directories: List[str]) -> None:
    """
    Ensure that the specified directories exist, create them if they don't
    
    Args:
        directories: List of directory paths to ensure exist
    """
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

def get_file_extension(filename: str) -> str:
    """
    Get the file extension from a filename
    
    Args:
        filename: The filename to extract extension from
        
    Returns:
        str: The file extension (without the dot)
    """
    return os.path.splitext(filename)[1][1:].lower()

def is_allowed_file(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Check if a file has an allowed extension
    
    Args:
        filename: The filename to check
        allowed_extensions: List of allowed extensions
        
    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    return get_file_extension(filename) in [ext.lower() for ext in allowed_extensions]