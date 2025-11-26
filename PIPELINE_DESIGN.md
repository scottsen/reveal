# Reveal Pipeline Architecture

**Goal:** Make reveal composable and pipeable for complex queries across codebases.

## Core Principles

1. **Unix Philosophy** - Do one thing well, compose with others
2. **stdin/stdout** - Read file lists from stdin, output in pipeable formats
3. **Multiple output formats** - text (human), json (scripts), grep (pipes), files (lists)
4. **Filter at any level** - Files, functions, classes, imports
5. **Backwards compatible** - Don't break existing usage

---

## Output Formats

### Current
```bash
reveal file.py              # text format (human readable)
reveal file.py --format=json    # json (structured data)
reveal file.py --format=grep    # grep-compatible (file:line:content)
```

### NEW: --format=files
```bash
reveal src/ --format=files
# Output:
src/main.py
src/base.py
src/tree.py
```

Purpose: List files only (for piping to next command)

---

## Filter Flags (New)

### File-level filters
```bash
reveal src/ --files-matching "*auth*"      # Glob pattern
reveal src/ --has-import "requests"        # Files importing X
reveal src/ --has-class "BaseModel"        # Files with class X
reveal src/ --has-function "authenticate"  # Files with function X
```

### Function-level filters
```bash
reveal file.py --functions --line-count ">100"    # Long functions
reveal file.py --functions --depth ">4"           # Deep nesting
reveal file.py --functions --params ">5"          # Many parameters
reveal file.py --functions --matching "auth*"     # Name pattern
```

### Import-level filters
```bash
reveal file.py --imports --category stdlib       # Show only stdlib
reveal file.py --imports --category external     # Show only external
reveal file.py --imports --from "requests"       # Specific module
```

### God mode (combined filters)
```bash
reveal file.py --god                    # line_count>50 OR depth>4
reveal file.py --god --threshold=100    # line_count>100 OR depth>5
```

---

## Query Syntax

### Comparison operators
```
>N   - greater than
<N   - less than
>=N  - greater or equal
<=N  - less or equal
=N   - exactly
N    - exactly (shorthand)
N-M  - range (inclusive)
```

### Examples
```bash
--line-count ">100"      # More than 100 lines
--line-count "50-100"    # Between 50 and 100
--depth ">=5"            # Depth 5 or more
--params "3"             # Exactly 3 parameters
```

---

## Pipeline Examples

### Example 1: Find god functions across project
```bash
# Method 1: Direct (with glob)
reveal src/**/*.py --god --format=grep

# Method 2: Pipeline (more flexible)
reveal src/ --format=files | \
  xargs -I{} reveal {} --god --format=grep
```

### Example 2: Find authentication-related code with complexity
```bash
# Find files with "auth" in name or content
reveal src/ --files-matching "*auth*" --format=files | \
# Show their god functions
  xargs -I{} reveal {} --god
```

### Example 3: Find external dependencies usage
```bash
# Find all files importing requests
reveal src/ --has-import "requests" --format=files | \
# Show functions using it (would need code analysis)
  xargs -I{} reveal {} --functions --matching "*request*"
```

### Example 4: Refactoring candidates
```bash
# Find all functions >100 lines with >4 depth
reveal src/**/*.py \
  --functions \
  --line-count ">100" \
  --depth ">4" \
  --format=json
```

### Example 5: Import audit
```bash
# Show all external dependencies across project
reveal src/**/*.py --imports --category external --format=grep | \
  cut -d: -f3 | sort -u
```

---

## stdin Support

### Read file list from stdin
```bash
# NEW flag: --stdin or --files-from-stdin
find src/ -name "*.py" | reveal --stdin --god

# Or implicit (if no path given and stdin is pipe)
find src/ -name "*.py" | reveal --god
```

---

## Implementation Plan

### Phase 1: Metrics (Foundation)
- [ ] Add line_count to function dicts
- [ ] Add depth calculation
- [ ] Add param_count
- [ ] Display in output: `function(...) [X lines, depth:Y]`

### Phase 2: God Mode
- [ ] Add --god flag
- [ ] Configurable thresholds
- [ ] Filter functions by metrics

### Phase 3: Import Categorization
- [ ] Categorize imports (stdlib/local/external)
- [ ] Display categories in output
- [ ] Add --imports flag with --category filter

### Phase 4: Filtering
- [ ] Add comparison operators (>, <, >=, etc)
- [ ] Function-level filters (--line-count, --depth, --params)
- [ ] File-level filters (--has-import, --has-function)

### Phase 5: Pipeline Support
- [ ] Add --format=files
- [ ] Add stdin support
- [ ] Test pipeline workflows

### Phase 6: Advanced Queries
- [ ] Combined filters (AND/OR logic)
- [ ] Inverse filters (NOT)
- [ ] Regular expressions

---

## Backwards Compatibility

All existing commands still work:
```bash
reveal file.py                    # Still shows structure
reveal file.py function_name      # Still extracts element
reveal file.py --meta             # Still shows metadata
reveal dir/                       # Still shows tree
```

New features are opt-in via flags.

---

## Future Ideas

### Cross-file analysis
```bash
# Find all functions calling a specific function
reveal src/ --calls "authenticate"

# Find unused functions
reveal src/ --unused

# Find circular dependencies
reveal src/ --circular-imports
```

### Smart suggestions
```bash
# Suggest refactorings
reveal file.py --suggest
# Output:
# - show_structure() is 170 lines (suggest: split into helpers)
# - deep nesting in handle_auth() (suggest: early returns)
```

---

## JSON Schema (for --format=json)

```json
{
  "file": "path/to/file.py",
  "type": "python",
  "structure": {
    "imports": [
      {
        "line": 3,
        "content": "import sys",
        "category": "stdlib",
        "module": "sys"
      }
    ],
    "functions": [
      {
        "line": 10,
        "line_end": 50,
        "name": "process_data",
        "signature": "(data: dict) -> list",
        "line_count": 41,
        "depth": 3,
        "param_count": 1,
        "is_god": false
      }
    ]
  }
}
```

---

## Testing Strategy

```bash
# Test on reveal's own codebase
reveal reveal/ --god
reveal reveal/ --imports --category external
reveal reveal/ --functions --line-count ">50"

# Pipeline tests
reveal reveal/ --has-import "tree_sitter" --format=files | wc -l
reveal reveal/**/*.py --god --format=grep | wc -l
```
