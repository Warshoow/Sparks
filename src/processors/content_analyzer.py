"""Content analysis for extracting entities, sentiment, and key phrases"""
from typing import List, Dict, Any, Optional
from loguru import logger

from ..config import config, get_llm_client, get_chat_model
from ..models import ProcessedContent, Content


class ContentAnalyzer:
    """Analyzes text content for entities, sentiment, and key information"""

    def __init__(self):
        self.client = get_llm_client()
        self.extract_entities = config["processors"]["content_analysis"]["extract_entities"]
        self.sentiment_analysis = config["processors"]["content_analysis"]["sentiment_analysis"]
        self.key_phrases = config["processors"]["content_analysis"]["key_phrases"]

    async def analyze_text_with_gpt(self, text: str) -> Dict[str, Any]:
        """Use GPT to analyze text content"""
        try:
            prompt = f"""Analyze the following text and provide:
1. Entities (people, organizations, locations, concepts)
2. Sentiment (positive/negative/neutral with score from -1 to 1)
3. Key phrases (important topics or ideas)
4. Main topics/themes

Text: {text}

Format your response as JSON with keys: entities, sentiment, sentiment_score, key_phrases, topics"""

            response = self.client.chat.completions.create(
                model=get_chat_model(),
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes text content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            result = response.choices[0].message.content

            # In production, properly parse JSON response
            # For now, return simplified structure
            return {
                "entities": [],
                "sentiment": 0.0,
                "key_phrases": [],
                "topics": []
            }

        except Exception as e:
            logger.error(f"Error analyzing text with GPT: {e}")
            return {}

    async def extract_entities_from_text(self, text: str) -> List[str]:
        """Extract named entities from text"""
        try:
            # Using spaCy for NER (if available)
            import spacy

            nlp = spacy.load("en_core_web_sm")
            doc = nlp(text)

            entities = [ent.text for ent in doc.ents]
            logger.info(f"Extracted {len(entities)} entities from text")
            return entities

        except ImportError:
            logger.warning("spaCy not available, using GPT for entity extraction")
            analysis = await self.analyze_text_with_gpt(text)
            return analysis.get("entities", [])
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []

    async def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text (-1 to 1)"""
        try:
            analysis = await self.analyze_text_with_gpt(text)
            sentiment = analysis.get("sentiment_score", 0.0)

            logger.info(f"Sentiment score: {sentiment}")
            return sentiment

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return 0.0

    async def extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text"""
        try:
            analysis = await self.analyze_text_with_gpt(text)
            phrases = analysis.get("key_phrases", [])

            logger.info(f"Extracted {len(phrases)} key phrases")
            return phrases

        except Exception as e:
            logger.error(f"Error extracting key phrases: {e}")
            return []

    async def analyze_content(
        self,
        content: Content,
        transcription: Optional[str] = None,
        visual_description: Optional[str] = None
    ) -> ProcessedContent:
        """Complete content analysis"""
        # Combine all text sources
        text_parts = []
        if content.text:
            text_parts.append(content.text)
        if transcription:
            text_parts.append(transcription)
        if visual_description:
            text_parts.append(visual_description)

        combined_text = " ".join(text_parts)

        # Analyze
        entities = []
        sentiment = 0.0
        key_phrases_list = []

        try:
            if self.extract_entities and combined_text:
                entities = await self.extract_entities_from_text(combined_text)

            if self.sentiment_analysis and combined_text:
                sentiment = await self.analyze_sentiment(combined_text)

            if self.key_phrases and combined_text:
                key_phrases_list = await self.extract_key_phrases(combined_text)

            logger.info(f"Completed content analysis for: {content.id}")

        except Exception as e:
            logger.error(f"Error in content analysis: {e}")

        return ProcessedContent(
            content_id=content.id,
            entities=entities,
            sentiment=sentiment,
            key_phrases=key_phrases_list
        )
