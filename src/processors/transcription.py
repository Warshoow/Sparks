"""Audio and video transcription using OpenAI Whisper"""
from typing import Optional
from pathlib import Path
from loguru import logger
import openai

from ..config import settings, config


class TranscriptionProcessor:
    """Processes audio/video content to extract transcriptions"""

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = config["processors"]["transcription"]["model"]
        self.language = config["processors"]["transcription"]["language"]

    async def transcribe_audio(self, audio_path: str) -> Optional[str]:
        """Transcribe audio file to text"""
        try:
            audio_file = Path(audio_path)
            if not audio_file.exists():
                logger.error(f"Audio file not found: {audio_path}")
                return None

            with open(audio_path, "rb") as audio:
                transcript = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio,
                    language=self.language if self.language != "auto" else None
                )

            logger.info(f"Transcribed audio: {audio_path}")
            return transcript.text

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None

    async def transcribe_video(self, video_path: str) -> Optional[str]:
        """Extract audio from video and transcribe"""
        try:
            from moviepy.editor import VideoFileClip

            video_file = Path(video_path)
            if not video_file.exists():
                logger.error(f"Video file not found: {video_path}")
                return None

            # Extract audio from video
            video = VideoFileClip(video_path)
            audio_path = str(video_file.with_suffix('.mp3'))
            video.audio.write_audiofile(audio_path, logger=None)
            video.close()

            # Transcribe extracted audio
            transcription = await self.transcribe_audio(audio_path)

            # Clean up temporary audio file
            Path(audio_path).unlink(missing_ok=True)

            logger.info(f"Transcribed video: {video_path}")
            return transcription

        except Exception as e:
            logger.error(f"Error transcribing video: {e}")
            return None

    async def transcribe(self, media_path: str, media_type: str) -> Optional[str]:
        """Transcribe audio or video file"""
        if media_type in ["audio", "mp3", "wav", "m4a"]:
            return await self.transcribe_audio(media_path)
        elif media_type in ["video", "mp4", "mov", "avi"]:
            return await self.transcribe_video(media_path)
        else:
            logger.warning(f"Unsupported media type for transcription: {media_type}")
            return None
