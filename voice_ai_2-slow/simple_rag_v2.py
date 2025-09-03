# simple_rag_v2.py - OPTIMIZED FOR ULTRA-LOW LATENCY
"""
OPTIMIZED RAG System: Ultra-fast knowledge retrieval with aggressive caching and single-query optimization
Target: 70-80% reduction in RAG latency through smart caching and query optimization
"""
import asyncio
import logging
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

# FIXED: Use correct LlamaIndex imports for LiveKit compatibility
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Settings,
    Document
)
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

# FIXED: Use both sync and async clients
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance

from config import config

logger = logging.getLogger(__name__)

class UltraFastRAGSystem:
    """
    OPTIMIZED: Ultra-fast RAG system with aggressive caching and single-query optimization
    Designed for <200ms response times in voice AI applications
    """
    
    def __init__(self):
        self.index: Optional[VectorStoreIndex] = None
        self.query_engine = None
        self.retriever = None
        self.ready = False
        
        # OPTIMIZATION: Multi-level caching system
        self.l1_cache = {}  # Hot cache - most frequent queries (50 items)
        self.l2_cache = {}  # Warm cache - recent queries (200 items)
        self.query_frequency = {}  # Track query frequency
        
        self.max_l1_cache = 50
        self.max_l2_cache = 200
        
        # Clients
        self.sync_client = None
        self.async_client = None
        
        # OPTIMIZATION: Pre-built query patterns for common requests
        self.common_patterns = {
            "towing_standard": "light duty car towing pricing cost base rate",
            "towing_heavy": "heavy duty truck towing pricing cost commercial rate", 
            "battery_service": "jumpstart battery service cost pricing rate",
            "tire_service": "tire change flat tire service cost pricing",
            "lockout_service": "lockout car key service cost pricing",
            "fuel_delivery": "fuel delivery gas diesel service cost pricing"
        }
        
        # Performance metrics
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_queries = 0
        
    async def initialize(self) -> bool:
        """Initialize with optimized settings for speed"""
        try:
            start_time = time.time()
            logger.info("⚡ Initializing ULTRA-FAST RAG system...")
            
            # OPTIMIZED embeddings for speed
            Settings.embed_model = OpenAIEmbedding(
                model="text-embedding-3-small",
                api_key=config.openai_api_key,
                dimensions=512
                # Note: timeout and retries handled internally
            )
            
            # OPTIMIZED LLM for ultra-fast processing
            Settings.llm = OpenAI(
                model="gpt-4o-mini",
                api_key=config.openai_api_key,
                temperature=0.0,  # Deterministic for caching
                max_tokens=200,  # Shorter responses
                # Note: timeout and retries handled internally
            )
            
            # Initialize clients with optimized settings
            try:
                self.sync_client = QdrantClient(
                    url=config.qdrant_url,
                    timeout=5  # Aggressive timeout
                )
                
                self.async_client = AsyncQdrantClient(
                    url=config.qdrant_url,
                    timeout=5  # Aggressive timeout
                )
                
                collections = self.sync_client.get_collections()
                logger.info(f"✅ Qdrant connected: {len(collections.collections)} collections")
                
            except Exception as e:
                logger.error(f"❌ Qdrant connection failed: {e}")
                return False
            
            # Create optimized vector store
            vector_store = QdrantVectorStore(
                client=self.sync_client,
                aclient=self.async_client,
                collection_name=config.qdrant_collection_name
            )
            
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            # Handle existing data
            collection_exists = False
            points_count = 0
            
            try:
                collection_info = self.sync_client.get_collection(config.qdrant_collection_name)
                collection_exists = True
                points_count = collection_info.points_count
                logger.info(f"📊 Found existing collection with {points_count} documents")
            except Exception:
                logger.info("📊 Collection doesn't exist, will create empty index")
            
            # Load or create index
            if collection_exists and points_count > 0:
                logger.info(f"⚡ Loading ultra-fast index with {points_count} documents")
                try:
                    self.index = VectorStoreIndex.from_vector_store(
                        vector_store=vector_store,
                        storage_context=storage_context
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Failed to load existing index, creating new: {e}")
                    self.index = VectorStoreIndex([], storage_context=storage_context)
            else:
                logger.info("📊 Creating new ultra-fast index")
                self.index = VectorStoreIndex([], storage_context=storage_context)
            
            # Create OPTIMIZED query components
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=3,  # Reduced for speed
                response_mode="compact",
                streaming=False,
                verbose=False
            )
            
            self.retriever = self.index.as_retriever(
                similarity_top_k=3,  # Reduced for speed  
                verbose=False
            )
            
            elapsed = (time.time() - start_time) * 1000
            self.ready = True
            
            # OPTIMIZATION: Pre-warm cache with common patterns
            await self._prewarm_cache()
            
            logger.info(f"⚡ ULTRA-FAST RAG system ready in {elapsed:.1f}ms")
            logger.info(f"🚀 Optimized for <200ms response times")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ultra-fast RAG initialization failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    async def retrieve_context(self, query: str, max_results: int = 3) -> str:
        """
        ULTRA-FAST: Optimized context retrieval with multi-level caching
        Target: <200ms response time
        """
        if not self.ready:
            logger.warning("⚠️ Ultra-fast RAG system not ready")
            return ""
        
        try:
            start_time = time.time()
            self.total_queries += 1
            
            # OPTIMIZATION: Create smart cache key
            cache_key = self._create_smart_cache_key(query)
            
            # L1 Cache check (hot cache - ~1ms)
            if cache_key in self.l1_cache:
                self.cache_hits += 1
                result = self.l1_cache[cache_key]
                response_time = (time.time() - start_time) * 1000
                logger.debug(f"⚡ L1 cache hit in {response_time:.1f}ms")
                self._update_query_frequency(cache_key)
                return result
            
            # L2 Cache check (warm cache - ~2ms)
            if cache_key in self.l2_cache:
                self.cache_hits += 1
                result = self.l2_cache[cache_key]
                # Promote to L1 cache
                self._promote_to_l1_cache(cache_key, result)
                response_time = (time.time() - start_time) * 1000
                logger.debug(f"⚡ L2 cache hit in {response_time:.1f}ms")
                return result
            
            self.cache_misses += 1
            
            # OPTIMIZATION: Single optimized retrieval with aggressive timeout
            try:
                nodes = await asyncio.wait_for(
                    self.retriever.aretrieve(query),
                    timeout=3.0  # Very aggressive timeout
                )
                
                if nodes:
                    contexts = []
                    for node in nodes[:max_results]:
                        text = node.text.strip()
                        if text and len(text) > 10:
                            cleaned = self._ultra_fast_clean(text)
                            if cleaned:
                                contexts.append(cleaned)
                    
                    if contexts:
                        # OPTIMIZATION: Fast context combination
                        context = self._fast_combine_contexts(contexts)
                        response_time = (time.time() - start_time) * 1000
                        
                        # Cache the result
                        self._cache_result(cache_key, context)
                        
                        logger.info(f"⚡ Ultra-fast retrieval in {response_time:.1f}ms")
                        return context
                
            except asyncio.TimeoutError:
                logger.warning(f"⏰ Ultra-fast retrieval timeout for: {query}")
                # Return cached fallback if available
                fallback = self._get_fallback_response(query)
                if fallback:
                    return fallback
            
            # No results - return empty
            response_time = (time.time() - start_time) * 1000
            logger.debug(f"⚠️ No results for: {query} (took {response_time:.1f}ms)")
            return ""
                
        except Exception as e:
            logger.error(f"❌ Ultra-fast RAG retrieval error: {e}")
            return ""
    
    def _create_smart_cache_key(self, query: str) -> str:
        """Create smart cache key optimized for voice AI queries"""
        # OPTIMIZATION: Extract key terms for better caching
        query_lower = query.lower().strip()
        
        # Check for common patterns first
        for pattern_key, pattern_query in self.common_patterns.items():
            if any(word in query_lower for word in pattern_query.split()[:3]):
                return pattern_key
        
        # Create hash-based key for other queries
        key_words = []
        important_words = ["towing", "battery", "tire", "lockout", "fuel", "heavy", "light", "cost", "price", "pricing"]
        
        for word in query_lower.split():
            if word in important_words:
                key_words.append(word)
        
        if key_words:
            return "_".join(sorted(key_words))
        else:
            # Fallback to hash for complex queries
            return hashlib.md5(query_lower.encode()).hexdigest()[:12]
    
    def _ultra_fast_clean(self, content: str) -> str:
        """Ultra-fast content cleaning optimized for speed"""
        if not content:
            return ""
        
        # SPEED: Minimal cleaning for ultra-fast processing
        cleaned = content.replace("\n", " ").replace("\t", " ")
        
        # Remove double spaces (single pass)
        while "  " in cleaned:
            cleaned = cleaned.replace("  ", " ")
        
        # Keep shorter for voice (under 150 chars)
        if len(cleaned) > 150:
            # Find first sentence
            first_sentence = cleaned.split('.')[0]
            if len(first_sentence) > 20:
                cleaned = first_sentence + "."
            else:
                cleaned = cleaned[:147] + "..."
        
        return cleaned.strip()
    
    def _fast_combine_contexts(self, contexts: List[str]) -> str:
        """Ultra-fast context combination"""
        if not contexts:
            return ""
        if len(contexts) == 1:
            return contexts[0]
        
        # SPEED: Simple concatenation with separator
        return " | ".join(contexts[:2])  # Max 2 contexts for speed
    
    def _cache_result(self, cache_key: str, result: str):
        """Cache result in appropriate cache level"""
        # Always add to L2 cache
        self.l2_cache[cache_key] = result
        self._update_query_frequency(cache_key)
        
        # Manage L2 cache size
        if len(self.l2_cache) > self.max_l2_cache:
            # Remove least frequent items
            items_by_freq = sorted(
                self.l2_cache.items(),
                key=lambda x: self.query_frequency.get(x[0], 0)
            )
            # Keep most frequent items
            keep_items = items_by_freq[-self.max_l2_cache//2:]
            self.l2_cache = dict(keep_items)
        
        # Promote to L1 if frequently accessed
        if self.query_frequency.get(cache_key, 0) >= 3:
            self._promote_to_l1_cache(cache_key, result)
    
    def _promote_to_l1_cache(self, cache_key: str, result: str):
        """Promote result to L1 hot cache"""
        self.l1_cache[cache_key] = result
        
        # Manage L1 cache size
        if len(self.l1_cache) > self.max_l1_cache:
            # Remove least recently used
            items = list(self.l1_cache.items())
            self.l1_cache = dict(items[-self.max_l1_cache//2:])
    
    def _update_query_frequency(self, cache_key: str):
        """Update query frequency for cache management"""
        self.query_frequency[cache_key] = self.query_frequency.get(cache_key, 0) + 1
    
    def _get_fallback_response(self, query: str) -> str:
        """Get fallback response for timeout scenarios"""
        query_lower = query.lower()
        
        if "towing" in query_lower:
            return "Towing service available. Pricing varies by vehicle type and distance."
        elif "battery" in query_lower:
            return "Battery jumpstart service available. Standard pricing applies."
        elif "tire" in query_lower:
            return "Tire service available. Pricing based on service type."
        elif "lockout" in query_lower:
            return "Lockout service available. Standard rates apply."
        elif "fuel" in query_lower:
            return "Fuel delivery service available. Distance-based pricing."
        else:
            return "Service available. Please contact dispatch for pricing."
    
    async def _prewarm_cache(self):
        """Pre-warm cache with common queries"""
        try:
            logger.info("⚡ Pre-warming cache with common patterns...")
            
            common_queries = [
                "towing cost",
                "battery service price", 
                "tire change cost",
                "lockout service price",
                "fuel delivery cost",
                "heavy duty towing",
                "truck towing price"
            ]
            
            prewarm_count = 0
            for query in common_queries:
                try:
                    result = await asyncio.wait_for(
                        self.retrieve_context(query, max_results=2),
                        timeout=2.0
                    )
                    if result:
                        prewarm_count += 1
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    continue
            
            logger.info(f"⚡ Pre-warmed {prewarm_count}/{len(common_queries)} common queries")
            
        except Exception as e:
            logger.warning(f"⚠️ Cache pre-warming error: {e}")
    
    async def search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """OPTIMIZED: Fast search with caching"""
        try:
            if not self.ready or not self.retriever:
                return []
            
            # Check cache first
            cache_key = self._create_smart_cache_key(query)
            cache_result_key = f"search_{cache_key}"
            
            if cache_result_key in self.l2_cache:
                cached_results = self.l2_cache[cache_result_key]
                self.cache_hits += 1
                return cached_results
            
            # Perform search with timeout
            nodes = await asyncio.wait_for(
                self.retriever.aretrieve(query),
                timeout=2.0
            )
            
            results = []
            for i, node in enumerate(nodes[:limit]):
                score = getattr(node, 'score', 1.0 - (i * 0.1))
                
                result = {
                    "text": node.text,
                    "score": min(score, 1.0),
                    "metadata": getattr(node, 'metadata', {}),
                    "ultra_fast": True
                }
                results.append(result)
            
            # Cache results
            if results:
                self.l2_cache[cache_result_key] = results
                self.cache_misses += 1
            
            return results
            
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Ultra-fast search timeout for: {query}")
            return []
        except Exception as e:
            logger.error(f"❌ Ultra-fast search error: {e}")
            return []
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents with optimized batching"""
        try:
            if not self.index:
                logger.error("❌ Index not initialized")
                return False
            
            logger.info(f"⚡ Adding {len(documents)} documents with ultra-fast indexing...")
            
            # Convert to LlamaIndex Document format
            llama_docs = []
            for doc in documents:
                llama_doc = Document(
                    text=doc["text"],
                    metadata=doc.get("metadata", {}),
                    doc_id=doc.get("id", f"doc_{len(llama_docs)}")
                )
                llama_docs.append(llama_doc)
            
            # Add documents in optimized batches
            batch_size = 5  # Smaller batches for speed
            total_added = 0
            
            for i in range(0, len(llama_docs), batch_size):
                batch = llama_docs[i:i + batch_size]
                
                try:
                    for doc in batch:
                        self.index.insert(doc)
                    
                    total_added += len(batch)
                    await asyncio.sleep(0.01)  # Minimal pause
                    
                except Exception as e:
                    logger.error(f"❌ Error in ultra-fast batch: {e}")
                    continue
            
            # Refresh components
            if total_added > 0:
                self.query_engine = self.index.as_query_engine(
                    similarity_top_k=3,
                    response_mode="compact",
                    streaming=False,
                    verbose=False
                )
                
                self.retriever = self.index.as_retriever(
                    similarity_top_k=3,
                    verbose=False
                )
                
                # Clear caches after adding documents
                self.l1_cache.clear()
                self.l2_cache.clear()
            
            logger.info(f"⚡ Ultra-fast indexing complete: {total_added}/{len(documents)} documents")
            return total_added > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to add documents with ultra-fast indexing: {e}")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get ultra-fast system status with cache statistics"""
        if not self.ready:
            return {"status": "not_ready"}
        
        try:
            points_count = 0
            if self.sync_client:
                try:
                    collection_info = self.sync_client.get_collection(config.qdrant_collection_name)
                    points_count = collection_info.points_count
                except:
                    points_count = 0
            
            cache_hit_rate = (self.cache_hits / self.total_queries * 100) if self.total_queries > 0 else 0
            
            return {
                "status": "ultra_fast_ready",
                "points_count": points_count,
                "l1_cache_size": len(self.l1_cache),
                "l2_cache_size": len(self.l2_cache),
                "cache_hit_rate": round(cache_hit_rate, 2),
                "total_queries": self.total_queries,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "optimizations_enabled": [
                    "multi_level_caching",
                    "smart_cache_keys",
                    "aggressive_timeouts",
                    "single_query_optimization",
                    "pre_warmed_cache",
                    "ultra_fast_cleaning"
                ],
                "target_response_time": "< 200ms",
                "dimensions": 512,
                "collection_name": config.qdrant_collection_name
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def cleanup(self):
        """Cleanup ultra-fast system resources"""
        try:
            if self.async_client:
                await self.async_client.close()
            if self.sync_client:
                self.sync_client.close()
            
            # Clear all caches
            self.l1_cache.clear()
            self.l2_cache.clear()
            self.query_frequency.clear()
            
            logger.info("⚡ Ultra-fast RAG system cleaned up")
        except Exception as e:
            logger.warning(f"⚠️ Ultra-fast cleanup warning: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        cache_hit_rate = (self.cache_hits / self.total_queries * 100) if self.total_queries > 0 else 0
        
        return {
            "cache_performance": {
                "hit_rate_percent": round(cache_hit_rate, 2),
                "total_hits": self.cache_hits,
                "total_misses": self.cache_misses,
                "total_queries": self.total_queries
            },
            "cache_sizes": {
                "l1_hot_cache": len(self.l1_cache),
                "l2_warm_cache": len(self.l2_cache),
                "query_frequency_tracker": len(self.query_frequency)
            },
            "optimization_status": {
                "multi_level_caching": True,
                "aggressive_timeouts": True,
                "smart_cache_keys": True,
                "ultra_fast_cleaning": True,
                "pre_warmed_patterns": len(self.common_patterns)
            }
        }

# Global ultra-fast instance
simplified_rag = UltraFastRAGSystem()