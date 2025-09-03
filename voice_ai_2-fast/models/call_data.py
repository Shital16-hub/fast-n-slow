# models/call_data.py - UPDATED FOR INTELLIGENT SYSTEM
"""
UPDATED: CallData model for intelligent LLM-based system
"""
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

@dataclass
class CallData:
    """UPDATED: Call data structure for intelligent LLM processing"""
    session_id: Optional[str] = None
    caller_id: Optional[str] = None
    phone_number: Optional[str] = None
    
    # Current call information (gathered during conversation)
    caller_name: Optional[str] = None
    location: Optional[str] = None
    vehicle_year: Optional[str] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    service_type: Optional[str] = None
    issue_description: Optional[str] = None
    
    # Intelligent system flags
    is_intelligent_mode: bool = True
    uses_llm_brain: bool = True
    uses_rag_pricing: bool = True
    
    # Progress tracking for conversation flow
    gathered_info: Dict[str, bool] = field(default_factory=lambda: {
        "name": False,
        "phone": False, 
        "location": False,
        "vehicle": False,
        "service": False,
        "pricing_provided": False
    })
    
    # Simplified caller info (no complex recognition)
    is_returning_caller: bool = False
    previous_calls_count: int = 0
    stored_info: Dict[str, Any] = field(default_factory=dict)
    
    # Current session context for LLM
    conversation_context: List[str] = field(default_factory=list)
    pricing_context: Dict[str, Any] = field(default_factory=dict)
    
    # Performance tracking
    session_start_time: float = field(default_factory=time.time)
    
    def get_vehicle_description(self) -> str:
        """Get complete vehicle description for LLM processing"""
        parts = [self.vehicle_year, self.vehicle_make, self.vehicle_model]
        return " ".join([part for part in parts if part]).strip()
    
    def get_conversation_stage(self) -> str:
        """Get current conversation stage for LLM guidance"""
        if not self.caller_name:
            return "collecting_name"
        elif not self.phone_number or self.phone_number == "unknown":
            return "confirming_phone"
        elif not self.get_vehicle_description():
            return "collecting_vehicle_info"
        elif not self.location:
            return "collecting_location"
        elif not self.service_type:
            return "identifying_service"
        elif not self.gathered_info.get("pricing_provided"):
            return "providing_pricing"
        else:
            return "completing_service"
    
    def get_context_for_llm(self) -> Dict[str, Any]:
        """Get complete context for LLM processing"""
        return {
            "customer_name": self.caller_name,
            "phone_number": self.phone_number,
            "vehicle": {
                "year": self.vehicle_year,
                "make": self.vehicle_make,
                "model": self.vehicle_model,
                "description": self.get_vehicle_description()
            },
            "location": self.location,
            "service_type": self.service_type,
            "conversation_stage": self.get_conversation_stage(),
            "session_duration": time.time() - self.session_start_time
        }
    
    def mark_pricing_provided(self, pricing_details: Dict[str, Any]):
        """Mark that pricing has been provided and store details"""
        self.gathered_info["pricing_provided"] = True
        self.pricing_context = pricing_details
    
    def is_ready_for_pricing(self) -> bool:
        """Check if all information needed for pricing is collected"""
        return (
            self.caller_name and
            self.phone_number and 
            self.get_vehicle_description() and
            self.location and
            self.service_type
        )