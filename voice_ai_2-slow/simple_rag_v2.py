# simple_rag_v2.py - SIMPLIFIED FOR ALL SERVICES
"""
SIMPLIFIED: RAG system that works efficiently for ALL services
Based on LiveKit example patterns - no over-engineering
"""
import asyncio
import logging
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

# Standard LlamaIndex imports
try:
    from llama_index.core import (
        VectorStoreIndex,
        StorageContext,
        Settings,
        Document
    )
    from llama_index.vector_stores.qdrant import QdrantVectorStore
    from llama_index.embeddings.openai import OpenAIEmbedding
    from llama_index.llms.openai import OpenAI
    LLAMA_INDEX_AVAILABLE = True
except ImportError as e:
    logging.error(f"LlamaIndex import error: {e}")
    LLAMA_INDEX_AVAILABLE = False

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import VectorParams, Distance
    from qdrant_client.http.exceptions import UnexpectedResponse
    QDRANT_AVAILABLE = True
except ImportError as e:
    logging.error(f"Qdrant import error: {e}")
    QDRANT_AVAILABLE = False

from config import config

logger = logging.getLogger(__name__)

class SimplifiedRAGSystem:
    """Simplified RAG system for all roadside services"""
    
    def __init__(self):
        self.index = None
        self.query_engine = None
        self.ready = False
        self.sync_client = None
        
        # Simple single-level cache
        self.cache = {}
        self.max_cache_size = 50
        
        # Basic metrics
        self.total_queries = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    async def initialize(self) -> bool:
        """Simple initialization without over-engineering"""
        try:
            if not LLAMA_INDEX_AVAILABLE or not QDRANT_AVAILABLE:
                logger.error("❌ Required libraries not available")
                return False
            
            logger.info("🚀 Initializing simplified RAG system...")
            start_time = time.time()
            
            # Configure LlamaIndex with simple settings
            Settings.embed_model = OpenAIEmbedding(
                model="text-embedding-3-small",
                api_key=config.openai_api_key,
                dimensions=512
            )
            
            Settings.llm = OpenAI(
                model="gpt-4o-mini",
                api_key=config.openai_api_key,
                temperature=0.0,
                max_tokens=150
            )
            
            # Simple Qdrant connection
            self.sync_client = QdrantClient(url=config.qdrant_url, timeout=10)
            
            # Test connection
            collections = self.sync_client.get_collections()
            logger.info(f"✅ Qdrant connected: {len(collections.collections)} collections")
            
            # Ensure collection exists
            await self._ensure_collection_exists()
            
            # Create vector store
            vector_store = QdrantVectorStore(
                client=self.sync_client,
                collection_name=config.qdrant_collection_name
            )
            
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            # Load or create index
            try:
                collection_info = self.sync_client.get_collection(config.qdrant_collection_name)
                points_count = collection_info.points_count
                
                if points_count > 0:
                    self.index = VectorStoreIndex.from_vector_store(
                        vector_store=vector_store,
                        storage_context=storage_context
                    )
                    logger.info(f"✅ Loaded index with {points_count} documents")
                else:
                    self.index = VectorStoreIndex([], storage_context=storage_context)
                    logger.info("📊 Created empty index")
                    
            except Exception as e:
                logger.warning(f"⚠️ Index loading issue: {e}")
                self.index = VectorStoreIndex([], storage_context=storage_context)
            
            # Create simple query engine
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=3,
                response_mode="compact",
                streaming=False
            )
            
            elapsed = (time.time() - start_time) * 1000
            self.ready = True
            
            logger.info(f"✅ Simplified RAG system ready in {elapsed:.1f}ms")
            return True
            
        except Exception as e:
            logger.error(f"❌ RAG initialization failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    async def _ensure_collection_exists(self) -> bool:
        """Ensure Qdrant collection exists"""
        try:
            try:
                collection_info = self.sync_client.get_collection(config.qdrant_collection_name)
                return True
            except UnexpectedResponse:
                # Create collection
                self.sync_client.create_collection(
                    collection_name=config.qdrant_collection_name,
                    vectors_config=VectorParams(
                        size=512,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ Created collection '{config.qdrant_collection_name}'")
                return True
                
        except Exception as e:
            logger.error(f"❌ Collection creation error: {e}")
            return False
    
    async def retrieve_context(self, query: str, max_results: int = 3) -> str:
        """Simple context retrieval - let LlamaIndex do the work"""
        if not self.ready:
            logger.warning("⚠️ RAG system not ready")
            return ""
        
        try:
            start_time = time.time()
            self.total_queries += 1
            
            # Simple cache check
            cache_key = query.lower().strip()
            if cache_key in self.cache:
                self.cache_hits += 1
                result = self.cache[cache_key]
                response_time = (time.time() - start_time) * 1000
                logger.debug(f"⚡ Cache hit in {response_time:.1f}ms")
                return result
            
            self.cache_misses += 1
            
            # Let LlamaIndex handle the query - don't over-engineer
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                self._execute_query, 
                query
            )
            
            # Clean and format response
            result = str(response).strip()
            
            # Simple response cleaning
            if result:
                # Remove common artifacts
                result = result.replace("According to the context,", "")
                result = result.replace("Based on the information provided,", "")
                result = result.strip()
                
                # Keep reasonable length for voice
                if len(result) > 200:
                    sentences = result.split('.')
                    if len(sentences) > 1:
                        result = sentences[0] + '.'
                    else:
                        result = result[:197] + "..."
            
            response_time = (time.time() - start_time) * 1000
            
            # Simple cache management
            if len(self.cache) >= self.max_cache_size:
                # Remove oldest entry
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            
            self.cache[cache_key] = result
            
            if result:
                logger.info(f"✅ Retrieved in {response_time:.1f}ms: {result[:60]}...")
                return result
            else:
                logger.debug(f"⚠️ No results for: {query}")
                return ""
                
        except Exception as e:
            logger.error(f"❌ Retrieval error: {e}")
            return ""
    
    def _execute_query(self, query: str):
        """Execute query synchronously"""
        return self.query_engine.query(query)
    
    async def search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Simple search interface"""
        try:
            if not self.ready:
                return []
            
            # Use the retriever directly for search
            retriever = self.index.as_retriever(similarity_top_k=limit)
            nodes = retriever.retrieve(query)
            
            results = []
            for i, node in enumerate(nodes):
                score = getattr(node, 'score', 1.0 - (i * 0.1))
                
                result = {
                    "text": node.text,
                    "score": min(score, 1.0),
                    "metadata": getattr(node, 'metadata', {}),
                    "simplified_version": True
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return []
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Simple document addition - no over-engineering"""
        try:
            if not self.index:
                logger.error("❌ Index not initialized")
                return False
            
            logger.info(f"📝 Adding {len(documents)} documents...")
            
            # Convert to LlamaIndex Documents with simple enhancement
            llama_docs = []
            for doc in documents:
                # Simple text enhancement for better retrieval
                enhanced_text = self._enhance_text_for_retrieval(doc["text"], doc.get("metadata", {}))
                
                llama_doc = Document(
                    text=enhanced_text,
                    metadata=doc.get("metadata", {}),
                    doc_id=doc.get("id", f"doc_{len(llama_docs)}")
                )
                llama_docs.append(llama_doc)
            
            # Add documents - let LlamaIndex handle batching
            for doc in llama_docs:
                self.index.insert(doc)
            
            # Recreate query engine after adding documents
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=3,
                response_mode="compact",
                streaming=False
            )
            
            # Clear cache after changes
            self.cache.clear()
            
            logger.info(f"✅ Added {len(documents)} documents successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add documents: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _enhance_text_for_retrieval(self, text: str, metadata: Dict[str, Any]) -> str:
        """Simple text enhancement for better retrieval of ALL services"""
        
        enhanced_parts = []
        
        # Add service context from metadata
        service_name = metadata.get("service_name", "")
        category = metadata.get("category", "")
        base_price = metadata.get("base_price", "")
        
        # Add service identification
        if service_name:
            enhanced_parts.append(f"Service: {service_name}")
        
        if category:
            enhanced_parts.append(f"Category: {category}")
        
        # Add pricing context if available
        if base_price:
            if base_price.isdigit():
                enhanced_parts.append(f"Price: ${base_price}")
                enhanced_parts.append(f"Cost: ${base_price}")
            else:
                enhanced_parts.append(f"Pricing: {base_price}")
        
        # Add original text
        enhanced_parts.append(text)
        
        # Add common search terms for each service category
        search_terms = self._get_search_terms_for_category(category, service_name)
        if search_terms:
            enhanced_parts.append(f"Keywords: {search_terms}")
        
        return ". ".join(enhanced_parts)
    
    def _get_search_terms_for_category(self, category: str, service_name: str) -> str:
        """Get search terms for each service category"""
        
        category_lower = category.lower() if category else ""
        service_lower = service_name.lower() if service_name else ""
        
        search_terms = []
        
        # Towing services
        if "towing" in category_lower or "towing" in service_lower:
            search_terms.extend(["vehicle transport", "car towing", "truck towing", "roadside towing", "flatbed", "wrecker"])
        
        # Battery services
        elif "battery" in category_lower or "jump" in service_lower or "battery" in service_lower:
            search_terms.extend(["dead battery", "car won't start", "jumpstart", "battery boost", "jump start"])
        
        # Tire services
        elif "tire" in category_lower or "tire" in service_lower:
            search_terms.extend(["flat tire", "tire puncture", "spare tire", "tire replacement", "tire change"])
        
        # Lockout services
        elif "lockout" in category_lower or "lockout" in service_lower:
            search_terms.extend(["locked out", "keys inside", "car locksmith", "vehicle entry", "unlock car"])
        
        # Fuel services
        elif "fuel" in category_lower or "fuel" in service_lower:
            search_terms.extend(["out of gas", "fuel delivery", "gasoline delivery", "diesel delivery", "emergency fuel"])
        
        # Winch/Recovery services
        elif "recovery" in category_lower or "winch" in service_lower:
            search_terms.extend(["stuck vehicle", "vehicle recovery", "winch out", "off road recovery"])
        
        # Mechanic services
        elif "mechanic" in category_lower or "diagnostic" in service_lower:
            search_terms.extend(["mobile mechanic", "car repair", "diagnostic", "vehicle inspection"])
        
        return ", ".join(search_terms)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get system status"""
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
                "status": "ready",
                "points_count": points_count,
                "cache_size": len(self.cache),
                "cache_hit_rate": round(cache_hit_rate, 2),
                "total_queries": self.total_queries,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "collection_name": config.qdrant_collection_name,
                "version": "simplified_all_services"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def cleanup(self):
        """Simple cleanup"""
        try:
            if self.sync_client:
                self.sync_client.close()
            
            self.cache.clear()
            
            logger.info("✅ RAG system cleaned up")
        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning: {e}")

# Global instance
simplified_rag = SimplifiedRAGSystem()