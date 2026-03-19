import unittest

from nbt.nbt import (
    ByteTag,
    ShortTag,
    IntTag,
    LongTag,
    ListTag,
    TagType,
    ByteArrayTag,
    StringTag,
)
from utils.tag_value_editor import update_tag_value


class TestTagValueEditorRanges(unittest.TestCase):
    def test_byte_tag_out_of_range_wrapped_to_signed(self):
        tag = ByteTag(0)
        update_tag_value(tag, "200")  # 200 -> -56 when represented as signed byte
        self.assertEqual(tag.value, -56)

    def test_short_tag_out_of_range_wrapped_to_signed(self):
        tag = ShortTag(0)
        update_tag_value(tag, "40000")  # 40000 -> -25536 when represented as signed short
        self.assertEqual(tag.value, -25536)

    def test_int_tag_out_of_range_rejected(self):
        tag = IntTag(0)
        with self.assertRaises(ValueError):
            update_tag_value(tag, "2147483648")  # int32 max + 1

    def test_long_tag_out_of_range_rejected(self):
        tag = LongTag(0)
        with self.assertRaises(ValueError):
            update_tag_value(tag, "9223372036854775808")  # int64 max + 1


class TestNBTRoundTripAndValidation(unittest.TestCase):
    def test_empty_list_preserves_element_type(self):
        # Per NBT spec: element type id is stored even when list is empty.
        original = ListTag([], TagType.STRING)
        blob = original.serialize()
        parsed, offset = ListTag.deserialize(blob, 0)
        self.assertEqual(offset, len(blob))
        self.assertEqual(parsed.list_tag_type, TagType.STRING)

    def test_invalid_list_element_type_id_rejected(self):
        # element type id 99 is invalid (valid ids are 0..12).
        blob = bytes([99]) + (0).to_bytes(4, byteorder="big", signed=True)
        with self.assertRaises(ValueError):
            ListTag.deserialize(blob, 0)

    def test_byte_array_bounds_checked(self):
        # Declared length is 10 but only 2 bytes are present.
        blob = (10).to_bytes(4, byteorder="big", signed=True) + b"\x01\x02"
        with self.assertRaises(ValueError):
            ByteArrayTag.deserialize(blob, 0)

    def test_string_bounds_checked(self):
        # Declared length is 5 but only 2 bytes are present (and they form valid utf-8).
        blob = (5).to_bytes(2, byteorder="big", signed=False) + b"hi"
        with self.assertRaises(ValueError):
            StringTag.deserialize(blob, 0)


if __name__ == "__main__":
    unittest.main()

