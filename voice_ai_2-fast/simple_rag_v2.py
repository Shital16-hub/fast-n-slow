# simple_rag_v2.py - ENHANCED FOR INTELLIGENT PRICING
"""
ENHANCED RAG System for Intelligent Voice AI Agent
Optimized for LLM brain with intelligent pricing queries
"""
import asyncio
import logging
import time
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

class IntelligentRAGSystem:
    """
    ENHANCED RAG system optimized for intelligent pricing and service queries
    Works with LLM brain to provide comprehensive service information
    """
    
    def __init__(self):
        self.index: Optional[VectorStoreIndex] = None
        self.query_engine = None
        self.retriever = None
        self.ready = False
        
        # Enhanced cache for intelligent queries
        self.pricing_cache = {}
        self.service_cache = {}
        self.max_cache_size = 150
        
        # Clients
        self.sync_client = None
        self.async_client = None
        
        # Intelligent query patterns
        self.pricing_keywords = [
            "cost", "price", "pricing", "rate", "fee", "charge", 
            "night", "weekend", "surcharge", "base", "$", "dollar"
        ]
        
        self.service_keywords = [
            "towing", "battery", "tire", "lockout", "fuel", "jumpstart",
            "heavy duty", "light duty", "emergency", "roadside"
        ]
        
    async def initialize(self) -> bool:
        """Initialize with enhanced intelligent features"""
        try:
            start_time = time.time()
            logger.info("🧠 Initializing INTELLIGENT RAG system...")
            
            # Enhanced embeddings for better service matching
            Settings.embed_model = OpenAIEmbedding(
                model="text-embedding-3-small",
                api_key=config.openai_api_key,
                dimensions=512
            )
            
            # Optimized LLM for intelligent processing
            Settings.llm = OpenAI(
                model="gpt-4o-mini",
                api_key=config.openai_api_key,
                temperature=0.1,
                request_timeout=8.0,
                max_tokens=512
            )
            
            # Initialize clients
            try:
                self.sync_client = QdrantClient(
                    url=config.qdrant_url,
                    timeout=20
                )
                
                self.async_client = AsyncQdrantClient(
                    url=config.qdrant_url,
                    timeout=20
                )
                
                collections = self.sync_client.get_collections()
                logger.info(f"✅ Qdrant connected: {len(collections.collections)} collections")
                
            except Exception as e:
                logger.error(f"❌ Qdrant connection failed: {e}")
                return False
            
            # Create enhanced vector store
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
                logger.info(f"📊 Found existing collection with {points_count} service documents")
            except Exception:
                logger.info("📊 Collection doesn't exist, will create empty index")
            
            # Load or create index
            if collection_exists and points_count > 0:
                logger.info(f"🧠 Loading intelligent index with {points_count} documents")
                try:
                    self.index = VectorStoreIndex.from_vector_store(
                        vector_store=vector_store,
                        storage_context=storage_context
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Failed to load existing index, creating new: {e}")
                    self.index = VectorStoreIndex([], storage_context=storage_context)
            else:
                logger.info("📊 Creating new intelligent index")
                self.index = VectorStoreIndex([], storage_context=storage_context)
            
            # Create enhanced query components
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=5,  # Increased for better coverage
                response_mode="compact",
                streaming=False,
                verbose=False
            )
            
            self.retriever = self.index.as_retriever(
                similarity_top_k=5,  # Increased for intelligent processing
                verbose=False
            )
            
            elapsed = (time.time() - start_time) * 1000
            self.ready = True
            
            logger.info(f"✅ INTELLIGENT RAG system ready in {elapsed:.1f}ms")
            logger.info(f"🧠 Enhanced for LLM brain processing")
            logger.info(f"💰 Optimized for intelligent pricing")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Intelligent RAG initialization failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    async def retrieve_context(self, query: str, max_results: int = 5) -> str:
        """
        INTELLIGENT: Enhanced context retrieval for LLM brain processing
        """
        if not self.ready:
            logger.warning("⚠️ Intelligent RAG system not ready")
            return ""
        
        try:
            # Intelligent cache key
            cache_key = self._create_intelligent_cache_key(query)
            
            # Check pricing cache first
            if self._is_pricing_query(query) and cache_key in self.pricing_cache:
                logger.debug("💰 Pricing cache hit")
                return self.pricing_cache[cache_key]
            
            # Check service cache
            if self._is_service_query(query) and cache_key in self.service_cache:
                logger.debug("🔧 Service cache hit")
                return self.service_cache[cache_key]
            
            start_time = time.time()
            
            # INTELLIGENT: Try retriever first for comprehensive results
            try:
                nodes = await asyncio.wait_for(
                    self.retriever.aretrieve(query),
                    timeout=5.0
                )
                
                if nodes:
                    contexts = []
                    for node in nodes[:max_results]:
                        text = node.text.strip()
                        if text and len(text) > 15:
                            cleaned = self._clean_for_intelligent_processing(text)
                            if cleaned:
                                contexts.append(cleaned)
                    
                    if contexts:
                        context = self._combine_contexts_intelligently(contexts, query)
                        search_time = (time.time() - start_time) * 1000
                        
                        # Intelligent caching
                        self._cache_result_intelligently(cache_key, context, query)
                        
                        logger.info(f"🧠 Intelligent context retrieved in {search_time:.1f}ms")
                        return context
                
            except asyncio.TimeoutError:
                logger.warning("⏰ Intelligent retriever timeout, trying query engine...")
            except Exception as e:
                logger.warning(f"⚠️ Intelligent retriever error: {e}")
            
            # Fallback to query engine with intelligent processing
            try:
                response = await asyncio.wait_for(
                    self.query_engine.aquery(query),
                    timeout=8.0
                )
                
                search_time = (time.time() - start_time) * 1000
                
                if response and hasattr(response, 'response') and response.response:
                    context = self._clean_for_intelligent_processing(str(response.response))
                    
                    if context and len(context.strip()) > 15:
                        # Intelligent caching
                        self._cache_result_intelligently(cache_key, context, query)
                        
                        logger.info(f"🧠 Intelligent query engine result in {search_time:.1f}ms")
                        return context
                        
            except asyncio.TimeoutError:
                logger.warning(f"⏰ Intelligent query engine timeout for: {query}")
                return ""
            except Exception as e:
                logger.warning(f"⚠️ Intelligent query engine error: {e}")
                return ""
            
            # No results found
            search_time = (time.time() - start_time) * 1000
            logger.debug(f"⚠️ No intelligent results for: {query} (took {search_time:.1f}ms)")
            return ""
                
        except Exception as e:
            logger.error(f"❌ Intelligent RAG retrieval error: {e}")
            return ""
    
    def _create_intelligent_cache_key(self, query: str) -> str:
        """Create intelligent cache key based on query type"""
        normalized = query.lower().strip()
        
        # Extract key terms for caching
        key_terms = []
        for word in normalized.split():
            if word in self.pricing_keywords or word in self.service_keywords:
                key_terms.append(word)
        
        if key_terms:
            return "_".join(sorted(key_terms))
        else:
            return normalized[:30]
    
    def _is_pricing_query(self, query: str) -> bool:
        """Check if query is pricing-related"""
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in self.pricing_keywords)
    
    def _is_service_query(self, query: str) -> bool:
        """Check if query is service-related"""
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in self.service_keywords)
    
    def _clean_for_intelligent_processing(self, content: str) -> str:
        """Clean content for intelligent LLM processing"""
        if not content:
            return ""
        
        # Remove RAG artifacts but preserve structure for LLM
        content = content.replace("Based on the provided context", "")
        content = content.replace("According to the information", "")
        content = content.replace("The document states", "")
        
        # Clean formatting but preserve pricing structure
        content = content.replace("\n", " ").replace("\t", " ")
        
        # Remove multiple spaces
        while "  " in content:
            content = content.replace("  ", " ")
        
        # Keep longer content for LLM brain processing (up to 300 chars)
        if len(content) > 300:
            sentences = content.split('.')
            if len(sentences) > 1:
                # Take first two complete sentences for pricing info
                content = '. '.join(sentences[:2]).strip() + "."
            else:
                content = content[:297] + "..."
        
        return content.strip()
    
    def _combine_contexts_intelligently(self, contexts: List[str], query: str) -> str:
        """Intelligently combine multiple contexts for LLM processing"""
        if not contexts:
            return ""
        
        if len(contexts) == 1:
            return contexts[0]
        
        # For pricing queries, prioritize contexts with pricing information
        if self._is_pricing_query(query):
            pricing_contexts = []
            other_contexts = []
            
            for context in contexts:
                if any(keyword in context.lower() for keyword in ["$", "cost", "price", "rate"]):
                    pricing_contexts.append(context)
                else:
                    other_contexts.append(context)
            
            # Combine pricing first, then other relevant info
            combined = pricing_contexts + other_contexts[:2]  # Max 3 total contexts
            return " | ".join(combined)
        
        # For service queries, combine up to 3 most relevant contexts
        return " | ".join(contexts[:3])
    
    def _cache_result_intelligently(self, cache_key: str, context: str, query: str):
        """Cache results intelligently based on query type"""
        if self._is_pricing_query(query):
            self.pricing_cache[cache_key] = context
            if len(self.pricing_cache) > self.max_cache_size:
                # Remove oldest pricing cache entry
                oldest_key = next(iter(self.pricing_cache))
                del self.pricing_cache[oldest_key]
        
        elif self._is_service_query(query):
            self.service_cache[cache_key] = context
            if len(self.service_cache) > self.max_cache_size:
                # Remove oldest service cache entry
                oldest_key = next(iter(self.service_cache))
                del self.service_cache[oldest_key]
    
    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Enhanced search for intelligent processing"""
        try:
            if not self.ready or not self.retriever:
                return []
            
            # Enhanced search with longer timeout
            nodes = await asyncio.wait_for(
                self.retriever.aretrieve(query),
                timeout=5.0
            )
            
            results = []
            for i, node in enumerate(nodes[:limit]):
                # Enhanced result with intelligent scoring
                score = getattr(node, 'score', 1.0 - (i * 0.1))
                
                # Boost score for pricing information
                text = node.text
                if self._is_pricing_query(query) and any(keyword in text.lower() for keyword in ["$", "cost", "price"]):
                    score += 0.2
                
                result = {
                    "text": text,
                    "score": min(score, 1.0),  # Cap at 1.0
                    "metadata": getattr(node, 'metadata', {}),
                    "intelligent_boost": score > getattr(node, 'score', 1.0 - (i * 0.1))
                }
                results.append(result)
            
            return results
            
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Intelligent search timeout for: {query}")
            return []
        except Exception as e:
            logger.error(f"❌ Intelligent search error: {e}")
            return []
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Enhanced document addition with intelligent indexing"""
        try:
            if not self.index:
                logger.error("❌ Index not initialized")
                return False
            
            logger.info(f"🧠 Adding {len(documents)} documents with intelligent indexing...")
            
            # Convert to LlamaIndex Document format with enhanced metadata
            llama_docs = []
            for doc in documents:
                # Enhance metadata for intelligent retrieval
                enhanced_metadata = doc.get("metadata", {})
                
                # Add intelligent tags based on content
                content_lower = doc["text"].lower()
                if any(keyword in content_lower for keyword in self.pricing_keywords):
                    enhanced_metadata["contains_pricing"] = True
                if any(keyword in content_lower for keyword in self.service_keywords):
                    enhanced_metadata["contains_service"] = True
                
                llama_doc = Document(
                    text=doc["text"],
                    metadata=enhanced_metadata,
                    doc_id=doc.get("id", f"doc_{len(llama_docs)}")
                )
                llama_docs.append(llama_doc)
            
            # Add documents in optimized batches
            batch_size = 8
            total_added = 0
            
            for i in range(0, len(llama_docs), batch_size):
                batch = llama_docs[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(llama_docs) - 1) // batch_size + 1
                
                logger.info(f"🧠 Processing intelligent batch {batch_num}/{total_batches}")
                
                try:
                    for doc in batch:
                        self.index.insert(doc)
                    
                    total_added += len(batch)
                    await asyncio.sleep(0.05)  # Brief pause
                    
                except Exception as e:
                    logger.error(f"❌ Error in intelligent batch {batch_num}: {e}")
                    continue
            
            # Refresh components
            if total_added > 0:
                logger.info("🧠 Refreshing intelligent query components...")
                self.query_engine = self.index.as_query_engine(
                    similarity_top_k=5,
                    response_mode="compact",
                    streaming=False,
                    verbose=False
                )
                
                self.retriever = self.index.as_retriever(
                    similarity_top_k=5,
                    verbose=False
                )
            
            logger.info(f"✅ Intelligently added {total_added}/{len(documents)} documents")
            return total_added > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to add documents intelligently: {e}")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get intelligent system status"""
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
            
            return {
                "status": "intelligent_ready",
                "points_count": points_count,
                "pricing_cache_size": len(self.pricing_cache),
                "service_cache_size": len(self.service_cache),
                "total_cache_size": len(self.pricing_cache) + len(self.service_cache),
                "index_ready": self.index is not None,
                "query_engine_ready": self.query_engine is not None,
                "retriever_ready": self.retriever is not None,
                "intelligent_features": {
                    "enhanced_caching": True,
                    "pricing_optimization": True,
                    "service_categorization": True,
                    "llm_brain_support": True
                },
                "dimensions": 512,
                "collection_name": config.qdrant_collection_name
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def cleanup(self):
        """Cleanup intelligent system resources"""
        try:
            if self.async_client:
                await self.async_client.close()
            if self.sync_client:
                self.sync_client.close()
            
            # Clear intelligent caches
            self.pricing_cache.clear()
            self.service_cache.clear()
            
            logger.info("✅ Intelligent RAG system cleaned up")
        except Exception as e:
            logger.warning(f"⚠️ Intelligent cleanup warning: {e}")

# Global intelligent instance
simplified_rag = IntelligentRAGSystem()