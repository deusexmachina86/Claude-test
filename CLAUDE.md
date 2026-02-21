# CLAUDE.md

This file provides guidance to AI assistants (Claude and others) working in this repository.

## Repository Status

Active development — milestone 1 (Toilet Listings + Geolocation) is complete.

---

## Project Overview

**Toilet Finder** — a REST API for storing and querying public toilet locations by geographic proximity. Built with FastAPI, PostgreSQL, and PostGIS.

The core value proposition is `GET /toilets/nearby?lat=x&lng=y&radius=500`, which returns toilets sorted by distance using PostGIS `ST_DWithin` + `ST_Distance` on a `geography` column.

---

## Repository Structure

```
.
├── app/
│   ├── main.py        # FastAPI app, lifespan (DB init)
│   ├── config.py      # Settings via pydantic-settings
│   ├── database.py    # SQLAlchemy engine, session, Base, init_db()
│   ├── models.py      # Toilet ORM model with PostGIS Geography column
│   ├── schemas.py     # Pydantic request/response schemas
│   └── routers/
│       └── toilets.py # POST /toilets, GET /toilets/{id}, GET /toilets/nearby
├── scripts/
│   └── seed.py        # Seed DB with ~8 London toilet fixtures
├── docker-compose.yml # postgis/postgis:16-3.4 + API service
├── Dockerfile
├── requirements.txt
├── .env.example
└── CLAUDE.md
```

---

## Development Setup

### Prerequisites

- Docker + Docker Compose (recommended)
- **or** Python ≥ 3.12 + a running PostgreSQL 16 instance with PostGIS 3.4

### Installation (Docker — recommended)

```bash
docker compose up --build
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Installation (local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL as needed
uvicorn app.main:app --reload
```

### Seed data

```bash
# Inside the container:
docker compose exec api python -m scripts.seed

# Or locally (with .venv active):
python -m scripts.seed
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://toilets:toilets@localhost:5432/toilets` | SQLAlchemy DSN |

---

## Common Commands

| Task | Command |
|------|---------|
| Start services | `docker compose up --build` |
| Run API only (local) | `uvicorn app.main:app --reload` |
| Seed database | `python -m scripts.seed` |
| Interactive API docs | `http://localhost:8000/docs` |

---

## Testing

- **Framework:** pytest (not yet configured — next step)
- Tests will live in `tests/` mirroring the `app/` structure.

### Testing Conventions

- Test files should live in a top-level `tests/` directory.
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
