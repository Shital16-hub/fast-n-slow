# run_transcript_indexer.py - SCHEDULER FOR BATCH PROCESSING
"""
Scheduler to run transcript indexer periodically
Keeps running and processes batches every 2 minutes
"""
import asyncio
import logging
import signal
import sys
from transcript_indexer import TranscriptIndexer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranscriptIndexerScheduler:
    """Scheduler for running transcript indexer periodically"""
    
    def __init__(self, interval_seconds: int = 120):  # Default: 2 minutes
        self.interval_seconds = interval_seconds
        self.running = True
        self.indexer = TranscriptIndexer()
    
    async def start(self):
        """Start the scheduler"""
        logger.info(f"🚀 Starting transcript indexer scheduler (every {self.interval_seconds}s)")
        
        # Initialize indexer
        if not await self.indexer.initialize():
            logger.error("❌ Failed to initialize indexer")
            return
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Main loop
        while self.running:
            try:
                logger.info("⏰ Running scheduled batch processing...")
                await self.indexer.run_batch_processing()
                
                # Wait for next interval
                if self.running:
                    await asyncio.sleep(self.interval_seconds)
                    
            except Exception as e:
                logger.error(f"❌ Scheduler error: {e}")
                if self.running:
                    await asyncio.sleep(30)  # Wait 30s on error
        
        # Cleanup
        await self.indexer.cleanup()
        logger.info("✅ Transcript indexer scheduler stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"📤 Received signal {signum}, shutting down...")
        self.running = False

async def main():
    scheduler = TranscriptIndexerScheduler(interval_seconds=120)  # 2 minutes
    await scheduler.start()

if __name__ == "__main__":
    asyncio.run(main())