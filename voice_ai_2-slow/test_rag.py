# test_rag_fixed.py - FIXED VERSION
import asyncio
from simple_rag_v2 import simplified_rag

async def main():
    print("🧪 Testing RAG System")
    print("=" * 50)
    
    # CRITICAL FIX: Force initialization first
    print("🔧 Initializing RAG system...")
    init_success = await simplified_rag.initialize()
    
    if not init_success:
        print("❌ RAG initialization failed!")
        return
    
    print("✅ RAG system initialized successfully!")
    
    # Test queries from your service docs
    test_queries = [
        "towing cost",
        "battery service price", 
        "tire change fee",
        "heavy duty towing",
        "motorcycle towing",
        "fuel delivery",
        "lockout service",
        "emergency towing",
        "luxury car towing",
        "semi truck help"
    ]
    
    print("\n🔍 Testing Queries:")
    print("-" * 30)
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        result = await simplified_rag.retrieve_context(query, max_results=2)
        
        if result:
            print(f"✅ Result: {result}")
        else:
            print("❌ No result found")
    
    print("\n📊 Final RAG System Status:")
    status = await simplified_rag.get_status()
    print(status)

if __name__ == "__main__":
    asyncio.run(main())