"""Validators for GSTIN, HSN, and other Indian compliance fields"""

import re
from app.config import settings


def validate_gstin(gstin: str) -> bool:
    """
    Validate GSTIN format and checksum.
    
    Format: 2 digits state code + 10 chars PAN + 1 entity number + Z + 1 checksum
    Example: 29ABCDE1234F1Z5
    
    Args:
        gstin: 15-character GSTIN string
        
    Returns:
        True if valid, False otherwise
    """
    if not gstin or len(gstin) != 15:
        return False
    
    # Format validation
    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    if not re.match(pattern, gstin):
        return False
    
    # Checksum validation (respect settings toggle)
    if not settings.gstin_checksum_enforced:
        return True
    return _validate_gstin_checksum(gstin)


def _validate_gstin_checksum(gstin: str) -> bool:
    """
    Validate GSTIN checksum (last character).
    
    Algorithm: Modulo 36 calculation on first 14 characters
    """
    checksum_char = gstin[14]
    base = gstin[:14]
    
    # Character to number mapping
    def char_value(c: str) -> int:
        if c.isdigit():
            return int(c)
        return ord(c) - ord('A') + 10
    
    # Calculate weighted sum (GST official: factors alternate 1,2 starting from 1)
    total = 0
    for i, char in enumerate(base):
        value = char_value(char)
        factor = 1 if i % 2 == 0 else 2
        product = value * factor
        total += product // 36 + product % 36
    
    # Calculate checksum
    checksum_value = (36 - (total % 36)) % 36
    expected_checksum = str(checksum_value) if checksum_value < 10 else chr(ord('A') + checksum_value - 10)
    
    return checksum_char == expected_checksum


def validate_hsn_code(hsn: str, turnover_category: str = "medium") -> bool:
    """
    Validate HSN/SAC code based on turnover category.
    
    Rules:
    - Turnover < 1.5 cr: 4 digits optional
    - Turnover 1.5-5 cr: 4 digits mandatory
    - Turnover > 5 cr: 6 digits mandatory (8 for exports)
    
    Args:
        hsn: HSN/SAC code string
        turnover_category: "low", "medium", "high"
        
    Returns:
        True if valid, False otherwise
    """
    if not hsn or not hsn.isdigit():
        return False
    
    length = len(hsn)
    
    if turnover_category == "low":
        return length in [4, 6, 8]
    elif turnover_category == "medium":
        return length in [4, 6, 8]
    elif turnover_category == "high":
        return length in [6, 8]
    
    return False


def validate_pincode(pincode: str) -> bool:
    """
    Validate Indian pincode (6 digits).
    
    Args:
        pincode: 6-digit pincode string
        
    Returns:
        True if valid, False otherwise
    """
    return bool(pincode and pincode.isdigit() and len(pincode) == 6)


def extract_state_code_from_gstin(gstin: str) -> str | None:
    """
    Extract state code from GSTIN (first 2 digits).
    
    Args:
        gstin: 15-character GSTIN string
        
    Returns:
        2-digit state code or None if invalid
    """
    if validate_gstin(gstin):
        return gstin[:2]
    return None


# State code to state name mapping (Indian states and UTs)
STATE_CODES = {
    "01": "Jammu and Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "26": "Dadra and Nagar Haveli and Daman and Diu",
    "27": "Maharashtra",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman and Nicobar Islands",
    "36": "Telangana",
    "37": "Andhra Pradesh",
    "38": "Ladakh",
}


def get_state_name(state_code: str) -> str | None:
    """
    Get state name from state code.
    
    Args:
        state_code: 2-digit state code
        
    Returns:
        State name or None if invalid
    """
    return STATE_CODES.get(state_code)


# State name to state code mapping (reverse lookup)
# e.g., {"Karnataka": "29", "Maharashtra": "27", ...}
STATE_CODE_MAP = {name: code for code, name in STATE_CODES.items()}
