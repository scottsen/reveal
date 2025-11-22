"""
SQL file analyzer - Reference implementation for Reveal plugins.

This analyzer demonstrates several important plugin patterns:

1. **Using External Libraries**: Integrates sqlglot for AST-based SQL parsing
2. **Error Handling**: Gracefully handles parse failures with fallback strategies
3. **Multi-dialect Support**: Detects and adapts to different SQL dialects
4. **Hybrid Approach**: Combines AST parsing with regex fallbacks for edge cases

This serves as a template for complex analyzers that need robust parsing.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from .base import BaseAnalyzer
from ..registry import register

# Optional dependency - gracefully handle if not installed
try:
    import sqlglot
    import sqlglot.expressions as exp
    SQLGLOT_AVAILABLE = True
except ImportError:
    SQLGLOT_AVAILABLE = False


@register(['.sql', '.ddl', '.dml'], name='SQL', icon='🗄️')
class SQLAnalyzer(BaseAnalyzer):
    """
    Analyzer for SQL files with AST-based parsing and regex fallbacks.

    Features:
    - Detects SQL dialect (PostgreSQL, MySQL, SQLite, etc.)
    - Extracts tables, columns, indexes, triggers, procedures
    - Handles complex SQL with graceful degradation
    - Falls back to regex when AST parsing fails
    """

    def __init__(self, lines: List[str], **kwargs):
        super().__init__(lines, **kwargs)
        self.content = '\n'.join(lines)
        self.dialect = self._detect_dialect()
        self.parse_error = None
        self.statements = []

        # Try to parse with sqlglot if available
        if SQLGLOT_AVAILABLE:
            try:
                # sqlglot.parse() returns a list of parsed statements
                self.statements = sqlglot.parse(
                    self.content,
                    read=self.dialect,
                    error_level=None  # Don't raise on errors, return None instead
                )
                # Filter out None values from failed parses
                self.statements = [s for s in self.statements if s is not None]
            except Exception as e:
                self.parse_error = f"sqlglot parse error: {str(e)}"
                # Will fall back to regex extraction

    def _detect_dialect(self) -> str:
        """
        Detect SQL dialect from syntax hints.

        Returns:
            str: Dialect name for sqlglot ('postgres', 'mysql', 'sqlite', etc.)
        """
        content_upper = self.content.upper()

        # PostgreSQL indicators
        if any(kw in content_upper for kw in ['TIMESTAMPTZ', 'SERIAL', '$$', 'JSONB']):
            return 'postgres'

        # MySQL indicators
        if any(kw in content_upper for kw in ['DELIMITER', 'AUTO_INCREMENT', 'TINYINT']):
            return 'mysql'

        # SQLite indicators
        if 'AUTOINCREMENT' in content_upper:
            return 'sqlite'

        # Default to PostgreSQL (most feature-rich)
        return 'postgres'

    def analyze_structure(self) -> Dict[str, Any]:
        """
        Extract SQL structure: tables, indexes, procedures, triggers.

        Strategy:
        1. Try AST-based extraction with sqlglot (clean, accurate)
        2. Fall back to regex for edge cases (DELIMITER, complex syntax)
        3. Fall back to basic stats if all else fails

        Returns:
            Dict with keys: dialect, tables, indexes, procedures, triggers, views
        """
        result = {
            'dialect': self.dialect.title(),
            'tables': [],
            'indexes': [],
            'procedures': [],
            'triggers': [],
            'views': [],
            'using_fallback': False
        }

        if self.parse_error:
            result['parse_error'] = self.parse_error

        # Strategy 1: AST-based extraction (preferred)
        if SQLGLOT_AVAILABLE and self.statements:
            self._extract_from_ast(result)

        # Strategy 2: Regex fallback for constructs sqlglot can't parse
        self._extract_from_regex_fallback(result)

        # Mark if we had to use fallback
        if not SQLGLOT_AVAILABLE or self.parse_error:
            result['using_fallback'] = True

        return result

    def _extract_from_ast(self, result: Dict[str, Any]) -> None:
        """
        Extract structure using sqlglot AST parsing.

        This is the preferred method - clean, type-safe, accurate.
        """
        for stmt in self.statements:
            if isinstance(stmt, exp.Create):
                self._handle_create_statement(stmt, result)
            elif isinstance(stmt, exp.Command):
                # Some complex SQL falls back to Command - use regex
                self._handle_command_fallback(stmt, result)

    def _handle_create_statement(self, stmt: exp.Create, result: Dict[str, Any]) -> None:
        """Handle CREATE TABLE/INDEX/VIEW statements from AST."""
        kind = stmt.args.get('kind')

        if kind == 'TABLE':
            table_info = self._extract_table_from_ast(stmt)
            if table_info:
                result['tables'].append(table_info)

        elif kind == 'INDEX':
            index_info = self._extract_index_from_ast(stmt)
            if index_info:
                result['indexes'].append(index_info)

        elif kind == 'VIEW':
            view_name = stmt.this.name if stmt.this else None
            if view_name:
                result['views'].append({'name': view_name})

    def _extract_table_from_ast(self, stmt: exp.Create) -> Optional[Dict[str, Any]]:
        """Extract table details from CREATE TABLE statement."""
        table_expr = stmt.this
        if not table_expr:
            return None

        # Get table name - handle both direct name and nested structure
        table_name = None
        if hasattr(table_expr, 'name'):
            table_name = table_expr.name
        if not table_name and hasattr(table_expr, 'this') and hasattr(table_expr.this, 'name'):
            table_name = table_expr.this.name
        if not table_name:
            # Fallback to string representation
            table_name = str(table_expr).split('(')[0].strip()

        columns = []

        # Extract column definitions
        for col_def in table_expr.find_all(exp.ColumnDef):
            col_name = col_def.this.name if col_def.this else "?"
            col_kind = col_def.args.get('kind')
            col_type = str(col_kind) if col_kind else "?"

            # Extract constraints (PRIMARY KEY, UNIQUE, etc.)
            constraints = []
            if 'constraints' in col_def.args:
                for constraint in col_def.args['constraints']:
                    if isinstance(constraint, exp.PrimaryKeyColumnConstraint):
                        constraints.append('PK')
                    elif isinstance(constraint, exp.UniqueColumnConstraint):
                        constraints.append('UNIQUE')
                    elif isinstance(constraint, exp.NotNullColumnConstraint):
                        constraints.append('NOT NULL')

            columns.append({
                'name': col_name,
                'type': col_type,
                'constraints': constraints
            })

        return {
            'name': table_name,
            'columns': columns[:10]  # Limit to first 10 for preview
        }

    def _extract_index_from_ast(self, stmt: exp.Create) -> Optional[Dict[str, Any]]:
        """Extract index details from CREATE INDEX statement."""
        index_expr = stmt.this
        if not index_expr:
            return None

        index_name = index_expr.name

        # Try to get table being indexed
        table = None
        if 'table' in stmt.args and stmt.args['table']:
            table = stmt.args['table'].name

        return {
            'name': index_name,
            'table': table
        }

    def _handle_command_fallback(self, stmt: exp.Command, result: Dict[str, Any]) -> None:
        """
        Handle SQL that sqlglot couldn't fully parse.

        This happens with:
        - DELIMITER statements (MySQL)
        - Complex stored procedures
        - Some trigger syntax variants

        We fall back to regex extraction here.
        """
        cmd = str(stmt)

        # Try to extract procedures
        if 'CREATE PROCEDURE' in cmd or 'CREATE OR REPLACE PROCEDURE' in cmd:
            proc = self._extract_procedure_regex(cmd)
            if proc:
                result['procedures'].append(proc)

        # Try to extract functions
        if 'CREATE FUNCTION' in cmd or 'CREATE OR REPLACE FUNCTION' in cmd:
            func = self._extract_function_regex(cmd)
            if func:
                result['procedures'].append(func)  # Group with procedures

        # Try to extract triggers
        if 'CREATE TRIGGER' in cmd:
            trigger = self._extract_trigger_regex(cmd)
            if trigger:
                result['triggers'].append(trigger)

    def _extract_from_regex_fallback(self, result: Dict[str, Any]) -> None:
        """
        Regex-based extraction for constructs that sqlglot missed.

        This catches:
        - Tables/indexes if AST parsing completely failed
        - Stored procedures with DELIMITER
        - Triggers with complex syntax
        """
        # Only use regex fallback if AST didn't find anything
        if not result['procedures']:
            for match in re.finditer(r'CREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE\s+(\w+)', self.content, re.IGNORECASE):
                result['procedures'].append({'name': match.group(1), 'type': 'procedure'})

        if not result['triggers']:
            for match in re.finditer(r'CREATE\s+(?:OR\s+REPLACE\s+)?TRIGGER\s+(\w+)', self.content, re.IGNORECASE):
                result['triggers'].append({'name': match.group(1)})

    def _extract_procedure_regex(self, cmd: str) -> Optional[Dict[str, Any]]:
        """Extract stored procedure metadata using regex."""
        match = re.search(r'CREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE\s+(\w+)\s*\((.*?)\)', cmd, re.IGNORECASE | re.DOTALL)
        if not match:
            return None

        proc_name = match.group(1)
        params_str = match.group(2).strip()

        # Parse parameters (IN/OUT/INOUT p_name TYPE)
        params = []
        if params_str:
            for param in params_str.split(',')[:5]:  # First 5 params
                param = param.strip()
                if param:
                    parts = param.split()
                    if len(parts) >= 2:
                        param_name = parts[1] if parts[0].upper() in ('IN', 'OUT', 'INOUT') else parts[0]
                        params.append(param_name)

        return {
            'name': proc_name,
            'type': 'procedure',
            'params': params
        }

    def _extract_function_regex(self, cmd: str) -> Optional[Dict[str, Any]]:
        """Extract function metadata using regex."""
        match = re.search(r'CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(\w+)\s*\(.*?\)\s+RETURNS\s+(\w+)',
                         cmd, re.IGNORECASE | re.DOTALL)
        if not match:
            return None

        return {
            'name': match.group(1),
            'type': 'function',
            'returns': match.group(2)
        }

    def _extract_trigger_regex(self, cmd: str) -> Optional[Dict[str, Any]]:
        """Extract trigger metadata using regex."""
        match = re.search(r'CREATE\s+(?:OR\s+REPLACE\s+)?TRIGGER\s+(\w+)\s+(BEFORE|AFTER)\s+(INSERT|UPDATE|DELETE)',
                         cmd, re.IGNORECASE)
        if not match:
            return None

        trig_name = match.group(1)
        timing = match.group(2).upper()
        event = match.group(3).upper()

        # Try to get target table
        table_match = re.search(r'ON\s+(\w+)\s+FOR', cmd, re.IGNORECASE)
        table = table_match.group(1) if table_match else None

        return {
            'name': trig_name,
            'event': f"{timing} {event}",
            'table': table
        }

    def _find_sql_definition(self, pattern: str, name_only: str = None) -> Optional[int]:
        """
        Find line number where SQL pattern appears.

        Helper for locating CREATE statements with fallback logic.
        """
        # Try exact pattern first
        line_num = self.find_definition(pattern, case_sensitive=False)
        if line_num:
            return line_num

        # Fall back to just the name (handles "IF NOT EXISTS table_name")
        if name_only:
            for i, line in enumerate(self.lines, 1):
                line_upper = line.upper()
                if name_only.upper() in line_upper and 'CREATE' in line_upper:
                    return i
        return None

    def _format_tables(self, tables: List[Dict[str, Any]]) -> List[str]:
        """Format tables section with line numbers."""
        lines = []
        lines.append(f"Tables ({len(tables)}):")
        for table in tables[:10]:
            table_name = table.get('name', '?')
            col_count = len(table.get('columns', []))
            line_num = self._find_sql_definition(f"CREATE TABLE {table_name}", name_only=table_name)
            line_ref = self.format_location(line_num)
            lines.append(f"  {line_ref:30}  └─ {table_name} ({col_count} columns)")

            # Show first few columns
            for col in table.get('columns', [])[:3]:
                col_name = col.get('name', '?')
                col_type = col.get('type', '?')
                constraints = col.get('constraints', [])
                constraint_str = f" [{', '.join(constraints)}]" if constraints else ""
                lines.append(f"{'':32}  • {col_name}: {col_type}{constraint_str}")
            if len(table.get('columns', [])) > 3:
                lines.append(f"{'':32}  ... and {len(table.get('columns', [])) - 3} more")
        if len(tables) > 10:
            lines.append(f"  ... and {len(tables) - 10} more tables")
        lines.append("")
        return lines

    def _format_indexes(self, indexes: List[Dict[str, Any]]) -> List[str]:
        """Format indexes section with line numbers."""
        lines = []
        lines.append(f"Indexes ({len(indexes)}):")
        for idx in indexes[:10]:
            idx_name = idx.get('name', '?')
            idx_table = idx.get('table', '')
            line_num = self._find_sql_definition(f"CREATE INDEX {idx_name}", name_only=idx_name)
            line_ref = self.format_location(line_num)
            table_str = f" → {idx_table}" if idx_table else ""
            lines.append(f"  {line_ref:30}  • {idx_name}{table_str}")
        if len(indexes) > 10:
            lines.append(f"  ... and {len(indexes) - 10} more")
        lines.append("")
        return lines

    def _format_procedures(self, procedures: List[Dict[str, Any]]) -> List[str]:
        """Format procedures/functions section with line numbers."""
        lines = []
        lines.append(f"Procedures/Functions ({len(procedures)}):")
        for proc in procedures[:10]:
            proc_name = proc.get('name', '?')
            proc_type = proc.get('type', 'procedure')
            params = proc.get('params', [])
            param_str = f"({', '.join(params[:3])})" if params else "()"
            returns = proc.get('returns', '')
            return_str = f" → {returns}" if returns else ""

            search_term = f"CREATE {proc_type.upper()} {proc_name}"
            line_num = self._find_sql_definition(search_term)
            line_ref = self.format_location(line_num)
            lines.append(f"  {line_ref:30}  • {proc_name}{param_str}{return_str}")
        if len(procedures) > 10:
            lines.append(f"  ... and {len(procedures) - 10} more")
        lines.append("")
        return lines

    def _format_triggers(self, triggers: List[Dict[str, Any]]) -> List[str]:
        """Format triggers section with line numbers."""
        lines = []
        lines.append(f"Triggers ({len(triggers)}):")
        for trig in triggers[:10]:
            trig_name = trig.get('name', '?')
            trig_event = trig.get('event', '')
            trig_table = trig.get('table', '')
            line_num = self._find_sql_definition(f"CREATE TRIGGER {trig_name}")
            line_ref = self.format_location(line_num)
            event_str = f" ({trig_event}" + (f" on {trig_table})" if trig_table else ")")
            lines.append(f"  {line_ref:30}  • {trig_name}{event_str if trig_event else ''}")
        if len(triggers) > 10:
            lines.append(f"  ... and {len(triggers) - 10} more")
        lines.append("")
        return lines

    def _format_views(self, views: List[Dict[str, Any]]) -> List[str]:
        """Format views section with line numbers."""
        lines = []
        lines.append(f"Views ({len(views)}):")
        for view in views[:10]:
            view_name = view.get('name', '?')
            line_num = self._find_sql_definition(f"CREATE VIEW {view_name}")
            line_ref = self.format_location(line_num)
            lines.append(f"  {line_ref:30}  • {view_name}")
        if len(views) > 10:
            lines.append(f"  ... and {len(views) - 10} more")
        lines.append("")
        return lines

    def _format_breadcrumbs(self) -> List[str]:
        """Format breadcrumb hints for next steps."""
        lines = []
        if self.file_path:
            lines.append("→ Next: Use line numbers to jump to definitions with any tool")
            lines.append(f"  Example: vim {self.file_path}:32")
            lines.append(f"  Or grep: reveal {self.file_path} --level 2 | grep -A 10 'schema.sql:32'")
        else:
            lines.append("→ Next: Use line numbers with --level 2 or --level 3 to see definitions")
            lines.append("  Example: reveal file.sql --level 2 | grep -A 10 'L0032'")
        lines.append("  Tip: --grep CREATE (filter), --level 0 (file metadata)")
        return lines

    def format_structure(self, structure: Dict[str, Any]) -> Optional[List[str]]:
        """
        Custom formatter for SQL structure output with source line numbers.

        Clean separation: delegates to focused helper methods.
        """
        lines = []

        # Dialect info
        dialect = structure.get('dialect', 'SQL')
        lines.append(f"Dialect:         {dialect}")
        lines.append("")

        # Delegate to focused helper methods
        if structure.get('tables'):
            lines.extend(self._format_tables(structure['tables']))

        if structure.get('indexes'):
            lines.extend(self._format_indexes(structure['indexes']))

        if structure.get('procedures'):
            lines.extend(self._format_procedures(structure['procedures']))

        if structure.get('triggers'):
            lines.extend(self._format_triggers(structure['triggers']))

        if structure.get('views'):
            lines.extend(self._format_views(structure['views']))

        # Breadcrumbs
        lines.extend(self._format_breadcrumbs())

        return lines

    def generate_preview(self) -> List[Tuple[int, str]]:
        """
        Generate SQL preview showing key structural elements.

        Returns:
            List of (line_number, line_text) tuples
        """
        preview = []

        # Show CREATE statements and comments
        in_comment_block = False
        for i, line in enumerate(self.lines, 1):
            line_upper = line.strip().upper()

            # Multi-line comments
            if '/*' in line:
                in_comment_block = True
            if in_comment_block:
                preview.append((i, line))
                if '*/' in line:
                    in_comment_block = False
                continue

            # Single-line comments at file start
            if line.strip().startswith('--') and i < 20:
                preview.append((i, line))

            # CREATE statements
            if any(kw in line_upper for kw in ['CREATE TABLE', 'CREATE INDEX', 'CREATE PROCEDURE',
                                                 'CREATE FUNCTION', 'CREATE TRIGGER', 'CREATE VIEW']):
                preview.append((i, line))
                # Add next few lines for context
                for j in range(i + 1, min(i + 5, len(self.lines) + 1)):
                    preview.append((j, self.lines[j - 1]))

            # Primary keys, indexes
            if any(kw in line_upper for kw in ['PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE']):
                preview.append((i, line))

        # Limit and deduplicate
        preview = sorted(list(set(preview)), key=lambda x: x[0])
        return preview[:50]
