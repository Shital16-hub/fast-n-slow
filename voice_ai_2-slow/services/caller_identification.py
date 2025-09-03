# services/caller_identification.py - ENHANCED for Better Greeting Context
"""
Enhanced caller identification with better stored information extraction
"""
import re
from typing import Dict, Any, List

from livekit import api, rtc
from livekit.agents import JobContext

from logging_config import create_call_logger
from models.call_data import CallData
from call_transcription_storage import get_call_storage
from utils.phone_utils import extract_phone_number

caller_logger = create_call_logger("caller_id")

async def identify_caller_and_restore_context(ctx: JobContext) -> CallData:
    """Enhanced caller identification with comprehensive stored information retrieval"""
    
    try:
        participant = await ctx.wait_for_participant()
        
        if participant.kind != rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
            caller_logger.warning("⚠️ No SIP participant found")
            return CallData()
        
        phone_number = extract_phone_number(participant)
        caller_logger.info(f"📞 Incoming call: {phone_number}")
        
        storage = await get_call_storage()
        caller_profile = await storage.get_caller_by_phone(phone_number)
        
        is_returning = False
        previous_calls = 0
        existing_caller_id = None
        stored_info = {}
        
        if caller_profile:
            if (caller_profile.total_calls > 0 and 
                caller_profile.caller_id and 
                caller_profile.caller_id.strip() and
                caller_profile.first_call_time and
                caller_profile.last_call_time):
                
                is_returning = True
                previous_calls = caller_profile.total_calls
                existing_caller_id = caller_profile.caller_id
                
                # Get comprehensive conversation history for better context
                history = await storage.get_caller_conversation_history(
                    caller_id=caller_profile.caller_id,
                    limit=50,  # More history for better context
                    days_back=365  # Full year of history
                )
                
                stored_info = await extract_comprehensive_information(history)
                
                caller_logger.info(f"👤 Returning caller: {previous_calls} previous calls")
                caller_logger.info(f"📋 Stored info: Name={stored_info.get('name', 'None')}, Service={stored_info.get('service', 'None')}, Vehicle={stored_info.get('vehicle', 'None')}")
            else:
                caller_logger.info("📋 Profile exists but incomplete - treating as new")
        else:
            caller_logger.info("👤 New caller detected")
        
        session_id, caller_id = await storage.start_call_session(
            phone_number=phone_number,
            session_metadata={
                "participant_identity": participant.identity,
                "returning_caller": is_returning,
                "previous_calls": previous_calls,
                "stored_info": stored_info
            }
        )
        
        if is_returning and existing_caller_id:
            caller_id = existing_caller_id
        
        call_data = CallData()
        call_data.session_id = session_id
        call_data.caller_id = caller_id
        call_data.phone_number = phone_number
        call_data.is_returning_caller = is_returning
        call_data.previous_calls_count = previous_calls
        call_data.stored_info = stored_info
        
        # Pre-populate known information
        if stored_info.get('name'):
            call_data.caller_name = stored_info['name']
        if stored_info.get('phone'):
            call_data.phone_number = stored_info['phone']
        if stored_info.get('service'):
            call_data.service_type = stored_info['service']
        
        caller_logger.info(f"✅ Session started: {session_id}")
        caller_logger.info(f"📊 Caller status: Returning={is_returning}, Previous calls={previous_calls}")
        
        return call_data
        
    except Exception as e:
        caller_logger.error(f"❌ Caller identification error: {e}")
        return CallData()

async def extract_comprehensive_information(history: List) -> Dict[str, Any]:
    """Enhanced information extraction from conversation history"""
    stored_info = {}
    
    try:
        # Track the most recent and reliable information
        name_confidence = 0
        service_confidence = 0
        vehicle_confidence = 0
        
        for item in history:
            content = item.content.lower() if hasattr(item, 'content') else ""
            role = item.role.lower() if hasattr(item, 'role') else ""
            
            # Enhanced name extraction with confidence scoring
            if role == "user":
                name_patterns = [
                    (r"my name is ([a-zA-Z\s]{2,30})", 3),  # Highest confidence
                    (r"i'm ([a-zA-Z\s]{2,30})", 2),
                    (r"this is ([a-zA-Z\s]{2,30})", 2),
                    (r"call me ([a-zA-Z\s]{2,30})", 2),
                ]
                
                for pattern, confidence in name_patterns:
                    match = re.search(pattern, content)
                    if match and confidence > name_confidence:
                        potential_name = match.group(1).strip().title()
                        # Enhanced validation
                        if (len(potential_name.split()) <= 3 and 
                            not any(word in potential_name.lower() for word in [
                                "sorry", "help", "stuck", "service", "calling", 
                                "need", "car", "mark", "agent", "roadside",
                                "hello", "yes", "no", "okay", "sure", "thanks"
                            ]) and
                            len(potential_name) > 2):
                            stored_info['name'] = potential_name
                            name_confidence = confidence
            
            # Enhanced service type extraction
            service_patterns = [
                ("towing", ["tow", "towed", "towing", "pull", "move my car"]),
                ("battery", ["battery", "dead battery", "jump", "jumpstart", "won't start"]),
                ("tire", ["tire", "flat tire", "puncture", "flat"]),
                ("fuel", ["gas", "fuel", "empty", "ran out", "out of gas"]),
                ("lockout", ["locked out", "keys", "locked", "can't get in"])
            ]
            
            for service_name, keywords in service_patterns:
                if any(keyword in content for keyword in keywords):
                    if service_confidence < 2:  # Only update if not already confident
                        stored_info['service'] = service_name
                        service_confidence = 2
            
            # Enhanced vehicle extraction
            vehicle_brands = [
                "honda", "toyota", "ford", "chevy", "chevrolet", "bmw", "audi", 
                "mercedes", "nissan", "hyundai", "kia", "jeep", "dodge", 
                "volkswagen", "vw", "subaru", "mazda", "lexus", "acura"
            ]
            
            for brand in vehicle_brands:
                if brand in content:
                    year_pattern = r'\b(19|20)\d{2}\b'
                    year_match = re.search(year_pattern, item.content)
                    year = year_match.group() if year_match else ""
                    
                    if vehicle_confidence < 2:
                        brand_display = brand.title()
                        if brand == "chevy":
                            brand_display = "Chevrolet"
                        elif brand == "vw":
                            brand_display = "Volkswagen"
                        
                        vehicle_desc = f"{year} {brand_display}".strip()
                        stored_info['vehicle'] = vehicle_desc
                        vehicle_confidence = 2
            
            # Phone number extraction (for validation)
            phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            phone_match = re.search(phone_pattern, item.content)
            if phone_match and 'phone' not in stored_info:
                stored_info['phone'] = phone_match.group()
        
        # Log what we found
        if stored_info:
            caller_logger.info(f"📊 Extracted info: {stored_info}")
        
        return stored_info
        
    except Exception as e:
        caller_logger.error(f"❌ Enhanced info extraction error: {e}")
        return {}

def extract_stored_information(history: List) -> Dict[str, Any]:
    """Legacy function - now delegates to enhanced version"""
    import asyncio
    return asyncio.run(extract_comprehensive_information(history))