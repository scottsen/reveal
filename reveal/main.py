"""Clean, simple CLI for reveal."""

import sys
import os
import argparse
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from .base import get_analyzer, get_all_analyzers, FileAnalyzer
from .tree_view import show_directory_tree
from . import __version__

# AI Agent Best Practices - exposed via --recommend-prompt
RECOMMENDED_PROMPT = """# Reveal - Semantic Code Explorer Best Practices

## Core Concept: Progressive Disclosure (Orient → Navigate → Focus)

Never read entire files blindly. Use reveal's semantic navigation for token efficiency.

### The Pattern (ALWAYS follow this order):

1. **ORIENT** - What exists?
   ```bash
   reveal .                    # Directory tree
   reveal file.py --outline    # File structure overview
   ```

2. **NAVIGATE** - What's relevant?
   ```bash
   reveal file.py --head 10    # First 10 functions (NEW in v0.12!)
   reveal file.py --tail 5     # Last 5 functions (bugs cluster here!)
   reveal file.py --check      # Code quality checks
   ```

3. **FOCUS** - Get details
   ```bash
   reveal file.py function_name  # Extract specific function
   ```

### Token Efficiency Examples

**❌ BAD - Traditional approach:**
```bash
# Read entire 500-line file = ~7,500 tokens
cat large_file.py
```

**✅ GOOD - Reveal approach:**
```bash
# 1. See structure (50 tokens)
reveal large_file.py --outline

# 2. Navigate to relevant area (300 tokens)
reveal large_file.py --tail 5

# 3. Extract what you need (200 tokens)
reveal large_file.py problematic_function

# Total: ~550 tokens = 13x more efficient!
```

### When to Use What

**Use `reveal <dir>/` for:**
- Initial project exploration
- Understanding codebase structure
- Finding relevant files

**Use `reveal file.py --outline` for:**
- Unknown files (don't know what's in them)
- Large files (>200 lines)
- Understanding file organization

**Use `reveal file.py --head/--tail/--range` for:**
- Targeting specific areas (bugs often cluster at end of files)
- Iterative deepening (explore progressively)
- Token budget constraints

**Use `reveal file.py --check` for:**
- Finding code quality issues
- Identifying complex functions
- Code review workflows

**Use `reveal file.py element_name` for:**
- Extracting specific functions/classes
- Focused code reading
- After you've oriented and navigated

### Integration with Other Tools

**With AST scanners:**
```bash
# Scanner identifies issues with line numbers
tia ast scan complexity .

# Use reveal to explore the problem files
reveal problematic_file.py --outline
reveal problematic_file.py --tail 5
reveal problematic_file.py bad_function
```

**With grep/search:**
```bash
# Find files
grep -r "pattern" . --files-with-matches

# Explore structure
reveal file.py --outline

# Navigate to area
reveal file.py --head 10
```

### Output Formats

**Text (default):** Human-readable, perfect for quick exploration
**JSON (--format=json):** Scriptable, pipe to jq for filtering
**Grep (--format=grep):** Pipeable, works with vim/git/awk

```bash
# JSON + jq for advanced filtering
reveal file.py --format=json | jq '.structure.functions[] | select(.line_count > 50)'

# Grep format for vim integration
reveal file.py --format=grep | grep "async"
```

### Common Anti-Patterns to Avoid

❌ **DON'T read files before revealing:**
```bash
cat file.py  # Wastes tokens!
```

✅ **DO reveal first:**
```bash
reveal file.py --outline  # See what's there
reveal file.py func       # Then extract what you need
```

❌ **DON'T guess what's in a file:**
```bash
# Assuming structure without checking
```

✅ **DO discover structure first:**
```bash
reveal file.py --outline  # Know before you act
```

❌ **DON'T read full files for one function:**
```bash
cat 500_line_file.py  # Just to see one function
```

✅ **DO extract specifically:**
```bash
reveal file.py --outline           # Find the function
reveal file.py specific_function   # Extract only what you need
```

### Real-World Workflow Example

**Task:** Find and fix a bug in a large codebase

```bash
# 1. ORIENT - Understand structure
reveal src/

# 2. NAVIGATE - Find relevant file
reveal src/problematic_module.py --outline

# 3. NAVIGATE - Target area where bugs cluster
reveal src/problematic_module.py --tail 5

# 4. FOCUS - Extract the problem function
reveal src/problematic_module.py buggy_function

# Total tokens: ~1,000 vs. ~15,000 for reading all files
# Result: 15x token efficiency!
```

### Best Practices Summary

1. **Always start with --outline** for unknown files
2. **Use --head/--tail for large files** before reading fully
3. **Extract specific elements** instead of reading entire files
4. **Combine with jq** for powerful filtering (--format=json)
5. **Use --check** for code quality checks
6. **Progressive disclosure** = Orient → Navigate → Focus

### Version Notes

- v0.11: Added URI adapters (env://)
- v0.12: Added semantic navigation (--head, --tail, --range)
- v0.13: Added pattern detectors (--check replaces --sloppy)

### Learn More

```bash
reveal --help                    # Full help
reveal --list-supported          # See all supported file types
reveal --recommend-prompt        # This message
```

Remember: Reveal is about **semantic understanding**, not raw text. Think in terms of **functions, classes, sections** - not lines.
"""


# ============================================================================
# Breadcrumb System - Agent-Friendly Navigation Hints
# ============================================================================

def get_element_placeholder(file_type):
    """Get appropriate element placeholder for file type.

    Args:
        file_type: File type string (e.g., 'python', 'yaml')

    Returns:
        String placeholder like '<function>', '<key>', etc.
    """
    mapping = {
        'python': '<function>',
        'javascript': '<function>',
        'typescript': '<function>',
        'rust': '<function>',
        'go': '<function>',
        'bash': '<function>',
        'gdscript': '<function>',
        'yaml': '<key>',
        'json': '<key>',
        'jsonl': '<entry>',
        'toml': '<key>',
        'markdown': '<heading>',
        'dockerfile': '<instruction>',
        'nginx': '<directive>',
        'jupyter': '<cell>',
    }
    return mapping.get(file_type, '<element>')


def get_file_type_from_analyzer(analyzer):
    """Get file type string from analyzer class name.

    Args:
        analyzer: FileAnalyzer instance

    Returns:
        File type string (e.g., 'python', 'markdown') or None
    """
    class_name = type(analyzer).__name__
    mapping = {
        'PythonAnalyzer': 'python',
        'JavaScriptAnalyzer': 'javascript',
        'TypeScriptAnalyzer': 'typescript',
        'RustAnalyzer': 'rust',
        'GoAnalyzer': 'go',
        'BashAnalyzer': 'bash',
        'MarkdownAnalyzer': 'markdown',
        'YamlAnalyzer': 'yaml',
        'JsonAnalyzer': 'json',
        'JsonlAnalyzer': 'jsonl',
        'TomlAnalyzer': 'toml',
        'DockerfileAnalyzer': 'dockerfile',
        'NginxAnalyzer': 'nginx',
        'GDScriptAnalyzer': 'gdscript',
        'JupyterAnalyzer': 'jupyter',
        'TreeSitterAnalyzer': None,  # Generic fallback
    }
    return mapping.get(class_name, None)


def print_breadcrumbs(context, path, file_type=None, **kwargs):
    """Print navigation breadcrumbs with reveal command suggestions.

    Args:
        context: 'structure', 'element', 'metadata'
        path: File or directory path
        file_type: Optional file type for context-specific suggestions
        **kwargs: Additional context (element_name, line_count, etc.)
    """
    print()  # Blank line before breadcrumbs

    if context == 'metadata':
        print(f"Next: reveal {path}              # See structure")
        print(f"      reveal {path} --check      # Quality check")

    elif context == 'structure':
        element_placeholder = get_element_placeholder(file_type)
        print(f"Next: reveal {path} {element_placeholder}   # Extract specific element")

        if file_type in ['python', 'javascript', 'typescript', 'rust', 'go', 'bash', 'gdscript']:
            print(f"      reveal {path} --check      # Check code quality")
            print(f"      reveal {path} --outline    # Nested structure")
        elif file_type == 'markdown':
            print(f"      reveal {path} --links      # Extract links")
            print(f"      reveal {path} --code       # Extract code blocks")
        elif file_type in ['yaml', 'json', 'toml', 'jsonl']:
            print(f"      reveal {path} --check      # Validate syntax")
        elif file_type in ['dockerfile', 'nginx']:
            print(f"      reveal {path} --check      # Validate configuration")

    elif context == 'element':
        element_name = kwargs.get('element_name', '')
        line_count = kwargs.get('line_count', '')

        info = f"Extracted {element_name}"
        if line_count:
            info += f" ({line_count} lines)"

        print(info)
        print(f"  → Back: reveal {path}          # See full structure")
        print(f"  → Check: reveal {path} --check # Quality analysis")


def check_for_updates():
    """Check PyPI for newer version (once per day, non-blocking).

    - Checks at most once per day (cached in ~/.config/reveal/last_update_check)
    - 1-second timeout (doesn't slow down CLI)
    - Fails silently (no errors shown to user)
    - Opt-out: Set REVEAL_NO_UPDATE_CHECK=1 environment variable
    """
    # Opt-out check
    if os.environ.get('REVEAL_NO_UPDATE_CHECK'):
        return

    try:
        # Setup cache directory (platform-appropriate)
        if sys.platform == 'win32':
            # Windows: Use %LOCALAPPDATA%\reveal
            cache_dir = Path(os.getenv('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / 'reveal'
        else:
            # Unix/macOS: Use ~/.config/reveal
            cache_dir = Path.home() / '.config' / 'reveal'
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / 'last_update_check'

        # Check if we should update (once per day)
        if cache_file.exists():
            last_check_str = cache_file.read_text().strip()
            try:
                last_check = datetime.fromisoformat(last_check_str)
                if datetime.now() - last_check < timedelta(days=1):
                    return  # Checked recently, skip
            except (ValueError, OSError):
                pass  # Invalid cache, continue with check

        # Check PyPI (using urllib to avoid new dependencies)
        import urllib.request
        import json

        req = urllib.request.Request(
            'https://pypi.org/pypi/reveal-cli/json',
            headers={'User-Agent': f'reveal-cli/{__version__}'}
        )

        with urllib.request.urlopen(req, timeout=1) as response:
            data = json.loads(response.read().decode('utf-8'))
            latest_version = data['info']['version']

        # Update cache file
        cache_file.write_text(datetime.now().isoformat())

        # Compare versions (simple string comparison works for semver)
        if latest_version != __version__:
            # Parse versions for proper comparison
            def parse_version(v):
                return tuple(map(int, v.split('.')))

            try:
                if parse_version(latest_version) > parse_version(__version__):
                    print(f"⚠️  Update available: reveal {latest_version} (you have {__version__})")
                    print(f"Update available: pip install --upgrade reveal-cli\n")
            except (ValueError, AttributeError):
                pass  # Version comparison failed, ignore

    except Exception:
        # Fail silently - don't interrupt user's workflow
        pass


def main():
    """Main CLI entry point."""
    # Fix Windows console encoding for emoji/unicode support
    if sys.platform == 'win32':
        # Set environment variable for subprocess compatibility
        os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
        # Reconfigure stdout/stderr to use UTF-8 with error handling
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    _main_impl()


def handle_uri(uri: str, element: Optional[str], args) -> None:
    """Handle URI-based resources (env://, https://, etc.).

    Args:
        uri: Full URI (e.g., env://, env://PATH)
        element: Optional element to extract
        args: Parsed command line arguments
    """
    # Parse URI
    if '://' not in uri:
        print(f"Error: Invalid URI format: {uri}", file=sys.stderr)
        sys.exit(1)

    scheme, resource = uri.split('://', 1)

    # Route to appropriate adapter
    if scheme == 'env':
        from .adapters.env import EnvAdapter
        adapter = EnvAdapter()

        if element or resource:
            # Get specific variable (element takes precedence)
            var_name = element if element else resource
            result = adapter.get_element(var_name, show_secrets=False)

            if result is None:
                print(f"Error: Environment variable '{var_name}' not found", file=sys.stderr)
                sys.exit(1)

            render_env_variable(result, args.format)
        else:
            # Get all variables
            result = adapter.get_structure(show_secrets=False)
            render_env_structure(result, args.format)

    else:
        print(f"Error: Unsupported URI scheme: {scheme}://", file=sys.stderr)
        print(f"Supported schemes: env://", file=sys.stderr)
        sys.exit(1)


def render_env_structure(data: Dict[str, Any], output_format: str) -> None:
    """Render environment variables structure.

    Args:
        data: Environment data from adapter
        output_format: Output format (text, json, grep)
    """
    if output_format == 'json':
        import json
        print(json.dumps(data, indent=2))
        return

    # Text format
    print(f"Environment Variables ({data['total_count']})")
    print()

    for category, variables in data['categories'].items():
        if not variables:
            continue

        print(f"{category} ({len(variables)}):")
        for var in variables:
            sensitive_marker = " (sensitive)" if var['sensitive'] else ""
            if output_format == 'grep':
                # grep format: env://VAR_NAME:value
                print(f"env://{var['name']}:{var['value']}")
            else:
                # text format
                print(f"  {var['name']:<30s} {var['value']}{sensitive_marker}")
        print()


def render_env_variable(data: Dict[str, Any], output_format: str) -> None:
    """Render single environment variable.

    Args:
        data: Variable data from adapter
        output_format: Output format (text, json, grep)
    """
    if output_format == 'json':
        import json
        print(json.dumps(data, indent=2))
        return

    if output_format == 'grep':
        print(f"env://{data['name']}:{data['value']}")
        return

    # Text format
    print(f"Environment Variable: {data['name']}")
    print(f"Category: {data['category']}")
    print(f"Value: {data['value']}")
    if data['sensitive']:
        print(f"⚠️  Sensitive: This variable appears to contain sensitive data")
        print(f"    Use --show-secrets to display actual value")
    print(f"Length: {data['length']} characters")


def _build_help_epilog() -> str:
    """Build dynamic help with conditional jq examples."""
    import shutil

    has_jq = shutil.which('jq') is not None

    base_help = '''
Examples:
  # Basic structure exploration
  reveal src/                    # Directory tree
  reveal app.py                  # Show structure with metrics
  reveal app.py --meta           # File metadata

  # Semantic navigation - iterative deepening! (NEW in v0.12!)
  reveal conversation.jsonl --head 10    # First 10 records
  reveal conversation.jsonl --tail 5     # Last 5 records
  reveal conversation.jsonl --range 48-52 # Records 48-52 (1-indexed)
  reveal app.py --head 5                 # First 5 functions
  reveal doc.md --tail 3                 # Last 3 headings

  # Code quality checks (pattern detectors)
  reveal main.py --check         # Run all quality checks
  reveal main.py --check --select=B,S  # Select specific categories
  reveal Dockerfile --check      # Docker best practices

  # Hierarchical outline (see structure as a tree!)
  reveal app.py --outline        # Classes with methods, nested structures
  reveal app.py --outline --check    # Outline with quality checks

  # Element extraction
  reveal app.py load_config      # Extract specific function
  reveal app.py Database         # Extract class definition
  reveal conversation.jsonl 42   # Extract record #42

  # Output formats
  reveal app.py --format=json    # JSON for scripting
  reveal app.py --format=grep    # Pipeable format

  # Pipeline workflows (Unix composability!)
  find src/ -name "*.py" | reveal --stdin --check
  git diff --name-only | reveal --stdin --outline
  git ls-files "*.ts" | reveal --stdin --format=json
  ls src/*.py | reveal --stdin
'''

    if has_jq:
        base_help += '''
  # Semantic navigation + jq (token-efficient exploration!)
  reveal conversation.jsonl --tail 10 --format=json | jq '.structure.records[] | select(.name | contains("user"))'
  reveal app.py --head 20 --format=json | jq '.structure.functions[] | select(.line_count > 30)'
  reveal log.jsonl --range 100-150 --format=json | jq '.structure.records[] | select(.name | contains("error"))'

  # Advanced filtering with jq (powerful!)
  reveal app.py --format=json | jq '.structure.functions[] | select(.line_count > 100)'
  reveal app.py --format=json | jq '.structure.functions[] | select(.depth > 3)'
  reveal app.py --format=json | jq '.structure.functions[] | select(.line_count > 50 and .depth > 2)'
  reveal src/**/*.py --format=json | jq -r '.structure.functions[] | "\\(.file):\\(.line) \\(.name) [\\(.line_count) lines]"'

  # Pipeline + jq (combine the power!)
  find . -name "*.py" | reveal --stdin --format=json | jq '.structure.functions[] | select(.line_count > 100)'
  git diff --name-only | grep "\\.py$" | reveal --stdin --check --format=grep
'''

    base_help += '''
  # Markdown-specific features
  reveal doc.md --links                       # Extract all links
  reveal doc.md --links --link-type external  # Only external links
  reveal doc.md --code                        # Extract all code blocks
  reveal doc.md --code --language python      # Only Python code blocks

  # URI adapters - explore ANY resource! (NEW in v0.11!)
  reveal env://                               # Show all environment variables
  reveal env://PATH                           # Get specific variable
  reveal env://DATABASE_URL                   # Check database config
  reveal env:// --format=json | jq '.categories.Python'  # Filter Python vars

File-type specific features:
  • Markdown: --links, --code (extract links/code blocks with filtering)
  • Code files: --check, --outline (quality checks, show hierarchical structure)
  • URI adapters: env:// (environment variables) - more coming soon!

Perfect filename:line format - works with vim, git, grep, sed, awk!
Metrics: All code files show [X lines, depth:Y] for complexity analysis
stdin: Reads file paths from stdin (one per line) - works with find, git, ls, etc.
'''

    return base_help


def _main_impl():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Reveal: Explore code semantically - The simplest way to understand code',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_build_help_epilog()
    )

    parser.add_argument('path', nargs='?', help='File or directory to reveal')
    parser.add_argument('element', nargs='?', help='Element to extract (function, class, etc.)')

    # Optional flags
    parser.add_argument('--version', action='version', version=f'reveal {__version__}')
    parser.add_argument('--list-supported', '-l', action='store_true',
                        help='List all supported file types')
    parser.add_argument('--recommend-prompt', action='store_true',
                        help='Show AI agent best practices for using reveal efficiently')
    parser.add_argument('--agent-help', action='store_true',
                        help='Show agent usage guide (llms.txt-style brief reference)')
    parser.add_argument('--agent-help-full', action='store_true',
                        help='Show comprehensive agent guide (complete examples, patterns, troubleshooting)')
    parser.add_argument('--stdin', action='store_true',
                        help='Read file paths from stdin (one per line) - enables Unix pipeline workflows')
    parser.add_argument('--meta', action='store_true', help='Show metadata only')
    parser.add_argument('--format', choices=['text', 'json', 'grep'], default='text',
                        help='Output format (text, json, grep)')
    parser.add_argument('--no-fallback', action='store_true',
                        help='Disable TreeSitter fallback for unknown file types')
    parser.add_argument('--depth', type=int, default=3, help='Directory tree depth (default: 3)')
    parser.add_argument('--max-entries', type=int, default=200,
                        help='Maximum entries to show in directory tree (default: 200, 0=unlimited)')
    parser.add_argument('--fast', action='store_true',
                        help='Fast mode: skip line counting for better performance')
    parser.add_argument('--outline', action='store_true',
                        help='Show hierarchical outline (classes with methods, nested structures)')

    # Pattern Detection (v0.13.0+) - Industry-aligned linting
    parser.add_argument('--check', '--lint', action='store_true',
                        help='Run pattern detectors (code quality, security, complexity checks)')
    parser.add_argument('--select', type=str, metavar='RULES',
                        help='Select specific rules or categories (e.g., "B,S" or "B001,S701")')
    parser.add_argument('--ignore', type=str, metavar='RULES',
                        help='Ignore specific rules or categories (e.g., "E501" or "C")')
    parser.add_argument('--rules', action='store_true',
                        help='List all available pattern detection rules')
    parser.add_argument('--explain', type=str, metavar='CODE',
                        help='Explain a specific rule (e.g., "B001")')

    # Semantic navigation (head/tail/range)
    parser.add_argument('--head', type=int, metavar='N',
                        help='Show first N semantic units (records, functions, sections)')
    parser.add_argument('--tail', type=int, metavar='N',
                        help='Show last N semantic units (records, functions, sections)')
    parser.add_argument('--range', type=str, metavar='START-END',
                        help='Show semantic units in range (e.g., 10-20, 1-indexed)')

    # Markdown entity filters
    parser.add_argument('--links', action='store_true',
                        help='Extract links from markdown files')
    parser.add_argument('--link-type', choices=['internal', 'external', 'email', 'all'],
                        help='Filter links by type (requires --links)')
    parser.add_argument('--domain', type=str,
                        help='Filter links by domain (requires --links)')

    parser.add_argument('--code', action='store_true',
                        help='Extract code blocks from markdown files')
    parser.add_argument('--language', type=str,
                        help='Filter code blocks by language (requires --code)')
    parser.add_argument('--inline', action='store_true',
                        help='Include inline code snippets (requires --code)')

    args = parser.parse_args()

    # Validate navigation arguments (mutually exclusive)
    nav_args = [args.head, args.tail, args.range]
    nav_count = sum(1 for arg in nav_args if arg is not None)
    if nav_count > 1:
        print("Error: --head, --tail, and --range are mutually exclusive", file=sys.stderr)
        sys.exit(1)

    # Parse and validate range if provided
    if args.range:
        try:
            start, end = args.range.split('-')
            start, end = int(start), int(end)
            if start < 1 or end < 1:
                raise ValueError("Range must be 1-indexed (start from 1)")
            if start > end:
                raise ValueError("Range start must be <= end")
            # Store parsed range as tuple for easy access
            args.range = (start, end)
        except ValueError as e:
            print(f"Error: Invalid range format '{args.range}': {e}", file=sys.stderr)
            print("Expected format: START-END (e.g., 10-20, 1-indexed)", file=sys.stderr)
            sys.exit(1)

    # Check for updates (once per day, non-blocking, opt-out available)
    check_for_updates()

    # Handle --list-supported
    if args.list_supported:
        list_supported_types()
        sys.exit(0)

    # Handle --recommend-prompt
    if args.recommend_prompt:
        print(RECOMMENDED_PROMPT)
        sys.exit(0)

    # Handle --agent-help
    if args.agent_help:
        agent_help_path = Path(__file__).parent / 'AGENT_HELP.md'
        try:
            with open(agent_help_path, 'r', encoding='utf-8') as f:
                print(f.read())
        except FileNotFoundError:
            print(f"Error: AGENT_HELP.md not found at {agent_help_path}", file=sys.stderr)
            print("This is a bug - please report it at https://github.com/scottsen/reveal/issues", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    # Handle --agent-help-full
    if args.agent_help_full:
        agent_help_full_path = Path(__file__).parent / 'AGENT_HELP_FULL.md'
        try:
            with open(agent_help_full_path, 'r', encoding='utf-8') as f:
                print(f.read())
        except FileNotFoundError:
            print(f"Error: AGENT_HELP_FULL.md not found at {agent_help_full_path}", file=sys.stderr)
            print("This is a bug - please report it at https://github.com/scottsen/reveal/issues", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    # Handle --rules (list all pattern detection rules)
    if args.rules:
        from .rules import RuleRegistry
        rules = RuleRegistry.list_rules()

        if not rules:
            print("No rules discovered")
            sys.exit(0)

        print(f"Reveal v{__version__} - Pattern Detection Rules\n")

        # Group by category
        by_category = {}
        for rule in rules:
            cat = rule['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(rule)

        # Print by category
        for category in sorted(by_category.keys()):
            cat_rules = by_category[category]
            print(f"{category.upper()} Rules ({len(cat_rules)}):")
            for rule in sorted(cat_rules, key=lambda r: r['code']):
                status = "✓" if rule['enabled'] else "✗"
                severity_icon = {"low": "ℹ️", "medium": "⚠️", "high": "❌", "critical": "🚨"}.get(rule['severity'], "")
                print(f"  {status} {rule['code']:8s} {severity_icon} {rule['message']}")
                if rule['file_patterns'] != ['*']:
                    print(f"             Files: {', '.join(rule['file_patterns'])}")
            print()

        print(f"Total: {len(rules)} rules")
        print("\nUsage: reveal <file> --check --select B,S --ignore E501")
        sys.exit(0)

    # Handle --explain (explain a specific rule)
    if args.explain:
        from .rules import RuleRegistry
        rule = RuleRegistry.get_rule(args.explain)

        if not rule:
            print(f"Error: Rule '{args.explain}' not found", file=sys.stderr)
            print("\nUse 'reveal --rules' to list all available rules", file=sys.stderr)
            sys.exit(1)

        print(f"Rule: {rule.code}")
        print(f"Message: {rule.message}")
        print(f"Category: {rule.category.value if rule.category else 'unknown'}")
        print(f"Severity: {rule.severity.value}")
        print(f"File Patterns: {', '.join(rule.file_patterns)}")
        if rule.uri_patterns:
            print(f"URI Patterns: {', '.join(rule.uri_patterns)}")
        print(f"Version: {rule.version}")
        print(f"Enabled: {'Yes' if rule.enabled else 'No'}")
        print(f"\nDescription:")
        print(f"  {rule.__doc__ or 'No description available.'}")
        sys.exit(0)

    # Handle --stdin (read file paths from stdin)
    if args.stdin:
        if args.element:
            print("Error: Cannot use element extraction with --stdin", file=sys.stderr)
            sys.exit(1)

        # Read file paths from stdin (one per line)
        for line in sys.stdin:
            file_path = line.strip()
            if not file_path:
                continue  # Skip empty lines

            path = Path(file_path)

            # Skip if path doesn't exist (graceful degradation)
            if not path.exists():
                print(f"Warning: {file_path} not found, skipping", file=sys.stderr)
                continue

            # Skip directories (only process files)
            if path.is_dir():
                print(f"Warning: {file_path} is a directory, skipping (use reveal {file_path}/ directly)", file=sys.stderr)
                continue

            # Process the file
            if path.is_file():
                handle_file(str(path), None, args.meta, args.format, args)

        sys.exit(0)

    # Path is required if not using --list-supported, --recommend-prompt, or --stdin
    if not args.path:
        parser.print_help()
        sys.exit(1)

    # Check if this is a URI (scheme://)
    if '://' in args.path:
        handle_uri(args.path, args.element, args)
        sys.exit(0)

    # Regular file/directory path
    path = Path(args.path)
    if not path.exists():
        print(f"Error: {args.path} not found", file=sys.stderr)
        sys.exit(1)

    # Route based on path type
    if path.is_dir():
        # Directory → show tree
        output = show_directory_tree(str(path), depth=args.depth,
                                     max_entries=args.max_entries, fast=args.fast)
        print(output)

    elif path.is_file():
        # File → show structure or extract element
        handle_file(str(path), args.element, args.meta, args.format, args)

    else:
        print(f"Error: {args.path} is neither file nor directory", file=sys.stderr)
        sys.exit(1)


def list_supported_types():
    """List all supported file types."""
    analyzers = get_all_analyzers()

    if not analyzers:
        print("No file types registered")
        return

    print(f"Reveal v{__version__} - Supported File Types\n")

    # Sort by name for nice display
    sorted_analyzers = sorted(analyzers.items(), key=lambda x: x[1]['name'])

    print("Built-in Analyzers:")
    for ext, info in sorted_analyzers:
        name = info['name']
        print(f"  {name:20s} {ext}")

    print(f"\nTotal: {len(analyzers)} file types with full support")

    # Probe tree-sitter for additional languages
    try:
        import warnings
        warnings.filterwarnings('ignore', category=FutureWarning, module='tree_sitter')

        from tree_sitter_languages import get_language

        # Common languages to check (extension -> language name mapping)
        fallback_languages = {
            '.java': ('java', 'Java'),
            '.c': ('c', 'C'),
            '.cpp': ('cpp', 'C++'),
            '.cc': ('cpp', 'C++'),
            '.cxx': ('cpp', 'C++'),
            '.h': ('c', 'C/C++ Header'),
            '.hpp': ('cpp', 'C++ Header'),
            '.cs': ('c_sharp', 'C#'),
            '.rb': ('ruby', 'Ruby'),
            '.php': ('php', 'PHP'),
            '.swift': ('swift', 'Swift'),
            '.kt': ('kotlin', 'Kotlin'),
            '.scala': ('scala', 'Scala'),
            '.lua': ('lua', 'Lua'),
            '.hs': ('haskell', 'Haskell'),
            '.elm': ('elm', 'Elm'),
            '.ocaml': ('ocaml', 'OCaml'),
            '.ml': ('ocaml', 'OCaml'),
        }

        # Filter out languages already registered
        available_fallbacks = []
        for ext, (lang, display_name) in fallback_languages.items():
            if ext not in analyzers:  # Not already registered
                try:
                    get_language(lang)
                    available_fallbacks.append((display_name, ext))
                except Exception:
                    # Language not available in tree-sitter-languages, skip it
                    pass

        if available_fallbacks:
            print("\nTree-Sitter Auto-Supported (basic):")
            for name, ext in sorted(available_fallbacks):
                print(f"  {name:20s} {ext}")
            print(f"\nTotal: {len(available_fallbacks)} additional languages via fallback")
            print("Note: These work automatically but may have basic support.")
            print("Note: Contributions for full analyzers welcome!")

    except Exception:
        # tree-sitter-languages not available or probe failed
        pass

    print(f"\nUsage: reveal <file>")
    print(f"Help: reveal --help")


def run_pattern_detection(analyzer: FileAnalyzer, path: str, output_format: str, args):
    """Run pattern detection rules on a file.

    Args:
        analyzer: File analyzer instance
        path: File path
        output_format: Output format ('text', 'json', 'grep')
        args: CLI arguments (for --select, --ignore)
    """
    from .rules import RuleRegistry

    # Parse select/ignore options
    select = args.select.split(',') if args.select else None
    ignore = args.ignore.split(',') if args.ignore else None

    # Get structure and content
    structure = analyzer.get_structure()
    content = analyzer.content

    # Run rules
    detections = RuleRegistry.check_file(path, structure, content, select=select, ignore=ignore)

    # Output results
    if output_format == 'json':
        import json
        result = {
            'file': path,
            'detections': [d.to_dict() for d in detections],
            'total': len(detections)
        }
        print(json.dumps(result, indent=2))

    elif output_format == 'grep':
        # Grep format: file:line:column:code:message
        for d in detections:
            print(f"{d.file_path}:{d.line}:{d.column}:{d.rule_code}:{d.message}")

    else:  # text
        if not detections:
            print(f"{path}: ✅ No issues found")
        else:
            print(f"{path}: Found {len(detections)} issues\n")
            for d in sorted(detections, key=lambda x: (x.line, x.column)):
                print(d)
                print()  # Blank line between detections


def handle_file(path: str, element: Optional[str], show_meta: bool, output_format: str, args=None):
    """Handle file analysis.

    Args:
        path: File path
        element: Optional element to extract
        show_meta: Whether to show metadata only
        output_format: Output format ('text', 'json', 'grep')
        args: Full argument namespace (for filter options)
    """
    # Get analyzer
    # Check fallback setting
    allow_fallback = not getattr(args, 'no_fallback', False) if args else True

    analyzer_class = get_analyzer(path, allow_fallback=allow_fallback)
    if not analyzer_class:
        ext = Path(path).suffix or '(no extension)'
        print(f"Error: No analyzer found for {path} ({ext})", file=sys.stderr)
        print(f"\nError: File type '{ext}' is not supported yet", file=sys.stderr)
        print(f"Run 'reveal --list-supported' to see all supported file types", file=sys.stderr)
        print(f"Visit https://github.com/scottsen/reveal to request new file types", file=sys.stderr)
        sys.exit(1)

    analyzer = analyzer_class(path)

    # Show metadata only?
    if show_meta:
        show_metadata(analyzer, output_format)
        return

    # Pattern detection mode (--check)?
    if args and getattr(args, 'check', False):
        run_pattern_detection(analyzer, path, output_format, args)
        return

    # Extract specific element?
    if element:
        extract_element(analyzer, element, output_format)
        return

    # Default: show structure
    show_structure(analyzer, output_format, args)


def show_metadata(analyzer: FileAnalyzer, output_format: str):
    """Show file metadata."""
    meta = analyzer.get_metadata()

    if output_format == 'json':
        import json
        print(json.dumps(meta, indent=2))
    else:
        print(f"File: {meta['name']}\n")
        print(f"Path:     {meta['path']}")
        print(f"Size:     {meta['size_human']}")
        print(f"Lines:    {meta['lines']}")
        print(f"Encoding: {meta['encoding']}")
        print_breadcrumbs('metadata', meta['path'])


def build_hierarchy(structure: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Build hierarchical tree from flat structure.

    Args:
        structure: Flat structure from analyzer (imports, functions, classes)

    Returns:
        List of root-level items with 'children' added
    """
    # Collect all items with parent info
    all_items = []

    for category, items in structure.items():
        for item in items:
            item = item.copy()  # Don't mutate original
            item['category'] = category
            item['children'] = []
            all_items.append(item)

    # Sort by line number
    all_items.sort(key=lambda x: x.get('line', 0))

    # Build parent-child relationships based on line ranges
    # An item is a child if it's within another item's line range
    for i, item in enumerate(all_items):
        item_start = item.get('line', 0)
        item_end = item.get('line_end', item_start)

        # Find potential parent (previous item that contains this one)
        parent = None
        for j in range(i - 1, -1, -1):
            candidate = all_items[j]
            candidate_start = candidate.get('line', 0)
            candidate_end = candidate.get('line_end', candidate_start)

            # Check if candidate contains this item
            if candidate_start < item_start and candidate_end >= item_end:
                # Found a containing item - use most recent (closest parent)
                parent = candidate
                break

        # Add to parent's children or mark as root
        if parent:
            parent['children'].append(item)
            item['is_child'] = True
        else:
            item['is_child'] = False

    # Return only root-level items
    return [item for item in all_items if not item.get('is_child', False)]


def render_outline(items: List[Dict[str, Any]], path: Path, indent: str = '', is_root: bool = True) -> None:
    """Render hierarchical outline with tree characters.

    Args:
        items: List of items (potentially with children)
        path: File path for line number display
        indent: Current indentation prefix
        is_root: Whether these are root-level items
    """
    if not items:
        return

    for i, item in enumerate(items):
        is_last_item = (i == len(items) - 1)

        # Format item
        line = item.get('line', '?')
        name = item.get('name', '')
        signature = item.get('signature', '')

        # Build metrics display
        metrics = ''
        if 'line_count' in item or 'depth' in item:
            parts = []
            if 'line_count' in item:
                parts.append(f"{item['line_count']} lines")
            if 'depth' in item:
                parts.append(f"depth:{item['depth']}")
            if parts:
                metrics = f" [{', '.join(parts)}]"

        # Format output
        if signature and name:
            display = f"{name}{signature}{metrics}"
        elif name:
            display = f"{name}{metrics}"
        else:
            display = item.get('content', '?')

        # Print item with appropriate prefix
        if is_root:
            # Root items - no tree chars, show full path
            print(f"{display} ({path}:{line})")
        else:
            # Child items - use tree chars
            tree_char = '└─ ' if is_last_item else '├─ '
            print(f"{indent}{tree_char}{display} (line {line})")

        # Recursively render children
        if item.get('children'):
            if is_root:
                # Children of root get minimal indent
                child_indent = '  '
            else:
                # Children of nested items continue the tree
                child_indent = indent + ('   ' if is_last_item else '│  ')
            render_outline(item['children'], path, child_indent, is_root=False)


def _format_links(items: List[Dict[str, Any]], path: Path, output_format: str) -> None:
    """Format and display link items grouped by type."""
    by_type = {}
    for item in items:
        link_type = item.get('type', 'unknown')
        by_type.setdefault(link_type, []).append(item)

    for link_type in ['external', 'internal', 'email']:
        if link_type not in by_type:
            continue

        type_items = by_type[link_type]
        print(f"\n  {link_type.capitalize()} ({len(type_items)}):")

        for item in type_items:
            line = item.get('line', '?')
            text = item.get('text', '')
            url = item.get('url', '')
            broken = item.get('broken', False)

            if output_format == 'grep':
                print(f"{path}:{line}:{url}")
            else:
                if broken:
                    print(f"    ❌ Line {line:<4} [{text}]({url}) [BROKEN]")
                else:
                    if link_type == 'external':
                        domain = item.get('domain', '')
                        print(f"    Line {line:<4} [{text}]({url})")
                        if domain:
                            print(f"             → {domain}")
                    else:
                        print(f"    Line {line:<4} [{text}]({url})")


def _format_code_blocks(items: List[Dict[str, Any]], path: Path, output_format: str) -> None:
    """Format and display code block items grouped by language."""
    by_lang = {}
    for item in items:
        lang = item.get('language', 'unknown')
        by_lang.setdefault(lang, []).append(item)

    # Show fenced blocks grouped by language
    for lang in sorted(by_lang.keys()):
        if lang == 'inline':
            continue

        lang_items = by_lang[lang]
        print(f"\n  {lang.capitalize()} ({len(lang_items)} blocks):")

        for item in lang_items:
            line_start = item.get('line_start', '?')
            line_end = item.get('line_end', '?')
            line_count = item.get('line_count', 0)
            source = item.get('source', '')

            if output_format == 'grep':
                first_line = source.split('\n')[0] if source else ''
                print(f"{path}:{line_start}:{first_line}")
            else:
                print(f"    Lines {line_start}-{line_end} ({line_count} lines)")
                preview_lines = source.split('\n')[:3]
                for preview_line in preview_lines:
                    print(f"      {preview_line}")
                if line_count > 3:
                    print(f"      ... ({line_count - 3} more lines)")

    # Show inline code if present
    if 'inline' in by_lang:
        inline_items = by_lang['inline']
        print(f"\n  Inline code ({len(inline_items)} snippets):")
        for item in inline_items[:10]:
            line = item.get('line', '?')
            source = item.get('source', '')
            if output_format == 'grep':
                print(f"{path}:{line}:{source}")
            else:
                print(f"    Line {line:<4} `{source}`")
        if len(inline_items) > 10:
            print(f"    ... and {len(inline_items) - 10} more")


def _format_standard_items(items: List[Dict[str, Any]], path: Path, output_format: str) -> None:
    """Format and display standard items (functions, classes, etc.)."""
    for item in items:
        line = item.get('line', '?')
        name = item.get('name', '')
        signature = item.get('signature', '')
        content = item.get('content', '')

        # Build metrics display (if available)
        metrics = ''
        if 'line_count' in item or 'depth' in item:
            parts = []
            if 'line_count' in item:
                parts.append(f"{item['line_count']} lines")
            if 'depth' in item:
                parts.append(f"depth:{item['depth']}")
            if parts:
                metrics = f" [{', '.join(parts)}]"

        # Format based on what's available
        if signature and name:
            if output_format == 'grep':
                print(f"{path}:{line}:{name}{signature}")
            else:
                print(f"  {path}:{line:<6} {name}{signature}{metrics}")
        elif name:
            if output_format == 'grep':
                print(f"{path}:{line}:{name}")
            else:
                print(f"  {path}:{line:<6} {name}{metrics}")
        elif content:
            if output_format == 'grep':
                print(f"{path}:{line}:{content}")
            else:
                print(f"  {path}:{line:<6} {content}")


def _build_analyzer_kwargs(analyzer: FileAnalyzer, args) -> Dict[str, Any]:
    """Build kwargs for get_structure() based on analyzer type and args.

    This centralizes all analyzer-specific argument mapping.
    """
    kwargs = {}

    # Navigation/slicing arguments (apply to all analyzers)
    if args:
        if getattr(args, 'head', None):
            kwargs['head'] = args.head
        if getattr(args, 'tail', None):
            kwargs['tail'] = args.tail
        if getattr(args, 'range', None):
            kwargs['range'] = args.range

    # Markdown-specific filters
    if args and hasattr(analyzer, '_extract_links'):
        if args.links or args.link_type or args.domain:
            kwargs['extract_links'] = True
            if args.link_type:
                kwargs['link_type'] = args.link_type
            if args.domain:
                kwargs['domain'] = args.domain

        if args.code or args.language or args.inline:
            kwargs['extract_code'] = True
            if args.language:
                kwargs['language'] = args.language
            if args.inline:
                kwargs['inline_code'] = args.inline

    return kwargs


def _print_file_header(path: Path, is_fallback: bool = False, fallback_lang: str = None) -> None:
    """Print file header with optional fallback indicator."""
    if is_fallback and fallback_lang:
        print(f"File: {path.name} (fallback: {fallback_lang})\n")
    else:
        print(f"File: {path.name}\n")


def _render_json_output(analyzer: FileAnalyzer, structure: Dict[str, List[Dict[str, Any]]]) -> None:
    """Render structure as JSON output."""
    import json

    is_fallback = getattr(analyzer, 'is_fallback', False)
    fallback_lang = getattr(analyzer, 'fallback_language', None)

    result = {
        'file': str(analyzer.path),
        'type': analyzer.__class__.__name__.replace('Analyzer', '').lower(),
        'analyzer': {
            'type': 'fallback' if is_fallback else 'explicit',
            'language': fallback_lang if is_fallback else None,
            'explicit': not is_fallback,
            'name': analyzer.__class__.__name__
        },
        'structure': structure
    }
    print(json.dumps(result, indent=2))


def _render_text_categories(structure: Dict[str, List[Dict[str, Any]]],
                            path: Path, output_format: str) -> None:
    """Render each category in text format."""
    for category, items in structure.items():
        if not items:
            continue

        # Format category name (e.g., 'functions' → 'Functions')
        category_name = category.capitalize()
        print(f"{category_name} ({len(items)}):")

        # Special handling for different categories
        if category == 'links':
            _format_links(items, path, output_format)
        elif category == 'code_blocks':
            _format_code_blocks(items, path, output_format)
        else:
            _format_standard_items(items, path, output_format)

        print()  # Blank line between categories


def show_structure(analyzer: FileAnalyzer, output_format: str, args=None):
    """Show file structure.

    Simplified using extracted helper functions.
    """
    # Build kwargs and get structure
    kwargs = _build_analyzer_kwargs(analyzer, args)
    structure = analyzer.get_structure(**kwargs)
    path = analyzer.path

    # Get fallback info
    is_fallback = getattr(analyzer, 'is_fallback', False)
    fallback_lang = getattr(analyzer, 'fallback_language', None)

    # Handle outline mode
    if args and getattr(args, 'outline', False):
        _print_file_header(path, is_fallback, fallback_lang)
        if not structure:
            print("No structure available for this file type")
            return
        hierarchy = build_hierarchy(structure)
        render_outline(hierarchy, path)
        return

    # Handle JSON output
    if output_format == 'json':
        _render_json_output(analyzer, structure)
        return

    # Handle empty structure
    if not structure:
        _print_file_header(path, is_fallback, fallback_lang)
        print("No structure available for this file type")
        return

    # Text output: show header, categories, and navigation hints
    _print_file_header(path, is_fallback, fallback_lang)
    _render_text_categories(structure, path, output_format)

    # Navigation hints
    if output_format == 'text':
        file_type = get_file_type_from_analyzer(analyzer)
        print_breadcrumbs('structure', path, file_type=file_type)


def extract_element(analyzer: FileAnalyzer, element: str, output_format: str):
    """Extract a specific element.

    Args:
        analyzer: File analyzer
        element: Element name to extract
        output_format: Output format
    """
    # Try common element types
    for element_type in ['function', 'class', 'struct', 'section', 'server', 'location', 'upstream']:
        result = analyzer.extract_element(element_type, element)
        if result:
            break
    else:
        # Not found
        print(f"Error: Element '{element}' not found in {analyzer.path}", file=sys.stderr)
        sys.exit(1)

    # Format output
    if output_format == 'json':
        import json
        print(json.dumps(result, indent=2))
        return

    path = analyzer.path
    line_start = result.get('line_start', 1)
    line_end = result.get('line_end', line_start)
    source = result.get('source', '')
    name = result.get('name', element)

    # Header
    print(f"{path}:{line_start}-{line_end} | {name}\n")

    # Source with line numbers
    if output_format == 'grep':
        # Grep format: filename:linenum:content
        for i, line in enumerate(source.split('\n')):
            line_num = line_start + i
            print(f"{path}:{line_num}:{line}")
    else:
        # Human-readable format
        formatted = analyzer.format_with_lines(source, line_start)
        print(formatted)

        # Navigation hints
        file_type = get_file_type_from_analyzer(analyzer)
        line_count = line_end - line_start + 1
        print_breadcrumbs('element', path, file_type=file_type,
                         element_name=name, line_count=line_count, line_start=line_start)


if __name__ == '__main__':
    main()
