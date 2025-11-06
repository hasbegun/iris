"""
Chat API endpoints for follow-up conversations.
"""
from fastapi import APIRouter, HTTPException
import logging

from ..models.schemas import ChatRequest, ChatResponse
from ..services.ollama_service import ollama_service
from ..services.context_manager import context_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Continue a conversation with follow-up questions.

    Args:
        request: Chat request with message and session_id

    Returns:
        Chat response
    """
    try:
        # Get session
        session = context_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found or expired. Please start a new vision analysis."
            )

        # Get conversation context
        context = context_manager.get_context(request.session_id)

        if not context:
            raise HTTPException(
                status_code=400,
                detail="No conversation context found. Please analyze an image first."
            )

        # Get response from chat model
        response = await ollama_service.chat(
            message=request.message,
            context_messages=context
        )

        # Store interaction
        context_manager.add_interaction(
            session_id=request.session_id,
            user_message=request.message,
            assistant_response=response
        )

        logger.info(f"Chat message processed for session {request.session_id}")

        return ChatResponse(
            session_id=request.session_id,
            response=response,
            model_used=ollama_service.chat_model
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")
