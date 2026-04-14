# ai-context-cli

**HTTP(S) → clean Markdown** for LLM context: `httpx` fetch → Readability → `markdownify`; optional **LiteLLM** summary with `--summary` (lazy-loaded — no LLM stack until you opt in).

```bash
# Markdown only (stdout stays pipe-clean; errors → stderr)
ai-context-cli "https://example.com/article"

# Same + LLM summary (loads .env from cwd for API keys)
ai-context-cli "https://example.com/article" --summary

# Verbose pipeline logs on stderr
ai-context-cli "https://example.com/article" --summary -v
```

Architecture and conventions: [SPEC.md](SPEC.md).

## ⚡ Why

Raw HTML wastes tokens. `ai-context-cli` is a small preprocessing step: one URL in, readable Markdown (and optionally a short summary) out.

## 🧩 What you get

- **Readability**-based main content extraction (`readability-lxml`)
- **Markdown** via `markdownify`
- **Optional LLM summary** via LiteLLM (`--summary`, `--model`)
- **Typed errors** → stable CLI exit codes (see [SPEC.md](SPEC.md) §7)

**Scope today:** `SOURCE` must be an **http(s) URL**. Local files and extra output formats are **planned** (see SPEC §5).

## 📦 Install

**From a clone (dev):**

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -e ".[dev]"
ai-context-cli --help
```

**From PyPI** (once published): `pip install ai-context-cli`

Requires **Python 3.11+**.

## 🤖 LLM providers (LiteLLM)

`--summary` uses [LiteLLM](https://github.com/BerriAI/litellm) model ids. Set the provider’s **native** env vars (also read from a `.env` in the working directory when `--summary` is used).

| Provider | Example `--model` | Credentials |
|----------|-------------------|---------------|
| **OpenAI** | `gpt-4o-mini` (default if `--model` omitted) | `OPENAI_API_KEY` |
| **Anthropic** | `anthropic/claude-3-5-sonnet-latest` | `ANTHROPIC_API_KEY` |
| **OpenRouter** | `openrouter/openai/gpt-4o-mini` (pick any model slug OpenRouter exposes) | `OPENROUTER_API_KEY` |
| **Ollama** (local) | `ollama/llama3` | Optional: `OLLAMA_API_BASE` (default `http://localhost:11434`) |

```bash
ai-context-cli "https://example.com/article" --summary --model "openrouter/openai/gpt-4o-mini"
ai-context-cli "https://example.com/article" --summary --model "ollama/llama3"
```

See [.env.example](.env.example) for other keys (`MISTRAL_API_KEY`, timeouts, etc.).

## 🧪 Tests & lint

```bash
pytest
ruff check .
ruff format --check .
mypy src
```

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) (layers, ports/adapters, where to put code).

## 📄 License

MIT — see [LICENSE](LICENSE).
