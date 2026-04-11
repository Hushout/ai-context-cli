# SPEC — ai-context

> CLI Python qui transforme une URL ou un fichier en Markdown propre, résumé clair et structure lisible par IA.

---

## 1. Problem Statement

Les LLMs sont sensibles au bruit. HTML brut, boilerplate, publicités et menus de navigation dégradent la qualité du contexte. `ai-context` agit comme couche de pré-traitement : étant donné une URL ou un fichier local, il produit une représentation propre, structurée et économe en tokens, prête à être injectée dans un prompt.

---

## 2. Goals

| Goal | Description |
|------|-------------|
| **Markdown propre** | Supprimer tout le bruit HTML. Garder uniquement le contenu sémantique (titres, paragraphes, listes, blocs de code, tableaux). |
| **Résumé** | Produire un résumé court — extractif ou assisté par LLM. |
| **Structure IA** | Émettre un document JSON/YAML décrivant la hiérarchie du contenu (titre, sections, entités clés). |
| **Composabilité** | La sortie peut aller vers stdout, un fichier, ou être pipée dans un autre outil. |
| **Dépendances minimales** | Priorité aux libs Python standard et bien maintenues. |

## 3. Non-Goals (v1)

- Pas de rendu JavaScript / automatisation navigateur (reporté v2 via Playwright).
- Pas de stockage persistant ni d'indexation.
- Pas d'interface graphique.
- Pas de gestion des flux d'authentification sur les URLs protégées.

---

## 4. Stack Technique

| Composant | Lib | Justification |
|-----------|-----|---------------|
| CLI | `typer` | Basé sur Click, type hints natifs, cohérence avec Pydantic |
| Validation données | `pydantic` v2 | Contrats stricts, sérialisation JSON/YAML intégrée |
| HTTP | `httpx` | Async-capable, moderne, meilleur que `requests` |
| Extraction contenu | `readability-lxml` | Port Python de Mozilla Readability |
| HTML → Markdown | `markdownify` | Léger, configurable |
| Sortie terminal | `rich` | Logs, couleurs, progress (s'intègre nativement avec Typer) |
| YAML | `pyyaml` | Stdlib-like, standard |
| Tests | `pytest` + `pytest-httpx` | Fixtures, mocking HTTP sans serveur réel |
| Packaging | `pyproject.toml` (hatchling) | Standard PEP 517/518 |

**Pas de SDK LLM** en v1 — l'interface `Summarizer` est prévue pour le swap en v1.1.

---

## 5. CLI Interface

### Usage

```
ai-context [OPTIONS] SOURCE
```

**Portée actuelle du dépôt** : seules certaines lignes du tableau ci-dessous sont implémentées. La colonne **Status** indique ce qui existe réellement dans `interfaces/cli.py` par rapport à la feuille de route v1.

`SOURCE` est aujourd’hui **uniquement** une URL HTTP(S) (`https://...`). Les chemins de fichier locaux et les autres schémas relèvent de **Planned v1.x** (voir `source_gate` et tickets associés).

### Options

| Option / entrée | Type | Défaut | Description | Status |
|-----------------|------|--------|-------------|--------|
| `--url` | — | — | **Pas de flag `--url` en ligne de commande.** L’URL est passée comme argument positionnel `SOURCE` (ex. `ai-context "https://…"`). Capacité « URL en entrée » : **Implemented** via `SOURCE`. | **Implemented** |
| `SOURCE` | `str` | *requis* | URL HTTP(S) à récupérer et convertir en Markdown (argument positionnel Typer). | **Implemented** |
| `--summary` / `--no-summary` | `bool` | `False` | Ajouter un résumé extractif minimal (trois premières phrases à partir du HTML article). | **Implemented** |
| `--verbose`, `-v` | `bool` | `False` | Journaliser les étapes du pipeline sur stderr (Rich). | **Implemented** |
| `--output`, `-o` | `Path` | stdout | Chemin de sortie | **Planned v1.x** |
| `--format`, `-f` | `markdown\|json\|yaml\|all` | `markdown` | Format de sortie | **Planned v1.x** |
| `--structure` / `--no-structure` | `bool` | `False` | Ajouter la structure IA | **Planned v1.x** |
| `--max-tokens` | `int` | — | Tronquer la sortie à ~N tokens | **Planned v1.x** |
| `--version` | | | Afficher la version et quitter | **Planned v1.x** |

### Exemples

```bash
# Minimal : Markdown vers stdout (comportement actuel)
ai-context https://example.com/article

# Avec résumé extractif et logs (comportement actuel)
ai-context https://example.com/article --summary --verbose

# Exemples cibles v1.x (options non encore câblées dans le CLI)
# ai-context https://example.com/article --format all -o ./output/
# ai-context ./page.html --format markdown --summary
# ai-context https://example.com --format json | jq '.meta.estimatedTokens'
```

---

## 6. Architecture (DDD Léger)

### 6.1 Vue d'ensemble des couches

```
┌─────────────────────────────────────────────────────────┐
│  interfaces/          CLI Typer — couche la plus mince   │
├─────────────────────────────────────────────────────────┤
│  application/         Use Cases — orchestration          │
├─────────────────────────────────────────────────────────┤
│  domain/              Modèles Pydantic, Ports, Exceptions│
├─────────────────────────────────────────────────────────┤
│  infrastructure/      Adaptateurs concrets (HTTP, fs...) │
└─────────────────────────────────────────────────────────┘
```

**Règle de dépendance** : les couches hautes dépendent des couches basses. Le `domain` ne dépend de rien. L'`infrastructure` dépend du `domain` (implémente ses ports), jamais l'inverse.

### 6.2 Domain Layer — `src/ai_context/domain/`

Cœur métier pur. Aucune dépendance sur httpx, typer, ou toute lib d'infrastructure.

#### Ports (interfaces abstraites)

```python
# domain/ports.py

from abc import ABC, abstractmethod
from collections.abc import Callable
from .models import ExtractedContent, ProcessedContent, RawContent

class ContentFetcher(ABC):
    @abstractmethod
    def fetch(self, source: str) -> RawContent: ...

class ContentExtractor(ABC):
    @abstractmethod
    def extract(self, raw: RawContent) -> ExtractedContent: ...  # titre + HTML article

class Summarizer(ABC):
    @abstractmethod
    def summarize(self, text: str) -> str: ...

class OutputFormatter(ABC):
    @abstractmethod
    def format(self, content: ProcessedContent) -> str: ...
```

#### Value Objects / Modèles Pydantic

```python
# domain/models.py

from pydantic import BaseModel, HttpUrl
from datetime import datetime

class ExtractedContent(BaseModel):
    title: str
    cleaned_html: str

class RawContent(BaseModel):
    source: str
    html: str | None = None
    text: str | None = None
    mime_type: str

class Section(BaseModel):
    heading: str
    level: int  # 1-6
    subsections: list["Section"] = []

class ContentStructure(BaseModel):
    title: str
    sections: list[Section]
    entities: list[str] = []

class ContentMeta(BaseModel):
    word_count: int
    estimated_tokens: int
    extracted_at: datetime
    processing_ms: int

class ProcessedContent(BaseModel):
    source: str
    title: str
    markdown: str
    summary: str | None = None
    structure: ContentStructure | None = None
    meta: ContentMeta
```

#### Exceptions métier

```python
# domain/exceptions.py

class AiContextError(Exception): ...
class NetworkError(AiContextError): ...
class ParseError(AiContextError): ...
class SourceNotFoundError(AiContextError): ...   # not FileNotFoundError — avoids shadowing Python builtin
class UnsupportedFormatError(AiContextError): ...
class OutputError(AiContextError): ...
```

### 6.3 Application Layer — `src/ai_context/application/`

Un seul use case en v1 : `ProcessSourceUseCase`. Il reçoit les ports par injection de dépendances (pas d'import direct d'infrastructure). La conversion HTML → Markdown est injectée sous forme de callable (`html_to_markdown`) depuis la couche interface pour éviter qu'`application` importe `markdownify`.

```python
# application/process_source.py

from collections.abc import Callable

@dataclass
class ProcessSourceCommand:
    source: str
    include_summary: bool = False
    include_structure: bool = False
    max_tokens: int | None = None

class ProcessSourceUseCase:
    def __init__(
        self,
        fetcher: ContentFetcher,
        extractor: ContentExtractor,
        html_to_markdown: Callable[[str], str],
    ) -> None: ...

    def execute(self, cmd: ProcessSourceCommand) -> ProcessedContent: ...
```

### 6.4 Infrastructure Layer — `src/ai_context/infrastructure/`

Implémentations concrètes des ports.

| Module | Port implémenté | Lib utilisée |
|--------|----------------|--------------|
| `fetchers/http_fetcher.py` | `ContentFetcher` | `httpx` |
| `fetchers/file_fetcher.py` | `ContentFetcher` | `pathlib` |
| `extractors/readability_extractor.py` | `ContentExtractor` | `readability-lxml` |
| `processors/markdown_converter.py` | — | `markdownify` |
| `processors/extractive_summarizer.py` | `Summarizer` | scoring maison |
| `processors/structure_analyzer.py` | — | parsing Markdown natif |
| `formatters/markdown_formatter.py` | `OutputFormatter` | — |
| `formatters/json_formatter.py` | `OutputFormatter` | Pydantic `.model_dump_json()` |
| `formatters/yaml_formatter.py` | `OutputFormatter` | `pyyaml` |
| `formatters/all_formatter.py` | `OutputFormatter` | Combine les trois |

**HTTP fetcher (implémenté, v1)** — `HttpContentFetcher` dans `fetchers/http_fetcher.py` :

- Client synchrone `httpx.Client` (pas d’`asyncio` en CLI v1) ; la méthode `_perform_get(client, url)` centralise le `GET` et `raise_for_status()` pour pouvoir être recopiée plus tard en variante async avec `httpx.AsyncClient`.
- Timeout par défaut **10 s** ; surcharge via variable d’environnement `AI_CONTEXT_FETCH_TIMEOUT` (valeur en **millisecondes**, comme documenté en §8).
- En-tête **User-Agent** explicite (chaîne du projet) pour limiter les blocages triviaux.
- Toute réponse **non 2xx** (dont **404** et **500**), ainsi que timeouts et erreurs de transport, est mappée vers `NetworkError` (cause d’origine conservée quand c’est pertinent).

### 6.5 Interface Layer — `src/ai_context/interfaces/`

CLI Typer. Responsabilité unique : parser les arguments, construire le use case avec les bons adaptateurs, afficher le résultat.

```python
# interfaces/cli.py

import typer
app = typer.Typer()

@app.command()
def main(
    source: str = typer.Argument(..., help="URL ou chemin de fichier"),
    output: Path | None = typer.Option(None, "--output", "-o"),
    format: FormatChoice = typer.Option(FormatChoice.markdown, "--format", "-f"),
    summary: bool = typer.Option(False, "--summary/--no-summary"),
    structure: bool = typer.Option(False, "--structure/--no-structure"),
    max_tokens: int | None = typer.Option(None, "--max-tokens"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None: ...
```

---

## 7. Gestion des Erreurs

Toutes les erreurs sont typées, jamais avalées silencieusement.

| Exception | Déclencheur | Exit Code |
|-----------|------------|-----------|
| `NetworkError` | Échec réseau, timeout, DNS, **statut HTTP non 2xx** (404, 500, … après `raise_for_status`) | 1 |
| `ParseError` | Contenu illisible ou vide | 2 |
| `SourceNotFoundError` | Fichier local absent | 3 |
| `UnsupportedFormatError` | Type de fichier non supporté | 4 |
| `OutputError` | Impossible d'écrire la sortie | 5 |

Les erreurs partent sur `stderr`. `stdout` reste propre pour le piping.

Le handler d'erreurs central vit dans le CLI (couche interface) — il mappe les exceptions domaine vers des messages `rich` + exit codes Typer.

---

## 8. Variables d'Environnement

```env
# Backend LLM pour le résumé assisté par IA (v1.1+)
# AI_CONTEXT_LLM_PROVIDER=openai     # openai | anthropic | ollama
# AI_CONTEXT_LLM_API_KEY=
# AI_CONTEXT_LLM_MODEL=gpt-4o-mini

# Timeout HTTP en ms (défaut : 10000)
# AI_CONTEXT_FETCH_TIMEOUT=10000

# Taille max du contenu en octets avant troncature (défaut : 2MB)
# AI_CONTEXT_MAX_CONTENT_SIZE=2097152
```

Aucun secret hardcodé. `.env.example` committé ; `.env` dans `.gitignore`.

---

## 9. Stratégie de Tests

- **Tests unitaires** (pytest) : chaque processeur et formateur en isolation avec des fixtures HTML/MD statiques.
- **Tests d'intégration** : pipeline complet sur fixtures locales — `pytest-httpx` mocke les appels HTTP, aucun vrai réseau en CI.
- **Tests E2E** (optionnels, désactivés en CI) : fetch URL réelle, activés via `TEST_E2E=true`.
- **Couverture cible** : ≥ 80% sur `domain/` et `infrastructure/processors/`.

---

## 10. Arborescence du Projet

```
ai-context/
│
├── src/
│   └── ai_context/
│       ├── __init__.py
│       │
│       ├── domain/                        # Cœur métier pur
│       │   ├── __init__.py
│       │   ├── models.py                  # Value Objects Pydantic
│       │   ├── ports.py                   # Interfaces abstraites (ABC)
│       │   └── exceptions.py             # Exceptions métier typées
│       │
│       ├── application/                   # Use Cases
│       │   ├── __init__.py
│       │   └── process_source.py          # ProcessSourceUseCase
│       │
│       ├── infrastructure/                # Adaptateurs concrets
│       │   ├── __init__.py
│       │   ├── fetchers/
│       │   │   ├── __init__.py
│       │   │   ├── http_fetcher.py        # ContentFetcher via httpx
│       │   │   └── file_fetcher.py        # ContentFetcher via pathlib
│       │   ├── extractors/
│       │   │   ├── __init__.py
│       │   │   └── readability_extractor.py
│       │   ├── processors/
│       │   │   ├── __init__.py
│       │   │   ├── markdown_converter.py  # HTML → Markdown (markdownify)
│       │   │   ├── extractive_summarizer.py
│       │   │   └── structure_analyzer.py
│       │   └── formatters/
│       │       ├── __init__.py
│       │       ├── markdown_formatter.py
│       │       ├── json_formatter.py      # Via Pydantic .model_dump_json()
│       │       ├── yaml_formatter.py
│       │       └── all_formatter.py
│       │
│       ├── interfaces/                    # Couche la plus mince
│       │   ├── __init__.py
│       │   └── cli.py                    # Typer app + error handler
│       │
│       └── utils/
│           ├── __init__.py
│           ├── logger.py                 # Rich logger (stderr, verbose)
│           └── tokens.py                # Estimation tokens (chars / 4)
│
├── tests/
│   ├── conftest.py                       # Fixtures partagées
│   ├── fixtures/
│   │   ├── sample.html
│   │   ├── sample.md
│   │   └── sample.txt
│   ├── domain/
│   │   └── test_models.py
│   ├── application/
│   │   └── test_process_source.py
│   └── infrastructure/
│       ├── test_http_fetcher.py
│       ├── test_file_fetcher.py
│       ├── test_markdown_converter.py
│       ├── test_extractive_summarizer.py
│       └── test_formatters.py
│
├── pyproject.toml                        # Packaging PEP 517/518 (hatchling)
├── .env.example
├── .gitignore
├── SPEC.md                               # Ce fichier
└── README.md
```

---

## 11. `pyproject.toml` — Structure Prévue

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ai-context"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "typer[all]>=0.12",        # [all] inclut rich
    "pydantic>=2.7",
    "httpx>=0.27",
    "readability-lxml>=0.8",
    "markdownify>=0.12",
    "pyyaml>=6.0",
]

[project.scripts]
ai-context = "ai_context.interfaces.cli:app"

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"
```

---

## 12. Roadmap Versionnée

| Version | Périmètre |
|---------|-----------|
| **v1.0** | URL + fichier, Markdown output, résumé extractif, structure JSON, suite de tests complète |
| **v1.1** | Stratégie LLM pour le résumé (OpenAI / Anthropic / Ollama) |
| **v2.0** | Adaptateur Playwright pour pages JS, support PDF via `pdfplumber` |
| **v2.1** | Mode batch (`--batch urls.txt`), crawl sitemap |

---

*Dernière mise à jour : 2026-04-11*
