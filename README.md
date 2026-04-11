# ai-context

CLI Python qui transforme une URL (ou, plus tard, un fichier) en Markdown propre, résumé et structure lisible par des modèles. Voir [SPEC.md](SPEC.md) pour l’architecture cible (DDD léger).

**État actuel (fondation / stub)** : le pipeline `fetch → extract` est branché avec des adaptateurs factices ; seules les **URLs HTTP(S)** sont acceptées. Aucun appel réseau réel pour l’instant.

## Prérequis

- **Python 3.11+**
- Git

## Installation (parcours standard)

À la racine du dépôt :

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e ".[dev]"
```

La commande **`ai-context`** est alors disponible dans l’environnement activé.

Vérifier :

```bash
ai-context --help
```

## Utilisation rapide

```bash
ai-context "https://example.com/article"
ai-context "https://example.com/article" --summary
ai-context "https://example.com/article" --summary -v
```

## Tests automatisés

```bash
pytest
```

## Tutoriel — vérification manuelle (même installation que ci-dessus)

Objectif : valider la CLI après `pip install -e ".[dev]"`, sans autre contournement.

### 1. Préparer le terminal

Active le venv (voir plus haut), place-toi à la racine du repo.

### 2. Aide

```bash
ai-context --help
```

Tu dois voir l’argument **SOURCE**, **--summary / --no-summary**, **--verbose / -v**.

### 3. Fichier local → erreur, code **4**

```bash
ai-context ./README.md
```

**Attendu** : message d’erreur sur **stderr** (style Rich, « Error: »), mention du fait que seules les URLs HTTP(S) sont prises en charge ; **code de sortie 4**.

Sous PowerShell, après la commande : `echo $LASTEXITCODE` doit afficher **4**. Sous bash : `echo $?` (juste après, souvent **4**).

### 4. URL invalide → code **2**

```bash
ai-context "https://"
```

**Attendu** : erreur explicite (URL invalide) ; **code 2**.

### 5. URL valide → succès sur stdout

```bash
ai-context "https://example.com/article"
```

**Attendu** : **code 0** ; sur **stdout** du Markdown stub (`# Stub document`, « First stub sentence », etc.) ; **pas** de section `## Summary (stub)` sans `--summary`.

### 6. Résumé stub (trois premières phrases)

```bash
ai-context "https://example.com/article" --summary
```

**Attendu** : **code 0** ; après le corps, bloc **`## Summary (stub)`** ; la phrase « Fourth stub sentence » **n’apparaît pas** dans ce bloc résumé (elle peut rester dans le corps au-dessus).

Les deux ordres suivants doivent fonctionner :

```bash
ai-context "https://example.com/article" --summary
ai-context --summary "https://example.com/article"
```

### 7. Verbose

```bash
ai-context "https://example.com/article" --summary -v
```

**Attendu** : **code 0** ; logs sur **stderr** ; **stdout** inchangé en nature (markdown + résumé), sans mélanger les logs dans le contenu pipé.

### 8. Grille rapide

| Cas                         | Code |
|----------------------------|------|
| Chemin fichier local       | 4    |
| `https://` invalide        | 2    |
| URL OK                     | 0    |
| URL + `--summary` + `-v`   | 0    |

## Licence

MIT (voir `pyproject.toml`).
