# config.py - FIXED FOR LOCAL LIVEKIT DEPLOYMENT
"""
FIXED: Configuration for Local LiveKit Server with SIP on port 5063
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
    """FIXED: Configuration for Local LiveKit deployment with SIP on port 5063"""
    
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
    
    # 🔥 GOOGLE STT CONFIGURATION (unchanged)
    google_stt_model: str = Field(default="latest_long", env="GOOGLE_STT_MODEL")
    google_stt_language: str = Field(default="en-US", env="GOOGLE_STT_LANGUAGE")
    google_stt_enable_automatic_punctuation: bool = Field(default=True, env="GOOGLE_STT_AUTO_PUNCTUATION")
    google_stt_enable_spoken_punctuation: bool = Field(default=False, env="GOOGLE_STT_SPOKEN_PUNCTUATION")
    google_stt_use_enhanced: bool = Field(default=True, env="GOOGLE_STT_USE_ENHANCED")
    google_stt_interim_results: bool = Field(default=True, env="GOOGLE_STT_INTERIM_RESULTS")
    
    # 🔥 TIMING SETTINGS (unchanged)
    min_endpointing_delay: float = Field(default=1.5, env="MIN_ENDPOINTING_DELAY")
    max_endpointing_delay: float = Field(default=4.0, env="MAX_ENDPOINTING_DELAY")
    min_interruption_duration: float = Field(default=0.8, env="MIN_INTERRUPTION_DURATION")
    google_stt_min_confidence: float = Field(default=0.3, env="GOOGLE_STT_MIN_CONFIDENCE")
    
    # 🎤 DEEPGRAM STT CONFIGURATION (BACKUP)
    deepgram_api_key: Optional[str] = Field(default="", env="DEEPGRAM_API_KEY")
    deepgram_model: str = Field(default="nova-2-general", env="DEEPGRAM_MODEL")
    
    # 🎙️ TTS CONFIGURATION (unchanged)
    default_voice_id: str = Field(default="pNInz6obpgDQGcFmaJgB", env="TTS_VOICE_ID")  # Adam
    tts_stability: float = Field(default=0.8, env="TTS_STABILITY")
    tts_similarity_boost: float = Field(default=0.9, env="TTS_SIMILARITY_BOOST")
    tts_style: float = Field(default=0.1, env="TTS_STYLE")
    tts_speed: float = Field(default=0.85, env="TTS_SPEED")
    tts_use_speaker_boost: bool = Field(default=True, env="TTS_USE_SPEAKER_BOOST")
    tts_model: str = Field(default="eleven_turbo_v2_5", env="TTS_MODEL")
    
    # 🚀 DATABASE CONFIGURATION (unchanged)
    mongodb_url: str = Field(
        default="mongodb://localhost:27017/voice-ai", 
        env="MONGODB_URL"
    )
    mongodb_database: str = Field(default="voice_ai", env="MONGODB_DATABASE")
    
    # 🚀 REDIS CONFIGURATION (LOCAL)
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_session_ttl: int = Field(default=300, env="REDIS_SESSION_TTL")
    
    # 🚀 QDRANT SETTINGS (LOCAL)
    qdrant_url: str = Field(default="http://localhost:6333", env="QDRANT_URL")
    qdrant_collection_name: str = Field(default="telephony_knowledge", env="QDRANT_COLLECTION")
    
    # 🚀 RAG SETTINGS (unchanged)
    embedding_model: str = Field(default="text-embedding-3-small", env="EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=512, env="EMBEDDING_DIMENSIONS")
    search_limit: int = Field(default=3, env="SEARCH_LIMIT")
    
    # 🚀 MONGODB PERFORMANCE SETTINGS (unchanged)
    mongodb_max_pool_size: int = Field(default=50, env="MONGODB_MAX_POOL_SIZE")
    mongodb_min_pool_size: int = Field(default=15, env="MONGODB_MIN_POOL_SIZE")
    mongodb_max_idle_time_ms: int = Field(default=20000, env="MONGODB_MAX_IDLE_TIME_MS")
    
    # 🚀 CIRCUIT BREAKER SETTINGS (unchanged)
    circuit_breaker_threshold: int = Field(default=5, env="CIRCUIT_BREAKER_THRESHOLD")
    circuit_breaker_timeout: int = Field(default=60000, env="CIRCUIT_BREAKER_TIMEOUT")
    
    # ✅ TRANSFER SETTINGS (unchanged)
    auto_transfer_disabled: bool = Field(default=True, env="AUTO_TRANSFER_DISABLED")
    
    # ✅ PATHS (unchanged)
    @property
    def project_root(self) -> Path:
        return Path(__file__).parent
    
    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"
    
    # 🔥 LOCAL LIVEKIT SIP HELPER METHODS
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
    """Validate configuration for LOCAL LiveKit deployment"""
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
    
    print("✅ LOCAL LIVEKIT DEPLOYMENT Configuration")
    print(f"📞 FreeSwitch Server: {config.freeswitch_server_ip}")
    print(f"🌐 LiveKit URL: {config.livekit_url}")
    print(f"📡 Local SIP: {config.local_sip_ip}:{config.local_sip_port}")
    print(f"🆔 Primary Phone: {config.primary_phone_number}")
    print(f"🎤 STT Model: {config.google_stt_model}")
    print(f"🎙️ TTS: ElevenLabs Adam")
    print(f"🗄️ Database: MongoDB")
    print(f"🚀 Deployment: Local LiveKit Stack")
    
    if not google_ok:
        print(f"\n⚠️ WARNING: Google Cloud credentials not properly configured!")
        print(f"   Expected file: {config.google_application_credentials}")

if __name__ == "__main__":
    validate_config()