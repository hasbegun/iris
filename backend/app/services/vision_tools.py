"""
Vision Tools Factory for ReAct Agent
Creates tools with session_id pre-bound for simpler LLM interactions
"""
from langchain_core.tools import tool
from typing import Optional, List
from functools import partial
import logging

from app.services.ml_client import ml_client
from app.services.context_manager import context_manager
from app.services.ollama_service import ollama_service
from app.config import settings

logger = logging.getLogger(__name__)


def create_vision_tools(session_id: str) -> List:
    """
    Create vision analysis and YOLO detection tools with session_id pre-bound.

    This factory pattern allows the LLM to call tools with simple, single-parameter
    inputs that work better with the ReAct parser.

    Args:
        session_id: The session ID to bind to all tools

    Returns:
        List of tools ready for agent use
    """

    @tool
    async def analyze_image(question: str = "Describe what you see in this image") -> str:
        """
        Analyze the image using vision model to understand the general content.

        ALWAYS USE THIS FIRST for general questions like:
        - "What do you see?"
        - "What's in this image?"
        - "Describe this photo"
        - "Tell me about this image"
        - Any question asking for general description or understanding

        DO NOT use find_objects for general questions - only for specific object detection.

        Args:
            question: What to ask about the image

        Returns:
            Description of the image
        """
        try:
            image_bytes = context_manager.get_last_image(session_id)
            if not image_bytes:
                return "Error: No image found. Please upload an image first."

            context_messages = context_manager.get_context(session_id)
            analysis = await ollama_service.analyze_image(
                image_data=image_bytes,
                prompt=question,
                context_messages=context_messages
            )

            return analysis

        except Exception as e:
            logger.error(f"Vision analysis error: {e}", exc_info=True)
            return f"Error analyzing image: {str(e)}"


    @tool
    async def find_objects(objects: str = "") -> str:
        """
        Find and count SPECIFIC objects in an IMAGE (not video) using YOLO detection.

        IMPORTANT: This tool is for IMAGES ONLY. If a video is loaded, use find_objects_in_video instead.

        Use this when the user asks to find, detect, or count objects in an IMAGE:
        - "Find all cars"
        - "How many cars are there?"
        - "Detect pianos"
        - "Are there any dogs or cats?"
        - "Count the trucks"

        DO NOT use for:
        - General questions like "what do you see?" - use analyze_image instead
        - Video analysis - use find_objects_in_video instead

        Args:
            objects: Comma-separated list of objects to find (e.g., "car,truck,bus").
                    Leave empty to find all objects.
                    YOLO can detect: person, car, truck, bus, bicycle, motorcycle, airplane,
                    train, boat, dog, cat, horse, cow, sheep, bird, chair, couch, table,
                    laptop, tv, keyboard, phone, book, and 60+ other common objects.

        Returns:
            Summary of detected objects with counts
        """
        try:
            # Check if there's a video instead of an image
            video_bytes = context_manager.get_last_video(session_id)
            if video_bytes:
                # Guide agent to use the correct tool
                return "A video is loaded, not an image. Use the find_objects_in_video tool to analyze videos."

            image_bytes = context_manager.get_last_image(session_id)
            if not image_bytes:
                return "Error: No image found. Please upload an image first."

            # Let YOLO detect all objects naturally (no class filtering)
            # We'll filter results afterward if user requested specific objects
            result = await ml_client.detect_objects(
                image_bytes=image_bytes,
                confidence=0.7,
                classes=None  # Always detect all classes - let YOLO do what it's good at
            )

            if result.get('status') == 'error':
                return f"Error: {result.get('message', 'Detection failed')}"

            detections = result.get('detections', [])

            # Store raw detection results in session for frontend use
            image_shape = result.get('image_shape', [0, 0])
            if detections and image_shape:
                context_manager.store_detections(
                    session_id=session_id,
                    detections=detections,
                    image_shape=(image_shape[0], image_shape[1])  # (height, width)
                )

            # Filter results if user requested specific objects
            if objects:
                # Clean up requested object names
                requested = []
                for obj in objects.split(","):
                    # Remove quotes, extra spaces, and normalize
                    cleaned = obj.strip().strip('"').strip("'").strip().lower()
                    if cleaned:
                        requested.append(cleaned)

                # Filter detections to only requested objects
                filtered = []
                for det in detections:
                    class_name_lower = det['class_name'].lower()
                    # Check if detection matches any requested object
                    if any(req in class_name_lower or class_name_lower in req for req in requested):
                        filtered.append(det)

                detections = filtered

            count = len(detections)

            if count == 0:
                if objects:
                    return f"No {objects} found in the image."
                else:
                    return "No objects detected in the image."

            # Group by class and create summary
            class_counts = {}
            for det in detections:
                class_name = det['class_name']
                class_counts[class_name] = class_counts.get(class_name, 0) + 1

            # Build response
            if len(class_counts) == 1:
                obj_name = list(class_counts.keys())[0]
                cnt = class_counts[obj_name]
                return f"Found {cnt} {obj_name}{'s' if cnt > 1 else ''} in the image."
            else:
                parts = [f"{cnt} {name}(s)" for name, cnt in class_counts.items()]
                return f"Found: {', '.join(parts)}. Total: {count} objects."

        except Exception as e:
            logger.error(f"Object detection error: {e}", exc_info=True)
            return f"Error detecting objects: {str(e)}"


    @tool
    async def count_people() -> str:
        """
        Count how many people are in an IMAGE (not video).

        IMPORTANT: This tool is for IMAGES ONLY. For videos, use find_objects_in_video with objects="person".

        Use this when the user asks about people in an IMAGE:
        - "How many people are there?"
        - "Count the people"
        - "Are there any humans?"

        Returns:
            Number of people detected
        """
        try:
            # Check if there's a video instead of an image
            video_bytes = context_manager.get_last_video(session_id)
            if video_bytes:
                return "Error: A video is currently loaded. Please use find_objects_in_video tool with objects='person' for video analysis."

            image_bytes = context_manager.get_last_image(session_id)
            if not image_bytes:
                return "Error: No image found. Please upload an image first."

            result = await ml_client.detect_faces(
                image_bytes=image_bytes,
                confidence=0.7
            )

            if result.get('status') == 'error':
                return f"Error: {result.get('message', 'Detection failed')}"

            count = result.get('count', 0)
            detections = result.get('detections', [])

            # Store raw detection results in session for frontend use
            image_shape = result.get('image_shape', [0, 0])
            if detections and image_shape:
                context_manager.store_detections(
                    session_id=session_id,
                    detections=detections,
                    image_shape=(image_shape[0], image_shape[1])  # (height, width)
                )

            if count == 0:
                return "No people detected in the image."
            elif count == 1:
                return "There is 1 person in the image."
            else:
                return f"There are {count} people in the image."

        except Exception as e:
            logger.error(f"Face detection error: {e}", exc_info=True)
            return f"Error detecting people: {str(e)}"


    @tool
    async def segment_objects() -> str:
        """
        Get precise boundaries and shapes of all objects in an IMAGE (not video).

        IMPORTANT: This tool is for IMAGES ONLY. Segmentation is not available for videos.

        Use this when the user asks for segmentation in an IMAGE:
        - "Segment the image"
        - "Show object boundaries"
        - "Get precise outlines"

        Returns:
            Summary of segmented objects
        """
        try:
            # Check if there's a video instead of an image
            video_bytes = context_manager.get_last_video(session_id)
            if video_bytes:
                return "Error: A video is currently loaded. Segmentation is only available for images. Please upload an image for segmentation."

            image_bytes = context_manager.get_last_image(session_id)
            if not image_bytes:
                return "Error: No image found. Please upload an image first."

            result = await ml_client.segment_objects(
                image_bytes=image_bytes,
                confidence=0.7
            )

            if result.get('status') == 'error':
                return f"Error: {result.get('message', 'Segmentation failed')}"

            segments = result.get('segments', [])
            count = result.get('count', 0)

            # Store segmentation results in session for frontend use (segments have bbox too)
            image_shape = result.get('image_shape', [0, 0])
            if segments and image_shape:
                context_manager.store_detections(
                    session_id=session_id,
                    detections=segments,  # Segments also have bbox data
                    image_shape=(image_shape[0], image_shape[1])  # (height, width)
                )

            if count == 0:
                return "No objects segmented."

            # Group by class
            class_counts = {}
            for seg in segments:
                class_name = seg['class_name']
                class_counts[class_name] = class_counts.get(class_name, 0) + 1

            parts = [f"{cnt} {name}(s)" for name, cnt in class_counts.items()]
            return f"Segmented {count} objects: {', '.join(parts)}"

        except Exception as e:
            logger.error(f"Segmentation error: {e}", exc_info=True)
            return f"Error segmenting objects: {str(e)}"


    @tool
    async def find_objects_in_video(objects: str = "") -> str:
        """
        Find and count SPECIFIC objects in a VIDEO using YOLO frame-by-frame detection.

        ONLY use this when the user asks about objects in a VIDEO, such as:
        - "Find dogs in this video"
        - "How many cars are in the video?"
        - "Detect people in this video"
        - "Count bikes in the video"

        DO NOT use for images - use find_objects instead.
        DO NOT use for general video questions - this is specifically for object detection.

        Args:
            objects: Comma-separated list of objects to find (e.g., "car,truck,bus").
                    Leave empty to find all objects in the video.
                    YOLO can detect: person, car, truck, bus, bicycle, motorcycle, airplane,
                    train, boat, dog, cat, horse, cow, sheep, bird, chair, couch, table,
                    laptop, tv, keyboard, phone, book, and 60+ other common objects.

        Returns:
            Summary of detected objects in the video with total counts across multiple frames
        """
        try:
            video_bytes = context_manager.get_last_video(session_id)
            if not video_bytes:
                return "Error: No video found. Please upload a video first."

            # Parse object classes if provided
            classes = None
            if objects:
                classes = [obj.strip() for obj in objects.split(",")]

            # Call ML service to extract multiple frames and detect objects
            # Returns slideshow-ready data with multiple frames
            result = await ml_client.detect_video_frames(
                video_bytes=video_bytes,
                confidence=0.7,
                classes=classes,
                frame_interval=2.0,  # Extract frame every 2 seconds
                max_frames=10        # Maximum 10 frames
            )

            if result.get('status') == 'error':
                return f"Error: {result.get('message', 'Video detection failed')}"

            frames = result.get('frames', [])
            if not frames:
                return "Error: Failed to extract frames from video."

            # Store all frames in session with frame indices
            import base64
            session = context_manager.get_session(session_id)

            # Store frames data for frontend slideshow
            video_frames_data = []

            for idx, frame_data in enumerate(frames):
                frame_base64 = frame_data.get('frame_base64', '')
                if frame_base64:
                    frame_bytes = base64.b64decode(frame_base64)

                    # Store frame with index
                    if not hasattr(session, 'video_frames'):
                        session.video_frames = {}
                    session.video_frames[idx] = frame_bytes

                    # Store detections for this frame
                    detections = frame_data.get('detections', [])
                    image_shape = frame_data.get('image_shape', [0, 0])

                    video_frames_data.append({
                        'frame_index': idx,
                        'timestamp': frame_data.get('timestamp', 0),
                        'detections': detections,
                        'image_shape': image_shape,
                        'count': frame_data.get('count', 0)
                    })

            # Store video frames metadata in session
            session.video_frames_metadata = {
                'frames_count': len(frames),
                'frames': video_frames_data,
                'total_detections': result.get('total_detections', 0),
                'video_duration': result.get('video_duration', 0)
            }

            logger.debug(f"[find_objects_in_video] Stored {len(frames)} video frames with detections for slideshow")
            logger.debug(f"[find_objects_in_video] Session {session_id} now has video_frames_metadata: {hasattr(session, 'video_frames_metadata')}")
            logger.debug(f"[find_objects_in_video] Metadata: {session.video_frames_metadata}")

            # Aggregate all detections across all frames
            all_detections = []
            for frame_data in frames:
                all_detections.extend(frame_data.get('detections', []))

            # Count total detections by class
            class_counts = {}
            for det in all_detections:
                class_name = det['class_name']
                class_counts[class_name] = class_counts.get(class_name, 0) + 1

            total_detections = len(all_detections)
            frames_analyzed = result.get('frames_analyzed', 0)
            video_duration = result.get('video_duration', 0)

            if total_detections == 0:
                if objects:
                    return f"No {objects} found in the video (analyzed {frames_analyzed} frames over {video_duration}s)."
                else:
                    return f"No objects detected in the video (analyzed {frames_analyzed} frames over {video_duration}s)."

            # Build response with summary across all frames
            if len(class_counts) == 1:
                obj_name = list(class_counts.keys())[0]
                cnt = class_counts[obj_name]
                return f"Found {cnt} {obj_name}{'s' if cnt > 1 else ''} across {frames_analyzed} frames in the video ({video_duration}s duration)."
            else:
                parts = [f"{cnt} {name}(s)" for name, cnt in class_counts.items()]
                return f"Found across {frames_analyzed} frames: {', '.join(parts)}. Total: {total_detections} detections in {video_duration}s video."

        except Exception as e:
            logger.error(f"Video detection error: {e}", exc_info=True)
            return f"Error detecting objects in video: {str(e)}"


    @tool
    async def analyze_live_camera(command: str, objects: str = "") -> str:
        """
        Manage live camera detection with voice commands.

        IMPORTANT: Use this tool when the user explicitly mentions "live camera" or uses voice commands
        like "find [object]" in a live camera context.

        DO NOT use this for static images or videos - use analyze_image or find_objects instead.

        Supported commands:
        - "start find [objects]" or "find [objects]": Start live detection for specific objects
        - "stop": Stop live detection
        - "pause": Pause live detection
        - "resume": Resume live detection
        - "status": Get current live camera status

        Args:
            command: The command to execute (start/stop/pause/resume/status)
            objects: Comma-separated list of objects to find (required for 'start'/'find' commands)

        Returns:
            Status message about the live camera operation
        """
        try:
            session = context_manager.get_session(session_id)
            if not session:
                return "Error: Session not found. Please start a new session."

            cmd_lower = command.lower().strip()

            # Handle "start" or "find" command
            if "start" in cmd_lower or "find" in cmd_lower:
                if not objects:
                    return "Error: Please specify which objects to find. For example: 'find car' or 'find person,dog'"

                session.live_camera_active = True
                session.live_camera_target = objects
                logger.info(f"[LiveCamera] Started detection for: {objects}")

                return f"Live camera detection started. Looking for: {objects}. The camera will continuously detect these objects in real-time."

            # Handle "stop" command
            elif "stop" in cmd_lower:
                if not session.live_camera_active:
                    return "Live camera is not currently active."

                session.live_camera_active = False
                target = session.live_camera_target
                session.live_camera_target = None
                session.live_camera_last_frame = None
                session.live_camera_detections = None
                logger.info(f"[LiveCamera] Stopped detection")

                return f"Live camera detection stopped. Was looking for: {target}."

            # Handle "pause" command
            elif "pause" in cmd_lower:
                if not session.live_camera_active:
                    return "Live camera is not currently active."

                # TODO: Implement pause logic (might need additional state)
                return "Live camera detection paused. Say 'resume' to continue."

            # Handle "resume" command
            elif "resume" in cmd_lower or "continue" in cmd_lower:
                if not session.live_camera_active:
                    return "Live camera was not active. Use 'start find [object]' to begin detection."

                return f"Live camera detection resumed. Looking for: {session.live_camera_target}."

            # Handle "status" command
            elif "status" in cmd_lower:
                if session.live_camera_active:
                    return f"Live camera is active. Currently detecting: {session.live_camera_target}."
                else:
                    return "Live camera is not currently active. Say 'find [object]' to start detection."

            else:
                return f"Unknown command: {command}. Supported commands: start, stop, pause, resume, status."

        except Exception as e:
            logger.error(f"Live camera error: {e}", exc_info=True)
            return f"Error managing live camera: {str(e)}"


    # Return all tools
    return [analyze_image, find_objects, count_people, segment_objects, find_objects_in_video, analyze_live_camera]
