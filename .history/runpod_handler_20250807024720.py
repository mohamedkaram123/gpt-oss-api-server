#!/usr/bin/env python3
"""
RunPod Serverless Handler for GPT-OSS 120B API
This file handles RunPod serverless requests and responses
"""

import json
import asyncio
import logging
from typing import Dict, Any
import runpod
from main import app, ChatCompletionRequest, ChatMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod serverless handler function
    
    Args:
        event: RunPod event containing the request data
        
    Returns:
        Dict containing the response or error
    """
    try:
        # Extract input from event
        input_data = event.get("input", {})
        
        # Support both simple prompt format and messages format
        if "prompt" in input_data:
            # Simple prompt format: {"input": {"prompt": "Hello World"}}
            messages = [
                ChatMessage(role="user", content=input_data["prompt"])
            ]
        elif "messages" in input_data:
            # OpenAI format: {"input": {"messages": [{"role": "user", "content": "Hello"}]}}
            messages = [
                ChatMessage(role=msg.get("role", "user"), content=msg.get("content", ""))
                for msg in input_data["messages"]
            ]
        else:
            return {
                "error": "Missing required field: either 'prompt' or 'messages' must be provided"
            }
        
        # Create ChatCompletionRequest
        request = ChatCompletionRequest(
            messages=messages,
            model=input_data.get("model", "gpt-oss-120b"),
            max_tokens=input_data.get("max_tokens"),
            temperature=input_data.get("temperature"),
            stream=input_data.get("stream", False),
            top_p=input_data.get("top_p", 1.0),
            frequency_penalty=input_data.get("frequency_penalty", 0.0),
            presence_penalty=input_data.get("presence_penalty", 0.0)
        )
        
        # Process the request asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Import the chat_completions function
            from main import chat_completions, get_http_client
            
            # Get HTTP client
            client = loop.run_until_complete(get_http_client())
            
            # Process the chat completion
            result = loop.run_until_complete(chat_completions(request, client))
            
            return {
                "success": True,
                "result": result
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in RunPod handler: {str(e)}")
        return {
            "error": f"Handler error: {str(e)}"
        }

# Start the RunPod serverless worker
if __name__ == "__main__":
    logger.info("Starting RunPod serverless worker for GPT-OSS 120B")
    runpod.serverless.start({"handler": handler})