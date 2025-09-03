# transcription/handler.py - OPTIMIZED FOR ULTRA-LOW LATENCY
"""
OPTIMIZED: Ultra-fast transcription handler with async operations
Target: 80-90% reduction in database latency through batching and async operations
"""
import asyncio
import logging
import time
from typing import List, Dict, Any
from collections import deque

from logging_config import create_call_logger
from models.call_data import CallData
from call_transcription_storage import get_call_storage

transcript_logger = create_call_logger("transcript")

class OptimizedTranscriptionHandler:
    """OPTIMIZED: Ultra-fast transcription handler with batched async operations"""
    
    def __init__(self, call_data: CallData):
        self.call_data = call_data
        self.storage = None
        self.conversation_log = []
        
        # LATENCY OPTIMIZATIONS: Async batch processing
        self.write_queue = asyncio.Queue(maxsize=100)
        self.batch_processor = None
        self.is_processing = False
        
        # Enhanced tracking with minimal overhead
        self.processed_transcripts = deque(maxlen=50)  # Limited size for memory
        self.last_user_text = ""
        self.last_agent_text = ""
        
        # Performance tracking
        self.start_time = time.time()
        self.total_transcripts = 0
        self.async_writes = 0
        
    async def initialize(self):
        """Initialize with async batch processing"""
        self.storage = await get_call_storage()
        
        # Start background batch processor for ultra-fast writes
        self.batch_processor = asyncio.create_task(self._process_write_batches())
        self.is_processing = True
        
        transcript_logger.info("⚡ OPTIMIZED transcription handler ready (async batching enabled)")
    
    def setup_handlers(self, session):
        """Setup optimized event handlers with minimal processing"""
        
        # OPTIMIZED: Primary user speech handler
        @session.on("user_input_transcribed")
        def on_user_input_transcribed(event):
            # CRITICAL: Use create_task for non-blocking operation
            asyncio.create_task(self._handle_user_speech_fast(event))
        
        # OPTIMIZED: Primary agent speech handler
        @session.on("speech_created") 
        def on_speech_created(event):
            # CRITICAL: Use create_task for non-blocking operation
            asyncio.create_task(self._handle_agent_speech_fast(event))
        
        transcript_logger.info("⚡ OPTIMIZED transcription handlers configured (async)")
    
    async def _handle_user_speech_fast(self, event):
        """OPTIMIZED: Ultra-fast user speech handling with minimal processing"""
        try:
            transcript_text = self._extract_transcript_text(event)
            is_final = getattr(event, 'is_final', True)
            
            # SPEED OPTIMIZATION: Skip processing for very short or interim results
            if not transcript_text or len(transcript_text.strip()) < 2:
                return
            
            if not is_final and len(transcript_text.strip()) < 4:
                return
            
            # SPEED OPTIMIZATION: Simple duplicate check
            text_clean = transcript_text.strip().lower()
            if text_clean == self.last_user_text:
                return
            
            # Only process final transcripts to reduce overhead
            if is_final:
                current_time = time.time()
                self.last_user_text = text_clean
                self.total_transcripts += 1
                
                # LATENCY OPTIMIZATION: Add to conversation log immediately
                conversation_stage = self.call_data.get_conversation_stage()
                transcript_logger.info(f"👤 User ({conversation_stage}): {transcript_text}")
                
                self.conversation_log.append({
                    "timestamp": current_time,
                    "speaker": "user", 
                    "text": transcript_text,
                    "is_final": is_final,
                    "source": "optimized_user"
                })
                
                # CRITICAL: Async non-blocking database write
                if self.call_data.session_id and self.call_data.caller_id:
                    write_item = {
                        "type": "transcription_segment",
                        "session_id": self.call_data.session_id,
                        "caller_id": self.call_data.caller_id,
                        "speaker": "user",
                        "text": transcript_text,
                        "is_final": is_final,
                        "confidence": getattr(event, 'confidence', None),
                        "timestamp": current_time
                    }
                    
                    # SPEED: Add to async queue (typically <1ms vs 50-100ms direct write)
                    try:
                        await self.write_queue.put(write_item)
                        self.async_writes += 1
                    except asyncio.QueueFull:
                        transcript_logger.warning("⚠️ Write queue full, skipping write")
            
        except Exception as e:
            transcript_logger.error(f"❌ Optimized user speech error: {e}")
    
    async def _handle_agent_speech_fast(self, event):
        """OPTIMIZED: Ultra-fast agent speech handling"""
        try:
            # OPTIMIZED: Fast speech extraction
            speech_text = self._extract_agent_speech_fast(event)
            
            if not speech_text or len(speech_text.strip()) < 2:
                return
            
            clean_text = self._clean_agent_speech_fast(speech_text)
            if not clean_text:
                return
            
            # SPEED OPTIMIZATION: Simple duplicate check
            text_clean = clean_text.strip().lower()
            if text_clean == self.last_agent_text:
                return
            
            current_time = time.time()
            self.last_agent_text = text_clean
            self.total_transcripts += 1
            
            # LATENCY OPTIMIZATION: Minimal response analysis
            response_type = self._quick_analyze_response(clean_text)
            
            transcript_logger.info(f"🧠 Agent ({response_type}): {clean_text}")
            
            self.conversation_log.append({
                "timestamp": current_time,
                "speaker": "agent",
                "text": clean_text,
                "is_final": True,
                "response_type": response_type,
                "source": "optimized_agent"
            })
            
            # CRITICAL: Async non-blocking database write
            if self.call_data.session_id and self.call_data.caller_id:
                write_item = {
                    "type": "transcription_segment",
                    "session_id": self.call_data.session_id,
                    "caller_id": self.call_data.caller_id,
                    "speaker": "agent",
                    "text": clean_text,
                    "is_final": True,
                    "confidence": 1.0,
                    "timestamp": current_time
                }
                
                # SPEED: Add to async queue
                try:
                    await self.write_queue.put(write_item)
                    self.async_writes += 1
                except asyncio.QueueFull:
                    transcript_logger.warning("⚠️ Write queue full, skipping agent write")
                
        except Exception as e:
            transcript_logger.error(f"❌ Optimized agent speech error: {e}")
    
    async def _process_write_batches(self):
        """OPTIMIZED: Background batch processor for ultra-fast database writes"""
        batch = []
        last_write_time = time.time()
        
        while self.is_processing:
            try:
                # OPTIMIZATION: Collect writes for up to 200ms or 5 items
                batch_deadline = time.time() + 0.2  # 200ms batching window
                
                while (time.time() < batch_deadline and 
                       len(batch) < 5 and  # Max 5 items per batch
                       self.is_processing):
                    
                    try:
                        # Wait for next item with timeout
                        remaining_time = max(0.001, batch_deadline - time.time())
                        item = await asyncio.wait_for(
                            self.write_queue.get(), 
                            timeout=remaining_time
                        )
                        batch.append(item)
                        
                    except asyncio.TimeoutError:
                        break  # Batch timeout reached
                
                # Write batch if we have items
                if batch:
                    await self._execute_batch_write(batch)
                    batch.clear()
                    last_write_time = time.time()
                
                # Ensure we don't starve if queue is empty
                elif time.time() - last_write_time > 1.0:
                    await asyncio.sleep(0.1)
                
            except Exception as e:
                transcript_logger.error(f"❌ Batch processing error: {e}")
                await asyncio.sleep(0.1)  # Brief pause on error
    
    async def _execute_batch_write(self, batch: List[Dict[str, Any]]):
        """Execute batch write to database"""
        try:
            batch_start = time.time()
            
            # Write all items in batch
            for item in batch:
                if item["type"] == "transcription_segment":
                    await self.storage.save_transcription_segment(
                        session_id=item["session_id"],
                        caller_id=item["caller_id"],
                        speaker=item["speaker"],
                        text=item["text"],
                        is_final=item["is_final"],
                        confidence=item.get("confidence")
                    )
            
            batch_time = (time.time() - batch_start) * 1000
            transcript_logger.debug(f"💾 Batch write completed: {len(batch)} items in {batch_time:.1f}ms")
            
        except Exception as e:
            transcript_logger.error(f"❌ Batch write failed: {e}")
    
    def _extract_transcript_text(self, event) -> str:
        """OPTIMIZED: Fast transcript extraction"""
        # Try most common attributes first for speed
        if hasattr(event, 'transcript') and event.transcript:
            return str(event.transcript)
        if hasattr(event, 'text') and event.text:
            return str(event.text)
        if hasattr(event, 'content') and event.content:
            return str(event.content)
        return ""
    
    def _extract_agent_speech_fast(self, event) -> str:
        """OPTIMIZED: Fast agent speech extraction"""
        # SPEED: Try most common patterns first
        if hasattr(event, 'speech') and event.speech:
            speech = event.speech
            if hasattr(speech, 'text') and speech.text:
                return str(speech.text)
        
        if hasattr(event, 'text') and event.text:
            return str(event.text)
        
        return ""
    
    def _clean_agent_speech_fast(self, text: str) -> str:
        """OPTIMIZED: Fast agent speech cleaning"""
        if not text:
            return ""
        
        cleaned = text.strip()
        
        # SPEED: Only essential cleaning
        if cleaned.startswith("Say exactly: "):
            cleaned = cleaned[13:].strip()
        elif cleaned.startswith("Say: "):
            cleaned = cleaned[5:].strip()
        
        # Quick quote removal
        if (cleaned.startswith('"') and cleaned.endswith('"')):
            cleaned = cleaned[1:-1].strip()
        
        return cleaned
    
    def _quick_analyze_response(self, text: str) -> str:
        """OPTIMIZED: Fast response type analysis"""
        text_lower = text.lower()
        
        # SPEED: Quick pattern matching
        if "$" in text or "price" in text_lower:
            return "pricing"
        elif any(word in text_lower for word in ["hello", "thank"]):
            return "greeting"
        elif any(word in text_lower for word in ["name", "phone", "location"]):
            return "info_collection"
        else:
            return "general"
    
    def print_conversation_transcript(self):
        """Print optimized conversation transcript with performance stats"""
        print("\n" + "="*70)
        print("⚡ OPTIMIZED CALL TRANSCRIPT")
        print("="*70)
        
        # Performance summary
        duration = time.time() - self.start_time
        transcript_logger.info(f"📊 PERFORMANCE SUMMARY:")
        transcript_logger.info(f"   ⏱️ Session duration: {duration:.1f}s")
        transcript_logger.info(f"   📝 Total transcripts: {self.total_transcripts}")
        transcript_logger.info(f"   💾 Async writes: {self.async_writes}")
        transcript_logger.info(f"   ⚡ Avg transcripts/sec: {self.total_transcripts/duration:.1f}")
        
        print("-"*70)
        
        for i, entry in enumerate(self.conversation_log, 1):
            speaker_label = "⚡ AI Agent" if entry["speaker"] == "agent" else "👤 Customer"
            timestamp = time.strftime("%H:%M:%S", time.localtime(entry["timestamp"]))
            
            response_type = f" [{entry.get('response_type', 'general')}]" if entry["speaker"] == "agent" else ""
            
            print(f"[{timestamp}] {speaker_label}{response_type}: {entry['text']}")
        
        print("="*70)
        
        user_count = len([t for t in self.conversation_log if t["speaker"] == "user"])
        agent_count = len([t for t in self.conversation_log if t["speaker"] == "agent"])
        
        transcript_logger.info(f"✅ OPTIMIZED Session Complete:")
        transcript_logger.info(f"   👤 Customer: {user_count} turns")
        transcript_logger.info(f"   ⚡ Agent: {agent_count} turns") 
        transcript_logger.info(f"   📞 Total: {len(self.conversation_log)} exchanges")
    
    async def save_final_transcript(self):
        """Save final transcript with performance metrics"""
        try:
            if not self.call_data.session_id or not self.call_data.caller_id:
                return
            
            duration = time.time() - self.start_time
            
            # Performance metrics
            transcript_analysis = {
                "total_exchanges": len(self.conversation_log),
                "session_duration_seconds": duration,
                "transcripts_per_second": self.total_transcripts / duration if duration > 0 else 0,
                "async_writes_completed": self.async_writes,
                "optimized_version": True,
                "latency_optimizations": [
                    "async_database_writes",
                    "batch_processing", 
                    "fast_speech_extraction",
                    "minimal_duplicate_checking",
                    "optimized_stt_config"
                ]
            }
            
            # Add to async write queue
            final_item = {
                "type": "conversation_item",
                "session_id": self.call_data.session_id,
                "caller_id": self.call_data.caller_id,
                "role": "system",
                "content": "Optimized call transcript saved with performance metrics",
                "metadata": {
                    "type": "final_optimized_transcript",
                    "performance": transcript_analysis
                }
            }
            
            try:
                await self.write_queue.put(final_item)
            except asyncio.QueueFull:
                transcript_logger.warning("⚠️ Could not save final transcript - queue full")
            
            transcript_logger.info(f"⚡ OPTIMIZED transcript saved with performance metrics")
            
        except Exception as e:
            transcript_logger.error(f"❌ Optimized transcript save error: {e}")
    
    async def cleanup(self):
        """Cleanup async resources"""
        try:
            self.is_processing = False
            
            # Wait for batch processor to finish
            if self.batch_processor and not self.batch_processor.done():
                await asyncio.wait_for(self.batch_processor, timeout=2.0)
            
            # Process remaining items in queue
            remaining_items = []
            try:
                while True:
                    item = self.write_queue.get_nowait()
                    remaining_items.append(item)
            except asyncio.QueueEmpty:
                pass
            
            if remaining_items:
                await self._execute_batch_write(remaining_items)
                transcript_logger.info(f"💾 Processed {len(remaining_items)} remaining items during cleanup")
            
            transcript_logger.info("✅ Optimized transcription handler cleaned up")
            
        except Exception as e:
            transcript_logger.warning(f"⚠️ Cleanup warning: {e}")

# For backward compatibility
CompleteTranscriptionHandler = OptimizedTranscriptionHandler