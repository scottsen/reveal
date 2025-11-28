# Contributing to reveal

Thank you for your interest in contributing to `reveal`! This project is designed to grow through community contributions, especially new file type analyzers.

## Ways to Contribute

### 1. Add New File Type Analyzers 🔌

**This is the easiest and most impactful way to contribute!**

**For programming languages** (uses tree-sitter, 10 lines of code):

```python
# reveal/analyzers/kotlin.py
from ..base import register
from ..treesitter import TreeSitterAnalyzer

@register('.kt', name='Kotlin', icon='🟣')
class KotlinAnalyzer(TreeSitterAnalyzer):
    """Kotlin file analyzer."""
    language = 'kotlin'
```

**For structured text files** (custom logic, 50-200 lines):

```python
# reveal/analyzers/ini.py
from ..base import FileAnalyzer, register

@register('.ini', name='INI', icon='📋')
class IniAnalyzer(FileAnalyzer):
    """INI configuration file analyzer."""

    def get_structure(self):
        # Extract sections and keys
        ...

    def extract_element(self, element_type, name):
        # Extract specific section
        ...
```

**See:** [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for complete guide with examples.

### 2. Improve Existing Analyzers

- Make them faster
- Add more detailed structure extraction
- Improve output formatting
- Add better error handling

### 3. Add Features

- Syntax highlighting
- Export to different formats
- Integration with editors/IDEs
- Performance improvements

### 4. Documentation

- Improve README
- Write tutorials
- Add examples
- Document AI integration patterns

### 5. Bug Reports & Feature Requests

Open an issue with:
- Clear description
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Your environment (OS, Python version)

## Development Setup

```bash
# Clone and install in development mode
cd ~/src/projects/reveal
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black reveal/
ruff check reveal/

# Run specific test
pytest tests/test_plugin_loader.py -v
```

## Analyzer Development Workflow

1. **Check tree-sitter support:** Run `reveal --list-supported` to see if your language is already available
2. **Create analyzer file** in `reveal/analyzers/your_filetype.py`
3. **Register it** in `reveal/analyzers/__init__.py` by importing your analyzer class
4. **Add tests** in `tests/test_your_filetype.py`
5. **Add validation sample** in `validation_samples/sample.your_ext`
6. **Update README** - add to supported types list
7. **Submit PR** with examples

**Complete guide:** See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for step-by-step instructions

## Code Style

- **Python**: Follow PEP 8, use `black` for formatting
- **Line length**: 100 characters
- **Type hints**: Use them for public APIs
- **Docstrings**: Google style
- **Comments**: Explain *why*, not *what*

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=reveal --cov-report=html

# Test specific analyzer
pytest tests/test_python_analyzer.py -v
```

### Writing Tests

```python
def test_python_structure_analyzer():
    """Test Python structure analysis"""
    from reveal.analyzers.python_analyzer import PythonStructureAnalyzer

    analyzer = PythonStructureAnalyzer()
    result = analyzer.analyze("test_files/sample.py")

    assert "imports" in result
    assert len(result["classes"]) == 2
    assert "UserManager" in result["classes"]
```

## Commit Messages

Use conventional commits:

```
feat: add Rust file type plugin
fix: handle binary files in metadata analyzer
docs: improve plugin development guide
test: add C header analyzer tests
refactor: simplify plugin loader logic
```

## Pull Request Process

1. **Fork** the repository
2. **Create branch**: `git checkout -b feature/rust-plugin`
3. **Make changes** with clear commits
4. **Add tests** that pass
5. **Update docs** if needed
6. **Submit PR** with clear description

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] New file type plugin
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Performance improvement

## Testing
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Tested with example files

## Checklist
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

## Community

- **Questions?** Open a discussion
- **Ideas?** Open an issue with `[Idea]` tag
- **Stuck?** Ask for help in your PR

## Priority Areas

**Most wanted analyzers:**
- CSV/Excel (.csv, .xlsx) - Data file exploration
- SQL (.sql) - SQL script parsing
- Terraform (.tf) - Infrastructure as code
- Protocol Buffers (.proto) - API definitions
- GraphQL (.graphql) - Schema exploration
- XML (.xml) - Structured data
- Kotlin (.kt) - Android development
- Swift (.swift) - iOS development
- Java (.java) - Enterprise apps

**Most wanted features:**
- Call graph analysis (who calls what)
- Relationship tracking (imports, dependencies)
- Pattern detection (design patterns)
- Enhanced outline mode
- Better error messages
- Performance improvements

**Future: URI adapters** - See [ROADMAP.md](ROADMAP.md)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be listed in:
- README.md contributors section
- Release notes
- Plugin credits (for plugin authors)

---

**Thank you for making `reveal` better for the agentic AI community!** 🎉
