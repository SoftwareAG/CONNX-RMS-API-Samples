# Contributing

## Before opening a change

- Keep `.env` and all CONNX credentials out of commits, logs, screenshots, and issues.
- Keep the samples read-only. Do not add code that writes to RMS files.
- Keep application code behind the repository boundary; do not spread ODBC details through API handlers or examples.
- Preserve strict ANSI-92 compatibility for SQL sent through CONNX.

## Validation

From `python/`:

```powershell
pip install -c constraints.txt -e ".[dev]"
ruff check .
pytest
```

GitHub Actions (`.github/workflows/ci.yml`) runs the same Ruff and pytest checks on Python 3.11–3.13, builds the .NET sample, and compiles the Java sample on every push to `main` and every pull request. CI has no CONNX connection; tests use test doubles for the ODBC layer.

## Dependencies

`python/pyproject.toml` declares the supported version ranges. `python/constraints.txt` pins the exact versions the samples are validated with; CI and the README install with it. An extra CI job on Python 3.13 installs the newest versions the ranges allow, as an early warning; it does not fail the run.

After changing dependencies in `pyproject.toml`, or to move to newer versions, regenerate the pins with [uv](https://docs.astral.sh/uv/) from `python/`, using the command recorded at the top of `constraints.txt`:

```powershell
uv pip compile pyproject.toml --extra dev --universal --python-version 3.11 --annotation-style line -o constraints.txt
```

`--universal` produces one file valid on Windows, Linux, and macOS for Python 3.11 and later. Run Ruff and pytest before committing the updated file.

If a CONNX environment is available, also run `python smoketest.py` and verify `/health`, `/ready`, and the read-only API endpoints. Build the .NET sample with `dotnet restore` and `dotnet build` when the .NET SDK is available.

## Pull requests

Describe the RMS mapping assumptions, configuration changes, and validation performed. Do not include vendor driver binaries or JDBC JARs unless their redistribution terms have been reviewed.
