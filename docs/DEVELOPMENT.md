# Reveal Development Guide

> **Learn to extend reveal:** Add new file types in minutes, not hours

---

## 🎯 Quick Start

**Want to add support for a new file type?**

Two paths, depending on the file type:

| File Type | Approach | Lines of Code | Example |
|-----------|----------|---------------|---------|
| Programming language | Use Tree-Sitter | 10 lines | Python, Rust, Go, Java |
| Structured text | Custom analyzer | 50-200 lines | Markdown, YAML, Nginx |

**This guide shows you both.**

---

## 🚀 Path 1: Tree-Sitter Languages (10 Lines!)

### What is Tree-Sitter?

Tree-sitter provides syntax-aware parsing for 50+ languages. You get function extraction, class extraction, and import detection **for free**.

### Supported Languages

```bash
reveal --list-supported
```

Currently supported: Python, Rust, Go, JavaScript, TypeScript, C, C++, Java, C#, PHP, Ruby, Swift, Kotlin, and 40+ more.

### Example: Adding Kotlin Support

**Step 1:** Create analyzer file

```python
# reveal/analyzers/kotlin.py
"""Kotlin file analyzer - tree-sitter based."""

from ..base import register
from ..treesitter import TreeSitterAnalyzer


@register('.kt', name='Kotlin', icon='🟣')
class KotlinAnalyzer(TreeSitterAnalyzer):
    """Kotlin file analyzer.

    Full Kotlin support in 3 lines!
    """
    language = 'kotlin'
```

**That's it!** You now have:
- ✅ Function extraction
- ✅ Class extraction
- ✅ Import detection
- ✅ Element extraction by name
- ✅ Accurate line numbers

**Step 2:** Register the analyzer

```python
# reveal/analyzers/__init__.py
# Add this line:
from .kotlin import KotlinAnalyzer
```

**Step 3:** Test it

```bash
reveal example.kt
reveal example.kt MyClass
reveal example.kt myFunction
```

### What You Get For Free

When you extend `TreeSitterAnalyzer`, you automatically get:

```python
def get_structure(self):
    """Returns:
    {
        'imports': [...],
        'functions': [...],
        'classes': [...]
    }
    """

def extract_element(self, element_type, name):
    """Finds and extracts specific function/class by name."""

def get_metadata(self):
    """Returns file size, line count, encoding."""
```

### Multiple Extensions

```python
@register('.js', '.mjs', '.cjs', name='JavaScript', icon='📜')
class JavaScriptAnalyzer(TreeSitterAnalyzer):
    language = 'javascript'
```

---

## 🔧 Path 2: Custom Analyzers (50-200 Lines)

For file types that aren't programming languages (configs, markup, data formats), you'll write a custom analyzer.

### The Interface

All analyzers implement the `FileAnalyzer` interface:

```python
class FileAnalyzer:
    """Base class for file analyzers."""

    def __init__(self, path: str):
        self.path = Path(path)
        self.lines = self._read_file()  # List[str]
        self.content = '\n'.join(self.lines)

    def get_structure(self) -> Dict[str, List[Dict[str, Any]]]:
        """Extract file structure.

        Returns dict with structure elements.
        Example: {'sections': [...], 'links': [...]}
        """
        raise NotImplementedError

    def extract_element(self, element_type: str, name: str) -> Optional[Dict]:
        """Extract specific element by name.

        Args:
            element_type: Type of element ('section', 'function', etc.)
            name: Name of element to extract

        Returns:
            Dict with 'source', 'start_line', 'end_line', etc.
        """
        raise NotImplementedError

    def get_metadata(self) -> Dict[str, Any]:
        """Return file metadata (size, lines, encoding)."""
        # Provided by base class
```

---

### Example 1: Simple Custom Analyzer (TOML)

```python
# reveal/analyzers/toml.py
"""TOML configuration file analyzer."""

import toml
from typing import Dict, List, Any, Optional
from ..base import FileAnalyzer, register


@register('.toml', name='TOML', icon='📋')
class TomlAnalyzer(FileAnalyzer):
    """TOML configuration file analyzer."""

    def get_structure(self) -> Dict[str, List[Dict[str, Any]]]:
        """Extract TOML sections."""
        try:
            data = toml.loads(self.content)
        except toml.TomlDecodeError:
            return {'sections': []}

        sections = []
        for section_name in data.keys():
            # Find line number by searching file
            line_num = self._find_section_line(section_name)

            sections.append({
                'line': line_num,
                'name': section_name,
                'type': type(data[section_name]).__name__
            })

        return {'sections': sections}

    def extract_element(self, element_type: str, name: str) -> Optional[Dict]:
        """Extract a specific TOML section."""
        if element_type != 'section':
            return None

        # Find section in file
        start_line = None
        end_line = None

        for i, line in enumerate(self.lines, 1):
            if line.strip() == f'[{name}]':
                start_line = i
            elif start_line and line.startswith('['):
                end_line = i - 1
                break

        if not start_line:
            return None

        if not end_line:
            end_line = len(self.lines)

        # Extract lines
        section_lines = self.lines[start_line-1:end_line]
        source = '\n'.join(section_lines)

        return {
            'type': 'section',
            'name': name,
            'source': source,
            'start_line': start_line,
            'end_line': end_line,
            'path': str(self.path)
        }

    def _find_section_line(self, section_name: str) -> int:
        """Find line number of section."""
        for i, line in enumerate(self.lines, 1):
            if line.strip() == f'[{section_name}]':
                return i
        return 0
```

**Usage:**
```bash
reveal pyproject.toml              # Show all sections
reveal pyproject.toml project      # Extract [project] section
reveal pyproject.toml --format=json
```

---

### Example 2: Complex Custom Analyzer (Nginx)

For more complex file types, you need custom parsing logic:

```python
# reveal/analyzers/nginx.py
"""Nginx configuration file analyzer."""

import re
from typing import Dict, List, Any, Optional
from ..base import FileAnalyzer, register


@register('.conf', name='Nginx', icon='🌐',
          path_patterns=['/nginx/', '/etc/nginx/'])  # Path-based detection
class NginxAnalyzer(FileAnalyzer):
    """Nginx configuration file analyzer."""

    def get_structure(self) -> Dict[str, List[Dict[str, Any]]]:
        """Extract nginx configuration structure."""
        servers = []
        locations = []
        upstreams = []

        current_context = []  # Stack for nested blocks

        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()

            # Server blocks
            if re.match(r'^\s*server\s*{', line):
                servers.append({
                    'line': i,
                    'name': f'server_{len(servers) + 1}'
                })
                current_context.append('server')

            # Location blocks
            elif match := re.match(r'^\s*location\s+([^\s{]+)', line):
                path = match.group(1)
                locations.append({
                    'line': i,
                    'name': path,  # e.g., '/api/', '~* \.php$'
                    'path': path
                })

            # Upstream blocks
            elif match := re.match(r'^\s*upstream\s+(\w+)', line):
                name = match.group(1)
                upstreams.append({
                    'line': i,
                    'name': name
                })

            # End of block
            elif stripped == '}' and current_context:
                current_context.pop()

        return {
            'servers': servers,
            'locations': locations,
            'upstreams': upstreams
        }

    def extract_element(self, element_type: str, name: str) -> Optional[Dict]:
        """Extract specific nginx block."""
        if element_type == 'server':
            return self._extract_server(name)
        elif element_type == 'location':
            return self._extract_location(name)
        elif element_type == 'upstream':
            return self._extract_upstream(name)
        return None

    def _extract_server(self, name: str) -> Optional[Dict]:
        """Extract a server block."""
        # Find server block (by index like 'server_1')
        server_idx = int(name.split('_')[1]) if '_' in name else 1
        current_server = 0

        for i, line in enumerate(self.lines, 1):
            if re.match(r'^\s*server\s*{', line):
                current_server += 1
                if current_server == server_idx:
                    # Found it! Now extract the block
                    start_line = i
                    end_line = self._find_closing_brace(i)

                    source = '\n'.join(self.lines[start_line-1:end_line])

                    return {
                        'type': 'server',
                        'name': name,
                        'source': source,
                        'start_line': start_line,
                        'end_line': end_line,
                        'path': str(self.path)
                    }
        return None

    def _find_closing_brace(self, start_line: int) -> int:
        """Find matching closing brace."""
        depth = 0
        for i in range(start_line - 1, len(self.lines)):
            if '{' in self.lines[i]:
                depth += self.lines[i].count('{')
            if '}' in self.lines[i]:
                depth -= self.lines[i].count('}')
            if depth == 0:
                return i + 1
        return len(self.lines)
```

**Key patterns in custom analyzers:**
- Use regex for pattern matching
- Track context with a stack (for nested blocks)
- Find line numbers while parsing
- Extract blocks by finding start/end markers

---

## 📋 Analyzer Checklist

When implementing an analyzer, ensure you handle:

### ✅ Required Methods

- [ ] `get_structure()` - Returns dict with structure elements
- [ ] `extract_element()` - Extracts specific element by name

### ✅ Structure Format

```python
{
    'element_type': [  # e.g., 'functions', 'classes', 'sections'
        {
            'line': 15,           # Required: line number
            'name': 'element_name',  # Required: element name
            'signature': '...',   # Optional: for functions
            'type': '...',        # Optional: element metadata
            # ... any other fields
        }
    ]
}
```

### ✅ Extract Format

```python
{
    'type': 'function',      # Element type
    'name': 'load_config',   # Element name
    'source': '...',         # Element source code
    'start_line': 15,        # Start line number
    'end_line': 27,          # End line number
    'path': '/path/to/file'  # File path
}
```

### ✅ Error Handling

```python
def get_structure(self):
    """Extract structure with error handling."""
    try:
        # Parsing logic
        data = self.parse_file()
        return self.extract_structure(data)
    except Exception as e:
        # Graceful degradation - return empty structure
        return {'sections': []}
```

### ✅ Line Numbers

Always include accurate line numbers! Users rely on `filename:line` format for vim, git, etc.

```python
# Good - accurate line numbers
for i, line in enumerate(self.lines, 1):  # Start at 1, not 0!
    if self.is_section(line):
        sections.append({'line': i, 'name': self.parse_name(line)})

# Bad - no line numbers
sections.append({'name': name})  # Missing 'line' field!
```

---

## 🧪 Testing Your Analyzer

### Manual Testing

```bash
# Test structure extraction
reveal sample_file.ext

# Test element extraction
reveal sample_file.ext element_name

# Test output formats
reveal sample_file.ext --format=json
reveal sample_file.ext --format=grep

# Test metadata
reveal sample_file.ext --meta
```

### Unit Testing

```python
# tests/test_kotlin_analyzer.py
import pytest
from reveal.base import get_analyzer
from pathlib import Path


def test_kotlin_structure(tmp_path):
    """Test Kotlin analyzer structure extraction."""
    # Create test file
    test_file = tmp_path / "Sample.kt"
    test_file.write_text("""
        package com.example

        import java.util.*

        class UserManager {
            fun createUser(name: String) {
                println("Creating: $name")
            }

            fun deleteUser(id: Int) {
                println("Deleting: $id")
            }
        }
    """)

    # Get analyzer and parse
    analyzer_cls = get_analyzer(str(test_file))
    analyzer = analyzer_cls(str(test_file))
    structure = analyzer.get_structure()

    # Assertions
    assert 'classes' in structure
    assert len(structure['classes']) == 1
    assert structure['classes'][0]['name'] == 'UserManager'

    assert 'functions' in structure
    assert len(structure['functions']) == 2
    function_names = [f['name'] for f in structure['functions']]
    assert 'createUser' in function_names
    assert 'deleteUser' in function_names


def test_kotlin_element_extraction(tmp_path):
    """Test extracting specific function."""
    test_file = tmp_path / "Sample.kt"
    test_file.write_text("""
        fun greet(name: String) {
            println("Hello, $name!")
        }
    """)

    analyzer_cls = get_analyzer(str(test_file))
    analyzer = analyzer_cls(str(test_file))
    result = analyzer.extract_element('function', 'greet')

    assert result is not None
    assert result['name'] == 'greet'
    assert result['type'] == 'function'
    assert 'println' in result['source']
    assert result['start_line'] > 0
```

### Integration Testing

```bash
# Create test samples directory
mkdir -p validation_samples

# Add sample files
echo "Sample TOML content" > validation_samples/sample.toml

# Test with reveal
reveal validation_samples/sample.toml
```

---

## 🎨 Advanced Techniques

### Path-Based Detection

For files without extensions:

```python
@register('.conf', name='Nginx',
          path_patterns=['/nginx/', '/etc/nginx/'])
class NginxAnalyzer(FileAnalyzer):
    """Detects files in nginx directories."""
    ...
```

Now files like `/etc/nginx/sites-available/mysite` are detected automatically!

### Shebang Detection

For extensionless scripts:

```python
# base.py handles this automatically
# A file with #!/bin/bash is detected as BashAnalyzer
```

### Multiple Element Types

```python
def extract_element(self, element_type: str, name: str):
    """Support multiple element types."""
    if element_type == 'function':
        return self._extract_function(name)
    elif element_type == 'class':
        return self._extract_class(name)
    elif element_type == 'section':
        return self._extract_section(name)
    return None
```

### Hierarchical Structure

```python
def get_structure(self):
    """Return nested structure."""
    return {
        'classes': [
            {
                'name': 'UserManager',
                'line': 10,
                'methods': [  # Nested!
                    {'name': 'create', 'line': 15},
                    {'name': 'delete', 'line': 25}
                ]
            }
        ]
    }
```

### Caching Expensive Operations

```python
class MyAnalyzer(FileAnalyzer):
    def __init__(self, path):
        super().__init__(path)
        self._parsed_data = None  # Cache

    @property
    def parsed_data(self):
        """Lazy parse, cache result."""
        if self._parsed_data is None:
            self._parsed_data = self._expensive_parse()
        return self._parsed_data

    def get_structure(self):
        return self._extract_structure(self.parsed_data)

    def extract_element(self, element_type, name):
        return self._find_element(self.parsed_data, element_type, name)
```

---

## 🚫 Common Pitfalls

### ❌ Pitfall 1: Zero-Indexed Line Numbers

```python
# BAD - line numbers start at 0 (doesn't match editors)
for i, line in enumerate(self.lines):
    items.append({'line': i, 'name': name})

# GOOD - line numbers start at 1
for i, line in enumerate(self.lines, 1):
    items.append({'line': i, 'name': name})
```

### ❌ Pitfall 2: Not Handling Parse Errors

```python
# BAD - crashes on malformed files
def get_structure(self):
    data = json.loads(self.content)  # Throws on invalid JSON!
    return self.extract(data)

# GOOD - graceful degradation
def get_structure(self):
    try:
        data = json.loads(self.content)
        return self.extract(data)
    except json.JSONDecodeError:
        return {'sections': []}  # Empty structure, not a crash
```

### ❌ Pitfall 3: Missing Required Fields

```python
# BAD - missing 'line' field
functions.append({'name': func_name})

# GOOD - includes line number
functions.append({'line': line_num, 'name': func_name})
```

### ❌ Pitfall 4: Not Implementing extract_element

```python
# BAD - users can't extract elements
def extract_element(self, element_type, name):
    return None  # Always returns nothing!

# GOOD - actually extracts elements
def extract_element(self, element_type, name):
    if element_type == 'function':
        return self._find_function(name)
    # ... implementation
```

---

## 📚 Real-World Examples

### Study These Analyzers

**Simplest (Tree-Sitter):**
- `reveal/analyzers/python.py` - 15 lines
- `reveal/analyzers/rust.py` - 13 lines
- `reveal/analyzers/go.py` - 13 lines

**Medium Complexity (Custom):**
- `reveal/analyzers/toml.py` - 96 lines
- `reveal/analyzers/yaml_json.py` - 110 lines

**Complex (Custom with nested parsing):**
- `reveal/analyzers/nginx.py` - 186 lines
- `reveal/analyzers/markdown.py` - 312 lines

**Read them with reveal!**
```bash
reveal reveal/analyzers/python.py
reveal reveal/analyzers/nginx.py --outline
```

---

## 🚀 Quick Reference

### Tree-Sitter Analyzer Template

```python
from ..base import register
from ..treesitter import TreeSitterAnalyzer

@register('.ext', name='MyLanguage', icon='🎯')
class MyLanguageAnalyzer(TreeSitterAnalyzer):
    """Description."""
    language = 'language_name'  # Must match tree-sitter name
```

### Custom Analyzer Template

```python
from typing import Dict, List, Any, Optional
from ..base import FileAnalyzer, register

@register('.ext', name='MyFormat', icon='📄')
class MyFormatAnalyzer(FileAnalyzer):
    """Description."""

    def get_structure(self) -> Dict[str, List[Dict[str, Any]]]:
        """Extract structure."""
        elements = []

        for i, line in enumerate(self.lines, 1):
            if self.is_element(line):
                elements.append({
                    'line': i,
                    'name': self.parse_name(line)
                })

        return {'elements': elements}

    def extract_element(self, element_type: str, name: str) -> Optional[Dict]:
        """Extract specific element."""
        # Find element by name
        start_line = self._find_element_start(name)
        if not start_line:
            return None

        end_line = self._find_element_end(start_line)
        source = '\n'.join(self.lines[start_line-1:end_line])

        return {
            'type': element_type,
            'name': name,
            'source': source,
            'start_line': start_line,
            'end_line': end_line,
            'path': str(self.path)
        }

    # Helper methods
    def is_element(self, line: str) -> bool:
        """Check if line starts an element."""
        ...

    def parse_name(self, line: str) -> str:
        """Extract element name from line."""
        ...

    def _find_element_start(self, name: str) -> Optional[int]:
        """Find start line of element."""
        ...

    def _find_element_end(self, start: int) -> int:
        """Find end line of element."""
        ...
```

---

## 🤝 Contributing Your Analyzer

Ready to submit your analyzer?

1. **Create the analyzer** in `reveal/analyzers/your_format.py`
2. **Register it** in `reveal/analyzers/__init__.py`
3. **Add tests** in `tests/test_your_format_analyzer.py`
4. **Add validation sample** in `validation_samples/sample.your_ext`
5. **Update README** (add to supported file types list)
6. **Submit PR** with description and examples

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

---

## 📖 Next Steps

- **Explore the codebase:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **See the roadmap:** [ROADMAP.md](../ROADMAP.md)
- **Join the discussion:** [GitHub Discussions](https://github.com/scottsen/reveal/discussions)

---

**Questions?** Open an issue with `[Development]` tag or ask in Discussions!

**Last updated:** 2025-11-27
**For version:** v0.11.0
