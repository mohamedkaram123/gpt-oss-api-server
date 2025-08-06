# 🚀 RunPod Serverless Deployment Guide

This guide explains how to deploy the GPT-OSS 120B API Server on RunPod Serverless.

## 📋 Prerequisites

1. **RunPod Account**: [Sign up here](https://www.runpod.io/)
2. **RunPod API Key**: Get from RunPod Dashboard → Settings → API Keys
3. **Docker Hub Account**: For hosting the container image
4. **GPT-OSS 120B Access**: Ensure you have access to the model

## 🐳 Step 1: Build and Push Docker Image

1. **Build the Docker image**:
```bash
docker build -t your-username/gpt-oss-api-server:latest .
```

2. **Test locally** (optional):
```bash
docker run -p 8080:8080 -e GPT_OSS_API_URL=your_api_url your-username/gpt-oss-api-server:latest
```

3. **Push to Docker Hub**:
```bash
docker push your-username/gpt-oss-api-server:latest
```

## ⚙️ Step 2: Create RunPod Serverless Endpoint

1. **Go to RunPod Dashboard**:
   - Navigate to **Serverless** → **Endpoints**
   - Click **"Create Endpoint"**

2. **Configure the Endpoint**:
   - **Name**: `gpt-oss-120b-api`
   - **Container Image**: `your-username/gpt-oss-api-server:latest`
   - **Container Start Command**: `python runpod_handler.py`
   - **Container Disk**: `10GB` (minimum)
   - **GPU Type**: `A100 80GB` or `H100` (recommended for 120B model)
   - **Max Workers**: `1-3` (based on expected load)
   - **Idle Timeout**: `30` seconds (to save costs)

3. **Environment Variables**:
   ```
   GPT_OSS_API_URL=https://your-gpt-oss-endpoint.com
   GPT_OSS_API_KEY=your_api_key_here
   MAX_TOKENS=2048
   TEMPERATURE=0.7
   ```

4. **Advanced Settings**:
   - **Memory**: `32GB` (minimum for 120B model)
   - **CPU**: `8 vCPUs`
   - **Flash Boot**: Enable (for faster cold starts)

## 🧪 Step 3: Test the Deployment

1. **Get your endpoint URL** from the RunPod dashboard
2. **Test with curl**:

```bash
curl -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync" \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "messages": [
        {
          "role": "user",
          "content": "Hello! Can you introduce yourself?"
        }
      ],
      "max_tokens": 100,
      "temperature": 0.7
    }
  }'
```

3. **Expected Response**:
```json
{
  "delayTime": 1234,
  "executionTime": 5678,
  "id": "sync-request-id",
  "output": {
    "success": true,
    "result": {
      "id": "chatcmpl-xxx",
      "object": "chat.completion",
      "created": 1640995200,
      "model": "gpt-oss-120b",
      "choices": [...]
    }
  },
  "status": "COMPLETED"
}
```

## 💰 Cost Optimization Tips

### 1. **Idle Timeout**
- Set to `30-60 seconds` to minimize idle costs
- Balance between cost and user experience

### 2. **GPU Selection**
- **A100 80GB**: ~$1.64/hour - Good for 120B model
- **H100**: ~$1.99/hour - Faster inference, better for high load

### 3. **Auto-scaling**
- **Min Workers**: `0` (no idle costs)
- **Max Workers**: Based on expected concurrent requests
- **Scale Up Delay**: `5-10 seconds`

### 4. **Request Batching**
- Process multiple requests together when possible
- Reduces per-request overhead

## 🔧 Advanced Configuration

### Custom Handler for Better Performance

Create a more optimized handler in `runpod_handler.py`:

```python
import runpod
import asyncio
from main import app, ChatCompletionRequest, ChatMessage

# Pre-load model or initialize connections here
async def initialize():
    # Any startup logic
    pass

def handler(event):
    try:
        input_data = event.get("input", {})
        
        # Validate and process request
        request = ChatCompletionRequest(**input_data)
        
        # Process asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(process_request(request))
            return {"success": True, "result": result}
        finally:
            loop.close()
            
    except Exception as e:
        return {"error": str(e)}

# Initialize on startup
asyncio.run(initialize())
runpod.serverless.start({"handler": handler})
```

### Environment Variables for Production

```bash
# Performance
MAX_TOKENS=4096
TEMPERATURE=0.7
TOP_P=0.9

# Timeouts
REQUEST_TIMEOUT=300
CONNECTION_TIMEOUT=60

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# RunPod Specific
RUNPOD_ENDPOINT_ID=your_endpoint_id
RUNPOD_API_KEY=your_api_key
```

## 🐛 Troubleshooting

### Common Issues

1. **Cold Start Timeout**:
   - Increase container startup timeout
   - Use smaller base image
   - Pre-warm endpoints if needed

2. **Out of Memory**:
   - Increase memory allocation
   - Use model quantization (4-bit/8-bit)
   - Optimize batch size

3. **High Latency**:
   - Choose faster GPU (H100 vs A100)
   - Optimize model loading
   - Use model caching

4. **Request Failures**:
   - Check environment variables
   - Verify GPT-OSS API connectivity
   - Review container logs

### Monitoring and Logs

1. **RunPod Dashboard**:
   - Monitor request metrics
   - Check error rates
   - View execution logs

2. **Custom Logging**:
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 📊 Performance Expectations

### GPT-OSS 120B on RunPod Serverless

| Metric | A100 80GB | H100 |
|--------|-----------|------|
| **Cold Start** | 30-60s | 20-40s |
| **Warm Inference** | 2-5s | 1-3s |
| **Tokens/sec** | 15-25 | 25-40 |
| **Max Context** | 8192 | 8192+ |
| **Cost/hour** | $1.64 | $1.99 |

### Scaling Characteristics

- **0-1 requests**: Cold start penalty
- **1-10 requests**: Optimal performance
- **10+ requests**: May need multiple workers

## 🔒 Security Best Practices

1. **API Keys**: Store in environment variables, never in code
2. **Input Validation**: Validate all inputs before processing
3. **Rate Limiting**: Implement request rate limiting
4. **Logging**: Log requests but not sensitive data
5. **HTTPS**: Always use HTTPS endpoints

## 📈 Monitoring and Analytics

### Key Metrics to Track

1. **Request Volume**: Requests per hour/day
2. **Response Time**: Average and P95 latency
3. **Error Rate**: Failed requests percentage
4. **Cost**: GPU hours and total spend
5. **Model Performance**: Token generation speed

### Recommended Tools

- **RunPod Dashboard**: Built-in monitoring
- **Custom Metrics**: Log to external services
- **Alerting**: Set up cost and error alerts

## 🎯 Production Checklist

- [ ] Docker image built and pushed
- [ ] Environment variables configured
- [ ] Endpoint created and tested
- [ ] Monitoring set up
- [ ] Error handling implemented
- [ ] Cost limits configured
- [ ] Documentation updated
- [ ] Load testing completed