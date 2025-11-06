"""
Ollama service for interacting with local Ollama models.

Uses OpenAI-compatible API endpoints where possible for portability.
Ollama-specific features are clearly marked.
"""
import aiohttp
import base64
import logging
from typing import Optional, List, Dict, Any
from ..config import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """
    Service for interacting with Ollama API.

    Uses OpenAI-compatible endpoints (/v1/chat/completions) where possible.
    Falls back to Ollama-specific endpoints when needed (marked as OLLAMA_ONLY).
    """

    def __init__(self):
        self.base_url = settings.ollama_host
        self.vision_model = settings.vision_model
        self.chat_model = settings.chat_model

        # OpenAI-compatible endpoint
        self.openai_endpoint = f"{self.base_url}/v1/chat/completions"

        # OLLAMA_ONLY: Native Ollama endpoints
        self.ollama_chat_endpoint = f"{self.base_url}/api/chat"
        self.ollama_tags_endpoint = f"{self.base_url}/api/tags"

    async def check_health(self) -> tuple[bool, List[str]]:
        """
        Check if Ollama is running and list available models.

        OLLAMA_ONLY: Uses /api/tags endpoint.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.ollama_tags_endpoint) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model["name"] for model in data.get("models", [])]
                        return True, models
                    return False, []
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False, []

    async def verify_model_available(self, model_name: str) -> bool:
        """
        Verify a model is available and compatible.

        OLLAMA_ONLY: Uses /api/tags endpoint.
        """
        connected, models = await self.check_health()
        if not connected:
            return False
        return model_name in models

    async def analyze_image(
        self,
        image_data: bytes,
        prompt: str,
        context_messages: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Analyze an image with a vision model.

        OLLAMA_ONLY: Uses /api/chat with images field (not in OpenAI spec).
        The images field with base64 data is Ollama-specific.

        Args:
            image_data: Image bytes
            prompt: User's question or instruction
            context_messages: Previous conversation context

        Returns:
            Model's response
        """
        try:
            # Verify model is available
            if not await self.verify_model_available(self.vision_model):
                raise Exception(
                    f"Vision model '{self.vision_model}' not available. "
                    f"Please run: ollama pull {self.vision_model}"
                )

            # Encode image to base64
            image_b64 = base64.b64encode(image_data).decode("utf-8")

            # Build messages (OpenAI-compatible format)
            messages = []

            # Add context if available
            if context_messages:
                # Filter out any images from context to avoid memory issues
                for msg in context_messages:
                    if "images" not in msg:
                        messages.append(msg)

            # OLLAMA_ONLY: Add current vision query with images field
            # This format is Ollama-specific, not part of OpenAI API
            messages.append({
                "role": "user",
                "content": prompt,
                "images": [image_b64]  # OLLAMA_ONLY
            })

            payload = {
                "model": self.vision_model,
                "messages": messages,
                "stream": False
            }

            logger.info(f"Sending vision request to model: {self.vision_model}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.ollama_chat_endpoint,  # OLLAMA_ONLY endpoint
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data.get("message", {}).get("content", "")
                        if not content:
                            logger.warning("Empty response from vision model")
                            return "No response generated"
                        return content
                    else:
                        error_text = await response.text()
                        logger.error(f"Ollama API error {response.status}: {error_text}")

                        # Provide helpful error messages
                        if "no longer compatible" in error_text.lower():
                            raise Exception(
                                f"Model '{self.vision_model}' is incompatible. "
                                f"Run: ollama pull {self.vision_model}"
                            )
                        raise Exception(f"Ollama API error: {response.status} - {error_text}")

        except Exception as e:
            logger.error(f"Failed to analyze image: {e}")
            raise

    async def chat(
        self,
        message: str,
        context_messages: List[Dict[str, Any]]
    ) -> str:
        """
        Continue conversation with text-only chat.

        Uses OpenAI-compatible endpoint when possible.

        Args:
            message: User's message
            context_messages: Previous conversation context

        Returns:
            Model's response
        """
        try:
            # Verify model is available
            if not await self.verify_model_available(self.chat_model):
                raise Exception(
                    f"Chat model '{self.chat_model}' not available. "
                    f"Please run: ollama pull {self.chat_model}"
                )

            # Build messages with context (OpenAI-compatible format)
            messages = context_messages.copy()
            messages.append({
                "role": "user",
                "content": message
            })

            # Use OpenAI-compatible payload
            payload = {
                "model": self.chat_model,
                "messages": messages,
                "stream": False
            }

            logger.info(f"Sending chat request to model: {self.chat_model}")

            # Try OpenAI-compatible endpoint first
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.openai_endpoint,  # OpenAI-compatible
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # OpenAI-compatible response format
                        choices = data.get("choices", [])
                        if choices:
                            content = choices[0].get("message", {}).get("content", "")
                            if content:
                                return content

                        # Fallback: try Ollama format
                        content = data.get("message", {}).get("content", "")
                        if content:
                            return content

                        logger.warning("Empty response from chat model")
                        return "No response generated"
                    else:
                        error_text = await response.text()
                        logger.error(f"Chat API error {response.status}: {error_text}")

                        # Provide helpful error messages
                        if "no longer compatible" in error_text.lower():
                            raise Exception(
                                f"Model '{self.chat_model}' is incompatible. "
                                f"Run: ollama pull {self.chat_model}"
                            )
                        raise Exception(f"Chat API error: {response.status} - {error_text}")

        except Exception as e:
            logger.error(f"Failed to chat: {e}")
            raise

    async def warmup_models(self) -> None:
        """
        Warm up models by running a simple inference on each.
        This loads models into memory for faster first real request.
        """
        logger.info("Warming up models...")

        try:
            # Warm up vision model
            if await self.verify_model_available(self.vision_model):
                logger.info(f"Warming up vision model: {self.vision_model}")

                # Create a 1x1 pixel image (minimal data)
                dummy_image = base64.b64decode(
                    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
                )

                payload = {
                    "model": self.vision_model,
                    "messages": [{
                        "role": "user",
                        "content": "warmup",
                        "images": [base64.b64encode(dummy_image).decode("utf-8")]
                    }],
                    "stream": False
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.ollama_chat_endpoint,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        if response.status == 200:
                            logger.info(f"✓ Vision model warmed up")
                        else:
                            logger.warning(f"Vision model warmup failed: {response.status}")

            # Warm up chat model
            if await self.verify_model_available(self.chat_model):
                logger.info(f"Warming up chat model: {self.chat_model}")

                payload = {
                    "model": self.chat_model,
                    "messages": [{"role": "user", "content": "hi"}],
                    "stream": False
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.openai_endpoint,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            logger.info(f"✓ Chat model warmed up")
                        else:
                            logger.warning(f"Chat model warmup failed: {response.status}")

            logger.info("Model warmup complete")

        except Exception as e:
            logger.warning(f"Model warmup failed (non-critical): {e}")


# Singleton instance
ollama_service = OllamaService()
