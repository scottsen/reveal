# Reveal Sloppy Detectors: Pluggable Architecture Design

**Version:** 2.1 (TIA-Aligned)
**Date:** 2025-11-30
**Status:** ⚠️ SUPERSEDED - See Pattern Detection System (v0.13.0+)
**Author:** TIA + Claude (fageyipu-1130)
**Pattern:** Mirrors TIA's proven AST scanner architecture

---

## ⚠️ NOTICE: This Design Has Been Implemented

This document proposed a pluggable detector system. **That system is now live as of v0.13.0!**

**Current Implementation:**
- **Command:** `reveal --check` (replaces `--sloppy`)
- **Location:** `reveal/rules/` (category-based organization)
- **Format:** Industry-aligned rule codes (B001, S701, C901, etc.)
- **Docs:** See README.md "Pattern Detection" section

**This document is preserved for historical reference.**

---

## Executive Summary (Original Proposal)

Extend reveal's `--sloppy` feature from simple heuristics to a **pluggable detector system** using TIA's proven scanner pattern:

- **Auto-discovered detectors** - drop `*_detector.py` file, it works
- **Minimal interface** - ONE method: `detect_issues()`
- **File-type targeting** - Python, Dockerfile, Nginx, SQL, etc.
- **Category-based filtering** - `--sloppy=security`, `--sloppy=complexity`
- **Battle-tested pattern** - Same as TIA's 18+ AST scanners

**Use Case:** Instead of just showing "this function is long," reveal shows "bare except on line 45, prints to stdout on line 67, takes 8 parameters" - actionable, specific, context-aware.

---

## Design Philosophy: Copy What Works

**TIA's AST scanners have proven:**
- Auto-discovery by file naming convention (`*_scanner.py`)
- Single-method interface (`scan_file()`)
- Dataclass-based results (`ScanResult`)
- Zero manual registration

**Reveal will mirror this exactly:**
- Auto-discovery by file naming (`*_detector.py`)
- Single-method interface (`detect_issues()`)
- Dataclass-based results (`SloppyIssue`)
- Zero manual registration

**Why?** This pattern is proven to work across 18+ TIA scanners. Don't reinvent - replicate.

---

## Architecture Overview

### Plugin Discovery Flow

```
1. Reveal starts
   ↓
2. Scan detector directories:
   - Built-in:  reveal/detectors/*_detector.py
   - User:      ~/.reveal/detectors/*_detector.py
   - Project:   .reveal/detectors/*_detector.py
   ↓
3. Auto-register all BaseDetector subclasses
   ↓
4. User runs: reveal app.py --sloppy=error-handling
   ↓
5. Reveal calls matching detectors
   ↓
6. Detectors analyze and return SloppyIssue list
   ↓
7. Reveal enriches output with issue markers
```

### Component Structure

```
reveal/
├── detectors/                  # Built-in detector plugins
│   ├── __init__.py             # Auto-discovery (TIA pattern)
│   ├── base.py                 # BaseDetector (minimal interface)
│   ├── complexity_detector.py  # Universal (all file types)
│   ├── python_bare_except_detector.py
│   ├── python_unused_imports_detector.py
│   ├── dockerfile_security_detector.py
│   └── nginx_security_detector.py
│
├── base.py                     # FileAnalyzer (adds .get_sloppy_issues())
├── main.py                     # CLI (adds --sloppy flags)
└── __init__.py

~/.reveal/detectors/            # User-defined detectors
.reveal/detectors/              # Project-specific detectors
```

---

## Detector API Design

### BaseDetector Interface

```python
# reveal/detectors/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

class Severity(Enum):
    """Issue severity levels (TIA-compatible)."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Category(Enum):
    """Issue categories for filtering."""
    COMPLEXITY = "complexity"
    ERROR_HANDLING = "error-handling"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    STYLE = "style"

@dataclass
class SloppyIssue:
    """
    Standardized issue format (mirrors TIA's ScanResult).

    All detectors return this format for perfect composability.
    """
    file_path: str
    line: int
    severity: Severity
    category: Category
    issue_type: str           # e.g., "bare_except", "latest_tag"
    message: str              # Human-readable description
    suggestion: str = None    # Fix recommendation
    element_name: str = None  # Function/class name
    code_snippet: str = None  # Problematic code

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for JSON output."""
        return {
            'file_path': self.file_path,
            'line': self.line,
            'severity': self.severity.value,
            'category': self.category.value,
            'issue_type': self.issue_type,
            'message': self.message,
            'suggestion': self.suggestion,
            'element_name': self.element_name,
            'code_snippet': self.code_snippet,
        }


class BaseDetector(ABC):
    """
    Minimal detector interface (TIA pattern).

    Convention over Configuration:
    - Drop a *_detector.py file in reveal/detectors/
    - Inherit from BaseDetector
    - Set metadata (name, file_types, category)
    - Implement detect_issues() - that's it!

    Auto-Provided:
    - Auto-discovery (no manual registration)
    - File type filtering
    - Category filtering

    Example:
        class MyDetector(BaseDetector):
            name = "my-detector"
            description = "Find awesome issues"
            file_types = ['.py']
            category = Category.QUALITY

            def detect_issues(self, file_path, structure, content):
                # Your logic here
                return [SloppyIssue(...)]

    That's it! Auto-discovered, zero configuration.
    """

    # Auto-discovery metadata (override in subclass)
    name: str = "unknown"
    description: str = "No description provided"
    file_types: List[str] = ["*"]  # ['.py'] or ['*'] for universal
    category: Category = Category.COMPLEXITY
    version: str = "1.0.0"
    enabled: bool = True

    @abstractmethod
    def detect_issues(self, file_path: str, structure: Dict[str, List[Dict[str, Any]]],
                     content: str) -> List[SloppyIssue]:
        """
        Detect sloppy code issues - ONLY REQUIRED METHOD.

        Args:
            file_path: Path to file being analyzed
            structure: Structure dict from analyzer
                       e.g., {'functions': [...], 'classes': [...], 'imports': [...]}
            content: Raw file content as string

        Returns:
            List of SloppyIssue findings

        You get BOTH structure and content - use what you need!
        - Use structure for metadata checks (line count, depth, params)
        - Use content for AST parsing, regex patterns, etc.

        This is the ONLY method you need to implement!
        """
        pass

    def matches_file(self, file_path: str) -> bool:
        """Check if this detector applies to the given file (auto-provided)."""
        if '*' in self.file_types:
            return True
        return any(file_path.endswith(ext) for ext in self.file_types)

    def matches_category(self, category_filter: str = None) -> bool:
        """Check if detector matches category filter (auto-provided)."""
        if category_filter is None or category_filter == 'all':
            return True
        return self.category.value == category_filter
```

---

## Detector Examples

### Example 1: Universal Complexity (Structure-Based)

```python
# reveal/detectors/complexity_detector.py
from typing import List, Dict, Any
from .base import BaseDetector, SloppyIssue, Severity, Category

class ComplexityDetector(BaseDetector):
    """Detect complexity issues in any language with structure."""

    # Metadata
    name = "complexity"
    description = "Find long functions, deep nesting, too many parameters"
    file_types = ["*"]  # Universal - works for any language
    category = Category.COMPLEXITY
    version = "1.0.0"

    # Configurable thresholds
    THRESHOLDS = {
        'line_count': 50,
        'depth': 4,
        'params': 5,
    }

    def detect_issues(self, file_path: str, structure: Dict[str, List[Dict[str, Any]]],
                     content: str) -> List[SloppyIssue]:
        """Check structure for complexity issues."""
        issues = []

        # Check all functions
        for func in structure.get('functions', []):
            # Long function?
            line_count = func.get('line_count', 0)
            if line_count > self.THRESHOLDS['line_count']:
                severity = Severity.HIGH if line_count > 100 else Severity.MEDIUM
                issues.append(SloppyIssue(
                    file_path=file_path,
                    line=func.get('line', 0),
                    severity=severity,
                    category=self.category,
                    issue_type='long_function',
                    message=f"Function '{func['name']}' is {line_count} lines long",
                    suggestion=f"Break into smaller functions (<{self.THRESHOLDS['line_count']} lines each)",
                    element_name=func['name']
                ))

            # Deep nesting?
            depth = func.get('depth', 0)
            if depth > self.THRESHOLDS['depth']:
                issues.append(SloppyIssue(
                    file_path=file_path,
                    line=func.get('line', 0),
                    severity=Severity.MEDIUM,
                    category=self.category,
                    issue_type='deep_nesting',
                    message=f"Nesting depth of {depth} exceeds {self.THRESHOLDS['depth']}",
                    suggestion="Use early returns, extract helpers, or guard clauses",
                    element_name=func['name']
                ))

            # Too many parameters?
            params = func.get('params', 0)
            if params > self.THRESHOLDS['params']:
                issues.append(SloppyIssue(
                    file_path=file_path,
                    line=func.get('line', 0),
                    severity=Severity.MEDIUM,
                    category=self.category,
                    issue_type='too_many_parameters',
                    message=f"Function has {params} parameters (recommended: ≤{self.THRESHOLDS['params']})",
                    suggestion="Use a dataclass, config object, or **kwargs pattern",
                    element_name=func['name']
                ))

        return issues
```

### Example 2: Python Bare Except (AST-Based)

```python
# reveal/detectors/python_bare_except_detector.py
import ast
from typing import List, Dict, Any
from .base import BaseDetector, SloppyIssue, Severity, Category

class PythonBareExceptDetector(BaseDetector):
    """Detect bare except: clauses in Python code."""

    # Metadata
    name = "python-bare-except"
    description = "Find bare except clauses (catches all exceptions including SystemExit)"
    file_types = ['.py', '.pyi']
    category = Category.ERROR_HANDLING
    version = "1.0.0"

    def detect_issues(self, file_path: str, structure: Dict[str, List[Dict[str, Any]]],
                     content: str) -> List[SloppyIssue]:
        """Parse AST and find bare except handlers."""
        issues = []

        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError:
            return []  # Can't parse, skip

        # Walk AST looking for bare except
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                # Bare except has no exception type
                if node.type is None:
                    # Get the actual code line
                    lines = content.splitlines()
                    code_snippet = lines[node.lineno - 1] if node.lineno <= len(lines) else None

                    issues.append(SloppyIssue(
                        file_path=file_path,
                        line=node.lineno,
                        severity=Severity.HIGH,
                        category=self.category,
                        issue_type='bare_except',
                        message="Bare except clause catches all exceptions (including SystemExit, KeyboardInterrupt)",
                        suggestion="Use 'except Exception:' or specific exception types like ValueError, OSError",
                        code_snippet=code_snippet
                    ))

        return issues
```

### Example 3: Python Unused Imports (AST-Based)

```python
# reveal/detectors/python_unused_imports_detector.py
import ast
from typing import List, Dict, Any, Set
from .base import BaseDetector, SloppyIssue, Severity, Category

class PythonUnusedImportsDetector(BaseDetector):
    """Detect unused imports in Python code."""

    name = "python-unused-imports"
    description = "Find imported modules/names that are never used"
    file_types = ['.py', '.pyi']
    category = Category.MAINTAINABILITY
    version = "1.0.0"

    def detect_issues(self, file_path: str, structure: Dict[str, List[Dict[str, Any]]],
                     content: str) -> List[SloppyIssue]:
        """Find imports that are never referenced."""
        issues = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []

        # Collect imported names
        imported_names: Dict[str, int] = {}  # name -> line number

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imported_names[name] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == '*':
                        continue  # Skip star imports
                    name = alias.asname if alias.asname else alias.name
                    imported_names[name] = node.lineno

        # Collect used names
        used_names: Set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # For things like os.path, check 'os'
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)

        # Find unused
        for name, line in imported_names.items():
            if name not in used_names:
                issues.append(SloppyIssue(
                    file_path=file_path,
                    line=line,
                    severity=Severity.LOW,
                    category=self.category,
                    issue_type='unused_import',
                    message=f"Import '{name}' is never used",
                    suggestion=f"Remove unused import: {name}"
                ))

        return issues
```

### Example 4: Dockerfile Security (Pattern-Based)

```python
# reveal/detectors/dockerfile_security_detector.py
import re
from typing import List, Dict, Any
from .base import BaseDetector, SloppyIssue, Severity, Category

class DockerfileSecurityDetector(BaseDetector):
    """Detect Dockerfile security anti-patterns."""

    name = "dockerfile-security"
    description = "Find :latest tags, root user, missing healthcheck"
    file_types = ['Dockerfile', '.dockerfile']
    category = Category.SECURITY
    version = "1.0.0"

    def detect_issues(self, file_path: str, structure: Dict[str, List[Dict[str, Any]]],
                     content: str) -> List[SloppyIssue]:
        """Check for Docker security issues."""
        issues = []
        lines = content.splitlines()

        # Pattern 1: :latest tag
        for i, line in enumerate(lines, 1):
            if re.search(r'FROM\s+\S+:latest', line, re.IGNORECASE):
                issues.append(SloppyIssue(
                    file_path=file_path,
                    line=i,
                    severity=Severity.MEDIUM,
                    category=self.category,
                    issue_type='latest_tag',
                    message="Using :latest tag creates non-reproducible builds",
                    suggestion="Pin to specific version: FROM ubuntu:22.04",
                    code_snippet=line.strip()
                ))

        # Pattern 2: USER root
        for i, line in enumerate(lines, 1):
            if re.search(r'USER\s+root', line, re.IGNORECASE):
                issues.append(SloppyIssue(
                    file_path=file_path,
                    line=i,
                    severity=Severity.HIGH,
                    category=self.category,
                    issue_type='root_user',
                    message="Running container as root is a security risk",
                    suggestion="Create non-root user: RUN useradd -m appuser && USER appuser",
                    code_snippet=line.strip()
                ))

        # Pattern 3: Missing HEALTHCHECK
        if 'HEALTHCHECK' not in content:
            issues.append(SloppyIssue(
                file_path=file_path,
                line=1,
                severity=Severity.MEDIUM,
                category=self.category,
                issue_type='missing_healthcheck',
                message="No HEALTHCHECK instruction found",
                suggestion="Add HEALTHCHECK to enable container health monitoring"
            ))

        # Pattern 4: Too many RUN layers (use structure if available)
        run_directives = structure.get('runs', [])
        if len(run_directives) > 10:
            issues.append(SloppyIssue(
                file_path=file_path,
                line=1,
                severity=Severity.LOW,
                category=self.category,
                issue_type='too_many_run_layers',
                message=f"Too many RUN layers ({len(run_directives)}) - inefficient image size",
                suggestion="Combine RUN commands with && to reduce layers"
            ))

        return issues
```

### Example 5: Nginx Security (Domain Knowledge)

```python
# reveal/detectors/nginx_security_detector.py
from typing import List, Dict, Any
from .base import BaseDetector, SloppyIssue, Severity, Category

class NginxSecurityDetector(BaseDetector):
    """Detect insecure Nginx configurations."""

    name = "nginx-security"
    description = "Find missing SSL, weak ciphers, insecure directives"
    file_types = ['nginx.conf', '.conf']
    category = Category.SECURITY
    version = "1.0.0"

    # Weak cipher patterns
    WEAK_CIPHERS = ['DES-CBC3-SHA', 'RC4', 'MD5', 'NULL', 'EXPORT', 'LOW']

    def detect_issues(self, file_path: str, structure: Dict[str, List[Dict[str, Any]]],
                     content: str) -> List[SloppyIssue]:
        """Check Nginx config for security issues."""
        issues = []

        # Check server blocks for HTTP-only (no SSL)
        servers = structure.get('servers', [])
        for server in servers:
            listen_value = server.get('listen', '')
            directives = server.get('directives', [])

            # Port 80 without SSL redirect?
            if '80' in listen_value and not any('ssl' in str(d) for d in directives):
                issues.append(SloppyIssue(
                    file_path=file_path,
                    line=server.get('line', 0),
                    severity=Severity.HIGH,
                    category=self.category,
                    issue_type='no_ssl_redirect',
                    message="Server listening on port 80 without SSL redirect",
                    suggestion="Add: return 301 https://$server_name$request_uri;",
                    element_name=f"server block (line {server.get('line')})"
                ))

        # Check SSL cipher configuration
        directives = structure.get('directives', [])
        for directive in directives:
            if directive.get('name') == 'ssl_ciphers':
                cipher_string = directive.get('value', '')
                for weak in self.WEAK_CIPHERS:
                    if weak in cipher_string:
                        issues.append(SloppyIssue(
                            file_path=file_path,
                            line=directive.get('line', 0),
                            severity=Severity.MEDIUM,
                            category=self.category,
                            issue_type='weak_cipher',
                            message=f"Weak cipher suite detected: {weak}",
                            suggestion="Use modern ciphers: ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512"
                        ))

        # Check for directory listing
        for directive in directives:
            if directive.get('name') == 'autoindex' and directive.get('value') == 'on':
                issues.append(SloppyIssue(
                    file_path=file_path,
                    line=directive.get('line', 0),
                    severity=Severity.MEDIUM,
                    category=self.category,
                    issue_type='directory_listing',
                    message="Directory listing enabled (autoindex on)",
                    suggestion="Set: autoindex off;"
                ))

        return issues
```

---

## Auto-Discovery Implementation

### DetectorRegistry (Mirrors TIA ScannerRegistry)

```python
# reveal/detectors/__init__.py
"""
Auto-discover detectors (TIA pattern):
- Drop a *_detector.py file in this directory
- Inherit from BaseDetector
- It auto-discovers and works immediately

No registration code needed. No configuration files. Just works.
"""

from pathlib import Path
import importlib
import inspect
import sys
from typing import Dict, List, Optional

from .base import BaseDetector, SloppyIssue, Severity, Category

__all__ = ['DetectorRegistry', 'BaseDetector', 'SloppyIssue', 'Severity', 'Category']


class DetectorRegistry:
    """
    Auto-discover and register detectors (TIA pattern).

    Detectors are auto-discovered by:
    1. File naming convention: *_detector.py
    2. Class inherits from BaseDetector
    3. Class is not BaseDetector itself

    That's it! Drop file, detector exists.
    """

    _detectors: Dict[str, BaseDetector] = {}
    _discovered: bool = False

    @classmethod
    def discover(cls, force: bool = False):
        """
        Auto-discover all detectors in search paths.

        Args:
            force: Force re-discovery even if already discovered
        """
        if cls._discovered and not force:
            return

        cls._detectors.clear()

        # Search paths (in priority order)
        search_paths = [
            Path(__file__).parent,                    # Built-in: reveal/detectors/
            Path.home() / '.reveal' / 'detectors',    # User: ~/.reveal/detectors/
            Path.cwd() / '.reveal' / 'detectors',     # Project: ./.reveal/detectors/
        ]

        for search_path in search_paths:
            if not search_path.exists():
                continue

            # Find all *_detector.py files
            for detector_file in search_path.glob("*_detector.py"):
                if detector_file.name.startswith('_'):
                    continue  # Skip _private.py

                try:
                    # Import module
                    # Handle both built-in and external detectors
                    if search_path == Path(__file__).parent:
                        # Built-in detector
                        module_path = f"reveal.detectors.{detector_file.stem}"
                    else:
                        # External detector - add to sys.path temporarily
                        parent_dir = str(search_path)
                        if parent_dir not in sys.path:
                            sys.path.insert(0, parent_dir)
                        module_path = detector_file.stem

                    # Import the module
                    if module_path in sys.modules:
                        module = importlib.reload(sys.modules[module_path])
                    else:
                        module = importlib.import_module(module_path)

                    # Find BaseDetector subclasses
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)

                        # Check if it's a BaseDetector subclass
                        if (inspect.isclass(attr) and
                            issubclass(attr, BaseDetector) and
                            attr is not BaseDetector):

                            # Instantiate and register
                            detector = attr()
                            if detector.enabled:
                                cls._detectors[detector.name] = detector

                except Exception as e:
                    # Silently skip broken detectors
                    # TODO: Log warning in debug mode
                    pass

        cls._discovered = True

    @classmethod
    def get_detectors(cls, file_path: str, category: Optional[str] = None) -> List[BaseDetector]:
        """
        Get all detectors matching file type and category.

        Args:
            file_path: Path to file being analyzed
            category: Optional category filter (e.g., 'security', 'complexity')

        Returns:
            List of matching detector instances
        """
        if not cls._discovered:
            cls.discover()

        matches = []
        for detector in cls._detectors.values():
            if not detector.matches_file(file_path):
                continue
            if not detector.matches_category(category):
                continue
            matches.append(detector)

        return matches

    @classmethod
    def list_all(cls) -> List[BaseDetector]:
        """List all registered detectors."""
        if not cls._discovered:
            cls.discover()
        return list(cls._detectors.values())

    @classmethod
    def get_by_category(cls, category: str) -> List[BaseDetector]:
        """Get all detectors for a specific category."""
        if not cls._discovered:
            cls.discover()
        return [d for d in cls._detectors.values() if d.category.value == category]


# Auto-discover on import
DetectorRegistry.discover()
```

---

## Integration with FileAnalyzer

### Modify reveal/base.py

```python
# reveal/base.py (additions)
from typing import Optional, Dict, Any, List

class FileAnalyzer:
    # ... existing code ...

    def get_sloppy_issues(self, category: Optional[str] = None) -> List['SloppyIssue']:
        """
        Run all applicable detectors and return issues.

        Args:
            category: Filter by category (None = all categories)

        Returns:
            List of SloppyIssue objects from all matching detectors
        """
        from .detectors import DetectorRegistry

        # Get structure for detectors
        structure = self.get_structure()

        # Find matching detectors
        detectors = DetectorRegistry.get_detectors(str(self.path), category)

        # Run all detectors and aggregate results
        all_issues = []
        for detector in detectors:
            try:
                issues = detector.detect_issues(
                    file_path=str(self.path),
                    structure=structure,
                    content=self.content
                )
                all_issues.extend(issues)
            except Exception:
                # Skip detector on error
                # TODO: Log warning in debug mode
                pass

        return all_issues

    def enrich_structure_with_issues(self, structure: Dict[str, List[Dict[str, Any]]],
                                     category: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Add sloppy_issues field to each element in structure.

        This enriches the structure dict so rendering can show issues inline.

        Args:
            structure: Structure dict from get_structure()
            category: Optional category filter

        Returns:
            Enriched structure dict with sloppy_issues added to elements
        """
        issues = self.get_sloppy_issues(category)

        # Group issues by element name
        issues_by_element = {}
        for issue in issues:
            if issue.element_name:
                if issue.element_name not in issues_by_element:
                    issues_by_element[issue.element_name] = []
                issues_by_element[issue.element_name].append(issue)

        # Group issues by line number (for issues without element names)
        issues_by_line = {}
        for issue in issues:
            if not issue.element_name and issue.line:
                if issue.line not in issues_by_line:
                    issues_by_line[issue.line] = []
                issues_by_line[issue.line].append(issue)

        # Enrich structure
        for element_category, elements in structure.items():
            for element in elements:
                element_issues = []

                # Match by element name
                element_name = element.get('name')
                if element_name and element_name in issues_by_element:
                    element_issues.extend(issues_by_element[element_name])

                # Match by line number
                element_line = element.get('line')
                if element_line and element_line in issues_by_line:
                    element_issues.extend(issues_by_line[element_line])

                # Add to element
                if element_issues:
                    element['sloppy_issues'] = [issue.to_dict() for issue in element_issues]

        return structure
```

---

## CLI Integration

### Extend reveal/main.py

```python
# reveal/main.py (additions to argument parser)

parser.add_argument('--sloppy', nargs='?', const='all', default=None,
                   metavar='CATEGORY',
                   help='Show code quality issues (all, or category: complexity, error-handling, security)')

parser.add_argument('--sloppy-list', action='store_true',
                   help='List all available sloppy detectors')

parser.add_argument('--sloppy-types', nargs='?', const='all', metavar='FILETYPE',
                   help='List sloppy detection for file type (all, python, dockerfile, nginx)')


# In _main_impl():
if args.sloppy_list:
    list_detectors()
    return

if args.sloppy_types:
    list_sloppy_types(args.sloppy_types)
    return


# Modify show_structure() to enrich with issues
def show_structure(analyzer: FileAnalyzer, output_format: str, args=None):
    # ... existing structure retrieval ...

    structure = analyzer.get_structure(**kwargs)

    # If --sloppy flag present, enrich with issues
    if args and args.sloppy:
        category = args.sloppy if args.sloppy != 'all' else None
        structure = analyzer.enrich_structure_with_issues(structure, category)

    # ... rest of rendering ...


def list_detectors():
    """List all registered detectors (--sloppy-list)."""
    from .detectors import DetectorRegistry

    detectors = DetectorRegistry.list_all()

    print(f"\nAvailable Sloppy Detectors ({len(detectors)} loaded):\n")

    # Group by category
    by_category = {}
    for detector in detectors:
        cat = detector.category.value
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(detector)

    for category, dets in sorted(by_category.items()):
        print(f"  {category.upper()}")
        for det in dets:
            file_types = ', '.join(det.file_types) if det.file_types != ['*'] else 'all files'
            print(f"    {det.name:35} [{file_types}]")
            print(f"      {det.description}")
        print()


def list_sloppy_types(file_type: str):
    """List what detectors apply to a file type (--sloppy-types python)."""
    from .detectors import DetectorRegistry

    if file_type == 'all':
        # Show all file types
        detectors = DetectorRegistry.list_all()
        file_types = set()
        for det in detectors:
            if det.file_types != ['*']:
                file_types.update(det.file_types)

        print("\nSloppy Detection by File Type:\n")
        for ft in sorted(file_types):
            print(f"  {ft}")
            matching = [d for d in detectors if ft in d.file_types]
            categories = sorted(set(d.category.value for d in matching))
            print(f"    Categories: {', '.join(categories)}")
            for det in matching:
                print(f"      {det.name} - {det.description}")
        print()
    else:
        # Show detectors for specific file type
        ext = file_type if file_type.startswith('.') else f'.{file_type}'
        detectors = [d for d in DetectorRegistry.list_all()
                    if ext in d.file_types or '*' in d.file_types]

        print(f"\nSloppy Detection for {file_type}:\n")

        by_category = {}
        for det in detectors:
            cat = det.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(det)

        for category, dets in sorted(by_category.items()):
            print(f"  {category}:")
            for det in dets:
                print(f"    {det.name:35} {det.description}")
        print()
```

---

## Output Format Examples

### Text Output (Default)

```bash
$ reveal app.py --sloppy=error-handling

File: app.py

Imports (5):
  app.py:1    import os
  app.py:2    import sys
  app.py:3    import json
  app.py:4    from typing import Dict
  app.py:5    from pathlib import Path

Functions (3):
  app.py:10   load_config() [12 lines, depth:2]

  app.py:24   handle_request(data) [35 lines, depth:3] ⚠️ 2 issues
              ├─ [HIGH] bare_except (line 45)
              │  Bare except clause catches all exceptions (including SystemExit, KeyboardInterrupt)
              │  💡 Use 'except Exception:' or specific exception types
              └─ [MEDIUM] broad_exception (line 52)
                 Catching Exception is too broad - catches all runtime errors
                 💡 Use specific exception types like ValueError, OSError

  app.py:60   process_data(items: List[str]) [28 lines, depth:4] ⚠️ 1 issue
              └─ [HIGH] silent_failure (line 78)
                 Exception caught but silently ignored (pass/continue only)
                 💡 Add logging: logger.exception("Error occurred")

Summary:
  ✓ 1 clean function
  ⚠️ 2 functions with issues (3 total issues)

  By severity:
    🔴 HIGH: 2
    🟡 MEDIUM: 1
```

### JSON Output

```bash
$ reveal app.py --sloppy=error-handling --format=json

{
  "file": "app.py",
  "structure": {
    "functions": [
      {
        "name": "handle_request",
        "line": 24,
        "line_count": 35,
        "sloppy_issues": [
          {
            "file_path": "app.py",
            "line": 45,
            "severity": "high",
            "category": "error-handling",
            "issue_type": "bare_except",
            "message": "Bare except clause catches all exceptions",
            "suggestion": "Use 'except Exception:' or specific exception types",
            "element_name": "handle_request"
          }
        ]
      }
    ]
  }
}
```

---

## User-Defined Detectors

### Creating a Custom Detector

```bash
# Create detector directory
mkdir -p ~/.reveal/detectors

# Create detector file
cat > ~/.reveal/detectors/my_custom_detector.py <<'EOF'
from reveal.detectors.base import BaseDetector, SloppyIssue, Severity, Category

class MyCustomDetector(BaseDetector):
    """My custom quality check."""

    name = "my-custom"
    description = "Find TODO comments"
    file_types = ['*']  # All files
    category = Category.MAINTAINABILITY

    def detect_issues(self, file_path, structure, content):
        issues = []

        for i, line in enumerate(content.splitlines(), 1):
            if 'TODO' in line:
                issues.append(SloppyIssue(
                    file_path=file_path,
                    line=i,
                    severity=Severity.LOW,
                    category=self.category,
                    issue_type='todo_comment',
                    message="TODO comment found",
                    suggestion="Complete or remove TODO",
                    code_snippet=line.strip()
                ))

        return issues
EOF

# Auto-loaded on next reveal run!
reveal app.py --sloppy-list
# Output includes:
#   my-custom                            [all files]
#     Find TODO comments
```

---

## Implementation Roadmap

### Phase 1: Foundation (v0.13.0)
**Goal:** Prove the pattern works with Python detectors

**Tasks:**
- [ ] Create `reveal/detectors/` module structure
- [ ] Implement `BaseDetector` abstract class
- [ ] Implement `SloppyIssue` dataclass + enums
- [ ] Implement `DetectorRegistry` with auto-discovery (TIA pattern)
- [ ] Create 3 detectors:
  - `complexity_detector.py` (universal, structure-based)
  - `python_bare_except_detector.py` (Python, AST-based)
  - `python_unused_imports_detector.py` (Python, AST-based)
- [ ] Modify `FileAnalyzer`:
  - Add `get_sloppy_issues()`
  - Add `enrich_structure_with_issues()`
- [ ] Add CLI flags: `--sloppy`, `--sloppy-list`, `--sloppy-types`
- [ ] Update text output renderer to show issues inline
- [ ] Add JSON output support with `sloppy_issues` field
- [ ] Write unit tests for detector API + auto-discovery
- [ ] Update `--recommend-prompt` with sloppy usage patterns

**Success Criteria:**
- `reveal app.py --sloppy` shows all issues
- `reveal app.py --sloppy=error-handling` filters correctly
- `reveal --sloppy-list` shows all 3 detectors
- User can drop detector in `~/.reveal/detectors/` and it works

**Estimated Effort:** 2-3 days

### Phase 2: Domain-Specific (v0.14.0)
**Goal:** Expand to Dockerfile + Nginx

**Tasks:**
- [ ] Create `dockerfile_security_detector.py` (pattern-based)
- [ ] Create `nginx_security_detector.py` (structure + patterns)
- [ ] Add `--min-severity` flag (high, medium, low)
- [ ] Enhance output with colored severity markers
- [ ] Add detector documentation integration

**Success Criteria:**
- `reveal Dockerfile --sloppy=security` shows Docker issues
- `reveal nginx.conf --sloppy=security` shows Nginx issues
- `--min-severity=high` filters correctly

**Estimated Effort:** 1-2 days

### Phase 3: Ecosystem (v0.15.0)
**Goal:** Enable third-party detector packages

**Tasks:**
- [ ] Define entry point mechanism for external detectors
- [ ] Create example extension package: `reveal-detectors-sql`
- [ ] Add detector versioning checks
- [ ] Add detector enable/disable config file support
- [ ] Create detector development guide
- [ ] Publish detector development template

**Success Criteria:**
- `pip install reveal-detectors-sql` auto-registers detectors
- Example third-party package works

**Estimated Effort:** 2-3 days

### Phase 4: Polish (v0.16.0)
**Goal:** Production-ready

**Tasks:**
- [ ] Performance optimization (caching, async)
- [ ] CI/CD integration (GitHub Actions format)
- [ ] Configuration file support (`.reveal-config.yaml`)
- [ ] Auto-fix suggestions (where safe)
- [ ] Comprehensive documentation

**Estimated Effort:** 3-5 days

---

## Design Decisions & Rationale

### 1. Why Mirror TIA's Pattern Exactly?

**Battle-Tested:** TIA has 18+ scanners using this pattern successfully
**Proven Simple:** Minimal interface, easy for authors
**Auto-Discovery Works:** File naming convention is clear and works
**Single Method:** One entry point is easier than three

### 2. Why ONE Method (detect_issues) Not Three?

**Original design had:**
- `analyze_structure(structure)` - for metadata checks
- `analyze_element(element)` - per-element checks
- `analyze_content(content)` - AST/regex checks

**Problem:** Author confusion - which method do I use?

**Solution:** ONE method gets everything:
```python
def detect_issues(file_path, structure, content):
    # You get ALL the data - use what you need
    pass
```

**Benefits:**
- No confusion about which method to implement
- Author decides how to analyze (structure vs content vs both)
- Simpler base class, simpler docs

### 3. Why Dataclass (SloppyIssue) Not Dict?

**Type Safety:** Explicit fields, IDE autocomplete
**Validation:** Dataclass validates types
**Documentation:** Self-documenting structure
**TIA Precedent:** TIA uses `ScanResult` dataclass

### 4. Why Category Enum Not Strings?

**Prevents Typos:** Can't accidentally use "securtiy" vs "security"
**IDE Support:** Autocomplete shows valid categories
**Filtering:** Easy to filter by enum
**TIA Precedent:** TIA uses `Category` enum

### 5. Why Auto-Discovery Not Manual Registration?

**Original design had:** `DetectorRegistry.register(MyDetector())`

**Problem:** Easy to forget, extra boilerplate

**Solution:** File naming convention + auto-discovery

**Benefits:**
- Zero boilerplate - just inherit and save file
- Clear convention: `*_detector.py`
- Matches TIA's proven pattern

---

## Comparison to TIA Scanners

| Feature | TIA Scanners | Reveal Detectors |
|---------|--------------|------------------|
| **File Pattern** | `*_scanner.py` | `*_detector.py` |
| **Base Class** | `BaseScanner` | `BaseDetector` |
| **Method Count** | 1 (`scan_file`) | 1 (`detect_issues`) |
| **Output Format** | `ScanResult` dataclass | `SloppyIssue` dataclass |
| **Auto-Discovery** | Yes (file naming) | Yes (file naming) |
| **Categories** | Enum | Enum |
| **Severity** | Enum | Enum |
| **Manual Registration** | No | No |

**Differences:**
- TIA: `scan_file(file_path)` - reads file itself
- Reveal: `detect_issues(file_path, structure, content)` - structure pre-loaded

**Why the difference?** Reveal already parsed structure (expensive), so we pass it to detectors. TIA scanners are standalone, so they read files themselves.

---

## Success Metrics

**v0.13.0 (Foundation):**
- ✅ 3+ working detectors (complexity, bare except, unused imports)
- ✅ Auto-discovery works from `~/.reveal/detectors/`
- ✅ `--sloppy=<category>` filtering works
- ✅ Text + JSON output includes issues

**v0.14.0 (Domain-Specific):**
- ✅ 5+ detectors (add Dockerfile, Nginx)
- ✅ Multi-file-type detection working
- ✅ 100+ GitHub stars

**v0.15.0 (Ecosystem):**
- ✅ 1+ third-party detector package published
- ✅ Detector development guide complete
- ✅ 1000+ PyPI downloads/month

**v0.16.0 (Production):**
- ✅ 10+ detectors total
- ✅ Performance < 100ms overhead
- ✅ Comprehensive documentation
- ✅ 5000+ PyPI downloads/month

---

## Open Questions

### 1. Should detectors be async?

**Consideration:** Running 10+ detectors could be slow

**Options:**
- A) Sync (simple, v0.13.0)
- B) Async with asyncio (complex, v0.16.0+)
- C) Thread pool (middle ground, v0.15.0)

**Decision:** Start sync (A), add async if needed (B) in v0.16.0

### 2. Configuration file support?

**User might want:**
```yaml
# .reveal-config.yaml
detectors:
  complexity:
    thresholds:
      line_count: 100
  python-bare-except:
    enabled: false
```

**Decision:** Not in MVP (v0.13.0). Add if users request (v0.15.0).

### 3. Should detectors cache results?

**Consideration:** Same file analyzed multiple times

**Options:**
- A) No caching (simple, may be slow)
- B) Hash-based caching (file hash → results)

**Decision:** No caching in MVP. Measure performance first.

---

## Appendix: Quick Start Guide

### For Detector Authors

**1. Create detector file:**
```bash
touch ~/.reveal/detectors/my_detector.py
```

**2. Write detector:**
```python
from reveal.detectors.base import BaseDetector, SloppyIssue, Severity, Category

class MyDetector(BaseDetector):
    name = "my-detector"
    description = "What it checks"
    file_types = ['.py']  # or ['*'] for all
    category = Category.SECURITY

    def detect_issues(self, file_path, structure, content):
        issues = []
        # Your logic here
        issues.append(SloppyIssue(
            file_path=file_path,
            line=42,
            severity=Severity.HIGH,
            category=self.category,
            issue_type='my_issue_type',
            message="What's wrong",
            suggestion="How to fix"
        ))
        return issues
```

**3. Test:**
```bash
reveal myfile.py --sloppy
```

**Done!**

---

## References

- **TIA AST Scanner Pattern:** `/home/scottsen/src/tia/lib/tia/ast/scanners/`
- **TIA BaseScanner:** `/home/scottsen/src/tia/lib/tia/ast/scanners/base_scanner.py`
- **TIA ScannerRegistry:** `/home/scottsen/src/tia/lib/tia/ast/scanners/__init__.py`
- **TIA Example Scanners:**
  - `complexity_scanner.py`
  - `error_handling_scanner.py`
  - `timezone_audit_scanner.py`
- **Reveal Base Analyzer:** `/home/scottsen/src/projects/reveal/external-git/reveal/base.py`
- **Python AST Module:** https://docs.python.org/3/library/ast.html

---

## Document History

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-30 | 1.0 | Initial design proposal |
| 2025-11-30 | 2.0 | Simplified with decorator pattern |
| 2025-11-30 | 2.1 | **Aligned with TIA's proven pattern** |

---

**Status:** DRAFT - Ready for implementation

**Next Steps:**
1. Begin Phase 1 implementation (Foundation)
2. Create `reveal/detectors/` module structure
3. Implement first 3 detectors
4. Test auto-discovery with user detector
