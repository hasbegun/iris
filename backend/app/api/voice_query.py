"""
Voice Query API endpoints for voice-triggered vision analysis.

Handles voice queries with hallucination prevention using YOLO verification.
"""
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
import logging
import time
from typing import Optional

from ..models.schemas import VoiceQueryResponse
from ..services.ollama_service import ollama_service
from ..services.ml_client import ml_client
from ..services.context_manager import context_manager
from ..utils.query_classifier import (
    classify_query,
    extract_objects_from_query,
    verify_object_in_detections,
    should_verify_with_detection
)
from ..utils.voice_query_prompts import create_prompt, create_not_found_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice-query", tags=["voice-query"])


@router.post("/analyze", response_model=VoiceQueryResponse)
async def voice_query_analyze(
    image: UploadFile = File(...),
    query: str = Form(...),
    session_id: Optional[str] = Form(None),
    verify_with_detection: bool = Form(True),
    confidence: float = Form(0.7)
):
    """
    Analyze an image with a voice query and prevent hallucinations.

    This endpoint:
    1. Receives a camera frame and voice query text
    2. Classifies the query type (object, action, safety, etc.)
    3. Optionally runs YOLO detection for verification
    4. Creates specialized prompts to prevent hallucination
    5. Returns natural language response

    **Example voice queries:**
    - "What is this toy?"
    - "What is this person doing?"
    - "Do you see any dangerous object?"
    - "How many cars are there?"
    - "Is there a dog in the image?"

    Args:
        image: Camera frame image
        query: Voice query text (from speech-to-text)
        session_id: Optional session ID for conversation continuity
        verify_with_detection: Whether to use YOLO for verification (default: True)
        confidence: YOLO confidence threshold (default: 0.7)

    Returns:
        Voice query response with natural language answer
    """
    start_time = time.time()

    try:
        # Get or create session
        session_id, session = context_manager.get_or_create_session(session_id)

        # Read image data
        image_data = await image.read()
        logger.info(f"Voice query for session {session_id}: '{query}'")

        # Classify query type
        query_type = classify_query(query)
        logger.info(f"Query classified as: {query_type}")

        # Extract mentioned objects
        mentioned_objects = extract_objects_from_query(query)
        logger.info(f"Mentioned objects: {mentioned_objects}")

        # Determine if we need YOLO verification
        use_detection = verify_with_detection and should_verify_with_detection(query_type)

        detected_objects = []
        detections = []
        detection_response = None

        if use_detection:
            # Run YOLO detection for verification
            logger.info("Running YOLO detection for verification")
            try:
                detection_response = await ml_client.detect_objects(
                    image_bytes=image_data,
                    confidence=confidence,
                    classes=None  # Detect all objects
                )

                if detection_response.get('status') == 'success':
                    detections = detection_response.get('detections', [])
                    # Extract unique class names
                    detected_objects = list(set(
                        det.get('class_name', '') for det in detections
                    ))
                    logger.info(f"Detected {len(detections)} objects: {detected_objects}")

                    # Store detections in session for potential future use
                    image_shape = detection_response.get('image_shape', [0, 0])
                    if detections and image_shape:
                        context_manager.store_detections(
                            session_id=session_id,
                            detections=detections,
                            image_shape=(image_shape[0], image_shape[1])
                        )
                else:
                    logger.warning(f"Detection failed: {detection_response.get('message')}")
                    use_detection = False  # Fall back to no detection

            except Exception as e:
                logger.error(f"Detection error: {e}", exc_info=True)
                use_detection = False  # Fall back to no detection

        # Verify mentioned objects exist in detections
        if use_detection and mentioned_objects:
            all_found, missing_objects = verify_object_in_detections(
                mentioned_objects, detections
            )

            if not all_found:
                # Object not found - return immediate response
                response_text = create_not_found_response(missing_objects)
                logger.info(f"Objects not found: {missing_objects}")

                # Store interaction
                session.add_message("user", query, image=image_data)
                session.add_message("assistant", response_text)

                processing_time = time.time() - start_time

                return VoiceQueryResponse(
                    session_id=session_id,
                    query=query,
                    query_type=query_type,
                    response=response_text,
                    detected_objects=detected_objects,
                    detections_count=len(detections),
                    used_detection_verification=use_detection,
                    processing_time=processing_time
                )

        # Create specialized prompt based on query type
        prompt = create_prompt(
            query=query,
            query_type=query_type,
            detected_objects=detected_objects,
            detections=detections
        )

        if prompt is None:
            # Prompt creation returned None - object not found
            response_text = create_not_found_response(mentioned_objects)
        else:
            # Get conversation context
            context_messages = context_manager.get_context(session_id)

            # Analyze with vision LLM
            logger.info("Sending to vision LLM")
            response_text = await ollama_service.analyze_image(
                image_data=image_data,
                prompt=prompt,
                context_messages=context_messages
            )

            logger.info(f"LLM response: {response_text[:100]}...")

        # Store interaction in context
        session.add_message("user", query, image=image_data)
        session.add_message("assistant", response_text)

        processing_time = time.time() - start_time
        logger.info(f"Voice query completed in {processing_time:.2f}s")

        return VoiceQueryResponse(
            session_id=session_id,
            query=query,
            query_type=query_type,
            response=response_text,
            detected_objects=detected_objects,
            detections_count=len(detections),
            used_detection_verification=use_detection,
            processing_time=processing_time
        )

    except Exception as e:
        logger.error(f"Error in voice query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process voice query: {str(e)}"
        )


@router.get("/health")
async def voice_query_health():
    """
    Check health of voice query service.

    Returns:
        Health status with dependencies
    """
    try:
        # Check ML service
        ml_health = await ml_client.health_check()

        # Check Ollama
        ollama_ok, models = await ollama_service.check_health()

        return {
            "status": "healthy" if (ml_health.get("status") == "healthy" and ollama_ok) else "degraded",
            "ml_service": ml_health,
            "ollama": {
                "connected": ollama_ok,
                "vision_model": ollama_service.vision_model,
                "available": ollama_service.vision_model in models if models else False
            }
        }

    except Exception as e:
        logger.error(f"Voice query health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
