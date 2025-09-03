# services/session.py - FIXED FOR COMPATIBILITY
"""
FIXED: Ultra-low latency session configuration compatible with current LiveKit version
Target: 50-70% latency reduction through optimized STT, LLM, and session config
"""
import httpx
from livekit.agents import AgentSession
from livekit.plugins import google, openai, elevenlabs, silero

from logging_config import create_call_logger
from models.call_data import CallData
from config import config

session_logger = create_call_logger("session")

async def create_optimized_session(userdata: CallData) -> AgentSession[CallData]:
    """FIXED: Ultra-fast session configuration compatible with current LiveKit"""
    
    session_logger.info("⚡ Creating ULTRA-FAST session for minimal latency")
    
    try:
        # FIXED STT: Better accuracy for conversation capture
        stt = google.STT(
            # FIXED: Use latest_long for better conversation capture
            model="latest_long",  # Better for capturing complete thoughts
            
            # CONVERSATION OPTIMIZATIONS:
            languages=["en-US"],
            detect_language=False,  # Skip language detection overhead
            
            # ACCURACY FIXES for better conversation flow:
            interim_results=True,    # Enable to capture speech better
            punctuate=True,         # Enable punctuation for clarity
            spoken_punctuation=False, # Keep disabled
            
            # CONFIDENCE OPTIMIZATIONS:
            min_confidence_threshold=0.3,  # Lower for better capture
            
            # STREAMING OPTIMIZATIONS:
            use_streaming=True,
            sample_rate=16000,      # Optimal balance of quality/speed
            
            # CREDENTIALS
            credentials_info=config.get_google_credentials_dict(),
            location="global",
        )
        
        # FIXED LLM: Compatible configuration without unsupported parameters
        llm = openai.LLM(
            model="gpt-4o-mini",           # Fastest model available
            temperature=0.1,               # Lower = faster generation
            max_completion_tokens=120      # Shorter responses = faster
            # Note: Removed unsupported timeout and max_retries parameters
        )
        
        # OPTIMIZED TTS: Fastest synthesis
        tts = elevenlabs.TTS(
            voice_id="pNInz6obpgDQGcFmaJgB",  # Adam
            voice_settings=elevenlabs.VoiceSettings(
                stability=0.7,           # Slightly lower for speed
                similarity_boost=0.8,    # Slightly lower for speed
                style=0.0,               # No style processing
                speed=1.0,               # Normal speed
                use_speaker_boost=False, # Skip boost processing
            ),
            model="eleven_turbo_v2_5",      # Fastest model
            api_key=config.elevenlabs_api_key,
            # LATENCY OPTIMIZATION:
            chunk_length_schedule=[50],     # Smaller chunks = faster start
        )
        
        # FIXED VAD: Compatible configuration without unsupported parameters
        vad = silero.VAD.load()  # Use default settings for compatibility
        
        # OPTIMIZED SESSION: Minimal latency configuration
        session = AgentSession[CallData](
            # Core components
            stt=stt,
            llm=llm,
            tts=tts,
            vad=vad,
            
            # CRITICAL LATENCY OPTIMIZATIONS:
            allow_interruptions=True,
            min_interruption_duration=0.8,   # Faster interruption
            min_endpointing_delay=1.2,       # Shorter delay = faster response
            max_endpointing_delay=2.8,       # Prevent long waits
            
            userdata=userdata,
        )
        
        session_logger.info("✅ ULTRA-FAST session created successfully")
        session_logger.info("   🎤 STT: Google Cloud latest_short (FAST)")
        session_logger.info("   🧠 LLM: GPT-4o-mini (max_tokens=120)")
        session_logger.info("   🗣️ TTS: ElevenLabs Turbo (optimized)")
        session_logger.info("   ⏱️ LATENCY: Optimized for <1.5s response")
        session_logger.info("   🔄 INTERRUPTIONS: Aggressive (0.8s)")
        
        return session
        
    except Exception as e:
        session_logger.error(f"❌ Optimized session creation failed: {e}")
        
        # FALLBACK: Create basic session if optimized version fails
        session_logger.info("⚠️ Falling back to basic session configuration...")
        try:
            # Basic STT
            basic_stt = google.STT(
                model="latest_short",
                languages=["en-US"],
                credentials_info=config.get_google_credentials_dict(),
            )
            
            # Basic LLM
            basic_llm = openai.LLM(
                model="gpt-4o-mini",
                temperature=0.2
            )
            
            # Basic TTS
            basic_tts = elevenlabs.TTS(
                voice_id="pNInz6obpgDQGcFmaJgB",
                api_key=config.elevenlabs_api_key,
            )
            
            # Basic VAD
            basic_vad = silero.VAD.load()
            
            # Basic session
            session = AgentSession[CallData](
                stt=basic_stt,
                llm=basic_llm,
                tts=basic_tts,
                vad=basic_vad,
                userdata=userdata,
            )
            
            session_logger.info("✅ Basic session created as fallback")
            return session
            
        except Exception as fallback_error:
            session_logger.error(f"❌ Even fallback session failed: {fallback_error}")
            raise Exception(f"Failed to create any session: {fallback_error}")


# PERFORMANCE MONITORING
class SessionPerformanceMonitor:
    """Monitor session performance for latency optimization"""
    
    def __init__(self):
        self.metrics = {
            "stt_latency": [],
            "llm_latency": [], 
            "tts_latency": [],
            "total_response_time": []
        }
    
    def record_metric(self, metric_type: str, latency_ms: float):
        """Record performance metric"""
        if metric_type in self.metrics:
            self.metrics[metric_type].append(latency_ms)
            
            # Keep only last 100 measurements
            if len(self.metrics[metric_type]) > 100:
                self.metrics[metric_type] = self.metrics[metric_type][-100:]
    
    def get_average_latency(self, metric_type: str) -> float:
        """Get average latency for metric type"""
        if metric_type in self.metrics and self.metrics[metric_type]:
            return sum(self.metrics[metric_type]) / len(self.metrics[metric_type])
        return 0.0
    
    def get_p95_latency(self, metric_type: str) -> float:
        """Get 95th percentile latency"""
        if metric_type in self.metrics and self.metrics[metric_type]:
            sorted_metrics = sorted(self.metrics[metric_type])
            index = int(0.95 * len(sorted_metrics))
            return sorted_metrics[index] if index < len(sorted_metrics) else 0.0
        return 0.0
    
    def print_performance_summary(self):
        """Print performance summary"""
        session_logger.info("📊 SESSION PERFORMANCE SUMMARY")
        for metric_type in self.metrics:
            avg = self.get_average_latency(metric_type)
            p95 = self.get_p95_latency(metric_type)
            session_logger.info(f"   {metric_type}: avg={avg:.1f}ms, p95={p95:.1f}ms")

# Global performance monitor
performance_monitor = SessionPerformanceMonitor()