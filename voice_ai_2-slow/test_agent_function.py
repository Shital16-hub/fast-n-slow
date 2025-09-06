import asyncio
from agents.dispatcher import OptimizedIntelligentDispatcherAgent
from models.call_data import CallData
from simple_rag_v2 import simplified_rag

async def test_agent_search():
    print("🔧 Initializing RAG system...")
    
    # CRITICAL: Initialize RAG first
    rag_ready = await simplified_rag.initialize()
    if not rag_ready:
        print("❌ RAG initialization failed!")
        return
    
    print("✅ RAG system ready")
    
    # Create test data
    call_data = CallData()
    call_data.session_id = "test_session"
    call_data.caller_id = "test_caller"
    call_data.service_type = "lockout"
    call_data.vehicle_class = "standard"
    
    # Create agent
    agent = OptimizedIntelligentDispatcherAgent(call_data)
    
    # Create mock context
    class MockContext:
        def __init__(self):
            self.userdata = call_data
    
    mock_context = MockContext()
    
    # Test the search function directly
    print("🔍 Testing lockout service search...")
    result = await agent.search_knowledge(mock_context, "lockout service price")
    print(f"Agent search result: {result}")
    
    # Test with different query
    print("\n🔍 Testing direct lockout query...")
    rag_result = await simplified_rag.retrieve_context("lockout service cost", max_results=2)
    print(f"Direct RAG result: {rag_result}")

if __name__ == "__main__":
    asyncio.run(test_agent_search())