"""Instagram content collector"""
from typing import List, Optional
from loguru import logger
import instaloader
from datetime import datetime

from .base import BaseCollector
from ..models import Content, ContentType, Platform
from ..config import settings


class InstagramCollector(BaseCollector):
    """Collector for Instagram saved posts"""

    def __init__(self):
        super().__init__(Platform.INSTAGRAM)
        self.loader = instaloader.Instaloader()
        self._authenticated = False

    async def authenticate(self) -> bool:
        """Authenticate with Instagram"""
        try:
            if not settings.instagram_username or not settings.instagram_password:
                logger.warning("Instagram credentials not configured")
                return False

            self.loader.login(
                settings.instagram_username,
                settings.instagram_password
            )
            self._authenticated = True
            logger.info("Successfully authenticated with Instagram")
            return True

        except Exception as e:
            logger.error(f"Instagram authentication failed: {e}")
            return False

    async def collect_saved_content(self, limit: Optional[int] = None) -> List[Content]:
        """Collect saved posts from Instagram"""
        if not self._authenticated:
            logger.warning("Not authenticated with Instagram")
            return []

        contents = []
        try:
            profile = instaloader.Profile.from_username(
                self.loader.context,
                settings.instagram_username
            )

            # Get saved posts
            saved_posts = profile.get_saved_posts()

            count = 0
            for post in saved_posts:
                if limit and count >= limit:
                    break

                # Determine content type
                if post.is_video:
                    content_type = ContentType.VIDEO
                elif post.typename == "GraphSidecar":
                    content_type = ContentType.MIXED
                else:
                    content_type = ContentType.IMAGE

                # Extract media URLs
                media_urls = []
                if post.is_video:
                    media_urls.append(post.video_url)
                else:
                    media_urls.append(post.url)

                # Create content object
                content = Content(
                    id=f"ig_{post.shortcode}",
                    platform=Platform.INSTAGRAM,
                    content_type=content_type,
                    url=f"https://instagram.com/p/{post.shortcode}",
                    text=post.caption if post.caption else None,
                    media_urls=media_urls,
                    author=post.owner_username,
                    created_at=post.date_utc,
                    metadata={
                        "likes": post.likes,
                        "comments": post.comments,
                        "location": post.location.name if post.location else None,
                    }
                )

                contents.append(content)
                count += 1
                logger.debug(f"Collected Instagram post: {post.shortcode}")

            logger.info(f"Collected {len(contents)} saved Instagram posts")

        except Exception as e:
            logger.error(f"Error collecting Instagram content: {e}")

        return contents

    async def download_media(self, content: Content, output_path: str) -> List[str]:
        """Download media files for Instagram content"""
        downloaded_files = []

        try:
            # Extract shortcode from content ID
            shortcode = content.id.replace("ig_", "")
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)

            # Download using instaloader
            self.loader.download_post(post, target=output_path)

            # Return list of downloaded files (simplified)
            downloaded_files = content.media_urls
            logger.info(f"Downloaded media for Instagram post: {shortcode}")

        except Exception as e:
            logger.error(f"Error downloading Instagram media: {e}")

        return downloaded_files

    def is_authenticated(self) -> bool:
        return self._authenticated
