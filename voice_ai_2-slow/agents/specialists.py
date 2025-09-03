# agents/specialists_enhanced.py - ENHANCED WITH NEW KNOWLEDGE BASE
"""
Enhanced specialist agents optimized for the new structured knowledge base
Uses precise search strategies for better service information retrieval
"""
from .base import ContextAwareSpecialistAgent
from models.call_data import CallData
from livekit.agents import RunContext, function_tool
from logging_config import create_call_logger
from call_transcription_storage import get_call_storage

agent_logger = create_call_logger("agent")

class EnhancedTowingSpecialistAgent(ContextAwareSpecialistAgent):
    """Enhanced towing specialist with optimized knowledge base queries"""
    
    def __init__(self, call_data: CallData):
        super().__init__(call_data, "towing", "Sarah")
        
    async def on_enter(self):
        """Context-aware greeting with immediate knowledge search"""
        try:
            customer_name = self.call_data.caller_name or "there"
            vehicle_info = self.call_data.get_vehicle_description()
            location = self.call_data.location
            
            # Build contextual greeting
            greeting_parts = [
                f"Hello {customer_name}, I understand you need towing service"
            ]
            
            if vehicle_info:
                greeting_parts.append(f"for your {vehicle_info}")
            if location:
                greeting_parts.append(f"at {location}")
            
            greeting_parts.append("Let me get you current pricing and service options.")
            greeting = " ".join(greeting_parts)
            
            agent_logger.info(f"🚚 Enhanced towing specialist for {customer_name}")
            
            await self.session.generate_reply(
                instructions=f"Say exactly: '{greeting}'"
            )
            
        except Exception as e:
            agent_logger.error(f"❌ Enhanced towing greeting error: {e}")
    
    @function_tool()
    async def get_towing_pricing(
        self,
        context: RunContext[CallData],
        vehicle_type: str = "standard car",
        service_type: str = "standard towing"
    ) -> str:
        """Get specific towing pricing with enhanced search"""
        try:
            # Build precise search queries for the new knowledge base
            search_queries = []
            
            # Vehicle-specific search
            if "truck" in vehicle_type.lower() or "heavy" in vehicle_type.lower():
                search_queries.extend([
                    "heavy duty towing price",
                    "truck towing cost",
                    "commercial towing pricing"
                ])
            elif "motorcycle" in vehicle_type.lower():
                search_queries.append("motorcycle towing cost")
            elif "luxury" in vehicle_type.lower() or "exotic" in vehicle_type.lower():
                search_queries.append("luxury car towing price")
            else:
                search_queries.extend([
                    "light duty towing price",
                    "car towing cost",
                    "standard towing pricing"
                ])
            
            # Service-specific search
            if "flatbed" in service_type.lower():
                search_queries.append("flatbed towing cost")
            elif "emergency" in service_type.lower():
                search_queries.append("emergency towing price")
            elif "long distance" in service_type.lower():
                search_queries.append("long distance towing cost")
            
            # Try each search query until we get good results
            best_result = ""
            for query in search_queries:
                try:
                    result = await self.search_service_knowledge(context, query)
                    if result and "price" in result.lower() and "$" in result:
                        best_result = result
                        agent_logger.info(f"✅ Found pricing with query: {query}")
                        break
                except Exception:
                    continue
            
            if best_result:
                return f"For {vehicle_type} {service_type}: {best_result}"
            else:
                return f"Let me connect you with dispatch for current {service_type} pricing for your {vehicle_type}."
                
        except Exception as e:
            agent_logger.error(f"❌ Enhanced towing pricing error: {e}")
            return "I'll connect you with someone who can provide current towing rates."
    
    @function_tool()
    async def check_service_availability(
        self,
        context: RunContext[CallData],
        location: str = "",
        urgency: str = "normal"
    ) -> str:
        """Check service availability with location and urgency"""
        try:
            # Build location-aware response
            availability_info = []
            
            if urgency.lower() in ["emergency", "urgent", "high"]:
                search_query = "emergency towing service time"
                availability_info.append("Emergency service prioritized")
            else:
                search_query = "towing service time"
            
            # Get service timing information
            timing_info = await self.search_service_knowledge(context, search_query)
            
            if timing_info:
                availability_info.append(timing_info)
            
            if location:
                availability_info.append(f"Service area includes {location}")
            
            availability_info.append("I can arrange immediate dispatch")
            
            return ". ".join(availability_info) + "."
            
        except Exception as e:
            agent_logger.error(f"❌ Service availability error: {e}")
            return "I can arrange towing service for you right away."

class EnhancedBatterySpecialistAgent(ContextAwareSpecialistAgent):
    """Enhanced battery specialist with optimized knowledge queries"""
    
    def __init__(self, call_data: CallData):
        super().__init__(call_data, "battery", "Mike")
    
    async def on_enter(self):
        """Context-aware battery service greeting"""
        try:
            customer_name = self.call_data.caller_name or "there"
            vehicle_info = self.call_data.get_vehicle_description()
            
            greeting = f"Hello {customer_name}, I understand you're having battery issues with your {vehicle_info or 'vehicle'}. Can you tell me exactly what's happening when you try to start it?"
            
            agent_logger.info(f"🔋 Enhanced battery specialist for {customer_name}")
            
            await self.session.generate_reply(
                instructions=f"Say exactly: '{greeting}'"
            )
            
        except Exception as e:
            agent_logger.error(f"❌ Enhanced battery greeting error: {e}")
    
    @function_tool()
    async def diagnose_battery_issue(
        self,
        context: RunContext[CallData],
        symptoms: str = ""
    ) -> str:
        """Diagnose battery issue and provide service options"""
        try:
            # Analyze symptoms for appropriate service
            symptoms_lower = symptoms.lower()
            
            if any(word in symptoms_lower for word in ["clicking", "lights", "radio"]):
                service_query = "jumpstart service cost"
                diagnosis = "This sounds like your battery needs a jumpstart"
            elif any(word in symptoms_lower for word in ["completely dead", "nothing", "no power"]):
                service_query = "car battery change cost"
                diagnosis = "Your battery may need replacement"
            else:
                service_query = "battery service"
                diagnosis = "Let me check what battery service you need"
            
            # Get service information
            service_info = await self.search_service_knowledge(context, service_query)
            
            if service_info:
                return f"{diagnosis}. {service_info}"
            else:
                return f"{diagnosis}. I can arrange a technician to test your battery and provide the right service."
                
        except Exception as e:
            agent_logger.error(f"❌ Battery diagnosis error: {e}")
            return "I can send a technician to diagnose and fix your battery issue."

class EnhancedTireSpecialistAgent(ContextAwareSpecialistAgent):
    """Enhanced tire specialist with specific tire service queries"""
    
    def __init__(self, call_data: CallData):
        super().__init__(call_data, "tire", "Lisa")
    
    @function_tool()
    async def assess_tire_service(
        self,
        context: RunContext[CallData],
        tire_condition: str = "",
        vehicle_type: str = "standard car"
    ) -> str:
        """Assess tire service needs and pricing"""
        try:
            # Determine service type based on condition
            condition_lower = tire_condition.lower()
            
            if "flat" in condition_lower or "puncture" in condition_lower:
                if "truck" in vehicle_type.lower() or "heavy" in vehicle_type.lower():
                    service_query = "tire change heavy duty cost"
                else:
                    service_query = "flat tire service cost"
            else:
                service_query = "tire service"
            
            # Get specific service information
            service_info = await self.search_service_knowledge(context, service_query)
            
            if service_info:
                return f"For your {vehicle_type} tire service: {service_info}"
            else:
                return f"I can arrange tire service for your {vehicle_type} right away."
                
        except Exception as e:
            agent_logger.error(f"❌ Tire assessment error: {e}")
            return "I can send a technician to help with your tire issue."

class EnhancedFuelSpecialistAgent(ContextAwareSpecialistAgent):
    """Enhanced fuel delivery specialist"""
    
    def __init__(self, call_data: CallData):
        super().__init__(call_data, "fuel", "David")
    
    @function_tool()
    async def arrange_fuel_delivery(
        self,
        context: RunContext[CallData],
        fuel_type: str = "gasoline",
        location: str = ""
    ) -> str:
        """Arrange fuel delivery with specific details"""
        try:
            # Get fuel delivery information
            service_info = await self.search_service_knowledge(context, "fuel delivery cost")
            
            delivery_details = []
            if service_info:
                delivery_details.append(service_info)
            
            if location:
                delivery_details.append(f"Delivery to {location}")
            
            delivery_details.append(f"We'll bring {fuel_type} to get you back on the road")
            
            return ". ".join(delivery_details) + "."
            
        except Exception as e:
            agent_logger.error(f"❌ Fuel delivery error: {e}")
            return "I can arrange fuel delivery to your location right away."

class EnhancedLockoutSpecialistAgent(ContextAwareSpecialistAgent):
    """Enhanced lockout specialist"""
    
    def __init__(self, call_data: CallData):
        super().__init__(call_data, "lockout", "Anna")
    
    @function_tool()
    async def assess_lockout_situation(
        self,
        context: RunContext[CallData],
        lock_type: str = "standard",
        keys_location: str = "inside car"
    ) -> str:
        """Assess lockout situation and provide service info"""
        try:
            # Determine appropriate service
            if "ignition" in keys_location.lower() or "broken" in keys_location.lower():
                service_query = "broken ignition key removal cost"
            else:
                service_query = "car lockout cost"
            
            # Get service information
            service_info = await self.search_service_knowledge(context, service_query)
            
            if service_info:
                return f"For your lockout situation: {service_info}. I'll need to verify vehicle ownership when our technician arrives."
            else:
                return "I can send a locksmith to help you get back into your vehicle safely."
                
        except Exception as e:
            agent_logger.error(f"❌ Lockout assessment error: {e}")
            return "I can arrange lockout service to get you back into your vehicle."

class EnhancedEmergencySpecialistAgent(ContextAwareSpecialistAgent):
    """Enhanced emergency specialist with priority handling"""
    
    def __init__(self, call_data: CallData):
        super().__init__(call_data, "emergency", "Tom")
    
    async def on_enter(self):
        """Priority emergency greeting"""
        try:
            customer_name = self.call_data.caller_name or "there"
            
            greeting = f"Hello {customer_name}, I understand this is an emergency situation. Are you currently in a safe location and do you need emergency services like 911?"
            
            agent_logger.info(f"🚨 Enhanced emergency specialist for {customer_name}")
            
            await self.session.generate_reply(
                instructions=f"Say exactly: '{greeting}'"
            )
            
        except Exception as e:
            agent_logger.error(f"❌ Enhanced emergency greeting error: {e}")
    
    @function_tool()
    async def prioritize_emergency_service(
        self,
        context: RunContext[CallData],
        situation: str = "",
        location: str = ""
    ) -> str:
        """Prioritize emergency service based on situation"""
        try:
            situation_lower = situation.lower()
            
            # Determine service urgency and type
            if any(word in situation_lower for word in ["accident", "collision", "crash"]):
                service_query = "accident removal cost"
                priority = "highest"
            elif any(word in situation_lower for word in ["highway", "freeway", "interstate"]):
                service_query = "emergency towing cost"
                priority = "high"
            else:
                service_query = "emergency roadside assistance"
                priority = "normal"
            
            # Get emergency service info
            service_info = await self.search_service_knowledge(context, service_query)
            
            response_parts = []
            if priority == "highest":
                response_parts.append("This is a priority emergency situation")
            
            if service_info:
                response_parts.append(service_info)
            
            if location:
                response_parts.append(f"Emergency service dispatched to {location}")
            else:
                response_parts.append("Emergency service will be dispatched immediately")
            
            return ". ".join(response_parts) + "."
            
        except Exception as e:
            agent_logger.error(f"❌ Emergency prioritization error: {e}")
            return "Emergency service is being dispatched to your location immediately."

# Enhanced routing functions for the dispatcher
def get_enhanced_specialist_routing():
    """Get enhanced specialist routing with new agents"""
    return {
        "towing": EnhancedTowingSpecialistAgent,
        "battery": EnhancedBatterySpecialistAgent,
        "tire": EnhancedTireSpecialistAgent,
        "fuel": EnhancedFuelSpecialistAgent,
        "lockout": EnhancedLockoutSpecialistAgent,
        "emergency": EnhancedEmergencySpecialistAgent
    }

# Backwards compatibility - update your existing specialists.py imports
TowingSpecialistAgent = EnhancedTowingSpecialistAgent
BatterySpecialistAgent = EnhancedBatterySpecialistAgent
TireSpecialistAgent = EnhancedTireSpecialistAgent
FuelSpecialistAgent = EnhancedFuelSpecialistAgent
LockoutSpecialistAgent = EnhancedLockoutSpecialistAgent
EmergencySpecialistAgent = EnhancedEmergencySpecialistAgent