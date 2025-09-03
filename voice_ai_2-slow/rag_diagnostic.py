# rag_diagnostic.py - Complete RAG System Diagnostic
"""
Complete diagnostic for RAG system issues
"""
import asyncio
import logging
import traceback
from pathlib import Path

# Setup logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def diagnose_rag_system():
    """Complete RAG system diagnosis"""
    
    print("🔧 RAG SYSTEM DIAGNOSTIC")
    print("=" * 50)
    
    # Step 1: Check configuration
    print("\n1️⃣ CHECKING CONFIGURATION")
    try:
        from config import config
        print(f"✅ Config loaded")
        print(f"   Qdrant URL: {config.qdrant_url}")
        print(f"   Collection: {config.qdrant_collection_name}")
        print(f"   OpenAI Key: {'✅ Set' if config.openai_api_key else '❌ Missing'}")
        print(f"   Embedding Model: {config.embedding_model}")
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False
    
    # Step 2: Check Qdrant connection
    print("\n2️⃣ CHECKING QDRANT CONNECTION")
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(url=config.qdrant_url, timeout=10)
        
        # Test connection
        collections = client.get_collections()
        print(f"✅ Qdrant connected")
        print(f"   Collections: {len(collections.collections)}")
        
        # Check our specific collection
        collection_exists = False
        points_count = 0
        
        for collection in collections.collections:
            if collection.name == config.qdrant_collection_name:
                collection_exists = True
                collection_info = client.get_collection(config.qdrant_collection_name)
                points_count = collection_info.points_count
                print(f"✅ Collection '{config.qdrant_collection_name}' exists")
                print(f"   Points: {points_count}")
                break
        
        if not collection_exists:
            print(f"❌ Collection '{config.qdrant_collection_name}' not found")
            print("   Available collections:")
            for collection in collections.collections:
                print(f"     - {collection.name}")
            return False
        
        if points_count == 0:
            print(f"❌ Collection '{config.qdrant_collection_name}' is empty")
            print("   You need to index your documents first")
            return False
            
    except Exception as e:
        print(f"❌ Qdrant connection failed: {e}")
        print(f"   Make sure Qdrant is running: docker ps")
        return False
    
    # Step 3: Check OpenAI connection
    print("\n3️⃣ CHECKING OPENAI CONNECTION")
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=config.openai_api_key)
        
        # Test embedding
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input="test",
            dimensions=512
        )
        print(f"✅ OpenAI embeddings working")
        print(f"   Embedding dimensions: {len(response.data[0].embedding)}")
        
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        return False
    
    # Step 4: Test RAG initialization
    print("\n4️⃣ TESTING RAG INITIALIZATION")
    try:
        from simple_rag_v2 import simplified_rag
        
        # Force initialization
        success = await simplified_rag.initialize()
        
        if success:
            print("✅ RAG system initialized")
            
            # Get detailed status
            status = await simplified_rag.get_status()
            print(f"   Status: {status}")
            
            # Test a simple query
            print("\n5️⃣ TESTING SIMPLE QUERY")
            result = await simplified_rag.retrieve_context("towing", max_results=1)
            
            if result:
                print(f"✅ Query test successful")
                print(f"   Result: {result[:100]}...")
                return True
            else:
                print(f"❌ Query returned no results")
                return False
        else:
            print("❌ RAG initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ RAG initialization error: {e}")
        traceback.print_exc()
        return False

async def check_service_docs():
    """Check if service documentation exists"""
    print("\n📁 CHECKING SERVICE DOCUMENTATION")
    
    services_dir = Path("services_docs")
    if not services_dir.exists():
        print(f"❌ services_docs/ directory not found")
        return False
    
    service_files = list(services_dir.glob("*.txt"))
    print(f"✅ Found {len(service_files)} service files")
    
    if len(service_files) == 0:
        print("❌ No service files found in services_docs/")
        return False
    
    # Show some examples
    for i, file in enumerate(service_files[:5]):
        print(f"   - {file.name}")
    
    if len(service_files) > 5:
        print(f"   ... and {len(service_files) - 5} more")
    
    return True

async def suggest_fixes():
    """Suggest fixes based on what we found"""
    print("\n🔧 SUGGESTED FIXES")
    print("=" * 30)
    
    # Check if we have documentation
    has_docs = await check_service_docs()
    
    if not has_docs:
        print("1. Create service documentation:")
        print("   mkdir -p services_docs")
        print("   # Add your .txt service files to services_docs/")
        return
    
    print("1. Start Qdrant if not running:")
    print("   docker-compose up -d qdrant")
    print()
    
    print("2. Index your documents:")
    print("   python enhanced_kb_indexer.py")
    print()
    
    print("3. Test again:")
    print("   python test_rag.py")

async def main():
    """Main diagnostic function"""
    success = await diagnose_rag_system()
    
    if not success:
        await suggest_fixes()
    else:
        print("\n🎉 RAG SYSTEM IS WORKING!")
        print("You can now test with queries like:")
        print("  - 'towing cost'")
        print("  - 'battery service'")
        print("  - 'tire change'")

if __name__ == "__main__":
    asyncio.run(main())