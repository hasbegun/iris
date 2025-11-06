"""
Context manager for maintaining conversation sessions.
"""
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from ..config import settings
from ..utils.image_utils import resize_image
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConversationSession:
    """Represents a conversation session with context."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: List[Dict[str, Any]] = []
        self.last_image: Optional[bytes] = None
        self.last_video: Optional[bytes] = None
        self.last_detections: Optional[Dict[str, Any]] = None  # Store detection results
        self.last_accessed = datetime.now()
        self.created_at = datetime.now()

        # Live camera state
        self.live_camera_active: bool = False
        self.live_camera_target: Optional[str] = None
        self.live_camera_last_frame: Optional[bytes] = None
        self.live_camera_detections: Optional[Dict[str, Any]] = None

    def add_message(self, role: str, content: str, image: Optional[bytes] = None, video: Optional[bytes] = None):
        """Add a message to the conversation."""
        # Store message without image/video data for context
        message = {
            "role": role,
            "content": content
        }
        self.messages.append(message)

        # Store the latest image separately with automatic resizing
        if image:
            # Resize image to reduce memory and network usage
            # This will reduce 28.9MB images to ~2-5MB typically
            logger.info(f"Resizing image before storage (original size: {len(image) / (1024*1024):.2f}MB)")
            self.last_image = resize_image(
                image,
                max_dimension=1920,  # Good balance for both Ollama and YOLO
                quality=85
            )

        # Store the latest video separately (no resizing for videos)
        if video:
            logger.info(f"Storing video (size: {len(video) / (1024*1024):.2f}MB)")
            self.last_video = video

        # Keep only recent messages to avoid context overflow
        if len(self.messages) > settings.max_context_messages * 2:  # *2 for user+assistant pairs
            self.messages = self.messages[-(settings.max_context_messages * 2):]

        self.last_accessed = datetime.now()

    def get_context(self) -> List[Dict[str, Any]]:
        """Get conversation context without images."""
        return self.messages.copy()

    def get_last_image(self) -> Optional[bytes]:
        """Get the last analyzed image."""
        return self.last_image

    def get_last_video(self) -> Optional[bytes]:
        """Get the last uploaded video."""
        return self.last_video

    def store_detections(self, detections: List[Dict[str, Any]], image_shape: tuple):
        """Store detection results with image shape."""
        self.last_detections = {
            'detections': detections,
            'image_shape': image_shape
        }
        self.last_accessed = datetime.now()

    def get_detections(self) -> Optional[Dict[str, Any]]:
        """Get the last detection results."""
        return self.last_detections

    def is_expired(self) -> bool:
        """Check if session has expired."""
        expiry_time = datetime.now() - timedelta(seconds=settings.context_ttl_seconds)
        return self.last_accessed < expiry_time


class ContextManager:
    """Manages conversation sessions and context."""

    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    def start_cleanup_task(self):
        """Start background task to clean up expired sessions."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())

    async def _cleanup_expired_sessions(self):
        """Background task to periodically clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                expired_sessions = [
                    session_id
                    for session_id, session in self.sessions.items()
                    if session.is_expired()
                ]
                for session_id in expired_sessions:
                    del self.sessions[session_id]
                    logger.info(f"Cleaned up expired session: {session_id}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    def create_session(self) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = ConversationSession(session_id)
        logger.info(f"Created new session: {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get a session by ID."""
        session = self.sessions.get(session_id)
        if session and not session.is_expired():
            return session
        elif session:
            # Session expired, remove it
            del self.sessions[session_id]
        return None

    def get_or_create_session(self, session_id: Optional[str] = None) -> tuple[str, ConversationSession]:
        """Get existing session or create new one."""
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session_id, session

        # Create new session if not found or expired
        new_session_id = self.create_session()
        return new_session_id, self.sessions[new_session_id]

    def add_interaction(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        image: Optional[bytes] = None,
        video: Optional[bytes] = None
    ):
        """Add a user-assistant interaction to the session."""
        session = self.get_session(session_id)
        if session:
            session.add_message("user", user_message, image=image, video=video)
            session.add_message("assistant", assistant_response)

    def get_context(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation context for a session."""
        session = self.get_session(session_id)
        if session:
            return session.get_context()
        return []

    def get_last_image(self, session_id: str) -> Optional[bytes]:
        """Get the last image from a session."""
        session = self.get_session(session_id)
        if session:
            return session.get_last_image()
        return None

    def get_last_video(self, session_id: str) -> Optional[bytes]:
        """Get the last video from a session."""
        session = self.get_session(session_id)
        if session:
            return session.get_last_video()
        return None

    def store_detections(self, session_id: str, detections: List[Dict[str, Any]], image_shape: tuple):
        """Store detection results for a session."""
        session = self.get_session(session_id)
        if session:
            session.store_detections(detections, image_shape)
            logger.info(f"Stored {len(detections)} detections for session {session_id}")

    def get_detections(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detection results from a session."""
        session = self.get_session(session_id)
        if session:
            return session.get_detections()
        return None


# Singleton instance
context_manager = ContextManager()
