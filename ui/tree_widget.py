"""
NBT Tree Widget
Custom tree widget for displaying NBT file structure.
"""
import os
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt
from nbt.nbt import NBTFile, CompoundTag, ListTag, ByteArrayTag, IntArrayTag, LongArrayTag
from utils.type_icon import get_icon_for_tag


class NBTTreeWidget(QTreeWidget):
    """Custom tree widget for displaying NBT structure"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel("NBT Structure")
        self.itemSelectionChanged.connect(self.on_selection_changed)
        self.current_nbt_file = None
        self.on_tag_selected = None
        
        # Get the icon sheet path relative to the script location
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.icon_sheet_path = os.path.join(script_dir, "assets", "nbt_icon_sheet.png")
    
    def load_nbt(self, nbt_file: NBTFile):
        """Load NBT file into tree view"""
        self.clear()
        self.current_nbt_file = nbt_file
        
        if nbt_file.root is not None:
            root_item = self._create_tree_item("root", nbt_file.root)
            self.addTopLevelItem(root_item)
            root_item.setExpanded(True)
    
    def _create_tree_item(self, name: str, tag, parent_tag=None, parent_key=None) -> QTreeWidgetItem:
        """Recursively create tree items from NBT tags"""
        item = QTreeWidgetItem([name])
        item.setData(0, Qt.UserRole, tag)
        item.setData(1, Qt.UserRole, parent_tag)
        item.setData(2, Qt.UserRole, parent_key)
        
        tag_type = type(tag).__name__
        display_text = f"{name} ({tag_type})"
        
        if isinstance(tag, CompoundTag):
            display_text = f"{name} (Compound: {len(tag)} entries)"
            for key, value in tag.items():
                child = self._create_tree_item(key, value, parent_tag=tag, parent_key=key)
                item.addChild(child)
        elif isinstance(tag, ListTag):
            display_text = f"{name} (List: {len(tag)} items)"
            for i, value in enumerate(tag):
                child = self._create_tree_item(f"[{i}]", value, parent_tag=tag, parent_key=i)
                item.addChild(child)
        elif isinstance(tag, (ByteArrayTag, IntArrayTag, LongArrayTag)):
            display_text = f"{name} ({tag_type}: {len(tag)} elements)"
        else:
            display_text = f"{name} ({tag_type}): {str(tag)}"
        
        item.setText(0, display_text)
        
        # Set icon based on tag type
        icon = get_icon_for_tag(tag, self.icon_sheet_path)
        item.setIcon(0, icon)
        
        return item
    
    def on_selection_changed(self):
        """Handle tree item selection"""
        selected_items = self.selectedItems()
        if selected_items and self.on_tag_selected:
            item = selected_items[0]
            tag = item.data(0, Qt.UserRole)
            parent_tag = item.data(1, Qt.UserRole)
            parent_key = item.data(2, Qt.UserRole)
            tag_name = item.text(0).split(" (")[0]
            self.on_tag_selected(tag_name, tag, parent_tag, parent_key)

