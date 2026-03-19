"""
Custom NBT (Named Binary Tag) Library
Implements the NBT format used by Minecraft.
"""
import gzip
import struct
from typing import Any, Dict, List, Optional, Union, IO
from enum import IntEnum


class TagType(IntEnum):
    """NBT tag type IDs"""
    END = 0
    BYTE = 1
    SHORT = 2
    INT = 3
    LONG = 4
    FLOAT = 5
    DOUBLE = 6
    BYTE_ARRAY = 7
    STRING = 8
    LIST = 9
    COMPOUND = 10
    INT_ARRAY = 11
    LONG_ARRAY = 12


class Tag:
    """Base class for NBT tags"""
    
    def __init__(self, value: Any = None):
        self.value = value
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"
    
    def __str__(self):
        return str(self.value)
    
    def __eq__(self, other):
        if isinstance(other, Tag):
            return self.value == other.value
        return self.value == other
    
    def __getitem__(self, key):
        raise TypeError(f"{self.__class__.__name__} does not support indexing")
    
    def __setitem__(self, key, value):
        raise TypeError(f"{self.__class__.__name__} does not support item assignment")
    
    def __len__(self):
        raise TypeError(f"{self.__class__.__name__} does not support len()")
    
    def __iter__(self):
        raise TypeError(f"{self.__class__.__name__} is not iterable")
    
    @classmethod
    def tag_type(cls) -> TagType:
        raise NotImplementedError
    
    def serialize(self) -> bytes:
        raise NotImplementedError
    
    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple['Tag', int]:
        raise NotImplementedError


class ByteTag(Tag):
    """Byte tag (8-bit signed integer)"""
    
    @classmethod
    def tag_type(cls) -> TagType:
        return TagType.BYTE
    
    def serialize(self) -> bytes:
        return struct.pack('>b', self.value)
    
    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple['ByteTag', int]:
        value = struct.unpack_from('>b', data, offset)[0]
        return cls(value), offset + 1


class ShortTag(Tag):
    """Short tag (16-bit signed integer)"""
    
    @classmethod
    def tag_type(cls) -> TagType:
        return TagType.SHORT
    
    def serialize(self) -> bytes:
        return struct.pack('>h', self.value)
    
    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple['ShortTag', int]:
        value = struct.unpack_from('>h', data, offset)[0]
        return cls(value), offset + 2


class IntTag(Tag):
    """Int tag (32-bit signed integer)"""
    
    @classmethod
    def tag_type(cls) -> TagType:
        return TagType.INT
    
    def serialize(self) -> bytes:
        return struct.pack('>i', self.value)
    
    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple['IntTag', int]:
        value = struct.unpack_from('>i', data, offset)[0]
        return cls(value), offset + 4


class LongTag(Tag):
    """Long tag (64-bit signed integer)"""
    
    @classmethod
    def tag_type(cls) -> TagType:
        return TagType.LONG
    
    def serialize(self) -> bytes:
        return struct.pack('>q', self.value)
    
    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple['LongTag', int]:
        value = struct.unpack_from('>q', data, offset)[0]
        return cls(value), offset + 8


class FloatTag(Tag):
    """Float tag (32-bit IEEE 754 floating point)"""
    
    @classmethod
    def tag_type(cls) -> TagType:
        return TagType.FLOAT
    
    def serialize(self) -> bytes:
        return struct.pack('>f', self.value)
    
    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple['FloatTag', int]:
        value = struct.unpack_from('>f', data, offset)[0]
        return cls(value), offset + 4


class DoubleTag(Tag):
    """Double tag (64-bit IEEE 754 floating point)"""
    
    @classmethod
    def tag_type(cls) -> TagType:
        return TagType.DOUBLE
    
    def serialize(self) -> bytes:
        return struct.pack('>d', self.value)
    
    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple['DoubleTag', int]:
        value = struct.unpack_from('>d', data, offset)[0]
        return cls(value), offset + 8


class ByteArrayTag(Tag):
    """Byte array tag"""
    
    def __init__(self, value: Union[List[int], bytes] = None):
        if value is None:
            value = []
        elif isinstance(value, bytes):
            value = list(value)
        super().__init__(value)
    
    def __len__(self):
        return len(self.value)
    
    def __getitem__(self, key):
        return self.value[key]
    
    def __setitem__(self, key, value):
        self.value[key] = value
    
    def __iter__(self):
        return iter(self.value)
    
    @classmethod
    def tag_type(cls) -> TagType:
        return TagType.BYTE_ARRAY
    
    def serialize(self) -> bytes:
        length = len(self.value)
        result = struct.pack('>i', length)
        result += bytes(self.value)
        return result
    
    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple['ByteArrayTag', int]:
        if offset + 4 > len(data):
            raise ValueError("Truncated ByteArrayTag length")
        length = struct.unpack_from('>i', data, offset)[0]
        offset += 4
        if length < 0:
            raise ValueError("Negative ByteArrayTag length")
        end = offset + length
        if end > len(data):
            raise ValueError("Truncated ByteArrayTag payload")
        value = list(data[offset:end])
        return cls(value), end


class StringTag(Tag):
    """String tag (UTF-8 encoded)"""
    
    @classmethod
    def tag_type(cls) -> TagType:
        return TagType.STRING
    
    def serialize(self) -> bytes:
        encoded = self.value.encode('utf-8')
        length = len(encoded)
        return struct.pack('>H', length) + encoded
    
    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple['StringTag', int]:
        if offset + 2 > len(data):
            raise ValueError("Truncated StringTag length")
        length = struct.unpack_from('>H', data, offset)[0]
        offset += 2
        end = offset + length
        if end > len(data):
            raise ValueError("Truncated StringTag payload")
        value = data[offset:end].decode('utf-8')
        return cls(value), end


class ListTag(Tag):
    """List tag (homogeneous list of tags)"""
    
    def __init__(self, value: List[Tag] = None, tag_type: Optional[TagType] = None):
        if value is None:
            value = []
        super().__init__(value)
        self.list_tag_type = tag_type
    
    def __len__(self):
        return len(self.value)
    
    def __getitem__(self, key):
        return self.value[key]
    
    def __setitem__(self, key, value):
        self.value[key] = value
    
    def __iter__(self):
        return iter(self.value)
    
    def append(self, item: Tag):
        if self.list_tag_type is None:
            self.list_tag_type = item.tag_type()
        elif item.tag_type() != self.list_tag_type:
            raise TypeError(f"List expects {self.list_tag_type}, got {item.tag_type()}")
        self.value.append(item)
    
    @classmethod
    def tag_type(cls) -> TagType:
        return TagType.LIST
    
    def serialize(self) -> bytes:
        element_tag_type_id: TagType
        if self.list_tag_type is not None:
            element_tag_type_id = self.list_tag_type
        elif self.value:
            element_tag_type_id = self.value[0].tag_type()
        else:
            element_tag_type_id = TagType.END

        result = struct.pack('>B', element_tag_type_id)
        result += struct.pack('>i', len(self.value))
        for tag in self.value:
            result += tag.serialize()
        return result
    
    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple['ListTag', int]:
        if offset + 1 > len(data):
            raise ValueError("Truncated ListTag element type id")
        tag_type_id = struct.unpack_from('>B', data, offset)[0]
        offset += 1
        if offset + 4 > len(data):
            raise ValueError("Truncated ListTag length")
        length = struct.unpack_from('>i', data, offset)[0]
        offset += 4
        if length < 0:
            raise ValueError("Negative ListTag length")

        if tag_type_id not in TAG_CLASSES:
            raise ValueError(f"Invalid ListTag element type id: {tag_type_id}")
        element_tag_type = TagType(tag_type_id)

        if length == 0:
            # Preserve the element type id even for empty lists (NBT spec).
            return cls([], element_tag_type), offset
        if element_tag_type == TagType.END:
            raise ValueError("ListTag cannot be non-empty with element type END")

        tag_class = TAG_CLASSES[tag_type_id]
        if tag_class is None:
            raise ValueError("Invalid ListTag element type (no handler)")
        tags = []
        for _ in range(length):
            if offset >= len(data):
                raise ValueError("Truncated ListTag payload")
            tag, offset = tag_class.deserialize(data, offset)
            tags.append(tag)

        return cls(tags, element_tag_type), offset


class CompoundTag(Tag):
    """Compound tag (dictionary-like structure)"""
    
    def __init__(self, value: Dict[str, Tag] = None):
        if value is None:
            value = {}
        super().__init__(value)
    
    def __len__(self):
        return len(self.value)
    
    def __getitem__(self, key: str) -> Tag:
        return self.value[key]
    
    def __setitem__(self, key: str, value: Tag):
        self.value[key] = value
    
    def __delitem__(self, key: str):
        del self.value[key]
    
    def __contains__(self, key: str) -> bool:
        return key in self.value
    
    def __iter__(self):
        return iter(self.value)
    
    def keys(self):
        return self.value.keys()
    
    def values(self):
        return self.value.values()
    
    def items(self):
        return self.value.items()
    
    def get(self, key: str, default=None):
        return self.value.get(key, default)
    
    @classmethod
    def tag_type(cls) -> TagType:
        return TagType.COMPOUND
    
    def serialize(self) -> bytes:
        result = b''
        for key, tag in self.value.items():
            result += struct.pack('>B', tag.tag_type())
            key_bytes = key.encode('utf-8')
            result += struct.pack('>H', len(key_bytes)) + key_bytes
            result += tag.serialize()
        result += struct.pack('>B', TagType.END)
        return result
    
    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple['CompoundTag', int]:
        value = {}
        while True:
            if offset >= len(data):
                raise ValueError("Truncated CompoundTag payload")
            tag_type_id = struct.unpack_from('>B', data, offset)[0]
            offset += 1
            
            if tag_type_id == TagType.END:
                break

            if offset + 2 > len(data):
                raise ValueError("Truncated CompoundTag name length")
            name_length = struct.unpack_from('>H', data, offset)[0]
            offset += 2
            end = offset + name_length
            if end > len(data):
                raise ValueError("Truncated CompoundTag name payload")
            name = data[offset:end].decode('utf-8')
            offset = end

            if tag_type_id not in TAG_CLASSES:
                raise ValueError(f"Invalid CompoundTag child type id: {tag_type_id}")
            tag_class = TAG_CLASSES[tag_type_id]
            if tag_class is None:
                raise ValueError(f"Invalid CompoundTag child type id: {tag_type_id}")
            tag, offset = tag_class.deserialize(data, offset)
            value[name] = tag
        
        return cls(value), offset


class IntArrayTag(Tag):
    """Int array tag"""
    
    def __init__(self, value: List[int] = None):
        if value is None:
            value = []
        super().__init__(value)
    
    def __len__(self):
        return len(self.value)
    
    def __getitem__(self, key):
        return self.value[key]
    
    def __setitem__(self, key, value):
        self.value[key] = value
    
    def __iter__(self):
        return iter(self.value)
    
    @classmethod
    def tag_type(cls) -> TagType:
        return TagType.INT_ARRAY
    
    def serialize(self) -> bytes:
        length = len(self.value)
        result = struct.pack('>i', length)
        result += struct.pack(f'>{length}i', *self.value)
        return result
    
    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple['IntArrayTag', int]:
        if offset + 4 > len(data):
            raise ValueError("Truncated IntArrayTag length")
        length = struct.unpack_from('>i', data, offset)[0]
        offset += 4
        if length < 0:
            raise ValueError("Negative IntArrayTag length")
        if length == 0:
            return cls([]), offset
        bytes_needed = length * 4
        end = offset + bytes_needed
        if end > len(data):
            raise ValueError("Truncated IntArrayTag payload")
        value = list(struct.unpack_from(f'>{length}i', data, offset))
        return cls(value), end


class LongArrayTag(Tag):
    """Long array tag"""
    
    def __init__(self, value: List[int] = None):
        if value is None:
            value = []
        super().__init__(value)
    
    def __len__(self):
        return len(self.value)
    
    def __getitem__(self, key):
        return self.value[key]
    
    def __setitem__(self, key, value):
        self.value[key] = value
    
    def __iter__(self):
        return iter(self.value)
    
    @classmethod
    def tag_type(cls) -> TagType:
        return TagType.LONG_ARRAY
    
    def serialize(self) -> bytes:
        length = len(self.value)
        result = struct.pack('>i', length)
        result += struct.pack(f'>{length}q', *self.value)
        return result
    
    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple['LongArrayTag', int]:
        if offset + 4 > len(data):
            raise ValueError("Truncated LongArrayTag length")
        length = struct.unpack_from('>i', data, offset)[0]
        offset += 4
        if length < 0:
            raise ValueError("Negative LongArrayTag length")
        if length == 0:
            return cls([]), offset
        bytes_needed = length * 8
        end = offset + bytes_needed
        if end > len(data):
            raise ValueError("Truncated LongArrayTag payload")
        value = list(struct.unpack_from(f'>{length}q', data, offset))
        return cls(value), end


TAG_CLASSES = {
    TagType.END: None,
    TagType.BYTE: ByteTag,
    TagType.SHORT: ShortTag,
    TagType.INT: IntTag,
    TagType.LONG: LongTag,
    TagType.FLOAT: FloatTag,
    TagType.DOUBLE: DoubleTag,
    TagType.BYTE_ARRAY: ByteArrayTag,
    TagType.STRING: StringTag,
    TagType.LIST: ListTag,
    TagType.COMPOUND: CompoundTag,
    TagType.INT_ARRAY: IntArrayTag,
    TagType.LONG_ARRAY: LongArrayTag,
}


class NBTFile:
    """Represents an NBT file"""
    
    def __init__(self, root: Optional[CompoundTag] = None, name: str = ""):
        self.root = root if root is not None else CompoundTag()
        self.name = name
    
    @classmethod
    def load(cls, filepath: str, gzipped: bool = True) -> 'NBTFile':
        try:
            if gzipped:
                with gzip.open(filepath, 'rb') as f:
                    data = f.read()
            else:
                with open(filepath, 'rb') as f:
                    data = f.read()
            
            if not data:
                raise ValueError("File is empty")
            
            tag_type_id = struct.unpack_from('>B', data, 0)[0]
            if tag_type_id != TagType.COMPOUND:
                raise ValueError(f"Root tag must be Compound, got {tag_type_id}")
            
            offset = 1
            
            name_length = struct.unpack_from('>H', data, offset)[0]
            offset += 2
            name = data[offset:offset + name_length].decode('utf-8')
            offset += name_length
            
            root, _ = CompoundTag.deserialize(data, offset)
            
            return cls(root, name)
        except Exception as e:
            raise Exception(f"Failed to load NBT file: {str(e)}") from e
    
    def save(self, filepath: str, gzipped: bool = True):
        try:
            data = struct.pack('>B', TagType.COMPOUND)
            name_bytes = self.name.encode('utf-8')
            data += struct.pack('>H', len(name_bytes)) + name_bytes
            data += self.root.serialize()
            
            if gzipped:
                with gzip.open(filepath, 'wb') as f:
                    f.write(data)
            else:
                with open(filepath, 'wb') as f:
                    f.write(data)
        except Exception as e:
            raise Exception(f"Failed to save NBT file: {str(e)}") from e

