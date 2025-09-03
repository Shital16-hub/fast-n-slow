# complete_cleanup.py
"""
COMPLETE SYSTEM CLEANUP - Clean ALL caches and databases
This will make the system treat everyone as a new caller
"""
import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def clean_mongodb_completely():
    """Clean MongoDB completely"""
    try:
        from pymongo import AsyncMongoClient
        from config import config
        
        logger.info("🧹 Cleaning MongoDB completely...")
        
        client = AsyncMongoClient(config.get_optimized_mongodb_url())
        db = client[config.mongodb_database]
        
        # Collections to clean
        collections_to_clean = [
            "caller_profiles",
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
                logger.info(f"✅ MongoDB {collection_name}: {result.deleted_count} documents deleted")
                total_deleted += result.deleted_count
            else:
                logger.info(f"ℹ️ MongoDB {collection_name}: Already empty")
        
        # Close connection
        client.close()
        
        logger.info(f"✅ MongoDB: Total {total_deleted} documents deleted")
        return True
        
    except Exception as e:
        logger.error(f"❌ MongoDB cleanup failed: {e}")
        return False

async def clean_redis_completely():
    """Clean Redis cache completely"""
    try:
        import redis.asyncio as redis
        from config import config
        
        logger.info("🧹 Cleaning Redis cache completely...")
        
        r = redis.from_url(config.redis_url)
        
        # Get all voice AI related keys
        patterns_to_clean = [
            "voice_session:*",
            "user_profile:*", 
            "history_*",
            "*caller*",
            "*session*",
            "*profile*"
        ]
        
        total_deleted = 0
        for pattern in patterns_to_clean:
            keys = await r.keys(pattern)
            if keys:
                deleted = await r.delete(*keys)
                logger.info(f"✅ Redis pattern '{pattern}': {deleted} keys deleted")
                total_deleted += deleted
            else:
                logger.info(f"ℹ️ Redis pattern '{pattern}': No keys found")
        
        # Also try to flush specific databases if needed
        # await r.flushdb()  # Uncomment this to flush the entire Redis database
        
        await r.close()
        
        logger.info(f"✅ Redis: Total {total_deleted} keys deleted")
        return True
        
    except Exception as e:
        logger.error(f"❌ Redis cleanup failed: {e}")
        return False

def clean_local_sqlite():
    """Clean any local SQLite databases"""
    try:
        import sqlite3
        from pathlib import Path
        
        logger.info("🧹 Cleaning local SQLite databases...")
        
        # Common SQLite file names in your project
        sqlite_files = [
            "call_transcriptions.db",
            "conversation_memory.db",
            "*.db"
        ]
        
        deleted_count = 0
        for pattern in sqlite_files:
            if "*" in pattern:
                # Use glob for wildcard patterns
                for db_file in Path(".").glob(pattern):
                    if db_file.exists():
                        db_file.unlink()
                        logger.info(f"✅ Deleted SQLite file: {db_file}")
                        deleted_count += 1
            else:
                db_file = Path(pattern)
                if db_file.exists():
                    db_file.unlink()
                    logger.info(f"✅ Deleted SQLite file: {db_file}")
                    deleted_count += 1
                else:
                    logger.info(f"ℹ️ SQLite file not found: {db_file}")
        
        if deleted_count == 0:
            logger.info("ℹ️ No SQLite files found to delete")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ SQLite cleanup failed: {e}")
        return False

def clean_file_caches():
    """Clean various file caches"""
    try:
        import shutil
        from pathlib import Path
        
        logger.info("🧹 Cleaning file caches...")
        
        cache_dirs = [
            "logs",
            "memory",
            "__pycache__",
            ".pytest_cache",
            "qdrant_storage"  # This will reset your knowledge base too
        ]
        
        deleted_count = 0
        for cache_dir in cache_dirs:
            dir_path = Path(cache_dir)
            if dir_path.exists():
                if cache_dir == "qdrant_storage":
                    # Ask for confirmation before deleting knowledge base
                    response = input(f"⚠️ Delete Qdrant storage (knowledge base)? This will remove all indexed documents. [y/N]: ")
                    if response.lower() != 'y':
                        logger.info(f"ℹ️ Skipped: {cache_dir}")
                        continue
                
                shutil.rmtree(dir_path)
                logger.info(f"✅ Deleted directory: {cache_dir}")
                deleted_count += 1
            else:
                logger.info(f"ℹ️ Directory not found: {cache_dir}")
        
        # Clean individual cache files
        cache_files = list(Path(".").glob("**/*.pyc")) + list(Path(".").glob("**/*.pyo"))
        for cache_file in cache_files:
            cache_file.unlink()
            deleted_count += 1
        
        if cache_files:
            logger.info(f"✅ Deleted {len(cache_files)} Python cache files")
        
        logger.info(f"✅ File cleanup: {deleted_count} items deleted")
        return True
        
    except Exception as e:
        logger.error(f"❌ File cache cleanup failed: {e}")
        return False

async def verify_cleanup():
    """Verify that the cleanup was successful"""
    logger.info("🔍 Verifying cleanup...")
    
    try:
        # Test MongoDB
        from pymongo import AsyncMongoClient
        from config import config
        
        client = AsyncMongoClient(config.get_optimized_mongodb_url())
        db = client[config.mongodb_database]
        
        total_docs = 0
        for collection_name in ["caller_profiles", "call_sessions", "conversation_items", "transcription_segments"]:
            count = await db[collection_name].count_documents({})
            total_docs += count
        
        client.close()
        
        if total_docs == 0:
            logger.info("✅ MongoDB verification: All clean!")
        else:
            logger.warning(f"⚠️ MongoDB verification: {total_docs} documents still exist")
        
        # Test Redis
        import redis.asyncio as redis
        r = redis.from_url(config.redis_url)
        
        voice_keys = await r.keys("voice_session:*")
        profile_keys = await r.keys("user_profile:*")
        
        await r.close()
        
        total_redis_keys = len(voice_keys) + len(profile_keys)
        if total_redis_keys == 0:
            logger.info("✅ Redis verification: All clean!")
        else:
            logger.warning(f"⚠️ Redis verification: {total_redis_keys} voice AI keys still exist")
        
        return total_docs == 0 and total_redis_keys == 0
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

async def test_fresh_caller_simulation():
    """Simulate how the system will treat a caller after cleanup"""
    try:
        logger.info("🧪 Testing fresh caller simulation...")
        
        from call_transcription_storage import get_call_storage
        
        test_phone = "+18188395060"  # Your test phone number
        
        storage = await get_call_storage()
        
        # Check if caller exists
        caller_profile = await storage.get_caller_by_phone(test_phone)
        
        if caller_profile:
            logger.warning(f"⚠️ Test failed: Caller profile still exists for {test_phone}")
            logger.info(f"   Profile: {caller_profile.caller_id}, calls: {caller_profile.total_calls}")
            return False
        else:
            logger.info(f"✅ Test passed: No profile found for {test_phone} - will be treated as new caller")
            return True
        
    except Exception as e:
        logger.error(f"❌ Fresh caller test failed: {e}")
        return False

async def main():
    """Main cleanup function"""
    print("🧹 COMPLETE SYSTEM CLEANUP")
    print("=" * 60)
    print("This will clean ALL databases and caches to make everyone a new caller")
    print("")
    
    # Get confirmation
    print("⚠️ WARNING: This will delete:")
    print("   - All MongoDB call data")
    print("   - All Redis cache data") 
    print("   - All SQLite databases")
    print("   - All file caches")
    print("   - Optionally: Qdrant knowledge base")
    print("")
    
    response = input("Are you sure you want to proceed? Type 'yes' to confirm: ")
    if response.lower() != 'yes':
        print("❌ Cleanup cancelled")
        return
    
    print("\n🚀 Starting complete cleanup...")
    print("=" * 60)
    
    results = []
    
    # Clean MongoDB
    print("\n1. Cleaning MongoDB...")
    mongodb_success = await clean_mongodb_completely()
    results.append(("MongoDB", mongodb_success))
    
    # Clean Redis
    print("\n2. Cleaning Redis...")
    redis_success = await clean_redis_completely()
    results.append(("Redis", redis_success))
    
    # Clean SQLite
    print("\n3. Cleaning SQLite...")
    sqlite_success = clean_local_sqlite()
    results.append(("SQLite", sqlite_success))
    
    # Clean file caches
    print("\n4. Cleaning file caches...")
    file_success = clean_file_caches()
    results.append(("File Caches", file_success))
    
    # Verify cleanup
    print("\n5. Verifying cleanup...")
    verification_success = await verify_cleanup()
    results.append(("Verification", verification_success))
    
    # Test fresh caller simulation
    print("\n6. Testing fresh caller simulation...")
    test_success = await test_fresh_caller_simulation()
    results.append(("Fresh Caller Test", test_success))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 CLEANUP SUMMARY")
    print("=" * 60)
    
    all_success = True
    for component, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{component}: {status}")
        if not success:
            all_success = False
    
    print("\n" + "=" * 60)
    if all_success:
        print("🎉 COMPLETE CLEANUP SUCCESSFUL!")
        print("")
        print("✅ All data cleaned")
        print("✅ All caches cleared")
        print("✅ System reset to fresh state")
        print("")
        print("💡 NEXT STEPS:")
        print("1. Restart your voice AI: python main_new.py dev")
        print("2. Make a test call")
        print("3. You should now get: 'Roadside assistance, this is Mark, how can I help you today?'")
        print("4. NO MORE 'Welcome back' messages!")
        print("")
        
    else:
        print("❌ CLEANUP HAD SOME ISSUES")
        print("")
        print("🔧 Manual steps you can try:")
        print("1. Restart Redis: sudo systemctl restart redis")
        print("2. Restart MongoDB: sudo systemctl restart mongod")
        print("3. Delete files manually:")
        print("   rm -rf logs/ memory/ __pycache__/ .pytest_cache/")
        print("   rm -f *.db")
        print("4. Clear Redis manually: redis-cli FLUSHALL")
        print("")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())