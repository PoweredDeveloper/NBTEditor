from PyQt5.QtGui import QIcon, QPixmap

def get_icon_for_tag(tag, type_icon_sheet_path: str) -> QIcon:
    # Icon positions in the 4x4 grid (row, col) where each icon is 128x128
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
    
    pixmap = QPixmap(type_icon_sheet_path)
    if pixmap.isNull():
        return QIcon()
    
    # Extract the 128x128 icon from the sprite sheet
    icon_size = 128
    x = col * icon_size
    y = row * icon_size
    icon_pixmap = pixmap.copy(x, y, icon_size, icon_size)
    
    return QIcon(icon_pixmap)

def get_icon_for_toolbar(toolbar_icon_name: str, toolbar_icon_sheet_path: str) -> QIcon:
    # Icon positions in the 4x4 grid (row, col) where each icon is 128x128
    icon_map = {
        'NewFile': (0, 0),     
        'OpenFile': (0, 1),    
        'SaveFile': (0, 2),    
        'SaveFileAs': (0, 3),  
    }
    
    if toolbar_icon_name not in icon_map:
        row, col = (0, 0)
    else:
        row, col = icon_map[toolbar_icon_name]
    
    pixmap = QPixmap(toolbar_icon_sheet_path)
    if pixmap.isNull():
        return QIcon()
    
    # Extract the 128x128 icon from the sprite sheet
    icon_size = 128
    x = col * icon_size
    y = row * icon_size
    icon_pixmap = pixmap.copy(x, y, icon_size, icon_size)
    
    return QIcon(icon_pixmap)