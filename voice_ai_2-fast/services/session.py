# services/session.py - FIXED Response Timeout Issues
"""
FIXED: Google Cloud STT configuration to prevent speech cutoff and response timeouts
"""
import httpx
from livekit.agents import AgentSession
from livekit.plugins import google, openai, elevenlabs, silero

from logging_config import create_call_logger
from models.call_data import CallData
from config import config

session_logger = create_call_logger("session")

async def create_optimized_session(userdata: CallData) -> AgentSession[CallData]:
    """FIXED: Proper session configuration to prevent response timeouts"""
    
    session_logger.info("🔧 Creating FIXED session to prevent response cutoffs")
    
    try:
        # FIXED STT: Use correct model and settings for continuous conversation
        stt = google.STT(
            # CRITICAL FIX: Use correct model name
            model="latest_long",  # Best for continuous conversation
            
            # FIXED: Language configuration
            languages=["en-US"],
            detect_language=False,
            
            # CRITICAL FIXES for continuous speech:
            interim_results=True,    # Enable interim results
            punctuate=True,         # Enable punctuation 
            spoken_punctuation=False, # Disable spoken punctuation
            
            # TIMING FIXES - Prevent premature cutoff:
            min_confidence_threshold=0.2,  # LOWERED to catch more speech
            
            # CREDENTIALS
            credentials_info=config.get_google_credentials_dict(),
            
            # PERFORMANCE SETTINGS for continuous conversation
            sample_rate=16000,
            location="global",
            use_streaming=True,
        )
        
        # Optimized LLM for continuous conversation
        llm = openai.LLM(
            model="gpt-4o-mini",
            temperature=0.2,
            max_completion_tokens=150,  # FIXED: Use correct parameter name
        )
        
        # Working TTS configuration
        tts = elevenlabs.TTS(
            voice_id="pNInz6obpgDQGcFmaJgB",  # Adam
            voice_settings=elevenlabs.VoiceSettings(
                stability=0.8,
                similarity_boost=0.9,
                style=0.1,
                speed=0.9,  # Slightly faster to reduce delay
                use_speaker_boost=True,
            ),
            model="eleven_turbo_v2_5",  # Fastest model
            api_key=config.elevenlabs_api_key,
        )
        
        # VAD for voice activity detection
        vad = silero.VAD.load()
        
        # CRITICAL FIX: Basic session configuration without unsupported parameters
        session = AgentSession[CallData](
            # Core components
            stt=stt,
            llm=llm,
            tts=tts,
            vad=vad,
            
            # TIMING FIXES - Only supported parameters:
            allow_interruptions=True,
            min_interruption_duration=1.2,     # Prevents cutting off agent mid-sentence
            min_endpointing_delay=1.8,         # Allows complete thoughts
            max_endpointing_delay=3.5,         # Prevents long pauses
            
            userdata=userdata,
        )
        
        session_logger.info("✅ FIXED session created successfully")
        session_logger.info("   🎤 STT: Google Cloud latest_long")
        session_logger.info("   🧠 LLM: GPT-4o-mini (fast, short responses)")
        session_logger.info("   🗣️ TTS: ElevenLabs Turbo (fast)")
        session_logger.info("   ⏱️ TIMING: Optimized for continuous conversation")
        session_logger.info("   🔄 CONTINUITY: Fixed to prevent conversation restarts")
        
        return session
        
    except Exception as e:
        session_logger.error(f"❌ Session creation failed: {e}")
        raise Exception(f"Failed to create session: {e}")