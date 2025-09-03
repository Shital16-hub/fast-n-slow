# cache_cleaner.py
"""
Clean various caches in the Voice AI system
Use this when you want fresh results or after updating data
"""
import asyncio
import logging
import os
import shutil
from pathlib import Path
import argparse

# Import your systems
from simple_rag_v2 import simplified_rag
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceAICacheCleaner:
    """Clean all caches in the Voice AI system"""
    
    def __init__(self):
        self.caches_found = []
        self.caches_cleaned = []
        self.errors = []
    
    async def clean_rag_cache(self):
        """Clean RAG system cache"""
        try:
            logger.info("🧹 Cleaning RAG system cache...")
            
            # Clear simplified RAG cache
            if hasattr(simplified_rag, 'cache'):
                cache_size = len(simplified_rag.cache)
                simplified_rag.cache.clear()
                logger.info(f"✅ Cleared RAG cache: {cache_size} items")
                self.caches_cleaned.append(f"RAG cache ({cache_size} items)")
            
            # Reinitialize RAG system to clear any internal caches
            await simplified_rag.initialize()
            logger.info("✅ RAG system reinitialized")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cleaning RAG cache: {e}")
            self.errors.append(f"RAG cache: {e}")
            return False
    
    def clean_mongodb_cache(self):
        """Clean MongoDB-related caches"""
        try:
            logger.info("🧹 Cleaning MongoDB caches...")
            
            # Note: MongoDB caches are typically handled by the driver
            # We can clear any application-level caches
            
            cleaned_count = 0
            
            # If you have any MongoDB cache objects, clear them here
            # Example: if hasattr(call_storage, 'cache'): call_storage.cache.clear()
            
            logger.info(f"✅ MongoDB caches cleared: {cleaned_count} items")
            self.caches_cleaned.append(f"MongoDB cache ({cleaned_count} items)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cleaning MongoDB cache: {e}")
            self.errors.append(f"MongoDB cache: {e}")
            return False
    
    def clean_file_caches(self):
        """Clean file-based caches"""
        try:
            logger.info("🧹 Cleaning file-based caches...")
            
            cache_dirs = [
                Path("__pycache__"),
                Path(".pytest_cache"),
                Path("logs"),
                Path("memory")
            ]
            
            cache_files = [
                Path("*.pyc"),
                Path("*.pyo"),
                Path("*.log")
            ]
            
            cleaned_items = []
            
            # Clean cache directories
            for cache_dir in cache_dirs:
                if cache_dir.exists():
                    try:
                        shutil.rmtree(cache_dir)
                        cleaned_items.append(str(cache_dir))
                        logger.info(f"✅ Removed directory: {cache_dir}")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not remove {cache_dir}: {e}")
            
            # Clean cache files (using glob patterns)
            for pattern in ["**/*.pyc", "**/*.pyo", "**/__pycache__"]:
                for item in Path(".").glob(pattern):
                    try:
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                        cleaned_items.append(str(item))
                    except Exception as e:
                        logger.warning(f"⚠️ Could not remove {item}: {e}")
            
            if cleaned_items:
                logger.info(f"✅ Cleaned {len(cleaned_items)} file cache items")
                self.caches_cleaned.append(f"File caches ({len(cleaned_items)} items)")
            else:
                logger.info("ℹ️ No file caches found to clean")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cleaning file caches: {e}")
            self.errors.append(f"File caches: {e}")
            return False
    
    def clean_qdrant_cache(self):
        """Clean Qdrant-related caches"""
        try:
            logger.info("🧹 Checking Qdrant cache...")
            
            # Qdrant itself doesn't have application-level caches to clear
            # But we can check if there are any local cache files
            
            qdrant_storage = Path("qdrant_storage")
            if qdrant_storage.exists():
                # Don't delete the storage, just note its size
                storage_size = sum(f.stat().st_size for f in qdrant_storage.rglob('*') if f.is_file())
                logger.info(f"ℹ️ Qdrant storage exists: {storage_size / 1024 / 1024:.2f} MB")
                logger.info("ℹ️ Qdrant storage not cleared (contains your indexed data)")
            else:
                logger.info("ℹ️ No Qdrant storage found")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking Qdrant cache: {e}")
            self.errors.append(f"Qdrant cache: {e}")
            return False
    
    def clean_application_caches(self):
        """Clean application-specific caches"""
        try:
            logger.info("🧹 Cleaning application caches...")
            
            cleaned_count = 0
            
            # Clean any global caches that might exist in your modules
            modules_to_check = [
                'main',
                'enhanced_conversational_agent', 
                'call_transcription_storage'
            ]
            
            for module_name in modules_to_check:
                try:
                    if module_name in globals():
                        module = globals()[module_name]
                        if hasattr(module, 'cache'):
                            cache_size = len(module.cache) if hasattr(module.cache, '__len__') else 0
                            module.cache.clear()
                            cleaned_count += cache_size
                            logger.info(f"✅ Cleared {module_name} cache: {cache_size} items")
                except Exception as e:
                    logger.debug(f"No cache found in {module_name}: {e}")
            
            if cleaned_count > 0:
                self.caches_cleaned.append(f"Application caches ({cleaned_count} items)")
                logger.info(f"✅ Total application cache items cleared: {cleaned_count}")
            else:
                logger.info("ℹ️ No application caches found")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cleaning application caches: {e}")
            self.errors.append(f"Application caches: {e}")
            return False
    
    async def clean_all_caches(self, cache_types: list = None):
        """Clean all or specific cache types"""
        logger.info("🧹 VOICE AI CACHE CLEANER")
        logger.info("=" * 50)
        
        if cache_types is None:
            cache_types = ['rag', 'mongodb', 'files', 'qdrant', 'application']
        
        results = {}
        
        if 'rag' in cache_types:
            results['rag'] = await self.clean_rag_cache()
        
        if 'mongodb' in cache_types:
            results['mongodb'] = self.clean_mongodb_cache()
        
        if 'files' in cache_types:
            results['files'] = self.clean_file_caches()
        
        if 'qdrant' in cache_types:
            results['qdrant'] = self.clean_qdrant_cache()
        
        if 'application' in cache_types:
            results['application'] = self.clean_application_caches()
        
        return results
    
    def get_summary(self):
        """Get cleaning summary"""
        return {
            "caches_cleaned": self.caches_cleaned,
            "total_cleaned": len(self.caches_cleaned),
            "errors": self.errors,
            "success": len(self.errors) == 0
        }

async def main():
    """Main cache cleaning function"""
    parser = argparse.ArgumentParser(description="Clean Voice AI system caches")
    parser.add_argument("--type", "-t", 
                       choices=["rag", "mongodb", "files", "qdrant", "application", "all"],
                       default="all",
                       help="Type of cache to clean")
    parser.add_argument("--force", "-f", action="store_true",
                       help="Force cleaning without confirmation")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        logger.info("🧹 VOICE AI CACHE CLEANER STARTING")
        
        # Confirmation
        if not args.force:
            cache_type = "all caches" if args.type == "all" else f"{args.type} cache"
            response = input(f"\n⚠️ This will clear {cache_type}. Continue? [y/N]: ")
            if response.lower() != 'y':
                logger.info("❌ Cache cleaning cancelled")
                return
        
        # Create cleaner
        cleaner = VoiceAICacheCleaner()
        
        # Clean specified caches
        if args.type == "all":
            results = await cleaner.clean_all_caches()
        else:
            results = await cleaner.clean_all_caches([args.type])
        
        # Get summary
        summary = cleaner.get_summary()
        
        # Report results
        logger.info("\n" + "=" * 50)
        logger.info("📊 CACHE CLEANING SUMMARY")
        logger.info("=" * 50)
        
        if summary["caches_cleaned"]:
            logger.info("✅ Caches cleaned:")
            for cache in summary["caches_cleaned"]:
                logger.info(f"   - {cache}")
        else:
            logger.info("ℹ️ No caches found to clean")
        
        if summary["errors"]:
            logger.info("\n❌ Errors encountered:")
            for error in summary["errors"]:
                logger.info(f"   - {error}")
        
        if summary["success"]:
            logger.info(f"\n🎉 CACHE CLEANING COMPLETED SUCCESSFULLY!")
            logger.info(f"Total items cleaned: {summary['total_cleaned']}")
            logger.info("\n💡 NEXT STEPS:")
            logger.info("   1. Restart your voice AI for fresh performance")
            logger.info("   2. First queries may be slower as caches rebuild")
            logger.info("   3. Performance should improve after cache warmup")
        else:
            logger.warning(f"\n⚠️ CACHE CLEANING COMPLETED WITH ERRORS")
            logger.info("   Some caches may not have been cleared completely")
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Cache cleaning cancelled by user")
    except Exception as e:
        logger.error(f"\n❌ FATAL ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())