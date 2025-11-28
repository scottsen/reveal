# Reveal Roadmap

> **Vision:** Transform reveal from a code file explorer into a universal resource explorer

---

## 🎯 The Big Picture

Reveal already makes exploring code effortless. Imagine extending that same progressive disclosure pattern to **any structured resource**:

```bash
# Code files (✅ shipped)
reveal app.py                    # See structure
reveal app.py load_config        # Extract function

# Environment variables (✅ shipped v0.11.0)
reveal env://                    # See all variables
reveal env://DATABASE_URL        # Get specific variable

# Coming soon...
reveal postgres://prod           # Database schemas
reveal https://api.github.com    # API endpoints
reveal docker://container        # Container inspection
```

**One tool. One pattern. Any resource.**

---

## 🚀 What We've Shipped

### ✅ v0.11.0 - URI Adapter Foundation (Nov 2025)

**First non-file adapter: `env://`**

```bash
reveal env://                    # List all environment variables
reveal env://DATABASE_URL        # Get specific variable
reveal env:// --format=json      # JSON output for scripting
```

**Why this matters:**
- Proves the adapter architecture works
- Establishes patterns for future adapters
- Demonstrates optional dependency system
- Shows secure credential handling

**What we learned:**
- URI routing works elegantly
- Adapter protocol is flexible
- Output format consistency is key
- Graceful degradation is critical

---

## 🗺️ What's Next

### Phase 1: Database Adapters (v0.12.0 - v0.14.0)

**Goal:** Explore database schemas with the same ease as code files

```bash
pip install reveal-cli[database]

# Explore schema
reveal postgres://prod
reveal postgres://prod users      # Table structure
reveal postgres://prod users id   # Column details

# Compare environments
reveal postgres://prod users > prod.txt
reveal postgres://staging users > staging.txt
diff prod.txt staging.txt
```

**Adapters:**
- `postgres://` - PostgreSQL schemas, tables, columns
- `mysql://` - MySQL databases
- `sqlite://` - SQLite files
- `redis://` - Redis keys and data structures

**Status:** Design complete, implementation starting

---

### Phase 2: API Adapters (v0.15.0 - v0.16.0)

**Goal:** Discover API endpoints before building integrations

```bash
pip install reveal-cli[api]

# REST APIs
reveal https://api.github.com
reveal https://api.github.com/users/:username

# OpenAPI/Swagger
reveal openapi://https://petstore.swagger.io/v2/swagger.json

# GraphQL
reveal graphql://https://api.github.com/graphql
```

**Adapters:**
- `https://` - REST API exploration
- `openapi://` - Swagger/OpenAPI spec parsing
- `graphql://` - GraphQL schema introspection

**Key features:**
- Automatic authentication (API keys, Bearer tokens)
- Rate limit handling
- Response caching
- Request/response examples

**Status:** Architecture designed

---

### Phase 3: Container & Cloud Adapters (v0.17.0+)

**Goal:** Inspect containers and cloud resources

```bash
pip install reveal-cli[container]

# Docker
reveal docker://my-app-prod
reveal docker://my-app-prod --env     # Environment variables
reveal docker://my-app-prod --volumes # Volume mounts

# Docker Compose
reveal docker-compose://web

# Cloud (future)
reveal s3://my-bucket
reveal k8s://my-cluster/my-pod
```

**Status:** Early research

---

### Phase 4: Plugin Ecosystem (v2.0.0)

**Goal:** Enable community-contributed adapters

```bash
# Install third-party adapters
pip install reveal-adapter-mongodb
pip install reveal-adapter-elasticsearch

# Use them immediately
reveal mongodb://prod
reveal elasticsearch://logs
```

**Vision:**
- Adapter marketplace/registry
- Standard adapter template
- Plugin discovery system
- Community governance

**Status:** Design phase

---

## 💡 Core Design Principles

### 1. **Progressive Disclosure**
```bash
reveal postgres://prod              # Overview: all tables
reveal postgres://prod users        # Details: table structure
reveal postgres://prod users email  # Specific: column details
```

### 2. **Optional Dependencies**
```bash
pip install reveal-cli              # Core only (files, env)
pip install reveal-cli[database]    # Add database adapters
pip install reveal-cli[all]         # Everything
```

Keep core lightweight. Add features as needed.

### 3. **Secure by Default**
```yaml
# ~/.reveal/config.yaml
connections:
  prod:
    type: postgres
    host: prod.example.com
    database: mydb
    username: readonly
    password: ${POSTGRES_PROD_PASSWORD}  # From environment
```

```bash
# No credentials in shell history!
reveal postgres://prod
```

### 4. **Consistent Output**
Every adapter supports:
- Text output (human-readable)
- JSON output (`--format=json`)
- Grep-compatible output (`--format=grep`)

### 5. **Graceful Degradation**
```
❌ Adapter 'postgres' is not available.
Required packages: psycopg2-binary
Install with: pip install reveal-cli[database]
```

Clear errors. Helpful guidance.

---

## 🎯 Use Cases

### For Developers
```bash
# Quick schema check before migration
reveal postgres://prod users

# Compare prod vs staging
diff <(reveal postgres://prod users) <(reveal postgres://staging users)

# Explore API before integration
reveal https://api.stripe.com

# Debug container environment
reveal docker://my-app | grep DATABASE_
```

### For AI Agents
```bash
# Token-efficient exploration across resources
reveal app.py get_user           # Code: how does it work?
reveal postgres://prod users     # Database: what's the schema?
reveal https://api.internal user # API: what's the contract?

# Same pattern, consistent output, minimal tokens
```

### For DevOps
```bash
# Verify container configuration
reveal docker://production-web --env | grep -i secret

# Check database connections
reveal postgres://prod --meta

# Monitor API health
watch -n 5 reveal https://api.internal/health
```

---

## 🤝 How to Contribute

### Pick Your Adventure

**Want to build an adapter?**
- See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for current file analyzer patterns
- See [internal planning docs] for URI adapter architecture (ask maintainers)
- Start with a simple adapter (Redis, SQLite)

**Want to improve existing features?**
- Better error messages
- Performance optimizations
- Documentation improvements
- Test coverage

**Want to discuss the roadmap?**
- Open an issue with `[Roadmap]` tag
- Join discussions
- Share your use cases

### Good First Issues

- Implement SQLite adapter (simpler than PostgreSQL)
- Add Redis adapter (key-value exploration)
- Improve env:// adapter (better categorization)
- Write adapter developer guide

---

## 📊 Success Metrics

**Technical:**
- ✅ Core install < 5MB
- ✅ File operations < 100ms startup
- ✅ Zero credential leakage
- ✅ 100% test coverage on adapter protocol

**Adoption:**
- 🎯 50+ adapters (including community)
- 🎯 1,000+ downloads of adapter extras
- 🎯 10+ community-contributed adapters
- 🎯 Featured in AI agent toolkits

**Quality:**
- 🎯 Comprehensive docs for each adapter
- 🎯 Security audit completed
- 🎯 Performance benchmarks published

---

## 🔐 Security First

**Built-in protections:**
- Never log passwords (sanitized URIs in logs)
- Named connections prevent shell history exposure
- Environment variable resolution for secrets
- Read-only by default (no mutations without explicit flags)
- Connection timeouts and rate limits

**Security checklist:**
- [x] Credential protection in env:// adapter
- [ ] Security docs for adapter developers
- [ ] Penetration testing (when ecosystem grows)
- [ ] CVE monitoring for dependencies

---

## 🤔 Open Questions

**We'd love your input on:**

1. **Write operations:** Should reveal support mutations?
   ```bash
   reveal postgres://prod --execute "CREATE INDEX..."
   ```
   Pro: Complete tool | Con: Safety concerns, scope creep

2. **Data preview:** Should reveal show sample data?
   ```bash
   reveal postgres://prod users --sample 10
   ```
   Pro: More useful | Con: Privacy/security concerns

3. **Interactive mode:** Should there be a REPL?
   ```bash
   reveal postgres://prod --interactive
   ```
   Pro: Better exploration | Con: Different UX paradigm

4. **Cloud adapters:** Which cloud resources matter most?
   - AWS (S3, DynamoDB, Lambda)?
   - GCP (BigQuery, Cloud Storage)?
   - Azure (Blob Storage, Cosmos DB)?

**Share your thoughts in [Discussions](https://github.com/scottsen/reveal/discussions)!**

---

## 📅 Timeline

This is **community-driven** development. Timeline depends on contributor interest and availability.

**Rough estimates:**
- **Phase 1** (Database adapters): 2-4 months
- **Phase 2** (API adapters): 2-3 months
- **Phase 3** (Containers/Cloud): 3-6 months
- **Phase 4** (Plugin ecosystem): Ongoing

**Want to accelerate?** [Contribute!](CONTRIBUTING.md)

---

## 🌟 Why This Matters

**For the reveal project:**
- Expanded use cases beyond code files
- Community-driven ecosystem
- Unique value proposition in the ecosystem

**For developers:**
- One tool for all exploration needs
- Consistent UX across resource types
- Terminal-first, fast, composable

**For AI agents:**
- Token-efficient progressive disclosure
- Consistent output format
- Reduces tool proliferation

---

## 💬 Stay Connected

- **Questions?** Open a [Discussion](https://github.com/scottsen/reveal/discussions)
- **Ideas?** File an [Issue](https://github.com/scottsen/reveal/issues)
- **Want to help?** See [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Last updated:** 2025-11-27
**Current version:** v0.11.0
**Next milestone:** v0.12.0 (PostgreSQL adapter)
