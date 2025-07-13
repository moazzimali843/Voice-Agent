#!/usr/bin/env python3
"""
Debug script to test knowledge search functionality
"""
import uuid
from app.services.knowledge_service import knowledge_service

def test_knowledge_search():
    """Test the knowledge search with sample queries"""
    
    # Create a test session
    session_id = str(uuid.uuid4())
    
    print("Loading knowledge base...")
    success = knowledge_service.load_knowledge_base(session_id)
    
    if not success:
        print("❌ Failed to load knowledge base")
        return
    
    print("✅ Knowledge base loaded successfully")
    
    # Test queries
    test_queries = [
        "car accidents",
        "Hey. Tell me about the car accidents.",
        "vehicle crash",
        "auto accident criteria",
        "case acceptance",
        "injury claims"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        print("-" * 50)
        
        # Search for relevant chunks
        relevant_chunks = knowledge_service.search_knowledge(session_id, query, max_results=3)
        
        if relevant_chunks:
            print(f"Found {len(relevant_chunks)} relevant chunks:")
            for i, chunk in enumerate(relevant_chunks):
                print(f"\n📄 Chunk {i+1} (Score: {chunk.relevance_score:.2f})")
                print(f"Source: {chunk.source}")
                print(f"Content: {chunk.content[:200]}...")
                print()
        else:
            print("❌ No relevant chunks found")
    
    # Clean up
    knowledge_service.clear_session_knowledge(session_id)
    print("\n✅ Test completed")

if __name__ == "__main__":
    test_knowledge_search() 