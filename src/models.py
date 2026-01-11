"""Data models for the application"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Platform(str, Enum):
    """Supported social media platforms"""
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    BEEPER = "beeper"


class ContentType(str, Enum):
    """Types of content"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    NOTE = "note"
    MIXED = "mixed"


class Content(BaseModel):
    """Base content model"""
    id: str
    platform: Platform
    content_type: ContentType
    url: Optional[str] = None
    text: Optional[str] = None
    media_urls: List[str] = Field(default_factory=list)
    author: Optional[str] = None
    created_at: datetime
    collected_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProcessedContent(BaseModel):
    """Processed content with analysis"""
    content_id: str
    transcription: Optional[str] = None
    visual_description: Optional[str] = None
    extracted_text: Optional[str] = None  # OCR
    detected_objects: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    sentiment: Optional[float] = None  # -1 to 1
    key_phrases: List[str] = Field(default_factory=list)
    processed_at: datetime = Field(default_factory=datetime.now)


class Tag(BaseModel):
    """Content tag"""
    name: str
    confidence: float = Field(ge=0.0, le=1.0)
    source: str  # where the tag came from
    category: Optional[str] = None


class TaggedContent(BaseModel):
    """Content with tags"""
    content_id: str
    tags: List[Tag] = Field(default_factory=list)
    primary_topic: Optional[str] = None
    tagged_at: datetime = Field(default_factory=datetime.now)


class KnowledgeCluster(BaseModel):
    """Cluster of related content by tags"""
    id: str
    topic: str
    tags: List[str]
    content_ids: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    synthesis: Optional[str] = None
    quality_score: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ContentQuality(BaseModel):
    """Quality assessment of content"""
    content_id: str
    is_factual: Optional[bool] = None
    confidence: float = Field(ge=0.0, le=1.0)
    quality_score: float = Field(ge=0.0, le=1.0)
    issues: List[str] = Field(default_factory=list)
    verified_at: datetime = Field(default_factory=datetime.now)
