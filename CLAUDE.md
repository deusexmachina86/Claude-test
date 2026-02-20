# CLAUDE.md

This file provides guidance to AI assistants (Claude and others) working in this repository.

## Repository Status

This repository is currently **empty** — no source files, build system, or configuration have been committed yet. This CLAUDE.md serves as a foundation to be updated as the project evolves.

When the project takes shape, update each section below to reflect the actual codebase.

---

## Project Overview

> **TODO:** Replace this section with a description of the project: its purpose, the problem it solves, and its primary users.

---

## Repository Structure

> **TODO:** Document the directory layout once source files exist. Example format:

```
.
├── src/           # Application source code
├── tests/         # Test files
├── docs/          # Documentation
├── scripts/       # Utility / automation scripts
└── CLAUDE.md      # This file
```

---

## Development Setup

### Prerequisites

> **TODO:** List required tools, runtimes, and versions (e.g., Node ≥ 20, Python ≥ 3.11, Go ≥ 1.22).

### Installation

> **TODO:** Provide the commands needed to get a local environment running, for example:

```bash
# Clone the repository
git clone <repo-url>
cd <repo-name>

# Install dependencies (adjust for actual package manager)
npm install        # Node.js
pip install -e .   # Python
go mod download    # Go
```

### Environment Variables

> **TODO:** List required environment variables and where to obtain them. Never commit secrets.

---

## Common Commands

> **TODO:** Fill in actual commands once the build system is established.

| Task | Command |
|------|---------|
| Install dependencies | `<command>` |
| Run development server | `<command>` |
| Run all tests | `<command>` |
| Run linter | `<command>` |
| Format code | `<command>` |
| Build for production | `<command>` |

---

## Testing

> **TODO:** Describe the test framework, how to run tests, and any conventions for writing them.

- **Framework:** TBD
- **Run tests:** `<command>`
- **Run a single test:** `<command>`
- **Coverage report:** `<command>`

### Testing Conventions

- Test files should live adjacent to source files or in a top-level `tests/` directory.
- Each public function/module should have corresponding tests.
- Prefer unit tests for pure logic and integration tests for I/O boundaries.

---

## Code Style and Conventions

> **TODO:** Update with project-specific linting / formatting tools and rules.

### General

- Favour clarity over cleverness.
- Keep functions small and focused on a single responsibility.
- Avoid premature abstraction — three similar lines of code is better than a premature utility function.
- Delete unused code rather than commenting it out.

### Naming

- Use descriptive names that convey intent.
- Follow the conventions of the language in use (e.g., `snake_case` for Python, `camelCase` for JavaScript/TypeScript, `PascalCase` for exported Go identifiers).

### Comments

- Write comments to explain **why**, not **what**.
- Do not leave TODO comments in committed code unless they are tracked in the issue tracker.

### Error Handling

- Handle errors explicitly at the boundary where they occur.
- Do not swallow errors silently.
- Provide context when re-throwing or wrapping errors.

---

## Git Workflow

### Branches

- `main` — production-ready code; direct commits are restricted.
- `claude/<description>-<id>` — branches used by AI assistants.
- Feature branches follow the pattern `<type>/<short-description>` (e.g., `feat/user-auth`, `fix/null-pointer`).

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<optional scope>): <short summary>

<optional body>

<optional footer>
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples:**

```
feat(auth): add OAuth2 login support
fix(api): handle empty response from upstream service
docs: update CLAUDE.md with project structure
```

### Pull Requests

- Keep PRs focused — one logical change per PR.
- Include a clear description of what changed and why.
- Ensure all CI checks pass before requesting review.
- Reference related issues with `Closes #<issue-number>`.

---

## CI/CD

> **TODO:** Describe the CI/CD pipeline once configured (e.g., GitHub Actions workflows, deployment targets, required checks).

---

## Security

- Never commit credentials, API keys, tokens, or other secrets.
- Use environment variables or a secrets manager for sensitive values.
- Validate and sanitize all external input (user input, API responses, file contents).
- Follow the principle of least privilege for service accounts and API tokens.

---

## Working with AI Assistants

The following guidelines apply specifically when Claude or another AI assistant is working in this repository.

### Before Making Changes

1. Read relevant existing files before editing them.
2. Understand the existing patterns and conventions before introducing new ones.
3. Prefer editing existing files over creating new ones.

### Scope of Changes

- Make only the changes required to complete the stated task.
- Do not refactor surrounding code unless explicitly asked.
- Do not add comments, docstrings, or type annotations to code that was not changed.
- Do not add error handling for scenarios that cannot occur.

### Commits and Pushes

- Commit with descriptive messages following the Conventional Commits format above.
- Push to the designated feature branch (`claude/<description>-<id>`), never directly to `main`.
- Do not force-push without explicit instruction.

### When in Doubt

- Ask a clarifying question rather than making assumptions.
- Prefer the simplest solution that satisfies the requirement.
- If multiple valid approaches exist, explain the trade-offs and ask for a preference.

---

## Updating This File

This file should be kept current as the project grows. Update it whenever:

- A new tool, framework, or dependency is added.
- The directory structure changes significantly.
- New conventions or workflows are established.
- CI/CD configuration changes.
