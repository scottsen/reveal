# Reveal

> Semantic code exploration tool optimized for token efficiency. Helps AI agents understand code structure before reading files, achieving 10-150x token reduction.

**Key Principle:** Explore structure first (50 tokens), extract what you need (20 tokens), instead of reading full files (7,500+ tokens).

**Supported:** 18 file types including Python, JS/TS, Rust, Go, Bash, Docker, YAML, JSON, Markdown, Jupyter

---

## Quick Start

**Installation:**
```bash
pip install reveal-cli
```

**Basic Usage:**
```bash
reveal file.py                    # Show structure (functions, classes, imports)
reveal src/                       # Directory tree
reveal file.py function_name      # Extract specific function
reveal file.py --outline          # Hierarchical view (classes with methods)
```

**Core Workflow:** Explore → Navigate → Focus

---

## Core Use Cases

### Codebase Exploration

**Pattern:**
```bash
reveal src/                       # What directories exist?
reveal src/main.py                # What's in this file?
reveal src/main.py --outline      # Hierarchical structure
reveal src/main.py load_config    # Extract specific function
```

**Use when:** Unknown codebase, onboarding to project

**Token impact:** Traditional (read all): ~5,000 tokens → With reveal: ~200 tokens (25x reduction)

---

### Function Extraction

**Pattern:**
```bash
reveal file.py                    # See all functions/classes
reveal file.py target_function    # Extract specific code
```

**Use when:** Need to understand specific functionality

**Token impact:** Grep + read: ~500 tokens → Reveal: ~70 tokens (7x reduction)

---

### Code Quality Review

**Pattern:**
```bash
reveal file.py --check                   # Run all quality checks
reveal file.py --check --select B,S      # Focus on bugs & security
reveal file.py --outline --check         # Structure + issues
```

**Use when:** PR review, refactoring, security audit

**Rules:** Bugs (B), Security (S), Complexity (C), Errors (E), Refactoring (R), URLs (U)

---

### Large File Navigation

**Pattern:**
```bash
reveal large.py --head 10         # First 10 functions
reveal large.py --tail 5          # Last 5 functions (bugs cluster here!)
reveal large.py --range 15-20     # Specific range
reveal large.py specific_func     # Extract target
```

**Use when:** File too large to view all at once

**Token impact:** View only what's needed (10x+ reduction)

---

## Workflows

### PR Review Workflow
```bash
# Get changed files
git diff --name-only origin/main

# Quick structure check
git diff --name-only | reveal --stdin --outline

# Quality check changed files
git diff --name-only | grep "\.py$" | reveal --stdin --check

# Deep dive on specific file
reveal src/auth.py --check
reveal src/auth.py authenticate_user
```

---

### Bug Investigation Workflow
```bash
# Find file structure
reveal src/problematic_file.py --outline

# Check last functions (bugs often at end)
reveal src/problematic_file.py --tail 5

# Extract suspicious function
reveal src/problematic_file.py buggy_function

# Check for quality issues
reveal src/problematic_file.py --check --select B,E
```

---

### New Feature Understanding
```bash
# Explore feature directory
reveal src/features/new_thing/

# See main file structure
reveal src/features/new_thing/main.py

# Understand key functions
reveal src/features/new_thing/main.py --outline
reveal src/features/new_thing/main.py process_request
```

---

## Pipeline Composition

### With Git
```bash
# Changed files in PR
git diff --name-only origin/main | reveal --stdin --outline

# Quality check modified code
git diff --name-only | grep "\.py$" | reveal --stdin --check

# Find complex changes
git diff --name-only | reveal --stdin --check --select C
```

### With Find
```bash
# Explore all Python files
find src/ -name "*.py" | reveal --stdin

# Check all Dockerfiles
find . -name "Dockerfile*" | reveal --stdin --check

# JSON output for processing
find src/ -name "*.py" | reveal --stdin --format=json
```

### With jq (JSON Processing)
```bash
# Find complex functions
reveal app.py --format=json | jq '.structure.functions[] | select(.depth > 3)'

# Extract all function signatures
reveal app.py --format=json | jq -r '.structure.functions[] | "\(.name)(\(.line))"'

# Find all imports
reveal app.py --format=json | jq '.structure.imports[]'
```

---

## Integration Patterns

### With TIA (The Intelligent Agent)
```bash
# Orient: What exists?
tia search all "authentication"
tia beth explore "auth"

# Navigate: What's in this file? (Use reveal here!)
reveal path/from/search/auth.py

# Focus: Get specific code
reveal path/from/search/auth.py authenticate_user
```

**Reveal fits perfectly in the Navigate phase** - after finding files, before reading them.

---

### With Claude Code
```bash
# Before reading a file, explore it first
reveal unknown_file.py            # What's in here?
# Then use Read tool on specific functions only
```

---

## Common Patterns

### ✅ DO: Explore before reading
```bash
reveal file.py                    # Structure first (50 tokens)
reveal file.py target_func        # Then extract (20 tokens)
```

### ❌ DON'T: Read first
```bash
cat huge_file.py                  # 10,000 tokens wasted
```

---

### ✅ DO: Use pipelines
```bash
git diff --name-only | reveal --stdin
```

### ❌ DON'T: Manual iteration
```bash
reveal file1.py; reveal file2.py; ...
```

---

### ✅ DO: Progressive disclosure
```bash
reveal 1000_line_file.py --head 10    # Start small
reveal 1000_line_file.py --range 20-30 # Expand as needed
```

### ❌ DON'T: All at once
```bash
reveal 1000_line_file.py          # Overwhelming output
```

---

### ✅ DO: Semantic extraction
```bash
reveal file.py function           # Accurate, with context
```

### ❌ DON'T: Grep with manual counting
```bash
grep -A 20 "def function" file.py # Brittle, error-prone
```

---

## Key Flags Reference

| Flag | Purpose | Token Impact |
|------|---------|--------------|
| (none) | Show structure | Minimal (50-100) |
| `--outline` | Hierarchical view | Low (100-200) |
| `--head N` | First N elements | Minimal (10-50) |
| `--tail N` | Last N elements | Minimal (10-50) |
| `--range M-N` | Specific range | Minimal (20-100) |
| `--check` | Quality checks | Low (100-300) |
| `--select RULES` | Filter rules (B,S,C,E,R,U) | Variable |
| `--format=json` | JSON output | Same (for scripting) |
| `--stdin` | Pipeline mode | Scales with input |
| `element_name` | Extract element | Low (20-100) |

---

## Token Efficiency

### Scenario: 500-Line Python File

| Approach | Tokens | Time | Use When |
|----------|--------|------|----------|
| Read entire file | ~7,500 | Immediate | Never (unless truly needed) |
| reveal structure | ~50 | <100ms | First step (always) |
| reveal --outline | ~100 | <100ms | Need hierarchy |
| reveal + extract | ~70 | <200ms | Need specific code |
| reveal --check | ~150 | <500ms | Quality review |

**Best Practice:** Start with structure (50 tokens), then extract only what's needed.

---

### Scenario: Exploring 50-File Codebase

| Approach | Tokens | Result |
|----------|--------|--------|
| Read all files | ~375,000 | Context overflow, expensive |
| reveal all files | ~2,500 | Complete structure map |
| reveal + targeted reads | ~5,000 | Deep understanding where needed |

**Savings:** 75x token reduction with better understanding!

---

## Supported File Types

**18 Built-in analyzers:**
- **Code:** Python (.py), JavaScript (.js), TypeScript (.ts, .tsx), Rust (.rs), Go (.go), GDScript (.gd)
- **Scripts:** Bash/Shell (.sh, .bash)
- **Config:** YAML (.yaml, .yml), JSON (.json), TOML (.toml), Nginx (nginx.conf)
- **Containers:** Dockerfile
- **Docs:** Markdown (.md)
- **Data:** Jupyter (.ipynb), JSONL (.jsonl)
- **Fallback:** 30+ languages via Tree-sitter (automatic)

**Check support:**
```bash
reveal --list-supported
```

---

## Decision Tree

**When exploring code:**

```
Need to understand code?
├─ Unknown directory → reveal src/
├─ Unknown file → reveal file.py (or --outline for hierarchy)
├─ Need specific function → reveal file.py function_name
├─ Multiple files → find/git | reveal --stdin
├─ Code quality checks → reveal file.py --check
├─ Large file (>300 lines) → reveal file.py --head N (explore progressively)
└─ Full content needed → cat/Read tool (after exploring structure)
```

**Key Rule:** Never read full file without checking structure first!

---

## Resources

- **GitHub:** https://github.com/scottsen/reveal
- **PyPI:** https://pypi.org/project/reveal-cli/
- **Full Guide:** `reveal --agent-help-full`
- **Version:** `reveal --version`
- **Supported Types:** `reveal --list-supported`

---

## Optional

The following sections provide additional depth for agents needing comprehensive understanding:

- **Complete Token Analysis:** Detailed efficiency calculations across multiple scenarios (`reveal --agent-help-full`)
- **All Rules Reference:** Complete list of 8+ code quality detectors with examples
- **Advanced Pipeline Patterns:** Complex composition with jq, awk, sed
- **Anti-patterns Deep Dive:** Common mistakes and solutions explained
- **Performance Benchmarks:** Speed and accuracy metrics
- **Version History:** Feature additions by version
- **Troubleshooting Guide:** Solutions to common issues
- **Contributing Guide:** How to add new analyzers

**Access full documentation:** `reveal --agent-help-full`
