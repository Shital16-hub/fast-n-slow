# clean_mongodb_fresh_caller.py - FOR MONGODB-ONLY SYSTEM
"""
Clean MongoDB data to test as fresh caller (MongoDB-Only Version)
"""
import asyncio
import logging
from pymongo import AsyncMongoClient
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def clean_mongodb_for_testing():
    """Clean MongoDB collections for fresh testing"""
    try:
        logger.info("🧹 Cleaning MongoDB for fresh caller testing...")
        
        # Connect to MongoDB
        client = AsyncMongoClient(config.get_optimized_mongodb_url())
        db = client[config.mongodb_database]
        
        # Collections to clean
        collections_to_clean = [
            "caller_profiles",
            "call_sessions", 
            "conversation_items",
            "transcription_segments"
        ]
        
        for collection_name in collections_to_clean:
            collection = db[collection_name]
            
            # Count documents before deletion
            count_before = await collection.count_documents({})
            
            if count_before > 0:
                # Delete all documents in collection
                result = await collection.delete_many({})
                logger.info(f"✅ Cleaned {collection_name}: {result.deleted_count} documents deleted")
            else:
                logger.info(f"ℹ️ {collection_name}: Already empty")
        
        # Close connection
        client.close()
        
        logger.info("🎉 MongoDB cleaned successfully!")
        logger.info("💡 Now you can test as a fresh caller")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to clean MongoDB: {e}")
        return False

async def clean_specific_phone_number(phone_number: str):
    """Clean data for a specific phone number only"""
    try:
        logger.info(f"🧹 Cleaning data for phone number: {phone_number}")
        
        client = AsyncMongoClient(config.get_optimized_mongodb_url())
        db = client[config.mongodb_database]
        
        # Find caller profile for this phone number
        caller_profile = await db.caller_profiles.find_one({"phone_number": phone_number})
        
        if not caller_profile:
            logger.info("ℹ️ No data found for this phone number")
            client.close()
            return True
        
        caller_id = caller_profile["caller_id"]
        logger.info(f"📱 Found caller_id: {caller_id}")
        
        # Delete related data
        collections_and_queries = [
            ("caller_profiles", {"phone_number": phone_number}),
            ("call_sessions", {"phone_number": phone_number}),
            ("conversation_items", {"caller_id": caller_id}),
            ("transcription_segments", {"caller_id": caller_id})
        ]
        
        total_deleted = 0
        for collection_name, query in collections_and_queries:
            collection = db[collection_name]
            result = await collection.delete_many(query)
            if result.deleted_count > 0:
                logger.info(f"✅ {collection_name}: {result.deleted_count} documents deleted")
                total_deleted += result.deleted_count
        
        client.close()
        
        logger.info(f"🎉 Cleaned {total_deleted} total documents for {phone_number}")
        logger.info("💡 This phone number will now be treated as new caller")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to clean phone number data: {e}")
        return False

async def view_mongodb_data():
    """View current MongoDB data"""
    try:
        client = AsyncMongoClient(config.get_optimized_mongodb_url())
        db = client[config.mongodb_database]
        
        logger.info("📊 Current MongoDB Data:")
        logger.info("=" * 50)
        
        # Check each collection
        collections = ["caller_profiles", "call_sessions", "conversation_items", "transcription_segments"]
        
        for collection_name in collections:
            collection = db[collection_name]
            count = await collection.count_documents({})
            logger.info(f"{collection_name}: {count} documents")
            
            if collection_name == "caller_profiles" and count > 0:
                # Show caller profiles
                async for profile in collection.find().limit(5):
                    logger.info(f"  📱 {profile.get('phone_number')} -> {profile.get('caller_id')} ({profile.get('total_calls', 0)} calls)")
        
        client.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to view data: {e}")
        return False

async def clean_redis_cache():
    """Clean Redis cache as well"""
    try:
        logger.info("🧹 Cleaning Redis cache...")
        
        import redis.asyncio as redis
        r = redis.from_url(config.redis_url)
        
        # Get all voice AI related keys
        voice_keys = await r.keys("voice_session:*")
        profile_keys = await r.keys("user_profile:*")
        history_keys = await r.keys("history_*")
        
        all_keys = voice_keys + profile_keys + history_keys
        
        if all_keys:
            deleted = await r.delete(*all_keys)
            logger.info(f"✅ Redis cache: {deleted} keys deleted")
        else:
            logger.info(f"ℹ️ Redis cache: already empty")
        
        await r.close()
        return True
        
    except Exception as e:
        logger.warning(f"⚠️ Redis cleanup failed: {e}")
        return False

async def main():
    """Main cleanup function"""
    print("🧹 MONGODB-ONLY FRESH CALLER CLEANUP")
    print("=" * 50)
    print("This will help you test as a fresh caller")
    print("MongoDB-Only Version (No SQLite)")
    print("")
    
    while True:
        print("Options:")
        print("1. View current MongoDB data")
        print("2. Clean ALL data (complete reset)")
        print("3. Clean specific phone number only")
        print("4. Clean Redis cache only")
        print("5. Clean everything (MongoDB + Redis)")
        print("6. Exit")
        
        choice = input("\nChoose option (1-6): ").strip()
        
        if choice == "1":
            await view_mongodb_data()
            
        elif choice == "2":
            confirm = input("⚠️ This will delete ALL call data from MongoDB. Continue? [y/N]: ")
            if confirm.lower() == 'y':
                success = await clean_mongodb_for_testing()
                if success:
                    print("\n✅ Ready for fresh testing!")
                    break
            else:
                print("❌ Cancelled")
                
        elif choice == "3":
            phone_number = input("Enter phone number to clean (e.g., +18188395060): ").strip()
            if phone_number:
                success = await clean_specific_phone_number(phone_number)
                if success:
                    print(f"\n✅ {phone_number} will be treated as new caller!")
                    break
            else:
                print("❌ Invalid phone number")
                
        elif choice == "4":
            confirm = input("⚠️ This will clear Redis cache. Continue? [y/N]: ")
            if confirm.lower() == 'y':
                success = await clean_redis_cache()
                if success:
                    print("\n✅ Redis cache cleared!")
            else:
                print("❌ Cancelled")
                
        elif choice == "5":
            confirm = input("⚠️ This will delete ALL data (MongoDB + Redis). Continue? [y/N]: ")
            if confirm.lower() == 'y':
                mongo_success = await clean_mongodb_for_testing()
                redis_success = await clean_redis_cache()
                if mongo_success:
                    print("\n✅ Complete cleanup finished!")
                    print("💡 System is now completely fresh")
                    break
            else:
                print("❌ Cancelled")
                
        elif choice == "6":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    asyncio.run(main())