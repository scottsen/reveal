# Reveal Architecture Guide

> **For LLMs and developers:** Efficiently explore and understand the reveal codebase

---

## 🎯 Quick Start: Navigating This Codebase

**If you're an LLM agent exploring reveal:**

```bash
# 1. Start here - see overall structure
reveal reveal/

# 2. Understand core architecture
reveal reveal/base.py --outline        # Registration & analyzer base
reveal reveal/main.py --outline        # CLI & output formatting
reveal reveal/treesitter.py --outline  # Tree-sitter integration

# 3. See how analyzers work
reveal reveal/analyzers/python.py      # Simplest (3 lines!)
reveal reveal/analyzers/nginx.py       # Custom logic example

# 4. Check adapter system (new!)
reveal reveal/adapters/base.py         # Adapter protocol
reveal reveal/adapters/env.py          # First URI adapter
```

**Progressive deepening strategy:**
1. **Structure first** - Use reveal itself to explore
2. **Patterns second** - Understand @register decorator pattern
3. **Details last** - Read specific implementations as needed

---

## 📐 Architecture Overview

### Core Concept: Progressive Disclosure

Reveal is built around **three levels of detail**:

```
Level 1: Directory → Show files and sizes
Level 2: File      → Show structure (functions, classes, imports)
Level 3: Element   → Show implementation (specific function/class code)
```

**Key insight:** Users (especially AI agents) rarely need full files. Progressive disclosure saves tokens and time.

---

## 🏗️ System Architecture

```
reveal <path or URI>
        │
        ├─ File Path? ──→ Analyzer System
        │                     │
        │                     ├─ base.py (analyzer registry)
        │                     ├─ analyzers/* (file type handlers)
        │                     └─ treesitter.py (50+ languages)
        │
        └─ URI? ──────→ Adapter System
                              │
                              ├─ adapters/base.py (adapter protocol)
                              └─ adapters/env.py (environment variables)
                                 adapters/postgres.py (future)
                                 adapters/docker.py (future)
```

---

## 📦 Core Components

### 1. `reveal/base.py` (378 lines)

**Purpose:** Analyzer registration and base classes

**Key elements:**

```python
# Decorator-based registration
@register('.py', name='Python', icon='🐍')
class PythonAnalyzer(TreeSitterAnalyzer):
    language = 'python'
```

**What it provides:**
- `@register()` decorator - Registers file type analyzers
- `FileAnalyzer` base class - Interface all analyzers implement
- `get_analyzer()` - Finds the right analyzer for a file
- `get_all_analyzers()` - Lists all registered analyzers

**Key pattern:**
```python
# Registration happens at import time
ANALYZER_REGISTRY = {}  # Maps extensions to analyzer classes

def register(extension, name, icon='📄'):
    """Decorator that registers an analyzer."""
    def decorator(cls):
        ANALYZER_REGISTRY[extension] = cls
        cls.extension = extension
        cls.name = name
        cls.icon = icon
        return cls
    return decorator
```

**Navigator tip:**
```bash
reveal reveal/base.py get_analyzer     # See how analyzers are selected
reveal reveal/base.py register         # See registration pattern
```

---

### 2. `reveal/main.py` (921 lines)

**Purpose:** CLI entry point and output formatting

**Key responsibilities:**
1. Argument parsing
2. URI vs file path routing
3. Output formatting (text, json, grep)
4. Directory tree rendering
5. Structure display
6. Element extraction

**Structure:**
```python
main()                         # Entry point
├─ handle_uri()               # Route URIs to adapters
├─ handle_file()              # Route files to analyzers
├─ show_directory_tree()      # Directory view
├─ show_structure()           # File structure view
├─ show_metadata()            # File metadata
└─ extract_element()          # Element extraction
```

**Key patterns:**

```python
# Output format abstraction
if output_format == 'json':
    print(json.dumps(data))
elif output_format == 'grep':
    # filename:line:content format
else:
    # Human-readable text
```

**Navigator tip:**
```bash
reveal reveal/main.py --outline        # See all functions
reveal reveal/main.py show_structure   # Output formatting logic
reveal reveal/main.py handle_uri       # URI routing (new!)
```

---

### 3. `reveal/treesitter.py` (345 lines)

**Purpose:** Tree-sitter integration for 50+ languages

**Why this matters:** Tree-sitter provides syntactic parsing for languages without writing custom parsers. One base class supports Python, Rust, Go, JavaScript, TypeScript, C, C++, Java, etc.

**Key class:**

```python
class TreeSitterAnalyzer(FileAnalyzer):
    """Base class for tree-sitter based analyzers.

    Subclasses just need to set `language = 'python'`
    and get full parsing for free!
    """

    def get_structure(self):
        """Parse file and extract functions, classes, imports."""
        tree = self.parse_file()
        return self.extract_structure(tree)

    def extract_element(self, element_type, name):
        """Extract specific function/class by name."""
        tree = self.parse_file()
        return self.find_element(tree, element_type, name)
```

**What you get for free:**
- Function extraction
- Class extraction
- Import detection
- Accurate line numbers
- Scope-aware parsing

**Example - Adding Go support:**
```python
# That's it! 3 lines for full Go support
@register('.go', name='Go', icon='🔷')
class GoAnalyzer(TreeSitterAnalyzer):
    language = 'go'
```

**Navigator tip:**
```bash
reveal reveal/treesitter.py --outline
reveal reveal/treesitter.py get_structure    # Core parsing logic
reveal reveal/treesitter.py extract_element  # Element finding
```

---

### 4. `reveal/analyzers/` (14 built-in analyzers)

**Two types of analyzers:**

**A. Tree-sitter based (simple, 10-25 lines each):**
```python
# python.py, rust.py, go.py, javascript.py, typescript.py
@register('.py', name='Python')
class PythonAnalyzer(TreeSitterAnalyzer):
    language = 'python'  # That's all you need!
```

**B. Custom logic (for non-code files, 50-300 lines):**
```python
# markdown.py, nginx.py, dockerfile.py, yaml_json.py, toml.py
@register('.md', name='Markdown')
class MarkdownAnalyzer(FileAnalyzer):
    def get_structure(self):
        # Custom parsing logic
        headings = self.extract_headings()
        links = self.extract_links()
        return {'headings': headings, 'links': links}
```

**When to use which:**
- **Tree-sitter:** Programming languages with syntax trees (Python, Rust, Go, JS, TS, etc.)
- **Custom:** Structured text files (Markdown, YAML, JSON, configs)

**Navigator tip:**
```bash
reveal reveal/analyzers/          # See all analyzers
reveal reveal/analyzers/python.py # Simplest example
reveal reveal/analyzers/nginx.py  # Custom logic example
```

---

### 5. `reveal/adapters/` (URI adapter system - NEW!)

**Purpose:** Explore non-file resources via URIs

**Pattern:**
```python
# adapters/base.py - Protocol definition
class ResourceAdapter(Protocol):
    def get_structure(self) -> Dict: ...
    def extract_element(self, name: str) -> Optional[Dict]: ...
    def get_metadata(self) -> Dict: ...

# adapters/env.py - Concrete implementation
class EnvAdapter(ResourceAdapter):
    """Environment variable exploration."""

    def get_structure(self):
        """Return all environment variables, grouped by category."""
        return self.categorize_env_vars()

    def extract_element(self, name):
        """Get specific environment variable."""
        return os.getenv(name)
```

**Current adapters:**
- `env://` - Environment variables (v0.11.0)

**Coming soon:**
- `postgres://` - PostgreSQL schemas
- `https://` - REST APIs
- `docker://` - Containers

**Navigator tip:**
```bash
reveal reveal/adapters/base.py     # See protocol
reveal reveal/adapters/env.py      # See implementation
```

---

### 6. `reveal/tree_view.py` (105 lines)

**Purpose:** Directory tree rendering

**What it does:**
```bash
$ reveal src/
📁 src/
├── app.py (247 lines, Python)
├── config.py (82 lines, JSON)
└── models/
    ├── user.py (156 lines, Python)
    └── post.py (203 lines, Python)
```

**Key features:**
- File size detection
- File type detection (uses analyzer registry)
- Tree formatting with Unicode box characters
- Depth limiting (`--depth` flag)

---

## 🎨 Key Design Patterns

### Pattern 1: Decorator-Based Registration

**Why:** No central registry file to maintain. Analyzers self-register on import.

```python
# Old approach (brittle)
ANALYZERS = {
    '.py': PythonAnalyzer,
    '.rs': RustAnalyzer,
    # Forgot to add new analyzer? Silent failure!
}

# New approach (self-registering)
@register('.py', name='Python')
class PythonAnalyzer(TreeSitterAnalyzer):
    language = 'python'
    # Automatically registered on import!
```

**Benefits:**
- ✅ No central bottleneck
- ✅ Can't forget to register
- ✅ Easy to add new analyzers
- ✅ Clear metadata (name, icon, extension)

---

### Pattern 2: Progressive Inheritance

**Hierarchy:**
```
FileAnalyzer (base interface)
    │
    ├─ TreeSitterAnalyzer (adds tree-sitter parsing)
    │   │
    │   ├─ PythonAnalyzer (just sets language='python')
    │   ├─ RustAnalyzer (just sets language='rust')
    │   └─ GoAnalyzer (just sets language='go')
    │
    └─ Custom analyzers (implement get_structure + extract_element)
        ├─ MarkdownAnalyzer
        ├─ NginxAnalyzer
        └─ YamlJsonAnalyzer
```

**Why:** Maximize code reuse. Most analyzers are 3-line subclasses!

---

### Pattern 3: Consistent Output Format

**Every analyzer returns the same structure:**

```python
{
    'imports': [
        {'line': 1, 'name': 'import os'},
        {'line': 2, 'name': 'from typing import Dict'},
    ],
    'functions': [
        {'line': 15, 'name': 'load_config', 'signature': '(path: str) -> Dict'},
        {'line': 28, 'name': 'setup_logging', 'signature': '(level: str) -> None'},
    ],
    'classes': [
        {'line': 95, 'name': 'Database'},
        {'line': 145, 'name': 'RequestHandler'},
    ]
}
```

**Benefits:**
- ✅ CLI can format any analyzer output
- ✅ JSON output is predictable
- ✅ Easy to add new output formats
- ✅ Consistent for AI agents

---

### Pattern 4: Path-Based Fallback Detection

**Problem:** Many config files have no extension (nginx sites-available, Apache vhosts)

**Solution:** Check file path patterns

```python
# base.py
def get_analyzer(path):
    # Try extension first
    if path.suffix in ANALYZER_REGISTRY:
        return ANALYZER_REGISTRY[path.suffix]

    # Fallback: check path patterns
    if '/nginx/' in str(path) or '/etc/nginx/' in str(path):
        return NginxAnalyzer

    # Fallback: check shebang
    if has_shebang(path):
        return detect_from_shebang(path)
```

**Examples:**
- `/etc/nginx/sites-available/mytia.net` → NginxAnalyzer (path-based)
- `backup_script` with `#!/bin/bash` → BashAnalyzer (shebang-based)

---

## 🔧 How To...

### Add a New File Type (Tree-Sitter Language)

**Step 1:** Check if tree-sitter supports it
```bash
reveal --list-supported
# Look for your language
```

**Step 2:** Create analyzer (10 lines)
```python
# reveal/analyzers/kotlin.py
from ..base import register
from ..treesitter import TreeSitterAnalyzer

@register('.kt', name='Kotlin', icon='🟣')
class KotlinAnalyzer(TreeSitterAnalyzer):
    """Kotlin file analyzer."""
    language = 'kotlin'
```

**Step 3:** Import in `__init__.py`
```python
# reveal/analyzers/__init__.py
from .kotlin import KotlinAnalyzer
```

**Done!** Full Kotlin support in 10 lines.

---

### Add a Custom Analyzer (Non-Code Files)

**Example:** TOML files

```python
# reveal/analyzers/toml.py
import toml
from ..base import FileAnalyzer, register

@register('.toml', name='TOML', icon='📋')
class TomlAnalyzer(FileAnalyzer):
    """TOML configuration file analyzer."""

    def get_structure(self):
        """Extract TOML sections and keys."""
        data = toml.loads(self.content)

        sections = []
        for section, values in data.items():
            sections.append({
                'line': self.find_section_line(section),
                'name': section,
                'keys': list(values.keys())
            })

        return {'sections': sections}

    def extract_element(self, element_type, name):
        """Extract a specific section."""
        if element_type == 'section':
            # Find and return section content
            ...
```

**Pattern:** Implement `get_structure()` and `extract_element()`.

---

### Add a URI Adapter (Future)

**Example:** PostgreSQL adapter

```python
# reveal/adapters/postgres.py
from .base import ResourceAdapter
import psycopg2

class PostgresAdapter(ResourceAdapter):
    """PostgreSQL database adapter."""

    def __init__(self, uri):
        self.uri = uri
        self.conn = None

    def connect(self):
        """Establish database connection."""
        self.conn = psycopg2.connect(self.uri)

    def get_structure(self):
        """Return all tables in database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        tables = [{'name': row[0]} for row in cursor.fetchall()]
        return {'tables': tables}

    def extract_element(self, name):
        """Get table structure."""
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s
        """, (name,))
        columns = [{'name': r[0], 'type': r[1]} for r in cursor.fetchall()]
        return {'columns': columns}
```

**See:** [ROADMAP.md](../ROADMAP.md) for adapter development timeline

---

## 🧪 Testing Strategy

**Current test structure:**
```
tests/
├── test_python_analyzer.py        # Python-specific tests
├── test_nginx_analyzer.py         # Nginx-specific tests
├── test_toml_analyzer.py          # TOML-specific tests
└── test_core.py                   # Core functionality tests
```

**Pattern for analyzer tests:**
```python
def test_python_structure():
    """Test Python file structure extraction."""
    from reveal.base import get_analyzer

    analyzer = get_analyzer('sample.py')
    structure = analyzer.get_structure()

    assert 'functions' in structure
    assert 'classes' in structure
    assert len(structure['functions']) > 0
```

---

## 📊 Code Metrics

```
Total codebase: ~3,400 lines

Core:
  base.py         378 lines  (registration, base classes)
  main.py         921 lines  (CLI, formatting)
  treesitter.py   345 lines  (tree-sitter integration)
  tree_view.py    105 lines  (directory rendering)

Analyzers: ~1,400 lines (14 analyzers)
  Simple (tree-sitter): 10-25 lines each
  Custom: 50-300 lines each

Adapters: ~200 lines (1 adapter so far)
  env.py          164 lines  (environment variables)
  base.py          36 lines  (adapter protocol)

Tests: ~600 lines
```

**Design philosophy:** Keep analyzers tiny. Most are < 25 lines!

---

## 🎯 Design Decisions

### Why Python?
- Fast prototyping
- Excellent library ecosystem (tree-sitter, database drivers, API clients)
- Native to AI agent environments

### Why Tree-Sitter?
- Supports 50+ languages out of the box
- Syntax-aware (not regex-based)
- Fast incremental parsing
- Active community

### Why Decorator Registration?
- Self-documenting (metadata with code)
- Can't forget to register
- Easy to extend
- Clear ownership

### Why Progressive Disclosure?
- Token efficiency for AI agents
- Faster for humans (don't read full files)
- Composable (structure → detail)

### Why URI Adapters?
- Consistent UX across resource types
- Natural mental model (`file://`, `postgres://`, `https://`)
- Clear protocol boundaries
- Optional dependencies (keep core lightweight)

---

## 🚀 Performance Considerations

### Current Benchmarks

```bash
# Directory tree (1000 files)
$ time reveal src/
# ~50ms (file system scan)

# File structure (500-line Python file)
$ time reveal app.py
# ~100ms (tree-sitter parsing)

# Element extraction
$ time reveal app.py load_config
# ~100ms (parse + extract)
```

**Key optimizations:**
- Lazy parsing (only parse when needed)
- Single file pass (don't re-read)
- Efficient tree traversal (tree-sitter C bindings)

### Future Optimizations

**Considered but not implemented:**
- Caching parsed structures (tradeoff: freshness vs speed)
- Parallel directory scanning (not needed for typical usage)
- Incremental parsing (tree-sitter supports, not exposed yet)

---

## 🔮 Future Architecture

**From ROADMAP.md:**

1. **Metadata System** - Analyzers declare capabilities
   ```python
   @register('.py',
             name='Python',
             element_types=['function', 'class', 'method'],
             features=['outline', 'callers', 'callees'])
   ```

2. **Relationship Tracking** - Show who calls what
   ```bash
   reveal app.py --callers load_config  # What calls this?
   reveal app.py --callees load_config  # What does this call?
   ```

3. **Pattern Detection** - Identify architectural patterns
   ```bash
   reveal app.py --patterns  # Finds: factory pattern, singleton, etc.
   ```

4. **LLM Amplification** - Self-teaching output
   ```
   app.py:15-27 | load_config | used by 3 functions
   💡 Pattern: Configuration loading
   💡 Next: reveal app.py:15 to see implementation
   ```

---

## 📚 Learning Path

**For new contributors:**

1. **Day 1:** Run reveal on itself
   ```bash
   reveal reveal/
   reveal reveal/base.py --outline
   reveal reveal/analyzers/python.py
   ```

2. **Day 2:** Add a tree-sitter analyzer
   - Pick a language from `reveal --list-supported`
   - Create 10-line analyzer
   - Test it

3. **Day 3:** Study a custom analyzer
   - Read `reveal/analyzers/markdown.py`
   - Understand get_structure + extract_element pattern
   - Try adding a feature

4. **Week 2:** Build a custom analyzer
   - Pick a file format (CSV, XML, INI, etc.)
   - Implement FileAnalyzer interface
   - Add tests
   - Submit PR!

---

## 🤝 Contributing to Architecture

**Want to improve the architecture?**

1. **Open an issue** with `[Architecture]` tag
2. **Explain the problem** - What's hard? What's inefficient?
3. **Propose a solution** - Show examples, consider tradeoffs
4. **Discuss** - Maintainers and community weigh in
5. **Prototype** - Build a proof of concept
6. **PR** - Submit with tests and docs

**Good architecture proposals include:**
- **Problem:** Clear description of pain point
- **Solution:** Concrete design (with code examples)
- **Tradeoffs:** What do we gain? What do we lose?
- **Migration:** How do existing analyzers adapt?
- **Testing:** How do we validate it works?

---

## 📖 Related Documentation

- [ROADMAP.md](../ROADMAP.md) - Where we're going
- [DEVELOPMENT.md](DEVELOPMENT.md) - How to write analyzers
- [CONTRIBUTING.md](../CONTRIBUTING.md) - How to contribute
- [CHANGELOG.md](../CHANGELOG.md) - What we've shipped

---

**Last updated:** 2025-11-27
**For version:** v0.11.0
**Codebase size:** ~3,400 lines
