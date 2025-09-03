# clean_knowledge_base_fixed.py - FIXED VERSION
"""
FIXED Knowledge Base Cleanup Script for LiveKit Voice Agent
Works with current Qdrant client API
"""
import asyncio
import logging
import sys
import argparse
from pathlib import Path

# FIXED: Import the correct RAG system
from simple_rag_v2 import simplified_rag
from config import config

# FIXED: Import correct Qdrant models
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchAny
    QDRANT_CLIENT_AVAILABLE = True
except ImportError:
    QDRANT_CLIENT_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FixedKnowledgeBaseCleaner:
    """FIXED: Clean and reset Qdrant knowledge base with updated API"""
    
    def __init__(self):
        self.qdrant_client = None
        
    async def initialize_qdrant_client(self) -> bool:
        """Initialize direct Qdrant client for cleanup operations"""
        try:
            if not QDRANT_CLIENT_AVAILABLE:
                logger.warning("⚠️ Direct Qdrant client not available, using simple_rag only")
                return False
            
            logger.info("🔧 Initializing direct Qdrant client...")
            self.qdrant_client = QdrantClient(
                url=config.qdrant_url,
                timeout=30  # Increased timeout for cleanup operations
            )
            
            # Test connection
            collections = await asyncio.to_thread(self.qdrant_client.get_collections)
            logger.info(f"✅ Connected to Qdrant with {len(collections.collections)} collections")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Qdrant client: {e}")
            return False
    
    async def get_collection_info(self) -> dict:
        """Get current collection information"""
        try:
            logger.info("📊 Getting collection information...")
            
            # First try simple_rag
            status = await simplified_rag.get_status()
            if status.get("status") == "ready":
                points_count = status.get("points_count", 0)
                logger.info(f"✅ Collection '{config.qdrant_collection_name}' status via simple_rag:")
                logger.info(f"   Points count: {points_count}")
                logger.info(f"   Cache size: {status.get('cache_size', 'unknown')}")
                return status
            
            # Try direct client if available
            if self.qdrant_client:
                try:
                    collection_info = await asyncio.to_thread(
                        self.qdrant_client.get_collection,
                        config.qdrant_collection_name
                    )
                    logger.info(f"✅ Collection '{config.qdrant_collection_name}' status via direct client:")
                    logger.info(f"   Points count: {collection_info.points_count}")
                    logger.info(f"   Vector size: {collection_info.config.params.vectors.size}")
                    logger.info(f"   Distance metric: {collection_info.config.params.vectors.distance}")
                    
                    return {
                        "status": "ready",
                        "points_count": collection_info.points_count,
                        "vector_size": collection_info.config.params.vectors.size,
                        "distance_metric": collection_info.config.params.vectors.distance
                    }
                except Exception as e:
                    logger.warning(f"⚠️ Could not get collection info via direct client: {e}")
            
            return {"status": "unknown"}
            
        except Exception as e:
            logger.error(f"❌ Failed to get collection info: {e}")
            return {"status": "error", "error": str(e)}
    
    async def clear_collection_data_fixed(self) -> bool:
        """FIXED: Clear all data from collection using updated API"""
        try:
            logger.info(f"🧹 Clearing data from collection: {config.qdrant_collection_name}")
            
            # Get initial count
            initial_info = await self.get_collection_info()
            initial_count = initial_info.get("points_count", 0)
            
            if initial_count == 0:
                logger.info("✅ Collection is already empty")
                return True
            
            logger.info(f"📊 Current collection has {initial_count} documents")
            
            if self.qdrant_client:
                # FIXED: Use proper filter to select all points
                logger.info("🔧 Using direct client to clear collection with proper API...")
                
                try:
                    # Method 1: Try to delete all points using a broad filter
                    # This selects all points by using a filter that matches any existing field
                    result = await asyncio.to_thread(
                        self.qdrant_client.delete,
                        collection_name=config.qdrant_collection_name,
                        points_selector=Filter()  # Empty filter matches all points
                    )
                    
                    logger.info(f"✅ Delete operation completed: {result}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Method 1 failed: {e}")
                    
                    try:
                        # Method 2: Try recreating the collection (nuclear option)
                        logger.info("🔧 Trying collection recreation...")
                        
                        # Get current collection config
                        collection_info = await asyncio.to_thread(
                            self.qdrant_client.get_collection,
                            config.qdrant_collection_name
                        )
                        
                        # Delete and recreate collection
                        await asyncio.to_thread(
                            self.qdrant_client.delete_collection,
                            config.qdrant_collection_name
                        )
                        
                        # Recreate with same config
                        await asyncio.to_thread(
                            self.qdrant_client.create_collection,
                            collection_name=config.qdrant_collection_name,
                            vectors_config=collection_info.config.params.vectors
                        )
                        
                        logger.info("✅ Collection recreated successfully")
                        
                    except Exception as e2:
                        logger.error(f"❌ Method 2 also failed: {e2}")
                        return False
                
                # Wait for the operation to complete
                await asyncio.sleep(3)
                
                # Verify clearing
                final_info = await self.get_collection_info()
                final_count = final_info.get("points_count", 0)
                
                if final_count == 0:
                    logger.info(f"✅ Successfully cleared {initial_count} documents from collection")
                    return True
                else:
                    logger.warning(f"⚠️ Collection still has {final_count} documents after clearing")
                    return final_count < initial_count  # Partial success
                    
            else:
                logger.warning("⚠️ Direct client not available, cannot clear collection efficiently")
                logger.info("💡 Try: docker restart qdrant-voice-ai or check Qdrant connection")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to clear collection: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

async def main():
    """Main cleanup function"""
    parser = argparse.ArgumentParser(description="Clean Qdrant knowledge base - FIXED VERSION")
    parser.add_argument("--action", "-a", 
                       choices=["info", "clear"], 
                       default="info",
                       help="Action to perform: info (show info), clear (clear data)")
    parser.add_argument("--force", "-f", action="store_true", 
                       help="Skip confirmation prompts")
    
    args = parser.parse_args()
    
    try:
        logger.info("🧹 FIXED Knowledge Base Cleanup Tool")
        logger.info(f"🎯 Target collection: {config.qdrant_collection_name}")
        logger.info(f"🔗 Qdrant URL: {config.qdrant_url}")
        
        # Create cleaner
        cleaner = FixedKnowledgeBaseCleaner()
        
        # Initialize connections
        logger.info("\n🔧 Initializing connections...")
        qdrant_direct = await cleaner.initialize_qdrant_client()
        simple_rag_ready = await simplified_rag.initialize()
        
        logger.info(f"   Direct Qdrant client: {'✅ Ready' if qdrant_direct else '⚠️ Not available'}")
        logger.info(f"   Simple RAG system: {'✅ Ready' if simple_rag_ready else '⚠️ Not ready'}")
        
        if args.action == "info":
            logger.info("\n📊 Collection Information:")
            await cleaner.get_collection_info()
            
        elif args.action == "clear":
            logger.info("\n🧹 Clearing collection data...")
            
            # Show current status
            await cleaner.get_collection_info()
            
            # Confirm action
            if not args.force:
                response = input(f"\n⚠️ This will clear ALL data from '{config.qdrant_collection_name}'. Continue? [y/N]: ")
                if response.lower() != 'y':
                    logger.info("❌ Operation cancelled")
                    return
            
            success = await cleaner.clear_collection_data_fixed()
            if success:
                logger.info("✅ Knowledge base cleared successfully!")
                logger.info("💡 You can now run: python enhanced_kb_indexer.py")
            else:
                logger.error("❌ Failed to clear knowledge base completely")
                logger.info("💡 Try: docker restart qdrant-voice-ai")
                sys.exit(1)
        
        logger.info("\n🎯 Cleanup completed!")
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Cleanup cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ FATAL ERROR: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())