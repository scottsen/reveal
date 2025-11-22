"""Base analyzer interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseAnalyzer(ABC):
    """Base class for file type analyzers."""

    def __init__(self, lines: List[str], file_path: Optional[str] = None,
                 focus_start: Optional[int] = None, focus_end: Optional[int] = None,
                 **kwargs):
        """
        Initialize analyzer with file lines.

        Args:
            lines: List of file lines
            file_path: Path to source file (for composable output)
            focus_start: Optional start line for focused analysis
            focus_end: Optional end line for focused analysis
            **kwargs: Additional arguments for plugin-specific features
        """
        self.lines = lines
        self.file_path = file_path
        self.focus_start = focus_start
        self.focus_end = focus_end

    @abstractmethod
    def analyze_structure(self) -> Dict[str, Any]:
        """
        Analyze file structure for Level 1.

        Returns:
            Dictionary with structural information
        """
        pass

    @abstractmethod
    def generate_preview(self) -> List[tuple[int, str]]:
        """
        Generate preview for Level 2.

        Returns:
            List of (line_number, content) tuples
        """
        pass

    def format_structure(self, structure: Dict[str, Any]) -> Optional[List[str]]:
        """
        Format structure output for Level 1 display (optional override).

        Plugins can override this to provide custom formatting without
        modifying core reveal code. If not overridden, reveal uses
        generic formatting based on the structure dictionary.

        Args:
            structure: The dict returned from analyze_structure()

        Returns:
            List of formatted output lines, or None to use default formatting
        """
        return None  # Default: use generic formatter

    # Line number helpers for tool composability

    def format_location(self, line_num: Optional[int]) -> str:
        """
        Format a line reference in a composable way.

        Returns filename:line for tool integration (vim, grep, git, etc.)
        or L0000 format if no file_path available.

        Args:
            line_num: Line number to format (1-indexed)

        Returns:
            Formatted location string (e.g., "schema.sql:32" or "L0032")
        """
        if line_num is None:
            return ""
        if self.file_path:
            return f"{self.file_path}:{line_num}"
        return f"L{line_num:04d}"

    def with_location(self, text: str, line_num: Optional[int], width: int = 30) -> str:
        """
        Prepend location reference to text for aligned output.

        Args:
            text: Text to annotate
            line_num: Line number (1-indexed)
            width: Column width for location (default: 30)

        Returns:
            Formatted string with location prefix
        """
        loc = self.format_location(line_num)
        if loc:
            return f"{loc:<{width}}  {text}"
        return text

    def find_definition(self, identifier: str, start_line: int = 1,
                       case_sensitive: bool = True) -> Optional[int]:
        """
        Find the line number where an identifier is defined.

        Searches from start_line through the file for the identifier.
        Useful for automatically annotating structure with line numbers.

        Args:
            identifier: Text to search for (e.g., table name, function name)
            start_line: Line to start searching from (1-indexed)
            case_sensitive: Whether to match case (default: True)

        Returns:
            Line number (1-indexed) where identifier found, or None
        """
        search_text = identifier if case_sensitive else identifier.lower()
        for i, line in enumerate(self.lines[start_line - 1:], start_line):
            compare_line = line if case_sensitive else line.lower()
            if search_text in compare_line:
                return i
        return None

    def in_focus_range(self, line_num: int) -> bool:
        """
        Check if a line number is within the focus range.

        Useful when user requests specific line range (e.g., reveal file.sql:10-50)

        Args:
            line_num: Line number to check (1-indexed)

        Returns:
            True if in focus range or no focus set, False otherwise
        """
        if self.focus_start is None and self.focus_end is None:
            return True
        if self.focus_start and line_num < self.focus_start:
            return False
        if self.focus_end and line_num > self.focus_end:
            return False
        return True
