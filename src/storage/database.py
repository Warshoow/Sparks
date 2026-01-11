"""Database management for storing content and knowledge"""
from typing import List, Optional
from datetime import datetime
import json
from loguru import logger
from sqlalchemy import create_engine, Column, String, DateTime, Float, Text, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from ..config import settings
from ..models import (
    Content, ProcessedContent, TaggedContent,
    KnowledgeCluster, ContentQuality, Platform, ContentType
)

Base = declarative_base()


class ContentDB(Base):
    """Content table"""
    __tablename__ = "contents"

    id = Column(String, primary_key=True)
    platform = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    url = Column(String)
    text = Column(Text)
    media_urls = Column(JSON)
    author = Column(String)
    created_at = Column(DateTime, nullable=False)
    collected_at = Column(DateTime, nullable=False)
    metadata = Column(JSON)


class ProcessedContentDB(Base):
    """Processed content table"""
    __tablename__ = "processed_contents"

    content_id = Column(String, primary_key=True)
    transcription = Column(Text)
    visual_description = Column(Text)
    extracted_text = Column(Text)
    detected_objects = Column(JSON)
    entities = Column(JSON)
    sentiment = Column(Float)
    key_phrases = Column(JSON)
    processed_at = Column(DateTime, nullable=False)


class TaggedContentDB(Base):
    """Tagged content table"""
    __tablename__ = "tagged_contents"

    content_id = Column(String, primary_key=True)
    tags = Column(JSON)
    primary_topic = Column(String)
    tagged_at = Column(DateTime, nullable=False)


class KnowledgeClusterDB(Base):
    """Knowledge cluster table"""
    __tablename__ = "knowledge_clusters"

    id = Column(String, primary_key=True)
    topic = Column(String, nullable=False)
    tags = Column(JSON)
    content_ids = Column(JSON)
    summary = Column(Text)
    synthesis = Column(Text)
    quality_score = Column(Float)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class ContentQualityDB(Base):
    """Content quality table"""
    __tablename__ = "content_quality"

    content_id = Column(String, primary_key=True)
    is_factual = Column(Integer)  # Use Integer for boolean (SQLite compatibility)
    confidence = Column(Float)
    quality_score = Column(Float)
    issues = Column(JSON)
    verified_at = Column(DateTime, nullable=False)


class DatabaseManager:
    """Manages all database operations"""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Create tables
        Base.metadata.create_all(self.engine)
        logger.info("Database initialized")

    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()

    # Content operations
    def save_content(self, content: Content) -> bool:
        """Save content to database"""
        try:
            session = self.get_session()

            content_db = ContentDB(
                id=content.id,
                platform=content.platform.value,
                content_type=content.content_type.value,
                url=content.url,
                text=content.text,
                media_urls=content.media_urls,
                author=content.author,
                created_at=content.created_at,
                collected_at=content.collected_at,
                metadata=content.metadata
            )

            session.merge(content_db)
            session.commit()
            session.close()

            logger.debug(f"Saved content: {content.id}")
            return True

        except Exception as e:
            logger.error(f"Error saving content: {e}")
            return False

    def get_content(self, content_id: str) -> Optional[Content]:
        """Retrieve content by ID"""
        try:
            session = self.get_session()
            content_db = session.query(ContentDB).filter_by(id=content_id).first()
            session.close()

            if content_db:
                return Content(
                    id=content_db.id,
                    platform=Platform(content_db.platform),
                    content_type=ContentType(content_db.content_type),
                    url=content_db.url,
                    text=content_db.text,
                    media_urls=content_db.media_urls or [],
                    author=content_db.author,
                    created_at=content_db.created_at,
                    collected_at=content_db.collected_at,
                    metadata=content_db.metadata or {}
                )

            return None

        except Exception as e:
            logger.error(f"Error retrieving content: {e}")
            return None

    def get_all_contents(self) -> List[Content]:
        """Get all contents"""
        try:
            session = self.get_session()
            contents_db = session.query(ContentDB).all()
            session.close()

            contents = []
            for cdb in contents_db:
                contents.append(Content(
                    id=cdb.id,
                    platform=Platform(cdb.platform),
                    content_type=ContentType(cdb.content_type),
                    url=cdb.url,
                    text=cdb.text,
                    media_urls=cdb.media_urls or [],
                    author=cdb.author,
                    created_at=cdb.created_at,
                    collected_at=cdb.collected_at,
                    metadata=cdb.metadata or {}
                ))

            return contents

        except Exception as e:
            logger.error(f"Error retrieving all contents: {e}")
            return []

    # Processed content operations
    def save_processed_content(self, processed: ProcessedContent) -> bool:
        """Save processed content"""
        try:
            session = self.get_session()

            processed_db = ProcessedContentDB(
                content_id=processed.content_id,
                transcription=processed.transcription,
                visual_description=processed.visual_description,
                extracted_text=processed.extracted_text,
                detected_objects=processed.detected_objects,
                entities=processed.entities,
                sentiment=processed.sentiment,
                key_phrases=processed.key_phrases,
                processed_at=processed.processed_at
            )

            session.merge(processed_db)
            session.commit()
            session.close()

            logger.debug(f"Saved processed content: {processed.content_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving processed content: {e}")
            return False

    # Tagged content operations
    def save_tagged_content(self, tagged: TaggedContent) -> bool:
        """Save tagged content"""
        try:
            session = self.get_session()

            tags_json = [
                {"name": tag.name, "confidence": tag.confidence, "source": tag.source}
                for tag in tagged.tags
            ]

            tagged_db = TaggedContentDB(
                content_id=tagged.content_id,
                tags=tags_json,
                primary_topic=tagged.primary_topic,
                tagged_at=tagged.tagged_at
            )

            session.merge(tagged_db)
            session.commit()
            session.close()

            logger.debug(f"Saved tagged content: {tagged.content_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving tagged content: {e}")
            return False

    def get_all_tagged_contents(self) -> List[TaggedContent]:
        """Get all tagged contents"""
        try:
            session = self.get_session()
            tagged_db = session.query(TaggedContentDB).all()
            session.close()

            from ..models import Tag

            tagged_contents = []
            for tdb in tagged_db:
                tags = [
                    Tag(name=t["name"], confidence=t["confidence"], source=t["source"])
                    for t in (tdb.tags or [])
                ]

                tagged_contents.append(TaggedContent(
                    content_id=tdb.content_id,
                    tags=tags,
                    primary_topic=tdb.primary_topic,
                    tagged_at=tdb.tagged_at
                ))

            return tagged_contents

        except Exception as e:
            logger.error(f"Error retrieving tagged contents: {e}")
            return []

    # Knowledge cluster operations
    def save_knowledge_cluster(self, cluster: KnowledgeCluster) -> bool:
        """Save knowledge cluster"""
        try:
            session = self.get_session()

            cluster_db = KnowledgeClusterDB(
                id=cluster.id,
                topic=cluster.topic,
                tags=cluster.tags,
                content_ids=cluster.content_ids,
                summary=cluster.summary,
                synthesis=cluster.synthesis,
                quality_score=cluster.quality_score,
                created_at=cluster.created_at,
                updated_at=cluster.updated_at
            )

            session.merge(cluster_db)
            session.commit()
            session.close()

            logger.debug(f"Saved knowledge cluster: {cluster.id}")
            return True

        except Exception as e:
            logger.error(f"Error saving knowledge cluster: {e}")
            return False

    def get_all_clusters(self) -> List[KnowledgeCluster]:
        """Get all knowledge clusters"""
        try:
            session = self.get_session()
            clusters_db = session.query(KnowledgeClusterDB).all()
            session.close()

            clusters = []
            for cdb in clusters_db:
                clusters.append(KnowledgeCluster(
                    id=cdb.id,
                    topic=cdb.topic,
                    tags=cdb.tags or [],
                    content_ids=cdb.content_ids or [],
                    summary=cdb.summary,
                    synthesis=cdb.synthesis,
                    quality_score=cdb.quality_score,
                    created_at=cdb.created_at,
                    updated_at=cdb.updated_at
                ))

            return clusters

        except Exception as e:
            logger.error(f"Error retrieving clusters: {e}")
            return []
