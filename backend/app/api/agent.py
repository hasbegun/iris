"""
Agent API endpoints for intelligent image analysis with YOLO.
Uses LangChain agent to automatically select appropriate detection tools.
"""
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
import logging
import uuid
import requests
from pathlib import Path
import time
from typing import Optional

from ..models.schemas import (
    AgentQueryRequest,
    AgentQueryResponse,
    AgentAnalyzeResponse,
    DetectionRequest,
    DetectionResponse
)
from ..services.agent_service import vision_agent
from ..services.context_manager import context_manager
from ..services.ml_client import ml_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/analyze", response_model=AgentAnalyzeResponse)
async def agent_analyze(
    image: UploadFile = File(...),
    prompt: str = Form(...),
    session_id: Optional[str] = Form(None),
):
    """
    Unified endpoint: Upload image and analyze with natural language prompt in one request.

    This combines image upload and agent analysis into a single request, similar to /api/vision/analyze
    but using the intelligent agent that can automatically detect objects when needed.

    **Example prompts:**
    - "What's in this image?"
    - "How many cars are in this image?"
    - "Find all the people"
    - "What animals do you see?"
    - "Describe the scene"

    Args:
        image: Image file to analyze
        prompt: Natural language question or instruction
        session_id: Optional session ID for conversation continuity

    Returns:
        Agent's analysis response with processing time
    """
    start_time = time.time()

    try:
        # Get or create session (same as vision API)
        session_id, session = context_manager.get_or_create_session(session_id)

        # Read image/video data
        media_data = await image.read()
        logger.info(f"Received media for session {session_id}, size: {len(media_data)} bytes")

        # Detect if it's a video or image
        from app.utils.image_utils import is_video, extract_video_frame

        if is_video(media_data):
            logger.info(f"Detected VIDEO upload for session {session_id}")
            # Store BOTH video and extracted frame
            frame_bytes = extract_video_frame(media_data)
            logger.info(f"Extracted frame: {len(frame_bytes)} bytes")
            session.add_message("user", prompt, image=frame_bytes, video=media_data)
        else:
            logger.info(f"Detected IMAGE upload for session {session_id}")
            # Store image only
            session.add_message("user", prompt, image=media_data)

        # Get conversation context
        chat_history = context_manager.get_context(session_id)

        # Run agent with the prompt
        logger.info(f"Processing agent analyze: '{prompt}' for session {session_id}")
        result = await vision_agent.analyze_query(
            query=prompt,
            session_id=session_id,
            chat_history=chat_history
        )

        # Store the assistant response
        session.add_message("assistant", result.get("response", ""))

        processing_time = time.time() - start_time
        logger.info(f"Agent analyze completed for session {session_id} in {processing_time:.2f}s")

        # Check if annotated image was generated
        from pathlib import Path
        annotated_images_dir = Path(__file__).parent.parent.parent / "annotated_images"
        annotated_image_path = annotated_images_dir / f"{session_id}.jpg"

        annotated_image_url = None
        has_annotated_image = False

        if annotated_image_path.exists():
            annotated_image_url = f"/api/images/{session_id}.jpg"
            has_annotated_image = True
            logger.info(f"Annotated image available at: {annotated_image_url}")

        # Get detection data if available
        from ..models.schemas import Detection, ImageMetadata
        detections_data = context_manager.get_detections(session_id)
        detections = None
        image_metadata = None

        if detections_data:
            # Convert raw detections to Detection models
            detections = [
                Detection(
                    class_name=det.get('class_name', ''),
                    confidence=det.get('confidence', 0.0),
                    bbox=det.get('bbox', [])
                )
                for det in detections_data.get('detections', [])
            ]

            # Get image shape (height, width)
            image_shape = detections_data.get('image_shape', (0, 0))
            if image_shape and len(image_shape) >= 2:
                image_metadata = ImageMetadata(
                    width=image_shape[1],   # width
                    height=image_shape[0]   # height
                )

            logger.info(f"Including {len(detections)} detections in response for session {session_id}")

        return AgentAnalyzeResponse(
            session_id=session_id,
            response=result.get("response", ""),
            model_used=vision_agent.llm.model if vision_agent.llm else "unknown",
            processing_time=processing_time,
            annotated_image_url=annotated_image_url,
            has_annotated_image=has_annotated_image,
            detections=detections,
            image_metadata=image_metadata,
        )

    except Exception as e:
        logger.error(f"Error in agent analyze: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze image: {str(e)}"
        )


@router.post("/query", response_model=AgentQueryResponse)
async def agent_query(request: AgentQueryRequest):
    """
    Analyze an image using the AI agent with natural language queries.

    The agent automatically selects the appropriate YOLO detection tool based on your query:
    - Object detection: "find cars", "how many dogs", "what objects are in this image"
    - Face detection: "how many people", "detect faces", "find humans"
    - Segmentation: "segment objects", "show boundaries", "separate objects"

    **Example queries:**
    - "How many cars are in this image?"
    - "Find all the people"
    - "What animals do you see?"
    - "Detect all furniture"
    - "Are there any cats or dogs?"

    Args:
        request: Agent query request with query and session_id

    Returns:
        Agent's response with analysis results
    """
    try:
        # Check if session exists
        session = context_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found or expired. Please upload an image first."
            )

        # Check if session has an image
        if not session.get_last_image():
            raise HTTPException(
                status_code=400,
                detail="No image found in this session. Please upload an image first."
            )

        # Get conversation context for the agent
        chat_history = context_manager.get_context(request.session_id)

        # Run agent
        logger.info(f"Processing agent query: '{request.query}' for session {request.session_id}")
        result = await vision_agent.analyze_query(
            query=request.query,
            session_id=request.session_id,
            chat_history=chat_history
        )

        # Store the interaction in context
        context_manager.add_interaction(
            session_id=request.session_id,
            user_message=request.query,
            assistant_response=result.get("response", "")
        )

        logger.info(f"Agent query completed for session {request.session_id}")

        # Generate annotated image if requested
        annotated_image_url = None
        if request.annotate:
            try:
                # Get the image from session
                image_bytes = context_manager.get_last_image(request.session_id)
                if image_bytes:
                    # Determine if detection was likely performed based on the query
                    query_lower = request.query.lower()
                    needs_detection = any(word in query_lower for word in [
                        'find', 'detect', 'count', 'how many', 'car', 'person', 'people',
                        'object', 'dog', 'cat', 'vehicle', 'animal'
                    ])

                    if needs_detection:
                        # Call ML service to get annotated image
                        ml_url = f"{ml_client.base_url}/api/detect-annotated"

                        files = {"image": ("image.jpg", image_bytes, "image/jpeg")}
                        data = {"confidence": "0.7"}

                        # Try to extract classes from the query
                        # This is a simple heuristic - could be improved
                        common_objects = ['car', 'truck', 'bus', 'person', 'dog', 'cat',
                                         'chair', 'laptop', 'phone', 'bike', 'motorcycle']
                        detected_classes = [obj for obj in common_objects if obj in query_lower]
                        if detected_classes:
                            data["classes"] = ",".join(detected_classes)

                        response = requests.post(ml_url, files=files, data=data, timeout=30)

                        if response.status_code == 200 and response.headers.get('content-type') == 'image/jpeg':
                            # Save annotated image
                            filename = f"{request.session_id}_{uuid.uuid4().hex[:8]}.jpg"
                            annotated_path = Path(__file__).parent.parent.parent / "annotated_images" / filename
                            annotated_path.parent.mkdir(exist_ok=True)

                            with open(annotated_path, "wb") as f:
                                f.write(response.content)

                            annotated_image_url = f"/annotated/{filename}"
                            logger.info(f"Generated annotated image: {annotated_image_url}")
                        else:
                            logger.warning(f"Failed to generate annotated image: {response.status_code}")
            except Exception as e:
                logger.error(f"Error generating annotated image: {e}", exc_info=True)

        return AgentQueryResponse(
            session_id=request.session_id,
            query=request.query,
            response=result.get("response", ""),
            status=result.get("status", "success"),
            annotated_image_url=annotated_image_url
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing agent query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process agent query: {str(e)}"
        )


@router.post("/detect", response_model=DetectionResponse)
async def direct_detection(request: DetectionRequest):
    """
    Direct object detection without agent (faster, no LLM overhead).

    Use this endpoint when you want quick object detection without natural language processing.

    Args:
        request: Detection request with session_id and optional object_types

    Returns:
        Detection results with objects found
    """
    try:
        # Check if session exists
        session = context_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found or expired. Please upload an image first."
            )

        # Check if session has an image
        if not session.get_last_image():
            raise HTTPException(
                status_code=400,
                detail="No image found in this session. Please upload an image first."
            )

        # Perform detection
        logger.info(f"Direct detection for session {request.session_id}")
        result = await vision_agent.simple_detect(
            session_id=request.session_id,
            object_types=request.object_types,
            confidence=request.confidence
        )

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))

        return DetectionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in direct detection: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Direct detection failed: {str(e)}"
        )


@router.get("/session/{session_id}/frame")
async def get_session_frame(session_id: str, frame_index: Optional[int] = None):
    """
    Get the stored image/frame for a session.
    For videos with multiple frames (slideshow), use frame_index parameter.
    For single frame videos or images, omit frame_index.

    Args:
        session_id: Session ID
        frame_index: Optional frame index for video slideshow (0-based)

    Returns:
        JPEG image bytes
    """
    from fastapi.responses import Response

    try:
        session = context_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )

        image_bytes = None

        # If frame_index is specified, try to get video frame from slideshow
        if frame_index is not None:
            if hasattr(session, 'video_frames') and session.video_frames:
                image_bytes = session.video_frames.get(frame_index)
                if not image_bytes:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Frame {frame_index} not found for session {session_id}"
                    )
                logger.info(f"Serving video frame {frame_index} for session {session_id}, size: {len(image_bytes)} bytes")
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"No video frames found for session {session_id}"
                )
        else:
            # Fall back to last_image (for backward compatibility)
            image_bytes = session.get_last_image()
            if not image_bytes:
                raise HTTPException(
                    status_code=404,
                    detail=f"No image/frame found for session {session_id}"
                )
            logger.info(f"Serving frame for session {session_id}, size: {len(image_bytes)} bytes")

        return Response(
            content=image_bytes,
            media_type="image/jpeg",
            headers={
                "Cache-Control": "public, max-age=3600",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving frame: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to serve frame: {str(e)}"
        )


@router.get("/session/{session_id}/video-frames")
async def get_video_frames_metadata(session_id: str):
    """
    Get metadata about video frames stored in a session.
    Returns information about available frames, detections, and timestamps.

    Returns:
        JSON with video frames metadata
    """
    try:
        logger.info(f"[video-frames] Fetching metadata for session: {session_id}")

        session = context_manager.get_session(session_id)
        if not session:
            logger.error(f"[video-frames] Session {session_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )

        logger.info(f"[video-frames] Session found. Checking for video_frames_metadata attribute...")
        logger.debug(f"[video-frames] Session attributes: {dir(session)}")

        if not hasattr(session, 'video_frames_metadata'):
            logger.error(f"[video-frames] No video_frames_metadata attribute in session {session_id}")
            logger.error(f"[video-frames] Available attributes: {[attr for attr in dir(session) if not attr.startswith('_')]}")
            raise HTTPException(
                status_code=404,
                detail=f"No video frames metadata found for session {session_id}"
            )

        metadata = session.video_frames_metadata
        logger.info(f"[video-frames] SUCCESS: Serving metadata with {metadata.get('frames_count', 0)} frames")

        return metadata

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video frames metadata: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get video frames metadata: {str(e)}"
        )


@router.post("/session/{session_id}/segment-video-frames")
async def segment_video_frames(session_id: str):
    """
    Enrich existing video frames with segmentation data.
    Re-runs segmentation on the same video frames that were previously extracted for detection.

    Args:
        session_id: Session identifier

    Returns:
        Updated video frames metadata with segmentation masks
    """
    try:
        # Get session
        session = context_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Check if video exists
        video_bytes = context_manager.get_last_video(session_id)
        if not video_bytes:
            raise HTTPException(status_code=404, detail="No video found in session")

        # Check if video frames metadata exists
        if not hasattr(session, 'video_frames_metadata'):
            raise HTTPException(status_code=404, detail="No video frames found. Analyze video first.")

        logger.info(f"[segment_video_frames] Enriching video frames for session {session_id}")

        # Call ML service to segment the same frames
        result = await ml_client.segment_video_frames(
            video_bytes=video_bytes,
            confidence=0.7,
            classes=None,
            frame_interval=2.0,
            max_frames=10
        )

        if result.get('status') == 'error':
            raise HTTPException(status_code=500, detail=result.get('message', 'Segmentation failed'))

        frames = result.get('frames', [])
        if not frames:
            raise HTTPException(status_code=500, detail="Failed to segment video frames")

        # Update existing video_frames_metadata with segmentation data
        import base64

        for idx, frame_data in enumerate(frames):
            if idx < len(session.video_frames_metadata['frames']):
                # Add segments to existing frame data
                segments = frame_data.get('segments', [])
                session.video_frames_metadata['frames'][idx]['segments'] = segments
                session.video_frames_metadata['frames'][idx]['segments_count'] = len(segments)

                logger.info(f"[segment_video_frames] Frame {idx}: added {len(segments)} segments")

        # Add total segments count to metadata
        total_segments = result.get('total_segments', 0)
        session.video_frames_metadata['total_segments'] = total_segments

        logger.info(f"[segment_video_frames] Enriched {len(frames)} frames with {total_segments} total segments")

        return {
            "status": "success",
            "session_id": session_id,
            "frames_enriched": len(frames),
            "total_segments": total_segments,
            "video_frames_metadata": session.video_frames_metadata
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video frames segmentation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Segmentation failed: {str(e)}")


@router.get("/health")
async def agent_health():
    """
    Check health of agent service and ML service connection.

    Returns:
        Health status of both the agent and ML service
    """
    try:
        # Check ML service health
        ml_health = await ml_client.health_check()

        # Create sample tools to get count
        from app.services.vision_tools import create_vision_tools
        sample_tools = create_vision_tools("sample")

        agent_status = {
            "initialized": vision_agent.initialized,
            "model": vision_agent.llm.model if vision_agent.llm else None,
            "tools_count": len(sample_tools)
        }

        if not vision_agent.initialized:
            agent_status["error"] = vision_agent.initialization_error
            agent_status["note"] = "Agent unavailable - direct ML endpoints still work"

        return {
            "status": "healthy" if ml_health.get("status") == "healthy" else "degraded",
            "agent": agent_status,
            "ml_service": ml_health
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
