"""Content tagging and categorization"""
from typing import List, Optional
from loguru import logger
import openai
from sentence_transformers import SentenceTransformer

from ..config import settings, config
from ..models import Content, ProcessedContent, Tag, TaggedContent


class ContentTagger:
    """Automatically tags content based on analysis"""

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.min_confidence = config["tagging"]["min_confidence"]
        self.max_tags = config["tagging"]["max_tags_per_content"]

        # Load sentence transformer for semantic analysis
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.warning(f"Could not load embedding model: {e}")
            self.embedding_model = None

    async def generate_tags_with_gpt(
        self,
        content: Content,
        processed: ProcessedContent
    ) -> List[Tag]:
        """Generate tags using GPT"""
        try:
            # Build context from all available information
            context_parts = []

            if content.text:
                context_parts.append(f"Original text: {content.text}")

            if processed.transcription:
                context_parts.append(f"Transcription: {processed.transcription}")

            if processed.visual_description:
                context_parts.append(f"Visual content: {processed.visual_description}")

            if processed.entities:
                context_parts.append(f"Entities: {', '.join(processed.entities)}")

            if processed.key_phrases:
                context_parts.append(f"Key phrases: {', '.join(processed.key_phrases)}")

            context = "\n".join(context_parts)

            prompt = f"""Analyze the following content and generate relevant tags.
Each tag should be a single word or short phrase that categorizes the content.
Include topic tags, theme tags, and subject matter tags.
Rate each tag with a confidence score from 0 to 1.

Content:
{context}

Provide up to {self.max_tags} most relevant tags in this format:
tag_name: confidence_score

Example:
technology: 0.95
artificial_intelligence: 0.88
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content categorization system."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=300
            )

            result = response.choices[0].message.content
            tags = []

            # Parse tags from response
            for line in result.strip().split('\n'):
                if ':' in line:
                    try:
                        tag_name, confidence_str = line.split(':', 1)
                        tag_name = tag_name.strip()
                        confidence = float(confidence_str.strip())

                        if confidence >= self.min_confidence:
                            tags.append(Tag(
                                name=tag_name,
                                confidence=confidence,
                                source="gpt_analysis"
                            ))
                    except ValueError:
                        continue

            logger.info(f"Generated {len(tags)} tags for content: {content.id}")
            return tags[:self.max_tags]

        except Exception as e:
            logger.error(f"Error generating tags with GPT: {e}")
            return []

    async def extract_tags_from_entities(self, processed: ProcessedContent) -> List[Tag]:
        """Extract tags from identified entities"""
        tags = []

        for entity in processed.entities:
            # Entity-based tags have medium confidence
            tags.append(Tag(
                name=entity.lower().replace(' ', '_'),
                confidence=0.7,
                source="entity_extraction"
            ))

        logger.info(f"Extracted {len(tags)} tags from entities")
        return tags

    async def extract_tags_from_key_phrases(self, processed: ProcessedContent) -> List[Tag]:
        """Extract tags from key phrases"""
        tags = []

        for phrase in processed.key_phrases:
            # Phrase-based tags have medium-high confidence
            tags.append(Tag(
                name=phrase.lower().replace(' ', '_'),
                confidence=0.75,
                source="key_phrase_extraction"
            ))

        logger.info(f"Extracted {len(tags)} tags from key phrases")
        return tags

    def determine_primary_topic(self, tags: List[Tag]) -> Optional[str]:
        """Determine the primary topic from tags"""
        if not tags:
            return None

        # Sort tags by confidence
        sorted_tags = sorted(tags, key=lambda t: t.confidence, reverse=True)

        # Return the highest confidence tag
        return sorted_tags[0].name

    async def tag_content(
        self,
        content: Content,
        processed: ProcessedContent
    ) -> TaggedContent:
        """Generate comprehensive tags for content"""
        all_tags = []

        try:
            # Generate tags from different sources
            gpt_tags = await self.generate_tags_with_gpt(content, processed)
            all_tags.extend(gpt_tags)

            if config["tagging"]["tag_sources"].count("content_text"):
                entity_tags = await self.extract_tags_from_entities(processed)
                all_tags.extend(entity_tags)

                phrase_tags = await self.extract_tags_from_key_phrases(processed)
                all_tags.extend(phrase_tags)

            # Remove duplicates (keep highest confidence)
            unique_tags = {}
            for tag in all_tags:
                if tag.name not in unique_tags or tag.confidence > unique_tags[tag.name].confidence:
                    unique_tags[tag.name] = tag

            final_tags = list(unique_tags.values())

            # Sort by confidence and limit
            final_tags.sort(key=lambda t: t.confidence, reverse=True)
            final_tags = final_tags[:self.max_tags]

            # Determine primary topic
            primary_topic = self.determine_primary_topic(final_tags)

            logger.info(f"Tagged content {content.id} with {len(final_tags)} tags, primary topic: {primary_topic}")

            return TaggedContent(
                content_id=content.id,
                tags=final_tags,
                primary_topic=primary_topic
            )

        except Exception as e:
            logger.error(f"Error tagging content: {e}")
            return TaggedContent(
                content_id=content.id,
                tags=[],
                primary_topic=None
            )

    def calculate_similarity(self, tags1: List[str], tags2: List[str]) -> float:
        """Calculate similarity between two sets of tags"""
        if not tags1 or not tags2:
            return 0.0

        # Simple Jaccard similarity
        set1 = set(tags1)
        set2 = set(tags2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        return intersection / union

    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        if not self.embedding_model:
            return 0.0

        try:
            embeddings = self.embedding_model.encode([text1, text2])
            # Calculate cosine similarity
            from numpy import dot
            from numpy.linalg import norm

            similarity = dot(embeddings[0], embeddings[1]) / (
                norm(embeddings[0]) * norm(embeddings[1])
            )

            return float(similarity)

        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0
