# transcription/handler.py - COMPLETE FIXED VERSION
"""
COMPLETE: Transcription handler for intelligent LLM-based system
All methods included and working
"""
import asyncio
import logging
import time
from typing import List, Dict, Any

from logging_config import create_call_logger
from models.call_data import CallData
from call_transcription_storage import get_call_storage

transcript_logger = create_call_logger("transcript")

class CompleteTranscriptionHandler:
    """COMPLETE: Transcription handler for intelligent conversation flow"""
    
    def __init__(self, call_data: CallData):
        self.call_data = call_data
        self.storage = None
        self.conversation_log = []
        
        # Enhanced tracking for intelligent system
        self.processed_user_transcripts = set()
        self.processed_agent_speeches = set()
        self.last_user_transcript = ""
        self.last_agent_speech = ""
        self.transcript_timestamps = {}
        
        # Intelligent system context
        self.conversation_stages = []
        self.pricing_discussions = []
        
    async def initialize(self):
        """Initialize storage connection for intelligent system"""
        self.storage = await get_call_storage()
        transcript_logger.info("✅ Intelligent transcription handler ready")
    
    def setup_handlers(self, session):
        """Setup event handlers for intelligent conversation tracking"""
        
        # PRIMARY: User speech from STT
        @session.on("user_input_transcribed")
        def on_user_input_transcribed(event):
            asyncio.create_task(self._handle_user_speech_intelligent(event))
        
        # PRIMARY: Agent speech when created
        @session.on("speech_created") 
        def on_speech_created(event):
            asyncio.create_task(self._handle_agent_speech_intelligent(event))
        
        # INTELLIGENT: Conversation flow tracking
        @session.on("conversation_item_added")
        def on_conversation_item_added(event):
            asyncio.create_task(self._handle_intelligent_conversation_item(event))
        
        # INTELLIGENT: Agent decision tracking
        @session.on("agent_state_changed")
        def on_agent_state_changed(event):
            asyncio.create_task(self._track_agent_decisions(event))
        
        transcript_logger.info("✅ Intelligent transcription handlers configured")
    
    async def _handle_user_speech_intelligent(self, event):
        """INTELLIGENT: Handle user speech with context awareness"""
        try:
            transcript_text = self._extract_transcript_text(event)
            is_final = getattr(event, 'is_final', True)
            confidence = getattr(event, 'confidence', None)
            
            if not transcript_text or len(transcript_text.strip()) == 0:
                return
            
            # Skip very short interim results
            if not is_final and len(transcript_text.strip()) < 3:
                return
            
            # Duplicate prevention
            transcript_clean = transcript_text.strip().lower()
            current_time = time.time()
            
            if self._is_duplicate_user_transcript(transcript_clean, current_time):
                transcript_logger.debug(f"🔄 Skipped duplicate user: {transcript_text}")
                return
            
            # Only save final transcripts
            if is_final:
                self._mark_user_transcript_processed(transcript_clean, current_time)
                
                # INTELLIGENT: Analyze conversation context
                conversation_stage = self.call_data.get_conversation_stage()
                
                transcript_logger.info(f"👤 User ({conversation_stage}): {transcript_text}")
                
                self.conversation_log.append({
                    "timestamp": current_time,
                    "speaker": "user", 
                    "text": transcript_text,
                    "is_final": is_final,
                    "conversation_stage": conversation_stage,
                    "source": "user_input_transcribed"
                })
                
                # INTELLIGENT: Track conversation progress
                if conversation_stage not in self.conversation_stages:
                    self.conversation_stages.append(conversation_stage)
                
                # Save to database with intelligent context
                if self.call_data.session_id and self.call_data.caller_id:
                    await self.storage.save_transcription_segment(
                        session_id=self.call_data.session_id,
                        caller_id=self.call_data.caller_id,
                        speaker="user",
                        text=transcript_text,
                        is_final=is_final,
                        confidence=confidence
                    )
            
        except Exception as e:
            transcript_logger.error(f"❌ Intelligent user speech error: {e}")
    
    async def _handle_agent_speech_intelligent(self, event):
        """INTELLIGENT: Handle agent speech with context tracking"""
        try:
            transcript_logger.debug(f"🧠 Agent speech_created event: {event}")
            
            # Extract speech text comprehensively
            speech_text = self._extract_agent_speech_comprehensive(event)
            
            if not speech_text or len(speech_text.strip()) == 0:
                transcript_logger.debug("⚠️ No speech text found in intelligent agent event")
                return
            
            clean_text = self._clean_agent_speech(speech_text)
            if not clean_text:
                transcript_logger.debug(f"⚠️ Speech text empty after cleaning: '{speech_text}'")
                return
            
            # Duplicate prevention
            speech_clean = clean_text.strip().lower()
            current_time = time.time()
            
            if self._is_duplicate_agent_speech(speech_clean, current_time):
                transcript_logger.debug(f"🔄 Skipped duplicate agent: {clean_text}")
                return
            
            # Mark as processed and save
            self._mark_agent_speech_processed(speech_clean, current_time)
            
            # INTELLIGENT: Analyze agent response type
            response_type = self._analyze_agent_response(clean_text)
            conversation_stage = self.call_data.get_conversation_stage()
            
            transcript_logger.info(f"🧠 Agent ({response_type}): {clean_text}")
            
            self.conversation_log.append({
                "timestamp": current_time,
                "speaker": "agent",
                "text": clean_text,
                "is_final": True,
                "response_type": response_type,
                "conversation_stage": conversation_stage,
                "source": "speech_created"
            })
            
            # INTELLIGENT: Track pricing discussions
            if "price" in clean_text.lower() or "$" in clean_text:
                self.pricing_discussions.append({
                    "timestamp": current_time,
                    "text": clean_text,
                    "stage": conversation_stage
                })
            
            # Save to database with intelligent metadata
            if self.call_data.session_id and self.call_data.caller_id:
                await self.storage.save_transcription_segment(
                    session_id=self.call_data.session_id,
                    caller_id=self.call_data.caller_id,
                    speaker="agent",
                    text=clean_text,
                    is_final=True,
                    confidence=1.0
                )
                
        except Exception as e:
            transcript_logger.error(f"❌ Intelligent agent speech error: {e}")
    
    async def _handle_intelligent_conversation_item(self, event):
        """INTELLIGENT: Handle conversation items with context analysis"""
        try:
            if not hasattr(event, 'item'):
                return
                
            item = event.item
            role = getattr(item, 'role', 'unknown')
            content = self._extract_content_from_item(item)
            
            if not content or len(content.strip()) == 0:
                return
            
            # Only handle assistant responses that might have been missed
            if role not in ["assistant", "agent"]:
                return
            
            content_clean = content.strip().lower()
            current_time = time.time()
            
            # Check for recent captures to avoid duplicates
            recent_cutoff = current_time - 10.0
            for timestamp in self.transcript_timestamps.get('agent', []):
                if timestamp > recent_cutoff:
                    transcript_logger.debug(f"🔄 Agent speech already captured: {content[:50]}...")
                    return
            
            # This is a missed agent response - capture with intelligent analysis
            if not self._is_duplicate_agent_speech(content_clean, current_time):
                self._mark_agent_speech_processed(content_clean, current_time)
                
                response_type = self._analyze_agent_response(content)
                
                transcript_logger.info(f"🧠 Agent (backup-{response_type}): {content}")
                
                self.conversation_log.append({
                    "timestamp": current_time,
                    "speaker": "agent",
                    "text": content,
                    "is_final": True,
                    "response_type": response_type,
                    "source": "conversation_item_backup"
                })
                
                # Save with intelligent metadata
                if self.call_data.session_id and self.call_data.caller_id:
                    await self.storage.save_transcription_segment(
                        session_id=self.call_data.session_id,
                        caller_id=self.call_data.caller_id,
                        speaker="agent",
                        text=content,
                        is_final=True,
                        confidence=1.0
                    )
        
        except Exception as e:
            transcript_logger.error(f"❌ Intelligent conversation item error: {e}")
    
    async def _track_agent_decisions(self, event):
        """INTELLIGENT: Track agent decision-making process"""
        try:
            if hasattr(event, 'state'):
                state = event.state
                transcript_logger.debug(f"🧠 Agent decision state: {state}")
                
                # Track important decision points
                if state in ['thinking', 'processing', 'searching']:
                    conversation_stage = self.call_data.get_conversation_stage()
                    transcript_logger.debug(f"🔄 Agent {state} at stage: {conversation_stage}")
                    
        except Exception as e:
            transcript_logger.debug(f"Agent decision tracking error: {e}")
    
    def _analyze_agent_response(self, text: str) -> str:
        """INTELLIGENT: Analyze type of agent response"""
        text_lower = text.lower()
        
        if "price" in text_lower or "$" in text:
            return "pricing"
        elif any(word in text_lower for word in ["hello", "thank you", "calling"]):
            return "greeting"
        elif any(word in text_lower for word in ["name", "phone", "location", "vehicle"]):
            return "information_collection"
        elif any(word in text_lower for word in ["confirm", "correct", "right"]):
            return "confirmation"
        elif any(word in text_lower for word in ["dispatch", "technician", "arrive"]):
            return "service_arrangement"
        else:
            return "general"
    
    def _extract_transcript_text(self, event) -> str:
        """Extract transcript text from user input event"""
        for attr in ['transcript', 'text', 'content', 'text_content']:
            if hasattr(event, attr):
                value = getattr(event, attr)
                if value:
                    return str(value)
        return ""
    
    def _extract_agent_speech_comprehensive(self, event) -> str:
        """COMPREHENSIVE: Extract agent speech from any possible source"""
        speech_text = None
        
        # Method 1: event.speech.text
        if hasattr(event, 'speech'):
            speech = event.speech
            transcript_logger.debug(f"🔍 Speech object: {speech}")
            
            for attr in ['text', 'source_text', 'content', 'message']:
                if hasattr(speech, attr):
                    value = getattr(speech, attr)
                    if value:
                        speech_text = str(value)
                        transcript_logger.debug(f"✅ Found speech text in speech.{attr}")
                        break
        
        # Method 2: Direct event attributes
        if not speech_text:
            for attr in ['text', 'content', 'message', 'source_text']:
                if hasattr(event, attr):
                    value = getattr(event, attr)
                    if value:
                        speech_text = str(value)
                        transcript_logger.debug(f"✅ Found speech text in event.{attr}")
                        break
        
        # Method 3: Instructions
        if not speech_text:
            if hasattr(event, 'instructions') and event.instructions:
                speech_text = str(event.instructions)
                transcript_logger.debug(f"✅ Found speech text in instructions")
        
        return speech_text or ""
    
    def _extract_content_from_item(self, item) -> str:
        """Extract content from conversation item"""
        for attr in ['text_content', 'content', 'text', 'message']:
            if hasattr(item, attr):
                value = getattr(item, attr)
                if value:
                    return str(value)
        return ""
    
    def _clean_agent_speech(self, text: str) -> str:
        """Clean agent speech text"""
        if not text:
            return ""
        
        cleaned = text.strip()
        
        # Remove instruction prefixes
        prefixes_to_remove = [
            "Say exactly: ", "Say: ", "Respond with: ", "Tell them: ",
            "Reply with: ", "Generate reply: ", "instructions=\"", "instructions='"
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        
        # Remove quotes
        if (cleaned.startswith('"') and cleaned.endswith('"')) or \
           (cleaned.startswith("'") and cleaned.endswith("'")):
            cleaned = cleaned[1:-1].strip()
        
        # Clean artifacts
        cleaned = cleaned.replace('\\n', ' ').replace('\\t', ' ')
        
        return cleaned
    
    def _is_duplicate_user_transcript(self, transcript_clean: str, current_time: float) -> bool:
        """Check if user transcript is duplicate"""
        if transcript_clean in self.processed_user_transcripts:
            return True
        
        for existing_time in self.transcript_timestamps.get('user', []):
            if abs(current_time - existing_time) < 2.0:
                if transcript_clean == self.last_user_transcript:
                    return True
        
        return False
    
    def _is_duplicate_agent_speech(self, speech_clean: str, current_time: float) -> bool:
        """Check if agent speech is duplicate"""
        if speech_clean in self.processed_agent_speeches:
            return True
        
        for existing_time in self.transcript_timestamps.get('agent', []):
            if abs(current_time - existing_time) < 3.0:
                if speech_clean == self.last_agent_speech:
                    return True
        
        return False
    
    def _mark_user_transcript_processed(self, transcript_clean: str, current_time: float):
        """Mark user transcript as processed"""
        self.processed_user_transcripts.add(transcript_clean)
        self.last_user_transcript = transcript_clean
        
        if 'user' not in self.transcript_timestamps:
            self.transcript_timestamps['user'] = []
        self.transcript_timestamps['user'].append(current_time)
        
        # Cleanup old timestamps
        cutoff_time = current_time - 30.0
        self.transcript_timestamps['user'] = [
            t for t in self.transcript_timestamps['user'] if t > cutoff_time
        ]
        
        # Limit set size
        if len(self.processed_user_transcripts) > 100:
            self.processed_user_transcripts = set(list(self.processed_user_transcripts)[-50:])
    
    def _mark_agent_speech_processed(self, speech_clean: str, current_time: float):
        """Mark agent speech as processed"""
        self.processed_agent_speeches.add(speech_clean)
        self.last_agent_speech = speech_clean
        
        if 'agent' not in self.transcript_timestamps:
            self.transcript_timestamps['agent'] = []
        self.transcript_timestamps['agent'].append(current_time)
        
        # Cleanup old timestamps
        cutoff_time = current_time - 30.0
        self.transcript_timestamps['agent'] = [
            t for t in self.transcript_timestamps['agent'] if t > cutoff_time
        ]
        
        # Limit set size
        if len(self.processed_agent_speeches) > 100:
            self.processed_agent_speeches = set(list(self.processed_agent_speeches)[-50:])
    
    def print_conversation_transcript(self):
        """Print intelligent conversation transcript with analysis"""
        print("\n" + "="*70)
        print("🧠 INTELLIGENT CALL TRANSCRIPT")
        print("="*70)
        
        # Print conversation stages progression
        if self.conversation_stages:
            print(f"📈 Conversation Flow: {' → '.join(self.conversation_stages)}")
        
        # Print pricing discussions if any
        if self.pricing_discussions:
            print(f"💰 Pricing Discussions: {len(self.pricing_discussions)}")
        
        print("-"*70)
        
        for i, entry in enumerate(self.conversation_log, 1):
            speaker_label = "🧠 AI Agent" if entry["speaker"] == "agent" else "👤 Customer"
            timestamp = time.strftime("%H:%M:%S", time.localtime(entry["timestamp"]))
            
            # Add intelligent context
            context_info = ""
            if entry["speaker"] == "agent" and "response_type" in entry:
                context_info = f" [{entry['response_type']}]"
            elif "conversation_stage" in entry:
                context_info = f" [{entry['conversation_stage']}]"
            
            print(f"[{timestamp}] {speaker_label}{context_info}: {entry['text']}")
        
        print("="*70)
        
        user_count = len([t for t in self.conversation_log if t["speaker"] == "user"])
        agent_count = len([t for t in self.conversation_log if t["speaker"] == "agent"])
        
        transcript_logger.info(f"📊 Intelligent Session Complete:")
        transcript_logger.info(f"   👤 Customer: {user_count} turns")
        transcript_logger.info(f"   🧠 Agent: {agent_count} turns") 
        transcript_logger.info(f"   📈 Stages: {len(self.conversation_stages)}")
        transcript_logger.info(f"   💰 Pricing discussions: {len(self.pricing_discussions)}")
        transcript_logger.info(f"   📞 Total: {len(self.conversation_log)} exchanges")
    
    async def save_final_transcript(self):
        """Save intelligent transcript summary with analysis"""
        try:
            if not self.call_data.session_id or not self.call_data.caller_id:
                return
            
            # Intelligent transcript analysis
            transcript_analysis = {
                "total_exchanges": len(self.conversation_log),
                "user_turns": len([log for log in self.conversation_log if log["speaker"] == "user"]),
                "agent_turns": len([log for log in self.conversation_log if log["speaker"] == "agent"]),
                "conversation_stages": self.conversation_stages,
                "pricing_discussions": len(self.pricing_discussions),
                "conversation_start": self.conversation_log[0]["timestamp"] if self.conversation_log else None,
                "conversation_end": self.conversation_log[-1]["timestamp"] if self.conversation_log else None,
                "intelligent_features": {
                    "llm_brain": True,
                    "rag_pricing": True,
                    "context_aware": True,
                    "stage_tracking": True
                },
                "final_stage": self.call_data.get_conversation_stage(),
                "pricing_provided": self.call_data.gathered_info.get("pricing_provided", False)
            }
            
            await self.storage.save_conversation_item(
                session_id=self.call_data.session_id,
                caller_id=self.call_data.caller_id,
                role="system",
                content="Intelligent call transcript saved with LLM brain analysis",
                metadata={
                    "type": "final_intelligent_transcript",
                    "analysis": transcript_analysis
                }
            )
            
            transcript_logger.info(f"💾 Intelligent transcript saved:")
            transcript_logger.info(f"   📊 {len(self.conversation_log)} exchanges analyzed")
            transcript_logger.info(f"   🧠 LLM brain: {transcript_analysis['intelligent_features']['llm_brain']}")
            transcript_logger.info(f"   💰 RAG pricing: {transcript_analysis['intelligent_features']['rag_pricing']}")
            
        except Exception as e:
            transcript_logger.error(f"❌ Intelligent transcript save error: {e}")