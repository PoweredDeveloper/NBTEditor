"""
Tag Value Editor Utilities
Functions for parsing, editing, and formatting tag values.
"""
from typing import List
from nbt.nbt import (
    Tag, ByteTag, ShortTag, IntTag, LongTag, FloatTag, DoubleTag, StringTag,
    ByteArrayTag, IntArrayTag, LongArrayTag
)


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
        tag.value = int(value_string) if value_string else 0
    elif isinstance(tag, FloatTag):
        tag.value = float(value_string) if value_string else 0.0
    elif isinstance(tag, StringTag):
        tag.value = value_string
    elif isinstance(tag, ByteTag):
        tag.value = (int(value_string) if value_string else 0) & 0xFF
    elif isinstance(tag, ShortTag):
        tag.value = (int(value_string) if value_string else 0) & 0xFFFF
    elif isinstance(tag, LongTag):
        tag.value = int(value_string) if value_string else 0
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

