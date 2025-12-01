# Agent Help Standard for CLI Tools

**Version:** 1.0.0
**Based on:** [llms.txt specification](https://llmstxt.org/)
**Reference Implementation:** reveal CLI tool

---

## Purpose

This document defines a standard for CLI tools to provide AI agent-friendly documentation through `--agent-help` and `--agent-help-full` flags. The format is inspired by the llms.txt standard for web documentation, adapted for command-line tools.

---

## Core Principles

1. **Examples First**: Every section MUST include concrete, copy-paste examples
2. **Progressive Disclosure**: Brief version for quick reference, full version for deep dives
3. **Token Efficiency**: Structured to minimize token usage while maximizing value
4. **Markdown Format**: Standard markdown for easy parsing and display
5. **Consistent Structure**: Predictable headings enable agents to navigate efficiently

---

## Two-Tier System

### `--agent-help` (Brief Reference)
- **Target Length:** 150-400 lines
- **Purpose:** Quick reference for agents that know the basics
- **Content:** Core use cases, common patterns, essential workflows
- **Use When:** Agent needs refresher or syntax lookup

### `--agent-help-full` (Comprehensive Guide)
- **Target Length:** 800-1500 lines
- **Purpose:** Complete onboarding and troubleshooting
- **Content:** Extended examples, anti-patterns, rules reference, troubleshooting
- **Use When:** Agent is learning tool for first time or needs deep understanding

---

## Required Structure (Brief Version)

### 1. H1: Tool Name
```markdown
# ToolName
```

### 2. Blockquote: One-Line Summary
```markdown
> Tool purpose and key value proposition in 1-2 sentences. Include primary use case and unique differentiator.
```

**Example:**
```markdown
> Semantic code exploration tool optimized for token efficiency. Helps AI agents understand code structure before reading files, achieving 10-150x token reduction.
```

### 3. Key Facts (2-3 bullets)
```markdown
**Key Principle:** Core concept agents must understand

**Supported:** What file types/formats/systems does this tool support?
```

### 4. ## Quick Start
- Installation command
- 3-5 basic usage examples with inline comments
- Core workflow description (e.g., "Explore → Navigate → Focus")

**Example:**
```markdown
## Quick Start

**Installation:**
```bash
pip install tool-name
```

**Basic Usage:**
```bash
tool file.txt                    # Basic operation
tool file.txt --option          # Common variant
tool file.txt element           # Extract specific element
```

**Core Workflow:** Understand → Process → Output
```

### 5. ## Core Use Cases (3-5 scenarios)

Each use case MUST include:
- **Pattern:** Concrete bash commands in code block
- **Use when:** Clear trigger conditions
- **Token impact / Result:** Quantified benefit (if applicable)

**Example:**
```markdown
### Codebase Exploration

**Pattern:**
```bash
tool src/                       # What directories exist?
tool src/main.py                # What's in this file?
tool src/main.py function_name  # Extract specific function
```

**Use when:** Unknown codebase, onboarding to project

**Token impact:** Traditional: ~5,000 tokens → With tool: ~200 tokens (25x reduction)
```

### 6. ## Workflows (2-4 complete sequences)

Multi-step workflows showing tool in context:

**Example:**
```markdown
### PR Review Workflow
```bash
# Step 1: Identify changed files
git diff --name-only origin/main

# Step 2: Quick overview
git diff --name-only | tool --stdin

# Step 3: Deep dive
tool src/changed_file.py --check
```
```

### 7. ## Pipeline Composition (if applicable)

Show how tool composes with standard Unix tools:

**Example:**
```markdown
### With Git
```bash
git diff --name-only | tool --stdin
```

### With Find
```bash
find src/ -name "*.py" | tool --stdin
```

### With jq
```bash
tool file.py --format=json | jq '.data[]'
```
```

### 8. ## Integration Patterns

How tool works with popular ecosystems (Claude Code, TIA, etc):

**Example:**
```markdown
### With Claude Code
```bash
# Before reading a file, explore it first
tool unknown_file.py            # Structure first
# Then use Read tool on specific functions only
```
```

### 9. ## Common Patterns (DO/DON'T pairs)

3-5 comparison examples using ✅/❌:

**Example:**
```markdown
### ✅ DO: Explore before reading
```bash
tool file.py                    # Structure first (50 tokens)
tool file.py target_func        # Then extract (20 tokens)
```

### ❌ DON'T: Read first
```bash
cat huge_file.py                # 10,000 tokens wasted
```
```

### 10. ## Key Flags Reference

Table or list of most important options:

**Example:**
```markdown
| Flag | Purpose | Impact |
|------|---------|--------|
| (none) | Show structure | Minimal (50-100) |
| `--option` | Enable feature | Low (100-200) |
| `--format=json` | JSON output | Same (for scripting) |
```

### 11. ## Token Efficiency / Performance (if applicable)

Quantified benefits with tables:

**Example:**
```markdown
### Scenario: 500-Line File

| Approach | Tokens | Use When |
|----------|--------|----------|
| Read entire file | ~7,500 | Never (unless truly needed) |
| tool structure | ~50 | First step (always) |
| tool + extract | ~70 | Need specific code |
```

### 12. ## Resources

Links to documentation, repo, package manager:

**Example:**
```markdown
- **GitHub:** https://github.com/user/tool
- **PyPI:** https://pypi.org/project/tool/
- **Full Guide:** `tool --agent-help-full`
```

### 13. ## Optional

List sections available in full version:

**Example:**
```markdown
## Optional

The following sections provide additional depth:

- **Complete Token Analysis:** Detailed calculations (`tool --agent-help-full`)
- **All Rules Reference:** Complete list of detectors
- **Advanced Patterns:** Complex compositions
- **Troubleshooting Guide:** Solutions to common issues

**Access full documentation:** `tool --agent-help-full`
```

---

## Additional Structure (Full Version Only)

The full version expands the brief version with:

### 14. ## Extended Examples (3-5 complete flows)

Multi-step, real-world scenarios with context:

**Example:**
```markdown
### Example 1: Multi-File PR Review (Complete Flow)
```bash
# Step 1: Identify changed files
git diff --name-only origin/main
# Output: src/auth.py, src/utils.py, tests/test_auth.py

# Step 2: Quick overview of all changes
git diff --name-only | tool --stdin

# Step 3: Deep dive on critical file
tool src/auth.py --check

# Step 4: Extract specific new function
tool src/auth.py validate_token

# Step 5: Check test coverage
tool tests/test_auth.py
```
```

### 15. ## Complete Anti-Patterns Guide

Expanded DO/DON'T with explanations:

**Example:**
```markdown
### Anti-Pattern 1: Token Wastage
**❌ Bad:**
```bash
cat src/large_file.py
# Cost: 15,000 tokens
# Problem: Context overflow, expensive, slow to process
```

**✅ Good:**
```bash
tool src/large_file.py --head 10
# Cost: 100 tokens
tool src/large_file.py target_function
# Cost: 50 tokens
# Total: 150 tokens (100x reduction!)
```
```

### 16. ## Complete Rules/Features Reference

Detailed documentation of all rules, detectors, or features:

**Example:**
```markdown
### Security Issues (S)

**S701: Hardcoded credentials**
```python
# ❌ Bad: Credentials in code
API_KEY = "sk_live_abc123"

# ✅ Good: Environment variables
import os
API_KEY = os.getenv("API_KEY")
```

**Detection:**
```bash
tool file.py --check --select S
```
```

### 17. ## Advanced Pipeline Patterns

Complex compositions with multiple tools:

**Example:**
```markdown
### Pattern 1: Finding All High-Complexity Functions
```bash
find src/ -name "*.py" | \
  tool --stdin --check --format=json | \
  jq -r '.[] | select(.issues | length > 0) | .path' | \
  sort | uniq
```
```

### 18. ## Troubleshooting Guide

Common issues with symptoms, causes, solutions:

**Example:**
```markdown
### Issue: "Element not found"

**Symptom:**
```bash
tool file.py my_function
# Error: Element 'my_function' not found
```

**Causes:**
1. Typo in function name
2. Function is nested or private
3. Function is in different file

**Solutions:**
```bash
# List all available elements
tool file.py

# Search with grep
tool file.py --format=grep | grep -i "my_function"
```
```

### 19. ## Contributing Guide (if open source)

How to extend the tool:

**Example:**
```markdown
### Step 1: Create Analyzer Module
```python
# tool/analyzers/mylang.py
class MyLangAnalyzer:
    def analyze(self, source):
        # Implementation
        return result
```
```

### 20. ## Version History

Feature additions by version:

**Example:**
```markdown
### v1.2.0 (2025-11)
- ✨ Pattern detection
- ✨ Industry-aligned rule codes
- 📚 Agent help guide
```

### 21. ## Performance Benchmarks

Quantified performance data:

**Example:**
```markdown
| File Size | Lines | Parse Time | Memory |
|-----------|-------|------------|--------|
| Small | 100 | 20ms | 5MB |
| Large | 10,000 | 800ms | 80MB |
```

---

## Critical Rules

### ✅ MUST Have

1. **Every section has examples** - Text without examples is useless to agents
2. **Code blocks use bash syntax** - Copy-paste ready commands
3. **Concrete numbers** - Token counts, time, performance metrics
4. **Clear triggers** - "Use when X" conditions
5. **Progressive disclosure** - Brief → Full versioning

### ❌ MUST NOT Have

1. **No fluff** - Every sentence adds value or gets cut
2. **No abstract concepts without examples** - Show, don't tell
3. **No "see documentation"** - Everything needed is inline
4. **No broken examples** - Test all commands before publishing

---

## Implementation Checklist

### Code Implementation

- [ ] Add `--agent-help` flag to argument parser
- [ ] Add `--agent-help-full` flag to argument parser
- [ ] Create `AGENT_HELP.md` file in project root (371 lines target)
- [ ] Create `AGENT_HELP_FULL.md` file in project root (1000+ lines target)
- [ ] Add handlers to load and print markdown files
- [ ] Update `--help` description to mention agent flags

### Content Requirements

Brief version (`AGENT_HELP.md`):
- [ ] H1 with tool name
- [ ] Blockquote with one-line summary
- [ ] Quick Start section with installation + 3-5 examples
- [ ] Core Use Cases (3-5) with Pattern/Use when/Impact
- [ ] Workflows (2-4) with multi-step sequences
- [ ] Pipeline Composition examples
- [ ] Integration Patterns (Claude Code, TIA, etc)
- [ ] Common Patterns (3-5 DO/DON'T pairs)
- [ ] Key Flags Reference (table format)
- [ ] Token Efficiency or Performance metrics
- [ ] Resources section with links
- [ ] Optional section listing full version content

Full version (`AGENT_HELP_FULL.md`):
- [ ] All brief content (copy from brief version)
- [ ] Extended Examples (3-5 complete flows)
- [ ] Complete Anti-Patterns Guide
- [ ] Complete Rules/Features Reference
- [ ] Advanced Pipeline Patterns
- [ ] Troubleshooting Guide (3-5 issues)
- [ ] Contributing Guide (if open source)
- [ ] Version History
- [ ] Performance Benchmarks

### Quality Checks

- [ ] Every section has at least one code block example
- [ ] All bash commands are tested and working
- [ ] Token counts are realistic (test with actual LLM)
- [ ] Tables are properly formatted
- [ ] Links are valid
- [ ] Brief version is 150-400 lines
- [ ] Full version is 800-1500 lines
- [ ] No broken internal references

---

## Example Implementations

### Minimal Example (Brief)

```markdown
# MyTool

> Does X thing efficiently. Saves Y time compared to manual approach.

**Key Principle:** Core workflow concept

**Supported:** File types or systems

---

## Quick Start

**Installation:**
```bash
pip install mytool
```

**Basic Usage:**
```bash
mytool file.txt                 # Basic operation
mytool file.txt --option       # Common variant
```

---

## Core Use Cases

### Use Case 1: Primary Scenario

**Pattern:**
```bash
mytool input.txt
mytool input.txt --process
```

**Use when:** Specific trigger condition

**Result:** Quantified benefit

---

## Workflows

### Workflow: Common Task
```bash
# Step 1
command1

# Step 2
mytool result_from_step1
```

---

## Common Patterns

### ✅ DO: Recommended approach
```bash
mytool file.txt
```

### ❌ DON'T: Anti-pattern
```bash
old_tool file.txt
```

---

## Resources

- **GitHub:** https://github.com/user/mytool
- **Docs:** https://mytool.dev
- **Full Guide:** `mytool --agent-help-full`
```

---

## Testing Your Implementation

### Agent Comprehension Test

Ask an AI agent:
1. "How do I use MyTool for X?" (should answer from brief version)
2. "Show me a complete workflow for Y" (should reference workflows)
3. "What's the difference between A and B?" (should find in DO/DON'T)
4. "I'm getting error Z" (should find in troubleshooting - full version)

### Token Efficiency Test

Measure tokens for:
- Brief version (target: <5,000 tokens)
- Full version (target: <15,000 tokens)
- Compare to reading tool's entire documentation

### Example Coverage Test

- Count code blocks (target: 1 per 15-20 lines)
- Count DO/DON'T pairs (target: 5-10)
- Count complete workflows (target: 3-5)

---

## Benefits of This Standard

### For AI Agents
- ✅ Fast onboarding to new tools
- ✅ Copy-paste ready examples
- ✅ Clear decision tree (when to use what)
- ✅ Token-efficient reference

### For Tool Authors
- ✅ Structured documentation approach
- ✅ Forces concrete examples
- ✅ Increases tool adoption by AI agents
- ✅ Clear maintenance roadmap

### For Users
- ✅ Agents use tools correctly
- ✅ Fewer hallucinated commands
- ✅ Better workflow suggestions
- ✅ Faster problem solving

---

## Version History

### v1.0.0 (2025-11-30)
- 🎯 Initial standard definition
- 📋 Two-tier system (brief + full)
- 📚 Based on llms.txt specification
- ✨ Reference implementation in reveal CLI

---

## Related Standards

- **llms.txt:** https://llmstxt.org/ - Web documentation for LLMs
- **OpenAPI:** https://www.openapis.org/ - API documentation standard
- **man pages:** Traditional Unix documentation format

---

## License

This standard is released into the public domain. Tool authors are free to adopt, modify, and extend this standard without attribution.

---

## Contact

Questions or suggestions? Open an issue at:
- **reveal repo:** https://github.com/scottsen/reveal

---

**End of Standard**

Remember: **Examples are not optional. Every section needs concrete, tested, copy-paste code.**
