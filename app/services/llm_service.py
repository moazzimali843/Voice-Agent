import asyncio
import logging
from typing import List, Optional
from openai import AsyncOpenAI
# Fix imports to work from any directory
try:
    from ..config import settings
    from ..models.schemas import LLMRequest, LLMResponse, KnowledgeChunk
except ImportError:
    from config import settings
    from models.schemas import LLMRequest, LLMResponse, KnowledgeChunk

logger = logging.getLogger(__name__)

class LLMService:
    """Service for Large Language Model operations using OpenAI API"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate_response(self, query: str, context_chunks: List[KnowledgeChunk]) -> Optional[LLMResponse]:
        """
        Generate response using OpenAI API with context from knowledge base
        
        Args:
            query: User's query
            context_chunks: Relevant knowledge base chunks
            
        Returns:
            LLMResponse object or None if error
        """
        try:
            # Build context from knowledge chunks
            context = self._build_context(context_chunks)
            
            # Create prompt
            prompt = self._create_prompt(query, context)
            
            # Generate response
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Answer questions based on the provided context. If the context doesn't contain relevant information, say so clearly."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.MAX_TOKENS,
                temperature=settings.TEMPERATURE,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            if response and response.choices and len(response.choices) > 0:
                message = response.choices[0].message
                if message and message.content:
                    llm_response = LLMResponse(
                        response=message.content.strip(),
                        tokens_used=response.usage.total_tokens if response.usage else 0,
                        model=settings.OPENAI_MODEL
                    )
                    
                    logger.info(f"Successfully generated LLM response for query: {query[:50]}...")
                    return llm_response
            
            logger.warning("No valid response received from OpenAI API")
            return None
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            return None
    
    async def generate_with_request(self, request: LLMRequest) -> Optional[LLMResponse]:
        """
        Generate response using LLMRequest object
        
        Args:
            request: LLMRequest object with query and context
            
        Returns:
            LLMResponse object or None if error
        """
        return await self.generate_response(
            query=request.query,
            context_chunks=request.context
        )
    
    def _build_context(self, context_chunks: List[KnowledgeChunk]) -> str:
        """
        Build context string from knowledge chunks
        
        Args:
            context_chunks: List of relevant knowledge chunks
            
        Returns:
            Formatted context string
        """
        if not context_chunks:
            return "No relevant context found."
        
        context_parts = []
        for i, chunk in enumerate(context_chunks[:5]):  # Limit to top 5 chunks
            context_parts.append(f"Context {i+1} (Source: {chunk.source}):\n{chunk.content}")
        
        return "\n\n".join(context_parts)
    
    def _create_prompt(self, query: str, context: str) -> str:
        """
        Create formatted prompt for the LLM
        
        Args:
            query: User's query
            context: Formatted context from knowledge base
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a helpful legal assistant with expertise in personal injury law, specifically car accidents and related cases. 

Your task is to answer the user's question using the provided context from legal documents and case criteria.

Instructions:
1. Carefully read through ALL the provided context sections
2. Look for information that relates to the user's question, even if it's not an exact match
3. Provide a comprehensive answer based on the available information
4. If you find relevant information, explain it clearly and reference the source
5. Only say information is not available if you truly cannot find anything related in the context

The context contains legal documents about case criteria, intake procedures, and accident classifications.

CONTEXT INFORMATION:
{context}

USER QUESTION:
{query}

RESPONSE:"""
        
        return prompt
    
    async def test_llm_connection(self) -> bool:
        """
        Test LLM service connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "user", "content": "Say 'test successful' if you can respond."}
                ],
                max_tokens=10,
                temperature=0
            )
            
            if response and response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                return content is not None and "test successful" in content.lower()
            
            return False
            
        except Exception as e:
            logger.error(f"LLM connection test failed: {str(e)}")
            return False
    
    async def summarize_text(self, text: str, max_length: int = 150) -> Optional[str]:
        """
        Summarize text using the LLM
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary
            
        Returns:
            Summarized text or None if error
        """
        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": f"Summarize the following text in {max_length} words or less. Be concise but capture the key points."},
                    {"role": "user", "content": text}
                ],
                max_tokens=max_length * 2,  # Rough estimate for tokens
                temperature=0.3
            )
            
            if response and response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                return content.strip() if content else None
            
            return None
            
        except Exception as e:
            logger.error(f"Error summarizing text: {str(e)}")
            return None
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation)
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4
    
    def validate_request(self, request: LLMRequest) -> bool:
        """
        Validate LLM request parameters
        
        Args:
            request: LLMRequest object to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not request.query or not request.query.strip():
            return False
        
        if request.max_tokens < 1 or request.max_tokens > 4000:
            return False
        
        if request.temperature < 0 or request.temperature > 2:
            return False
        
        return True

# Global LLM service instance
llm_service = LLMService() 