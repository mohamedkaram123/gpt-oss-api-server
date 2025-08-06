#!/usr/bin/env python3
"""
Example client for testing GPT-OSS 120B API Server
"""

import asyncio
import httpx
import json
from typing import List, Dict

class GPTOSSClient:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=300.0)
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-oss-120b",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        stream: bool = False
    ) -> Dict:
        """Send a chat completion request"""
        
        payload = {
            "messages": messages,
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream
        }
        
        response = await self.client.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code} - {response.text}")
        
        return response.json()
    
    async def health_check(self) -> Dict:
        """Check API health"""
        response = await self.client.get(f"{self.base_url}/health")
        return response.json()
    
    async def test_connection(self) -> Dict:
        """Test connection to GPT-OSS API"""
        response = await self.client.post(f"{self.base_url}/test")
        return response.json()
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

async def main():
    """Example usage"""
    client = GPTOSSClient()
    
    try:
        # Health check
        print("🔍 Checking API health...")
        health = await client.health_check()
        print(f"✅ Health: {health}")
        
        # Test connection
        print("\n🔗 Testing connection to GPT-OSS...")
        test_result = await client.test_connection()
        print(f"📊 Test result: {test_result}")
        
        # Chat completion example
        print("\n💬 Testing chat completion...")
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": "What is the capital of France? Please provide a brief answer."}
        ]
        
        response = await client.chat_completion(
            messages=messages,
            max_tokens=100,
            temperature=0.7
        )
        
        print(f"🤖 Response: {json.dumps(response, indent=2)}")
        
        # Creative writing example
        print("\n✍️ Testing creative writing...")
        creative_messages = [
            {"role": "user", "content": "Write a short poem about artificial intelligence in Arabic."}
        ]
        
        creative_response = await client.chat_completion(
            messages=creative_messages,
            max_tokens=200,
            temperature=0.9
        )
        
        print(f"🎨 Creative response: {json.dumps(creative_response, indent=2)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())