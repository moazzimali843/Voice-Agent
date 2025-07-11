#!/usr/bin/env python3
"""
Test script to verify audio queue functionality
"""
import asyncio
import time
from app.services.tts_service import tts_service

async def test_audio_queue():
    """Test creating multiple audio chunks to verify sequential playback"""
    
    print("🎵 Testing Audio Queue Functionality")
    print("=" * 50)
    
    # Test phrases that should play sequentially
    test_phrases = [
        "This is the first audio chunk.",
        "This is the second audio chunk.",
        "This is the third audio chunk.",
        "This is the fourth and final chunk."
    ]
    
    print("📝 Creating audio chunks...")
    audio_chunks = []
    
    for i, phrase in enumerate(test_phrases):
        print(f"🔊 Generating audio for chunk {i+1}: {phrase}")
        
        start_time = time.time()
        audio_data = await tts_service.convert_text_chunk_to_speech(phrase)
        generation_time = time.time() - start_time
        
        if audio_data:
            audio_chunks.append({
                'number': i + 1,
                'phrase': phrase,
                'audio_size': len(audio_data),
                'generation_time': generation_time
            })
            print(f"  ✅ Generated in {generation_time:.2f}s ({len(audio_data)} bytes)")
        else:
            print(f"  ❌ Failed to generate audio")
    
    print(f"\n📊 Results:")
    print(f"  - Total chunks created: {len(audio_chunks)}")
    print(f"  - Average generation time: {sum(c['generation_time'] for c in audio_chunks) / len(audio_chunks):.2f}s")
    print(f"  - Total audio size: {sum(c['audio_size'] for c in audio_chunks)} bytes")
    
    print(f"\n🎯 Audio Queue Test Complete!")
    print(f"These chunks should play sequentially in the browser:")
    for i, chunk in enumerate(audio_chunks):
        print(f"  {i+1}. {chunk['phrase']} ({chunk['audio_size']} bytes)")
    
    print(f"\n💡 To test:")
    print(f"  1. Start the app: python run.py")
    print(f"  2. Ask a question about car accidents")
    print(f"  3. Watch the browser console for sequential audio playback")
    print(f"  4. Each chunk should play one after another, not simultaneously")

if __name__ == "__main__":
    asyncio.run(test_audio_queue()) 