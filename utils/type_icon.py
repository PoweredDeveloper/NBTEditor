import os
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QMessageBox


_missing_icon_sheet_warned = False


def _warn_once_missing_icon_sheet(icon_sheet_path: str) -> None:
    global _missing_icon_sheet_warned
    if _missing_icon_sheet_warned:
        return
    _missing_icon_sheet_warned = True

    if not os.path.exists(icon_sheet_path):
        detail = f"Icon sheet not found: {icon_sheet_path}"
    else:
        detail = f"Failed to load icon sheet: {icon_sheet_path}"

    QMessageBox.warning(
        None,
        "Missing Icons",
        "The icon sprite sheet could not be loaded; toolbar/tree icons may be missing.\n\n"
        + detail,
    )

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
        _warn_once_missing_icon_sheet(type_icon_sheet_path)
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
        'AddTag': (1, 0),
        'DeleteTag': (1, 1),
        'RenameTag': (1, 2),
    }
    
    if toolbar_icon_name not in icon_map:
        row, col = (0, 0)
    else:
        row, col = icon_map[toolbar_icon_name]
    
    pixmap = QPixmap(toolbar_icon_sheet_path)
    if pixmap.isNull():
        _warn_once_missing_icon_sheet(toolbar_icon_sheet_path)
        return QIcon()
    
    # Extract the 128x128 icon from the sprite sheet
    icon_size = 128
    x = col * icon_size
    y = row * icon_size
    icon_pixmap = pixmap.copy(x, y, icon_size, icon_size)
    
    return QIcon(icon_pixmap)