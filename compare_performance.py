#!/usr/bin/env python3
"""
Compare performance between old (wait for full response) vs new (streaming) methods
"""
import asyncio
import time
import uuid
from app.services.llm_service import llm_service
from app.services.tts_service import tts_service
from app.services.knowledge_service import knowledge_service

async def test_old_method():
    """Test the old method: wait for full response, then convert to speech"""
    
    print("🐌 Testing OLD Method (Full Response Then TTS)")
    print("=" * 60)
    
    # Create a test session
    session_id = str(uuid.uuid4())
    
    # Load knowledge base
    knowledge_service.load_knowledge_base(session_id)
    
    # Test query
    query = "Tell me about car accidents and case criteria"
    relevant_chunks = knowledge_service.search_knowledge(session_id, query)
    
    start_time = time.time()
    
    # Generate full response first
    print("⏳ Generating full response...")
    response_start = time.time()
    llm_response = await llm_service.generate_response(query, relevant_chunks)
    response_time = time.time() - response_start
    
    if llm_response:
        print(f"✅ Response generated in {response_time:.2f}s")
        print(f"   Response length: {len(llm_response.response)} characters")
        
        # Now convert entire response to speech
        print("⏳ Converting entire response to speech...")
        tts_start = time.time()
        tts_response = await tts_service.convert_text_to_speech(llm_response.response)
        tts_time = time.time() - tts_start
        
        if tts_response and tts_response.audio_data:
            print(f"✅ TTS completed in {tts_time:.2f}s")
            print(f"   Audio size: {len(tts_response.audio_data)} bytes")
        else:
            print("❌ TTS failed")
            tts_time = 0
    else:
        print("❌ Response generation failed")
    
    total_time = time.time() - start_time
    print(f"\n📊 OLD Method Results:")
    print(f"   - Response time: {response_time:.2f}s")
    print(f"   - TTS time: {tts_time:.2f}s")
    print(f"   - Total time: {total_time:.2f}s")
    print(f"   - Time to first audio: {total_time:.2f}s")
    
    # Clean up
    knowledge_service.clear_session_knowledge(session_id)
    
    return total_time, response_time + tts_time

async def test_new_method():
    """Test the new method: streaming response with immediate TTS"""
    
    print("\n🚀 Testing NEW Method (Streaming + Immediate TTS)")
    print("=" * 60)
    
    # Create a test session
    session_id = str(uuid.uuid4())
    
    # Load knowledge base
    knowledge_service.load_knowledge_base(session_id)
    
    # Test query
    query = "Tell me about car accidents and case criteria"
    relevant_chunks = knowledge_service.search_knowledge(session_id, query)
    
    start_time = time.time()
    first_audio_time = None
    
    try:
        # Start streaming response
        print("⏳ Starting streaming response...")
        text_stream = llm_service.generate_response_streaming(query, relevant_chunks)
        
        # Buffer and chunk the streaming text
        chunk_stream = llm_service.buffer_text_for_chunking(text_stream, min_chunk_size=15)
        
        chunk_count = 0
        total_audio_bytes = 0
        
        async for text_chunk in chunk_stream:
            if not text_chunk:
                continue
                
            chunk_count += 1
            print(f"📝 Chunk {chunk_count}: {text_chunk[:30]}...")
            
            # Convert chunk to speech immediately
            chunk_tts_start = time.time()
            audio_data = await tts_service.convert_text_chunk_to_speech(text_chunk)
            chunk_tts_time = time.time() - chunk_tts_start
            
            if audio_data:
                total_audio_bytes += len(audio_data)
                if first_audio_time is None:
                    first_audio_time = time.time() - start_time
                    print(f"🎯 First audio ready in {first_audio_time:.2f}s!")
                
                print(f"   ✅ Audio chunk {chunk_count} ready in {chunk_tts_time:.2f}s ({len(audio_data)} bytes)")
            else:
                print(f"   ❌ Failed to generate audio for chunk {chunk_count}")
        
        total_time = time.time() - start_time
        
        print(f"\n📊 NEW Method Results:")
        print(f"   - Total chunks: {chunk_count}")
        print(f"   - Total audio: {total_audio_bytes} bytes")
        print(f"   - Time to first audio: {first_audio_time:.2f}s")
        print(f"   - Total time: {total_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Error during streaming: {str(e)}")
        total_time = time.time() - start_time
        first_audio_time = total_time
    
    # Clean up
    knowledge_service.clear_session_knowledge(session_id)
    
    return total_time, first_audio_time

async def main():
    """Compare both methods"""
    
    print("🔥 Voice Agent Performance Comparison")
    print("=" * 70)
    
    # Test old method
    old_total, old_first_audio = await test_old_method()
    
    # Wait a bit between tests
    await asyncio.sleep(2)
    
    # Test new method
    new_total, new_first_audio = await test_new_method()
    
    # Compare results
    print("\n" + "=" * 70)
    print("🏆 PERFORMANCE COMPARISON")
    print("=" * 70)
    
    print(f"Time to First Audio:")
    print(f"  OLD Method: {old_first_audio:.2f}s")
    if new_first_audio is not None:
        print(f"  NEW Method: {new_first_audio:.2f}s")
        improvement = ((old_first_audio - new_first_audio) / old_first_audio) * 100
        print(f"  Improvement: {improvement:.1f}% faster! 🚀")
    else:
        print(f"  NEW Method: Failed to get first audio time")
    
    print(f"\nTotal Processing Time:")
    print(f"  OLD Method: {old_total:.2f}s")
    print(f"  NEW Method: {new_total:.2f}s")
    
    if new_first_audio is not None and new_first_audio < old_first_audio:
        print(f"\n✅ NEW Method wins! Users hear audio {old_first_audio - new_first_audio:.2f}s earlier!")
    else:
        print(f"\n❌ Something went wrong - old method was faster")
    
    print("\n🎯 Key Benefits of Streaming:")
    print("  • Users hear response immediately as it's generated")
    print("  • No waiting for complete response before audio starts")
    print("  • Better user experience with progressive audio")
    print("  • Lower perceived latency")

if __name__ == "__main__":
    asyncio.run(main()) 