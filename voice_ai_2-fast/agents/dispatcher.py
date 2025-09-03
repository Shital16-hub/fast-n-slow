# agents/dispatcher.py - FIXED CLASS NAME
"""
FIXED: IntelligentDispatcherAgent with proper class name and heavy-duty pricing via RAG (no auto-callback)
"""
import asyncio
import datetime
import re
from typing import Annotated
from pydantic import Field

from livekit.agents import Agent, RunContext, ChatContext, ChatMessage, function_tool

from logging_config import create_call_logger
from models.call_data import CallData
from call_transcription_storage import get_call_storage

agent_logger = create_call_logger("agent")

class IntelligentDispatcherAgent(Agent):
    """INTELLIGENT: LLM acts as the brain, RAG provides data, LLM calculates pricing"""

    def __init__(self, call_data: CallData):
        self.call_data = call_data
        instructions = self._build_intelligent_instructions()
        super().__init__(instructions=instructions)

    def _build_intelligent_instructions(self) -> str:
        """Build instructions for intelligent LLM-based operation"""

        current_time = datetime.datetime.now()
        is_night = current_time.hour >= 20 or current_time.hour < 6
        is_weekend = current_time.weekday() >= 5
        time_context = f"Current time: {current_time.strftime('%A, %I:%M %p')} - {'Night service' if is_night else 'Day service'}, {'Weekend' if is_weekend else 'Weekday'}"

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
- store_info(): Store customer data as collected
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
        """Inject context and current time information"""
        try:
            user_text = new_message.text_content
            if not user_text or len(user_text.strip()) < 2:
                return

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

            if context_parts:
                context_msg = f"CURRENT SESSION: {' | '.join(context_parts)}"
                turn_ctx.add_message(role="system", content=context_msg)

            # Time-based pricing context
            current_time = datetime.datetime.now()
            is_night = current_time.hour >= 20 or current_time.hour < 6
            is_weekend = current_time.weekday() >= 5

            time_info = ""
            if is_night:
                time_info += " night service"
            if is_weekend:
                time_info += " weekend service"

            time_msg = f"CURRENT TIME: {current_time.strftime('%A %I:%M %p')} - Search for pricing including{time_info} surcharges if applicable"
            turn_ctx.add_message(role="system", content=time_msg)

            # Add classification context if available
            if hasattr(self.call_data, 'classification_prompt') and self.call_data.classification_prompt:
                turn_ctx.add_message(role="system", content=self.call_data.classification_prompt)
                self.call_data.classification_prompt = None

            stage = self._get_conversation_stage()

            continuity_msg = f"CONVERSATION STAGE: {stage}"
            if context_parts:
                continuity_msg += f"\nCONTINUITY: You already have customer information - DO NOT restart conversation or ask for information already provided. Continue from current stage."

            turn_ctx.add_message(role="system", content=continuity_msg)

        except Exception as e:
            agent_logger.error(f"❌ Context error: {e}")

    def _get_conversation_stage(self) -> str:
        """Determine conversation stage for LLM guidance"""
        if not self.call_data.caller_name:
            return "COLLECT_NAME - Ask for customer's full name"
        elif not self.call_data.phone_number or self.call_data.phone_number == "unknown" or self.call_data.phone_number.startswith("forwarded"):
            return "COLLECT_PHONE - Ask: 'What's the best phone number where I can reach you if we need to call back?'"
        elif not self.call_data.get_vehicle_description():
            return "GET_VEHICLE - Ask for year, make, model"
        elif not self.call_data.location:
            return "GET_LOCATION - Get exact vehicle location and confirm"
        elif not self.call_data.service_type:
            return "IDENTIFY_SERVICE - CRITICAL: Ask 'What type of service do you need today?' (towing, battery, tire, lockout, fuel)"
        else:
            return "PROVIDE_PRICING - Get pricing from knowledge base and calculate with surcharges"

    @function_tool()
    async def store_info(
        self,
        context: RunContext[CallData],
        name: Annotated[str, Field(description="Customer's full name")] = None,
        phone: Annotated[str, Field(description="Phone number")] = None,
        location: Annotated[str, Field(description="Vehicle location/address")] = None,
        vehicle: Annotated[str, Field(description="Vehicle description (year, make, model)")] = None,
        service: Annotated[str, Field(description="Type of service needed")] = None,
    ) -> str:
        """Store customer information"""

        userdata = context.userdata
        updates = []

        if name and len(name.strip()) > 1:
            clean_name = name.strip().title()
            userdata.caller_name = clean_name
            updates.append(f"name: {clean_name}")
            agent_logger.info(f"✅ Name: {clean_name}")

        if phone:
            clean_phone = phone.strip()
            digits_only = re.sub(r'[^\d]', '', clean_phone)
            # Accept 10-15 digits to accommodate international formats
            if 10 <= len(digits_only) <= 15:
                userdata.phone_number = clean_phone
                updates.append(f"phone: {clean_phone}")
                agent_logger.info(f"✅ Phone: {clean_phone}")
            else:
                agent_logger.warning(f"⚠️ Invalid phone format: {phone}")
                return "I need a valid phone number with area code. Could you please provide your full phone number?"

        if location:
            userdata.location = location.strip()
            updates.append(f"location: {location}")
            agent_logger.info(f"✅ Location: {location}")

        if vehicle:
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
            agent_logger.info(f"✅ Vehicle: {vehicle}")

        if service:
            userdata.service_type = service.strip()
            updates.append(f"service: {service}")
            agent_logger.info(f"✅ Service: {service}")

        # Save to database
        if updates:
            asyncio.create_task(self._save_to_database(userdata, updates))

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
        """
        INTELLIGENT: Determine vehicle service classification.
        - Sets context.userdata.vehicle_class to "heavy_duty" or "standard".
        - Uses quick RAG hints when available, but primarily relies on deterministic rules for reliability.
        """
        try:
            vehicle_desc = f"{vehicle_year} {vehicle_make} {vehicle_model}".strip()
            agent_logger.info(f"🧠 LLM analyzing vehicle: {vehicle_desc}")

            # Deterministic heavy-duty keyword rules
            heavy_keywords = [
                "bus", "coach", "shuttle", "school bus", "city bus",
                "semi", "18-wheeler", "tractor", "tractor-trailer", "articulated",
                "box truck", "straight truck", "cargo truck", "26ft", "26 ft", "26-foot",
                "dump truck", "tow truck", "flatbed truck", "garbage truck",
                "cement truck", "mixer", "bucket truck", "boom truck",
                "rv class a", "class a motorhome",
                "commercial truck", "heavy truck", "medium duty", "heavy duty",
            ]
            desc_lower = f"{vehicle_year} {vehicle_make} {vehicle_model}".lower()

            is_heavy = any(k in desc_lower for k in heavy_keywords)

            # Heuristic: large model names often imply heavy (e.g., F-650, F-750)
            if re.search(r"\bf[- ]?(6|7|8)\d{2}\b", desc_lower):
                is_heavy = True

            # Standard defaults for common consumer vehicles
            standard_keywords = [
                "sedan", "coupe", "hatchback", "civic", "corolla", "camry",
                "accord", "model 3", "model y", "cr-v", "rav4", "tucson", "seltos",
                "wrangler", "cherokee", "x series", "x3", "x5", "x7", "tahoe", "suburban",
                "expedition", "pilot", "highlander", "f-150", "silverado 1500", "ram 1500"
            ]
            if any(k in desc_lower for k in standard_keywords):
                is_heavy = False

            vehicle_class = "heavy_duty" if is_heavy else "standard"
            context.userdata.vehicle_class = vehicle_class

            # Provide classification context for LLM
            context_message = f"""VEHICLE CLASSIFICATION:
Vehicle: {vehicle_desc}
CLASSIFICATION RESULT: {vehicle_class.upper()}

CLASSIFICATION RULES:
- HEAVY DUTY: Semi trucks, 18-wheelers, large commercial trucks, buses, large construction equipment, tractor-trailers, medium/heavy-duty units (e.g., box truck 26ft).
- STANDARD/LIGHT DUTY: Cars, SUVs (BMW X Series, Tahoe, Suburban, etc.), pickup trucks (F-150, Silverado 1500), small RVs, motorcycles.

Use heavy-duty pricing in RAG if vehicle_class=heavy_duty."""
            context.userdata.vehicle_analysis_context = context_message
            agent_logger.info(f"🧠 Vehicle classified as: {vehicle_class} ({vehicle_desc})")
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
        """Get complete service information including pricing rules from knowledge base"""
        try:
            from simple_rag_v2 import simplified_rag

            service_type = (context.userdata.service_type or "").strip()
            vehicle_desc = (context.userdata.get_vehicle_description() or "").strip()
            vehicle_class = getattr(context.userdata, "vehicle_class", "") or ""

            # Build comprehensive search queries to get all pricing information
            search_queries = []

            # Primary queries
            if service_type and vehicle_desc:
                search_queries.append(f"{service_type} {vehicle_desc} {vehicle_class} pricing rates rules")
                search_queries.append(f"{service_type} {vehicle_class} towing pricing night weekend surcharge")
            elif service_type:
                search_queries.append(f"{service_type} {vehicle_class} pricing rates rules")
                search_queries.append(f"{service_type} pricing night weekend surcharge")

            # Time-specific queries
            current_time = datetime.datetime.now()
            if current_time.hour >= 20 or current_time.hour < 6:
                search_queries.append(f"{service_type} {vehicle_class} night service pricing")
            if current_time.weekday() >= 5:
                search_queries.append(f"{service_type} {vehicle_class} weekend service pricing")

            # General pricing rules query + caller query
            search_queries.append("pricing rules surcharge night weekend heavy duty standard")
            if query:
                search_queries.append(query)

            agent_logger.info(f"🔍 Comprehensive knowledge search for: service={service_type}, class={vehicle_class}")

            # Collect relevant pricing information
            all_pricing_info = []
            for search_query in search_queries[:5]:  # keep bounded
                try:
                    rag_context = await simplified_rag.retrieve_context(search_query, max_results=2)
                    if rag_context and len(rag_context.strip()) > 10:
                        all_pricing_info.append(rag_context)
                        agent_logger.debug(f"✅ Found info for: {search_query}")
                except Exception as e:
                    agent_logger.debug(f"Search failed for {search_query}: {e}")
                    continue

            if all_pricing_info:
                combined_info = " ".join(all_pricing_info)
                agent_logger.info("✅ Pricing information retrieved from knowledge base")
                return f"COMPLETE PRICING INFORMATION FROM KNOWLEDGE BASE: {combined_info}"
            else:
                agent_logger.warning("⚠️ Limited pricing information found")
                # Explicitly mention heavy_duty in fallback to guide LLM
                class_hint = f" ({vehicle_class})" if vehicle_class else ""
                return f"Basic {service_type or 'roadside assistance'}{class_hint} service available. Please check knowledge base for current rates or starting prices."

        except Exception as e:
            agent_logger.error(f"❌ Knowledge search error: {e}")
            return "Service available. Please use knowledge base for pricing information."

    async def _save_to_database(self, userdata, updates):
        """Save information to database"""
        try:
            storage = await get_call_storage()
            await storage.save_conversation_item(
                session_id=userdata.session_id,
                caller_id=userdata.caller_id,
                role="agent",
                content=f"Information collected: {', '.join(updates)}",
                metadata={"type": "info_collection", "intelligent_mode": True}
            )
        except Exception as e:
            agent_logger.error(f"❌ Database save error: {e}")

# Backwards compatibility
MainDispatcherAgent = IntelligentDispatcherAgent