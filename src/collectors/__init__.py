"""Content collectors for various social media platforms"""
from .base import BaseCollector
from .instagram import InstagramCollector
from .facebook import FacebookCollector
from .linkedin import LinkedInCollector
from .beeper import BeeperCollector

__all__ = [
    "BaseCollector",
    "InstagramCollector",
    "FacebookCollector",
    "LinkedInCollector",
    "BeeperCollector",
]
