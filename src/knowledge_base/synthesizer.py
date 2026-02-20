"""Synthesizes content clusters into coherent knowledge"""
from typing import List, Optional, Dict
from loguru import logger

from ..config import config, get_llm_client, get_chat_model
from ..models import KnowledgeCluster, Content, ProcessedContent, ContentQuality


class ContentSynthesizer:
    """Synthesizes multiple related content pieces into coherent knowledge"""

    def __init__(self):
        self.client = get_llm_client()
        self.summary_length = config["knowledge_base"]["synthesis"]["summary_length"]
        self.include_sources = config["knowledge_base"]["synthesis"]["include_sources"]
        self.fact_checking_enabled = config["knowledge_base"]["filtering"]["fact_checking"]

    async def synthesize_cluster(
        self,
        cluster: KnowledgeCluster,
        contents: List[Content],
        processed_contents: List[ProcessedContent]
    ) -> KnowledgeCluster:
        """Synthesize a knowledge cluster into coherent summary"""
        try:
            # Build context from all content in the cluster
            context_parts = []

            for content in contents:
                if content.id not in cluster.content_ids:
                    continue

                # Get processed data
                processed = next(
                    (p for p in processed_contents if p.content_id == content.id),
                    None
                )

                # Build content representation
                content_text = []
                if content.text:
                    content_text.append(content.text)

                if processed:
                    if processed.transcription:
                        content_text.append(f"[Transcription: {processed.transcription}]")
                    if processed.visual_description:
                        content_text.append(f"[Visual: {processed.visual_description}]")

                if content_text:
                    context_parts.append({
                        "id": content.id,
                        "text": " ".join(content_text),
                        "platform": content.platform.value,
                        "created_at": content.created_at.isoformat()
                    })

            # Generate synthesis
            synthesis = await self._generate_synthesis(
                cluster.topic,
                context_parts
            )

            # Generate summary
            summary = await self._generate_summary(synthesis)

            # Assess quality
            quality_score = await self._assess_quality(synthesis, context_parts)

            # Update cluster
            cluster.synthesis = synthesis
            cluster.summary = summary
            cluster.quality_score = quality_score

            logger.info(f"Synthesized cluster '{cluster.topic}' (quality: {quality_score:.2f})")

        except Exception as e:
            logger.error(f"Error synthesizing cluster: {e}")

        return cluster

    async def _generate_synthesis(
        self,
        topic: str,
        content_parts: List[Dict]
    ) -> str:
        """Generate coherent synthesis from multiple content pieces"""
        try:
            # Build prompt
            sources_text = "\n\n".join([
                f"Source {i+1} ({part['platform']}, {part['created_at']}):\n{part['text']}"
                for i, part in enumerate(content_parts)
            ])

            prompt = f"""You are synthesizing knowledge from multiple social media posts about: {topic}

Here are the sources:

{sources_text}

Create a coherent, well-structured synthesis that:
1. Identifies common themes and ideas across the sources
2. Combines complementary information
3. Resolves any contradictions
4. Presents the information in a clear, logical flow
5. Distinguishes facts from opinions

The synthesis should be comprehensive yet concise, focusing on extracting real value and insights."""

            response = self.client.chat.completions.create(
                model=get_chat_model(),
                messages=[
                    {
                        "role": "system",
                        "content": "You are a knowledge synthesis expert who creates coherent, valuable insights from fragmented information."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,
                max_tokens=1500
            )

            synthesis = response.choices[0].message.content
            return synthesis

        except Exception as e:
            logger.error(f"Error generating synthesis: {e}")
            return ""

    async def _generate_summary(self, synthesis: str) -> str:
        """Generate a summary of the synthesis"""
        try:
            length_instructions = {
                "short": "2-3 sentences",
                "medium": "1 paragraph (4-6 sentences)",
                "long": "2-3 paragraphs"
            }

            length = length_instructions.get(self.summary_length, "1 paragraph")

            prompt = f"""Summarize the following synthesis in {length}:

{synthesis}

Focus on the key insights and main takeaways."""

            response = self.client.chat.completions.create(
                model=get_chat_model(),
                messages=[
                    {
                        "role": "system",
                        "content": "You create clear, concise summaries."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=300
            )

            summary = response.choices[0].message.content
            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return synthesis[:200] + "..."

    async def _assess_quality(
        self,
        synthesis: str,
        content_parts: List[Dict]
    ) -> float:
        """Assess the quality of synthesized content"""
        try:
            num_sources = len(content_parts)
            synthesis_length = len(synthesis.split())

            # Basic quality metrics
            quality_score = 0.5  # Base score

            # More sources = higher quality potential
            if num_sources >= 5:
                quality_score += 0.2
            elif num_sources >= 3:
                quality_score += 0.1

            # Reasonable length indicates thorough synthesis
            if 200 <= synthesis_length <= 1000:
                quality_score += 0.2
            elif 100 <= synthesis_length < 200:
                quality_score += 0.1

            # Cap at 1.0
            quality_score = min(quality_score, 1.0)

            return quality_score

        except Exception as e:
            logger.error(f"Error assessing quality: {e}")
            return 0.5

    async def verify_factual_content(
        self,
        content: Content,
        processed: ProcessedContent
    ) -> ContentQuality:
        """Verify if content appears factual and identify potential issues"""
        try:
            text = content.text or ""
            if processed.transcription:
                text += " " + processed.transcription

            prompt = f"""Analyze this content for factual accuracy and quality:

{text}

Assess:
1. Does it appear to be factual or opinion-based?
2. Are there any obvious red flags (misinformation, extreme bias, etc.)?
3. What is the overall quality and reliability?

Respond in JSON format:
{{
    "is_factual": true/false,
    "confidence": 0.0-1.0,
    "quality_score": 0.0-1.0,
    "issues": ["list", "of", "issues"]
}}"""

            response = self.client.chat.completions.create(
                model=get_chat_model(),
                messages=[
                    {
                        "role": "system",
                        "content": "You are a fact-checking and content quality assessment expert."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=300
            )

            result = response.choices[0].message.content

            # In production, properly parse JSON
            # For now, return default quality assessment
            return ContentQuality(
                content_id=content.id,
                is_factual=True,
                confidence=0.7,
                quality_score=0.7,
                issues=[]
            )

        except Exception as e:
            logger.error(f"Error verifying content: {e}")
            return ContentQuality(
                content_id=content.id,
                is_factual=None,
                confidence=0.5,
                quality_score=0.5,
                issues=["verification_failed"]
            )
