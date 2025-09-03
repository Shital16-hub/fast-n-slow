# utils/helpers.py
"""
General helper functions for the Voice AI system
"""
import time
import re
from typing import Optional, Dict, Any, List

def clean_text_for_voice(text: str) -> str:
    """Clean text for better voice readability"""
    if not text:
        return ""
    
    # Remove common artifacts
    cleaned = text.strip()
    cleaned = cleaned.replace("Q:", "").replace("A:", "")
    cleaned = cleaned.replace("•", "").replace("-", "").replace("*", "")
    cleaned = cleaned.replace("\n", " ").replace("\t", " ")
    
    # Remove multiple spaces
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    
    return cleaned

def extract_vehicle_info(text: str) -> Dict[str, Optional[str]]:
    """Extract vehicle information from text"""
    vehicle_info = {
        "year": None,
        "make": None,
        "model": None
    }
    
    text_lower = text.lower()
    
    # Extract year
    year_pattern = r'\b(19|20)\d{2}\b'
    year_match = re.search(year_pattern, text)
    if year_match:
        vehicle_info["year"] = year_match.group()
    
    # Extract make (common brands)
    brands = [
        "honda", "toyota", "ford", "chevy", "chevrolet", "bmw", "audi", 
        "mercedes", "nissan", "hyundai", "kia", "jeep", "dodge", 
        "volkswagen", "vw", "subaru", "mazda", "lexus", "acura", "infiniti"
    ]
    
    for brand in brands:
        if brand in text_lower:
            vehicle_info["make"] = brand.title()
            if brand == "chevy":
                vehicle_info["make"] = "Chevrolet"
            elif brand == "vw":
                vehicle_info["make"] = "Volkswagen"
            break
    
    return vehicle_info

def classify_service_urgency(text: str) -> str:
    """Classify service urgency from description"""
    text_lower = text.lower()
    
    # Emergency indicators
    emergency_words = [
        "emergency", "urgent", "stranded", "highway", "dangerous", 
        "accident", "stuck", "blocking", "traffic"
    ]
    
    if any(word in text_lower for word in emergency_words):
        return "high"
    
    # Medium urgency indicators
    medium_words = [
        "won't start", "dead battery", "flat tire", "locked out",
        "breakdown", "broken down"
    ]
    
    if any(word in text_lower for word in medium_words):
        return "medium"
    
    return "normal"

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        if minutes > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{hours} hour{'s' if hours != 1 else ''}"

def sanitize_text_for_logging(text: str, max_length: int = 100) -> str:
    """Sanitize text for safe logging"""
    if not text:
        return ""
    
    # Remove potential sensitive information patterns
    sanitized = text
    
    # Remove phone numbers
    sanitized = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', sanitized)
    
    # Remove email addresses
    sanitized = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', sanitized)
    
    # Remove potential SSN
    sanitized = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', sanitized)
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length-3] + "..."
    
    return sanitized

def calculate_performance_score(response_time_ms: float, success: bool) -> float:
    """Calculate performance score based on response time and success"""
    if not success:
        return 0.0
    
    # Excellent: < 1000ms = 1.0
    # Good: 1000-2000ms = 0.8
    # Fair: 2000-3000ms = 0.6
    # Poor: > 3000ms = 0.4
    
    if response_time_ms < 1000:
        return 1.0
    elif response_time_ms < 2000:
        return 0.8
    elif response_time_ms < 3000:
        return 0.6
    else:
        return 0.4

def validate_gathered_info(gathered_info: Dict[str, bool]) -> Dict[str, Any]:
    """Validate gathered information completeness"""
    required_fields = ["name", "phone", "location", "vehicle", "service"]
    
    missing = [field for field, gathered in gathered_info.items() if not gathered and field in required_fields]
    complete = len(missing) == 0
    completion_rate = (len(required_fields) - len(missing)) / len(required_fields)
    
    return {
        "complete": complete,
        "missing_fields": missing,
        "completion_rate": completion_rate,
        "next_required": missing[0] if missing else None
    }