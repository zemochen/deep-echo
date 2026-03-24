---
name: project-docs-qa
description: Answer project-specific technical questions by referencing project documentation. Use when users ask about project architecture, implementation details, API usage, configuration, or technical decisions related to this codebase.
---

# Project Documentation Q&A

This Skill helps answer project-specific technical questions by finding and referencing project documentation.

## Instructions

When answering project-related questions, follow this process:

### 1. Search for documentation first

Look for documentation in these locations:
- `docs/` directory and subdirectories
- `README.md` files (root and subdirectories)
- `CONTRIBUTING.md`, `ARCHITECTURE.md`, `API.md`
- Inline code comments with `@docs` or similar markers

### 2. Use appropriate tools

- **Grep**: Search for keywords across documentation files
- **Read**: Read specific documentation files for detailed information
- **Glob**: Find all documentation files matching patterns

Example search patterns:
```bash
# Find all documentation files
glob "**/*.md"

# Search for specific topics
grep "authentication" docs/

# Search in README files
glob "**/README.md"
```

### 3. Reference documentation in answers

When providing answers:
- **Always cite sources**: Include file path and relevant section
- **Quote directly**: Use exact documentation language when possible
- **Provide context**: Explain why this documentation applies to the question
- **Link to files**: Use relative paths (e.g., `docs/api/auth.md`)

Example answer format:
```
According to [docs/api/authentication.md](docs/api/authentication.md):

> The project uses JWT tokens for authentication. Tokens are issued with a
> 24-hour expiration and must be refreshed using the `/api/refresh` endpoint.

To implement this in your code, see the example in the same file:
```

### 4. Handle missing documentation

If documentation doesn't exist for a topic:
1. Search the codebase for implementation examples
2. Base answers on actual code and patterns
3. Explicitly state: "Based on code analysis, not documented"
4. Suggest adding documentation if this is a common question

### 5. Prioritize project-specific context

Always consider:
- Project conventions and patterns
- Existing technical decisions
- Team preferences documented in CONTRIBUTING.md or similar
- Architecture decisions in ARCHITECTURE.md

## Search Strategy

### Start with specific searches
1. Search for exact keywords in documentation files
2. Search for related concepts (e.g., "auth" for "authentication")
3. Search in code comments if documentation is sparse

### Expand if needed
1. Look for similar patterns in the codebase
2. Check configuration files for implementation hints
3. Review package.json/requirements.txt for related libraries

## Documentation Structure

This project uses the following documentation structure (adjust as needed):

```
docs/
├── api/           # API documentation
├── architecture/  # System architecture and design decisions
├── guides/        # How-to guides and tutorials
├── reference/     # Technical reference materials
└── README.md      # Documentation index
```

## Examples

**Question**: "How do I authenticate API requests?"

**Answer**:
According to [docs/api/authentication.md](docs/api/authentication.md):

> API requests must include an `Authorization` header with a JWT token.
> Format: `Authorization: Bearer <token>`

To obtain a token, use the `/api/login` endpoint as documented in [docs/api/endpoints.md](docs/api/endpoints.md#login).

## Best Practices

- **Always verify** that documentation is current by checking modification dates
- **Cross-reference** related documentation files when topics overlap
- **Be specific** with file paths and section references
- **Acknowledge uncertainty** when documentation is ambiguous or outdated
- **Suggest updates** if documentation is missing or incorrect

## When Not to Use This Skill

Do not use for:
- General programming questions (use other resources)
- Questions about external libraries (consult official docs)
- Questions unrelated to this project
- Code changes or implementations (unless documentation-driven)

## Contributing

If you frequently answer the same questions, consider:
1. Adding documentation to `docs/`
2. Creating FAQ section in `docs/faq.md`
3. Updating this Skill to reference new documentation locations
