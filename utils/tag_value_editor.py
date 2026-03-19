"""
Tag Value Editor Utilities
Functions for parsing, editing, and formatting tag values.
"""
from typing import List
from nbt.nbt import (
    Tag, ByteTag, ShortTag, IntTag, LongTag, FloatTag, DoubleTag, StringTag,
    ByteArrayTag, IntArrayTag, LongArrayTag
)


INT32_MIN = -(2**31)
INT32_MAX = 2**31 - 1
INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1


def _to_signed(value: int, bits: int) -> int:
    """
    Convert an integer to two's-complement signed value with the given bit width.
    Example: 200 with bits=8 -> -56.
    """
    mask = (1 << bits) - 1
    value &= mask
    sign_bit = 1 << (bits - 1)
    if value & sign_bit:
        return value - (1 << bits)
    return value


def _parse_int_in_range(value_string: str, min_value: int, max_value: int) -> int:
    if not value_string:
        return 0
    val = int(value_string)
    if val < min_value or val > max_value:
        raise ValueError(f"Value must be in range [{min_value}, {max_value}]")
    return val


def parse_array_string(value_string: str, array_type: type) -> List[int]:
    """
    Parse comma-separated string into array values.
    
    Args:
        value_string: Comma-separated string of values
        array_type: Type of array (ByteArrayTag, IntArrayTag, LongArrayTag)
        
    Returns:
        List of parsed integer values
    """
    if not value_string.strip():
        return []
    
    values = []
    for item in value_string.split(","):
        item = item.strip()
        if item:
            val = int(item)
            if array_type == ByteArrayTag:
                val = val & 0xFF
            values.append(val)
    
    return values


def update_tag_value(tag: Tag, value_string: str) -> None:
    """
    Update a tag's value from a string input.
    
    Args:
        tag: The tag to update
        value_string: String representation of the new value
    """
    value_string = value_string.strip()
    
    if isinstance(tag, IntTag):
        tag.value = _parse_int_in_range(value_string, INT32_MIN, INT32_MAX)
    elif isinstance(tag, FloatTag):
        tag.value = float(value_string) if value_string else 0.0
    elif isinstance(tag, StringTag):
        tag.value = value_string
    elif isinstance(tag, ByteTag):
        # ByteTag is stored as signed 8-bit. Convert from user integer using two's complement.
        tag.value = _to_signed(int(value_string) if value_string else 0, 8)
    elif isinstance(tag, ShortTag):
        # ShortTag is stored as signed 16-bit. Convert from user integer using two's complement.
        tag.value = _to_signed(int(value_string) if value_string else 0, 16)
    elif isinstance(tag, LongTag):
        tag.value = _parse_int_in_range(value_string, INT64_MIN, INT64_MAX)
    elif isinstance(tag, DoubleTag):
        tag.value = float(value_string) if value_string else 0.0
    elif isinstance(tag, ByteArrayTag):
        tag.value = parse_array_string(value_string, ByteArrayTag)
    elif isinstance(tag, IntArrayTag):
        tag.value = parse_array_string(value_string, IntArrayTag)
    elif isinstance(tag, LongArrayTag):
        tag.value = parse_array_string(value_string, LongArrayTag)


def get_tag_display_value(tag: Tag) -> str:
    """
    Get a formatted display string for a tag's value.
    
    Args:
        tag: The tag to format
        
    Returns:
        Formatted string representation of the tag value
    """
    from utils.tag_helpers import is_array_tag, is_list_tag, is_compound_tag
    
    if is_array_tag(tag):
        if len(tag) > 0:
            return ", ".join(map(str, tag.value))
        return "(empty)"
    elif is_list_tag(tag):
        return f"List with {len(tag)} items"
    elif is_compound_tag(tag):
        return f"Compound with {len(tag)} entries"
    else:
        return str(tag.value)


def get_tag_edit_value(tag: Tag) -> str:
    """
    Get the editable string representation of a tag's value.
    
    Args:
        tag: The tag to get the value from
        
    Returns:
        String representation suitable for editing
    """
    from utils.tag_helpers import is_array_tag
    
    if is_array_tag(tag):
        if len(tag) > 0:
            return ", ".join(map(str, tag.value))
        return ""
    else:
        return str(tag.value)

