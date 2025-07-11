#!/usr/bin/env python3
"""
Test script to verify streaming functionality
"""
import asyncio
import uuid
from app.services.llm_service import llm_service
from app.services.tts_service import tts_service
from app.services.knowledge_service import knowledge_service

async def test_streaming():
    """Test the streaming functionality"""
    
    print("🔄 Testing Streaming Functionality")
    print("=" * 50)
    
    # Create a test session
    session_id = str(uuid.uuid4())
    
    # Load knowledge base
    print("📚 Loading knowledge base...")
    success = knowledge_service.load_knowledge_base(session_id)
    
    if not success:
        print("❌ Failed to load knowledge base")
        return
    
    print("✅ Knowledge base loaded")
    
    # Test query
    query = "Tell me about car accidents and case criteria"
    print(f"\n🔍 Testing streaming for query: '{query}'")
    
    # Search knowledge base
    print("🔎 Searching knowledge base...")
    relevant_chunks = knowledge_service.search_knowledge(session_id, query)
    print(f"✅ Found {len(relevant_chunks)} relevant chunks")
    
    # Test LLM streaming
    print("\n🤖 Testing LLM streaming...")
    print("-" * 30)
    
    try:
        text_stream = llm_service.generate_response_streaming(query, relevant_chunks)
        
        # Test text buffering and chunking
        print("📝 Streaming text chunks:")
        chunk_stream = llm_service.buffer_text_for_chunking(text_stream, min_chunk_size=15)
        
        chunk_count = 0
        full_response = ""
        
        async for text_chunk in chunk_stream:
            if not text_chunk:
                continue
                
            chunk_count += 1
            full_response += text_chunk + " "
            
            print(f"  Chunk {chunk_count}: {text_chunk[:50]}...")
            
            # Test TTS for each chunk
            print(f"  🔊 Converting chunk {chunk_count} to speech...")
            audio_data = await tts_service.convert_text_chunk_to_speech(text_chunk)
            
            if audio_data:
                print(f"  ✅ Audio generated for chunk {chunk_count} ({len(audio_data)} bytes)")
            else:
                print(f"  ❌ Failed to generate audio for chunk {chunk_count}")
            
            # Small delay to simulate real-time processing
            await asyncio.sleep(0.1)
        
        print(f"\n📊 Streaming Results:")
        print(f"  - Total chunks: {chunk_count}")
        print(f"  - Full response length: {len(full_response)} characters")
        print(f"  - Response preview: {full_response[:100]}...")
        
    except Exception as e:
        print(f"❌ Error during streaming: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Clean up
    knowledge_service.clear_session_knowledge(session_id)
    print("\n✅ Streaming test completed")

async def test_chunking():
    """Test text chunking functionality"""
    
    print("\n🔄 Testing Text Chunking")
    print("=" * 50)
    
    # Sample long text
    sample_text = """
    Car accidents can result in serious injuries and require immediate legal attention. 
    The case criteria for accepting car accident cases include several factors. 
    First, the severity of the accident must meet our minimum threshold. 
    Second, there must be clear evidence of negligence by the other party. 
    Third, the client must have sustained documentable injuries. 
    Finally, the case must have sufficient potential value to justify our involvement.
    """
    
    print("📝 Original text:")
    print(sample_text.strip())
    
    # Test chunking
    chunks = llm_service.chunk_text_for_tts(sample_text.strip(), max_tokens=20)
    
    print(f"\n✂️ Text split into {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        token_count = llm_service.estimate_tokens(chunk)
        print(f"  Chunk {i+1} ({token_count} tokens): {chunk}")
    
    print("\n✅ Chunking test completed")

async def main():
    """Run all tests"""
    await test_chunking()
    await test_streaming()

if __name__ == "__main__":
    asyncio.run(main()) 