# main.py - OPTIMIZED FOR LOW LATENCY (MINIMAL LOGGING)
"""
OPTIMIZED: Ultra-fast main.py with minimal logging to reduce latency
All debug prints and unnecessary logging removed for maximum performance
"""
import asyncio
import logging
import os
from dotenv import load_dotenv

# CRITICAL: Load environment FIRST and FORCE localhost
load_dotenv()

# FORCE localhost connection to prevent external IP usage
os.environ['LIVEKIT_URL'] = 'ws://localhost:7880'
os.environ['LIVEKIT_API_KEY'] = 'devkey'
os.environ['LIVEKIT_API_SECRET'] = 'secret'

from livekit.agents import JobContext, WorkerOptions, cli

# OPTIMIZED: Minimal logging setup - WARNING level only
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors
    format='%(levelname)s: %(message)s',  # Minimal format
    handlers=[logging.StreamHandler()]
)

# Disable verbose third-party loggers
for logger_name in ['pymongo', 'livekit', 'qdrant_client', 'openai', 'httpx', 'httpcore']:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

# Import modular components (no debug prints)
from services.session import create_optimized_session
from transcription.handler import CompleteTranscriptionHandler
from agents.dispatcher import IntelligentDispatcherAgent
from call_transcription_storage import get_call_storage
from simple_rag_v2 import simplified_rag
from models.call_data import CallData

def prewarm(proc):
    """Optimized prewarm - loads VAD model silently"""
    try:
        from livekit.plugins import silero
        proc.userdata["vad"] = silero.VAD.load()
    except Exception:
        pass  # Silent fail - no error logging to reduce latency

async def entrypoint(ctx: JobContext):
    """OPTIMIZED: Ultra-fast entrypoint with minimal logging"""
    
    try:
        # Connect to room immediately
        await ctx.connect()
        
        # Initialize storage silently
        storage = await get_call_storage()
        
        # Initialize RAG silently
        await simplified_rag.initialize()
        
        # Create session data
        call_data = await create_simple_session_data(ctx, storage)
        
        # Create session
        session = await create_optimized_session(call_data)
        
        # Setup transcription
        transcription_handler = CompleteTranscriptionHandler(call_data)
        await transcription_handler.initialize()
        transcription_handler.setup_handlers(session)
        
        # Create intelligent agent
        initial_agent = IntelligentDispatcherAgent(call_data)
        
        # Start session
        await session.start(agent=initial_agent, room=ctx.room)
        
        # Optimized greeting - no logging
        greeting_message = "Hello, thank you for calling General Towing & Roadside Assistance! I'm Mark, and I'm here to help you today."
        await session.generate_reply(instructions=f"Say exactly: '{greeting_message}'")
        
        # Setup cleanup handlers
        @session.on("close")
        def on_session_close(event):
            asyncio.create_task(transcription_handler.save_final_transcript())
        
    except Exception as e:
        # Only log critical errors
        print(f"CRITICAL ERROR: {e}")
        raise

async def create_simple_session_data(ctx: JobContext, storage) -> CallData:
    """Optimized session data creation - minimal logging"""
    
    try:
        participant = await ctx.wait_for_participant()
        
        # Extract phone number efficiently
        phone_number = "unknown"
        if hasattr(participant, 'attributes'):
            phone_attrs = ["sip.phoneNumber", "sip.from_number", "sip.caller_number", "phoneNumber", "from_number"]
            
            for attr in phone_attrs:
                if attr in participant.attributes:
                    phone = participant.attributes[attr]
                    if phone and phone != "unknown":
                        phone_number = phone
                        break
        
        # Create new session efficiently
        session_id, caller_id = await storage.start_call_session(
            phone_number=phone_number,
            session_metadata={
                "participant_identity": participant.identity,
                "intelligent_mode": True,
                "optimized": True
            }
        )
        
        # Create call data efficiently
        call_data = CallData()
        call_data.session_id = session_id
        call_data.caller_id = caller_id
        call_data.phone_number = phone_number
        call_data.is_returning_caller = False
        call_data.previous_calls_count = 0
        call_data.stored_info = {}
        
        return call_data
        
    except Exception as e:
        print(f"Session creation error: {e}")
        raise

if __name__ == "__main__":
    try:
        # Create worker options with minimal configuration
        worker_options = WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name="my-telephony-agent",
            ws_url="ws://localhost:7880",
            api_key="devkey",
            api_secret="secret",
        )
        
        # Start the optimized agent
        cli.run_app(worker_options)
        
    except KeyboardInterrupt:
        pass  # Silent exit
    except Exception as e:
        print(f"FATAL: {e}")
        exit(1)