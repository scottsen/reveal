"""Environment variable adapter (env://)."""

import os
from typing import Dict, List, Any, Optional
from .base import ResourceAdapter


class EnvAdapter(ResourceAdapter):
    """Adapter for exploring environment variables via env:// URIs."""

    SENSITIVE_PATTERNS = [
        'PASSWORD', 'SECRET', 'TOKEN', 'KEY', 'CREDENTIAL',
        'API_KEY', 'AUTH', 'PRIVATE', 'PASSPHRASE'
    ]

    SYSTEM_VARS = {
        'PATH', 'HOME', 'SHELL', 'USER', 'LANG', 'PWD',
        'LOGNAME', 'TERM', 'DISPLAY', 'EDITOR', 'PAGER'
    }

    def __init__(self):
        """Initialize the environment adapter."""
        self.variables = dict(os.environ)

    def get_structure(self, show_secrets: bool = False) -> Dict[str, Any]:
        """Get all environment variables, grouped by category.

        Args:
            show_secrets: If True, show actual values of sensitive variables

        Returns:
            Dict containing categorized environment variables
        """
        categorized = {
            'System': [],
            'Python': [],
            'Node': [],
            'Application': [],
            'Custom': []
        }

        for name, value in sorted(self.variables.items()):
            category = self._categorize(name)
            var_info = {
                'name': name,
                'value': self._maybe_redact(name, value, show_secrets),
                'sensitive': self._is_sensitive(name),
                'length': len(value)
            }
            categorized[category].append(var_info)

        # Remove empty categories
        categorized = {k: v for k, v in categorized.items() if v}

        return {
            'type': 'environment',
            'total_count': len(self.variables),
            'categories': categorized
        }

    def get_element(self, var_name: str, show_secrets: bool = False) -> Optional[Dict[str, Any]]:
        """Get details about a specific environment variable.

        Args:
            var_name: Name of the environment variable
            show_secrets: If True, show actual value even if sensitive

        Returns:
            Dict with variable details, or None if not found
        """
        if var_name not in self.variables:
            return None

        value = self.variables[var_name]
        return {
            'name': var_name,
            'value': self._maybe_redact(var_name, value, show_secrets),
            'category': self._categorize(var_name),
            'sensitive': self._is_sensitive(var_name),
            'length': len(value),
            'raw_value': value if show_secrets else None
        }

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the environment.

        Returns:
            Dict with environment metadata
        """
        sensitive_count = sum(1 for name in self.variables if self._is_sensitive(name))

        return {
            'type': 'environment',
            'total_variables': len(self.variables),
            'sensitive_variables': sensitive_count,
            'categories': self._get_category_counts()
        }

    def _is_sensitive(self, name: str) -> bool:
        """Check if variable name suggests sensitive data.

        Args:
            name: Variable name to check

        Returns:
            True if name matches sensitive patterns
        """
        upper_name = name.upper()
        return any(pattern in upper_name for pattern in self.SENSITIVE_PATTERNS)

    def _maybe_redact(self, name: str, value: str, show_secrets: bool) -> str:
        """Redact sensitive values unless show_secrets=True.

        Args:
            name: Variable name
            value: Variable value
            show_secrets: Whether to show actual value

        Returns:
            Original value or redacted string
        """
        if not show_secrets and self._is_sensitive(name):
            return '***'
        return value

    def _categorize(self, name: str) -> str:
        """Categorize variable by name pattern.

        Args:
            name: Variable name

        Returns:
            Category name
        """
        # System variables
        if name in self.SYSTEM_VARS:
            return 'System'

        # Python-related
        if name.startswith('PYTHON') or name.startswith('VIRTUAL') or name == 'PYTHONPATH':
            return 'Python'

        # Node/NPM-related
        if name.startswith('NODE') or name.startswith('NPM') or name.startswith('NVM'):
            return 'Node'

        # Application-specific (common patterns)
        if any(name.startswith(prefix) for prefix in ['APP_', 'DATABASE_', 'REDIS_', 'API_']):
            return 'Application'

        # Everything else
        return 'Custom'

    def _get_category_counts(self) -> Dict[str, int]:
        """Get count of variables per category.

        Returns:
            Dict mapping category to count
        """
        counts = {}
        for name in self.variables:
            category = self._categorize(name)
            counts[category] = counts.get(category, 0) + 1
        return counts
