#!/usr/bin/env python3
"""
GPT-OSS 120B API Server
A FastAPI server for interacting with GPT-OSS 120B model
Designed for deployment on RunPod Serverless
"""

import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import httpx
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    GPT_OSS_API_URL = os.getenv("GPT_OSS_API_URL", "http://localhost:8000")
    GPT_OSS_API_KEY = os.getenv("GPT_OSS_API_KEY", "")
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    PORT = int(os.getenv("PORT", "8080"))
    HOST = os.getenv("HOST", "0.0.0.0")

config = Config()

# Pydantic models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    content: str = Field(..., description="Content of the message")

class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="List of messages in the conversation")
    model: str = Field(default="gpt-oss-120b", description="Model to use for completion")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(default=None, description="Sampling temperature")
    stream: Optional[bool] = Field(default=False, description="Whether to stream the response")
    top_p: Optional[float] = Field(default=1.0, description="Top-p sampling parameter")
    frequency_penalty: Optional[float] = Field(default=0.0, description="Frequency penalty")
    presence_penalty: Optional[float] = Field(default=0.0, description="Presence penalty")

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    model: str
    version: str

# Global HTTP client
http_client: Optional[httpx.AsyncClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    global http_client
    
    # Startup
    logger.info("Starting GPT-OSS API Server...")
    http_client = httpx.AsyncClient(timeout=300.0)
    
    # Test connection to GPT-OSS (skip for testing)
    try:
        response = await http_client.get(f"{config.GPT_OSS_API_URL}/health")
        if response.status_code == 200:
            logger.info("Successfully connected to GPT-OSS API")
        else:
            logger.warning(f"GPT-OSS API health check failed: {response.status_code}")
    except Exception as e:
        logger.warning(f"GPT-OSS API not available during startup: {e}")
        logger.info("Server will start anyway - configure GPT_OSS_API_URL when ready")
    
    yield
    
    # Shutdown
    logger.info("Shutting down GPT-OSS API Server...")
    if http_client:
        await http_client.aclose()

# Initialize FastAPI app
app = FastAPI(
    title="GPT-OSS 120B API Server",
    description="FastAPI server for GPT-OSS 120B model interactions",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get HTTP client
async def get_http_client() -> httpx.AsyncClient:
    if http_client is None:
        raise HTTPException(status_code=500, detail="HTTP client not initialized")
    return http_client

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "GPT-OSS 120B API Server",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        model="gpt-oss-120b",
        version="1.0.0"
    )

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """
    Create a chat completion using GPT-OSS 120B
    Compatible with OpenAI API format
    """
    try:
        # Prepare request for GPT-OSS API
        gpt_oss_request = {
            "messages": [msg.dict() for msg in request.messages],
            "model": request.model,
            "max_tokens": request.max_tokens or config.MAX_TOKENS,
            "temperature": request.temperature or config.TEMPERATURE,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
            "stream": request.stream
        }
        
        # Add API key if available
        headers = {"Content-Type": "application/json"}
        if config.GPT_OSS_API_KEY:
            headers["Authorization"] = f"Bearer {config.GPT_OSS_API_KEY}"
        
        # Make request to GPT-OSS API
        logger.info(f"Making request to GPT-OSS API: {config.GPT_OSS_API_URL}/v1/chat/completions")
        
        if request.stream:
            # Handle streaming response
            async def generate_stream():
                async with client.stream(
                    "POST",
                    f"{config.GPT_OSS_API_URL}/v1/chat/completions",
                    json=gpt_oss_request,
                    headers=headers
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"GPT-OSS API error: {response.status_code} - {error_text}")
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"GPT-OSS API error: {error_text.decode()}"
                        )
                    
                    async for chunk in response.aiter_text():
                        if chunk:
                            yield chunk
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache"}
            )
        
        else:
            # Handle regular response
            response = await client.post(
                f"{config.GPT_OSS_API_URL}/v1/chat/completions",
                json=gpt_oss_request,
                headers=headers
            )
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"GPT-OSS API error: {response.status_code} - {error_text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"GPT-OSS API error: {error_text}"
                )
            
            result = response.json()
            logger.info("Successfully received response from GPT-OSS API")
            return result
            
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to GPT-OSS API: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/v1/models")
async def list_models():
    """List available models"""
    return {
        "object": "list",
        "data": [
            {
                "id": "gpt-oss-120b",
                "object": "model",
                "created": 1640995200,
                "owned_by": "openai",
                "permission": [],
                "root": "gpt-oss-120b",
                "parent": None
            }
        ]
    }

@app.post("/test")
async def test_connection(
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Test connection to GPT-OSS API"""
    try:
        test_request = ChatCompletionRequest(
            messages=[
                ChatMessage(role="user", content="Hello! Can you respond with a simple greeting?")
            ],
            max_tokens=50
        )
        
        response = await chat_completions(test_request, client)
        return {
            "status": "success",
            "message": "Connection to GPT-OSS API is working",
            "test_response": response
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to connect to GPT-OSS API: {str(e)}"
        }

@app.post("/mock-test")
async def mock_test():
    """Mock test endpoint that doesn't require GPT-OSS API"""
    return {
        "status": "success",
        "message": "Server is running correctly",
        "mock_response": {
            "id": "chatcmpl-mock-123",
            "object": "chat.completion",
            "created": 1640995200,
            "model": "gpt-oss-120b",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! This is a mock response from GPT-OSS 120B API Server. The server is working correctly!"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }
    }

if __name__ == "__main__":
    logger.info(f"Starting server on {config.HOST}:{config.PORT}")
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=False,
        log_level="info"
    )