"""TOML file analyzer."""

import re
from typing import Dict, Any, List
from .base import BaseAnalyzer
from ..registry import register

try:
    import tomli
    HAS_TOMLI = True
except ImportError:
    try:
        import tomllib
        tomli = tomllib
        HAS_TOMLI = True
    except ImportError:
        HAS_TOMLI = False


@register(['.toml'], name='TOML', icon='⚙️')
class TOMLAnalyzer(BaseAnalyzer):
    """Analyzer for TOML configuration files"""

    def __init__(self, lines: List[str], **kwargs):
        super().__init__(lines, **kwargs)
        self.parse_error = None
        self.parsed_data = None

        if HAS_TOMLI:
            try:
                content = '\n'.join(lines)
                self.parsed_data = tomli.loads(content)
            except Exception as e:
                self.parse_error = str(e)

    def analyze_structure(self) -> Dict[str, Any]:
        """Analyze TOML structure."""
        if self.parse_error:
            return {
                'error': self.parse_error,
                'top_level_keys': [],
                'sections': [],
                'nesting_depth': 0
            }

        if not HAS_TOMLI:
            return {
                'error': 'tomli not installed. Install with: pip install tomli',
                'top_level_keys': [],
                'sections': [],
                'nesting_depth': 0
            }

        # Get top-level keys with line numbers
        top_level_keys = []
        sections = []

        if isinstance(self.parsed_data, dict):
            for key in self.parsed_data.keys():
                value = self.parsed_data[key]

                if isinstance(value, dict):
                    # This is a section [key]
                    line_num = self.find_definition(f'[{key}]', case_sensitive=True)
                    if line_num is None:
                        # Try without brackets (dotted key)
                        line_num = self.find_definition(f'{key}.', case_sensitive=True)
                    if line_num is None:
                        # Fallback: just the key
                        line_num = self.find_definition(key, case_sensitive=True)

                    sections.append({
                        'name': key,
                        'line': line_num if line_num is not None else 1,
                        'subsections': self._count_subsections(value)
                    })
                else:
                    # This is a top-level key = value
                    line_num = self.find_definition(f'{key} =', case_sensitive=True)
                    if line_num is None:
                        # Try with different spacing
                        line_num = self.find_definition(f'{key}=', case_sensitive=True)
                    if line_num is None:
                        # Fallback: just the key
                        line_num = self.find_definition(key, case_sensitive=True)

                    top_level_keys.append({
                        'name': key,
                        'line': line_num if line_num is not None else 1
                    })

        # Calculate nesting depth
        nesting_depth = self._calculate_depth(self.parsed_data)

        return {
            'top_level_keys': top_level_keys,
            'sections': sections,
            'nesting_depth': nesting_depth
        }

    def _count_subsections(self, obj: Any) -> int:
        """Count nested sections in a table."""
        count = 0
        if isinstance(obj, dict):
            for value in obj.values():
                if isinstance(value, dict):
                    count += 1
        return count

    def _calculate_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth."""
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(self._calculate_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(self._calculate_depth(item, current_depth + 1) for item in obj)
        else:
            return current_depth

    def generate_preview(self) -> List[tuple[int, str]]:
        """Generate TOML preview (first 20 lines)."""
        preview = []

        if self.parse_error or not HAS_TOMLI:
            # Fallback to first 20 lines
            for i, line in enumerate(self.lines[:20], 1):
                preview.append((i, line))
            return preview

        # Show first 20 lines
        for i, line in enumerate(self.lines[:20], 1):
            preview.append((i, line))

        return preview
