"""Base collector interface"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..models import Content, Platform


class BaseCollector(ABC):
    """Base class for all social media collectors"""

    def __init__(self, platform: Platform):
        self.platform = platform

    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the platform"""
        pass

    @abstractmethod
    async def collect_saved_content(self, limit: Optional[int] = None) -> List[Content]:
        """Collect saved/archived content from the platform"""
        pass

    @abstractmethod
    async def download_media(self, content: Content, output_path: str) -> List[str]:
        """Download media files associated with content"""
        pass

    def is_authenticated(self) -> bool:
        """Check if collector is authenticated"""
        return False
