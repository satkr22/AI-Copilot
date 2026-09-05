import os
from typing import Optional

# Mapping of file extensions to language names
EXTENSION_TO_LANGUAGE = {
    '.py': 'python',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.java': 'java',
    '.c': 'c',
}


def detect_language(file_path: str) -> Optional[str]:
    """
    Detect the programming language of a file based on its extension.
    
    Args:
        file_path: Path to the file (can be absolute or relative)
        
    Returns:
        The language name as a string, or None if the language is not supported
        
    Examples:
        >>> detect_language("app/api/user.py")
        'python'
        >>> detect_language("README.md")
        None
    """
    # Get the file extension (including the dot)
    _, extension = os.path.splitext(file_path)
    
    # Return the language if found, otherwise None
    return EXTENSION_TO_LANGUAGE.get(extension.lower())