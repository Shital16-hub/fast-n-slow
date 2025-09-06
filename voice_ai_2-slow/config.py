# config.py - FIXED FOR LOCAL LIVEKIT DEPLOYMENT WITH PERFORMANCE OPTIMIZATIONS
"""
FIXED: Configuration for Local LiveKit Server with SIP on port 5063 + Ultra-Fast Performance Settings
"""
import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import json

load_dotenv()

class LocalLiveKitConfig(BaseSettings):
    """FIXED: Configuration for Local LiveKit deployment with SIP on port 5063 + Performance Optimizations"""
    
    # ✅ LOCAL LIVEKIT SETTINGS (FIXED)
    livekit_url: str = Field(default="ws://localhost:7880", env="LIVEKIT_URL")
    livekit_api_key: str = Field(default="devkey", env="LIVEKIT_API_KEY")
    livekit_api_secret: str = Field(default="secret", env="LIVEKIT_API_SECRET")
    
    # 🔥 LOCAL SIP CONFIGURATION (port 5063 for external, 5060 internal)
    local_sip_port: int = Field(default=5070, env="LOCAL_SIP_PORT")  # External port
    local_sip_internal_port: int = Field(default=5070, env="LOCAL_SIP_INTERNAL_PORT")  # Container port
    local_sip_ip: str = Field(default="15.204.54.41", env="LOCAL_SIP_IP")
    
    # 🔥 FREESWITCH CONFIGURATION (UPDATED for port 5063)
    freeswitch_server_ip: str = Field(default="15.204.54.41", env="FREESWITCH_SERVER_IP")
    freeswitch_username: str = Field(default="admin@15.204.54.41", env="FREESWITCH_USERNAME")
    freeswitch_password: str = Field(default="TemOFgULiSdthb4YR2K7EOIj8", env="FREESWITCH_PASSWORD")
    freeswitch_web_url: str = Field(default="https://pbxai2.logicalcrm.com", env="FREESWITCH_WEB_URL")
    
    # 🔥 PHONE NUMBER CONFIGURATION
    primary_phone_number: str = Field(default="12726639251", env="PRIMARY_PHONE_NUMBER")
    
    # ✅ AI SERVICE API KEYS (unchanged)
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    elevenlabs_api_key: str = Field(default="", env="ELEVENLABS_API_KEY")
    
    # 🚀 GOOGLE CLOUD CONFIGURATION (unchanged)
    google_application_credentials: str = Field(
        default="./my-tts-project-458404-8ab56bac7265.json", 
        env="GOOGLE_APPLICATION_CREDENTIALS"
    )
    google_cloud_project: str = Field(default="my-tts-project-458404", env="GOOGLE_CLOUD_PROJECT")
    google_cloud_location: str = Field(default="global", env="GOOGLE_CLOUD_LOCATION")
    
    # ⚡ FIXED STT CONFIGURATION (CHANGED BACK TO LONG FOR BETTER ACCURACY)
    google_stt_model: str = Field(default="latest_long", env="GOOGLE_STT_MODEL")  # BACK TO LONG FOR ACCURACY
    google_stt_language: str = Field(default="en-US", env="GOOGLE_STT_LANGUAGE")
    google_stt_enable_automatic_punctuation: bool = Field(default=True, env="GOOGLE_STT_AUTO_PUNCTUATION")  # RE-ENABLED
    google_stt_enable_spoken_punctuation: bool = Field(default=False, env="GOOGLE_STT_SPOKEN_PUNCTUATION")
    google_stt_use_enhanced: bool = Field(default=True, env="GOOGLE_STT_USE_ENHANCED")
    google_stt_interim_results: bool = Field(default=True, env="GOOGLE_STT_INTERIM_RESULTS")  # RE-ENABLED FOR BETTER CAPTURE
    google_stt_min_confidence: float = Field(default=0.3, env="GOOGLE_STT_MIN_CONFIDENCE")  # LOWERED FOR BETTER CAPTURE
    
    # ⚡ ULTRA-FAST TIMING SETTINGS (OPTIMIZED)
    min_endpointing_delay: float = Field(default=1.2, env="MIN_ENDPOINTING_DELAY")  # REDUCED
    max_endpointing_delay: float = Field(default=2.8, env="MAX_ENDPOINTING_DELAY")  # REDUCED
    min_interruption_duration: float = Field(default=0.8, env="MIN_INTERRUPTION_DURATION")  # REDUCED
    
    # 🎤 DEEPGRAM STT CONFIGURATION (BACKUP)
    deepgram_api_key: Optional[str] = Field(default="", env="DEEPGRAM_API_KEY")
    deepgram_model: str = Field(default="nova-2-general", env="DEEPGRAM_MODEL")
    
    # ⚡ ULTRA-FAST TTS CONFIGURATION (OPTIMIZED)
    default_voice_id: str = Field(default="pNInz6obpgDQGcFmaJgB", env="TTS_VOICE_ID")  # Adam
    tts_stability: float = Field(default=0.7, env="TTS_STABILITY")  # REDUCED FOR SPEED
    tts_similarity_boost: float = Field(default=0.8, env="TTS_SIMILARITY_BOOST")  # REDUCED FOR SPEED
    tts_style: float = Field(default=0.0, env="TTS_STYLE")  # DISABLED FOR SPEED
    tts_speed: float = Field(default=1.0, env="TTS_SPEED")  # NORMAL SPEED
    tts_use_speaker_boost: bool = Field(default=False, env="TTS_USE_SPEAKER_BOOST")  # DISABLED FOR SPEED
    tts_model: str = Field(default="eleven_turbo_v2_5", env="TTS_MODEL")  # FASTEST MODEL
    
    # 🚀 DATABASE CONFIGURATION (unchanged)
    mongodb_url: str = Field(
        default="mongodb://localhost:27017/voice-ai", 
        env="MONGODB_URL"
    )
    mongodb_database: str = Field(default="voice_ai", env="MONGODB_DATABASE")
    
    # 🚀 REDIS CONFIGURATION (LOCAL)
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_session_ttl: int = Field(default=300, env="REDIS_SESSION_TTL")
    
    # ⚡ ULTRA-FAST QDRANT SETTINGS (OPTIMIZED)
    qdrant_url: str = Field(default="http://localhost:6333", env="QDRANT_URL")
    qdrant_collection_name: str = Field(default="telephony_knowledge", env="QDRANT_COLLECTION")
    qdrant_timeout: int = Field(default=5, env="QDRANT_TIMEOUT")  # AGGRESSIVE TIMEOUT
    
    # ⚡ ULTRA-FAST RAG SETTINGS (OPTIMIZED)
    embedding_model: str = Field(default="text-embedding-3-small", env="EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=512, env="EMBEDDING_DIMENSIONS")
    search_limit: int = Field(default=3, env="SEARCH_LIMIT")  # REDUCED FOR SPEED
    rag_similarity_top_k: int = Field(default=3, env="RAG_SIMILARITY_TOP_K")  # REDUCED
    rag_timeout_seconds: float = Field(default=3.0, env="RAG_TIMEOUT")  # AGGRESSIVE TIMEOUT
    
    # ⚡ ULTRA-FAST DATABASE SETTINGS (OPTIMIZED)
    mongodb_max_pool_size: int = Field(default=20, env="MONGODB_MAX_POOL_SIZE")  # REDUCED
    mongodb_min_pool_size: int = Field(default=5, env="MONGODB_MIN_POOL_SIZE")  # REDUCED
    mongodb_max_idle_time_ms: int = Field(default=10000, env="MONGODB_MAX_IDLE_TIME_MS")  # REDUCED
    
    # ⚡ ULTRA-FAST CIRCUIT BREAKER SETTINGS (OPTIMIZED)
    circuit_breaker_threshold: int = Field(default=3, env="CIRCUIT_BREAKER_THRESHOLD")  # REDUCED
    circuit_breaker_timeout: int = Field(default=30000, env="CIRCUIT_BREAKER_TIMEOUT")  # REDUCED
    
    # ⚡ PERFORMANCE MODE SETTING
    performance_mode: str = Field(default="ultra_fast", env="PERFORMANCE_MODE")
    
    # ⚡ CACHING SETTINGS
    enable_l1_cache: bool = Field(default=True, env="ENABLE_L1_CACHE")
    l1_cache_size: int = Field(default=50, env="L1_CACHE_SIZE")
    l2_cache_size: int = Field(default=200, env="L2_CACHE_SIZE")
    
    # ⚡ ASYNC DATABASE SETTINGS
    async_database_writes: bool = Field(default=True, env="ASYNC_DATABASE_WRITES")
    database_batch_size: int = Field(default=5, env="DATABASE_BATCH_SIZE")
    database_batch_timeout_ms: float = Field(default=200.0, env="DATABASE_BATCH_TIMEOUT_MS")
    
    # ✅ TRANSFER SETTINGS (unchanged)
    auto_transfer_disabled: bool = Field(default=True, env="AUTO_TRANSFER_DISABLED")

    # TRANSFER CONFIGURATION SETTINGS
    human_agent_number: str = Field(default="+15105550200", env="HUMAN_AGENT_NUMBER")
    human_agent_extension: str = Field(default="200", env="HUMAN_AGENT_EXTENSION") 
    transfer_timeout_seconds: int = Field(default=30, env="TRANSFER_TIMEOUT_SECONDS")
    transfer_enabled: bool = Field(default=True, env="TRANSFER_ENABLED")

    # FusionPBX transfer settings
    fusionpbx_human_ring_group: str = Field(default="201", env="FUSIONPBX_HUMAN_RING_GROUP")
    fusionpbx_transfer_context: str = Field(default="default", env="FUSIONPBX_TRANSFER_CONTEXT")

    def get_transfer_config(self) -> dict:
        """Get transfer configuration for FusionPBX"""
        return {
            "human_agent_number": self.human_agent_number,
            "human_agent_extension": self.human_agent_extension,
            "ring_group": self.fusionpbx_human_ring_group,
            "context": self.fusionpbx_transfer_context,
            "timeout": self.transfer_timeout_seconds,
            "enabled": self.transfer_enabled
        }

    
    # ✅ PATHS (unchanged)
    @property
    def project_root(self) -> Path:
        return Path(__file__).parent
    
    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"
    
    # ⚡ ULTRA-FAST MODE METHODS
    def is_ultra_fast_mode(self) -> bool:
        """Check if ultra-fast mode is enabled"""
        return self.performance_mode == "ultra_fast"
    
    def get_ultra_fast_stt_config(self) -> dict:
        """Get ultra-fast STT configuration"""
        return {
            "model": self.google_stt_model,
            "interim_results": self.google_stt_interim_results,
            "min_confidence": self.google_stt_min_confidence,
            "enable_automatic_punctuation": self.google_stt_enable_automatic_punctuation,
            "enable_spoken_punctuation": self.google_stt_enable_spoken_punctuation,
        }
    
    def get_ultra_fast_timing_config(self) -> dict:
        """Get ultra-fast timing configuration"""
        return {
            "min_endpointing_delay": self.min_endpointing_delay,
            "max_endpointing_delay": self.max_endpointing_delay,
            "min_interruption_duration": self.min_interruption_duration,
        }
    
    def get_ultra_fast_tts_config(self) -> dict:
        """Get ultra-fast TTS configuration"""
        return {
            "stability": self.tts_stability,
            "similarity_boost": self.tts_similarity_boost,
            "style": self.tts_style,
            "speed": self.tts_speed,
            "use_speaker_boost": self.tts_use_speaker_boost,
            "model": self.tts_model
        }
    
    def get_performance_targets(self) -> dict:
        """Get performance targets for monitoring"""
        if self.is_ultra_fast_mode():
            return {
                "total_response_time_ms": 1500,
                "initialization_time_ms": 500,
                "stt_latency_ms": 300,
                "llm_latency_ms": 600, 
                "tts_latency_ms": 400,
                "rag_latency_ms": 200,
                "database_latency_ms": 10,
                "cache_hit_rate_percent": 70
            }
        else:
            return {
                "total_response_time_ms": 2500,
                "initialization_time_ms": 1000,
                "cache_hit_rate_percent": 50
            }
    
    # 🔥 LOCAL LIVEKIT SIP HELPER METHODS (unchanged)
    def get_local_sip_address(self) -> str:
        """Get local SIP address for FusionPBX gateway configuration"""
        return f"{self.local_sip_ip}:{self.local_sip_port}"
    
    def get_fusionpbx_gateway_config_local(self) -> dict:
        """Get FusionPBX gateway configuration for LOCAL LiveKit SIP (port 5063)"""
        return {
            "gateway_name": "livekit-local-gateway",
            "proxy": f"{self.local_sip_ip}:{self.local_sip_port}",  # Points to port 5070
            "register": False,
            "context": "public",
            "profile": "external",
            "enabled": True,
            "description": f"Local LiveKit SIP Gateway on port {self.local_sip_port}"
        }
    
    def get_fusionpbx_ringgroup_config_local(self) -> dict:
        """Get FusionPBX ring group configuration for LOCAL LiveKit SIP"""
        return {
            "name": "livekit-voice-ai-local",
            "extension": "8888",
            "strategy": "simultaneous",
            "destinations": [
                f"sofia/gateway/livekit-local-gateway/{self.primary_phone_number}@{self.local_sip_ip}:{self.local_sip_port}"
            ],
            "description": f"Local LiveKit Voice AI Ring Group (port {self.local_sip_port})"
        }
    
    def get_livekit_local_urls(self) -> dict:
        """Get all local LiveKit service URLs"""
        return {
            "livekit_server": self.livekit_url,
            "sip_service": f"sip:{self.local_sip_ip}:{self.local_sip_port}",
            "redis": self.redis_url,
            "qdrant": self.qdrant_url
        }
    
    def get_google_credentials_dict(self) -> Optional[dict]:
        """Get Google credentials as dictionary from the JSON file"""
        try:
            with open(self.google_application_credentials, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load Google credentials: {e}")
            return None
    
    def ensure_google_credentials(self) -> bool:
        """Ensure Google credentials are properly set up"""
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.google_application_credentials
        
        if not Path(self.google_application_credentials).exists():
            print(f"❌ Google credentials file not found: {self.google_application_credentials}")
            return False
        
        try:
            creds = self.get_google_credentials_dict()
            if not creds or "project_id" not in creds:
                print("❌ Invalid Google credentials format")
                return False
            
            print(f"✅ Google credentials loaded: Project {creds['project_id']}")
            return True
            
        except Exception as e:
            print(f"❌ Google credentials error: {e}")
            return False
    
    def get_optimized_mongodb_url(self) -> str:
        """Get MongoDB connection string"""
        return self.mongodb_url
    
    def ensure_directories(self):
        """Create necessary directories"""
        self.data_dir.mkdir(exist_ok=True)
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

# Global configuration instance
config = LocalLiveKitConfig()
config.ensure_directories()

def validate_config():
    """Validate configuration for LOCAL LiveKit deployment with ULTRA-FAST mode"""
    required_fields = [
        ("OPENAI_API_KEY", config.openai_api_key),
        ("MONGODB_URL", config.mongodb_url),
        ("ELEVENLABS_API_KEY", config.elevenlabs_api_key),
        ("LIVEKIT_URL", config.livekit_url),
        ("LIVEKIT_API_KEY", config.livekit_api_key),
    ]
    
    missing_fields = [field for field, value in required_fields if not value]
    
    if missing_fields:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_fields)}")
    
    # Ensure Google credentials are set up
    google_ok = config.ensure_google_credentials()
    
    print("⚡ ULTRA-FAST LOCAL LIVEKIT DEPLOYMENT Configuration")
    print(f"📞 FreeSwitch Server: {config.freeswitch_server_ip}")
    print(f"🌐 LiveKit URL: {config.livekit_url}")
    print(f"📡 Local SIP: {config.local_sip_ip}:{config.local_sip_port}")
    print(f"🆔 Primary Phone: {config.primary_phone_number}")
    print(f"⚡ Performance Mode: {config.performance_mode}")
    print(f"🎤 STT Model: {config.google_stt_model} (OPTIMIZED)")
    print(f"🎙️ TTS: ElevenLabs {config.tts_model} (OPTIMIZED)")
    print(f"🗄️ Database: MongoDB (ASYNC BATCHING)")
    print(f"🚀 Deployment: Ultra-Fast Local LiveKit Stack")
    
    # Show performance targets
    if config.is_ultra_fast_mode():
        print("\n⚡ ULTRA-FAST PERFORMANCE TARGETS:")
        targets = config.get_performance_targets()
        print(f"   🎯 Total Response Time: <{targets['total_response_time_ms']}ms")
        print(f"   🚀 Initialization: <{targets['initialization_time_ms']}ms")
        print(f"   💾 Cache Hit Rate: >{targets['cache_hit_rate_percent']}%")
        print(f"   🔍 RAG Latency: <{targets['rag_latency_ms']}ms")
        print(f"   💾 Database Latency: <{targets['database_latency_ms']}ms")
    
    if not google_ok:
        print(f"\n⚠️ WARNING: Google Cloud credentials not properly configured!")
        print(f"   Expected file: {config.google_application_credentials}")

if __name__ == "__main__":
    validate_config()