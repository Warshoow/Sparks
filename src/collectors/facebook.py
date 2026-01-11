"""Facebook content collector"""
from typing import List, Optional
from loguru import logger
import requests
from datetime import datetime

from .base import BaseCollector
from ..models import Content, ContentType, Platform
from ..config import settings


class FacebookCollector(BaseCollector):
    """Collector for Facebook saved posts"""

    def __init__(self):
        super().__init__(Platform.FACEBOOK)
        self.access_token = settings.facebook_access_token
        self.api_base = "https://graph.facebook.com/v18.0"
        self._authenticated = False

    async def authenticate(self) -> bool:
        """Authenticate with Facebook"""
        try:
            if not self.access_token:
                logger.warning("Facebook access token not configured")
                return False

            # Verify token
            response = requests.get(
                f"{self.api_base}/me",
                params={"access_token": self.access_token}
            )

            if response.status_code == 200:
                self._authenticated = True
                logger.info("Successfully authenticated with Facebook")
                return True
            else:
                logger.error(f"Facebook authentication failed: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Facebook authentication error: {e}")
            return False

    async def collect_saved_content(self, limit: Optional[int] = None) -> List[Content]:
        """Collect saved posts from Facebook"""
        if not self._authenticated:
            logger.warning("Not authenticated with Facebook")
            return []

        contents = []
        try:
            # Get saved posts (using Facebook's saved items collection)
            response = requests.get(
                f"{self.api_base}/me/saved",
                params={
                    "access_token": self.access_token,
                    "fields": "id,message,created_time,picture,full_picture,type,link,from",
                    "limit": limit or 100
                }
            )

            if response.status_code != 200:
                logger.error(f"Failed to fetch saved posts: {response.text}")
                return []

            data = response.json()

            for item in data.get("data", []):
                # Determine content type
                item_type = item.get("type", "")
                if "video" in item_type:
                    content_type = ContentType.VIDEO
                elif "photo" in item_type:
                    content_type = ContentType.IMAGE
                else:
                    content_type = ContentType.TEXT

                # Extract media URLs
                media_urls = []
                if item.get("full_picture"):
                    media_urls.append(item["full_picture"])
                elif item.get("picture"):
                    media_urls.append(item["picture"])

                # Create content object
                content = Content(
                    id=f"fb_{item['id']}",
                    platform=Platform.FACEBOOK,
                    content_type=content_type,
                    url=item.get("link"),
                    text=item.get("message"),
                    media_urls=media_urls,
                    author=item.get("from", {}).get("name"),
                    created_at=datetime.fromisoformat(item["created_time"].replace("Z", "+00:00")),
                    metadata={
                        "type": item.get("type"),
                    }
                )

                contents.append(content)
                logger.debug(f"Collected Facebook post: {item['id']}")

            logger.info(f"Collected {len(contents)} saved Facebook posts")

        except Exception as e:
            logger.error(f"Error collecting Facebook content: {e}")

        return contents

    async def download_media(self, content: Content, output_path: str) -> List[str]:
        """Download media files for Facebook content"""
        downloaded_files = []

        try:
            for url in content.media_urls:
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    filename = f"{output_path}/{content.id}_{len(downloaded_files)}.jpg"
                    with open(filename, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    downloaded_files.append(filename)
                    logger.debug(f"Downloaded media: {filename}")

            logger.info(f"Downloaded {len(downloaded_files)} files for Facebook post: {content.id}")

        except Exception as e:
            logger.error(f"Error downloading Facebook media: {e}")

        return downloaded_files

    def is_authenticated(self) -> bool:
        return self._authenticated
