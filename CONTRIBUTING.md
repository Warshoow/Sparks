# Guide de Contribution

Merci de votre intérêt pour contribuer au Social Content Archiver ! 🎉

## 📋 Table des matières

- [Code of Conduct](#code-of-conduct)
- [Comment contribuer](#comment-contribuer)
- [Configuration du développement](#configuration-du-développement)
- [Standards de code](#standards-de-code)
- [Workflow Git](#workflow-git)
- [Tests](#tests)
- [Documentation](#documentation)
- [Revue de code](#revue-de-code)

## 🤝 Code of Conduct

- Soyez respectueux et constructif
- Accueillez les nouveaux contributeurs
- Focalisez sur le code, pas sur les personnes
- Rapportez les comportements inappropriés

## 💡 Comment contribuer

### Types de contributions

1. **Bug reports** 🐛
   - Vérifiez que le bug n'a pas déjà été reporté
   - Créez une issue avec le template bug report
   - Incluez: version, OS, steps to reproduce, logs

2. **Feature requests** ✨
   - Décrivez le cas d'usage
   - Expliquez pourquoi c'est utile
   - Proposez une solution si possible

3. **Code contributions** 💻
   - Corrigez des bugs
   - Implémentez de nouvelles features
   - Améliorez la documentation
   - Ajoutez des tests

4. **Documentation** 📚
   - Corrigez des typos
   - Clarifiez des sections confuses
   - Ajoutez des exemples
   - Traduisez

## 🔧 Configuration du développement

### Prérequis

- Python 3.9+
- Git
- OpenAI API key (pour tester)
- Tesseract OCR (pour visual analysis)

### Setup

```bash
# 1. Fork le repo
# Cliquez sur "Fork" sur GitHub

# 2. Clone votre fork
git clone https://github.com/VOTRE_USERNAME/Sparks.git
cd Sparks

# 3. Ajoutez le repo upstream
git remote add upstream https://github.com/ORIGINAL_OWNER/Sparks.git

# 4. Créez un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# 5. Installez les dépendances
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Si disponible

# 6. Installez spaCy model
python -m spacy download en_core_web_sm

# 7. Configurez .env
cp .env.example .env
# Éditez .env avec vos clés API de test

# 8. Installez pre-commit hooks (optionnel mais recommandé)
pip install pre-commit
pre-commit install
```

### Vérification

```bash
# Vérifiez que tout fonctionne
python -m src.main --help

# Lancez les tests (quand implémentés)
pytest tests/
```

## 📏 Standards de code

### Style Python

Nous suivons **PEP 8** avec quelques spécificités :

```python
# Longueur de ligne: 100 caractères
# Indentation: 4 espaces (pas de tabs)
# Quotes: doubles pour strings, simples pour dict keys

# ✅ Bon
def process_content(content: Content) -> ProcessedContent:
    """Process a content item with transcription and analysis."""
    logger.info(f"Processing content: {content.id}")
    return ProcessedContent(...)

# ❌ Mauvais
def process_content(content):
    print("Processing content: " + content.id)
    return ProcessedContent(...)
```

### Type Hints

**Obligatoires** pour toutes les fonctions publiques :

```python
# ✅ Bon
from typing import List, Optional

async def collect_saved_content(
    self,
    limit: Optional[int] = None
) -> List[Content]:
    """Collect saved content from platform."""
    pass

# ❌ Mauvais
async def collect_saved_content(self, limit=None):
    pass
```

### Docstrings

Utilisez le **style Google** :

```python
def synthesize_cluster(
    self,
    cluster: KnowledgeCluster,
    contents: List[Content]
) -> KnowledgeCluster:
    """Synthesize a knowledge cluster into coherent summary.

    Args:
        cluster: The knowledge cluster to synthesize
        contents: List of content items in the cluster

    Returns:
        Updated cluster with synthesis and summary

    Raises:
        OpenAIError: If GPT API call fails
        ValueError: If cluster is empty

    Example:
        >>> cluster = KnowledgeCluster(topic="AI")
        >>> synthesizer.synthesize_cluster(cluster, contents)
    """
    pass
```

### Imports

Organisez dans cet ordre :

```python
# 1. Standard library
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

# 2. Third-party
from loguru import logger
import openai
from sqlalchemy import Column, Integer, String

# 3. Local
from ..models import Content, ProcessedContent
from ..config import settings, config
from .base import BaseCollector
```

### Naming Conventions

```python
# Classes: PascalCase
class InstagramCollector(BaseCollector):
    pass

# Functions/methods: snake_case
def collect_saved_content():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# Privé: prefix _
def _internal_helper():
    pass

# Variables: snake_case
content_id = "instagram_123"
processed_contents = []
```

### Logging

Utilisez **loguru**, pas `print()` :

```python
from loguru import logger

# ✅ Bon
logger.info(f"Collected {count} posts from Instagram")
logger.error(f"Failed to authenticate: {error}")
logger.debug(f"Response: {response}")

# ❌ Mauvais
print(f"Collected {count} posts")
print("ERROR:", error)
```

## 🌿 Workflow Git

### Branches

```bash
# Mettez à jour main
git checkout main
git pull upstream main

# Créez une feature branch
git checkout -b feature/nom-de-la-feature
# ou
git checkout -b fix/nom-du-bug

# Nommage:
# - feature/add-twitter-collector
# - fix/instagram-auth-error
# - docs/improve-readme
# - refactor/simplify-tagger
```

### Commits

**Format**: [Conventional Commits](https://www.conventionalcommits.org/)

```bash
# Structure
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types** :
- `feat`: Nouvelle fonctionnalité
- `fix`: Correction de bug
- `docs`: Documentation uniquement
- `style`: Formatage (pas de changement de code)
- `refactor`: Refactoring (pas de feat ni fix)
- `test`: Ajout/modification de tests
- `chore`: Maintenance (deps, config, etc.)

**Exemples** :

```bash
# ✅ Bon
git commit -m "feat(collectors): add Twitter collector with API v2"
git commit -m "fix(tagger): handle empty content gracefully"
git commit -m "docs: add architecture diagrams to ARCHITECTURE.md"
git commit -m "refactor(processors): extract common transcription logic"

# ❌ Mauvais
git commit -m "fix stuff"
git commit -m "WIP"
git commit -m "updated files"
```

**Commits atomiques** :
- Un commit = une modification logique
- Pas de commits géants
- Pas de "WIP" dans l'historique final (squash avant merge)

### Pull Requests

```bash
# 1. Poussez votre branch
git push origin feature/nom-de-la-feature

# 2. Créez une PR sur GitHub
# - Utilisez le template PR
# - Décrivez ce qui change et pourquoi
# - Référencez les issues liées (#123)
# - Ajoutez des captures d'écran si UI
```

**Template PR** :

```markdown
## Description
Brief description of the changes

## Type of change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No new warnings

## Related Issues
Fixes #123

## Screenshots (if applicable)

## Additional context
```

### Revue de code

Avant de merger, la PR doit :
- ✅ Passer tous les checks CI/CD (quand implémenté)
- ✅ Avoir au moins 1 approbation
- ✅ Répondre à tous les commentaires
- ✅ Être à jour avec main

**Pour les reviewers** :
- Soyez constructif et pédagogique
- Proposez des solutions, pas juste des critiques
- Approuvez si le code est "assez bon", pas "parfait"

## 🧪 Tests

### Structure

```
tests/
├── unit/                    # Tests unitaires
│   ├── test_collectors/
│   │   ├── test_instagram.py
│   │   └── test_facebook.py
│   ├── test_processors/
│   └── test_tagging/
├── integration/             # Tests d'intégration
│   ├── test_full_pipeline.py
│   └── test_database.py
├── fixtures/                # Données de test
│   └── sample_contents.json
└── conftest.py             # Fixtures pytest
```

### Écrire des tests

```python
import pytest
from unittest.mock import Mock, patch

# Unit test
def test_instagram_collector_authenticate():
    """Test Instagram collector authentication."""
    collector = InstagramCollector()

    with patch('instaloader.Instaloader') as mock_loader:
        mock_loader.return_value.login.return_value = True
        result = await collector.authenticate()

    assert result is True
    mock_loader.return_value.login.assert_called_once()

# Integration test
@pytest.mark.integration
async def test_full_pipeline_with_sample_data():
    """Test complete pipeline with sample data."""
    archiver = SocialContentArchiver()

    # Load fixtures
    with open('tests/fixtures/sample_contents.json') as f:
        sample_contents = json.load(f)

    # Process
    await archiver.process_content(sample_contents)

    # Verify
    results = archiver.db.get_all_processed_contents()
    assert len(results) == len(sample_contents)
```

### Lancer les tests

```bash
# Tous les tests
pytest

# Tests unitaires uniquement
pytest tests/unit/

# Avec coverage
pytest --cov=src --cov-report=html

# Un fichier spécifique
pytest tests/unit/test_collectors/test_instagram.py

# Verbose
pytest -v

# Arrêter au premier échec
pytest -x
```

### Fixtures

```python
# conftest.py
import pytest

@pytest.fixture
def sample_content():
    """Create a sample content for testing."""
    return Content(
        id="test_123",
        platform=Platform.INSTAGRAM,
        content_type=ContentType.POST,
        text="Sample post",
        created_at=datetime.now(),
        collected_at=datetime.now()
    )

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    with patch('openai.OpenAI') as mock:
        yield mock
```

## 📚 Documentation

### Où documenter

1. **Code** : Docstrings pour classes/fonctions publiques
2. **README.md** : Vue d'ensemble, installation, usage
3. **CLAUDE.md** : Contexte pour Claude Code
4. **ARCHITECTURE.md** : Architecture technique détaillée
5. **CONTRIBUTING.md** : Ce fichier
6. **docs/** : Documentation API, guides, tutoriels

### Standards

```python
# Classes
class ContentAnalyzer:
    """Analyzes text content for entities, sentiment, and key information.

    The ContentAnalyzer uses NLP techniques (spaCy) and GPT-4 to extract
    meaningful information from content text, transcriptions, and visual
    descriptions.

    Attributes:
        client: OpenAI client instance
        extract_entities: Whether to extract named entities
        sentiment_analysis: Whether to analyze sentiment

    Example:
        >>> analyzer = ContentAnalyzer()
        >>> result = await analyzer.analyze_content(content)
        >>> print(result.sentiment)
        0.75
    """

# Méthodes complexes
async def synthesize_cluster(self, cluster, contents):
    """Synthesize a knowledge cluster into coherent summary.

    This method combines multiple related content pieces into a single
    coherent synthesis using GPT-4. It identifies common themes, combines
    complementary information, and resolves contradictions.

    Args:
        cluster: KnowledgeCluster to synthesize
        contents: List of Content objects in the cluster

    Returns:
        Updated KnowledgeCluster with synthesis and summary

    Raises:
        OpenAIError: If GPT API call fails
        ValueError: If cluster contains no content

    Note:
        This operation can be expensive due to GPT-4 usage.
        Consider using gpt-4o-mini for cost optimization.
    """
```

### README updates

Quand vous ajoutez une feature, mettez à jour :
- Liste des features
- Exemple d'utilisation
- Configuration requise
- Dépendances

## ✅ Checklist avant PR

Avant de créer une PR, vérifiez :

- [ ] Code suit les standards (PEP 8, type hints, docstrings)
- [ ] Tests ajoutés/mis à jour et passent
- [ ] Documentation mise à jour (README, CLAUDE.md, etc.)
- [ ] Pas de secrets commités (.env, API keys)
- [ ] Commits sont propres et suivent Conventional Commits
- [ ] Branch est à jour avec main
- [ ] Pas de code commenté ou debug prints
- [ ] Logging approprié (pas de print())
- [ ] Error handling géré correctement

## 🐛 Rapporter un bug

Utilisez le template :

```markdown
## Description
Clear description of the bug

## To Reproduce
1. Run command '...'
2. Click on '...'
3. See error

## Expected behavior
What you expected to happen

## Actual behavior
What actually happened

## Environment
- OS: [e.g. macOS 12.0]
- Python version: [e.g. 3.9.7]
- App version: [e.g. 0.1.0]

## Logs
```
Paste relevant logs here
```

## Screenshots
If applicable
```

## 💬 Questions ?

- **Issues GitHub** : Pour bugs et features
- **Discussions** : Pour questions générales
- **Email** : Pour questions privées

## 🙏 Remerciements

Merci de contribuer au Social Content Archiver ! Chaque contribution, petite ou grande, est appréciée.

---

**Dernière mise à jour** : 2026-01-11
