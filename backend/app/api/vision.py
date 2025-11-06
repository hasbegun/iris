"""
Vision API endpoints for image and video analysis.
"""
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional
import logging

from ..models.schemas import VisionAnalysisResponse
from ..services.ollama_service import ollama_service
from ..services.context_manager import context_manager
from ..services.video_processor import video_processor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vision", tags=["vision"])


@router.post("/analyze", response_model=VisionAnalysisResponse)
async def analyze_media(
    image: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
    prompt: str = Form(...),
    session_id: Optional[str] = Form(None)
):
    """
    Analyze an image or video with a vision model.

    Args:
        image: Image file (jpg, png, webp) - optional
        video: Video file (mp4, mov, avi) - optional
        prompt: User's question or instruction
        session_id: Optional session ID for context

    Returns:
        Analysis response with session ID
    """
    try:
        # Ensure at least one media file is provided
        if not image and not video:
            raise HTTPException(
                status_code=400,
                detail="Either image or video must be provided"
            )

        # Ensure only one media type is provided
        if image and video:
            raise HTTPException(
                status_code=400,
                detail="Only one of image or video should be provided"
            )

        # Get or create session
        session_id, session = context_manager.get_or_create_session(session_id)

        # Get conversation context (previous messages, excluding images)
        context = context_manager.get_context(session_id)

        # Process based on media type
        if image:
            # Handle image
            response_text = await _process_image(image, prompt, context, session_id)
        else:
            # Handle video
            response_text = await _process_video(video, prompt, context, session_id)

        logger.info(f"Analyzed media for session {session_id}")

        return VisionAnalysisResponse(
            session_id=session_id,
            response=response_text,
            model_used=ollama_service.vision_model
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing media: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze media: {str(e)}")


async def _process_image(
    image: UploadFile,
    prompt: str,
    context: list,
    session_id: str
) -> str:
    """Process and analyze an image."""
    # Validate image type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if image.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image type. Allowed: {', '.join(allowed_types)}"
        )

    # Read image data
    image_data = await image.read()

    # Analyze image
    response = await ollama_service.analyze_image(
        image_data=image_data,
        prompt=prompt,
        context_messages=context
    )

    # Store interaction in context
    context_manager.add_interaction(
        session_id=session_id,
        user_message=prompt,
        assistant_response=response,
        image=image_data
    )

    return response


async def _process_video(
    video: UploadFile,
    prompt: str,
    context: list,
    session_id: str
) -> str:
    """Process and analyze a video by extracting and analyzing frames."""
    # Validate video type
    allowed_types = ["video/mp4", "video/quicktime", "video/x-msvideo"]
    if video.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid video type. Allowed: {', '.join(allowed_types)}"
        )

    logger.info(f"Processing video: {video.filename} ({video.content_type})")

    # Read video data
    video_data = await video.read()

    # Extract frames from video
    frames = await video_processor.extract_frames(video_data, num_frames=5)

    if not frames:
        raise HTTPException(
            status_code=400,
            detail="Could not extract frames from video"
        )

    logger.info(f"Extracted {len(frames)} frames from video")

    # Analyze frames with vision model
    # We'll analyze each frame and combine the responses
    frame_analyses = []

    for i, frame_data in enumerate(frames):
        try:
            analysis = await ollama_service.analyze_image(
                image_data=frame_data,
                prompt=f"Frame {i+1}/{len(frames)}: {prompt}",
                context_messages=context
            )
            frame_analyses.append(f"**Frame {i+1}**: {analysis}")
            logger.info(f"Analyzed frame {i+1}/{len(frames)}")
        except Exception as e:
            logger.error(f"Error analyzing frame {i+1}: {e}")
            frame_analyses.append(f"**Frame {i+1}**: Error analyzing frame")

    # Combine frame analyses into a comprehensive response
    if len(frames) == 1:
        combined_response = frame_analyses[0].replace("**Frame 1**: ", "")
    else:
        # Create a summary prompt for the video
        summary_prompt = f"""Based on the analysis of {len(frames)} frames from a video, provide a comprehensive answer to: "{prompt}"

Frame analyses:
{chr(10).join(frame_analyses)}

Provide a cohesive summary that synthesizes information from all frames."""

        # Get a final summary from the vision model
        try:
            combined_response = await ollama_service.analyze_image(
                image_data=frames[0],  # Use first frame as visual context
                prompt=summary_prompt,
                context_messages=context
            )
        except Exception as e:
            logger.error(f"Error generating video summary: {e}")
            # Fallback to just combining frame analyses
            combined_response = f"Video Analysis ({len(frames)} frames):\n\n" + "\n\n".join(frame_analyses)

    # Store interaction in context (using first frame as reference and full video)
    context_manager.add_interaction(
        session_id=session_id,
        user_message=f"[Video] {prompt}",
        assistant_response=combined_response,
        image=frames[0],  # Store first frame as reference
        video=video_data  # Store full video for YOLO detection
    )

    return combined_response


@router.post("/stream", response_model=VisionAnalysisResponse)
async def analyze_stream_frame(
    frame: UploadFile = File(...),
    prompt: str = Form(...),
    session_id: Optional[str] = Form(None),
    frame_number: Optional[int] = Form(0),
    timestamp_ms: Optional[float] = Form(0.0)
):
    """
    Analyze a video stream frame.

    Args:
        frame: Video frame image
        prompt: User's question or instruction
        session_id: Optional session ID for context
        frame_number: Frame number in the video
        timestamp_ms: Timestamp in milliseconds

    Returns:
        Analysis response with session ID
    """
    try:
        # Validate image type
        allowed_types = ["image/jpeg", "image/png", "image/webp"]
        if frame.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid frame type. Allowed: {', '.join(allowed_types)}"
            )

        # Read frame data
        frame_data = await frame.read()

        # Get or create session
        session_id, session = context_manager.get_or_create_session(session_id)

        # Get conversation context
        context = context_manager.get_context(session_id)

        # Analyze frame
        response = await ollama_service.analyze_image(
            image_data=frame_data,
            prompt=prompt,
            context_messages=context
        )

        # Store interaction in context
        context_manager.add_interaction(
            session_id=session_id,
            user_message=f"{prompt} [Frame {frame_number} @ {timestamp_ms}ms]",
            assistant_response=response,
            image=frame_data
        )

        logger.info(f"Analyzed frame {frame_number} for session {session_id}")

        return VisionAnalysisResponse(
            session_id=session_id,
            response=response,
            model_used=ollama_service.vision_model
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing frame: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze frame: {str(e)}")
