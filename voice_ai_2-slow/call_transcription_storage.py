# call_transcription_storage.py - SIMPLIFIED VERSION
"""
SIMPLIFIED: MongoDB-Only Call Transcription Storage System WITHOUT caller recognition
Removed all caller identification and returning caller logic - treats everyone as new
"""
import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import hashlib
import uuid
from enum import Enum

# MongoDB and Redis imports
try:
    from pymongo import AsyncMongoClient
    from pymongo.errors import PyMongoError, ConnectionFailure
    MONGODB_AVAILABLE = True
except ImportError:
    raise ImportError("PyMongo is required for MongoDB-only mode. Install with: pip install pymongo[srv]")

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from config import config

logger = logging.getLogger(__name__)

class StorageBackend(Enum):
    MONGODB_ONLY = "mongodb_only"

@dataclass
class TranscriptionSegment:
    """Individual transcription segment (user or agent speech)"""
    segment_id: str
    session_id: str
    caller_id: str
    speaker: str  # "user" or "agent" 
    text: str
    timestamp: float
    is_final: bool
    confidence: Optional[float] = None
    duration_ms: Optional[int] = None
    
@dataclass
class ConversationItem:
    """Complete conversation turn"""
    item_id: str
    session_id: str
    caller_id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: float
    interrupted: bool = False
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class CallSession:
    """Complete call session record"""
    session_id: str
    caller_id: str
    phone_number: str
    start_time: float
    end_time: Optional[float] = None
    duration_seconds: Optional[float] = None
    total_turns: int = 0
    status: str = "active"  # active, completed, failed
    metadata: Optional[Dict[str, Any]] = None

class VoiceAICacheManager:
    """SIMPLIFIED: Redis cache manager without caller profile caching"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client = None
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0
        }
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            if REDIS_AVAILABLE:
                self.redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_timeout=1.0,
                    socket_connect_timeout=0.5,
                    retry_on_timeout=False
                )
                await self.redis_client.ping()
                logger.info("✅ Redis cache manager initialized")
                return True
            else:
                logger.warning("⚠️ Redis not available, caching disabled")
                return False
        except Exception as e:
            logger.error(f"❌ Redis initialization failed: {e}")
            return False
    
    async def cache_session_context(self, session_id: str, context_data: Dict[str, Any], 
                                  ttl: int = None):
        """Cache session context with optimized TTL"""
        if not self.redis_client:
            return
        
        try:
            cache_key = f"voice_session:{session_id}"
            ttl = ttl or config.redis_session_ttl
            
            await self.redis_client.setex(
                cache_key, 
                ttl, 
                json.dumps(context_data, default=str)
            )
            logger.debug(f"📝 Cached session context: {session_id}")
            
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.debug(f"Cache write error: {e}")
    
    async def get_session_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session context from cache"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = f"voice_session:{session_id}"
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                self.cache_stats["hits"] += 1
                return json.loads(cached_data)
            else:
                self.cache_stats["misses"] += 1
                return None
                
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.debug(f"Cache read error: {e}")
            return None
    
    async def invalidate_session_cache(self, session_id: str):
        """Invalidate session-related cache"""
        if not self.redis_client:
            return
        
        try:
            pattern = f"*{session_id}*"
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
                
        except Exception as e:
            logger.debug(f"Cache invalidation error: {e}")
    
    async def clear_all_voice_cache(self):
        """Clear all voice AI related cache"""
        if not self.redis_client:
            return
        
        try:
            patterns = ["voice_session:*"]
            total_deleted = 0
            
            for pattern in patterns:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    deleted = await self.redis_client.delete(*keys)
                    total_deleted += deleted
                    logger.info(f"🧹 Cleared {deleted} keys matching {pattern}")
            
            logger.info(f"✅ Total cache keys cleared: {total_deleted}")
            return total_deleted
            
        except Exception as e:
            logger.error(f"❌ Failed to clear cache: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hit_rate_percent": round(hit_rate, 2),
            "total_hits": self.cache_stats["hits"],
            "total_misses": self.cache_stats["misses"],
            "total_errors": self.cache_stats["errors"],
            "cache_available": self.redis_client is not None
        }

class DatabaseCircuitBreaker:
    """Circuit breaker for database operations"""
    
    def __init__(self, threshold: int = None, timeout: int = None):
        self.threshold = threshold or config.circuit_breaker_threshold
        self.timeout = timeout or config.circuit_breaker_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    async def execute(self, operation):
        """Execute operation with circuit breaker protection"""
        if self.state == 'OPEN':
            if time.time() * 1000 - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception('Circuit breaker is OPEN - Database unavailable')
        
        try:
            result = await operation()
            self.reset()
            return result
        except Exception as error:
            self.record_failure()
            raise error
    
    def record_failure(self):
        """Record a failure"""
        self.failure_count += 1
        self.last_failure_time = time.time() * 1000
        
        if self.failure_count >= self.threshold:
            self.state = 'OPEN'
            logger.warning(f"🚨 Circuit breaker OPEN after {self.failure_count} failures")
    
    def reset(self):
        """Reset circuit breaker on success"""
        if self.failure_count > 0:
            logger.info(f"✅ Circuit breaker reset after {self.failure_count} failures")
        self.failure_count = 0
        self.state = 'CLOSED'

class MongoDBCallTranscriptionStorage:
    """
    SIMPLIFIED: MongoDB-Only storage system without caller recognition
    """
    
    def __init__(self):
        # MongoDB setup
        self.mongo_client = None
        self.mongo_db = None
        self.mongodb_available = False
        
        # Cache manager
        self.cache_manager = VoiceAICacheManager(config.redis_url)
        
        # Circuit breaker
        self.mongo_circuit_breaker = DatabaseCircuitBreaker()
        
        # Storage state
        self.storage_backend = StorageBackend.MONGODB_ONLY
        
        # Performance metrics
        self.metrics = {
            "mongodb_operations": 0,
            "cache_operations": 0,
            "avg_response_time_ms": 0.0
        }
        
        # In-memory cache for active sessions (fallback)
        self.active_sessions = {}
    
    async def initialize(self):
        """Initialize MongoDB storage system"""
        logger.info("🚀 Initializing SIMPLIFIED MongoDB Storage (No Caller Recognition)")
        
        # Initialize cache
        cache_success = await self.cache_manager.initialize()
        
        # Initialize MongoDB
        mongodb_success = await self._init_mongodb()
        
        if not mongodb_success:
            raise Exception("MongoDB initialization failed - required for MongoDB-only mode")
        
        self.storage_backend = StorageBackend.MONGODB_ONLY
        logger.info("📊 Storage Backend: MongoDB Only (Simplified)")
        
        logger.info(f"✅ SIMPLIFIED MongoDB storage initialized - Cache: {'✅' if cache_success else '❌'}")
        return True
    
    async def _init_mongodb(self):
        """Initialize MongoDB connection with optimizations"""
        try:
            # Create optimized MongoDB client
            self.mongo_client = AsyncMongoClient(
                config.get_optimized_mongodb_url(),
                maxPoolSize=config.mongodb_max_pool_size,
                minPoolSize=config.mongodb_min_pool_size,
                maxIdleTimeMS=config.mongodb_max_idle_time_ms,
                waitQueueTimeoutMS=500,
                connectTimeoutMS=500,
                serverSelectionTimeoutMS=200,
                socketTimeoutMS=2000,
                heartbeatFrequencyMS=5000
            )
            
            self.mongo_db = self.mongo_client[config.mongodb_database]
            
            # Test connection
            await self.mongo_client.admin.command('ping')
            
            # Create indexes for optimal performance
            await self._create_mongodb_indexes()
            
            self.mongodb_available = True
            logger.info("✅ MongoDB initialized with voice AI optimizations")
            return True
            
        except Exception as e:
            logger.error(f"❌ MongoDB initialization failed: {e}")
            self.mongodb_available = False
            return False
    
    async def _create_mongodb_indexes(self):
        """Create optimized indexes for voice AI workloads"""
        try:
            # Call sessions indexes
            await self.mongo_db.call_sessions.create_index("session_id", unique=True)
            await self.mongo_db.call_sessions.create_index("phone_number")
            await self.mongo_db.call_sessions.create_index([("start_time", -1)])
            
            # Transcription segments indexes
            await self.mongo_db.transcription_segments.create_index([
                ("session_id", 1),
                ("timestamp", 1)
            ])
            
            # Conversation items indexes
            await self.mongo_db.conversation_items.create_index([
                ("session_id", 1),
                ("timestamp", 1)
            ])
            
            logger.info("✅ MongoDB indexes created for optimal voice AI performance")
            
        except Exception as e:
            logger.warning(f"⚠️ Index creation warning: {e}")
    
    def _generate_ids(self) -> tuple[str, str]:
        """Generate session_id and caller_id"""
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        caller_id = f"caller_{hashlib.md5(str(time.time()).encode()).hexdigest()[:10]}"
        return session_id, caller_id
    
    # === SIMPLIFIED PUBLIC API METHODS ===
    
    async def start_call_session(
        self, 
        phone_number: str, 
        session_metadata: Optional[Dict[str, Any]] = None
    ) -> tuple[str, str]:
        """SIMPLIFIED: Start a new call session - always treats as new caller"""
        start_time = time.time()
        
        try:
            logger.info(f"📞 New call session: {phone_number}")
            
            # SIMPLIFIED: Always generate new IDs (no caller lookup)
            session_id = f"session_{uuid.uuid4().hex[:12]}"
            caller_id = f"caller_{hashlib.md5((phone_number + '_' + str(time.time())).encode()).hexdigest()[:10]}"
            
            # Create call session
            call_session = CallSession(
                session_id=session_id,
                caller_id=caller_id,
                phone_number=phone_number,
                start_time=time.time(),
                metadata=session_metadata or {}
            )
            
            # Save to MongoDB
            await self._save_call_session_mongo(call_session)
            
            # Cache session context
            await self.cache_manager.cache_session_context(
                session_id,
                {
                    "caller_id": caller_id,
                    "phone_number": phone_number,
                    "start_time": call_session.start_time,
                    "simplified_mode": True
                }
            )
            
            response_time = (time.time() - start_time) * 1000
            self._update_metrics("start_session", response_time)
            
            logger.info(f"🎯 Call session started in {response_time:.1f}ms: {session_id}")
            logger.info(f"📊 Mode: Simplified (no caller recognition)")
            
            return session_id, caller_id
            
        except Exception as e:
            logger.error(f"❌ Failed to start call session: {e}")
            raise
    
    async def save_transcription_segment(
        self,
        session_id: str,
        caller_id: str,
        speaker: str,
        text: str,
        is_final: bool,
        confidence: Optional[float] = None,
        duration_ms: Optional[int] = None
    ) -> str:
        """Save transcription segment with ultra-fast writes"""
        start_time = time.time()
        
        try:
            segment = TranscriptionSegment(
                segment_id=f"seg_{uuid.uuid4().hex[:12]}",
                session_id=session_id,
                caller_id=caller_id,
                speaker=speaker,
                text=text,
                timestamp=time.time(),
                is_final=is_final,
                confidence=confidence,
                duration_ms=duration_ms
            )
            
            # Fire-and-forget write for minimal latency
            asyncio.create_task(self._save_transcription_segment_mongo(segment))
            
            response_time = (time.time() - start_time) * 1000
            self._update_metrics("save_transcription", response_time)
            
            logger.debug(f"💬 Transcription saved in {response_time:.1f}ms: {speaker}")
            return segment.segment_id
            
        except Exception as e:
            logger.error(f"❌ Failed to save transcription segment: {e}")
            return ""
    
    async def save_conversation_item(
        self,
        session_id: str,
        caller_id: str,
        role: str,
        content: str,
        interrupted: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save conversation item with caching"""
        start_time = time.time()
        
        try:
            item = ConversationItem(
                item_id=f"item_{uuid.uuid4().hex[:12]}",
                session_id=session_id,
                caller_id=caller_id,
                role=role,
                content=content,
                timestamp=time.time(),
                interrupted=interrupted,
                metadata=metadata
            )
            
            # Save to MongoDB
            await self._save_conversation_item_mongo(item)
            
            # Update session cache
            await self._update_session_cache(session_id, item)
            
            response_time = (time.time() - start_time) * 1000
            self._update_metrics("save_conversation", response_time)
            
            logger.debug(f"📝 Conversation item saved in {response_time:.1f}ms: {role}")
            return item.item_id
            
        except Exception as e:
            logger.error(f"❌ Failed to save conversation item: {e}")
            return ""
    
    async def get_conversation_history(
        self, 
        session_id: str, 
        limit: int = 50
    ) -> List[ConversationItem]:
        """Get conversation history for current session only"""
        start_time = time.time()
        
        try:
            # Get conversation history for this session only
            history = await self._get_session_conversation_history_mongo(session_id, limit)
            
            response_time = (time.time() - start_time) * 1000
            self._update_metrics("get_history", response_time)
            
            logger.info(f"📚 Retrieved {len(history)} items in {response_time:.1f}ms")
            return history
            
        except Exception as e:
            logger.error(f"❌ Failed to get conversation history: {e}")
            return []
    
    async def end_call_session(self, session_id: str) -> bool:
        """End call session and update statistics"""
        try:
            # Update session if in active sessions
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.end_time = time.time()
                session.duration_seconds = session.end_time - session.start_time
                session.status = "completed"
                
                # Save final session state
                await self._save_call_session_mongo(session)
                
                # Remove from active sessions
                del self.active_sessions[session_id]
                
                logger.info(f"✅ Call session ended: {session_id}")
                return True
            else:
                logger.warning(f"⚠️ Session not found in active sessions: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to end call session: {e}")
            return False
    
    async def get_recent_sessions(self, limit: int = 10) -> List[CallSession]:
        """Get recent call sessions for monitoring"""
        try:
            return await self._get_recent_sessions_mongo(limit)
        except Exception as e:
            logger.error(f"❌ Failed to get recent sessions: {e}")
            return []
    
    # === MONGODB SPECIFIC METHODS ===
    
    async def _save_transcription_segment_mongo(self, segment: TranscriptionSegment):
        """Save transcription to MongoDB"""
        try:
            doc = {
                "segment_id": segment.segment_id,
                "session_id": segment.session_id,
                "caller_id": segment.caller_id,
                "speaker": segment.speaker,
                "text": segment.text,
                "timestamp": datetime.fromtimestamp(segment.timestamp),
                "is_final": segment.is_final,
                "confidence": segment.confidence,
                "duration_ms": segment.duration_ms,
                "created_at": datetime.utcnow()
            }
            
            await self.mongo_db.transcription_segments.insert_one(doc)
            self.metrics["mongodb_operations"] += 1
            
        except Exception as e:
            logger.debug(f"MongoDB transcription write failed: {e}")
            raise
    
    async def _save_conversation_item_mongo(self, item: ConversationItem):
        """Save conversation item to MongoDB"""
        try:
            doc = {
                "item_id": item.item_id,
                "session_id": item.session_id,
                "caller_id": item.caller_id,
                "role": item.role,
                "content": item.content,
                "timestamp": datetime.fromtimestamp(item.timestamp),
                "interrupted": item.interrupted,
                "metadata": item.metadata,
                "created_at": datetime.utcnow()
            }
            
            await self.mongo_db.conversation_items.insert_one(doc)
            self.metrics["mongodb_operations"] += 1
            
        except Exception as e:
            logger.error(f"MongoDB conversation write failed: {e}")
            raise
    
    async def _save_call_session_mongo(self, session: CallSession):
        """Save call session to MongoDB"""
        try:
            doc = {
                "session_id": session.session_id,
                "caller_id": session.caller_id,
                "phone_number": session.phone_number,
                "start_time": datetime.fromtimestamp(session.start_time),
                "end_time": datetime.fromtimestamp(session.end_time) if session.end_time else None,
                "duration_seconds": session.duration_seconds,
                "total_turns": session.total_turns,
                "status": session.status,
                "metadata": session.metadata,
                "created_at": datetime.utcnow()
            }
            
            await self.mongo_db.call_sessions.insert_one(doc)
            self.metrics["mongodb_operations"] += 1
            
        except Exception as e:
            logger.error(f"MongoDB session write failed: {e}")
            raise
    
    async def _get_session_conversation_history_mongo(self, session_id: str, limit: int) -> List[ConversationItem]:
        """Get conversation history for specific session from MongoDB"""
        try:
            cursor = self.mongo_db.conversation_items.find({
                "session_id": session_id
            }).sort("timestamp", -1).limit(limit)
            
            history = []
            async for doc in cursor:
                history.append(ConversationItem(
                    item_id=doc["item_id"],
                    session_id=doc["session_id"],
                    caller_id=doc["caller_id"],
                    role=doc["role"],
                    content=doc["content"],
                    timestamp=doc["timestamp"].timestamp(),
                    interrupted=doc.get("interrupted", False),
                    metadata=doc.get("metadata")
                ))
            
            return history
            
        except Exception as e:
            logger.error(f"MongoDB history query failed: {e}")
            raise
    
    async def _get_recent_sessions_mongo(self, limit: int) -> List[CallSession]:
        """Get recent sessions from MongoDB"""
        try:
            cursor = self.mongo_db.call_sessions.find().sort("start_time", -1).limit(limit)
            
            sessions = []
            async for doc in cursor:
                sessions.append(CallSession(
                    session_id=doc["session_id"],
                    caller_id=doc["caller_id"],
                    phone_number=doc["phone_number"],
                    start_time=doc["start_time"].timestamp(),
                    end_time=doc["end_time"].timestamp() if doc.get("end_time") else None,
                    duration_seconds=doc.get("duration_seconds"),
                    total_turns=doc.get("total_turns", 0),
                    status=doc.get("status", "active"),
                    metadata=doc.get("metadata", {})
                ))
            
            return sessions
            
        except Exception as e:
            logger.error(f"MongoDB sessions query failed: {e}")
            raise
    
    # === UTILITY METHODS ===
    
    async def _update_session_cache(self, session_id: str, item: ConversationItem):
        """Update session cache with new conversation item"""
        try:
            cache_key = f"voice_session:{session_id}"
            cached_context = await self.cache_manager.get_session_context(cache_key)
            
            if cached_context:
                # Add new item to cached context
                if "recent_items" not in cached_context:
                    cached_context["recent_items"] = []
                
                cached_context["recent_items"].append(asdict(item))
                
                # Keep only last 10 items in cache
                if len(cached_context["recent_items"]) > 10:
                    cached_context["recent_items"] = cached_context["recent_items"][-10:]
                
                # Update cache
                await self.cache_manager.cache_session_context(
                    session_id,
                    cached_context,
                    ttl=300
                )
        except Exception as e:
            logger.debug(f"Session cache update error: {e}")
    
    def _update_metrics(self, operation: str, response_time_ms: float):
        """Update performance metrics"""
        self.metrics[f"{operation}_count"] = self.metrics.get(f"{operation}_count", 0) + 1
        self.metrics["avg_response_time_ms"] = (
            (self.metrics["avg_response_time_ms"] + response_time_ms) / 2
        )
    
    # === CLEANUP AND DIAGNOSTIC METHODS ===
    
    async def clear_all_data(self) -> Dict[str, int]:
        """Clear all data from both MongoDB and Redis"""
        try:
            logger.info("🧹 Clearing ALL data from MongoDB and Redis...")
            
            # Clear MongoDB
            mongo_deleted = 0
            collections = ["call_sessions", "conversation_items", "transcription_segments"]
            
            for collection_name in collections:
                collection = self.mongo_db[collection_name]
                result = await collection.delete_many({})
                mongo_deleted += result.deleted_count
                logger.info(f"✅ MongoDB {collection_name}: {result.deleted_count} documents deleted")
            
            # Clear Redis cache
            redis_deleted = await self.cache_manager.clear_all_voice_cache()
            
            # Clear in-memory caches
            self.active_sessions.clear()
            
            logger.info(f"✅ Total cleanup: MongoDB={mongo_deleted}, Redis={redis_deleted}")
            
            return {
                "mongodb_deleted": mongo_deleted,
                "redis_deleted": redis_deleted,
                "total_deleted": mongo_deleted + redis_deleted
            }
            
        except Exception as e:
            logger.error(f"❌ Data cleanup failed: {e}")
            return {"error": str(e)}
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        cache_stats = self.cache_manager.get_cache_stats()
        
        return {
            "storage_backend": self.storage_backend.value,
            "mongodb_available": self.mongodb_available,
            "cache_available": cache_stats["cache_available"],
            "operations": self.metrics,
            "cache_performance": cache_stats,
            "circuit_breaker": {
                "mongo_state": self.mongo_circuit_breaker.state,
                "mongo_failures": self.mongo_circuit_breaker.failure_count
            },
            "simplified_mode": True,
            "caller_recognition": False
        }

# Global storage instance
call_storage = MongoDBCallTranscriptionStorage()

async def get_call_storage() -> MongoDBCallTranscriptionStorage:
    """Get the global call storage instance"""
    if not hasattr(call_storage, '_initialized'):
        await call_storage.initialize()
        call_storage._initialized = True
    return call_storage