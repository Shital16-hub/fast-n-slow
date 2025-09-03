# utils/phone_utils.py - UPDATED FOR FREESWITCH INTEGRATION
"""
Phone number utility functions for FreeSwitch/FusionPBX integration
Handles SIP headers from FreeSwitch → LiveKit SIP Service → LiveKit Cloud
"""
import re
import logging

logger = logging.getLogger(__name__)

def extract_phone_number(participant) -> str:
    """
    Extract phone number from FreeSwitch SIP participant via LiveKit SIP Service
    FreeSwitch → LiveKit SIP → LiveKit Cloud may use different header mappings
    """
    
    # FreeSwitch + LiveKit SIP service may use these attributes
    freeswitch_phone_attrs = [
        # Standard SIP headers
        "sip.phoneNumber", 
        "sip.from_number", 
        "sip.caller_number",
        
        # FreeSwitch specific headers
        "sip.remote_user",      # FreeSwitch caller user part
        "sip.from_user",        # From header user part
        "sip.caller_id_number", # FreeSwitch caller ID
        "sip.ani",              # Automatic Number Identification
        "sip.dnis",             # Dialed Number Identification Service
        
        # LiveKit SIP service mappings
        "phoneNumber",
        "from_number",
        "caller_number",
        "remote_number",
        
        # Fallback attributes
        "phone",
        "number",
        "caller_id"
    ]
    
    logger.debug(f"🔍 Extracting phone from participant attributes: {list(participant.attributes.keys()) if hasattr(participant, 'attributes') else 'No attributes'}")
    
    if not hasattr(participant, 'attributes'):
        logger.warning("⚠️ Participant has no attributes")
        return "unknown"
    
    for attr in freeswitch_phone_attrs:
        if attr in participant.attributes:
            phone = participant.attributes[attr]
            if phone and phone != "unknown" and phone.strip():
                cleaned_phone = clean_phone_number(phone)
                logger.info(f"✅ Found phone number in {attr}: {cleaned_phone}")
                return cleaned_phone
            else:
                logger.debug(f"🔍 Empty value in {attr}: '{phone}'")
    
    # Log all available attributes for debugging
    logger.warning(f"⚠️ No phone number found in any known attribute")
    logger.debug(f"🔍 Available attributes: {dict(participant.attributes)}")
    
    return "unknown"

def clean_phone_number(phone: str) -> str:
    """
    Clean phone number from FreeSwitch SIP headers
    FreeSwitch may send numbers in various formats
    """
    if not phone:
        return "unknown"
    
    # Remove common SIP formatting
    cleaned = phone.strip()
    
    # Remove SIP URI parts (sip:+1234567890@domain.com → +1234567890)
    if "sip:" in cleaned:
        # Extract number from SIP URI
        sip_match = re.search(r'sip:([^@]+)', cleaned)
        if sip_match:
            cleaned = sip_match.group(1)
    
    # Remove quotes and brackets
    cleaned = cleaned.replace('"', '').replace("'", '')
    cleaned = cleaned.replace('<', '').replace('>', '')
    cleaned = cleaned.replace('[', '').replace(']', '')
    
    # Remove common prefixes that FreeSwitch might add
    prefixes_to_remove = ['tel:', 'phone:', 'number:']
    for prefix in prefixes_to_remove:
        if cleaned.lower().startswith(prefix):
            cleaned = cleaned[len(prefix):]
    
    # Normalize the number format
    cleaned = cleaned.strip()
    
    logger.debug(f"🧹 Cleaned phone number: '{phone}' → '{cleaned}'")
    return cleaned

def format_phone_number(phone: str) -> str:
    """Format phone number for display - handles FreeSwitch formats"""
    if not phone or phone == "unknown":
        return "Unknown"
    
    # Clean the phone number first
    cleaned = clean_phone_number(phone)
    
    # Remove any non-digit characters for formatting
    digits = ''.join(filter(str.isdigit, cleaned))
    
    # Format based on digit count
    if len(digits) == 10:
        # US number without country code: 1234567890 → (123) 456-7890
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        # US number with country code: 11234567890 → +1 (123) 456-7890
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    elif len(digits) > 11:
        # International number: keep original format but clean
        return f"+{digits}"
    elif len(digits) >= 7:
        # Shorter numbers: just add dashes
        if len(digits) == 7:
            return f"{digits[:3]}-{digits[3:]}"
        else:
            return cleaned
    else:
        # Very short numbers or extensions: return as-is
        return cleaned

def validate_phone_number(phone: str) -> bool:
    """Validate phone number format - accommodates FreeSwitch formats"""
    if not phone or phone == "unknown":
        return False
    
    cleaned = clean_phone_number(phone)
    digits = ''.join(filter(str.isdigit, cleaned))
    
    # Accept various lengths for different number types
    # US: 10 or 11 digits
    # International: 7-15 digits typically
    # Extensions: 3-6 digits
    return len(digits) >= 3 and len(digits) <= 15

def extract_caller_info(participant) -> dict:
    """
    Extract comprehensive caller information from FreeSwitch SIP participant
    Returns dictionary with all available caller details
    """
    
    info = {
        "phone_number": "unknown",
        "caller_name": "unknown",
        "caller_id_name": "unknown",
        "from_domain": "unknown",
        "to_number": "unknown",
        "original_called_number": "unknown"
    }
    
    if not hasattr(participant, 'attributes'):
        return info
    
    attrs = participant.attributes
    
    # Extract phone number
    info["phone_number"] = extract_phone_number(participant)
    
    # Extract caller name (if available)
    caller_name_attrs = [
        "sip.caller_id_name",
        "sip.from_display_name", 
        "sip.remote_name",
        "caller_name",
        "display_name"
    ]
    
    for attr in caller_name_attrs:
        if attr in attrs and attrs[attr] and attrs[attr] != "unknown":
            info["caller_id_name"] = attrs[attr].strip()
            break
    
    # Extract domain information (useful for routing)
    domain_attrs = [
        "sip.from_host",
        "sip.from_domain",
        "sip.to_host",
        "from_domain",
        "domain"
    ]
    
    for attr in domain_attrs:
        if attr in attrs and attrs[attr]:
            info["from_domain"] = attrs[attr].strip()
            break
    
    # Extract called number (what number was dialed)
    called_number_attrs = [
        "sip.to_user",
        "sip.req_user", 
        "sip.destination_number",
        "destination_number",
        "called_number",
        "to_number"
    ]
    
    for attr in called_number_attrs:
        if attr in attrs and attrs[attr]:
            info["to_number"] = attrs[attr].strip()
            info["original_called_number"] = attrs[attr].strip()
            break
    
    logger.debug(f"📋 Extracted caller info: {info}")
    return info

def get_freeswitch_sip_uri(phone_number: str, sip_service_ip: str, sip_service_port: int = 5060) -> str:
    """
    Generate SIP URI for FreeSwitch gateway configuration
    Used in FusionPBX gateway and ring group setup
    """
    cleaned_number = clean_phone_number(phone_number)
    return f"sip:{cleaned_number}@{sip_service_ip}:{sip_service_port}"

def parse_sip_uri(sip_uri: str) -> dict:
    """
    Parse SIP URI into components
    Useful for debugging FreeSwitch SIP routing
    """
    # sip:user@host:port;params
    sip_pattern = r'sip:([^@]+)@([^:;]+)(?::(\d+))?(?:;(.+))?'
    match = re.match(sip_pattern, sip_uri)
    
    if match:
        return {
            "user": match.group(1),
            "host": match.group(2), 
            "port": int(match.group(3)) if match.group(3) else 5060,
            "params": match.group(4) if match.group(4) else None
        }
    else:
        return {"error": "Invalid SIP URI format"}

def format_for_freeswitch_dialplan(phone_number: str) -> str:
    """
    Format phone number for FreeSwitch dialplan expressions
    Used in FusionPBX destination matching
    """
    cleaned = clean_phone_number(phone_number)
    digits = ''.join(filter(str.isdigit, cleaned))
    
    # For FreeSwitch dialplan, we typically want just digits
    return digits

def is_valid_did_number(number: str) -> bool:
    """
    Validate if number is a valid DID (Direct Inward Dialing) number
    Used for FusionPBX inbound route configuration
    """
    if not number:
        return False
    
    cleaned = clean_phone_number(number)
    digits = ''.join(filter(str.isdigit, cleaned))
    
    # DID numbers are typically 10-11 digits for US
    return len(digits) >= 10 and len(digits) <= 11

def normalize_for_comparison(phone1: str, phone2: str) -> tuple:
    """
    Normalize two phone numbers for comparison
    Useful for matching caller against database records
    """
    def normalize_single(phone):
        if not phone:
            return ""
        cleaned = clean_phone_number(phone)
        digits = ''.join(filter(str.isdigit, cleaned))
        
        # Normalize US numbers to 10 digits (remove country code)
        if len(digits) == 11 and digits[0] == '1':
            digits = digits[1:]
        
        return digits
    
    return normalize_single(phone1), normalize_single(phone2)

def phones_match(phone1: str, phone2: str) -> bool:
    """
    Check if two phone numbers match (accounting for different formats)
    """
    norm1, norm2 = normalize_for_comparison(phone1, phone2)
    return norm1 == norm2 and len(norm1) >= 7  # At least 7 digits to be valid