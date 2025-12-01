# Semantic Navigation: Head/Tail/Range Support in Reveal

**Status:** Design Document
**Date:** 2025-11-30
**Feature:** Add `--head`, `--tail`, `--range` flags for semantic navigation

---

## Overview

Enable iterative deepening of file exploration by allowing users to navigate semantic units (functions, records, sections) using head/tail/range operations.

**Key Principle:** Operations work on **semantic units**, not raw text lines.

---

## Motivation

### The Problem

Current reveal shows a fixed preview (first 10 semantic units). Users cannot:
- View the end of a file ("how does this conversation end?")
- Navigate to middle ranges ("show me functions 20-30")
- Override preview size ("show me first 50 records")

### Why Semantic, Not Lines?

```bash
# Traditional Unix tools (line-based)
head -10 conversation.jsonl    # First 10 lines (might be incomplete JSON)
tail -5 app.py                 # Last 5 lines (probably closing braces)

# Reveal semantic navigation (unit-based)
reveal conversation.jsonl --head 10   # First 10 complete, parsed records
reveal app.py --tail 5                # Last 5 functions defined
```

**Semantic units preserve meaning:**
- JSONL: Complete JSON records (one per line)
- Python: Complete functions/classes with line ranges
- Markdown: Complete sections with headers
- Jupyter: Complete cells with outputs

### Use Cases

**1. Conversation Analysis (JSONL)**
```bash
# How did this session start?
reveal conversation.jsonl --head 5

# How did it end?
reveal conversation.jsonl --tail 5

# What happened around message 50?
reveal conversation.jsonl --range 48-52
```

**2. Code Exploration (Python)**
```bash
# First few functions (entry points)
reveal app.py --head 3

# Last few functions (helpers often at end)
reveal app.py --tail 10

# Functions 10-20 in file
reveal app.py --range 10-20
```

**3. Documentation (Markdown)**
```bash
# Table of contents (first sections)
reveal README.md --head 5

# Appendix/References (last sections)
reveal README.md --tail 3
```

---

## Architecture

### 1. CLI Arguments

Add to `main.py` argument parser:

```python
parser.add_argument('--head', type=int, metavar='N',
                    help='Show first N semantic units (functions, records, sections)')
parser.add_argument('--tail', type=int, metavar='N',
                    help='Show last N semantic units')
parser.add_argument('--range', type=str, metavar='START-END',
                    help='Show semantic units from START to END (e.g., 10-20)')
```

**Mutual Exclusivity:**
- Can only use ONE of: `--head`, `--tail`, `--range`
- If none specified, default behavior (current: head 10)

### 2. Base Analyzer API

Update `FileAnalyzer.get_structure()` signature:

```python
def get_structure(self, head=None, tail=None, range=None, **kwargs) -> Dict[str, List[Dict[str, Any]]]:
    """Return file structure with optional slicing.

    Args:
        head: Show first N semantic units (override default)
        tail: Show last N semantic units
        range: Tuple (start, end) for range of semantic units
        **kwargs: Additional analyzer-specific options

    Returns:
        Dict mapping category names to lists of semantic units
    """
```

**Implementation in `show_structure()`:**

```python
# Parse range if provided
range_tuple = None
if args.range:
    try:
        start, end = args.range.split('-')
        range_tuple = (int(start), int(end))
    except ValueError:
        print("Error: --range must be in format START-END (e.g., 10-20)")
        sys.exit(1)

# Build kwargs for get_structure
kwargs = {}
if args.head:
    kwargs['head'] = args.head
elif args.tail:
    kwargs['tail'] = args.tail
elif range_tuple:
    kwargs['range'] = range_tuple

# Call with parameters
structure = analyzer.get_structure(**kwargs)
```

### 3. Analyzer Implementation Pattern

Each analyzer implements slicing for its semantic units:

```python
class JsonlAnalyzer(FileAnalyzer):
    def get_structure(self, head=None, tail=None, range=None, **kwargs):
        """Extract JSONL records with optional slicing."""

        # Parse all records to get count and types
        all_records = []
        record_types = {}

        for i, line in enumerate(self.lines, 1):
            line = line.strip()
            if not line:
                continue

            try:
                obj = json.loads(line)
                rec_type = obj.get('type', 'record')
                record_types[rec_type] = record_types.get(rec_type, 0) + 1
                all_records.append((i, rec_type, obj))
            except json.JSONDecodeError as e:
                all_records.append((i, '⚠️ Invalid JSON', str(e)))

        # Apply slicing
        if head is not None:
            selected = all_records[:head]
        elif tail is not None:
            selected = all_records[-tail:]
        elif range is not None:
            start, end = range
            # 1-based indexing for user, 0-based for Python
            selected = all_records[start-1:end]
        else:
            # Default: first 10
            selected = all_records[:10]

        # Build preview for selected records
        records = []
        for i, rec_type, data in selected:
            if isinstance(data, str):  # Error case
                records.append({
                    'line': i,
                    'name': rec_type,
                    'preview': data[:50]
                })
            else:
                preview = self._build_preview(data)
                records.append({
                    'line': i,
                    'name': f"{rec_type} #{i}",
                    'preview': preview
                })

        # Add summary
        summary = {
            'line': 0,
            'name': f'📊 Summary: {len(all_records)} total records',
            'preview': ', '.join(f'{k}: {v}' for k, v in
                                sorted(record_types.items(), key=lambda x: -x[1]))
        }

        return {'records': [summary] + records}
```

### 4. Default Behavior

**Current behavior (unchanged if no flags):**
- Shows first 10 semantic units
- Maintains backward compatibility

**With flags:**
- `--head 20`: First 20 units
- `--tail 5`: Last 5 units
- `--range 10-20`: Units 10 through 20 (inclusive, 1-based)

---

## Implementation Plan

### Phase 1: CLI & Infrastructure (30 min)

1. Add CLI arguments to `main.py`
2. Add mutual exclusivity validation
3. Parse `--range` format (START-END)
4. Pass parameters to `get_structure()`

**Files:**
- `reveal/main.py`: Argument parsing, validation

### Phase 2: Base API Update (15 min)

1. Update `FileAnalyzer.get_structure()` signature
2. Document parameters in docstring
3. Update default implementations

**Files:**
- `reveal/base.py`: Base class signature

### Phase 3: Analyzer Implementation (60 min)

Implement in order of value:

1. **JsonlAnalyzer** (highest value - conversation logs)
2. **PythonAnalyzer** (code exploration)
3. **MarkdownAnalyzer** (documentation)
4. **JupyterAnalyzer** (notebook exploration)

Other analyzers can default to base implementation (no-op).

**Files:**
- `reveal/analyzers/jsonl.py`
- `reveal/analyzers/python.py`
- `reveal/analyzers/markdown.py`
- `reveal/analyzers/jupyter_analyzer.py`

### Phase 4: Testing (30 min)

**Test cases:**

```bash
# JSONL
reveal conversation.jsonl --head 5
reveal conversation.jsonl --tail 3
reveal conversation.jsonl --range 48-52

# Python
reveal app.py --head 3
reveal app.py --tail 5
reveal app.py --range 10-15

# Composition with other flags
reveal conversation.jsonl --tail 5 --format=json
reveal app.py --head 10 --format=grep
reveal conversation.jsonl --range 1-10 --format=json | jq '...'
```

**Files:**
- Manual testing (no automated tests yet)

### Phase 5: Documentation (20 min)

1. Update `--help` output with examples
2. Add to README.md
3. Update this design doc with outcomes

**Files:**
- `reveal/main.py`: Help text
- `README.md`: Usage examples

---

## Examples

### JSONL Conversation Logs

```bash
# Overview
$ reveal conversation.jsonl
File: conversation.jsonl

Records (11):
  conversation.jsonl:0      📊 Summary: 182 total records
  conversation.jsonl:1      file-history-snapshot #1
  conversation.jsonl:2      user #2 | role=user | "boot."
  conversation.jsonl:3      assistant #3 | role=assistant | "I'll run the TIA boot sequence..."
  ...
  conversation.jsonl:10     user #10

# First 5 messages
$ reveal conversation.jsonl --head 5
File: conversation.jsonl

Records (6):
  conversation.jsonl:0      📊 Summary: 182 total records
  conversation.jsonl:1      file-history-snapshot #1
  conversation.jsonl:2      user #2 | role=user | "boot."
  conversation.jsonl:3      assistant #3 | role=assistant | "I'll run the TIA boot sequence..."
  conversation.jsonl:4      assistant #4 | role=assistant | [tool_use] Bash
  conversation.jsonl:5      user #5 | role=user | [tool_result] # TIA System Boot...

# How did conversation end?
$ reveal conversation.jsonl --tail 3
File: conversation.jsonl

Records (4):
  conversation.jsonl:0      📊 Summary: 182 total records
  conversation.jsonl:180    user #180 | role=user | "Let's commit this work"
  conversation.jsonl:181    assistant #181 | role=assistant | "I'll create a commit..."
  conversation.jsonl:182    user #182 | role=user | [tool_result] Git commit succeeded

# Context around message 50
$ reveal conversation.jsonl --range 48-52
File: conversation.jsonl

Records (6):
  conversation.jsonl:0      📊 Summary: 182 total records
  conversation.jsonl:48     user #48
  conversation.jsonl:49     assistant #49
  conversation.jsonl:50     user #50
  conversation.jsonl:51     assistant #51
  conversation.jsonl:52     user #52

# Compose with jq
$ reveal conversation.jsonl --tail 10 --format=json | \
  jq '.structure.records[] | select(.preview | contains("error"))'
```

### Python Code Exploration

```bash
# First few functions (entry points)
$ reveal app.py --head 3
File: app.py

Functions (3):
  app.py:10     main(args: List[str]) -> int [45 lines, depth:3]
  app.py:58     parse_arguments(argv: List[str]) -> Namespace [22 lines, depth:2]
  app.py:82     run_server(config: Config) -> None [18 lines, depth:2]

# Last few functions (helpers)
$ reveal app.py --tail 5
File: app.py

Functions (5):
  app.py:245    _validate_config(config: dict) -> bool [12 lines, depth:2]
  app.py:259    _setup_logging(level: str) -> None [8 lines, depth:1]
  app.py:269    _signal_handler(signum, frame) -> None [5 lines, depth:1]
  app.py:276    _cleanup_resources() -> None [15 lines, depth:2]
  app.py:293    if __name__ == '__main__': [3 lines, depth:0]

# Functions 10-15
$ reveal app.py --range 10-15 --format=grep
app.py:105:_init_database(db_path: str) -> Database
app.py:125:_load_plugins(plugin_dir: Path) -> List[Plugin]
app.py:148:_configure_routes(app: Flask) -> None
app.py:167:_health_check() -> Dict[str, Any]
app.py:180:_metrics_endpoint() -> Response
app.py:195:_shutdown() -> None
```

### Markdown Documentation

```bash
# First few sections (TOC)
$ reveal README.md --head 5
File: README.md

Sections (5):
  README.md:1      # Reveal - Semantic Code Explorer
  README.md:15     ## Installation
  README.md:28     ## Quick Start
  README.md:45     ## Features
  README.md:67     ## Usage Examples

# Last sections (appendix)
$ reveal README.md --tail 3
File: README.md

Sections (3):
  README.md:289    ## Contributing
  README.md:305    ## License
  README.md:315    ## Credits
```

---

## Unix Composability

### Piping with jq

```bash
# Get user messages from last 10 records
$ reveal conversation.jsonl --tail 10 --format=json | \
  jq -r '.structure.records[] | select(.name | contains("user")) | .line'

# Find god functions in first 20
$ reveal app.py --head 20 --format=json | \
  jq '.structure.functions[] | select(.line_count > 50) | {name, line, line_count}'
```

### Piping with grep

```bash
# Find error-related records in tail
$ reveal conversation.jsonl --tail 20 --format=grep | grep -i error

# Extract specific function lines
$ reveal app.py --range 10-20 --format=grep | cut -d: -f1-2
```

### Integration with vim

```bash
# Jump to last function
$ vim $(reveal app.py --tail 1 --format=grep | cut -d: -f1-2)
```

---

## Edge Cases & Validation

### Invalid Range Format

```bash
$ reveal file.jsonl --range 10
Error: --range must be in format START-END (e.g., 10-20)

$ reveal file.jsonl --range abc-def
Error: --range values must be integers
```

### Mutual Exclusivity

```bash
$ reveal file.jsonl --head 10 --tail 5
Error: Cannot use --head and --tail together. Choose one.

$ reveal file.jsonl --head 10 --range 5-15
Error: Cannot use --head and --range together. Choose one.
```

### Out of Bounds

```bash
# File has 50 records, request 100
$ reveal file.jsonl --head 100
File: file.jsonl

Records (51):  # Shows summary + all 50 records
  file.jsonl:0      📊 Summary: 50 total records
  file.jsonl:1      record #1
  ...
  file.jsonl:50     record #50

# Range beyond file size
$ reveal file.jsonl --range 45-100
File: file.jsonl

Records (7):  # Shows summary + records 45-50
  file.jsonl:0      📊 Summary: 50 total records
  file.jsonl:45     record #45
  ...
  file.jsonl:50     record #50
```

### Empty Results

```bash
# Range with no records
$ reveal file.jsonl --range 100-200
File: file.jsonl

Records (1):
  file.jsonl:0      📊 Summary: 50 total records

# (No records in range 100-200)
```

---

## Performance Considerations

### JSONL Files

**Two-pass approach needed:**
1. First pass: Count total records, collect types
2. Second pass: Extract requested range

**Optimization for tail:**
- Could read file backwards
- Or use file seek + negative offset
- Initial implementation: simple, correct (read all, slice)

**Large files (>10k records):**
- Consider streaming approach
- Or index file on first access (cache .jsonl.idx)
- Future optimization

### Python Files

**TreeSitter already parsed:**
- All functions/classes available
- Slicing is O(1) array operation
- No performance concern

### Markdown Files

**Section extraction:**
- Parse headers first (fast)
- Extract content lazily if needed
- No performance concern

---

## Future Enhancements

### 1. Filtering with Slicing

```bash
# Last 10 user messages
reveal conversation.jsonl user --tail 10

# First 5 god functions
reveal app.py --head 5 --god
```

**Implementation:** Apply filter first, then slice.

### 2. Reverse Order

```bash
# Show newest first
reveal conversation.jsonl --tail 10 --reverse
```

### 3. Streaming Mode

```bash
# Follow new records (like tail -f)
reveal conversation.jsonl --tail 10 --follow
```

### 4. Smart Defaults Per Type

```yaml
# Different defaults per file type
jsonl: head=10
python: head=20   # More context for code
markdown: head=5  # Just TOC
```

---

## Success Criteria

**Must have:**
- ✅ `--head N` shows first N semantic units
- ✅ `--tail N` shows last N semantic units
- ✅ `--range START-END` shows units START to END
- ✅ Works with `--format=json` and `--format=grep`
- ✅ Maintains backward compatibility (no flags = current behavior)
- ✅ Clear error messages for invalid input

**Nice to have:**
- ✅ Performance acceptable for files <100k semantic units
- ✅ Combines with existing filters (--god, type extraction)
- ✅ Documentation with examples

**Out of scope (for now):**
- ❌ Stdin filtering
- ❌ Streaming/follow mode
- ❌ Reverse order
- ❌ File indexing for large files

---

## Timeline

- **Phase 1:** 30 min (CLI infrastructure)
- **Phase 2:** 15 min (Base API)
- **Phase 3:** 60 min (Analyzer implementations)
- **Phase 4:** 30 min (Testing)
- **Phase 5:** 20 min (Documentation)

**Total:** ~2.5 hours

---

## Validation Questions

Before implementation, validate:

1. ✅ Does this align with reveal's "iterative deepening" mission?
2. ✅ Does it compose well with Unix tools (jq, grep, etc.)?
3. ✅ Is the API clean and extendable?
4. ✅ Are edge cases handled gracefully?
5. ✅ Does it work for both humans and AI agents?

---

## Sign-off

**Approved for implementation:** _[Pending user review]_

**Notes:**
- Start with JSONL (highest value)
- Test thoroughly with real conversation files
- Document all examples in README

**Next Steps:**
1. User reviews this document
2. Implement Phase 1 (CLI)
3. Implement Phase 2 (Base API)
4. Implement Phase 3 (JSONL analyzer first)
5. Test and iterate
