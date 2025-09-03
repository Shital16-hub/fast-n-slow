# main.py - OPTIMIZED FOR ULTRA-LOW LATENCY
"""
OPTIMIZED: Ultra-fast main.py with minimal overhead and optimized initialization
Target: 40-60% total system latency reduction through optimized components
"""
import asyncio
import logging
import os
import time
from dotenv import load_dotenv

# CRITICAL: Load environment FIRST and FORCE localhost
load_dotenv()

# FORCE localhost connection to prevent external IP usage
os.environ['LIVEKIT_URL'] = 'ws://localhost:7880'
os.environ['LIVEKIT_API_KEY'] = 'devkey'
os.environ['LIVEKIT_API_SECRET'] = 'secret'

from livekit.agents import JobContext, WorkerOptions, cli

# OPTIMIZED: Minimal logging setup for maximum performance
logging.basicConfig(
    level=logging.WARNING,  # Only warnings and errors for speed
    format='%(levelname)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

# Disable verbose third-party loggers for performance
for logger_name in ['pymongo', 'livekit', 'qdrant_client', 'openai', 'httpx', 'httpcore', 'urllib3']:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

# Import optimized components
from services.session import create_optimized_session
from transcription.handler import OptimizedTranscriptionHandler
from agents.dispatcher import OptimizedIntelligentDispatcherAgent
from call_transcription_storage import get_call_storage
from simple_rag_v2 import simplified_rag
from models.call_data import CallData

# Performance tracking
session_start_time = time.time()
performance_logger = logging.getLogger("performance")

def prewarm(proc):
    """OPTIMIZED: Ultra-fast prewarm with minimal processing"""
    try:
        from livekit.plugins import silero
        proc.userdata["vad"] = silero.VAD.load(
            threshold=0.6,  # More aggressive for faster detection
            min_speech_duration_ms=250,
            min_silence_duration_ms=800
        )
    except Exception:
        pass  # Silent fail for maximum speed

async def entrypoint(ctx: JobContext):
    """OPTIMIZED: Ultra-fast entrypoint with minimal latency"""
    
    entry_start = time.time()
    
    try:
        # STEP 1: Connect to room immediately (no delays)
        await ctx.connect()
        connect_time = (time.time() - entry_start) * 1000
        
        # STEP 2: Initialize storage with async pattern
        storage_start = time.time()
        storage = await get_call_storage()
        storage_time = (time.time() - storage_start) * 1000
        
        # STEP 3: Initialize RAG system (async)
        rag_start = time.time()
        rag_task = asyncio.create_task(simplified_rag.initialize())
        
        # STEP 4: Create session data while RAG initializes
        session_data_start = time.time()
        call_data = await create_ultra_fast_session_data(ctx, storage)
        session_data_time = (time.time() - session_data_start) * 1000
        
        # STEP 5: Wait for RAG initialization to complete
        await rag_task
        rag_time = (time.time() - rag_start) * 1000
        
        # STEP 6: Create optimized session
        session_start = time.time()
        session = await create_optimized_session(call_data)
        session_time = (time.time() - session_start) * 1000
        
        # STEP 7: Setup optimized transcription
        transcription_start = time.time()
        transcription_handler = OptimizedTranscriptionHandler(call_data)
        await transcription_handler.initialize()
        transcription_handler.setup_handlers(session)
        transcription_time = (time.time() - transcription_start) * 1000
        
        # STEP 8: Create optimized agent
        agent_start = time.time()
        initial_agent = OptimizedIntelligentDispatcherAgent(call_data)
        agent_time = (time.time() - agent_start) * 1000
        
        # STEP 9: Start session
        start_session_start = time.time()
        await session.start(agent=initial_agent, room=ctx.room)
        start_session_time = (time.time() - start_session_start) * 1000
        
        # STEP 10: MINIMAL greeting to prevent timeout
        greeting_start = time.time()
        
        try:
            # CRITICAL: Use asyncio timeout to prevent hanging
            await asyncio.wait_for(
                session.generate_reply(
                    instructions="Say: 'Hello, this is Mark from General Towing. What's your name?'"
                ),
                timeout=3.0  # 3 second timeout
            )
            greeting_time = (time.time() - greeting_start) * 1000
        except asyncio.TimeoutError:
            greeting_time = (time.time() - greeting_start) * 1000
            performance_logger.error(f"❌ Greeting timeout after {greeting_time:.1f}ms")
            # Don't fail the entire system, just continue without greeting
        except Exception as e:
            greeting_time = (time.time() - greeting_start) * 1000
            performance_logger.error(f"❌ Greeting error after {greeting_time:.1f}ms: {e}")
            # Continue without greeting
        
        # PERFORMANCE SUMMARY
        total_time = (time.time() - entry_start) * 1000
        performance_logger.warning(f"⚡ ULTRA-FAST INITIALIZATION COMPLETE: {total_time:.1f}ms")
        performance_logger.warning(f"   📡 Connect: {connect_time:.1f}ms")
        performance_logger.warning(f"   💾 Storage: {storage_time:.1f}ms") 
        performance_logger.warning(f"   🔍 RAG: {rag_time:.1f}ms")
        performance_logger.warning(f"   📞 Session Data: {session_data_time:.1f}ms")
        performance_logger.warning(f"   ⚙️ Session: {session_time:.1f}ms")
        performance_logger.warning(f"   📝 Transcription: {transcription_time:.1f}ms")
        performance_logger.warning(f"   🧠 Agent: {agent_time:.1f}ms")
        performance_logger.warning(f"   🚀 Start: {start_session_time:.1f}ms")
        performance_logger.warning(f"   👋 Greeting: {greeting_time:.1f}ms")
        
        # Setup cleanup handlers
        @session.on("close")
        def on_session_close(event):
            asyncio.create_task(transcription_handler.save_final_transcript())
            asyncio.create_task(transcription_handler.cleanup())
            transcription_handler.print_conversation_transcript()
        
    except Exception as e:
        error_time = (time.time() - entry_start) * 1000
        performance_logger.error(f"❌ ENTRYPOINT ERROR after {error_time:.1f}ms: {e}")
        raise

async def create_ultra_fast_session_data(ctx: JobContext, storage) -> CallData:
    """OPTIMIZED: Ultra-fast session data creation with minimal processing"""
    
    try:
        # STEP 1: Get participant with timeout
        participant = await asyncio.wait_for(ctx.wait_for_participant(), timeout=5.0)
        
        # STEP 2: Extract phone number (fast method)
        phone_number = "unknown"
        if hasattr(participant, 'attributes'):
            # Try most common attributes first for speed
            for attr in ["sip.phoneNumber", "sip.from_number", "phoneNumber"]:
                if attr in participant.attributes:
                    phone = participant.attributes[attr]
                    if phone and phone != "unknown":
                        phone_number = phone
                        break
        
        # STEP 3: Create session (async, non-blocking)
        session_create_start = time.time()
        session_id, caller_id = await storage.start_call_session(
            phone_number=phone_number,
            session_metadata={
                "participant_identity": participant.identity,
                "ultra_fast_mode": True,
                "optimized": True,
                "initialization_time": time.time()
            }
        )
        session_create_time = (time.time() - session_create_start) * 1000
        
        # STEP 4: Create call data with minimal processing
        call_data = CallData()
        call_data.session_id = session_id
        call_data.caller_id = caller_id
        call_data.phone_number = phone_number
        call_data.is_returning_caller = False
        call_data.previous_calls_count = 0
        call_data.stored_info = {}
        call_data.session_start_time = time.time()
        
        performance_logger.warning(f"📞 Ultra-fast session created in {session_create_time:.1f}ms")
        
        return call_data
        
    except asyncio.TimeoutError:
        performance_logger.error("❌ Participant wait timeout")
        raise
    except Exception as e:
        performance_logger.error(f"❌ Session creation error: {e}")
        raise

class PerformanceMonitor:
    """Monitor system performance for optimization"""
    
    def __init__(self):
        self.metrics = {
            "total_calls": 0,
            "avg_initialization_time": 0.0,
            "avg_response_time": 0.0,
            "cache_hit_rate": 0.0
        }
    
    def record_call_start(self, initialization_time_ms: float):
        """Record call start metrics"""
        self.metrics["total_calls"] += 1
        
        # Update running average
        current_avg = self.metrics["avg_initialization_time"]
        call_count = self.metrics["total_calls"]
        self.metrics["avg_initialization_time"] = (
            (current_avg * (call_count - 1) + initialization_time_ms) / call_count
        )
    
    def get_performance_summary(self) -> dict:
        """Get performance summary"""
        return {
            "system_performance": self.metrics,
            "optimizations_active": [
                "ultra_fast_session_creation",
                "optimized_stt_config",
                "aggressive_caching",
                "async_database_operations",
                "single_rag_queries",
                "consolidated_context",
                "minimal_logging"
            ],
            "target_metrics": {
                "initialization_time": "< 500ms",
                "response_time": "< 1500ms", 
                "cache_hit_rate": "> 70%"
            }
        }

# Global performance monitor
perf_monitor = PerformanceMonitor()

if __name__ == "__main__":
    try:
        startup_start = time.time()
        
        print("⚡ ULTRA-FAST VOICE AI SYSTEM")
        print("=" * 50)
        print("✅ Optimizations: STT, LLM, RAG, Database, Caching")
        print("✅ Target: <1.5s total response time")
        print("✅ LiveKit URL: ws://localhost:7880")
        print("✅ Mode: Ultra-Fast Performance")
        print("=" * 50)
        
        # Create optimized worker options
        worker_options = WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name="my-telephony-agent",
            ws_url="ws://localhost:7880",
            api_key="devkey",
            api_secret="secret",
        )
        
        startup_time = (time.time() - startup_start) * 1000
        print(f"⚡ System startup complete in {startup_time:.1f}ms")
        print("🚀 Ready for ultra-fast voice calls!")
        
        cli.run_app(worker_options)
        
    except KeyboardInterrupt:
        print("🛑 Ultra-fast system stopped by user")
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        exit(1)