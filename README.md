# GPT-OSS 120B API Server

A FastAPI-based server for interacting with GPT-OSS 120B model, designed for easy deployment on RunPod Serverless.

## 🚀 Features

- **OpenAI-Compatible API**: Drop-in replacement for OpenAI's chat completions API
- **RunPod Serverless Ready**: Optimized for deployment on RunPod Serverless
- **Streaming Support**: Real-time response streaming
- **Docker Support**: Containerized deployment
- **Health Monitoring**: Built-in health checks and monitoring
- **Arabic Support**: Full support for Arabic language processing

## 📋 Requirements

- Python 3.11+
- FastAPI
- httpx
- Docker (for containerized deployment)
- RunPod account (for serverless deployment)

## 🛠️ Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/mohamedkaram123/gpt-oss-api-server.git
cd gpt-oss-api-server
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your GPT-OSS API configuration
```

5. Run the server:
```bash
python main.py
```

The API will be available at `http://localhost:8080`

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t gpt-oss-api-server .
```

2. Run with Docker Compose:
```bash
docker-compose up -d
```

## 🌐 RunPod Serverless Deployment

### Prerequisites
- RunPod account
- Docker image pushed to a registry (Docker Hub, etc.)

### Deployment Steps

1. **Prepare Docker Image**:
```bash
# Build and tag
docker build -t your-username/gpt-oss-api-server:latest .

# Push to Docker Hub
docker push your-username/gpt-oss-api-server:latest
```

2. **Create RunPod Serverless Endpoint**:
   - Go to RunPod Dashboard
   - Navigate to "Serverless" → "Endpoints"
   - Click "Create Endpoint"
   - Configure:
     - **Container Image**: `your-username/gpt-oss-api-server:latest`
     - **Container Start Command**: `python runpod_handler.py`
     - **Container Disk**: 5GB minimum
     - **Environment Variables**:
       ```
       GPT_OSS_API_URL=your_gpt_oss_api_url
       GPT_OSS_API_KEY=your_api_key
       ```

3. **Test Deployment**:
```bash
curl -X POST "https://api.runpod.ai/v2/your-endpoint-id/runsync" \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "messages": [
        {"role": "user", "content": "Hello, how are you?"}
      ]
    }
  }'
```

## 📚 API Usage

### Chat Completions

```python
import httpx

async def chat_with_gpt_oss():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8080/v1/chat/completions",
            json={
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is artificial intelligence?"}
                ],
                "model": "gpt-oss-120b",
                "max_tokens": 2048,
                "temperature": 0.7
            }
        )
        return response.json()
```

### Streaming Response

```python
import httpx

async def stream_chat():
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8080/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Tell me a story"}],
                "stream": True
            }
        ) as response:
            async for chunk in response.aiter_text():
                print(chunk, end="")
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GPT_OSS_API_URL` | GPT-OSS API endpoint URL | `http://localhost:8000` |
| `GPT_OSS_API_KEY` | API key for GPT-OSS | `""` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8080` |
| `MAX_TOKENS` | Default max tokens | `2048` |
| `TEMPERATURE` | Default temperature | `0.7` |

## 🧪 Testing

Run the example client:
```bash
python client_example.py
```

Test specific endpoints:
```bash
# Health check
curl http://localhost:8080/health

# Test connection
curl -X POST http://localhost:8080/test

# Chat completion
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

## 📊 Monitoring

The server includes several monitoring endpoints:

- `GET /health` - Health check
- `GET /` - Basic info
- `POST /test` - Test GPT-OSS connection
- `GET /v1/models` - List available models

## 🔒 Security

- Use environment variables for sensitive configuration
- Enable HTTPS in production
- Implement rate limiting for production use
- Validate and sanitize all inputs

## 🐛 Troubleshooting

### Common Issues

1. **Connection to GPT-OSS API fails**:
   - Check `GPT_OSS_API_URL` configuration
   - Verify GPT-OSS service is running
   - Check network connectivity

2. **RunPod deployment issues**:
   - Ensure Docker image is accessible
   - Check environment variables
   - Review RunPod logs

3. **High latency**:
   - Use appropriate GPU tier on RunPod
   - Optimize `max_tokens` parameter
   - Consider model caching strategies

## 💰 Cost Comparison

### GPT-OSS 120B on RunPod Serverless vs GPT-4o

| Service | Cost per Request* | Monthly Cost (1000 req/day) |
|---------|------------------|------------------------------|
| **GPT-OSS on RunPod** | ~$0.0014 | ~$42 |
| **GPT-4o API** | ~$0.002 | ~$60 |
| **Savings** | **30%** | **$18/month** |

*Based on average request (500 input + 50 output tokens)

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review RunPod documentation for deployment issues