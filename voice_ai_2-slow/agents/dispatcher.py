# agents/dispatcher.py - COMPLETE VERSION WITH TRANSFER FUNCTIONALITY AND DEBUG
"""
COMPLETE: Ultra-fast IntelligentDispatcherAgent with transfer functionality and debug
"""
import asyncio
import datetime
import re
import time
from typing import Annotated, Dict, Any, Optional
from pydantic import Field

from livekit.agents import Agent, RunContext, ChatContext, ChatMessage, function_tool
from livekit.agents import get_job_context
from livekit import rtc

from logging_config import create_call_logger
from models.call_data import CallData
from call_transcription_storage import get_call_storage

agent_logger = create_call_logger("agent")

# OPTIMIZATION: Global response cache for common responses
RESPONSE_CACHE = {}
PRICING_CACHE = {}
CACHE_MAX_SIZE = 100

class OptimizedIntelligentDispatcherAgent(Agent):
    """COMPLETE: Ultra-fast LLM brain with transfer functionality and debug"""

    def __init__(self, call_data: CallData):
        self.call_data = call_data
        self.response_start_times = {}  # Track response times
        instructions = self._build_optimized_instructions()
        super().__init__(instructions=instructions)

    def _build_optimized_instructions(self) -> str:
        """Build your exact specified instructions with optimizations"""

        current_time = datetime.datetime.now()
        is_night = current_time.hour >= 20 or current_time.hour < 6
        is_weekend = current_time.weekday() >= 5
        time_context = f"Current time: {current_time.strftime('%A, %I:%M %p')} - {'Night service' if is_night else 'Day service'}, {'Weekend' if is_weekend else 'Weekday'}"

        # YOUR EXACT SPECIFIED INSTRUCTIONS WITH TRANSFER CAPABILITY
        instructions = f"""You are Mark, an intelligent dispatcher for General Towing & Roadside Assistance.

🧠 YOU ARE THE BRAIN: Use your intelligence to:
- Process information from search_knowledge() 
- Calculate pricing based on service data + time/day surcharges
- Make decisions about service requirements (standard vs heavy_duty)
- Present information clearly and professionally
- Transfer calls to human agents when requested

⏰ TIME CONTEXT: {time_context}
📞 NOTE: Always ask for customer's actual phone number (system number is forwarded)

📋 EXACT CONVERSATION FLOW:

1. GREETING & NAME:
   "Hello, thank you for calling General Towing & Roadside Assistance! I'm Mark, and I'm here to help you today."
   "May I please get your full name so I can better assist you?"
   Use name throughout: "Thanks, {{customerName}}"

2. PHONE COLLECTION:
   "What's the best phone number where I can reach you if we need to call back?"
   Store this as their actual callback number
   Then confirm: "Perfect, so I can reach you at [number] if needed, is that correct?"

3. VEHICLE INFORMATION:
   "To assist you better, could you tell me the year, make, and model of your vehicle?"
   Call vehicle_size_tool() which will provide classification and store it as standard or heavy_duty.

   When you receive "needs_llm_classification", check the classification_prompt in context and follow its instructions exactly:
   - Read the classification prompt provided
   - Analyze the vehicle using the CLASSIFICATION RULES
   - Make decision: "heavy_duty" or "standard"

   ✅ IMPORTANT BEHAVIOR CHANGE:
   - If HEAVY DUTY: Ask "What type of service do you need today?" (towing, battery, tire, lockout, fuel).
     Then CONTINUE the normal flow (no auto-callback script). You must:
       • Proceed to LOCATION
       • Use search_knowledge() to retrieve HEAVY-DUTY pricing for the given service/vehicle
       • Apply surcharges (Night +20% for 8PM-6AM, Weekend +10% Sat-Sun)
       • Present a clear price breakdown and ask to proceed
   - If STANDARD: Continue to location step and price the same way.

4. VEHICLE LOCATION:
   "What is the exact location of your vehicle? Please provide the full street address, city, and any nearby landmarks if possible. Accurate location details help us dispatch assistance quickly."
   Confirm: "So your vehicle is at [location]. Is that correct?"

5. SERVICE TYPE:
   "What type of service do you need today?"
   Identify: towing, battery, tire, lockout, fuel, etc.

6. SUMMARY & PRICING INTELLIGENCE:
   "Just to confirm, you have a [year] [make] [model] at [location] and you need [service]. Is there anything else I should know?"

   Then call search_knowledge() to get pricing data (be explicit about heavy_duty if applicable).
   Use your BRAIN to calculate final pricing:
   - Base price from RAG data (prefer heavy-duty pricing if vehicle_class=heavy_duty)
   - Night surcharge
   - Weekend surcharge
   - Present clearly with breakdown

7. COMPLETION:
   If accepted: "Great! I'll dispatch the nearest available unit and share the ETA."
   If customer asks to compare/confirm: Summarize the math again and ask for confirmation to proceed.
   If declined: "Thank you for calling. Please feel free to call us back if you change your mind."

🔄 TRANSFER TO HUMAN AGENT:
If customer requests to speak with a human, agent, person, representative, or says "transfer":
- Use transfer_to_human_agent() immediately
- Don't ask follow-up questions about the transfer request
- The system will handle the transfer to extension 201

🧠 PRICING INTELLIGENCE:
When you get pricing data from search_knowledge():
1. The RAG system will provide pricing information including:
   - Base prices (standard vs heavy-duty when available)
   - Night surcharge rules (8PM-6AM): +20% 
   - Weekend surcharge rules (Sat-Sun): +10%
   - Any other pricing notes
2. Use your intelligence to:
   - Parse the pricing information from RAG
   - Apply the correct surcharges based on current time
   - Calculate final pricing
   - Present clearly with breakdown
3. Present like: "For your 2020 Honda Civic towing, the cost will be $90 (base $75 plus $15 night service charge according to our pricing guidelines)."

🔧 TOOLS:
- store_info(): Store customer data as collected (ALL PARAMETERS ARE OPTIONAL!)
- vehicle_size_tool(): Determine vehicle classification and store it for pricing logic
- search_knowledge(): Get pricing data from knowledge base
- transfer_to_human_agent(): Transfer call to human agent when requested
- Your BRAIN: Process the data and calculate intelligent final pricing

NEVER say "routing" or "transferring" - you handle everything intelligently unless specifically transferring to human.

🚨 CRITICAL CONVERSATION CONTINUITY:
- NEVER restart the conversation if customer says "hello", "are you there", etc.
- If interrupted, continue from where you left off using stored information
- Always check what information you already have before asking again
- Use context to maintain conversation flow, don't reset to beginning"""
        
        return instructions

    async def on_user_turn_completed(self, turn_ctx: ChatContext, new_message: ChatMessage) -> None:
        """Enhanced context injection with transfer detection and debug"""
        try:
            start_time = time.time()
            user_text = new_message.text_content
            
            if not user_text or len(user_text.strip()) < 2:
                return

            # CRITICAL DEBUG: Log what the user said
            agent_logger.info(f"🔍 Processing user input: '{user_text}'")

            # Check for transfer request FIRST
            if self._should_transfer_to_human(user_text):
                turn_ctx.add_message(
                    role="system", 
                    content=f"User requested human agent: '{user_text}'. Use transfer_to_human_agent() to transfer the call immediately."
                )
                return

            # TIMEOUT PROTECTION: Add timeout to context processing
            try:
                await asyncio.wait_for(
                    self._process_user_message(turn_ctx, new_message),
                    timeout=2.0  # 2 second timeout for context processing
                )
                
                context_time = (time.time() - start_time) * 1000
                agent_logger.debug(f"⚡ Context processed in {context_time:.1f}ms")
                
                # ADD THIS CRITICAL DEBUG:
                agent_logger.info(f"🎯 TRIGGERING LLM RESPONSE GENERATION NOW")
                
            except asyncio.TimeoutError:
                context_time = (time.time() - start_time) * 1000
                agent_logger.error(f"❌ Context processing timeout after {context_time:.1f}ms")
                
                # Add minimal context as fallback
                stage = self._get_conversation_stage()
                turn_ctx.add_message(role="system", content=f"STAGE: {stage} - Respond to user immediately.")

        except Exception as e:
            agent_logger.error(f"❌ Context error: {e}")
            
    async def _process_user_message(self, turn_ctx: ChatContext, new_message: ChatMessage):
        """Process user message with full context (wrapped with timeout)"""
        user_text = new_message.text_content
        
        # Current session context
        context_parts = []
        if self.call_data.caller_name:
            context_parts.append(f"Customer: {self.call_data.caller_name}")
        if self.call_data.phone_number and self.call_data.phone_number != "unknown":
            context_parts.append(f"Phone: {self.call_data.phone_number}")
        if self.call_data.location:
            context_parts.append(f"Location: {self.call_data.location}")
        if self.call_data.get_vehicle_description():
            context_parts.append(f"Vehicle: {self.call_data.get_vehicle_description()}")
        if getattr(self.call_data, "vehicle_class", None):
            context_parts.append(f"Class: {self.call_data.vehicle_class}")
        if self.call_data.service_type:
            context_parts.append(f"Service: {self.call_data.service_type}")

        # Conversation stage for exact flow
        stage = self._get_conversation_stage()
        agent_logger.info(f"🎯 Current conversation stage: {stage}")

        # SIMPLIFIED: Add only essential context to prevent timeout
        if context_parts:
            context_msg = f"SESSION: {' | '.join(context_parts)}"
            turn_ctx.add_message(role="system", content=context_msg)

        # CRITICAL: Add immediate response instruction with specific guidance
        if stage == "COLLECT_NAME":
            response_instruction = f"User said their name is '{user_text}'. Store it with store_info(name='{user_text}') and then ask for their callback phone number following step 2 of your conversation flow."
        elif stage == "COLLECT_PHONE":
            response_instruction = f"User provided phone: '{user_text}'. Store it with store_info(phone='{user_text}') and ask about their vehicle following step 3."
        else:
            response_instruction = f"STAGE: {stage} - User said: '{user_text}' - Respond immediately following your conversation flow step {stage}."
        
        turn_ctx.add_message(role="system", content=response_instruction)
        agent_logger.info(f"📝 Added response instruction for stage: {stage}")

    def _get_conversation_stage(self) -> str:
        """OPTIMIZED: Fast conversation stage determination"""
        if not self.call_data.caller_name:
            return "COLLECT_NAME"
        elif not self.call_data.phone_number or self.call_data.phone_number == "unknown":
            return "COLLECT_PHONE"
        elif not self.call_data.get_vehicle_description():
            return "GET_VEHICLE"
        elif not self.call_data.location:
            return "GET_LOCATION"
        elif not self.call_data.service_type:
            return "IDENTIFY_SERVICE"
        else:
            return "PROVIDE_PRICING"

    def _should_transfer_to_human(self, user_message: str) -> bool:
        """Check if user is requesting human agent"""
        transfer_keywords = [
            "human", "agent", "person", "transfer", "speak with",
            "talk to", "customer service", "representative", "supervisor",
            "human nature", "actual person", "real person", "operator",
            "connect me", "get me to", "escalate"
        ]
        user_lower = user_message.lower()
        return any(keyword in user_lower for keyword in transfer_keywords)

    @function_tool()
    async def store_info(
        self,
        context: RunContext[CallData],
        name: Annotated[Optional[str], Field(description="Customer's full name", default=None)] = None,
        phone: Annotated[Optional[str], Field(description="Phone number", default=None)] = None,
        location: Annotated[Optional[str], Field(description="Vehicle location/address", default=None)] = None,
        vehicle: Annotated[Optional[str], Field(description="Vehicle description (year, make, model)", default=None)] = None,
        service: Annotated[Optional[str], Field(description="Type of service needed", default=None)] = None,
    ) -> str:
        """FIXED: Fast information storage with OPTIONAL parameters"""

        userdata = context.userdata
        updates = []

        # SPEED: Direct assignment with minimal validation
        if name and len(name.strip()) > 1:
            clean_name = name.strip().title()
            userdata.caller_name = clean_name
            updates.append(f"name: {clean_name}")

        if phone:
            clean_phone = phone.strip()
            digits_only = re.sub(r'[^\d]', '', clean_phone)
            if 10 <= len(digits_only) <= 15:
                userdata.phone_number = clean_phone
                updates.append(f"phone: {clean_phone}")

        if location:
            userdata.location = location.strip()
            updates.append(f"location: {location}")

        if vehicle:
            # OPTIMIZED: Fast vehicle parsing
            vehicle_parts = vehicle.strip().split()
            if len(vehicle_parts) >= 2:
                for part in vehicle_parts:
                    if part.isdigit() and len(part) == 4 and part.startswith(('19', '20')):
                        userdata.vehicle_year = part
                        break

                non_year_parts = [p for p in vehicle_parts if not (p.isdigit() and len(p) == 4)]
                if non_year_parts:
                    userdata.vehicle_make = non_year_parts[0]
                    if len(non_year_parts) > 1:
                        userdata.vehicle_model = ' '.join(non_year_parts[1:])

            updates.append(f"vehicle: {vehicle}")

        if service:
            userdata.service_type = service.strip()
            updates.append(f"service: {service}")

        # OPTIMIZATION: Async database save (non-blocking)
        if updates:
            asyncio.create_task(self._save_to_database(userdata, updates))

        # SPEED: Cached responses for common confirmations
        customer_name = userdata.caller_name
        if updates and customer_name:
            return f"Got it, {customer_name}."
        elif updates:
            return "Perfect, I have that information."
        else:
            return "I'm ready to help you."

    @function_tool()
    async def vehicle_size_tool(
        self,
        context: RunContext[CallData],
        vehicle_year: str,
        vehicle_make: str, 
        vehicle_model: str
    ) -> str:
        """OPTIMIZED: Fast vehicle classification with caching"""
        try:
            vehicle_desc = f"{vehicle_year} {vehicle_make} {vehicle_model}".strip()
            
            # OPTIMIZATION: Check cache first
            cache_key = f"{vehicle_make.lower()}_{vehicle_model.lower()}"
            if cache_key in RESPONSE_CACHE:
                vehicle_class = RESPONSE_CACHE[cache_key]
                context.userdata.vehicle_class = vehicle_class
                agent_logger.debug(f"⚡ Vehicle classification cached: {vehicle_class}")
                return vehicle_class

            # Fast classification logic
            desc_lower = f"{vehicle_year} {vehicle_make} {vehicle_model}".lower()
            
            # Heavy-duty keywords (quick check)
            heavy_keywords = [
                "bus", "semi", "18-wheeler", "tractor", "box truck", "dump truck",
                "commercial", "heavy duty", "medium duty", "f-650", "f-750"
            ]
            
            is_heavy = any(k in desc_lower for k in heavy_keywords)
            vehicle_class = "heavy_duty" if is_heavy else "standard"
            
            # Cache result
            if len(RESPONSE_CACHE) < CACHE_MAX_SIZE:
                RESPONSE_CACHE[cache_key] = vehicle_class
            
            context.userdata.vehicle_class = vehicle_class
            
            agent_logger.info(f"🧠 Vehicle classified: {vehicle_desc} → {vehicle_class}")
            return vehicle_class

        except Exception as e:
            agent_logger.error(f"❌ Vehicle analysis error: {e}")
            context.userdata.vehicle_class = "standard"
            return "standard"

    @function_tool()
    async def search_knowledge(
        self, 
        context: RunContext[CallData],
        query: str
    ) -> str:
        """OPTIMIZED: Single fast knowledge search with smart caching and debug"""
        try:
            start_time = time.time()
            
            service_type = (context.userdata.service_type or "").strip()
            vehicle_class = getattr(context.userdata, "vehicle_class", "") or "standard"
            
            # OPTIMIZATION: Build single optimized query instead of multiple searches
            if service_type and vehicle_class:
                optimized_query = f"{service_type} {vehicle_class} pricing cost rate"
            elif service_type:
                optimized_query = f"{service_type} pricing cost"
            else:
                optimized_query = query
            
            # OPTIMIZATION: Check pricing cache first
            cache_key = f"{service_type}_{vehicle_class}".lower()
            if cache_key in PRICING_CACHE:
                cached_result = PRICING_CACHE[cache_key]
                search_time = (time.time() - start_time) * 1000
                agent_logger.info(f"⚡ Pricing cache hit in {search_time:.1f}ms")
                return cached_result

            agent_logger.info(f"🔍 Single optimized search: {optimized_query}")

            # CRITICAL: Single RAG search instead of multiple
            from simple_rag_v2 import simplified_rag
            
            try:
                # Single search with timeout
                rag_context = await asyncio.wait_for(
                    simplified_rag.retrieve_context(optimized_query, max_results=3),
                    timeout=3.0
                )
                
                if rag_context and len(rag_context.strip()) > 15:
                    search_time = (time.time() - start_time) * 1000
                    
                    # ADD THESE DEBUG LINES:
                    agent_logger.info(f"🎯 RAG CONTEXT FOUND: {rag_context[:100]}...")
                    return_value = f"PRICING INFORMATION: {rag_context}"
                    agent_logger.info(f"🔄 RETURNING TO LLM: {return_value[:100]}...")
                    
                    # Cache successful results
                    if len(PRICING_CACHE) < CACHE_MAX_SIZE:
                        PRICING_CACHE[cache_key] = return_value
                    
                    agent_logger.info(f"✅ Knowledge retrieved in {search_time:.1f}ms")
                    return return_value
                else:
                    agent_logger.warning(f"⚠️ No knowledge found for: {optimized_query}")
                    return f"Service available for {vehicle_class} {service_type}. Please check with dispatch for current pricing."
                    
            except asyncio.TimeoutError:
                agent_logger.warning(f"⏰ Knowledge search timeout for: {optimized_query}")
                return f"Service available. Please use standard rates for {vehicle_class} {service_type}."

        except Exception as e:
            agent_logger.error(f"❌ Knowledge search error: {e}")
            return f"Service available. Standard pricing applies."

    @function_tool()
    async def transfer_to_human_agent(
        self, 
        context: RunContext[CallData],
        reason: str = "Customer requested human assistance"
    ) -> str:
        """Transfer call to human agent with correct participant detection"""
        try:
            # Import here to avoid circular imports
            from utils.transfer_handler import call_transfer_handler
            
            # Inform customer
            await context.session.generate_reply(
                instructions="Say: 'I'm transferring you to a human agent now. Please hold.'"
            )
            
            # Wait for the message to play
            await asyncio.sleep(2)
            
            # Get job context and room
            job_ctx = get_job_context()
            room_name = job_ctx.room.name
            
            # Debug: Log all participants
            agent_logger.info(f"🔍 Room participants debug:")
            agent_logger.info(f"   Room name: {room_name}")
            
            # Find the SIP participant
            sip_participant = None
            
            # Look through remote participants in the room
            for participant in job_ctx.room.remote_participants.values():
                agent_logger.info(f"   Remote participant: {participant.identity}, kind: {participant.kind}")
                
                # Check for SIP participant using the correct enum
                if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
                    sip_participant = participant
                    agent_logger.info(f"✅ Found SIP participant: {participant.identity}")
                    break
            
            # If no SIP participant found, get the first non-agent participant
            if not sip_participant:
                for participant in job_ctx.room.remote_participants.values():
                    # Skip agent participants - look for standard participants  
                    if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_STANDARD:
                        sip_participant = participant
                        agent_logger.info(f"✅ Found standard participant: {participant.identity}")
                        break
            
            # Final fallback - get any remote participant
            if not sip_participant and job_ctx.room.remote_participants:
                sip_participant = list(job_ctx.room.remote_participants.values())[0]
                agent_logger.info(f"✅ Using first available participant: {sip_participant.identity}")
            
            if not sip_participant:
                agent_logger.error("❌ No participant found for transfer")
                await context.session.generate_reply(
                    instructions="Say: 'I'm sorry, I can't transfer the call right now. Let me continue helping you.'"
                )
                return "No participant found for transfer"
            
            participant_identity = sip_participant.identity
            
            agent_logger.info(f"🔄 Executing transfer: room={room_name}, participant={participant_identity}")
            
            # Execute transfer
            result = await call_transfer_handler.transfer_to_human(room_name, participant_identity)
            
            # Check string result, not enum
            if result["result"] == "success":
                agent_logger.info("✅ Transfer completed successfully")
                return "Transfer completed successfully"
            else:
                agent_logger.error(f"❌ Transfer failed: {result['message']}")
                await context.session.generate_reply(
                    instructions="Say: 'I'm sorry, I couldn't connect you to an agent right now. Let me continue helping you.'"
                )
                return f"Transfer failed: {result['message']}"
                
        except Exception as e:
            agent_logger.error(f"❌ Transfer error: {e}")
            
            try:
                await context.session.generate_reply(
                    instructions="Say: 'I'm having trouble connecting you to an agent. Let me continue helping you with your request.'"
                )
            except:
                pass
                
            return f"Transfer error: {e}"

    async def _save_to_database(self, userdata, updates):
        """OPTIMIZED: Async non-blocking database save"""
        try:
            storage = await get_call_storage()
            await storage.save_conversation_item(
                session_id=userdata.session_id,
                caller_id=userdata.caller_id,
                role="agent",
                content=f"Information collected: {', '.join(updates)}",
                metadata={"type": "optimized_info_collection", "updates": len(updates)}
            )
        except Exception as e:
            agent_logger.error(f"❌ Database save error: {e}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get agent performance statistics"""
        return {
            "response_cache_size": len(RESPONSE_CACHE),
            "pricing_cache_size": len(PRICING_CACHE), 
            "optimizations_enabled": [
                "consolidated_context",
                "single_rag_search",
                "smart_caching",
                "async_database_writes",
                "fast_vehicle_classification",
                "human_transfer_capability",
                "debug_logging"
            ]
        }

# OPTIMIZATION: Cache cleanup function
def cleanup_caches():
    """Clean up caches when they get too large"""
    global RESPONSE_CACHE, PRICING_CACHE
    
    if len(RESPONSE_CACHE) > CACHE_MAX_SIZE:
        # Keep most recent half
        items = list(RESPONSE_CACHE.items())
        RESPONSE_CACHE = dict(items[-CACHE_MAX_SIZE//2:])
    
    if len(PRICING_CACHE) > CACHE_MAX_SIZE:
        # Keep most recent half
        items = list(PRICING_CACHE.items())
        PRICING_CACHE = dict(items[-CACHE_MAX_SIZE//2:])

# For backward compatibility
IntelligentDispatcherAgent = OptimizedIntelligentDispatcherAgent
MainDispatcherAgent = OptimizedIntelligentDispatcherAgent