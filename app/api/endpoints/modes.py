"""
Mode management endpoints for Pombi AI Assistant
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.core.ai_engine import AIEngine
from app.utils.logging import setup_logging

logger = setup_logging(__name__)

# Create router
router = APIRouter()

# Global AI engine instance (shared with chat endpoints)
ai_engine = AIEngine()


async def get_ai_engine() -> AIEngine:
    """Dependency to get AI engine instance"""
    return ai_engine


@router.get("/", response_model=Dict[str, Any])
async def get_available_modes(ai_engine: AIEngine = Depends(get_ai_engine)):
    """Get information about available conversation modes"""
    try:
        modes_info = await ai_engine.get_mode_info()
        return {
            "success": True,
            "data": {
                "modes": modes_info,
                "count": len(modes_info)
            }
        }
    except Exception as e:
        logger.error("Error getting mode information", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to retrieve mode information")


@router.get("/{mode_name}", response_model=Dict[str, Any])
async def get_mode_details(mode_name: str, ai_engine: AIEngine = Depends(get_ai_engine)):
    """Get detailed information about a specific mode"""
    try:
        modes_info = await ai_engine.get_mode_info()

        # Find the requested mode
        mode_info = None
        for mode in modes_info:
            if mode["name"] == mode_name:
                mode_info = mode
                break

        if not mode_info:
            raise HTTPException(status_code=404, detail=f"Mode '{mode_name}' not found")

        return {
            "success": True,
            "data": mode_info
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting mode details",
            extra={
                "mode_name": mode_name,
                "error": str(e)
            }
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve mode details")


@router.get("/validate/{mode_name}")
async def validate_mode(mode_name: str):
    """Validate if a mode name is supported"""
    try:
        valid_modes = ["creative", "precise", "teach", "code", "analyze"]

        is_valid = mode_name in valid_modes

        return {
            "success": True,
            "data": {
                "mode_name": mode_name,
                "is_valid": is_valid,
                "valid_modes": valid_modes
            }
        }
    except Exception as e:
        logger.error("Error validating mode", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to validate mode")


@router.get("/examples/{mode_name}")
async def get_mode_examples(mode_name: str):
    """Get example prompts and responses for a specific mode"""
    try:
        examples = {
            "creative": {
                "description": "Example prompts that work well in creative mode",
                "prompts": [
                    "Write a short story about a detective who can talk to ghosts",
                    "Create a unique superhero name and origin story",
                    "Imagine a world where colors have flavors. Describe dinner",
                    "Write a poem about the relationship between time and memory",
                    "Create a dialogue between two rival artists"
                ]
            },
            "precise": {
                "description": "Example prompts for precise, factual answers",
                "prompts": [
                    "What are the main differences between RNA and DNA?",
                    "Explain the process of photosynthesis step by step",
                    "What were the primary causes of World War I?",
                    "How does blockchain technology work?",
                    "What is the boiling point of water at sea level?"
                ]
            },
            "teach": {
                "description": "Example prompts for educational explanations",
                "prompts": [
                    "Teach me about quantum computing like I'm a beginner",
                    "Explain how to solve quadratic equations with examples",
                    "Teach me the basics of photography",
                    "Explain the concept of supply and demand in economics",
                    "How do I learn to program? Give me a roadmap"
                ]
            },
            "code": {
                "description": "Example prompts for programming and technical help",
                "prompts": [
                    "Write a Python function to sort a list of numbers",
                    "How do I create a REST API in Node.js?",
                    "Debug this JavaScript code that's not working",
                    "Explain recursion with a simple example",
                    "Create a SQL query to find duplicate records"
                ]
            },
            "analyze": {
                "description": "Example prompts for analysis and comparison",
                "prompts": [
                    "Compare and contrast Python and JavaScript for web development",
                    "Analyze the pros and cons of remote work",
                    "What are the environmental impacts of electric vehicles?",
                    "Compare different approaches to machine learning",
                    "Analyze the effectiveness of social media marketing"
                ]
            }
        }

        if mode_name not in examples:
            raise HTTPException(status_code=404, detail=f"Examples for mode '{mode_name}' not found")

        return {
            "success": True,
            "data": examples[mode_name]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting mode examples",
            extra={
                "mode_name": mode_name,
                "error": str(e)
            }
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve mode examples")