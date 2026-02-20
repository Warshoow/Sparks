"""Visual content analysis using OCR and AI vision models"""
from typing import Optional, List, Dict, Any
from pathlib import Path
from loguru import logger
import base64
import cv2
from PIL import Image

from ..config import config, get_llm_client, get_vision_model


class VisualAnalysisProcessor:
    """Processes images and videos for visual content analysis"""

    def __init__(self):
        self.client = get_llm_client()
        self.extract_text_enabled = config["processors"]["visual_analysis"]["extract_text"]
        self.detect_objects_enabled = config["processors"]["visual_analysis"]["detect_objects"]
        self.analyze_context_enabled = config["processors"]["visual_analysis"]["analyze_context"]

    async def extract_text_from_image(self, image_path: str) -> Optional[str]:
        """Extract text from image using OCR"""
        try:
            import pytesseract

            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)

            logger.info(f"Extracted text from image: {image_path}")
            return text.strip() if text else None

        except ImportError:
            logger.warning("pytesseract not installed, OCR unavailable")
            return None
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return None

    async def analyze_image_with_gpt4v(self, image_path: str) -> Dict[str, Any]:
        """Analyze image using GPT-4 Vision"""
        try:
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            response = self.client.chat.completions.create(
                model=get_vision_model(),
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this image and provide: 1) A detailed description, 2) List of objects/elements visible, 3) Context and setting, 4) Any text visible in the image. Format your response as JSON."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )

            result = response.choices[0].message.content
            logger.info(f"Analyzed image with GPT-4V: {image_path}")

            # Parse result (simplified - in production, parse JSON properly)
            return {
                "description": result,
                "objects": [],
                "context": result
            }

        except Exception as e:
            logger.error(f"Error analyzing image with GPT-4V: {e}")
            return {}

    async def detect_objects(self, image_path: str) -> List[str]:
        """Detect objects in image"""
        try:
            # Using OpenCV with a pre-trained model (simplified example)
            # In production, use YOLO, Faster R-CNN, or similar
            image = cv2.imread(image_path)

            # Placeholder for object detection
            # This would use an actual object detection model
            objects = []

            logger.info(f"Detected objects in image: {image_path}")
            return objects

        except Exception as e:
            logger.error(f"Error detecting objects: {e}")
            return []

    async def extract_video_frames(self, video_path: str, num_frames: int = 5) -> List[str]:
        """Extract key frames from video for analysis"""
        try:
            from moviepy.editor import VideoFileClip

            video = VideoFileClip(video_path)
            duration = video.duration
            frames_path = []

            # Extract frames at regular intervals
            for i in range(num_frames):
                timestamp = (duration / num_frames) * i
                frame_path = f"{video_path}_frame_{i}.jpg"
                video.save_frame(frame_path, t=timestamp)
                frames_path.append(frame_path)

            video.close()
            logger.info(f"Extracted {num_frames} frames from video: {video_path}")
            return frames_path

        except Exception as e:
            logger.error(f"Error extracting video frames: {e}")
            return []

    async def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Complete image analysis"""
        result = {
            "extracted_text": None,
            "objects": [],
            "description": None,
            "context": None
        }

        try:
            if self.extract_text_enabled:
                result["extracted_text"] = await self.extract_text_from_image(image_path)

            if self.analyze_context_enabled:
                analysis = await self.analyze_image_with_gpt4v(image_path)
                result["description"] = analysis.get("description")
                result["context"] = analysis.get("context")

            if self.detect_objects_enabled:
                result["objects"] = await self.detect_objects(image_path)

            logger.info(f"Completed analysis of image: {image_path}")

        except Exception as e:
            logger.error(f"Error in complete image analysis: {e}")

        return result

    async def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """Complete video analysis by analyzing key frames"""
        result = {
            "frames_analysis": [],
            "overall_description": None,
            "objects": []
        }

        try:
            # Extract key frames
            frames = await self.extract_video_frames(video_path)

            # Analyze each frame
            for frame_path in frames:
                frame_analysis = await self.analyze_image(frame_path)
                result["frames_analysis"].append(frame_analysis)

                # Aggregate objects
                if frame_analysis.get("objects"):
                    result["objects"].extend(frame_analysis["objects"])

            # Remove duplicate objects
            result["objects"] = list(set(result["objects"]))

            # Clean up frame files
            for frame_path in frames:
                Path(frame_path).unlink(missing_ok=True)

            logger.info(f"Completed analysis of video: {video_path}")

        except Exception as e:
            logger.error(f"Error in video analysis: {e}")

        return result
