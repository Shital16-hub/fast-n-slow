import asyncio
from simple_rag_v2 import simplified_rag

async def test_fuel_delivery():
    print("🔍 Testing Fuel Delivery RAG")
    
    await simplified_rag.initialize()
    
    # Test the exact query from your logs
    result = await simplified_rag.retrieve_context("heavy-duty fuel delivery", max_results=3)
    print(f"Query: 'heavy-duty fuel delivery'")
    print(f"Result: {result}")
    print()
    
    # Test other fuel queries
    queries = [
        "fuel delivery cost",
        "gas delivery price",
        "diesel fuel service",
        "emergency fuel delivery"
    ]
    
    for query in queries:
        result = await simplified_rag.retrieve_context(query, max_results=2)
        print(f"Query: '{query}'")
        print(f"Result: {result}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_fuel_delivery())