# Voice Agent

A voice-powered AI agent that processes speech input, searches a knowledge base, and responds with both text and speech output.

## Features

- **Speech-to-Text**: Real-time audio transcription using Deepgram API
- **Knowledge Base Search**: Fast search through PDF documents
- **AI Response Generation**: Intelligent responses using OpenAI GPT
- **Text-to-Speech**: Natural voice synthesis using Deepgram TTS
- **Real-time Communication**: WebSocket-based real-time interaction
- **Session Management**: Multi-session support with isolated knowledge bases
- **Web Interface**: Simple HTML/CSS/JS frontend

## Architecture

```
voice-agent/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── apis/
│   │   └── voice_agent.py   # API endpoints and WebSocket handlers
│   ├── services/
│   │   ├── stt_service.py   # Speech-to-Text service
│   │   ├── tts_service.py   # Text-to-Speech service
│   │   ├── llm_service.py   # LLM integration service
│   │   └── knowledge_service.py  # Knowledge base management
│   └── models/
│       └── schemas.py       # Pydantic models
├── knowledge_base/          # PDF documents directory
├── requirements.txt         # Python dependencies
├── .env                    # Environment variables (create from .env.example)
└── README.md              # This file
```

## Quick Start

### 1. Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd voice-agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file and configure your API keys:

```bash
# Copy the example file
cp env_example.txt .env

# Edit .env with your API keys
# Required:
# - DEEPGRAM_API_KEY: Your Deepgram API key
# - OPENAI_API_KEY: Your OpenAI API key
```

### 3. Add Knowledge Base

Place your PDF documents in the `knowledge_base/` directory:

```bash
# Example:
cp your_document.pdf knowledge_base/
```

### 4. Run the Application

```bash
# Start the server
python -m app.main

# Or use uvicorn directly
uvicorn app.main:app --reload
```

### 5. Access the Application

Open your browser and navigate to:
- Web Interface: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

## API Usage

### Start a Session

```bash
curl -X POST "http://localhost:8000/api/v1/start-session"
```

### Check Session Status

```bash
curl "http://localhost:8000/api/v1/session/{session_id}/status"
```

### WebSocket Connection

Connect to `ws://localhost:8000/api/v1/ws/{session_id}` for real-time voice interaction.

### Text Query (for testing)

```bash
curl -X POST "http://localhost:8000/api/v1/query/text" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "your-session-id", "query": "What is this document about?"}'
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEEPGRAM_API_KEY` | Deepgram API key for STT/TTS | Required |
| `OPENAI_API_KEY` | OpenAI API key for LLM | Required |
| `APP_HOST` | Server host | `localhost` |
| `APP_PORT` | Server port | `8000` |
| `DEBUG` | Enable debug mode | `True` |
| `KNOWLEDGE_BASE_PATH` | Path to PDF documents | `./knowledge_base` |
| `AUDIO_SAMPLE_RATE` | Audio sample rate | `16000` |
| `AUDIO_CHANNELS` | Audio channels | `1` |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4o-mini` |
| `MAX_TOKENS` | Maximum tokens per response | `500` |
| `TEMPERATURE` | LLM temperature | `0.7` |

## How It Works

1. **Session Start**: User clicks "Start Session" → System loads PDF knowledge base
2. **Voice Input**: User speaks → Audio captured via WebRTC
3. **Speech-to-Text**: Audio sent to Deepgram → Transcribed to text
4. **Knowledge Search**: Text query searches through PDF content
5. **AI Response**: Query + relevant context sent to OpenAI GPT
6. **Text-to-Speech**: Response converted to audio via Deepgram TTS
7. **Audio Output**: Audio played back to user

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/start-session` | Start new session |
| `GET` | `/api/v1/session/{id}/status` | Get session status |
| `POST` | `/api/v1/query/text` | Process text query |
| `WS` | `/api/v1/ws/{session_id}` | WebSocket for voice interaction |
| `DELETE` | `/api/v1/session/{id}` | End session |
| `GET` | `/api/v1/health` | Service health check |

## WebSocket Messages

### Client → Server
- Audio data (binary)

### Server → Client
- `session_update`: Session status changes
- `transcription`: Speech-to-text result
- `response`: AI text response
- `processing`: Processing status updates
- `error`: Error messages
- `complete`: Processing complete
- Audio data (binary): TTS response

## Development

### Project Structure

- **`app/main.py`**: FastAPI application setup
- **`app/config.py`**: Configuration management
- **`app/apis/`**: API endpoints and WebSocket handlers
- **`app/services/`**: Business logic services
- **`app/models/`**: Data models and schemas

### Adding New Features

1. **New Service**: Add to `app/services/`
2. **New API Endpoint**: Add to `app/apis/`
3. **New Data Model**: Add to `app/models/schemas.py`
4. **Configuration**: Update `app/config.py`

### Testing

```bash
# Run health check
curl http://localhost:8000/health

# Test STT/TTS/LLM services
curl http://localhost:8000/api/v1/health
```

## Troubleshooting

### Common Issues

1. **"Configuration validation failed"**
   - Check that API keys are set in `.env`
   - Ensure `.env` file is in the root directory

2. **"No PDF files found"**
   - Add PDF files to the `knowledge_base/` directory
   - Check file permissions

3. **WebSocket connection fails**
   - Ensure server is running
   - Check browser console for errors
   - Verify session ID is valid

4. **Audio not working**
   - Check browser microphone permissions
   - Ensure HTTPS for production (required for getUserMedia)
   - Verify Deepgram API key is valid

### Logging

Logs are written to both console and `voice_agent.log` file.

## Production Deployment

### Environment Setup

1. Set `DEBUG=False` in production
2. Configure proper CORS origins
3. Use HTTPS for secure WebSocket connections
4. Set up proper logging and monitoring

### Security

- Never commit API keys to version control
- Use environment variables for sensitive data
- Configure CORS appropriately
- Use HTTPS in production

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

## Support

[Add support information here] 