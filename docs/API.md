# API Documentation

Documentation des interfaces publiques et des modules principaux du Social Content Archiver.

## 📚 Table des matières

- [Models](#models)
- [Collectors](#collectors)
- [Processors](#processors)
- [Tagging](#tagging)
- [Knowledge Base](#knowledge-base)
- [Storage](#storage)

## Models

### Content

Représente un contenu collecté depuis une plateforme sociale.

```python
@dataclass
class Content:
    id: str                         # Unique identifier (platform_postid)
    platform: Platform              # Source platform
    content_type: ContentType       # Type of content
    url: Optional[str]              # Original URL
    text: Optional[str]             # Text content
    media_urls: List[str]           # URLs of media files
    author: Optional[str]           # Content author
    created_at: datetime            # When content was created
    collected_at: datetime          # When we collected it
    metadata: Dict[str, Any]        # Additional metadata

# Enums
class Platform(str, Enum):
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    BEEPER = "beeper"

class ContentType(str, Enum):
    POST = "post"
    VIDEO = "video"
    IMAGE = "image"
    STORY = "story"
    NOTE = "note"
```

**Example:**

```python
content = Content(
    id="instagram_ABC123",
    platform=Platform.INSTAGRAM,
    content_type=ContentType.POST,
    url="https://instagram.com/p/ABC123/",
    text="Amazing view! #travel",
    media_urls=["https://example.com/photo.jpg"],
    author="traveler_joe",
    created_at=datetime(2024, 1, 15, 10, 30),
    collected_at=datetime.now(),
    metadata={"likes": 250, "comments": 18}
)
```

### ProcessedContent

Résultat du traitement d'un contenu (transcription, analyse visuelle, NLP).

```python
@dataclass
class ProcessedContent:
    content_id: str                     # Reference to Content.id
    transcription: Optional[str]        # Audio/video transcription
    visual_description: Optional[str]   # GPT-4V description
    extracted_text: Optional[str]       # OCR text
    detected_objects: List[str]         # Detected objects
    entities: List[str]                 # Named entities (NER)
    sentiment: float                    # Sentiment score (-1 to 1)
    key_phrases: List[str]              # Important phrases
    processed_at: datetime              # Processing timestamp
```

**Example:**

```python
processed = ProcessedContent(
    content_id="instagram_ABC123",
    transcription=None,
    visual_description="A scenic mountain landscape at sunset",
    extracted_text="",
    detected_objects=["mountains", "sky", "sunset"],
    entities=["travel", "nature"],
    sentiment=0.85,
    key_phrases=["amazing view", "beautiful sunset"],
    processed_at=datetime.now()
)
```

### TaggedContent

Contenu avec tags générés automatiquement.

```python
@dataclass
class Tag:
    name: str           # Tag name (lowercase, underscore-separated)
    confidence: float   # Confidence score (0-1)
    source: str         # Where tag came from

@dataclass
class TaggedContent:
    content_id: str             # Reference to Content.id
    tags: List[Tag]             # List of tags
    primary_topic: Optional[str] # Main topic
    tagged_at: datetime         # Tagging timestamp
```

**Example:**

```python
tagged = TaggedContent(
    content_id="instagram_ABC123",
    tags=[
        Tag(name="travel", confidence=0.95, source="gpt_analysis"),
        Tag(name="nature", confidence=0.88, source="gpt_analysis"),
        Tag(name="photography", confidence=0.75, source="entity_extraction")
    ],
    primary_topic="travel",
    tagged_at=datetime.now()
)
```

### KnowledgeCluster

Groupe de contenus liés avec synthèse.

```python
@dataclass
class KnowledgeCluster:
    id: str                         # Unique cluster ID
    topic: str                      # Main topic
    tags: List[str]                 # Common tags
    content_ids: List[str]          # IDs of contents in cluster
    synthesis: Optional[str]        # Generated synthesis
    summary: Optional[str]          # Short summary
    quality_score: Optional[float]  # Quality assessment (0-1)
    created_at: datetime
    updated_at: datetime
```

**Example:**

```python
cluster = KnowledgeCluster(
    id="cluster_travel_001",
    topic="travel",
    tags=["travel", "nature", "photography", "adventure"],
    content_ids=["instagram_ABC123", "facebook_XYZ789", ...],
    synthesis="A comprehensive view of travel experiences...",
    summary="Collection of travel insights from various trips.",
    quality_score=0.82,
    created_at=datetime.now(),
    updated_at=datetime.now()
)
```

## Collectors

### BaseCollector (Abstract)

Interface de base pour tous les collectors.

```python
class BaseCollector(ABC):
    """Abstract base class for platform collectors."""

    def __init__(self, platform: Platform):
        self.platform = platform

    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the platform.

        Returns:
            True if authentication successful, False otherwise
        """
        pass

    @abstractmethod
    async def collect_saved_content(
        self,
        limit: Optional[int] = None
    ) -> List[Content]:
        """Collect saved content from platform.

        Args:
            limit: Maximum number of items to collect

        Returns:
            List of Content objects

        Raises:
            AuthenticationError: If not authenticated
            CollectionError: If collection fails
        """
        pass

    @abstractmethod
    async def download_media(
        self,
        content: Content,
        output_path: str
    ) -> List[str]:
        """Download media files for a content item.

        Args:
            content: Content object with media URLs
            output_path: Directory to save files

        Returns:
            List of downloaded file paths

        Raises:
            DownloadError: If download fails
        """
        pass

    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        pass
```

### InstagramCollector

Collecte les posts sauvegardés depuis Instagram.

```python
class InstagramCollector(BaseCollector):
    """Collector for Instagram saved posts."""

    def __init__(self):
        super().__init__(Platform.INSTAGRAM)
        self.username = settings.instagram_username
        self.password = settings.instagram_password

    async def authenticate(self) -> bool:
        """Authenticate with Instagram using Instaloader."""

    async def collect_saved_content(
        self,
        limit: Optional[int] = None
    ) -> List[Content]:
        """Collect saved posts from Instagram."""

    async def download_media(
        self,
        content: Content,
        output_path: str
    ) -> List[str]:
        """Download images/videos from Instagram post."""
```

**Example usage:**

```python
collector = InstagramCollector()

if await collector.authenticate():
    contents = await collector.collect_saved_content(limit=50)
    print(f"Collected {len(contents)} posts")

    for content in contents:
        media_files = await collector.download_media(
            content,
            output_path="/path/to/media"
        )
```

## Processors

### TranscriptionProcessor

Transcrit l'audio et la vidéo avec OpenAI Whisper.

```python
class TranscriptionProcessor:
    """Transcribes audio and video using OpenAI Whisper."""

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = "whisper-1"

    async def transcribe_audio(self, file_path: str) -> str:
        """Transcribe an audio file.

        Args:
            file_path: Path to audio file (mp3, wav, etc.)

        Returns:
            Transcribed text

        Raises:
            TranscriptionError: If transcription fails
        """

    async def transcribe_video(self, file_path: str) -> str:
        """Transcribe a video file by extracting audio first.

        Args:
            file_path: Path to video file (mp4, mov, etc.)

        Returns:
            Transcribed text

        Raises:
            TranscriptionError: If transcription fails
        """

    async def extract_audio_from_video(
        self,
        video_path: str
    ) -> str:
        """Extract audio track from video.

        Args:
            video_path: Path to video file

        Returns:
            Path to extracted audio file

        Raises:
            ExtractionError: If extraction fails
        """
```

**Example usage:**

```python
processor = TranscriptionProcessor()

# Audio
text = await processor.transcribe_audio("podcast.mp3")

# Video
text = await processor.transcribe_video("interview.mp4")
```

### VisualAnalysisProcessor

Analyse les images avec GPT-4 Vision et Tesseract OCR.

```python
class VisualAnalysisProcessor:
    """Analyzes images using GPT-4 Vision and OCR."""

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.ocr_enabled = config["processors"]["visual_analysis"]["extract_text"]

    async def analyze_image(self, image_path: str) -> VisualAnalysis:
        """Perform complete visual analysis of an image.

        Args:
            image_path: Path to image file

        Returns:
            VisualAnalysis object with all analysis results

        Raises:
            AnalysisError: If analysis fails
        """

    async def describe_image_content(self, image_path: str) -> str:
        """Get contextual description of image using GPT-4V.

        Args:
            image_path: Path to image file

        Returns:
            Natural language description

        Raises:
            VisionError: If GPT-4V call fails
        """

    async def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using OCR.

        Args:
            image_path: Path to image file

        Returns:
            Extracted text

        Raises:
            OCRError: If OCR fails
        """

    async def detect_objects(self, image_path: str) -> List[str]:
        """Detect objects in image using GPT-4V.

        Args:
            image_path: Path to image file

        Returns:
            List of detected objects

        Raises:
            VisionError: If detection fails
        """
```

**Example usage:**

```python
processor = VisualAnalysisProcessor()

analysis = await processor.analyze_image("photo.jpg")
print(f"Description: {analysis.description}")
print(f"OCR text: {analysis.extracted_text}")
print(f"Objects: {analysis.detected_objects}")
```

### ContentAnalyzer

Analyse le texte avec NLP (spaCy et GPT-4).

```python
class ContentAnalyzer:
    """Analyzes text content using NLP and GPT-4."""

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)

    async def analyze_content(
        self,
        content: Content,
        transcription: Optional[str] = None,
        visual_description: Optional[str] = None
    ) -> ProcessedContent:
        """Complete content analysis.

        Args:
            content: Content object to analyze
            transcription: Optional transcription text
            visual_description: Optional visual analysis

        Returns:
            ProcessedContent with all analysis results

        Raises:
            AnalysisError: If analysis fails
        """

    async def extract_entities_from_text(self, text: str) -> List[str]:
        """Extract named entities (people, places, etc.).

        Args:
            text: Text to analyze

        Returns:
            List of entity names

        Raises:
            NLPError: If NER fails
        """

    async def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text.

        Args:
            text: Text to analyze

        Returns:
            Sentiment score from -1 (negative) to 1 (positive)

        Raises:
            AnalysisError: If sentiment analysis fails
        """

    async def extract_key_phrases(self, text: str) -> List[str]:
        """Extract important phrases and topics.

        Args:
            text: Text to analyze

        Returns:
            List of key phrases

        Raises:
            AnalysisError: If extraction fails
        """
```

**Example usage:**

```python
analyzer = ContentAnalyzer()

processed = await analyzer.analyze_content(
    content,
    transcription="This is the transcription...",
    visual_description="A beautiful landscape"
)

print(f"Entities: {processed.entities}")
print(f"Sentiment: {processed.sentiment}")
print(f"Key phrases: {processed.key_phrases}")
```

## Tagging

### ContentTagger

Génère des tags automatiques pour le contenu.

```python
class ContentTagger:
    """Automatically tags content using GPT-4 and embeddings."""

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.min_confidence = config["tagging"]["min_confidence"]
        self.max_tags = config["tagging"]["max_tags_per_content"]

    async def tag_content(
        self,
        content: Content,
        processed: ProcessedContent
    ) -> TaggedContent:
        """Generate comprehensive tags for content.

        Args:
            content: Original content
            processed: Processed content analysis

        Returns:
            TaggedContent with tags and primary topic

        Raises:
            TaggingError: If tagging fails
        """

    async def generate_tags_with_gpt(
        self,
        content: Content,
        processed: ProcessedContent
    ) -> List[Tag]:
        """Generate contextual tags using GPT-4.

        Args:
            content: Content to tag
            processed: Analysis results

        Returns:
            List of tags with confidence scores

        Raises:
            GPTError: If GPT call fails
        """

    def calculate_similarity(
        self,
        tags1: List[str],
        tags2: List[str]
    ) -> float:
        """Calculate Jaccard similarity between tag sets.

        Args:
            tags1: First tag set
            tags2: Second tag set

        Returns:
            Similarity score (0-1)
        """

    def calculate_semantic_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """Calculate semantic similarity using embeddings.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Cosine similarity score (0-1)

        Raises:
            EmbeddingError: If embedding generation fails
        """
```

**Example usage:**

```python
tagger = ContentTagger()

tagged = await tagger.tag_content(content, processed)

print(f"Primary topic: {tagged.primary_topic}")
for tag in tagged.tags:
    print(f"- {tag.name} ({tag.confidence:.2f}) from {tag.source}")

# Check similarity
sim = tagger.calculate_similarity(
    ["travel", "nature"],
    ["adventure", "nature", "hiking"]
)
print(f"Similarity: {sim:.2f}")
```

## Knowledge Base

### KnowledgeAggregator

Regroupe les contenus similaires en clusters.

```python
class KnowledgeAggregator:
    """Aggregates related content into knowledge clusters."""

    def __init__(self):
        self.similarity_threshold = config["knowledge_base"]["aggregation"]["similarity_threshold"]
        self.min_related_items = config["knowledge_base"]["aggregation"]["min_related_items"]

    def create_knowledge_clusters(
        self,
        tagged_contents: List[TaggedContent]
    ) -> List[KnowledgeCluster]:
        """Create knowledge clusters from tagged content.

        Args:
            tagged_contents: List of tagged content items

        Returns:
            List of knowledge clusters

        Raises:
            AggregationError: If clustering fails
        """

    def _should_merge_clusters(
        self,
        cluster1: KnowledgeCluster,
        cluster2: KnowledgeCluster
    ) -> bool:
        """Determine if two clusters should be merged.

        Args:
            cluster1: First cluster
            cluster2: Second cluster

        Returns:
            True if clusters should be merged
        """
```

**Example usage:**

```python
aggregator = KnowledgeAggregator()

clusters = aggregator.create_knowledge_clusters(tagged_contents)

for cluster in clusters:
    print(f"\nCluster: {cluster.topic}")
    print(f"Tags: {cluster.tags}")
    print(f"Contents: {len(cluster.content_ids)}")
```

### ContentSynthesizer

Génère des synthèses à partir de clusters de contenus.

```python
class ContentSynthesizer:
    """Synthesizes content clusters into coherent knowledge."""

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.summary_length = config["knowledge_base"]["synthesis"]["summary_length"]

    async def synthesize_cluster(
        self,
        cluster: KnowledgeCluster,
        contents: List[Content],
        processed_contents: List[ProcessedContent]
    ) -> KnowledgeCluster:
        """Synthesize a cluster into coherent summary.

        Args:
            cluster: Knowledge cluster to synthesize
            contents: Content items in cluster
            processed_contents: Processed analysis of contents

        Returns:
            Updated cluster with synthesis and summary

        Raises:
            SynthesisError: If synthesis fails
        """

    async def verify_factual_content(
        self,
        content: Content,
        processed: ProcessedContent
    ) -> ContentQuality:
        """Verify factual accuracy of content.

        Args:
            content: Content to verify
            processed: Processed analysis

        Returns:
            ContentQuality assessment

        Raises:
            VerificationError: If verification fails
        """
```

**Example usage:**

```python
synthesizer = ContentSynthesizer()

cluster = await synthesizer.synthesize_cluster(
    cluster,
    contents,
    processed_contents
)

print(f"Synthesis:\n{cluster.synthesis}")
print(f"\nSummary:\n{cluster.summary}")
print(f"Quality: {cluster.quality_score:.2f}")
```

## Storage

### DatabaseManager

Gère la persistence avec SQLite/SQLAlchemy.

```python
class DatabaseManager:
    """Manages database operations for content storage."""

    def __init__(self, db_url: str = "sqlite:///data/archive.db"):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    # Content operations
    def save_content(self, content: Content) -> None:
        """Save or update content in database."""

    def get_content(self, content_id: str) -> Optional[Content]:
        """Retrieve content by ID."""

    def get_all_contents(self) -> List[Content]:
        """Retrieve all contents."""

    # Processed content operations
    def save_processed_content(self, processed: ProcessedContent) -> None:
        """Save processed content analysis."""

    def get_processed_content(
        self,
        content_id: str
    ) -> Optional[ProcessedContent]:
        """Retrieve processed content by content ID."""

    # Tagged content operations
    def save_tagged_content(self, tagged: TaggedContent) -> None:
        """Save tagged content."""

    def get_all_tagged_contents(self) -> List[TaggedContent]:
        """Retrieve all tagged contents."""

    # Cluster operations
    def save_knowledge_cluster(self, cluster: KnowledgeCluster) -> None:
        """Save knowledge cluster."""

    def get_cluster(self, cluster_id: str) -> Optional[KnowledgeCluster]:
        """Retrieve cluster by ID."""

    def get_all_clusters(self) -> List[KnowledgeCluster]:
        """Retrieve all knowledge clusters."""
```

**Example usage:**

```python
db = DatabaseManager()

# Save content
db.save_content(content)

# Retrieve
retrieved = db.get_content("instagram_ABC123")

# Get all
all_contents = db.get_all_contents()
print(f"Total contents: {len(all_contents)}")
```

## Error Handling

Toutes les fonctions peuvent lever des exceptions personnalisées :

```python
class ArchiverError(Exception):
    """Base exception for archiver."""

class AuthenticationError(ArchiverError):
    """Authentication failed."""

class CollectionError(ArchiverError):
    """Content collection failed."""

class ProcessingError(ArchiverError):
    """Content processing failed."""

class TaggingError(ArchiverError):
    """Tagging failed."""

class StorageError(ArchiverError):
    """Database operation failed."""
```

**Usage:**

```python
try:
    contents = await collector.collect_saved_content()
except AuthenticationError:
    logger.error("Please check your credentials")
except CollectionError as e:
    logger.error(f"Failed to collect: {e}")
```

---

**Version**: 0.1.0
**Dernière mise à jour**: 2026-01-11
