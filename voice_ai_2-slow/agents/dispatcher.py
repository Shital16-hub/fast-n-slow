# agents/dispatcher.py - FIXED VERSION
"""
FIXED: Ultra-fast IntelligentDispatcherAgent with corrected store_info function
The issue was that all parameters were required but should be optional
"""
import asyncio
import datetime
import re
import time
from typing import Annotated, Dict, Any, Optional
from pydantic import Field

from livekit.agents import Agent, RunContext, ChatContext, ChatMessage, function_tool

from logging_config import create_call_logger
from models.call_data import CallData
from call_transcription_storage import get_call_storage

agent_logger = create_call_logger("agent")

# OPTIMIZATION: Global response cache for common responses
RESPONSE_CACHE = {}
PRICING_CACHE = {}
CACHE_MAX_SIZE = 100

class OptimizedIntelligentDispatcherAgent(Agent):
    """FIXED: Ultra-fast LLM brain with corrected function parameters"""

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

        # YOUR EXACT SPECIFIED INSTRUCTIONS
        instructions = f"""You are Mark, an intelligent dispatcher for General Towing & Roadside Assistance.

🧠 YOU ARE THE BRAIN: Use your intelligence to:
- Process information from search_knowledge() 
- Calculate pricing based on service data + time/day surcharges
- Make decisions about service requirements (standard vs heavy_duty)
- Present information clearly and professionally

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

   EXAMPLES:
   - "2023 bus" = HEAVY DUTY → Ask service type → Continue to location → Pull heavy-duty pricing via RAG → Present total
   - "BMW X Series" = STANDARD → Continue to location → Pricing via RAG → Present total

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

   If RAG returns a range or starting rate, present the best-available figure and explain briefly:
   "For heavy-duty towing, pricing starts at $X based on our guidelines. With night/weekend adjustments, today's total is $Y."

7. COMPLETION:
   If accepted: "Great! I'll dispatch the nearest available unit and share the ETA."
   If customer asks to compare/confirm: Summarize the math again and ask for confirmation to proceed.
   If declined: "Thank you for calling. Please feel free to call us back if you change your mind."

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
4. Trust the RAG system for pricing rules - don't override with hardcoded values. If heavy-duty rates are separate, use them; if absent, use best-available guideline and state that clearly.

🔧 TOOLS:
- store_info(): Store customer data as collected (ALL PARAMETERS ARE OPTIONAL!)
- vehicle_size_tool(): Determine vehicle classification and store it for pricing logic
- search_knowledge(): Get pricing data from knowledge base
- Your BRAIN: Process the data and calculate intelligent final pricing

NEVER say "routing" or "transferring" - you handle everything intelligently.

🚨 CRITICAL CONVERSATION CONTINUITY:
- NEVER restart the conversation if customer says "hello", "are you there", etc.
- If interrupted, continue from where you left off using stored information
- Always check what information you already have before asking again
- Use context to maintain conversation flow, don't reset to beginning"""
        
        return instructions

    async def on_user_turn_completed(self, turn_ctx: ChatContext, new_message: ChatMessage) -> None:
        """Inject context with timeout protection to prevent hanging"""
        try:
            start_time = time.time()
            user_text = new_message.text_content
            
            if not user_text or len(user_text.strip()) < 2:
                return

            # TIMEOUT PROTECTION: Add timeout to context processing
            try:
                await asyncio.wait_for(
                    self._process_user_message(turn_ctx, new_message),
                    timeout=2.0  # 2 second timeout for context processing
                )
                
                context_time = (time.time() - start_time) * 1000
                agent_logger.debug(f"⚡ Context processed in {context_time:.1f}ms")
                
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
        
        # CRITICAL DEBUG: Log what the user said
        agent_logger.info(f"🔍 Processing user input: '{user_text}'")
        
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
        """OPTIMIZED: Single fast knowledge search with smart caching"""
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
                    
                    # Cache successful results
                    if len(PRICING_CACHE) < CACHE_MAX_SIZE:
                        PRICING_CACHE[cache_key] = rag_context
                    
                    agent_logger.info(f"✅ Knowledge retrieved in {search_time:.1f}ms")
                    return f"PRICING INFORMATION: {rag_context}"
                else:
                    agent_logger.warning(f"⚠️ No knowledge found for: {optimized_query}")
                    return f"Service available for {vehicle_class} {service_type}. Please check with dispatch for current pricing."
                    
            except asyncio.TimeoutError:
                agent_logger.warning(f"⏰ Knowledge search timeout for: {optimized_query}")
                return f"Service available. Please use standard rates for {vehicle_class} {service_type}."

        except Exception as e:
            agent_logger.error(f"❌ Knowledge search error: {e}")
            return f"Service available. Standard pricing applies."

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
                "fast_vehicle_classification"
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