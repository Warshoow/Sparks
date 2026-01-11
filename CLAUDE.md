# CLAUDE.md - Guide de développement pour Claude Code

Ce document fournit le contexte nécessaire pour développer efficacement sur ce projet avec Claude Code.

## 📋 Vue d'ensemble du projet

**Nom**: Social Content Archiver
**Objectif**: Archiver, analyser et synthétiser des contenus sauvegardés depuis les réseaux sociaux pour créer une base de connaissance structurée.

**Problème résolu**: Les utilisateurs sauvegardent des posts sur Instagram, Facebook, LinkedIn et Beeper qui contiennent des fragments d'idées et de valeur, mais ne les exploitent jamais. Cette app transforme ces fragments en connaissances cohérentes.

## 🏗️ Architecture du projet

```
src/
├── collectors/          # Collecte depuis plateformes sociales
│   ├── base.py         # Classe abstraite BaseCollector
│   ├── instagram.py    # Instaloader
│   ├── facebook.py     # Graph API
│   ├── linkedin.py     # API non-officielle (à implémenter)
│   └── beeper.py       # Matrix API (à implémenter)
│
├── processors/         # Traitement du contenu
│   ├── transcription.py      # Whisper pour audio/vidéo
│   ├── visual_analysis.py    # GPT-4V + Tesseract OCR
│   └── content_analyzer.py   # NLP (spaCy + GPT)
│
├── tagging/           # Système de tagging automatique
│   └── tagger.py      # GPT-4 + embeddings
│
├── knowledge_base/    # Agrégation et synthèse
│   ├── aggregator.py  # Clustering par tags
│   └── synthesizer.py # Génération de synthèses
│
├── storage/           # Persistence
│   └── database.py    # SQLAlchemy + SQLite
│
├── models.py          # Modèles Pydantic
├── config.py          # Configuration (charge .env + config.yaml)
└── main.py            # CLI Click + orchestration
```

## 🔑 Concepts clés

### Pipeline de données

```
1. COLLECT    → Récupère posts sauvegardés (Instagram, Facebook, etc.)
2. PROCESS    → Transcription + Analyse visuelle + NLP
3. TAG        → Auto-tagging avec GPT-4
4. AGGREGATE  → Regroupe contenus par tags similaires
5. SYNTHESIZE → Crée synthèses cohérentes à partir de clusters
```

### Modèles principaux

- **Content**: Contenu brut collecté (texte, médias, métadonnées)
- **ProcessedContent**: Résultat du traitement (transcription, entités, sentiment)
- **TaggedContent**: Contenu avec tags et topic principal
- **KnowledgeCluster**: Groupe de contenus liés + synthèse

## 🛠️ Stack technique

- **Python 3.9+**
- **OpenAI API**: GPT-4 (analyse), Whisper (transcription), GPT-4V (vision)
- **spaCy**: NLP pour extraction d'entités
- **Sentence Transformers**: Embeddings pour similarité sémantique
- **SQLAlchemy**: ORM
- **Pydantic**: Validation de données
- **Click**: CLI
- **Rich**: Interface terminal
- **Instaloader**: Instagram
- **Tesseract**: OCR

## 📝 Conventions de code

### Style
- **PEP 8** pour le style Python
- **Type hints** obligatoires pour les fonctions publiques
- **Docstrings** Google-style pour classes et méthodes publiques
- **Logging** avec `loguru` (pas de print sauf dans CLI)

### Nommage
- **Classes**: PascalCase (`InstagramCollector`)
- **Fonctions/méthodes**: snake_case (`collect_saved_content`)
- **Constantes**: UPPER_SNAKE_CASE (`MAX_RETRIES`)
- **Privé**: préfixe underscore (`_internal_method`)

### Imports
```python
# Standard library
import asyncio
from typing import List, Optional

# Third-party
from loguru import logger
import openai

# Local
from ..models import Content
from ..config import settings
```

## 🔧 Patterns utilisés

### 1. Collectors (Strategy Pattern)
Tous les collectors héritent de `BaseCollector` et implémentent:
- `authenticate() -> bool`
- `collect_saved_content(limit) -> List[Content]`
- `download_media(content, path) -> List[str]`

### 2. Async/Await
- Toutes les opérations I/O sont async
- Usage de `asyncio.run()` dans le CLI

### 3. Configuration
- Variables d'environnement via `.env` (credentials)
- Configuration structurée via `config.yaml` (paramètres)
- Chargement centralisé dans `src/config.py`

### 4. Dependency Injection
- Classes reçoivent leurs dépendances via le constructeur
- Exemple: `ContentAnalyzer` reçoit `openai.OpenAI` client

## 🧪 Testing (à implémenter)

Structure à créer:
```
tests/
├── unit/
│   ├── test_collectors/
│   ├── test_processors/
│   └── test_tagging/
├── integration/
└── fixtures/
```

Utiliser **pytest** avec fixtures pour mock les API calls.

## 📦 Dépendances importantes

```python
# API externes
openai>=1.0.0           # GPT-4, Whisper, Vision
instaloader>=4.10       # Instagram

# NLP & ML
spacy>=3.7              # Entités, NLP
sentence-transformers   # Embeddings
pytesseract>=0.3.10    # OCR

# Database & Storage
sqlalchemy>=2.0         # ORM
pydantic>=2.0          # Validation

# CLI & UI
click>=8.0             # CLI framework
rich>=13.0             # Terminal UI
loguru>=0.7            # Logging
```

## 🚀 Commandes de développement

```bash
# Installation
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Lancer l'app
python -m src.main run              # Pipeline complet
python -m src.main collect          # Collecter uniquement
python -m src.main show             # Afficher KB

# Tests (quand implémentés)
pytest tests/
pytest tests/unit/test_collectors/

# Linting
black src/                          # Format code
flake8 src/                         # Linting
mypy src/                           # Type checking
```

## 🔐 Configuration requise

### `.env` minimal
```env
OPENAI_API_KEY=sk-...
INSTAGRAM_USERNAME=...
INSTAGRAM_PASSWORD=...
```

### `config.yaml`
Configurable: platforms, processeurs, seuils de qualité, etc.

## 📂 Fichiers importants

| Fichier | Description |
|---------|-------------|
| `src/main.py` | Point d'entrée, orchestration, CLI |
| `src/models.py` | Tous les modèles de données |
| `src/config.py` | Chargement configuration |
| `src/collectors/base.py` | Interface collector |
| `src/storage/database.py` | Gestion DB |
| `config/config.yaml` | Configuration métier |

## 🐛 Debugging

### Logs
- Logs dans `logs/` (auto-créé)
- Niveau configurable dans code
- Format: `logger.info()`, `logger.error()`, etc.

### Database
```bash
# Explorer la DB SQLite
sqlite3 data/archive.db
.tables
SELECT * FROM contents LIMIT 5;
```

### API Calls
- Ajouter `logger.debug()` pour voir les requêtes/réponses
- Vérifier les coûts OpenAI (GPT-4 est cher!)

## ⚠️ Limitations connues

1. **LinkedIn & Beeper**: APIs non officielles, implémentation partielle
2. **Rate limits**: Instagram peut bloquer si trop de requêtes
3. **Coûts**: GPT-4 Vision et Whisper coûtent cher en volume
4. **Qualité OCR**: Tesseract peut mal lire certaines images

## 🎯 TODOs / Améliorations futures

- [ ] **Tests**: Ajouter pytest avec coverage
- [ ] **LinkedIn collector**: Implémenter avec API réelle
- [ ] **Beeper collector**: Intégration Matrix protocol
- [ ] **Web UI**: Dashboard avec FastAPI + React
- [ ] **Export**: Notion, Obsidian, Markdown
- [ ] **Graphe**: Visualisation des relations entre contenus
- [ ] **Search**: Recherche sémantique dans la KB
- [ ] **Monitoring**: Métriques de coûts API
- [ ] **Docker**: Containerisation
- [ ] **CI/CD**: GitHub Actions

## 💡 Comment ajouter une nouvelle plateforme

1. **Créer collector**: `src/collectors/nouvelle_plateforme.py`
   ```python
   class NouvellePlateformeCollector(BaseCollector):
       def __init__(self):
           super().__init__(Platform.NOUVELLE_PLATEFORME)

       async def authenticate(self) -> bool:
           # Implémenter
           pass

       async def collect_saved_content(self, limit) -> List[Content]:
           # Implémenter
           pass
   ```

2. **Ajouter enum**: Dans `models.py`, ajouter à `Platform`
   ```python
   class Platform(str, Enum):
       # ...
       NOUVELLE_PLATEFORME = "nouvelle_plateforme"
   ```

3. **Configurer**: Ajouter section dans `config.yaml`
   ```yaml
   collectors:
     enabled_platforms:
       - nouvelle_plateforme

     nouvelle_plateforme:
       max_posts_per_sync: 100
   ```

4. **Initialiser**: Dans `main.py`, ajouter dans `_init_collectors()`
   ```python
   if "nouvelle_plateforme" in enabled:
       collectors["nouvelle_plateforme"] = NouvellePlateformeCollector()
   ```

## 🔄 Workflow Git recommandé

```bash
# Créer une branche feature
git checkout -b feature/nouvelle-fonctionnalite

# Développer, tester

# Commit avec message descriptif
git commit -m "feat: Ajoute support pour TikTok saved videos"

# Push
git push -u origin feature/nouvelle-fonctionnalite

# Créer PR vers main
```

## 📚 Ressources

- [OpenAI API Docs](https://platform.openai.com/docs)
- [Instaloader Docs](https://instaloader.github.io/)
- [spaCy Docs](https://spacy.io/usage)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)

## 🤝 Aide pour Claude

### Quand modifier ce projet

1. **Ajout de plateforme**: Suivre pattern des collectors existants
2. **Amélioration traitement**: Modifier/ajouter dans `processors/`
3. **Changement DB**: Modifier `models.py` + migrations
4. **Nouveaux tags**: Ajuster prompts dans `tagger.py`
5. **Interface**: Ajouter commandes dans `main.py`

### Points d'attention

- ⚠️ **Coûts API**: GPT-4 Vision très cher, utiliser avec parcimonie
- ⚠️ **Rate limits**: Implémenter retry avec backoff
- ⚠️ **Credentials**: JAMAIS commit `.env`
- ⚠️ **Type safety**: Toujours utiliser type hints
- ⚠️ **Error handling**: Try/except autour API calls

### Questions fréquentes

**Q: Comment tester sans vraies API?**
A: Créer mocks dans `tests/fixtures/` avec données fake

**Q: L'app crash avec des gros volumes?**
A: Implémenter pagination + batching dans collectors

**Q: Comment réduire coûts OpenAI?**
A: Utiliser gpt-4o-mini au lieu de gpt-4, cacher résultats

**Q: Database trop grosse?**
A: Implémenter cleanup job pour vieux contenus

---

**Dernière mise à jour**: 2026-01-11
**Version**: 0.1.0
