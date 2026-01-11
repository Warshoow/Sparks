"""Aggregates related content into knowledge clusters"""
from typing import List, Dict, Set
from collections import defaultdict
from loguru import logger
import uuid

from ..config import config
from ..models import TaggedContent, KnowledgeCluster
from ..tagging.tagger import ContentTagger


class KnowledgeAggregator:
    """Aggregates related content based on tags and topics"""

    def __init__(self):
        self.tagger = ContentTagger()
        self.min_related_items = config["knowledge_base"]["aggregation"]["min_related_items"]
        self.similarity_threshold = config["knowledge_base"]["aggregation"]["similarity_threshold"]

    def find_related_content(
        self,
        tagged_contents: List[TaggedContent]
    ) -> Dict[str, List[str]]:
        """Find groups of related content based on tags"""
        # Group content by tags
        tag_to_content: Dict[str, Set[str]] = defaultdict(set)

        for tagged in tagged_contents:
            for tag in tagged.tags:
                tag_to_content[tag.name].add(tagged.content_id)

        # Find clusters of related content
        clusters: Dict[str, Set[str]] = {}

        for tag, content_ids in tag_to_content.items():
            if len(content_ids) >= self.min_related_items:
                # Create or merge cluster
                cluster_key = tag
                if cluster_key not in clusters:
                    clusters[cluster_key] = set()
                clusters[cluster_key].update(content_ids)

        logger.info(f"Found {len(clusters)} content clusters")
        return {k: list(v) for k, v in clusters.items()}

    def merge_similar_clusters(
        self,
        clusters: Dict[str, List[str]],
        tagged_contents: List[TaggedContent]
    ) -> Dict[str, List[str]]:
        """Merge clusters that are similar to each other"""
        # Create a map for quick lookup
        content_tags_map = {
            tc.content_id: [tag.name for tag in tc.tags]
            for tc in tagged_contents
        }

        merged_clusters = {}
        processed_tags = set()

        for tag1, content_ids1 in clusters.items():
            if tag1 in processed_tags:
                continue

            # Start a new merged cluster
            merged_content = set(content_ids1)
            merged_tags = {tag1}

            # Check for similar clusters
            for tag2, content_ids2 in clusters.items():
                if tag2 == tag1 or tag2 in processed_tags:
                    continue

                # Calculate overlap
                overlap = len(set(content_ids1) & set(content_ids2))
                total = len(set(content_ids1) | set(content_ids2))

                if total > 0 and (overlap / total) >= self.similarity_threshold:
                    # Merge clusters
                    merged_content.update(content_ids2)
                    merged_tags.add(tag2)
                    processed_tags.add(tag2)

            # Create merged cluster key
            cluster_key = "_".join(sorted(merged_tags))
            merged_clusters[cluster_key] = list(merged_content)
            processed_tags.add(tag1)

        logger.info(f"Merged into {len(merged_clusters)} final clusters")
        return merged_clusters

    def create_knowledge_clusters(
        self,
        tagged_contents: List[TaggedContent]
    ) -> List[KnowledgeCluster]:
        """Create knowledge clusters from tagged content"""
        knowledge_clusters = []

        try:
            # Find related content
            initial_clusters = self.find_related_content(tagged_contents)

            # Merge similar clusters
            final_clusters = self.merge_similar_clusters(initial_clusters, tagged_contents)

            # Create KnowledgeCluster objects
            for topic, content_ids in final_clusters.items():
                tags = topic.split("_")

                cluster = KnowledgeCluster(
                    id=str(uuid.uuid4()),
                    topic=topic.replace("_", " ").title(),
                    tags=tags,
                    content_ids=content_ids
                )

                knowledge_clusters.append(cluster)
                logger.debug(f"Created cluster '{cluster.topic}' with {len(content_ids)} items")

            logger.info(f"Created {len(knowledge_clusters)} knowledge clusters")

        except Exception as e:
            logger.error(f"Error creating knowledge clusters: {e}")

        return knowledge_clusters

    def find_content_by_topic(
        self,
        topic: str,
        clusters: List[KnowledgeCluster]
    ) -> List[str]:
        """Find all content IDs related to a specific topic"""
        content_ids = []

        for cluster in clusters:
            if topic.lower() in cluster.topic.lower() or topic.lower() in cluster.tags:
                content_ids.extend(cluster.content_ids)

        return list(set(content_ids))

    def get_cluster_statistics(self, cluster: KnowledgeCluster) -> Dict:
        """Get statistics about a knowledge cluster"""
        return {
            "id": cluster.id,
            "topic": cluster.topic,
            "num_tags": len(cluster.tags),
            "num_content_items": len(cluster.content_ids),
            "tags": cluster.tags,
            "quality_score": cluster.quality_score
        }
