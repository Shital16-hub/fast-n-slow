import asyncio
from simple_rag_v2 import simplified_rag

async def test_towing_queries():
    print("Testing Towing RAG System")
    print("=" * 40)
    
    await simplified_rag.initialize()
    
    # Test different towing queries
    towing_queries = [
        "towing",
        "towing cost", 
        "towing price",
        "car towing",
        "vehicle towing",
        "heavy duty towing",
        "light duty towing",
        "truck towing",
        "motorcycle towing", 
        "flatbed towing",
        "emergency towing",
        "towing service"
    ]
    
    for query in towing_queries:
        result = await simplified_rag.retrieve_context(query, max_results=2)
        print(f"Query: '{query}'")
        print(f"Result: {result}")
        print("-" * 50)
    
    # Test what your agent would search for
    print("\nAGENT QUERIES:")
    agent_queries = [
        "towing standard pricing cost rate",
        "towing heavy_duty pricing cost rate"
    ]
    
    for query in agent_queries:
        result = await simplified_rag.retrieve_context(query, max_results=2)
        print(f"Agent Query: '{query}'")
        print(f"Result: {result}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_towing_queries())