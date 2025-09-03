# utils/phone_utils.py
"""
Phone number utility functions
"""

def extract_phone_number(participant) -> str:
    """Extract phone number from SIP participant"""
    phone_attrs = [
        "sip.phoneNumber", 
        "sip.from_number", 
        "sip.caller_number",
        "phoneNumber",
        "from_number"
    ]
    
    for attr in phone_attrs:
        if attr in participant.attributes:
            phone = participant.attributes[attr]
            if phone and phone != "unknown":
                return phone
    
    return "unknown"

def format_phone_number(phone: str) -> str:
    """Format phone number for display"""
    if not phone or phone == "unknown":
        return "Unknown"
    
    # Remove any non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    
    # Format as (XXX) XXX-XXXX if US number
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone

def validate_phone_number(phone: str) -> bool:
    """Validate phone number format"""
    if not phone:
        return False
    
    digits = ''.join(filter(str.isdigit, phone))
    
    # US numbers should be 10 or 11 digits
    return len(digits) in [10, 11]