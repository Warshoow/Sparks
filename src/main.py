"""Main application entry point and orchestration"""
import asyncio
from pathlib import Path
from typing import List, Optional
from loguru import logger
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .config import settings, config
from .models import Platform, Content
from .collectors import (
    InstagramCollector,
    FacebookCollector,
    LinkedInCollector,
    BeeperCollector
)
from .processors import (
    TranscriptionProcessor,
    VisualAnalysisProcessor,
    ContentAnalyzer
)
from .tagging import ContentTagger
from .knowledge_base import KnowledgeAggregator, ContentSynthesizer
from .storage import DatabaseManager

console = Console()


class SocialContentArchiver:
    """Main application orchestrator"""

    def __init__(self):
        self.db = DatabaseManager()
        self.collectors = self._init_collectors()
        self.transcription = TranscriptionProcessor()
        self.visual_analysis = VisualAnalysisProcessor()
        self.content_analyzer = ContentAnalyzer()
        self.tagger = ContentTagger()
        self.aggregator = KnowledgeAggregator()
        self.synthesizer = ContentSynthesizer()

        # Ensure directories exist
        settings.archive_path.mkdir(parents=True, exist_ok=True)
        settings.media_path.mkdir(parents=True, exist_ok=True)

    def _init_collectors(self) -> dict:
        """Initialize collectors for enabled platforms"""
        collectors = {}
        enabled = config["collectors"]["enabled_platforms"]

        if "instagram" in enabled:
            collectors["instagram"] = InstagramCollector()
        if "facebook" in enabled:
            collectors["facebook"] = FacebookCollector()
        if "linkedin" in enabled:
            collectors["linkedin"] = LinkedInCollector()
        if "beeper" in enabled:
            collectors["beeper"] = BeeperCollector()

        return collectors

    async def collect_all_content(self) -> List[Content]:
        """Collect content from all enabled platforms"""
        all_content = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:

            for platform_name, collector in self.collectors.items():
                task = progress.add_task(f"Collecting from {platform_name}...", total=None)

                try:
                    # Authenticate
                    if await collector.authenticate():
                        # Collect content
                        max_posts = config["collectors"].get(platform_name, {}).get("max_posts_per_sync", 100)
                        contents = await collector.collect_saved_content(limit=max_posts)

                        # Save to database
                        for content in contents:
                            self.db.save_content(content)

                        all_content.extend(contents)
                        logger.info(f"Collected {len(contents)} items from {platform_name}")
                    else:
                        logger.warning(f"Failed to authenticate with {platform_name}")

                except Exception as e:
                    logger.error(f"Error collecting from {platform_name}: {e}")

                progress.update(task, completed=True)

        console.print(f"\n[green]✓[/green] Collected {len(all_content)} total items")
        return all_content

    async def process_content(self, contents: List[Content]) -> None:
        """Process all collected content"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:

            task = progress.add_task("Processing content...", total=len(contents))

            for content in contents:
                try:
                    processed = await self.content_analyzer.analyze_content(content)

                    # Save processed content
                    self.db.save_processed_content(processed)

                except Exception as e:
                    logger.error(f"Error processing content {content.id}: {e}")

                progress.advance(task)

        console.print(f"[green]✓[/green] Processed {len(contents)} items")

    async def tag_all_content(self) -> None:
        """Tag all content in database"""
        contents = self.db.get_all_contents()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:

            task = progress.add_task("Tagging content...", total=len(contents))

            for content in contents:
                try:
                    # Get processed content
                    from .models import ProcessedContent
                    processed = ProcessedContent(content_id=content.id)

                    # Tag content
                    tagged = await self.tagger.tag_content(content, processed)

                    # Save tagged content
                    self.db.save_tagged_content(tagged)

                except Exception as e:
                    logger.error(f"Error tagging content {content.id}: {e}")

                progress.advance(task)

        console.print(f"[green]✓[/green] Tagged {len(contents)} items")

    async def build_knowledge_base(self) -> None:
        """Build knowledge base from tagged content"""
        console.print("\n[bold]Building Knowledge Base[/bold]")

        # Get all tagged content
        tagged_contents = self.db.get_all_tagged_contents()
        console.print(f"Found {len(tagged_contents)} tagged items")

        # Create clusters
        with console.status("[bold green]Creating knowledge clusters..."):
            clusters = self.aggregator.create_knowledge_clusters(tagged_contents)

        console.print(f"[green]✓[/green] Created {len(clusters)} knowledge clusters")

        # Synthesize clusters
        contents = self.db.get_all_contents()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:

            task = progress.add_task("Synthesizing clusters...", total=len(clusters))

            for cluster in clusters:
                try:
                    # Get content for this cluster
                    cluster_contents = [c for c in contents if c.id in cluster.content_ids]

                    # Get processed content (placeholder)
                    from .models import ProcessedContent
                    processed_contents = [
                        ProcessedContent(content_id=c.id)
                        for c in cluster_contents
                    ]

                    # Synthesize
                    synthesized_cluster = await self.synthesizer.synthesize_cluster(
                        cluster,
                        cluster_contents,
                        processed_contents
                    )

                    # Save cluster
                    self.db.save_knowledge_cluster(synthesized_cluster)

                except Exception as e:
                    logger.error(f"Error synthesizing cluster {cluster.id}: {e}")

                progress.advance(task)

        console.print(f"[green]✓[/green] Synthesized {len(clusters)} clusters")

    def display_knowledge_base(self) -> None:
        """Display the knowledge base"""
        clusters = self.db.get_all_clusters()

        console.print(f"\n[bold]Knowledge Base Summary[/bold]")
        console.print(f"Total clusters: {len(clusters)}\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Topic", style="cyan")
        table.add_column("Items", justify="right")
        table.add_column("Quality", justify="right")
        table.add_column("Tags")

        for cluster in clusters:
            quality = f"{cluster.quality_score:.2f}" if cluster.quality_score else "N/A"
            tags = ", ".join(cluster.tags[:3]) + ("..." if len(cluster.tags) > 3 else "")

            table.add_row(
                cluster.topic,
                str(len(cluster.content_ids)),
                quality,
                tags
            )

        console.print(table)


@click.group()
def cli():
    """Social Content Archiver - Build knowledge from your saved social media content"""
    pass


@cli.command()
def collect():
    """Collect saved content from all configured platforms"""
    archiver = SocialContentArchiver()
    asyncio.run(archiver.collect_all_content())


@cli.command()
def process():
    """Process collected content (transcription, visual analysis, etc.)"""
    archiver = SocialContentArchiver()
    contents = archiver.db.get_all_contents()
    asyncio.run(archiver.process_content(contents))


@cli.command()
def tag():
    """Tag all processed content"""
    archiver = SocialContentArchiver()
    asyncio.run(archiver.tag_all_content())


@cli.command()
def build():
    """Build knowledge base from tagged content"""
    archiver = SocialContentArchiver()
    asyncio.run(archiver.build_knowledge_base())


@cli.command()
def run():
    """Run full pipeline: collect -> process -> tag -> build"""
    console.print("[bold]Starting Social Content Archiver[/bold]\n")

    archiver = SocialContentArchiver()

    # Collect
    console.print("\n[bold cyan]Step 1: Collecting Content[/bold cyan]")
    contents = asyncio.run(archiver.collect_all_content())

    if not contents:
        console.print("[yellow]No content collected. Exiting.[/yellow]")
        return

    # Process
    console.print("\n[bold cyan]Step 2: Processing Content[/bold cyan]")
    asyncio.run(archiver.process_content(contents))

    # Tag
    console.print("\n[bold cyan]Step 3: Tagging Content[/bold cyan]")
    asyncio.run(archiver.tag_all_content())

    # Build knowledge base
    console.print("\n[bold cyan]Step 4: Building Knowledge Base[/bold cyan]")
    asyncio.run(archiver.build_knowledge_base())

    # Display results
    archiver.display_knowledge_base()

    console.print("\n[bold green]✓ Complete![/bold green]")


@cli.command()
def show():
    """Show current knowledge base"""
    archiver = SocialContentArchiver()
    archiver.display_knowledge_base()


if __name__ == "__main__":
    cli()
