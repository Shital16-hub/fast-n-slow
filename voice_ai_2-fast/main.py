# main.py - UPDATED FOR INTELLIGENT DISPATCHER
"""
UPDATED: Uses IntelligentDispatcherAgent with LLM brain and RAG pricing
"""
import asyncio
import logging
import os
from dotenv import load_dotenv

print("🔍 DEBUG: Starting imports...")

# CRITICAL: Load environment FIRST and FORCE localhost
load_dotenv()

# FORCE localhost connection to prevent external IP usage
os.environ['LIVEKIT_URL'] = 'ws://localhost:7880'
os.environ['LIVEKIT_API_KEY'] = 'devkey'
os.environ['LIVEKIT_API_SECRET'] = 'secret'

print("🔍 DEBUG: Environment forced to localhost")
print(f"🔍 LIVEKIT_URL: {os.environ['LIVEKIT_URL']}")
print(f"🔍 LIVEKIT_API_KEY: {os.environ['LIVEKIT_API_KEY']}")

from livekit.agents import JobContext, WorkerOptions, cli

print("🔍 DEBUG: LiveKit imports successful")

# Setup logging first
from logging_config import setup_development_logging, create_call_logger
setup_development_logging()

print("🔍 DEBUG: Logging setup complete")

# Import modular components
from services.session import create_optimized_session
from transcription.handler import CompleteTranscriptionHandler
from agents.dispatcher import IntelligentDispatcherAgent  # UPDATED: Use intelligent dispatcher
from call_transcription_storage import get_call_storage
from simple_rag_v2 import simplified_rag
from models.call_data import CallData

print("🔍 DEBUG: All imports successful")

main_logger = create_call_logger("main")

def prewarm(proc):
    """Prewarm function - loads VAD model"""
    print("🔍 DEBUG: Starting prewarm...")
    try:
        from livekit.plugins import silero
        proc.userdata["vad"] = silero.VAD.load()
        main_logger.info("✅ VAD preloaded successfully")
        print("🔍 DEBUG: Prewarm complete")
    except Exception as e:
        print(f"🔍 DEBUG: Prewarm error: {e}")
        main_logger.error(f"❌ Prewarm error: {e}")

async def entrypoint(ctx: JobContext):
    """UPDATED: Entrypoint uses IntelligentDispatcherAgent"""
    
    print("🔍 DEBUG: Entrypoint called!")
    main_logger.info("🧠 Intelligent Voice AI System Starting (LLM Brain + RAG)")
    main_logger.info("✅ LLM acts as brain, RAG provides pricing data")
    main_logger.info(f"🔗 Connecting to: {os.environ['LIVEKIT_URL']}")
    
    try:
        # CRITICAL: Connect to room FIRST
        print("🔍 DEBUG: Connecting to LOCAL LiveKit room...")
        await ctx.connect()
        print("🔍 DEBUG: Connected to LOCAL LiveKit room!")
        main_logger.info("📡 Connected to LOCAL LiveKit room")
        
        # Initialize storage
        print("🔍 DEBUG: Initializing storage...")
        storage = await get_call_storage()
        main_logger.info("✅ Storage initialized")
        
        # Initialize RAG
        print("🔍 DEBUG: Initializing RAG...")
        rag_success = await simplified_rag.initialize()
        main_logger.info(f"✅ RAG initialized: {rag_success}")
        
        print("🔍 DEBUG: Creating session data...")
        # Create call data
        call_data = await create_simple_session_data(ctx, storage)
        
        print("🔍 DEBUG: Creating session...")
        # Create session
        session = await create_optimized_session(call_data)
        
        print("🔍 DEBUG: Setting up transcription...")
        # Setup transcription
        transcription_handler = CompleteTranscriptionHandler(call_data)
        await transcription_handler.initialize()
        transcription_handler.setup_handlers(session)
        
        print("🔍 DEBUG: Creating intelligent agent...")
        # UPDATED: Create IntelligentDispatcherAgent
        initial_agent = IntelligentDispatcherAgent(call_data)
        
        print("🔍 DEBUG: Starting session...")
        # Start session
        await session.start(agent=initial_agent, room=ctx.room)
        
        print("🔍 DEBUG: Generating greeting...")
        # Intelligent greeting
        greeting_message = "Hello, thank you for calling General Towing & Roadside Assistance! I'm Mark, and I'm here to help you today."
        await session.generate_reply(instructions=f"Say exactly: '{greeting_message}'")
        
        main_logger.info(f"🧠 Intelligent greeting: {greeting_message}")
        
        # Setup cleanup handlers
        @session.on("close")
        def on_session_close(event):
            asyncio.create_task(transcription_handler.save_final_transcript())
            transcription_handler.print_conversation_transcript()
        
        print("🔍 DEBUG: Intelligent agent ready and waiting for calls!")
        main_logger.info("🚀 Intelligent Voice AI System Ready - LLM Brain + RAG Pricing")
        
    except Exception as e:
        print(f"🔍 DEBUG: ENTRYPOINT ERROR: {e}")
        main_logger.error(f"❌ Entrypoint error: {e}")
        import traceback
        traceback.print_exc()
        raise

async def create_simple_session_data(ctx: JobContext, storage) -> CallData:
    """Create session data for intelligent processing"""
    
    try:
        print("🔍 DEBUG: Waiting for participant...")
        participant = await ctx.wait_for_participant()
        
        print("🔍 DEBUG: Participant received!")
        # Extract phone number
        phone_number = "unknown"
        if hasattr(participant, 'attributes'):
            phone_attrs = [
                "sip.phoneNumber", 
                "sip.from_number", 
                "sip.caller_number",
                "phoneNumber",
                "from_number"
            ]
            
            for attr in phone_attrs:
                if attr in participant.attributes:
                    phone = participant.attributes[attr]
                    if phone and phone != "unknown":
                        phone_number = phone
                        break
        
        print(f"🔍 DEBUG: Phone number: {phone_number}")
        main_logger.info(f"📞 Incoming call: {phone_number}")
        
        # Create new session
        session_id, caller_id = await storage.start_call_session(
            phone_number=phone_number,
            session_metadata={
                "participant_identity": participant.identity,
                "intelligent_mode": True,
                "llm_brain": True,
                "rag_pricing": True
            }
        )
        
        print(f"🔍 DEBUG: Session created: {session_id}")
        
        # Create call data
        call_data = CallData()
        call_data.session_id = session_id
        call_data.caller_id = caller_id
        call_data.phone_number = phone_number
        call_data.is_returning_caller = False
        call_data.previous_calls_count = 0
        call_data.stored_info = {}
        
        main_logger.info(f"✅ Intelligent session started: {session_id}")
        main_logger.info(f"🧠 Mode: LLM brain with RAG pricing")
        
        print(f"🔍 DEBUG: Call data ready")
        return call_data
        
    except Exception as e:
        print(f"🔍 DEBUG: Session creation error: {e}")
        main_logger.error(f"❌ Session creation error: {e}")
        raise

if __name__ == "__main__":
    try:
        print("🔍 DEBUG: Starting CLI...")
        print("🧠 INTELLIGENT VOICE AI SYSTEM")
        print("=" * 50)
        print("✅ LLM Brain: GPT-4o-mini")
        print("✅ Knowledge Base: RAG with Qdrant")
        print("✅ Pricing: Intelligent calculation from knowledge base")
        print("✅ LiveKit URL: ws://localhost:7880")
        print("✅ API Key: devkey (development)")
        print("=" * 50)
        
        # Verify environment
        print(f"🔍 Final check - LIVEKIT_URL: {os.environ.get('LIVEKIT_URL')}")
        print(f"🔍 Final check - LIVEKIT_API_KEY: {os.environ.get('LIVEKIT_API_KEY')}")
        
        print("🔍 DEBUG: Calling cli.run_app...")
        
        # Create worker options
        worker_options = WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name="my-telephony-agent",
            ws_url="ws://localhost:7880",
            api_key="devkey",
            api_secret="secret",
        )
        
        print("🔍 DEBUG: Worker options created...")
        print("🔍 DEBUG: Starting Intelligent LiveKit agent...")
        cli.run_app(worker_options)
        
    except KeyboardInterrupt:
        print("🔍 DEBUG: Interrupted by user")
        main_logger.info("🛑 Application stopped by user")
    except Exception as e:
        print(f"🔍 DEBUG: FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)