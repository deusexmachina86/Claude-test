# uv Skill — Python Package & Project Management

A cheatsheet and quick-reference for using **uv** and the `uvw` wrapper script in this repo.

---

## What is uv?

uv is a single, Rust-powered tool that replaces `pip`, `pip-tools`, `pipx`, `poetry`, `pyenv`, `virtualenv`, and more.
Key selling point: **10–20× faster** than the tools it replaces.

---

## Installation

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## uvw — wrapper script

`uv_wrapper.py` provides a friendlier `uvw` interface over raw uv commands.

```bash
# Make it executable (once)
chmod +x uv_wrapper.py

# Optional: put it on your PATH
ln -s "$PWD/uv_wrapper.py" ~/.local/bin/uvw
```

---

## Quick-reference

### Project lifecycle

| Task | uvw command | Raw uv equivalent |
|------|-------------|-------------------|
| Create a new project | `uvw init myproject` | `uv init myproject` |
| Install / sync dependencies | `uvw install` | `uv sync` |
| Install without dev deps | `uvw install --no-dev` | `uv sync --no-group dev` |
| Run a script / command | `uvw run manage.py runserver` | `uv run manage.py runserver` |

### Dependency management

| Task | uvw command | Raw uv equivalent |
|------|-------------|-------------------|
| Add a package | `uvw add requests` | `uv add requests` |
| Add a dev dependency | `uvw add --dev pytest` | `uv add --dev pytest` |
| Add to a named group | `uvw add --group prod gunicorn` | `uv add --group prod gunicorn` |
| Remove a package | `uvw remove requests` | `uv remove requests` |
| Upgrade one package | `uvw upgrade requests` | `uv sync --upgrade-package requests` |
| Upgrade all packages | `uvw upgrade` | `uv lock --upgrade` |

### Python & tools

| Task | uvw command | Raw uv equivalent |
|------|-------------|-------------------|
| Install Python 3.12 | `uvw python 3.12` | `uv python install 3.12` |
| Run a one-off tool | `uvw tool pycowsay hello` | `uvx pycowsay hello` |
| Run tool from package | `uvw tool --from django django-admin startproject x` | `uv tool run --from django django-admin startproject x` |

---

## Key files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Declares direct dependencies (like `requirements.in`) |
| `uv.lock` | Pinned, cross-platform lock file (like `requirements.txt`) — commit this |
| `.venv/` | Local virtual environment — do **not** commit |

---

## Docker (production)

```dockerfile
# Copy uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-group dev --group prod

# In the runtime stage, put the venv first on PATH
ENV PATH="/app/.venv/bin:$PATH"
```

---

## Resources

- [uv documentation](https://docs.astral.sh/uv/)
- [uv GitHub](https://github.com/astral-sh/uv)
- [Charlie Marsh's talk on uv internals](https://www.youtube.com/watch?v=gSKTfG1GXYQ)
- [Using uv with Docker — Hynek Schlawack](https://hynek.me/articles/docker-uv/)
