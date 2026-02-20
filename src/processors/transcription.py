"""Audio and video transcription using OpenAI Whisper or Faster-Whisper"""
from typing import Optional
from pathlib import Path
from loguru import logger

from ..config import settings, config, get_llm_client


class TranscriptionProcessor:
    """Processes audio/video content to extract transcriptions.

    Supports two backends:
    - "openai": Uses OpenAI Whisper API (cloud, paid)
    - "faster-whisper": Uses Faster-Whisper locally (free)
    """

    def __init__(self):
        transcription_config = config["processors"]["transcription"]
        self.language = transcription_config["language"]
        self.provider = settings.transcription_provider

        if self.provider == "faster-whisper":
            self._init_faster_whisper()
        else:
            self._init_openai(transcription_config)

    def _init_openai(self, transcription_config: dict) -> None:
        """Initialize OpenAI Whisper backend."""
        self.client = get_llm_client()
        self.model = transcription_config["model"]
        self._whisper_model = None
        logger.info("Transcription backend: OpenAI Whisper API")

    def _init_faster_whisper(self) -> None:
        """Initialize Faster-Whisper backend."""
        try:
            from faster_whisper import WhisperModel

            model_size = settings.faster_whisper_model
            device = settings.faster_whisper_device
            compute_type = settings.faster_whisper_compute_type

            self._whisper_model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
            )
            self.client = None
            self.model = None
            logger.info(
                f"Transcription backend: Faster-Whisper "
                f"(model={model_size}, device={device}, compute={compute_type})"
            )
        except ImportError:
            logger.error(
                "faster-whisper not installed. "
                "Install with: pip install faster-whisper"
            )
            raise

    async def transcribe_audio(self, audio_path: str) -> Optional[str]:
        """Transcribe audio file to text"""
        try:
            audio_file = Path(audio_path)
            if not audio_file.exists():
                logger.error(f"Audio file not found: {audio_path}")
                return None

            if self.provider == "faster-whisper":
                return self._transcribe_with_faster_whisper(audio_path)
            else:
                return self._transcribe_with_openai(audio_path)

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None

    def _transcribe_with_openai(self, audio_path: str) -> Optional[str]:
        """Transcribe using OpenAI Whisper API."""
        with open(audio_path, "rb") as audio:
            transcript = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio,
                language=self.language if self.language != "auto" else None,
            )
        logger.info(f"Transcribed audio (OpenAI): {audio_path}")
        return transcript.text

    def _transcribe_with_faster_whisper(self, audio_path: str) -> Optional[str]:
        """Transcribe using Faster-Whisper locally."""
        language = self.language if self.language != "auto" else None

        segments, info = self._whisper_model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
        )

        text = " ".join(segment.text.strip() for segment in segments)

        logger.info(
            f"Transcribed audio (Faster-Whisper): {audio_path} "
            f"[detected={info.language}, prob={info.language_probability:.2f}]"
        )
        return text if text else None

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
