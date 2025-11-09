"""
LangChain Tools for Vision Analysis and YOLO Object Detection
Tools that the LLM agent can use to analyze images and detect objects
"""
from langchain_core.tools import tool
from typing import Optional
import logging

from app.services.ml_client import ml_client
from app.services.context_manager import context_manager
from app.services.ollama_service import ollama_service
from app.services.search_service import search_service
from app.config import settings

logger = logging.getLogger(__name__)


@tool
async def vision_analysis(
    session_id: str,
    prompt: str = "Describe what you see in this image in detail."
) -> dict:
    """
    Analyze an image using the vision model (llava) to get a general understanding.

    Use this tool when the user asks:
    - General questions about the image ("What's in this image?", "Describe this photo")
    - To understand the overall scene before detecting specific objects
    - Questions about context, setting, or overall composition

    Args:
        session_id: The session ID to get the current image from
        prompt: The question or instruction for the vision model

    Returns:
        Dictionary with vision model's analysis

    Examples of when to use:
        - "What's in this image?" -> vision_analysis(session_id, "Describe what you see")
        - "Tell me about this photo" -> vision_analysis(session_id, "Describe this photo in detail")
        - "What's happening here?" -> vision_analysis(session_id, "What's happening in this image?")
    """
    try:
        # Get current image from session
        image_bytes = context_manager.get_last_image(session_id)

        if not image_bytes:
            return {
                "status": "error",
                "message": "No image found in this session. Please upload an image first."
            }

        # Get conversation context for better responses
        context_messages = context_manager.get_context(session_id)

        # Call vision model
        analysis = await ollama_service.analyze_image(
            image_data=image_bytes,
            prompt=prompt,
            context_messages=context_messages
        )

        return {
            "status": "success",
            "analysis": analysis,
            "model_used": ollama_service.vision_model
        }

    except Exception as e:
        logger.error(f"Vision analysis tool error: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Vision analysis failed: {str(e)}"
        }


@tool
async def detect_objects(
    session_id: str,
    object_types: Optional[str] = None,
    confidence: Optional[float] = None
) -> dict:
    """
    Detect specific objects in an image using YOLO object detection.

    Use this tool when the user asks to:
    - Find, detect, or locate objects
    - Count specific objects (e.g., "how many cars")
    - Identify objects in an image

    Args:
        session_id: The session ID to get the current image from
        object_types: Comma-separated object types to detect (e.g., "car,person,dog").
                     Leave empty to detect all objects. Common objects include:
                     car, truck, bus, motorcycle, bicycle, person, cat, dog, bird,
                     chair, couch, bed, table, laptop, tv, phone, piano, etc.
        confidence: Detection confidence threshold (0.0-1.0). Default is 0.7.
                   Use lower values (0.5-0.6) for harder-to-detect objects.

    Returns:
        Dictionary with detected objects, counts, and bounding boxes

    Examples of when to use:
        - "find cars in this image" -> detect_objects(session_id, object_types="car")
        - "how many people are there" -> detect_objects(session_id, object_types="person")
        - "detect all animals" -> detect_objects(session_id, object_types="cat,dog,bird,horse")
        - "what objects do you see" -> detect_objects(session_id)
        - "find my laptop" -> detect_objects(session_id, object_types="laptop")
    """
    try:
        # Get current image from session
        image_bytes = context_manager.get_last_image(session_id)

        if not image_bytes:
            return {
                "status": "error",
                "message": "No image found in this session. Please upload an image first."
            }

        # Parse object types
        classes = None
        if object_types:
            classes = [c.strip() for c in object_types.split(",")]

        # Use default confidence if not specified
        conf = confidence if confidence is not None else settings.yolo_default_confidence

        # Call ML service
        result = await ml_client.detect_objects(
            image_bytes=image_bytes,
            confidence=conf,
            classes=classes
        )

        # Format response for LLM
        if result.get('status') == 'error':
            return result

        # Create human-readable summary
        detections = result.get('detections', [])
        count = result.get('count', 0)

        if count == 0:
            summary = f"No objects detected"
            if object_types:
                summary += f" of type(s): {object_types}"
        else:
            # Group by class
            class_counts = {}
            for det in detections:
                class_name = det['class_name']
                class_counts[class_name] = class_counts.get(class_name, 0) + 1

            summary_parts = [f"{count} {class_name}(s)" for class_name, count in class_counts.items()]
            summary = f"Found: {', '.join(summary_parts)}"

        return {
            "status": "success",
            "detections": detections,
            "total_count": count,
            "summary": summary,
            "inference_time_ms": result.get('inference_time_ms')
        }

    except Exception as e:
        logger.error(f"Object detection tool error: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Detection failed: {str(e)}"
        }


@tool
async def segment_image(
    session_id: str,
    confidence: Optional[float] = None
) -> dict:
    """
    Perform instance segmentation on an image to get precise object boundaries.

    Use this tool when the user asks to:
    - Segment or separate objects
    - Get precise boundaries or outlines
    - Distinguish individual objects
    - Get detailed object shapes

    Args:
        session_id: The session ID to get the current image from
        confidence: Segmentation confidence threshold (0.0-1.0). Default is 0.7.

    Returns:
        Dictionary with segmentation masks and object boundaries

    Examples of when to use:
        - "segment all objects" -> segment_image(session_id)
        - "separate the objects in this image" -> segment_image(session_id)
        - "show me object boundaries" -> segment_image(session_id)
        - "get precise outlines of objects" -> segment_image(session_id)
    """
    try:
        # Get current image from session
        image_bytes = context_manager.get_last_image(session_id)

        if not image_bytes:
            return {
                "status": "error",
                "message": "No image found in this session. Please upload an image first."
            }

        # Use default confidence if not specified
        conf = confidence if confidence is not None else settings.yolo_default_confidence

        # Call ML service
        result = await ml_client.segment_objects(
            image_bytes=image_bytes,
            confidence=conf
        )

        # Format response for LLM
        if result.get('status') == 'error':
            return result

        # Create human-readable summary
        segments = result.get('segments', [])
        count = result.get('count', 0)

        if count == 0:
            summary = "No objects segmented"
        else:
            # Group by class
            class_counts = {}
            for seg in segments:
                class_name = seg['class_name']
                class_counts[class_name] = class_counts.get(class_name, 0) + 1

            summary_parts = [f"{count} {class_name}(s)" for class_name, count in class_counts.items()]
            summary = f"Segmented: {', '.join(summary_parts)}"

        return {
            "status": "success",
            "segments": segments,
            "total_count": count,
            "summary": summary,
            "inference_time_ms": result.get('inference_time_ms')
        }

    except Exception as e:
        logger.error(f"Segmentation tool error: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Segmentation failed: {str(e)}"
        }


@tool
async def detect_faces(
    session_id: str,
    confidence: Optional[float] = None
) -> dict:
    """
    Detect human faces or people in an image.

    Use this tool when the user asks about:
    - People or humans in an IMAGE
    - Faces in an IMAGE
    - How many people are present in an IMAGE
    - Human detection in an IMAGE

    Args:
        session_id: The session ID to get the current image from
        confidence: Detection confidence threshold (0.0-1.0). Default is 0.7.

    Returns:
        Dictionary with face locations and counts

    Examples of when to use:
        - "how many people are in this photo" -> detect_faces(session_id)
        - "find faces" -> detect_faces(session_id)
        - "detect humans" -> detect_faces(session_id)
        - "are there any people here" -> detect_faces(session_id)
        - "count the people" -> detect_faces(session_id)
    """
    try:
        # Get current image from session
        image_bytes = context_manager.get_last_image(session_id)

        if not image_bytes:
            return {
                "status": "error",
                "message": "No image found in this session. Please upload an image first."
            }

        # Use default confidence if not specified
        conf = confidence if confidence is not None else settings.yolo_default_confidence

        # Call ML service
        result = await ml_client.detect_faces(
            image_bytes=image_bytes,
            confidence=conf
        )

        # Format response for LLM
        if result.get('status') == 'error':
            return result

        # Create human-readable summary
        faces = result.get('faces', [])
        count = result.get('count', 0)

        if count == 0:
            summary = "No people/faces detected in the image"
        elif count == 1:
            summary = "Detected 1 person in the image"
        else:
            summary = f"Detected {count} people in the image"

        return {
            "status": "success",
            "faces": faces,
            "total_count": count,
            "summary": summary,
            "inference_time_ms": result.get('inference_time_ms')
        }

    except Exception as e:
        logger.error(f"Face detection tool error: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Face detection failed: {str(e)}"
        }


@tool
async def detect_objects_in_video(
    session_id: str,
    object_types: Optional[str] = None,
    confidence: Optional[float] = None
) -> dict:
    """
    Detect objects in a VIDEO using YOLO. This analyzes video frame-by-frame.

    Use this tool when the user asks to find objects in a VIDEO, not an image.

    Args:
        session_id: The session ID to get the current video from
        object_types: Comma-separated object types to detect (e.g., "car,person,dog").
                     Leave empty to detect all objects. Common objects include:
                     car, truck, bus, motorcycle, bicycle, person, cat, dog, bird,
                     chair, couch, bed, table, laptop, tv, phone, etc.
        confidence: Detection confidence threshold (0.0-1.0). Default is 0.5.

    Returns:
        Dictionary with detected objects across video frames, counts, and summary

    Examples of when to use:
        - "find dogs in this video" -> detect_objects_in_video(session_id, object_types="dog")
        - "how many cars are in the video" -> detect_objects_in_video(session_id, object_types="car")
        - "detect people in this video" -> detect_objects_in_video(session_id, object_types="person")
        - "what objects are in the video" -> detect_objects_in_video(session_id)
    """
    try:
        # Get current video from session
        video_bytes = context_manager.get_last_video(session_id)

        if not video_bytes:
            return {
                "status": "error",
                "message": "No video found in this session. Please upload a video first."
            }

        # Parse object types
        classes = None
        if object_types:
            classes = [c.strip() for c in object_types.split(",")]

        # Use default confidence if not specified
        conf = confidence if confidence is not None else 0.5

        # Call ML service for video detection
        result = await ml_client.detect_objects_in_video(
            video_bytes=video_bytes,
            confidence=conf,
            classes=classes,
            frame_skip=2  # Skip frames for faster processing
        )

        # Format response for LLM
        if result.get('status') == 'error':
            return result

        # Create human-readable summary
        summary = result.get('summary', {})
        total_detections = summary.get('total_detections', 0)
        detections_by_class = summary.get('detections_by_class', {})
        frames_with_detections = summary.get('frames_with_detections', 0)

        video_info = result.get('video_info', {})
        total_frames = video_info.get('total_frames', 0)
        duration = video_info.get('duration_seconds', 0)

        if total_detections == 0:
            summary_text = f"No objects detected in the video"
            if object_types:
                summary_text += f" of type(s): {object_types}"
        else:
            class_summary = ', '.join([f"{count} {name}(s)" for name, count in detections_by_class.items()])
            summary_text = f"Found {total_detections} objects in video ({duration:.1f}s, {total_frames} frames): {class_summary}. Objects appeared in {frames_with_detections} frames."

        return {
            "status": "success",
            "total_detections": total_detections,
            "detections_by_class": detections_by_class,
            "frames_with_detections": frames_with_detections,
            "video_duration": duration,
            "total_frames": total_frames,
            "summary": summary_text,
            "processing_time": result.get('processing_time_seconds')
        }

    except Exception as e:
        logger.error(f"Video detection tool error: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Video detection failed: {str(e)}"
        }


@tool
async def web_search(query: str) -> str:
    """
    Search the web for current information using SearXNG.

    Use this tool when you need to:
    - Find current/real-time information (stock prices, news, weather)
    - Look up facts, definitions, or explanations
    - Get information about detected objects (e.g., after detecting a "car", search "what is a car used for")
    - Answer questions that require up-to-date knowledge

    IMPORTANT: This tool should be used AFTER using vision tools if the user is asking
    about objects in an image. For example:
    - If user asks "what's in this image?", use detect_objects or vision_analysis
    - If user then asks "what does it do?", construct query from detected objects
      and search (e.g., if cars were detected, search "what are cars used for")

    Args:
        query: The search query (be specific and clear)

    Returns:
        Formatted string with search results

    Examples of when to use:
        - "what is nvidia stock price today" -> web_search("nvidia stock price")
        - After detecting "car": "what does it do?" -> web_search("what is a car used for")
        - "latest news about AI" -> web_search("latest AI news")
        - After detecting "bottle": "what's it for?" -> web_search("water bottle uses")
    """
    try:
        logger.info(f"Web search tool called with query: '{query}'")

        # Perform search
        search_result = await search_service.search(
            query=query,
            max_results=settings.searxng_max_results
        )

        # Format results for the agent
        if search_result.total_results == 0:
            return f"No search results found for query: '{query}'"

        # Build formatted response
        response_parts = [f"Search results for '{query}':\n"]

        for i, result in enumerate(search_result.results, 1):
            response_parts.append(f"\n{i}. {result.title}")
            response_parts.append(f"   URL: {result.url}")
            response_parts.append(f"   {result.content}\n")

        formatted_response = "\n".join(response_parts)
        logger.info(f"Web search returned {search_result.total_results} results")

        return formatted_response

    except Exception as e:
        logger.error(f"Web search tool error: {e}", exc_info=True)
        error_msg = f"Web search failed: {str(e)}"
        return error_msg


# List of all tools for easy import
VISION_TOOLS = [
    vision_analysis,
    detect_objects,
    segment_image,
    detect_faces,
    detect_objects_in_video
]

# Web search tool
SEARCH_TOOLS = [
    web_search
]

# All tools combined
ALL_TOOLS = VISION_TOOLS + SEARCH_TOOLS

# Alias for backward compatibility
YOLO_TOOLS = VISION_TOOLS


def get_all_tools():
    """
    Returns a list of all defined tools for the agent.
    Includes both vision and search tools.
    """
    return ALL_TOOLS
