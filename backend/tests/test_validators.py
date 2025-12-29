"""Unit tests for validators"""

import pytest
from app.utils.validators import (
    validate_gstin,
    validate_hsn_code,
    validate_pincode,
    extract_state_code_from_gstin,
    get_state_name
)


def test_valid_gstin():
    """Test valid GSTIN format"""
    # Real GSTIN format examples
    assert validate_gstin("29ABCDE1234F1Z5") == True
    assert validate_gstin("27AABCT1234C1Z5") == True


def test_invalid_gstin_length():
    """Test invalid GSTIN length"""
    assert validate_gstin("29ABCDE1234F1Z") == False  # Too short
    assert validate_gstin("29ABCDE1234F1Z55") == False  # Too long


def test_invalid_gstin_format():
    """Test invalid GSTIN format"""
    assert validate_gstin("XX ABCDE1234F1Z5") == False  # Invalid state code
    assert validate_gstin("29abcde1234F1Z5") == False  # Lowercase
    assert validate_gstin("29ABCDE1234F0Z5") == False  # Invalid entity number


def test_valid_hsn_codes():
    """Test valid HSN code lengths"""
    assert validate_hsn_code("1234") == True  # 4 digits
    assert validate_hsn_code("123456") == True  # 6 digits
    assert validate_hsn_code("12345678") == True  # 8 digits


def test_invalid_hsn_codes():
    """Test invalid HSN codes"""
    assert validate_hsn_code("123") == False  # Too short
    assert validate_hsn_code("12345") == False  # Invalid length
    assert validate_hsn_code("1234567") == False  # Invalid length
    assert validate_hsn_code("ABCD") == False  # Non-numeric


def test_valid_pincode():
    """Test valid pincode"""
    assert validate_pincode("560001") == True
    assert validate_pincode("110001") == True


def test_invalid_pincode():
    """Test invalid pincode"""
    assert validate_pincode("56000") == False  # Too short
    assert validate_pincode("5600011") == False  # Too long
    assert validate_pincode("ABCDEF") == False  # Non-numeric


def test_extract_state_code():
    """Test state code extraction from GSTIN"""
    assert extract_state_code_from_gstin("29ABCDE1234F1Z5") == "29"
    assert extract_state_code_from_gstin("27AABCT1234C1Z5") == "27"
    assert extract_state_code_from_gstin("invalid") == None


def test_get_state_name():
    """Test state name retrieval"""
    assert get_state_name("29") == "Karnataka"
    assert get_state_name("27") == "Maharashtra"
    assert get_state_name("07") == "Delhi"
    assert get_state_name("99") == None  # Invalid code
