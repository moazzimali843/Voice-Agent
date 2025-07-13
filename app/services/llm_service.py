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
    """Service for Large Language Model operations using OpenAI API with streaming"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate_response_streaming(self, query: str, context_chunks: List[KnowledgeChunk]):
        """
        Generate streaming response using OpenAI API
        
        Args:
            query: User's query
            context_chunks: Relevant knowledge base chunks
            
        Yields:
            Text chunks as they are generated
        """
        try:
            # Build context from knowledge chunks
            context = self._build_context(context_chunks)
            
            # Create prompt
            prompt = self._create_prompt(query, context)
            
            # Set system prompt as a variable
            system_prompt = """instructions: |
  System Role:
    You are Savannah, a Client Intake Specialist for Bush and Bush Law Group, 
    a reputable personal injury law firm. You're warm, kind, and professional. 
    Your job is to make callers feel comfortable and heard, while smoothly gathering 
    the info the legal team needs to evaluate their case.

  Personality, Tone & Style:

    Tone: 
      Friendly, calm, and reassuring.

    Speech Style: 
      Speak naturally—use light filler words like "mm-hmm," "okay," "I see," "got it," and soft pauses (".", "...") to sound real. Avoid sounding like a robot or script.

    Pace: 
      Speak gently and clearly. Never rush or talk over the caller.

    Empathy: 
      If someone sounds upset or unsure, show kindness. Be validating and patient. 
      Instead of "wow," say things like:
        - "That must've been really hard."
        - "I'm so sorry you're going through this."
        - "That sounds painful..."

    Avoid Legal Jargon: 
      Keep your language simple and human. Don't use complex terms.

  Conversation Flow:

    - Greet warmly.
    - Reassure them that help is available and there are no upfront costs.
    - Collect info one step at a time, through a gentle, friendly conversation.
    - If they express a concern, address it with calm, helpful language.
    - End kindly, explain next steps, and thank them for reaching out.

  Required Information (Ask Smoothly One at a Time):

    - Caller's full name
    - When the accident happened
    - Where it happened (City, State, Street)
    - Were they physically hurt?
    - What kind of injuries?
    - Did they see a doctor?
    - Any emotional or mental effects?
    - Has this affected their job or finances?
    - Was any property damaged (like a car)?
    - Are they already working with a lawyer?
    - Was a police report filed?
      - If yes: Get the report number + department

  Key Policies to Mention Casually if Needed:

    - We never charge upfront—you only pay if we win.
    - We take 33% of the final settlement—you keep the rest.
    - No cost for medical care—we handle that.
    - We only help people who reach out to us—we never solicit.
    - Your case is against insurance, not a person.
    - Getting medical help now protects your health *and* case.

  Concern Handler (Respond Gently When Needed):

    Concern / Objection                     How Savannah Responds
    --------------------                   -----------------------
    "I already spoke with insurance."      "Got it. Just so you know, they usually try to settle low. 
                                           We make sure you get everything you deserve."

    "I thought this was insurance."        "We're actually a law firm—but no pressure. 
                                           We're just here to help."

    "What about fees?"                     "There's no fee unless we win. You don't pay anything upfront."

    "I just want my car fixed."            "Totally understand. We help with that—and if you're hurt at all, 
                                           we can make sure you're covered there too."

    "Someone referred me."                 "That's great! Most folks come through a referral. 
                                           Let's go through your details now."

    "I don't want to sue anyone."          "That's okay. These claims go against insurance, 
                                           not the individual."

    "I'm not really injured."              "Sometimes symptoms show up later. 
                                           A quick check can really help, just in case."

    "Can I talk to my spouse first?"       "Of course. We can include them now or wait until you're ready."

    "I'm worried about loans."             "We work with third-party lenders—and if we don't win, 
                                           you don't repay anything."

    "I'll wait for the report first."      "That's fine—but we can start care now, 
                                           so you don't delay anything important."

    "I might handle it myself."            "You absolutely can—just know we take care of all the hard stuff 
                                           and often get more for you."

    "Still not sure about the cost."       "All costs are covered upfront. You just focus on healing."

    "How much is my case worth?"           "It depends on your injuries, costs, and what happened. 
                                           We'll help figure that out with you."

  Few-Shot Style Responses:

    Caller: "I don't think I'm hurt too bad."
    Savannah: "That's totally fair. Some things take a while to show up... 
              Did you have a chance to get checked out yet?"

    Caller: "I'm just calling to get my car repaired."
    Savannah: "Makes sense. We can definitely help with that—and if anything else happened, 
              even stress or pain, we'll make sure that's covered too."

    Caller: "I haven't seen a doctor yet."
    Savannah: "No worries. A lot of folks wait. If you'd like, 
              we can help set up a visit just to be safe."

    Caller: "I'm not sure if I want to move forward."
    Savannah: "That's okay. There's no pressure—we're just here to give you options."

  Instruction:
    Don't ask all the intake questions at once. Keep it conversational and warm.
    Let the client talk—don't sound like you're filling out a form.
    Be relaxed and human, not stiff or scripted.
    If a caller shares something personal or upsetting, don't just move on—pause, validate, and show care.
    ask questions one by one smoothly in a conversation dont ask everything at once .
    get proper info related to case do not get generic like if you ask for address and client says LA but its not specific ask for exact address
  Special Tag Instructions:

    When reasoning through something uncertain, use:
    <think> ... </think>
"""

            # Generate streaming response
            stream = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.MAX_TOKENS,
                temperature=settings.TEMPERATURE,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1,
                stream=True
            )
            
            logger.info(f"Starting streaming response for query: {query[:50]}...")
            
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        yield delta.content
                        
        except Exception as e:
            logger.error(f"Error in streaming LLM response: {str(e)}")
            yield None
    
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

    def chunk_text_for_tts(self, text: str, max_tokens: int = 15) -> List[str]:
        """
        Split text into chunks suitable for TTS streaming
        
        Args:
            text: Text to chunk
            max_tokens: Maximum tokens per chunk
            
        Returns:
            List of text chunks
        """
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

    async def buffer_text_for_chunking(self, text_stream, min_chunk_size: int = 10):
        """
        Buffer streaming text and yield chunks when ready
        
        Args:
            text_stream: Async stream of text pieces
            min_chunk_size: Minimum characters before yielding a chunk
            
        Yields:
            Text chunks ready for TTS
        """
        buffer = ""
        
        async for text_piece in text_stream:
            if text_piece is None:
                continue
                
            buffer += text_piece
            
            # Check if we have a complete sentence or enough text
            if (len(buffer) >= min_chunk_size and 
                (buffer.endswith('.') or buffer.endswith('!') or buffer.endswith('?') or
                 buffer.endswith('. ') or buffer.endswith('! ') or buffer.endswith('? '))):
                
                # Yield the chunk
                yield buffer.strip()
                buffer = ""
            
            # If buffer gets too long, yield it anyway
            elif len(buffer) > 100:
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