"""
Tag Helper Utilities
Centralized functions for tag type checking and operations.
"""
from nbt.nbt import (
    Tag, ByteTag, ShortTag, IntTag, LongTag, FloatTag, DoubleTag, StringTag,
    ByteArrayTag, IntArrayTag, LongArrayTag, ListTag, CompoundTag
)


# Tag type groups for easy checking
PRIMITIVE_TAGS = (ByteTag, ShortTag, IntTag, LongTag, FloatTag, DoubleTag, StringTag)
ARRAY_TAGS = (ByteArrayTag, IntArrayTag, LongArrayTag)
COMPLEX_TAGS = (ListTag, CompoundTag)
EDITABLE_TAGS = PRIMITIVE_TAGS + ARRAY_TAGS
ADDABLE_TAGS = (CompoundTag, ListTag) + ARRAY_TAGS


def is_primitive_tag(tag: Tag) -> bool:
    """Check if tag is a primitive type (Byte, Short, Int, Long, Float, Double, String)"""
    return isinstance(tag, PRIMITIVE_TAGS)


def is_array_tag(tag: Tag) -> bool:
    """Check if tag is an array type (ByteArray, IntArray, LongArray)"""
    return isinstance(tag, ARRAY_TAGS)


def is_complex_tag(tag: Tag) -> bool:
    """Check if tag is a complex type (List, Compound)"""
    return isinstance(tag, COMPLEX_TAGS)


def is_compound_tag(tag: Tag) -> bool:
    """Check if tag is a Compound tag"""
    return isinstance(tag, CompoundTag)


def is_list_tag(tag: Tag) -> bool:
    """Check if tag is a List tag"""
    return isinstance(tag, ListTag)


def can_add_to_tag(tag: Tag) -> bool:
    """Check if tag supports adding children (Compound, List, Arrays)"""
    return isinstance(tag, ADDABLE_TAGS)


def can_edit_tag(tag: Tag) -> bool:
    """Check if tag value can be directly edited (Primitives and Arrays)"""
    return isinstance(tag, EDITABLE_TAGS)


def can_delete_from_parent(parent_tag: Tag) -> bool:
    """Check if a tag can be deleted from its parent (parent must be Compound)"""
    return isinstance(parent_tag, CompoundTag)


def get_tag_type_name(tag: Tag) -> str:
    """Get the human-readable type name of a tag"""
    return type(tag).__name__


def is_integer_type(tag: Tag) -> bool:
    """Check if tag is an integer type (Byte, Short, Int, Long)"""
    return isinstance(tag, (ByteTag, ShortTag, IntTag, LongTag))


def is_float_type(tag: Tag) -> bool:
    """Check if tag is a float type (Float, Double)"""
    return isinstance(tag, (FloatTag, DoubleTag))

