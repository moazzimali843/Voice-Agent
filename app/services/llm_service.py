import asyncio
import logging
from typing import List, Optional, Dict
from anthropic import AsyncAnthropic
import hashlib

# Fix imports to work from any directory
try:
    from ..config import settings
    from ..models.schemas import LLMRequest, LLMResponse, KnowledgeChunk
except ImportError:
    from config import settings
    from models.schemas import LLMRequest, LLMResponse, KnowledgeChunk

logger = logging.getLogger(__name__)

class LLMService:
    """Service for Large Language Model operations using Anthropic Claude API with prompt caching"""
    
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.conversation_history: Dict[str, List[dict]] = {}  # session_id -> messages list
    
    def _build_cached_system_prompt(self, context_chunks: List[KnowledgeChunk]) -> List[dict]:
        """Build system prompt with cached knowledge base context"""
        
        # Create knowledge context from chunks
        context_parts = []
        if context_chunks:
            for i, chunk in enumerate(context_chunks[:5]):  # Limit to top 5 chunks
                context_parts.append(f"Document {i+1} (Source: {chunk.source}):\n{chunk.content}")
        
        knowledge_context = "\n\n".join(context_parts) if context_parts else "No specific knowledge context available."
        
        # System prompt with knowledge base context (will be cached)
        system_prompt = f"""You are Savannah, a Client Intake Specialist for Bush and Bush Law Group, 
a reputable personal injury law firm. You're warm, kind, and professional. 
Your job is to make callers feel comfortable and heard, while smoothly gathering 
the info the legal team needs to evaluate their case.

KNOWLEDGE BASE CONTEXT:
{knowledge_context}

Personality, Tone & Style:
- Tone: Friendly, calm, and reassuring
- Speech Style: Speak naturally with light filler words like "mm-hmm," "okay," "I see"
- Pace: Speak gently and clearly. Never rush
- Empathy: Show kindness and validation to upset callers

Key Policies:
- We never charge upfront—you only pay if we win
- We take 33% of final settlement—you keep the rest
- No cost for medical care—we handle that
- Cases are against insurance, not individuals

Required Information (Ask one at a time):
- Caller's full name
- When the accident happened
- Where it happened (exact address)
- Physical injuries sustained
- Medical attention received
- Emotional/mental effects
- Impact on job/finances
- Property damage
- Existing legal representation
- Police report details

Instructions:
- Ask questions one by one smoothly in conversation
- Be conversational, not like filling out a form
- Get specific details, not generic responses
- Show empathy for personal/upsetting information"""

        return [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"}
            }
        ]
    
    async def generate_response_streaming(self, query: str, context_chunks: List[KnowledgeChunk], session_id: Optional[str] = None):
        """Generate streaming response using Claude with cached knowledge context"""
        try:
            # Build cached system prompt
            system_messages = self._build_cached_system_prompt(context_chunks)
            
            # Get conversation history
            conversation_context = []
            if session_id and session_id in self.conversation_history:
                conversation_context = self.conversation_history[session_id]
            
            # Add current query
            conversation_context.append({"role": "user", "content": query})
            
            # Generate streaming response
            stream = await self.client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=settings.MAX_TOKENS,
                temperature=settings.TEMPERATURE,
                system=system_messages,
                messages=conversation_context,
                stream=True
            )
            
            logger.info(f"Starting streaming response for query: {query[:50]}... (Session: {session_id})")
            
            full_response = ""
            async for chunk in stream:
                if chunk.type == "content_block_delta":
                    if hasattr(chunk.delta, 'text'):
                        content = chunk.delta.text
                        full_response += content
                        yield content
            
            # Update conversation history
            if session_id and full_response:
                conversation_context.append({"role": "assistant", "content": full_response})
                self.conversation_history[session_id] = conversation_context
                
                # Keep last 10 messages only
                if len(conversation_context) > 10:
                    self.conversation_history[session_id] = conversation_context[-9:]
                        
        except Exception as e:
            logger.error(f"Error in streaming LLM response: {str(e)}")
            yield None
    
    async def generate_response(self, query: str, context_chunks: List[KnowledgeChunk], session_id: Optional[str] = None) -> Optional[LLMResponse]:
        """Generate non-streaming response using Claude with cached knowledge context"""
        try:
            # Build cached system prompt
            system_messages = self._build_cached_system_prompt(context_chunks)
            
            # Get conversation history
            conversation_context = []
            if session_id and session_id in self.conversation_history:
                conversation_context = self.conversation_history[session_id]
            
            # Add current query
            conversation_context.append({"role": "user", "content": query})
            
            # Generate response
            response = await self.client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=settings.MAX_TOKENS,
                temperature=settings.TEMPERATURE,
                system=system_messages,
                messages=conversation_context
            )
            
            if response and response.content and len(response.content) > 0:
                content_block = response.content[0]
                if hasattr(content_block, 'text'):
                    message_content = content_block.text
                else:
                    message_content = str(content_block)
                
                llm_response = LLMResponse(
                    response=message_content.strip(),
                    tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                    model=settings.ANTHROPIC_MODEL
                )
                
                # Update conversation history
                if session_id:
                    conversation_context.append({"role": "assistant", "content": message_content.strip()})
                    self.conversation_history[session_id] = conversation_context
                    
                    # Keep last 10 messages only
                    if len(conversation_context) > 10:
                        self.conversation_history[session_id] = conversation_context[-9:]
                
                # Log cache usage if available
                if hasattr(response.usage, 'cache_creation_input_tokens'):
                    logger.info(f"Cache creation tokens: {response.usage.cache_creation_input_tokens}")
                if hasattr(response.usage, 'cache_read_input_tokens'):
                    logger.info(f"Cache read tokens: {response.usage.cache_read_input_tokens}")
                
                logger.info(f"Successfully generated LLM response for query: {query[:50]}... (Session: {session_id})")
                return llm_response
            
            logger.warning("No valid response received from Anthropic API")
            return None
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            return None
    
    def clear_conversation_history(self, session_id: str):
        """Clear conversation history for a specific session"""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
            logger.info(f"Cleared conversation history for session: {session_id}")
    
    def get_conversation_history(self, session_id: str) -> List[dict]:
        """Get conversation history for a specific session"""
        return self.conversation_history.get(session_id, [])
    
    async def test_llm_connection(self) -> bool:
        """Test LLM service connection"""
        try:
            response = await self.client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=10,
                messages=[
                    {"role": "user", "content": "Say 'test successful' if you can respond."}
                ]
            )
            
            if response and response.content and len(response.content) > 0:
                content = response.content[0].text
                return content is not None and "test successful" in content.lower()
            
            return False
            
        except Exception as e:
            logger.error(f"LLM connection test failed: {str(e)}")
            return False
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)"""
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4

    def chunk_text_for_tts(self, text: str, max_tokens: int = 15) -> List[str]:
        """Split text into chunks suitable for TTS streaming"""
        # Split by sentences first
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # If adding this sentence would exceed max tokens, save current chunk
            if current_chunk and self.estimate_tokens(current_chunk + " " + sentence) > max_tokens:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add the last chunk if it exists
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

    async def buffer_text_for_chunking(self, text_stream, min_chunk_size: int = 5):
        """Buffer streaming text and yield chunks when ready (optimized for speed)"""
        buffer = ""
        
        async for text_piece in text_stream:
            if text_piece is None:
                continue
                
            buffer += text_piece
            
            # More aggressive chunking for faster response
            should_chunk = (
                len(buffer) >= min_chunk_size and (
                    # Complete sentences
                    buffer.endswith('.') or buffer.endswith('!') or buffer.endswith('?') or
                    buffer.endswith('. ') or buffer.endswith('! ') or buffer.endswith('? ') or
                    # Commas for faster chunks
                    buffer.endswith(', ') or buffer.endswith(',') or
                    # Word boundaries with enough content
                    (len(buffer) >= min_chunk_size * 2 and buffer.endswith(' '))
                )
            )
            
            if should_chunk:
                # Yield the chunk
                yield buffer.strip()
                buffer = ""
            
            # If buffer gets too long, yield it anyway (reduced threshold)
            elif len(buffer) > 40:  # Reduced from 100 to 40
                # Try to break at a word boundary
                words = buffer.split()
                if len(words) > 1:
                    chunk = " ".join(words[:-1])
                    buffer = words[-1]
                    yield chunk.strip()
                else:
                    yield buffer.strip()
                    buffer = ""
        
        # Yield any remaining text
        if buffer.strip():
            yield buffer.strip()

# Global LLM service instance
llm_service = LLMService() 