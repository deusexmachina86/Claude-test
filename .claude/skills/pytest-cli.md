---
name: pytest-cli
description: Runs Python tests via the pytest-cli wrapper. Use when the user needs to run tests, filter by keyword or marker, check coverage, list fixtures/markers, debug failures, re-run failed tests, or collect test suites.
allowed-tools: Bash(pytest-cli:*)
---

# Python Testing with pytest-cli

`pytest-cli` is a thin stateful wrapper around `pytest`. It records the result of every run so you can quickly re-run failures, check status, and build up test invocations incrementally.

## Quick start

```bash
# run the whole suite
pytest-cli run

# run a single file or directory
pytest-cli run tests/test_auth.py

# filter by name
pytest-cli run -k "login"

# re-run only what failed last time
pytest-cli last-failed

# check what happened in the last run
pytest-cli status
```

## Commands

### Core

```bash
pytest-cli run
pytest-cli run tests/
pytest-cli run tests/test_auth.py
pytest-cli run tests/test_auth.py::TestLogin::test_valid_user
pytest-cli run -k "login or logout"
pytest-cli run -m smoke
pytest-cli run -v
pytest-cli run -q
pytest-cli run -x                        # stop on first failure
pytest-cli run --maxfail=3
pytest-cli run --tb=short                # short | long | no | line | native | auto
pytest-cli run --timeout=30
pytest-cli run -- --strict-markers       # pass extra args after --
```

### Re-running failures

```bash
pytest-cli last-failed                   # alias: lf
pytest-cli last-failed -v
pytest-cli rerun                         # repeat exact last invocation
```

### Discovery

```bash
pytest-cli collect
pytest-cli collect tests/
pytest-cli collect -k "api"
pytest-cli collect -m integration
pytest-cli markers                       # list registered markers
pytest-cli fixtures                      # list available fixtures
pytest-cli fixtures tests/conftest.py
```

### Coverage

```bash
pytest-cli coverage                      # alias: cov
pytest-cli coverage tests/
pytest-cli coverage --source=src/
pytest-cli coverage --html               # generates htmlcov/
pytest-cli coverage --xml                # generates coverage.xml
pytest-cli coverage --fail-under=90
pytest-cli coverage --source=mypackage --html --fail-under=80
```

### Debugging

```bash
pytest-cli debug                         # runs with -s --tb=long
pytest-cli debug tests/test_api.py
pytest-cli debug -k "slow_test"
```

### Parallel (requires pytest-xdist)

```bash
pytest-cli parallel                      # alias: par  (auto workers)
pytest-cli parallel -n 4
pytest-cli parallel tests/unit/
```

### State management

```bash
pytest-cli status                        # show last run result + failures
pytest-cli clear                         # delete saved state
```

## State file

`pytest-cli` writes `.pytest-cli-state.json` in the working directory after every run. It records:

- `last_failed` — list of node IDs that failed
- `last_exit_code` — pytest exit code
- `last_args` — the pytest arguments that were used

Add `.pytest-cli-state.json` to `.gitignore` to avoid committing it.

## Examples

### Run and iterate on failures

```bash
pytest-cli run tests/
pytest-cli status
pytest-cli last-failed -v
pytest-cli last-failed
pytest-cli status
```

### Focused debug session

```bash
pytest-cli collect -k "checkout"
pytest-cli debug -k "checkout"
pytest-cli run -k "checkout" --tb=short
```

### CI pipeline

```bash
pytest-cli coverage --source=src/ --xml --fail-under=85
```

### Parallel smoke tests

```bash
pytest-cli parallel -m smoke -n 4
pytest-cli status
```

### Filter by marker and keyword together

```bash
pytest-cli run -m "not slow" -k "api" -q
```
