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
    '.cpp': 'cpp',
    '.cc': 'cpp',
    '.cxx': 'cpp',
    '.h': 'cpp',
    '.hpp': 'cpp',
    '.go': 'go',
    '.rs': 'rust',
    '.kt': 'kotlin',
    '.kts': 'kotlin',
    '.swift': 'swift',
    '.php': 'php',
    '.rb': 'ruby',
    '.sh': 'bash',
    '.bash': 'bash',
    '.sql': 'sql',
    '.cs': 'csharp',
}


def detect_language(file_path: str, content: bytes | None = None) -> Optional[str]:
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
    language = EXTENSION_TO_LANGUAGE.get(extension.lower())
    if language:
        return language
    if content:
        first_line = content.splitlines()[0].decode("utf-8", errors="ignore") if content.splitlines() else ""
        if first_line.startswith("#!") and ("python" in first_line):
            return "python"
        if first_line.startswith("#!") and any(name in first_line for name in ("bash", "sh", "zsh")):
            return "bash"
    return None
