"""
Chat endpoints for Pombi AI Assistant
"""

import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import json
import asyncio

from app.core.ai_engine import AIEngine
from app.utils.validators import ChatRequest, ValidationError
from app.utils.logging import setup_logging

logger = setup_logging(__name__)

# Create router
router = APIRouter()
security = HTTPBearer(auto_error=False)

# Global AI engine instance
ai_engine = AIEngine()


async def get_ai_engine() -> AIEngine:
    """Dependency to get AI engine instance"""
    return ai_engine


async def get_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """Extract user ID from authorization header (simplified)"""
    if credentials:
        # In a real implementation, this would validate JWT tokens
        # For now, we'll use a simple approach
        return credentials.credentials[:20]  # Use first 20 chars as user ID
    return None


@router.post("/", response_model=Dict[str, Any])
async def chat_message(
    request: ChatRequest,
    ai_engine: AIEngine = Depends(get_ai_engine),
    user_id: Optional[str] = Depends(get_user_id)
):
    """
    Process a chat message and generate response
    """
    try:
        logger.info(
            "Chat request received",
            extra={
                "user_id": user_id,
                "mode": request.mode,
                "message_length": len(request.message),
                "has_conversation_id": request.conversation_id is not None
            }
        )

        response = await ai_engine.process_message(
            message=request.message,
            mode=request.mode,
            conversation_id=request.conversation_id,
            context=request.context,
            model_preference=request.model_preference,
            user_id=user_id
        )

        return {
            "success": True,
            "data": response
        }

    except ValidationError as e:
        logger.warning(
            "Validation error in chat request",
            extra={
                "user_id": user_id,
                "error": str(e)
            }
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(
            "Unexpected error in chat endpoint",
            extra={
                "user_id": user_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/conversations/{conversation_id}/history")
async def get_conversation_history(
    conversation_id: str,
    ai_engine: AIEngine = Depends(get_ai_engine),
    user_id: Optional[str] = Depends(get_user_id)
):
    """Get conversation history"""
    try:
        history = await ai_engine.get_conversation_history(conversation_id)
        return {
            "success": True,
            "data": {
                "conversation_id": conversation_id,
                "history": history
            }
        }
    except Exception as e:
        logger.error(
            "Error getting conversation history",
            extra={
                "user_id": user_id,
                "conversation_id": conversation_id,
                "error": str(e)
            }
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation history")


@router.get("/conversations/{conversation_id}/summary")
async def get_conversation_summary(
    conversation_id: str,
    ai_engine: AIEngine = Depends(get_ai_engine),
    user_id: Optional[str] = Depends(get_user_id)
):
    """Get conversation summary"""
    try:
        summary = await ai_engine.get_conversation_summary(conversation_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {
            "success": True,
            "data": summary
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting conversation summary",
            extra={
                "user_id": user_id,
                "conversation_id": conversation_id,
                "error": str(e)
            }
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation summary")


@router.websocket("/stream")
async def chat_stream(websocket: WebSocket):
    """WebSocket endpoint for streaming chat responses"""
    await websocket.accept()

    try:
        # Receive initial message
        data = await websocket.receive_text()
        message_data = json.loads(data)

        # Validate request
        try:
            request = ChatRequest(**message_data)
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "data": {"error": f"Invalid request format: {str(e)}"}
            })
            return

        # Send acknowledgment
        await websocket.send_json({
            "type": "connected",
            "data": {"conversation_id": request.conversation_id}
        })

        # Process message
        response_data = await ai_engine.process_message(
            message=request.message,
            mode=request.mode,
            conversation_id=request.conversation_id,
            context=request.context,
            model_preference=request.model_preference,
            user_id=None  # WebSocket requests don't have auth headers in this simple implementation
        )

        # Send response
        await websocket.send_json({
            "type": "response",
            "data": response_data
        })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(
            "WebSocket error",
            extra={"error": str(e)},
            exc_info=True
        )
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"error": "An unexpected error occurred"}
            })
        except:
            pass  # Connection might already be closed


@router.post("/cleanup")
async def cleanup_sessions(ai_engine: AIEngine = Depends(get_ai_engine)):
    """Clean up expired sessions"""
    try:
        cleaned_count = await ai_engine.cleanup_expired_sessions()
        return {
            "success": True,
            "data": {
                "cleaned_sessions": cleaned_count,
                "message": f"Cleaned up {cleaned_count} expired sessions"
            }
        }
    except Exception as e:
        logger.error("Error during cleanup", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Cleanup failed")


@router.get("/stats")
async def get_system_stats(ai_engine: AIEngine = Depends(get_ai_engine)):
    """Get system statistics"""
    try:
        stats = await ai_engine.get_system_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error("Error getting system stats", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to retrieve system statistics")