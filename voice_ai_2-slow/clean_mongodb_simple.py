# clean_mongodb_simple.py - SIMPLIFIED FOR SYSTEM WITHOUT CALLER RECOGNITION
"""
SIMPLIFIED: Clean MongoDB data for simplified system (no caller profiles needed)
"""
import asyncio
import logging
from pymongo import AsyncMongoClient
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def clean_mongodb_simple():
    """Clean MongoDB collections for simplified system"""
    try:
        logger.info("🧹 Cleaning MongoDB for simplified system...")
        
        # Connect to MongoDB
        client = AsyncMongoClient(config.get_optimized_mongodb_url())
        db = client[config.mongodb_database]
        
        # Collections to clean (removed caller_profiles since we don't use caller recognition)
        collections_to_clean = [
            "call_sessions", 
            "conversation_items",
            "transcription_segments"
        ]
        
        total_deleted = 0
        for collection_name in collections_to_clean:
            collection = db[collection_name]
            
            # Count documents before deletion
            count_before = await collection.count_documents({})
            
            if count_before > 0:
                # Delete all documents in collection
                result = await collection.delete_many({})
                logger.info(f"✅ Cleaned {collection_name}: {result.deleted_count} documents deleted")
                total_deleted += result.deleted_count
            else:
                logger.info(f"ℹ️ {collection_name}: Already empty")
        
        # Close connection
        client.close()
        
        logger.info(f"🎉 MongoDB cleaned successfully! Total: {total_deleted} documents deleted")
        logger.info("💡 System is now fresh and ready")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to clean MongoDB: {e}")
        return False

async def clean_redis_cache():
    """Clean Redis cache as well"""
    try:
        logger.info("🧹 Cleaning Redis cache...")
        
        import redis.asyncio as redis
        r = redis.from_url(config.redis_url)
        
        # Get all voice AI related keys (removed user_profile patterns)
        voice_keys = await r.keys("voice_session:*")
        
        if voice_keys:
            deleted = await r.delete(*voice_keys)
            logger.info(f"✅ Redis cache: {deleted} keys deleted")
        else:
            logger.info(f"ℹ️ Redis cache: already empty")
        
        await r.close()
        return True
        
    except Exception as e:
        logger.warning(f"⚠️ Redis cleanup failed: {e}")
        return False

async def view_mongodb_data():
    """View current MongoDB data"""
    try:
        client = AsyncMongoClient(config.get_optimized_mongodb_url())
        db = client[config.mongodb_database]
        
        logger.info("📊 Current MongoDB Data:")
        logger.info("=" * 50)
        
        # Check each collection (removed caller_profiles)
        collections = ["call_sessions", "conversation_items", "transcription_segments"]
        
        for collection_name in collections:
            collection = db[collection_name]
            count = await collection.count_documents({})
            logger.info(f"{collection_name}: {count} documents")
            
            if collection_name == "call_sessions" and count > 0:
                # Show recent sessions
                async for session in collection.find().sort("start_time", -1).limit(3):
                    phone = session.get('phone_number', 'Unknown')
                    session_id = session.get('session_id', 'Unknown')
                    logger.info(f"  📞 {phone} -> {session_id}")
        
        client.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to view data: {e}")
        return False

async def main():
    """Main cleanup function"""
    print("🧹 SIMPLIFIED MONGODB CLEANUP")
    print("=" * 50)
    print("Simplified system (no caller recognition)")
    print("")
    
    while True:
        print("Options:")
        print("1. View current MongoDB data")
        print("2. Clean ALL data (complete reset)")
        print("3. Clean Redis cache only")
        print("4. Clean everything (MongoDB + Redis)")
        print("5. Exit")
        
        choice = input("\nChoose option (1-5): ").strip()
        
        if choice == "1":
            await view_mongodb_data()
            
        elif choice == "2":
            confirm = input("⚠️ This will delete ALL call data from MongoDB. Continue? [y/N]: ")
            if confirm.lower() == 'y':
                success = await clean_mongodb_simple()
                if success:
                    print("\n✅ Ready for fresh testing!")
                    break
            else:
                print("❌ Cancelled")
                
        elif choice == "3":
            confirm = input("⚠️ This will clear Redis cache. Continue? [y/N]: ")
            if confirm.lower() == 'y':
                success = await clean_redis_cache()
                if success:
                    print("\n✅ Redis cache cleared!")
            else:
                print("❌ Cancelled")
                
        elif choice == "4":
            confirm = input("⚠️ This will delete ALL data (MongoDB + Redis). Continue? [y/N]: ")
            if confirm.lower() == 'y':
                mongo_success = await clean_mongodb_simple()
                redis_success = await clean_redis_cache()
                if mongo_success:
                    print("\n✅ Complete cleanup finished!")
                    print("💡 System is now completely fresh")
                    break
            else:
                print("❌ Cancelled")
                
        elif choice == "5":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    asyncio.run(main())