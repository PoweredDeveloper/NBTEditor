from PyQt5.QtGui import QIcon, QPixmap

def get_icon_for_tag(tag, icon_sheet_path: str) -> QIcon:
    # Icon positions in the 4x4 grid (row, col) where each icon is 32x32
    icon_map = {
        'ByteTag': (0, 0),              # Byte
        'ShortTag': (1, 1),             # Short
        'IntTag': (0, 3),               # Integer
        'LongTag': (1, 0),              # Long
        'FloatTag': (0, 2),             # Float
        'DoubleTag': (0, 1),            # Double
        'ByteArrayTag': (2, 0),         # Byte Array
        'StringTag': (1, 2),            # String
        'ListTag': (2, 2),              # List/Collection
        'CompoundTag': (1, 3),          # Compound/Collection
        'IntArrayTag': (2, 1),          # Int Array
        'LongArrayTag': (3, 0),         # Long Array
    }
    
    tag_type_name = type(tag).__name__
    
    if tag_type_name not in icon_map:
        row, col = (0, 0)
    else:
        row, col = icon_map[tag_type_name]
    
    pixmap = QPixmap(icon_sheet_path)
    if pixmap.isNull():
        return QIcon()
    
    # Extract the 32x32 icon from the sprite sheet
    icon_size = 32
    x = col * icon_size
    y = row * icon_size
    icon_pixmap = pixmap.copy(x, y, icon_size, icon_size)
    
    return QIcon(icon_pixmap)