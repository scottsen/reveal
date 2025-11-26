"""Base adapter interface for URI resources."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ResourceAdapter(ABC):
    """Base class for all resource adapters."""

    @abstractmethod
    def get_structure(self, **kwargs) -> Dict[str, Any]:
        """Get the structure/overview of the resource.

        Returns:
            Dict containing structured representation of the resource
        """
        pass

    def get_element(self, element_name: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Get details about a specific element within the resource.

        Args:
            element_name: Name/identifier of the element to retrieve

        Returns:
            Dict containing element details, or None if not found
        """
        return None

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the resource.

        Returns:
            Dict containing metadata (type, size, etc.)
        """
        return {'type': self.__class__.__name__}
