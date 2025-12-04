"""Type system for reveal analyzers.

Provides optional type declarations and relationship tracking for analyzers.
Maintains backward compatibility - existing analyzers work unchanged.

Usage:
    from reveal.types import Entity, relationship

    types = {
        'function': Entity(
            properties={'name': str, 'line': int, 'signature': str},
            searchable=['name'],
            contains=['variable']
        ),
        'method': Entity(
            inherits='function',
            properties={'parent_class': str, 'decorators': list}
        )
    }

    relationships = {
        'calls': relationship(
            from_types=['function', 'method'],
            to_types=['function', 'method'],
            bidirectional=True
        )
    }
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Union, get_origin, get_args
import logging

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Declare an entity type for semantic code elements.

    An entity represents a semantic element in code (function, class, variable, etc.)
    with properties, relationships, and searchability.

    Args:
        properties: Dict mapping property names to types (e.g., {'name': str, 'line': int})
        inherits: Name of parent entity type (for type inheritance)
        contains: List of entity types this entity can contain
        searchable: List of property names to index for search (defaults to all)
        description: Human-readable description of this entity type

    Examples:
        # Basic entity
        function = Entity(
            properties={'name': str, 'line': int},
            searchable=['name']
        )

        # Entity with inheritance
        method = Entity(
            inherits='function',
            properties={'parent_class': str}
        )

        # Entity with containment
        class_def = Entity(
            properties={'name': str},
            contains=['method', 'attribute']
        )
    """

    properties: Dict[str, type]
    inherits: Optional[str] = None
    contains: List[str] = field(default_factory=list)
    searchable: List[str] = field(default_factory=list)
    description: str = ""

    def __post_init__(self):
        """Validate and set defaults."""
        # Default searchable to all properties if not specified
        if not self.searchable:
            self.searchable = list(self.properties.keys())

        # Validate properties are types
        for prop_name, prop_type in self.properties.items():
            if not self._is_valid_type(prop_type):
                logger.warning(
                    f"Property '{prop_name}' has invalid type annotation: {prop_type}"
                )

    @staticmethod
    def _is_valid_type(typ: Any) -> bool:
        """Check if a type annotation is valid.

        Accepts:
        - Built-in types (str, int, bool, float, list, dict, etc.)
        - Union types (str | None, int | str)
        - Generic types (list[str], dict[str, int])
        - Optional types (Optional[str])
        """
        # Handle None
        if typ is type(None):
            return True

        # Handle Union types (including | syntax and Optional)
        origin = get_origin(typ)
        if origin is Union:
            return all(Entity._is_valid_type(arg) for arg in get_args(typ))

        # Handle generic types (list[str], dict[str, int])
        if origin is not None:
            return True

        # Handle built-in types
        if isinstance(typ, type):
            return True

        return False


@dataclass
class RelationshipDef:
    """Definition of a relationship between entity types.

    Relationships connect entities (e.g., function calls function, class inherits class).
    Can be bidirectional (auto-generates reverse) and transitive (follows chains).

    Args:
        from_types: List of source entity types
        to_types: List of target entity types
        bidirectional: If True, auto-create reverse relationship
        reverse_name: Name of reverse relationship (default: adds '_by' suffix)
        transitive: If True, follow relationship chains (A→B→C means A→C)
        properties: Additional properties stored on relationship edges

    Examples:
        # Function calls
        calls = RelationshipDef(
            from_types=['function', 'method'],
            to_types=['function', 'method'],
            bidirectional=True,  # Creates 'called_by' automatically
            reverse_name='called_by'
        )

        # Class inheritance (transitive)
        inherits_from = RelationshipDef(
            from_types=['class'],
            to_types=['class'],
            transitive=True  # Follow inheritance chain
        )

        # Import with metadata
        imports_from = RelationshipDef(
            from_types=['module'],
            to_types=['module'],
            properties={'symbols': list}
        )
    """

    from_types: List[str]
    to_types: List[str]
    bidirectional: bool = False
    reverse_name: Optional[str] = None
    transitive: bool = False
    properties: Dict[str, type] = field(default_factory=dict)

    def __post_init__(self):
        """Set defaults for reverse relationship name."""
        if self.bidirectional and not self.reverse_name:
            # Auto-generate reverse name by adding '_by' suffix
            # This will be set by the relationship registry with context
            pass


def relationship(
    from_types: List[str],
    to_types: List[str],
    bidirectional: bool = False,
    reverse_name: Optional[str] = None,
    transitive: bool = False,
    properties: Optional[Dict[str, type]] = None,
) -> RelationshipDef:
    """Define a relationship between entity types.

    Convenience function for creating RelationshipDef instances.

    Args:
        from_types: Source entity types
        to_types: Target entity types
        bidirectional: Auto-create reverse relationship
        reverse_name: Name of reverse (default: adds '_by' suffix)
        transitive: Follow chain (A→B→C means A→C)
        properties: Extra data on relationship edges

    Returns:
        RelationshipDef instance

    Examples:
        # Simple relationship
        calls = relationship(['function'], ['function'])

        # Bidirectional with custom reverse name
        calls = relationship(
            ['function'], ['function'],
            bidirectional=True,
            reverse_name='called_by'
        )

        # Transitive relationship
        inherits = relationship(
            ['class'], ['class'],
            transitive=True
        )
    """
    return RelationshipDef(
        from_types=from_types,
        to_types=to_types,
        bidirectional=bidirectional,
        reverse_name=reverse_name,
        transitive=transitive,
        properties=properties or {},
    )


class TypeRegistry:
    """Registry for entity types and inheritance resolution.

    Handles:
    - Type registration and validation
    - Inheritance resolution (merging parent properties)
    - Type hierarchy queries
    - Property validation

    Usage:
        registry = TypeRegistry()
        registry.register_types(analyzer.types)
        registry.resolve_inheritance()
    """

    def __init__(self):
        self.types: Dict[str, Entity] = {}
        self._inheritance_resolved = False

    def register_types(self, types: Dict[str, Entity]) -> None:
        """Register entity types.

        Args:
            types: Dict mapping type names to Entity definitions
        """
        self.types.update(types)
        self._inheritance_resolved = False

    def resolve_inheritance(self) -> None:
        """Resolve type inheritance by merging parent properties.

        After resolution, child types have all parent properties plus their own.
        Handles multi-level inheritance chains.
        """
        if self._inheritance_resolved:
            return

        # Build dependency graph to handle multi-level inheritance
        resolved = set()
        in_progress = set()

        def resolve_type(type_name: str) -> None:
            """Recursively resolve a type's inheritance."""
            if type_name in resolved:
                return

            if type_name in in_progress:
                raise ValueError(f"Circular inheritance detected: {type_name}")

            entity = self.types.get(type_name)
            if not entity or not entity.inherits:
                resolved.add(type_name)
                return

            # Resolve parent first
            in_progress.add(type_name)
            parent_name = entity.inherits

            if parent_name not in self.types:
                logger.warning(
                    f"Type '{type_name}' inherits from unknown type '{parent_name}'"
                )
                resolved.add(type_name)
                in_progress.remove(type_name)
                return

            resolve_type(parent_name)
            parent = self.types[parent_name]

            # Merge parent properties (child properties override parent)
            merged_properties = {**parent.properties, **entity.properties}
            entity.properties = merged_properties

            # Merge contains lists (child adds to parent)
            merged_contains = list(parent.contains) + [
                c for c in entity.contains if c not in parent.contains
            ]
            entity.contains = merged_contains

            # Merge searchable lists (child adds to parent)
            merged_searchable = list(parent.searchable) + [
                s for s in entity.searchable if s not in parent.searchable
            ]
            entity.searchable = merged_searchable

            resolved.add(type_name)
            in_progress.remove(type_name)

        # Resolve all types
        for type_name in list(self.types.keys()):
            resolve_type(type_name)

        self._inheritance_resolved = True

    def get_type(self, type_name: str) -> Optional[Entity]:
        """Get entity type by name.

        Args:
            type_name: Name of the type

        Returns:
            Entity definition or None if not found
        """
        return self.types.get(type_name)

    def get_subtypes(self, type_name: str) -> List[str]:
        """Get all subtypes of a type (types that inherit from it).

        Args:
            type_name: Parent type name

        Returns:
            List of subtype names
        """
        subtypes = []
        for name, entity in self.types.items():
            if entity.inherits == type_name:
                subtypes.append(name)
                # Recursively get subtypes of subtypes
                subtypes.extend(self.get_subtypes(name))
        return subtypes

    def is_subtype_of(self, child: str, parent: str) -> bool:
        """Check if child type inherits from parent type.

        Args:
            child: Child type name
            parent: Parent type name

        Returns:
            True if child inherits from parent (directly or transitively)
        """
        if child == parent:
            return True

        entity = self.types.get(child)
        if not entity or not entity.inherits:
            return False

        if entity.inherits == parent:
            return True

        # Check parent's parent
        return self.is_subtype_of(entity.inherits, parent)

    def validate_entity(self, type_name: str, entity_data: Dict[str, Any]) -> List[str]:
        """Validate an entity instance against its type definition.

        Args:
            type_name: Name of the entity type
            entity_data: Entity data dict to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        entity_def = self.types.get(type_name)
        if not entity_def:
            errors.append(f"Unknown entity type: {type_name}")
            return errors

        # Check required properties
        for prop_name, prop_type in entity_def.properties.items():
            if prop_name not in entity_data:
                # Property is missing - this might be OK if it's optional (None union)
                origin = get_origin(prop_type)
                if origin is Union and type(None) in get_args(prop_type):
                    continue  # Optional property
                # For now, we'll be lenient and just warn
                logger.debug(f"Entity '{type_name}' missing property '{prop_name}'")
                continue

            # Type check (basic validation)
            value = entity_data[prop_name]
            if value is not None:
                expected_type = prop_type
                origin = get_origin(expected_type)

                # Handle Union types (str | None)
                if origin is Union:
                    args = get_args(expected_type)
                    valid = any(self._check_type(value, arg) for arg in args if arg is not type(None))
                    if not valid and value is not None:
                        errors.append(
                            f"Property '{prop_name}' has invalid type: expected {expected_type}, got {type(value)}"
                        )
                # Handle other types
                elif not self._check_type(value, expected_type):
                    errors.append(
                        f"Property '{prop_name}' has invalid type: expected {expected_type}, got {type(value)}"
                    )

        return errors

    @staticmethod
    def _check_type(value: Any, expected_type: type) -> bool:
        """Check if value matches expected type."""
        origin = get_origin(expected_type)

        # Handle generic types (list, dict, etc.)
        if origin is not None:
            if origin is list:
                return isinstance(value, list)
            elif origin is dict:
                return isinstance(value, dict)
            # Add more generic type checks as needed
            return True

        # Handle basic types
        return isinstance(value, expected_type)


class RelationshipRegistry:
    """Registry for relationship definitions and indexing.

    Handles:
    - Relationship registration
    - Bidirectional relationship generation
    - Relationship validation
    - Relationship indexing for fast queries

    Usage:
        registry = RelationshipRegistry(type_registry)
        registry.register_relationships(analyzer.relationships)
        edges = registry.build_index(relationship_data)
    """

    def __init__(self, type_registry: TypeRegistry):
        self.type_registry = type_registry
        self.relationships: Dict[str, RelationshipDef] = {}

    def register_relationships(self, relationships: Dict[str, RelationshipDef]) -> None:
        """Register relationship definitions.

        Args:
            relationships: Dict mapping relationship names to RelationshipDef
        """
        for name, rel_def in relationships.items():
            # Set reverse name if bidirectional and not specified
            if rel_def.bidirectional and not rel_def.reverse_name:
                rel_def.reverse_name = f"{name}_by"

            self.relationships[name] = rel_def

    def validate_relationship(
        self, rel_name: str, edge: Dict[str, Any]
    ) -> List[str]:
        """Validate a relationship edge.

        Args:
            rel_name: Relationship name
            edge: Edge data dict with 'from' and 'to' keys

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        rel_def = self.relationships.get(rel_name)
        if not rel_def:
            errors.append(f"Unknown relationship: {rel_name}")
            return errors

        # Check edge has required keys
        if 'from' not in edge:
            errors.append(f"Relationship edge missing 'from' key")
        if 'to' not in edge:
            errors.append(f"Relationship edge missing 'to' key")

        if errors:
            return errors

        # Validate from type
        from_entity = edge['from']
        from_type = from_entity.get('type') if isinstance(from_entity, dict) else None
        if from_type and from_type not in rel_def.from_types:
            # Check if it's a subtype
            valid = any(
                self.type_registry.is_subtype_of(from_type, allowed)
                for allowed in rel_def.from_types
            )
            if not valid:
                errors.append(
                    f"Invalid 'from' type '{from_type}' for relationship '{rel_name}'. "
                    f"Expected one of: {rel_def.from_types}"
                )

        # Validate to type
        to_entity = edge['to']
        to_type = to_entity.get('type') if isinstance(to_entity, dict) else None
        if to_type and to_type not in rel_def.to_types:
            # Check if it's a subtype
            valid = any(
                self.type_registry.is_subtype_of(to_type, allowed)
                for allowed in rel_def.to_types
            )
            if not valid:
                errors.append(
                    f"Invalid 'to' type '{to_type}' for relationship '{rel_name}'. "
                    f"Expected one of: {rel_def.to_types}"
                )

        return errors

    def build_index(
        self, relationship_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Build relationship index with bidirectional edges.

        Args:
            relationship_data: Dict mapping relationship names to edge lists

        Returns:
            Enhanced relationship data with bidirectional edges added
        """
        enhanced = dict(relationship_data)

        for rel_name, edges in relationship_data.items():
            rel_def = self.relationships.get(rel_name)
            if not rel_def or not rel_def.bidirectional:
                continue

            # Generate reverse edges
            reverse_name = rel_def.reverse_name
            reverse_edges = []

            for edge in edges:
                reverse_edge = {
                    'from': edge['to'],
                    'to': edge['from'],
                }

                # Copy over additional properties
                for key, value in edge.items():
                    if key not in ('from', 'to'):
                        reverse_edge[key] = value

                reverse_edges.append(reverse_edge)

            # Add or extend reverse relationship
            if reverse_name in enhanced:
                enhanced[reverse_name].extend(reverse_edges)
            else:
                enhanced[reverse_name] = reverse_edges

        return enhanced

    def traverse_transitive(
        self, rel_name: str, start_entity: Dict[str, Any],
        relationship_data: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Traverse a transitive relationship to find all reachable entities.

        Args:
            rel_name: Relationship name
            start_entity: Starting entity
            relationship_data: Relationship edge data

        Returns:
            List of all entities reachable via this relationship
        """
        rel_def = self.relationships.get(rel_name)
        if not rel_def or not rel_def.transitive:
            return []

        edges = relationship_data.get(rel_name, [])
        visited = set()
        reachable = []

        def traverse(entity: Dict[str, Any]) -> None:
            entity_id = (entity.get('type'), entity.get('name'))
            if entity_id in visited:
                return

            visited.add(entity_id)

            # Find edges from this entity
            for edge in edges:
                if self._entities_match(edge['from'], entity):
                    to_entity = edge['to']
                    reachable.append(to_entity)
                    traverse(to_entity)

        traverse(start_entity)
        return reachable

    @staticmethod
    def _entities_match(entity1: Dict[str, Any], entity2: Dict[str, Any]) -> bool:
        """Check if two entity references match."""
        return (
            entity1.get('type') == entity2.get('type') and
            entity1.get('name') == entity2.get('name')
        )
