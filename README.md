# Voice Agent - OpenAI Realtime API Edition

A voice-powered AI agent that leverages OpenAI's Realtime API with GPT-4o-mini for live speech-to-speech interaction, featuring built-in prompt caching and natural conversation flow.

## Features

- **Live Speech-to-Speech**: Direct speech interaction using OpenAI's Realtime API with GPT-4o-mini
- **Automatic Prompt Caching**: Built-in optimization with ≥1,024 token context prefix for reduced latency and cost
- **Streaming Audio**: Continuous audio streaming with `streaming=True` for natural conversation flow
- **Knowledge Base Integration**: Smart context integration from PDF documents with cached prompts
- **Voice Activity Detection**: Server-side VAD for natural turn-taking
- **Real-time Communication**: WebSocket-based bidirectional audio streaming
- **Session Management**: Multi-session support with persistent knowledge context
- **Web Interface**: Simple HTML/CSS/JS frontend for voice interaction

## Architecture

```
voice-agent/
├── app/
│   ├── main.py                      # FastAPI application entry point
│   ├── config.py                    # Configuration management (OpenAI settings)
│   ├── apis/
│   │   └── voice_agent.py          # API endpoints and WebSocket handlers
│   ├── services/
│   │   ├── openai_realtime_service.py  # OpenAI Realtime API integration
│   │   └── knowledge_service.py     # Knowledge base management
│   └── models/
│       └── schemas.py               # Pydantic models
├── knowledge_base/                  # PDF documents directory
├── requirements.txt                 # Python dependencies
├── .env                            # Environment variables (create from .env.example)
└── README.md                       # This file
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

Copy the example environment file and configure your OpenAI API key:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here
```

**Required Environment Variables:**
- `OPENAI_API_KEY`: Your OpenAI API key with access to GPT-4o-mini-realtime-preview

**Optional Configuration:**
- `OPENAI_REALTIME_MODEL`: Model to use (default: gpt-4o-mini-realtime-preview)
- `OPENAI_REALTIME_VOICE`: Voice selection (default: alloy)
- `VAD_THRESHOLD`: Voice activity detection sensitivity (default: 0.5)
- `ENABLE_PROMPT_CACHING`: Enable automatic prompt caching (default: True)

### 3. Add Knowledge Base

Place your PDF documents in the `knowledge_base/` directory:

```bash
mkdir -p knowledge_base
# Copy your PDF files to knowledge_base/
```

### 4. Run the Application

**Option 1: Quick Start (Recommended)**
```bash
# Guided startup with automatic testing
python start.py
```

**Option 2: Manual Steps**
```bash
# Test imports and configuration
python test_imports.py

# Test OpenAI API connectivity (optional)
python test_openai_realtime.py

# Start the server
python run.py
```

**Option 3: Direct Uvicorn**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at `http://localhost:8000`

### 5. Troubleshooting Startup

If you encounter import errors:

```bash
# Test all imports
python test_imports.py

# Check specific issues
python test_openai_realtime.py
```

Common fixes:
- Ensure you're in the project root directory
- Verify Python dependencies: `pip install -r requirements.txt`
- Check `.env` file configuration

## How It Works

### OpenAI Realtime API Integration

1. **Session Creation**: Each user session creates a cached context with knowledge base content (≥1,024 tokens)
2. **Audio Streaming**: Real-time bidirectional audio streaming via WebSockets
3. **Voice Activity Detection**: Server-side VAD automatically detects speech start/end
4. **Live Response Generation**: GPT-4o-mini generates responses in real-time with streaming audio output
5. **Context Preservation**: Conversation context maintained throughout the session with caching optimization

### Conversation Flow

1. **Initialization**: User starts session → Knowledge base loaded → Context cached
2. **Voice Input**: User speaks → Audio streamed to OpenAI Realtime API
3. **Processing**: VAD detects speech end → Model processes with cached context
4. **Response**: Real-time audio response streamed back to user
5. **Continuation**: Natural conversation flow with maintained context

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/start-session` | Start new session with knowledge loading |
| `GET` | `/api/v1/session/{id}/status` | Get session status and connection info |
| `POST` | `/api/v1/query/text` | Process text query (fallback mode) |
| `WS` | `/api/v1/ws/{session_id}` | WebSocket for live voice interaction |
| `DELETE` | `/api/v1/session/{id}` | End session and cleanup |
| `GET` | `/api/v1/health` | Service health check |

## WebSocket Protocol

### Client → Server
- **Audio Data**: Binary audio chunks (PCM16, 24kHz, mono)
- **Control Messages**: JSON messages for commands (ping, etc.)

### Server → Client
- **Audio Response**: Binary audio chunks from OpenAI
- **Transcript Updates**: Real-time transcript deltas
- **Status Updates**: Session status, speech detection, errors
- **System Messages**: Connection status, processing updates

## Key Features

### Prompt Caching Optimization

The system automatically builds cached context with:
- Knowledge base content integrated into system prompt
- Minimum 1,024 tokens for effective caching
- Automatic cache invalidation after 1 hour
- Cost and latency reduction through reused context

### Streaming Audio with Natural Flow

- **Continuous Streaming**: Audio flows continuously for natural conversation
- **Low Latency**: Direct WebSocket connection to OpenAI Realtime API
- **Voice Activity Detection**: Automatic turn detection without manual controls
- **Interruption Handling**: Natural conversation interruptions supported

### Session Management

- **Isolated Sessions**: Each session has independent knowledge context
- **Persistent Context**: Conversation history maintained during session
- **Auto Cleanup**: Sessions automatically cleaned up after timeout
- **Reconnection Support**: Graceful handling of connection drops

## Development

### Project Structure

- **`app/main.py`**: FastAPI application setup with CORS and routing
- **`app/config.py`**: Configuration management for OpenAI Realtime API
- **`app/apis/voice_agent.py`**: WebSocket endpoints for live voice interaction
- **`app/services/openai_realtime_service.py`**: OpenAI Realtime API integration
- **`app/services/knowledge_service.py`**: PDF processing and knowledge management
- **`app/models/schemas.py`**: Data models and API schemas

### Adding New Features

1. **Extend Voice Interaction**: Modify `openai_realtime_service.py`
2. **Add Knowledge Sources**: Update `knowledge_service.py`
3. **New API Endpoints**: Add to `app/apis/voice_agent.py`
4. **Configuration Options**: Update `app/config.py`

### Testing

```bash
# Check service health
curl http://localhost:8000/api/v1/health

# Test session creation
curl -X POST http://localhost:8000/api/v1/start-session

# Test with audio (requires WebSocket client)
# See frontend implementation for audio streaming examples
```

## Configuration Options

### Voice Settings
- **Voice Options**: alloy, echo, fable, onyx, nova, shimmer
- **Audio Format**: PCM16 at 24kHz (optimized for OpenAI)
- **Sample Rate**: 24,000 Hz (OpenAI Realtime API standard)

### Model Settings
- **Primary Model**: gpt-4o-mini-realtime-preview (fast, cost-effective)
- **Alternative**: gpt-4o-realtime-preview (higher quality, higher cost)
- **Temperature**: 0.7 (balanced creativity/consistency)
- **Max Tokens**: 4096 (configurable response length)

### Performance Tuning
- **VAD Threshold**: Adjust speech detection sensitivity
- **Silence Duration**: Configure pause detection timing
- **Cache Timeout**: Control context cache lifetime
- **Session Timeout**: Set automatic session cleanup time

## Troubleshooting

### Common Issues

1. **"OpenAI API key not configured"**
   - Ensure `OPENAI_API_KEY` is set in `.env`
   - Verify API key has access to GPT-4o-mini-realtime-preview

2. **"Failed to connect to OpenAI Realtime API"**
   - Check internet connectivity
   - Verify API key permissions
   - Ensure model is available in your region

3. **"No audio response"**
   - Check audio format (PCM16, 24kHz, mono)
   - Verify WebSocket connection is established
   - Check browser audio permissions

4. **"Knowledge base not loading"**
   - Ensure PDF files are in `knowledge_base/` directory
   - Check PDF file permissions and format
   - Review server logs for processing errors

### Performance Optimization

- **Prompt Caching**: Enabled by default for cost/latency benefits
- **Audio Streaming**: Continuous streaming reduces perceived latency
- **Session Reuse**: Keep sessions active for better performance
- **Knowledge Chunking**: Optimize PDF content for better context

## Requirements

- **Python**: 3.8 or higher
- **OpenAI API**: Access to GPT-4o-mini-realtime-preview model
- **Audio Format**: Browser with WebRTC support for audio streaming
- **WebSocket**: Modern browser with WebSocket support

## License

[Add your license information here]

## Contributing

[Add contributing guidelines here] 