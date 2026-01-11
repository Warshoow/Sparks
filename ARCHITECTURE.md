# Architecture Technique - Social Content Archiver

Ce document décrit l'architecture technique détaillée du projet.

## 📐 Vue d'ensemble

Le Social Content Archiver suit une architecture en **pipeline modulaire** avec séparation claire des responsabilités.

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Interface (Click)                    │
│                        src/main.py                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Orchestrator (SocialContentArchiver)            │
│  - Coordonne le pipeline                                     │
│  - Gère le flux de données entre modules                     │
└─────┬────────┬───────────┬──────────┬──────────┬───────────┘
      │        │           │          │          │
      ▼        ▼           ▼          ▼          ▼
┌──────────┐ ┌─────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
│Collectors│ │Processor│ │Content │ │Tagger  │ │Knowledge │
│          │ │         │ │Analyzer│ │        │ │Base      │
└────┬─────┘ └────┬────┘ └────┬───┘ └───┬────┘ └─────┬────┘
     │            │           │         │            │
     └────────────┴───────────┴─────────┴────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │ Storage (DB)   │
                  │  SQLite        │
                  └────────────────┘
```

## 🏛️ Modules principaux

### 1. Collectors (`src/collectors/`)

**Responsabilité**: Récupérer les contenus sauvegardés depuis les plateformes sociales.

#### Architecture

```python
BaseCollector (ABC)
├── authenticate() -> bool
├── collect_saved_content(limit) -> List[Content]
└── download_media(content, path) -> List[str]

Implémentations:
├── InstagramCollector   # Instaloader
├── FacebookCollector    # Graph API
├── LinkedInCollector    # API non-officielle
└── BeeperCollector      # Matrix protocol
```

#### Flow de collecte

```
1. authenticate()
   └─> Vérifie credentials
   └─> Établit session

2. collect_saved_content(limit)
   └─> Récupère liste des posts sauvegardés
   └─> Pour chaque post:
       ├─> Extrait métadonnées
       ├─> Télécharge médias (images/vidéos)
       └─> Crée objet Content

3. download_media(content, path)
   └─> Télécharge fichiers médias
   └─> Sauvegarde dans media_path
   └─> Retourne chemins des fichiers
```

#### Gestion des erreurs

- Retry avec backoff exponentiel (3 tentatives)
- Logging détaillé de chaque erreur
- Continue malgré les échecs individuels

### 2. Processors (`src/processors/`)

**Responsabilité**: Traiter le contenu brut (transcription, vision, NLP).

#### 2.1 TranscriptionProcessor

```python
class TranscriptionProcessor:
    async def transcribe_audio(file_path: str) -> str
    async def transcribe_video(file_path: str) -> str
    async def extract_audio_from_video(video_path: str) -> str
```

**Technologie**: OpenAI Whisper API

**Flow**:
```
Vidéo → extract_audio → Audio → Whisper → Transcription
```

#### 2.2 VisualAnalysisProcessor

```python
class VisualAnalysisProcessor:
    async def analyze_image(image_path: str) -> VisualAnalysis
    async def extract_text_from_image(image_path: str) -> str  # OCR
    async def describe_image_content(image_path: str) -> str   # GPT-4V
    async def detect_objects(image_path: str) -> List[str]     # GPT-4V
```

**Technologies**:
- GPT-4 Vision pour compréhension contextuelle
- Tesseract OCR pour extraction de texte

**Flow**:
```
Image → GPT-4V → Description contextuelle
      → Tesseract → Texte extrait (OCR)
      → GPT-4V → Objets détectés

VisualAnalysis {
    description: str
    extracted_text: str
    detected_objects: List[str]
}
```

#### 2.3 ContentAnalyzer

```python
class ContentAnalyzer:
    async def analyze_text_with_gpt(text: str) -> Dict
    async def extract_entities_from_text(text: str) -> List[str]
    async def analyze_sentiment(text: str) -> float
    async def extract_key_phrases(text: str) -> List[str]
    async def analyze_content(content, transcription, visual) -> ProcessedContent
```

**Technologies**:
- spaCy pour NER (Named Entity Recognition)
- GPT-4 pour analyse sémantique avancée
- Fallback: si spaCy indisponible → GPT uniquement

**Flow**:
```
Content + Transcription + Visual Description
    ↓
Combine all text sources
    ↓
┌─────────────────┬──────────────────┬──────────────────┐
│ Entity Extract  │  Sentiment       │  Key Phrases     │
│ (spaCy/GPT)     │  (GPT)          │  (GPT)           │
└────────┬────────┴─────────┬────────┴──────────┬───────┘
         └──────────────────┴───────────────────┘
                            ↓
                    ProcessedContent {
                        entities: List[str]
                        sentiment: float
                        key_phrases: List[str]
                    }
```

### 3. Tagging System (`src/tagging/`)

**Responsabilité**: Générer des tags automatiques pour catégoriser le contenu.

#### Architecture

```python
class ContentTagger:
    # Tagging
    async def generate_tags_with_gpt(...) -> List[Tag]
    async def extract_tags_from_entities(...) -> List[Tag]
    async def extract_tags_from_key_phrases(...) -> List[Tag]
    async def tag_content(...) -> TaggedContent

    # Similarité
    def calculate_similarity(tags1, tags2) -> float
    def calculate_semantic_similarity(text1, text2) -> float
```

**Technologie**:
- GPT-4 pour génération de tags contextuels
- Sentence Transformers pour embeddings sémantiques

#### Flow de tagging

```
Content + ProcessedContent
    ↓
Generate tags from multiple sources:
    ├─> GPT-4 analysis (contextual tags)
    ├─> Entity extraction (entity-based tags)
    └─> Key phrases (phrase-based tags)
    ↓
Merge & deduplicate (keep highest confidence)
    ↓
Sort by confidence & limit to max_tags
    ↓
Determine primary topic
    ↓
TaggedContent {
    tags: List[Tag(name, confidence, source)]
    primary_topic: str
}
```

#### Stratégie de scoring

```python
Tag confidence sources:
- GPT analysis:     0.70 - 1.00  (high, contextual)
- Entity-based:     0.70         (medium)
- Phrase-based:     0.75         (medium-high)

Min threshold: 0.70 (configurable)
Max tags per content: 10 (configurable)
```

### 4. Knowledge Base (`src/knowledge_base/`)

**Responsabilité**: Agréger contenus similaires et générer synthèses.

#### 4.1 KnowledgeAggregator

```python
class KnowledgeAggregator:
    def create_knowledge_clusters(tagged_contents) -> List[KnowledgeCluster]
    def _group_by_tags(tagged_contents) -> Dict[str, List]
    def _should_merge_clusters(cluster1, cluster2) -> bool
    def _merge_clusters(clusters) -> List[KnowledgeCluster]
```

**Algorithme de clustering**:

```
1. Grouper par tag principal
   ↓
2. Pour chaque paire de clusters:
   - Calculer similarité (Jaccard sur tags)
   - Si similarité >= threshold (0.75): merger
   ↓
3. Itérer jusqu'à convergence
   ↓
KnowledgeClusters {
    topic: str
    tags: List[str]
    content_ids: List[str]
}
```

**Similarité Jaccard**:
```python
similarity = |tags1 ∩ tags2| / |tags1 ∪ tags2|
```

#### 4.2 ContentSynthesizer

```python
class ContentSynthesizer:
    async def synthesize_cluster(...) -> KnowledgeCluster
    async def _generate_synthesis(...) -> str
    async def _generate_summary(...) -> str
    async def _assess_quality(...) -> float
    async def verify_factual_content(...) -> ContentQuality
```

**Flow de synthèse**:

```
KnowledgeCluster + Contents + ProcessedContents
    ↓
Build context from all sources:
    ├─> Original text
    ├─> Transcriptions
    └─> Visual descriptions
    ↓
GPT-4 generates synthesis:
    ├─> Identify common themes
    ├─> Combine complementary info
    ├─> Resolve contradictions
    └─> Distinguish facts from opinions
    ↓
Generate summary (configurable length)
    ↓
Assess quality:
    ├─> Number of sources
    ├─> Synthesis length
    └─> Coherence
    ↓
Updated KnowledgeCluster {
    synthesis: str
    summary: str
    quality_score: float
}
```

**Quality Assessment**:
```python
Base score: 0.5

+ sources >= 5:  +0.2
+ sources >= 3:  +0.1
+ 200-1000 words: +0.2
+ 100-200 words:  +0.1

Max: 1.0
```

### 5. Storage (`src/storage/`)

**Responsabilité**: Persistence des données dans SQLite.

#### Schema

```sql
-- Contents table
CREATE TABLE contents (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    content_type TEXT,
    url TEXT,
    text TEXT,
    author TEXT,
    created_at TIMESTAMP,
    collected_at TIMESTAMP,
    media_urls JSON,
    metadata JSON
);

-- Processed contents table
CREATE TABLE processed_contents (
    id INTEGER PRIMARY KEY,
    content_id TEXT REFERENCES contents(id),
    transcription TEXT,
    visual_description TEXT,
    extracted_text TEXT,
    detected_objects JSON,
    entities JSON,
    sentiment FLOAT,
    key_phrases JSON,
    processed_at TIMESTAMP
);

-- Tagged contents table
CREATE TABLE tagged_contents (
    id INTEGER PRIMARY KEY,
    content_id TEXT REFERENCES contents(id),
    tags JSON,  -- [{name, confidence, source}]
    primary_topic TEXT,
    tagged_at TIMESTAMP
);

-- Knowledge clusters table
CREATE TABLE knowledge_clusters (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    tags JSON,
    content_ids JSON,
    synthesis TEXT,
    summary TEXT,
    quality_score FLOAT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### ORM (SQLAlchemy)

```python
class DatabaseManager:
    def __init__(self, db_url: str)

    # Content operations
    def save_content(content: Content)
    def get_content(content_id: str) -> Content
    def get_all_contents() -> List[Content]

    # Processed content operations
    def save_processed_content(processed: ProcessedContent)
    def get_processed_content(content_id: str) -> ProcessedContent

    # Tagged content operations
    def save_tagged_content(tagged: TaggedContent)
    def get_all_tagged_contents() -> List[TaggedContent]

    # Cluster operations
    def save_knowledge_cluster(cluster: KnowledgeCluster)
    def get_all_clusters() -> List[KnowledgeCluster]
```

## 🔄 Data Flow complet

```
┌──────────────┐
│   Platforms  │ (Instagram, Facebook, LinkedIn, Beeper)
└──────┬───────┘
       │ Collectors.collect_saved_content()
       ▼
┌──────────────┐
│   Content    │ (raw text, media URLs, metadata)
└──────┬───────┘
       │ save_content()
       ▼
┌──────────────┐
│   Database   │
└──────────────┘
       │ get_all_contents()
       ▼
┌──────────────┐
│ Processors   │ (Transcription, Visual Analysis, NLP)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Processed    │ (transcription, entities, sentiment, etc.)
│ Content      │
└──────┬───────┘
       │ save_processed_content()
       ▼
┌──────────────┐
│   Database   │
└──────────────┘
       │ get_all_contents() + get_processed_content()
       ▼
┌──────────────┐
│   Tagger     │ (GPT-4 + embeddings)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Tagged     │ (tags with confidence, primary topic)
│   Content    │
└──────┬───────┘
       │ save_tagged_content()
       ▼
┌──────────────┐
│   Database   │
└──────────────┘
       │ get_all_tagged_contents()
       ▼
┌──────────────┐
│  Aggregator  │ (Cluster by tags)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Knowledge   │ (groups of related content)
│  Clusters    │
└──────┬───────┘
       │ get_all_contents() + get_processed_contents()
       ▼
┌──────────────┐
│ Synthesizer  │ (GPT-4 generates coherent synthesis)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Synthesized  │ (synthesis, summary, quality score)
│  Clusters    │
└──────┬───────┘
       │ save_knowledge_cluster()
       ▼
┌──────────────┐
│   Database   │ (final knowledge base)
└──────────────┘
```

## 🧩 Modèles de données (Pydantic)

### Content

```python
@dataclass
class Content:
    id: str                    # Unique identifier
    platform: Platform         # Enum: INSTAGRAM, FACEBOOK, etc.
    content_type: ContentType  # Enum: POST, VIDEO, IMAGE, etc.
    url: Optional[str]
    text: Optional[str]
    media_urls: List[str]
    author: Optional[str]
    created_at: datetime
    collected_at: datetime
    metadata: Dict[str, Any]
```

### ProcessedContent

```python
@dataclass
class ProcessedContent:
    content_id: str
    transcription: Optional[str]
    visual_description: Optional[str]
    extracted_text: Optional[str]     # OCR
    detected_objects: List[str]
    entities: List[str]               # NER
    sentiment: float                  # -1 to 1
    key_phrases: List[str]
    processed_at: datetime
```

### Tag & TaggedContent

```python
@dataclass
class Tag:
    name: str
    confidence: float     # 0 to 1
    source: str          # "gpt_analysis", "entity_extraction", etc.

@dataclass
class TaggedContent:
    content_id: str
    tags: List[Tag]
    primary_topic: Optional[str]
    tagged_at: datetime
```

### KnowledgeCluster

```python
@dataclass
class KnowledgeCluster:
    id: str
    topic: str
    tags: List[str]
    content_ids: List[str]
    synthesis: Optional[str]
    summary: Optional[str]
    quality_score: Optional[float]
    created_at: datetime
    updated_at: datetime
```

## 🔌 API Externes

### OpenAI API

```python
# GPT-4o-mini (cost-effective)
- Content analysis
- Tag generation
- Synthesis

# GPT-4 Vision
- Image description
- Object detection
- Visual context

# Whisper
- Audio transcription
- Video transcription
```

**Rate limits**: Géré avec retry + backoff

### Platform APIs

```python
# Instagram: Instaloader (unofficial)
- Saved posts
- Stories
- Highlights

# Facebook: Graph API (official)
- Saved posts
- Photos/Videos

# LinkedIn: Unofficial scraping
- To be implemented

# Beeper: Matrix protocol
- Notes only
- To be implemented
```

## ⚙️ Configuration

### Hiérarchie

```
1. Defaults (hardcoded)
2. config.yaml (structure)
3. .env (secrets)
4. Runtime overrides
```

### Config loading

```python
# src/config.py
class Settings(BaseSettings):
    openai_api_key: str
    instagram_username: str
    # ... loaded from .env

    class Config:
        env_file = ".env"

settings = Settings()
config = yaml.safe_load(open("config/config.yaml"))
```

## 🚦 Error Handling Strategy

### Niveaux

1. **Collector errors**: Log + continue with next item
2. **Processor errors**: Log + save partial result
3. **Database errors**: Raise + rollback
4. **API errors**: Retry with backoff (max 3x)

### Logging

```python
from loguru import logger

logger.add("logs/app.log", rotation="1 day")

# Usage
logger.info("Collected 50 posts from Instagram")
logger.error(f"Failed to transcribe video: {error}")
logger.debug(f"API response: {response}")
```

## 📈 Performance Considerations

### Bottlenecks

1. **OpenAI API calls**: Most expensive operation
   - Use gpt-4o-mini when possible
   - Batch requests
   - Cache results

2. **Media downloads**: I/O intensive
   - Async downloads
   - Stream large files

3. **Database writes**: Can be slow with large batches
   - Batch inserts
   - Use transactions

### Optimizations

```python
# Parallelize independent operations
async def process_all(contents):
    tasks = [process_content(c) for c in contents]
    return await asyncio.gather(*tasks)

# Cache embeddings
@lru_cache(maxsize=1000)
def get_embedding(text: str):
    return model.encode(text)

# Batch database operations
with db.session.begin():
    for content in contents:
        db.add(content)
```

## 🔒 Security

### Secrets Management

- **Never commit** `.env` file
- Use environment variables for all credentials
- Rotate API keys regularly

### Data Privacy

- User content is stored locally (SQLite)
- No data sent to third parties (except OpenAI for processing)
- Implement data retention policy

## 🧪 Testing Strategy (à implémenter)

### Unit Tests

```python
# Test collectors with mocked APIs
@pytest.fixture
def mock_instagram_api():
    with patch('instaloader.Instaloader') as mock:
        yield mock

def test_instagram_collector(mock_instagram_api):
    collector = InstagramCollector()
    contents = await collector.collect_saved_content(limit=10)
    assert len(contents) <= 10
```

### Integration Tests

```python
# Test full pipeline with small dataset
def test_full_pipeline():
    archiver = SocialContentArchiver()
    contents = await archiver.collect_all_content()
    await archiver.process_content(contents)
    await archiver.tag_all_content()
    await archiver.build_knowledge_base()

    clusters = archiver.db.get_all_clusters()
    assert len(clusters) > 0
```

## 📊 Monitoring (futur)

### Metrics à tracker

- Number of contents collected per platform
- Processing success/failure rate
- API costs (OpenAI)
- Cluster quality distribution
- Database size

### Alerting

- Failed authentication
- API rate limits hit
- Database errors
- High costs

---

**Version**: 0.1.0
**Dernière mise à jour**: 2026-01-11
