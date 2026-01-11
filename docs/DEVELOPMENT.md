# Guide de Développement

Documentation technique pour les développeurs travaillant sur Social Content Archiver.

## 🚀 Quick Start

```bash
# Setup complet en une fois
git clone <repo-url> && cd Sparks
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env
# Éditez .env avec vos clés
python -m src.main --help
```

## 🛠️ Outils de développement

### Python Tools

```bash
# Formatage
black src/ tests/                    # Auto-format code
isort src/ tests/                    # Sort imports

# Linting
flake8 src/ tests/                   # Check style
pylint src/                          # Deep linting
mypy src/                            # Type checking

# Tests
pytest                               # Run all tests
pytest -v                            # Verbose
pytest --cov=src                     # With coverage
pytest -k "test_instagram"           # Specific test

# Pre-commit (recommandé)
pip install pre-commit
pre-commit install                   # Setup hooks
pre-commit run --all-files          # Run manually
```

### requirements-dev.txt

Créez ce fichier pour les dépendances de dev :

```txt
# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0

# Linting & Formatting
black>=23.7.0
flake8>=6.1.0
isort>=5.12.0
mypy>=1.5.0
pylint>=2.17.0

# Pre-commit
pre-commit>=3.3.0

# Debugging
ipdb>=0.13.0
ipython>=8.14.0

# Documentation
sphinx>=7.1.0
sphinx-rtd-theme>=1.3.0
```

## 🧩 Structure des modules

### Ajouter un nouveau collector

```python
# src/collectors/twitter.py

from typing import List, Optional
from loguru import logger
from .base import BaseCollector
from ..models import Content, Platform

class TwitterCollector(BaseCollector):
    """Collector for Twitter/X saved tweets."""

    def __init__(self):
        super().__init__(Platform.TWITTER)
        self.api_key = settings.twitter_api_key
        self.api_secret = settings.twitter_api_secret

    async def authenticate(self) -> bool:
        """Authenticate with Twitter API v2."""
        try:
            # Your auth logic
            logger.info("Successfully authenticated with Twitter")
            return True
        except Exception as e:
            logger.error(f"Twitter authentication failed: {e}")
            return False

    async def collect_saved_content(
        self,
        limit: Optional[int] = None
    ) -> List[Content]:
        """Collect saved/bookmarked tweets."""
        contents = []
        try:
            # Your collection logic
            # Use Twitter API v2 to get bookmarks
            # Convert to Content objects
            pass
        except Exception as e:
            logger.error(f"Error collecting Twitter content: {e}")

        return contents

    async def download_media(
        self,
        content: Content,
        output_path: str
    ) -> List[str]:
        """Download media from tweets."""
        # Your media download logic
        return []
```

### Étapes d'intégration

1. **Créer le collector** : `src/collectors/twitter.py`
2. **Ajouter à l'enum** :
   ```python
   # src/models.py
   class Platform(str, Enum):
       INSTAGRAM = "instagram"
       FACEBOOK = "facebook"
       LINKEDIN = "linkedin"
       BEEPER = "beeper"
       TWITTER = "twitter"  # ← Nouveau
   ```

3. **Configurer** :
   ```yaml
   # config/config.yaml
   collectors:
     enabled_platforms:
       - twitter  # ← Ajouter

     twitter:
       max_posts_per_sync: 100
       include_retweets: false
   ```

4. **Initialiser** :
   ```python
   # src/main.py
   def _init_collectors(self):
       # ...
       if "twitter" in enabled:
           collectors["twitter"] = TwitterCollector()
   ```

5. **Ajouter credentials** :
   ```bash
   # .env
   TWITTER_API_KEY=...
   TWITTER_API_SECRET=...
   ```

6. **Tester** :
   ```python
   # tests/unit/test_collectors/test_twitter.py
   @pytest.mark.asyncio
   async def test_twitter_collector_authenticate():
       collector = TwitterCollector()
       with patch('tweepy.Client') as mock_client:
           result = await collector.authenticate()
       assert result is True
   ```

## 🔍 Debugging Tips

### Logging

```python
# Activer debug logging
from loguru import logger

logger.remove()  # Remove default handler
logger.add(
    "logs/debug.log",
    level="DEBUG",
    rotation="100 MB"
)

# Usage
logger.debug("Detailed debug info")
logger.info("General info")
logger.warning("Warning message")
logger.error("Error occurred")
```

### IPython debugging

```python
# Insérer un breakpoint
import ipdb; ipdb.set_trace()

# Ou avec Python 3.7+
breakpoint()
```

### Tester un module individuellement

```python
# Test script temporaire
# test_instagram.py

import asyncio
from src.collectors.instagram import InstagramCollector
from src.config import settings

async def main():
    collector = InstagramCollector()

    if await collector.authenticate():
        contents = await collector.collect_saved_content(limit=5)
        print(f"Collected {len(contents)} posts")

        for content in contents:
            print(f"- {content.id}: {content.text[:50]}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Inspecter la database

```bash
# SQLite CLI
sqlite3 data/archive.db

# Commandes utiles
.tables                              # List all tables
.schema contents                     # Show table schema
SELECT COUNT(*) FROM contents;       # Count rows
SELECT * FROM contents LIMIT 5;      # View first 5 rows
.mode column                         # Pretty print
.headers on                          # Show column names

# Ou avec Python
python -c "
from src.storage.database import DatabaseManager
db = DatabaseManager()
contents = db.get_all_contents()
print(f'Total contents: {len(contents)}')
for c in contents[:5]:
    print(f'{c.platform}: {c.text[:50]}')
"
```

## 📊 Profiling & Performance

### Mesurer le temps d'exécution

```python
import time
from functools import wraps

def timer(func):
    """Decorator to measure execution time."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper

# Usage
@timer
async def process_content(content):
    # Your code
    pass
```

### Memory profiling

```bash
pip install memory-profiler

# Décorer la fonction
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Your code
    pass

# Exécuter
python -m memory_profiler script.py
```

### API cost tracking

```python
# Track OpenAI costs
class CostTracker:
    def __init__(self):
        self.gpt4_calls = 0
        self.whisper_minutes = 0.0

    def track_gpt4(self, tokens: int):
        """Track GPT-4 usage."""
        self.gpt4_calls += 1
        cost = tokens * 0.00003  # Approximate
        logger.info(f"GPT-4 cost: ${cost:.4f}")

    def track_whisper(self, duration_seconds: float):
        """Track Whisper usage."""
        minutes = duration_seconds / 60
        self.whisper_minutes += minutes
        cost = minutes * 0.006  # $0.006 per minute
        logger.info(f"Whisper cost: ${cost:.4f}")

    def get_total_cost(self) -> float:
        """Get estimated total cost."""
        return (self.gpt4_calls * 0.01) + (self.whisper_minutes * 0.006)
```

## 🧪 Testing Patterns

### Mocking OpenAI API

```python
@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    with patch('openai.OpenAI') as mock:
        # Mock chat completion
        mock.return_value.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Mocked response"))]
        )

        # Mock transcription
        mock.return_value.audio.transcriptions.create.return_value = Mock(
            text="Mocked transcription"
        )

        yield mock

async def test_content_analyzer(mock_openai):
    analyzer = ContentAnalyzer()
    result = await analyzer.analyze_text_with_gpt("test")
    assert "entities" in result
```

### Fixtures pour contenus

```python
# conftest.py
@pytest.fixture
def instagram_post():
    """Sample Instagram post."""
    return Content(
        id="instagram_123456",
        platform=Platform.INSTAGRAM,
        content_type=ContentType.POST,
        url="https://instagram.com/p/ABC123/",
        text="Amazing sunset! #nature #photography",
        author="user123",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        collected_at=datetime.now(),
        media_urls=["https://example.com/image.jpg"],
        metadata={"likes": 150, "comments": 12}
    )

@pytest.fixture
def processed_content():
    """Sample processed content."""
    return ProcessedContent(
        content_id="instagram_123456",
        transcription=None,
        visual_description="A beautiful sunset over the ocean",
        extracted_text="",
        detected_objects=["sky", "ocean", "sun"],
        entities=["nature", "photography"],
        sentiment=0.8,
        key_phrases=["amazing sunset", "beautiful view"]
    )
```

### Tests d'intégration

```python
@pytest.mark.integration
class TestFullPipeline:
    """Integration tests for full pipeline."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test database."""
        self.db = DatabaseManager(db_url="sqlite:///test.db")
        yield
        # Cleanup
        os.remove("test.db")

    async def test_collect_process_tag_pipeline(self):
        """Test complete pipeline."""
        archiver = SocialContentArchiver()

        # Collect (mocked)
        with patch.object(
            InstagramCollector,
            'collect_saved_content'
        ) as mock_collect:
            mock_collect.return_value = [self.instagram_post()]
            contents = await archiver.collect_all_content()

        assert len(contents) == 1

        # Process
        await archiver.process_content(contents)
        processed = self.db.get_processed_content(contents[0].id)
        assert processed is not None

        # Tag
        await archiver.tag_all_content()
        tagged = self.db.get_tagged_content(contents[0].id)
        assert len(tagged.tags) > 0
```

## 🔐 Secrets Management

### Ne JAMAIS commiter

```bash
# .gitignore contient déjà:
.env
.env.*
*.key
credentials.json

# Vérifier avant commit
git status
git diff --cached
```

### Utiliser python-dotenv

```python
# src/config.py
from dotenv import load_dotenv
import os

load_dotenv()  # Charge .env

class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    instagram_username: str = os.getenv("INSTAGRAM_USERNAME")

    def __post_init__(self):
        # Valider que les secrets existent
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set")
```

### Pour production

```bash
# Ne pas utiliser .env en production
# Utiliser variables d'environnement système

export OPENAI_API_KEY="sk-..."
export INSTAGRAM_USERNAME="..."

# Ou secrets manager (AWS, GCP, Azure)
```

## 📦 Packaging & Distribution

### Setup.py

```python
from setuptools import setup, find_packages

setup(
    name="social-content-archiver",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        line.strip()
        for line in open('requirements.txt')
        if line.strip() and not line.startswith('#')
    ],
    entry_points={
        'console_scripts': [
            'archiver=src.main:cli',
        ],
    },
    python_requires='>=3.9',
)
```

### Installation en mode dev

```bash
pip install -e .

# Maintenant vous pouvez utiliser
archiver run
archiver collect
archiver show
```

## 🐳 Docker (futur)

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

# Copy application
COPY . .

# Run
CMD ["python", "-m", "src.main", "run"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  archiver:
    build: .
    volumes:
      - ./data:/app/data
      - ./media:/app/media
      - ./logs:/app/logs
    env_file:
      - .env
    command: python -m src.main run
```

## 🚀 CI/CD (futur)

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
        python -m spacy download en_core_web_sm

    - name: Lint
      run: |
        black --check src/
        flake8 src/

    - name: Test
      run: pytest --cov=src

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## 📚 Documentation

### Générer docs avec Sphinx

```bash
pip install sphinx sphinx-rtd-theme

# Initialize
cd docs/
sphinx-quickstart

# Build
make html

# View
open _build/html/index.html
```

## 🎯 Bonnes pratiques

### Error handling

```python
# ✅ Bon: Spécifique et informatif
try:
    result = await api_call()
except OpenAIError as e:
    logger.error(f"OpenAI API error: {e}")
    raise
except NetworkError as e:
    logger.warning(f"Network error, retrying: {e}")
    await asyncio.sleep(2)
    result = await api_call()

# ❌ Mauvais: Trop générique
try:
    result = await api_call()
except Exception as e:
    print("Error:", e)
    pass
```

### Configuration

```python
# ✅ Bon: Centralisé et typé
from dataclasses import dataclass

@dataclass
class ProcessorConfig:
    transcription_enabled: bool
    visual_analysis_enabled: bool
    max_video_duration: int = 600

config = ProcessorConfig(
    transcription_enabled=True,
    visual_analysis_enabled=True
)

# ❌ Mauvais: Magic values éparpillées
if some_flag:  # Quelle flag?
    process_video()  # Avec quels params?
```

### Async/Await

```python
# ✅ Bon: Paralléliser quand possible
async def process_multiple(contents):
    tasks = [process_one(c) for c in contents]
    return await asyncio.gather(*tasks)

# ❌ Mauvais: Séquentiel inutile
async def process_multiple(contents):
    results = []
    for c in contents:
        result = await process_one(c)  # Bloque à chaque itération
        results.append(result)
    return results
```

---

**Dernière mise à jour** : 2026-01-11
**Version** : 0.1.0
