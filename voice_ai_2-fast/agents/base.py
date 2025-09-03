# agents/base.py - IMPROVED SEARCH VERSION
"""
Base agent classes with improved knowledge base search functionality
"""
import asyncio
import logging
from typing import Dict, Any, List

from livekit.agents import Agent, RunContext, ChatContext, ChatMessage, function_tool

from logging_config import create_call_logger
from models.call_data import CallData
from simple_rag_v2 import simplified_rag
from call_transcription_storage import get_call_storage

agent_logger = create_call_logger("agent")

class ContextAwareSpecialistAgent(Agent):
    """Base specialist agent with IMPROVED knowledge search"""
    
    def __init__(self, call_data: CallData, specialist_type: str, specialist_name: str):
        self.call_data = call_data
        self.specialist_type = specialist_type
        self.specialist_name = specialist_name
        
        # Build context-aware instructions
        instructions = self._build_context_aware_instructions()
        super().__init__(instructions=instructions)
    
    def _build_context_aware_instructions(self) -> str:
        """Build instructions with FULL context awareness"""
        
        # Get vehicle classification for PRECISE pricing
        vehicle_class = self._classify_vehicle()
        
        instructions = f"""You are {self.specialist_name}, a {self.specialist_type} specialist for roadside assistance.

CRITICAL: You have FULL CONTEXT from the dispatcher. The customer has already provided their information.

CUSTOMER CONTEXT:
- Name: {self.call_data.caller_name or 'Not provided'}
- Phone: {self.call_data.phone_number or 'Not provided'}
- Location: {self.call_data.location or 'Not provided'}
- Vehicle: {self.call_data.get_vehicle_description() or 'Not provided'}
- Vehicle Classification: {vehicle_class}
- Service Requested: {self.call_data.service_type or 'General assistance'}
- Issue: {self.call_data.issue_description or 'Not described'}

NATURAL CONVERSATION FLOW:
1. Acknowledge the transfer naturally: "Hello {self.call_data.caller_name or 'there'}, I understand you need {self.specialist_type} service."
2. Reference their information: "I see you're at {self.call_data.location or 'your location'} with your {self.call_data.get_vehicle_description() or 'vehicle'}."
3. Use search_service_knowledge() with MULTIPLE search strategies for comprehensive results
4. Provide specific pricing based on vehicle classification
5. Guide them through service arrangement

IMPROVED SEARCH STRATEGY:
- Try multiple search terms for better results
- Use vehicle-specific queries when appropriate
- Combine service type + vehicle type for precise matching
- Fallback to general terms if specific searches fail

IMPORTANT: Don't ask for information already provided. Be natural and helpful."""
        
        return instructions
    
    def _classify_vehicle(self) -> str:
        """Classify vehicle for accurate pricing"""
        vehicle_make = (self.call_data.vehicle_make or "").lower()
        vehicle_model = (self.call_data.vehicle_model or "").lower()
        
        # SUV/Truck indicators
        suv_truck_indicators = [
            "truck", "suv", "pickup", "f-150", "silverado", "ram", 
            "tahoe", "suburban", "expedition", "escalade", "navigator",
            "4runner", "pilot", "highlander", "pathfinder", "semi",
            "18 wheeler", "big rig", "heavy duty", "commercial"
        ]
        
        # Check for SUV/Truck indicators first
        if any(indicator in vehicle_make or indicator in vehicle_model for indicator in suv_truck_indicators):
            return "SUV/Truck/Heavy Duty"
        
        # Luxury car indicators
        luxury_indicators = ["bmw", "mercedes", "audi", "lexus", "acura", "infiniti", "cadillac"]
        if any(brand in vehicle_make for brand in luxury_indicators):
            return "Luxury Car"
        
        # Default classification
        return "Standard Car"
    
    async def on_enter(self):
        """Natural context-aware greeting"""
        try:
            customer_name = self.call_data.caller_name or "there"
            vehicle_info = self.call_data.get_vehicle_description()
            location = self.call_data.location
            
            # Build natural greeting with context
            greeting_parts = [
                f"Hello {customer_name}, I understand you need {self.specialist_type} service."
            ]
            
            if vehicle_info and location:
                greeting_parts.append(f"I see you're at {location} with your {vehicle_info}.")
            elif vehicle_info:
                greeting_parts.append(f"I see you have a {vehicle_info}.")
            elif location:
                greeting_parts.append(f"I see you're at {location}.")
            
            greeting_parts.append("Let me get you the right information and pricing.")
            
            greeting = " ".join(greeting_parts)
            
            agent_logger.info(f"🎯 {self.specialist_type} greeting for {customer_name}")
            
            await self.session.generate_reply(
                instructions=f"Say exactly: '{greeting}'"
            )
            
        except Exception as e:
            agent_logger.error(f"❌ {self.specialist_type} greeting error: {e}")
            # Fallback greeting
            await self.session.generate_reply(
                instructions=f"Say: 'Hello! How can I assist you today with {self.specialist_type} services?'"
            )
    
    async def on_user_turn_completed(self, turn_ctx: ChatContext, new_message: ChatMessage) -> None:
        """Enhanced context injection"""
        try:
            user_text = new_message.text_content
            if not user_text or len(user_text.strip()) < 3:
                return
            
            # Inject customer context
            context_message = f"""CUSTOMER CONTEXT:
- Customer: {self.call_data.caller_name or 'Unknown'}
- Vehicle: {self.call_data.get_vehicle_description() or 'Unknown'}
- Vehicle Type: {self._classify_vehicle()}
- Location: {self.call_data.location or 'Unknown'}
- Service: {self.call_data.service_type or self.specialist_type}

Use this context to provide personalized, relevant responses."""
            
            turn_ctx.add_message(role="system", content=context_message)
            
        except Exception as e:
            agent_logger.error(f"❌ {self.specialist_type} context error: {e}")
    
    @function_tool()
    async def search_service_knowledge(
        self, 
        context: RunContext[CallData],
        query: str
    ) -> str:
        """IMPROVED: Multi-strategy knowledge search"""
        try:
            vehicle_class = self._classify_vehicle()
            vehicle_info = context.userdata.get_vehicle_description()
            
            agent_logger.info(f"🔍 {self.specialist_type} knowledge search: {query} (Vehicle: {vehicle_class})")
            
            # IMPROVED: Create multiple search strategies
            search_strategies = []
            
            # Strategy 1: Exact service + vehicle type
            if vehicle_class == "SUV/Truck/Heavy Duty":
                search_strategies.extend([
                    f"heavy duty {self.specialist_type} {query}",
                    f"truck {self.specialist_type} cost",
                    f"commercial {self.specialist_type} pricing"
                ])
            elif vehicle_class == "Luxury Car":
                search_strategies.extend([
                    f"luxury {self.specialist_type} {query}",
                    f"luxury car {self.specialist_type} cost",
                    f"premium {self.specialist_type} service"
                ])
            else:
                search_strategies.extend([
                    f"car {self.specialist_type} {query}",
                    f"standard {self.specialist_type} cost",
                    f"light duty {self.specialist_type} pricing"
                ])
            
            # Strategy 2: Service-specific searches
            search_strategies.extend([
                f"{self.specialist_type} {query}",
                f"{self.specialist_type} service cost",
                f"{self.specialist_type} pricing"
            ])
            
            # Strategy 3: General searches as fallback
            search_strategies.extend([
                f"{query} service",
                f"{query} cost",
                query
            ])
            
            # Try each strategy until we get good results
            best_result = ""
            best_score = 0
            
            for i, search_query in enumerate(search_strategies[:6]):  # Limit to 6 tries
                try:
                    # Use direct retrieval for faster results
                    results = await simplified_rag.search(search_query, limit=2)
                    
                    if results:
                        for result in results:
                            score = result.get("score", 0)
                            text = result.get("text", "")
                            
                            if score > best_score and len(text.strip()) > 20:
                                formatted_result = self._format_knowledge_for_specialist(text, vehicle_class)
                                if formatted_result:
                                    best_result = formatted_result
                                    best_score = score
                                    agent_logger.info(f"✅ Found result with query '{search_query}' (score: {score:.3f})")
                                    break
                    
                    # If we found a good result, stop searching
                    if best_score > 0.7:  # Good confidence threshold
                        break
                        
                except Exception as search_error:
                    agent_logger.debug(f"Search strategy {i+1} failed: {search_error}")
                    continue
            
            if best_result:
                return f"Based on our service information for {vehicle_class.lower()} vehicles: {best_result}"
            else:
                return f"I don't have specific pricing information available right now for {vehicle_class.lower()} {self.specialist_type} service. Let me connect you with dispatch for current pricing."
                
        except Exception as e:
            agent_logger.error(f"❌ {self.specialist_type} knowledge error: {e}")
            return f"I'm having trouble accessing pricing information. Let me transfer you back to dispatch for current {self.specialist_type} service rates."
    
    def _format_knowledge_for_specialist(self, raw_text: str, vehicle_class: str) -> str:
        """Format knowledge specifically for this specialist and vehicle type"""
        if not raw_text:
            return ""
        
        # Clean the text
        cleaned = raw_text.strip()
        cleaned = cleaned.replace("SERVICE:", "").replace("BASE_PRICE:", "").replace("DESCRIPTION:", "")
        cleaned = cleaned.replace("REQUIREMENTS:", "").replace("TIME:", "").replace("PRICING_RULES:", "")
        cleaned = cleaned.replace("Q:", "").replace("A:", "")
        cleaned = cleaned.replace("•", "").replace("-", "").replace("*", "")
        cleaned = cleaned.replace("\n", " ").replace("\t", " ")
        
        # Remove multiple spaces
        while "  " in cleaned:
            cleaned = cleaned.replace("  ", " ")
        
        # Ensure it's relevant and contains useful information
        if (len(cleaned.strip()) > 10 and 
            (self.specialist_type.lower() in cleaned.lower() or
             any(word in cleaned.lower() for word in ["cost", "price", "fee", "$", "service"]))):
            
            # Keep it concise for voice (under 100 characters for quick responses)
            if len(cleaned) > 100:
                sentences = cleaned.split('.')
                if sentences and len(sentences[0].strip()) > 0:
                    cleaned = sentences[0].strip() + "."
                else:
                    cleaned = cleaned[:97] + "..."
            
            return cleaned.strip()
        
        return ""
    
    @function_tool()
    async def arrange_service(
        self, 
        context: RunContext[CallData],
        estimated_arrival: str = "30-45 minutes",
        special_instructions: str = None
    ) -> str:
        """Arrange the specialist service with context"""
        try:
            customer_name = context.userdata.caller_name or "Customer"
            vehicle_info = context.userdata.get_vehicle_description()
            location = context.userdata.location
            
            # Build service arrangement summary
            arrangement_parts = [
                f"Perfect! I'm arranging {self.specialist_type} service for {customer_name}."
            ]
            
            if vehicle_info:
                arrangement_parts.append(f"For your {vehicle_info}")
            
            if location:
                arrangement_parts.append(f"at {location}")
            
            arrangement_parts.append(f"Estimated arrival time: {estimated_arrival}")
            
            if special_instructions:
                arrangement_parts.append(f"Special instructions: {special_instructions}")
            
            arrangement_message = " ".join(arrangement_parts)
            
            # Save to database
            storage = await get_call_storage()
            await storage.save_conversation_item(
                session_id=context.userdata.session_id,
                caller_id=context.userdata.caller_id,
                role="agent",
                content=f"{self.specialist_type} service arranged: {arrangement_message}",
                metadata={
                    "type": "service_arrangement",
                    "specialist": self.specialist_type,
                    "vehicle_class": self._classify_vehicle(),
                    "estimated_arrival": estimated_arrival
                }
            )
            
            agent_logger.info(f"✅ {self.specialist_type} service arranged for {customer_name} (ETA: {estimated_arrival})")
            
            return arrangement_message
            
        except Exception as e:
            agent_logger.error(f"❌ {self.specialist_type} arrangement error: {e}")
            return f"I'm arranging your {self.specialist_type} service now. You should receive a call with the estimated arrival time shortly."