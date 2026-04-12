# Contributing to ai-context

Thanks for improving the project. Keep changes focused, typed, and aligned with the dependency rule below.

## Architecture (light DDD)

Dependencies flow **inward**: `interfaces` → `application` → `domain` ← `infrastructure`.

```text
interfaces/     Typer CLI — parsing, wiring adapters, exit codes
application/    Use cases (orchestration), no httpx/typer/litellm imports
domain/         Models, ports (ABCs), exceptions — zero infra imports
infrastructure/ Http fetcher, Readability, LiteLLM summarizer, markdown helpers
```

- **Domain** defines *what* the system is (ports like `ContentFetcher`, `Summarizer`).
- **Infrastructure** implements those ports (*how*).
- **Application** runs the pipeline with injected implementations.
- **Interfaces** builds the graph for the CLI.

**Do not** put business rules in `infrastructure/`. If you need a new behavior, extend a port in `domain/ports.py`, implement it under `infrastructure/`, and wire it from `interfaces/cli.py` (or a small factory there).

See [SPEC.md](SPEC.md) §6 for the canonical description.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

## Checks before you open a PR

```bash
ruff check .
ruff format .
pytest
mypy src
```

- **Ruff** is the linter/formatter (`pyproject.toml` → `[tool.ruff]`).
- **pytest** + **pytest-httpx** for HTTP fakes (no real network in CI for unit/integration tests).
- **mypy** strict mode is enabled; match existing typing style.

## Packaging

The wheel is built with **Hatchling** (`hatchling.build`). You do not need the `hatch` CLI for day-to-day work; `pip install -e ".[dev]"` is enough.

## Tests

- Prefer **pytest** modules under `tests/` mirroring `src/ai_context/`.
- Mark real-network tests with `@pytest.mark.e2e` (skipped unless `TEST_E2E=true`).

## Questions

Open a [GitHub issue](https://github.com/Hushout/ai-context/issues) or discuss on your PR.
