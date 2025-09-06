# transcript_indexer.py - FIXED VERSION
"""
FIXED: Batch processor to send completed call transcripts to LogicalCRM API
Runs independently from voice AI system for zero latency impact
"""
import asyncio
import logging
import time
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import httpx
from pymongo import AsyncMongoClient

from config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranscriptIndexer:
    """FIXED: Batch processor for sending call transcripts to external API"""
    
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        
        # External API configuration
        self.api_config = {
            "url": "https://api.logicalcrm.com/api/open/ai_call_center_webhook",
            "bearer_token": "4a9f82d9b22d4e7bb1f2c18f0cf4377fbe1a1a73e9c847f65d85c1c317dcb5e0",
            "merchant_id": "6686c196d763eb864652d89e",
            "timeout": 30.0
        }
        
        # Processing statistics
        self.stats = {
            "processed_calls": 0,
            "successful_sends": 0,
            "failed_sends": 0,
            "start_time": time.time()
        }
    
    async def initialize(self):
        """Initialize MongoDB connection"""
        try:
            self.mongo_client = AsyncMongoClient(config.get_optimized_mongodb_url())
            self.mongo_db = self.mongo_client[config.mongodb_database]
            
            # Test connection
            await self.mongo_client.admin.command('ping')
            logger.info("✅ Transcript indexer initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Indexer initialization failed: {e}")
            return False
    
    async def get_unprocessed_calls(self, limit: int = 50) -> List[Dict[str, Any]]:
        """FIXED: Get completed calls that haven't been sent to external API"""
        try:
            # Query for completed calls without external_api_sent flag
            query = {
                "status": "completed",
                "end_time": {"$exists": True},
                "$or": [
                    {"external_api_sent": {"$exists": False}},
                    {"external_api_sent": False}
                ]
            }
            
            calls = []
            # FIXED: Use find() instead of aggregate() and properly await the cursor
            cursor = self.mongo_db.call_sessions.find(query).sort("end_time", 1).limit(limit)
            
            async for call in cursor:
                calls.append(call)
            
            logger.info(f"📋 Found {len(calls)} unprocessed calls")
            return calls
            
        except Exception as e:
            logger.error(f"❌ Error getting unprocessed calls: {e}")
            return []
    
    async def get_call_transcript(self, session_id: str) -> Dict[str, Any]:
        """FIXED: Get complete transcript for a call session"""
        try:
            # Get conversation items
            conversation_items = []
            cursor1 = self.mongo_db.conversation_items.find(
                {"session_id": session_id}
            ).sort("timestamp", 1)
            
            async for item in cursor1:
                conversation_items.append(item)
            
            # Get transcription segments
            transcription_segments = []
            cursor2 = self.mongo_db.transcription_segments.find(
                {"session_id": session_id}
            ).sort("timestamp", 1)
            
            async for segment in cursor2:
                transcription_segments.append(segment)
            
            return {
                "conversation_items": conversation_items,
                "transcription_segments": transcription_segments
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting transcript for {session_id}: {e}")
            return {"conversation_items": [], "transcription_segments": []}
    
    def extract_caller_info(self, call_session: Dict[str, Any], transcript_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract caller information from call data"""
        
        # Start with phone number from session
        phone = call_session.get("phone_number", "")
        if phone == "unknown" or not phone:
            phone = ""
        
        # Extract name from conversation
        first_name = ""
        last_name = ""
        
        # Look through conversation items for name information
        for item in transcript_data.get("conversation_items", []):
            if item.get("role") == "user":
                content = item.get("content", "").lower()
                
                # Try to extract name patterns
                name_patterns = [
                    r"my name is ([a-zA-Z\s]{2,30})",
                    r"i'm ([a-zA-Z\s]{2,30})",
                    r"this is ([a-zA-Z\s]{2,30})",
                    r"call me ([a-zA-Z\s]{2,30})"
                ]
                
                for pattern in name_patterns:
                    match = re.search(pattern, content)
                    if match:
                        full_name = match.group(1).strip().title()
                        name_parts = full_name.split()
                        if len(name_parts) >= 1:
                            first_name = name_parts[0]
                        if len(name_parts) >= 2:
                            last_name = " ".join(name_parts[1:])
                        break
                
                if first_name:  # Stop at first found name
                    break
        
        # Fallback if no name found
        if not first_name:
            first_name = "Unknown"
            last_name = "Caller"
        
        return {
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "email": ""  # Not available in voice calls
        }
    
    def build_custom_fields(self, call_session: Dict[str, Any], transcript_data: Dict[str, Any]) -> str:
        """Build custom fields data from call transcript"""
        
        custom_data = {
            "call_duration": call_session.get("duration_seconds", 0),
            "service_type": "Roadside Assistance",
            "call_start_time": call_session.get("start_time"),
            "call_end_time": call_session.get("end_time"),
            "session_id": call_session.get("session_id"),
            "total_turns": len(transcript_data.get("conversation_items", [])),
            "transcript_summary": self._create_transcript_summary(transcript_data)
        }
        
        return json.dumps(custom_data)
    
    def _create_transcript_summary(self, transcript_data: Dict[str, Any]) -> str:
        """Create a summary of the call transcript"""
        
        conversation_items = transcript_data.get("conversation_items", [])
        
        # Extract key information
        services_mentioned = []
        vehicle_info = ""
        location_info = ""
        
        for item in conversation_items:
            content = item.get("content", "").lower()
            
            # Look for services
            if any(word in content for word in ["towing", "tow"]):
                services_mentioned.append("towing")
            if any(word in content for word in ["battery", "jumpstart", "jump"]):
                services_mentioned.append("battery")
            if any(word in content for word in ["tire", "flat"]):
                services_mentioned.append("tire")
            if any(word in content for word in ["lockout", "locked"]):
                services_mentioned.append("lockout")
            if any(word in content for word in ["fuel", "gas"]):
                services_mentioned.append("fuel")
            
            # Look for vehicle info
            if not vehicle_info:
                vehicle_brands = ["honda", "toyota", "ford", "chevy", "bmw", "audi", "tata"]
                for brand in vehicle_brands:
                    if brand in content:
                        vehicle_info = f"Vehicle: {brand.title()}"
                        break
        
        # Build summary
        summary_parts = []
        if services_mentioned:
            summary_parts.append(f"Services: {', '.join(set(services_mentioned))}")
        if vehicle_info:
            summary_parts.append(vehicle_info)
        
        summary = " | ".join(summary_parts) if summary_parts else "General roadside assistance inquiry"
        return summary
    
    async def send_to_external_api(self, call_data: Dict[str, Any]) -> bool:
        """Send call data to external API"""
        try:
            async with httpx.AsyncClient(timeout=self.api_config["timeout"]) as client:
                headers = {
                    'authorization': f'Bearer {self.api_config["bearer_token"]}',
                    'Content-Type': 'application/json'
                }
                
                response = await client.post(
                    self.api_config["url"],
                    headers=headers,
                    json=call_data
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Successfully sent call data for {call_data.get('phone')}")
                    return True
                else:
                    logger.error(f"❌ API error {response.status_code}: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to send to API: {e}")
            return False
    
    async def mark_as_processed(self, session_id: str, success: bool):
        """Mark call as processed in MongoDB"""
        try:
            update_data = {
                "external_api_sent": success,
                "external_api_sent_at": datetime.utcnow(),
                "external_api_attempts": 1
            }
            
            if not success:
                update_data["external_api_last_error"] = datetime.utcnow()
            
            await self.mongo_db.call_sessions.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
            
        except Exception as e:
            logger.error(f"❌ Error marking {session_id} as processed: {e}")
    
    async def process_call(self, call_session: Dict[str, Any]) -> bool:
        """Process a single call and send to external API"""
        try:
            session_id = call_session.get("session_id")
            logger.info(f"🔄 Processing call: {session_id}")
            
            # Get transcript data
            transcript_data = await self.get_call_transcript(session_id)
            
            # Extract caller information
            caller_info = self.extract_caller_info(call_session, transcript_data)
            
            # Build API payload
            api_payload = {
                "merchant_id": self.api_config["merchant_id"],
                "first_name": caller_info["first_name"],
                "last_name": caller_info["last_name"],
                "email": caller_info["email"],
                "phone": caller_info["phone"],
                "tags": [
                    "Voice-AI-Agent",
                    "Roadside-Assistance",
                    "Auto-Generated"
                ],
                "custom_fields": self.build_custom_fields(call_session, transcript_data)
            }
            
            # Send to external API
            success = await self.send_to_external_api(api_payload)
            
            # Mark as processed
            await self.mark_as_processed(session_id, success)
            
            # Update statistics
            self.stats["processed_calls"] += 1
            if success:
                self.stats["successful_sends"] += 1
            else:
                self.stats["failed_sends"] += 1
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error processing call {call_session.get('session_id')}: {e}")
            await self.mark_as_processed(call_session.get("session_id"), False)
            self.stats["processed_calls"] += 1
            self.stats["failed_sends"] += 1
            return False
    
    async def run_batch_processing(self):
        """Run one batch of processing"""
        try:
            logger.info("🚀 Starting batch processing...")
            
            # Get unprocessed calls
            unprocessed_calls = await self.get_unprocessed_calls(limit=20)
            
            if not unprocessed_calls:
                logger.info("✅ No unprocessed calls found")
                return
            
            # Process each call
            for call_session in unprocessed_calls:
                await self.process_call(call_session)
                await asyncio.sleep(0.5)  # Small delay between API calls
            
            # Print statistics
            elapsed = time.time() - self.stats["start_time"]
            logger.info(f"📊 Batch complete: {self.stats['successful_sends']}/{self.stats['processed_calls']} successful in {elapsed:.1f}s")
            
        except Exception as e:
            logger.error(f"❌ Batch processing error: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.mongo_client:
            self.mongo_client.close()

async def main():
    """Main batch processing function"""
    indexer = TranscriptIndexer()
    
    try:
        # Initialize
        if not await indexer.initialize():
            logger.error("❌ Failed to initialize indexer")
            return
        
        # Run processing
        await indexer.run_batch_processing()
        
    except Exception as e:
        logger.error(f"❌ Main processing error: {e}")
    finally:
        await indexer.cleanup()

if __name__ == "__main__":
    asyncio.run(main())