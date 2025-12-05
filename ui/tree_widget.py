"""
NBT Tree Widget
Custom tree widget for displaying NBT file structure.
"""
import os
from typing import Optional, Callable, Set, Tuple, Any
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu
from PyQt5.QtCore import Qt
from nbt.nbt import NBTFile, CompoundTag, ListTag, ByteArrayTag, IntArrayTag, LongArrayTag, Tag
from utils.type_icon import get_icon_for_tag
from utils.tag_action_controller import TagActionController
from utils.tag_helpers import can_add_to_tag, can_delete_from_parent


class NBTTreeWidget(QTreeWidget):
    """Custom tree widget for displaying NBT structure"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel("NBT Structure")
        self.itemSelectionChanged.connect(self.on_selection_changed)
        self.current_nbt_file = None
        self.on_tag_selected = None
        self.on_value_changed = None
        self.action_controller = TagActionController(self)
        
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.icon_sheet_path = os.path.join(script_dir, "assets", "nbt_icon_sheet_scaled.png")
    
    def _get_expanded_state(self) -> Set[Tuple[int, Any]]:
        """
        Get the set of expanded tag paths.
        """
        expanded = set()
        
        def collect_expanded(item, path=()):
            if item.isExpanded():
                tag = item.data(0, Qt.UserRole)
                parent_tag = item.data(1, Qt.UserRole)
                parent_key = item.data(2, Qt.UserRole)
                if tag is not None:
                    expanded.add((id(parent_tag), parent_key))
            
            for i in range(item.childCount()):
                child = item.child(i)
                child_parent_tag = child.data(1, Qt.UserRole)
                child_parent_key = child.data(2, Qt.UserRole)
                child_path = (id(child_parent_tag), child_parent_key)
                collect_expanded(child, child_path)
        
        root = self.topLevelItem(0)
        if root:
            collect_expanded(root)
        
        return expanded
    
    def _restore_expanded_state(self, expanded_state: Set[Tuple[int, Any]]) -> None:
        """
        Restore expanded state based on tag paths.
        """
        def restore_item(item):
            parent_tag = item.data(1, Qt.UserRole)
            parent_key = item.data(2, Qt.UserRole)
            if parent_tag is not None:
                state_key = (id(parent_tag), parent_key)
                if state_key in expanded_state:
                    item.setExpanded(True)
            
            for i in range(item.childCount()):
                restore_item(item.child(i))
        
        root = self.topLevelItem(0)
        if root:
            restore_item(root)
    
    def load_nbt(self, nbt_file: NBTFile, preserve_state: bool = False):
        """
        Load NBT file into tree view.
        """
        expanded_state = None
        if preserve_state:
            expanded_state = self._get_expanded_state()
        
        self.clear()
        self.current_nbt_file = nbt_file
        
        if nbt_file.root is not None:
            root_item = self._create_tree_item("root", nbt_file.root)
            self.addTopLevelItem(root_item)
            root_item.setExpanded(True)
            
            if preserve_state and expanded_state:
                self._restore_expanded_state(expanded_state)
    
    def refresh_tree(self):
        """
        Refresh the tree while preserving expanded state and selection.
        This should be called instead of load_nbt() when updating after operations.
        """
        if self.current_nbt_file is None:
            return
        
        selected_items = self.selectedItems()
        selected_tag = None
        if selected_items:
            item = selected_items[0]
            selected_tag = item.data(0, Qt.UserRole)
        
        self.load_nbt(self.current_nbt_file, preserve_state=True)
        
        if selected_tag is not None:
            self._select_tag_in_tree(selected_tag)
    
    def _create_tree_item(
        self,
        name: str,
        tag: Tag,
        parent_tag: Optional[Tag] = None,
        parent_key: Any = None
    ) -> QTreeWidgetItem:
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
        
        icon = get_icon_for_tag(tag, self.icon_sheet_path)
        item.setIcon(0, icon)
        
        return item
    
    def _extract_item_data(self, item: QTreeWidgetItem) -> Tuple[Tag, Optional[Tag], Any, str]:
        """
        Extract tag data from a tree item.
        """
        tag = item.data(0, Qt.UserRole)
        parent_tag = item.data(1, Qt.UserRole)
        parent_key = item.data(2, Qt.UserRole)
        tag_name = item.text(0).split(" (")[0]
        return tag, parent_tag, parent_key, str(tag_name)
    
    def on_selection_changed(self):
        """Handle tree item selection"""
        selected_items = self.selectedItems()
        if selected_items and self.on_tag_selected:
            item = selected_items[0]
            tag, parent_tag, parent_key, tag_name = self._extract_item_data(item)
            self.on_tag_selected(tag_name, tag, parent_tag, parent_key)
    
    def contextMenuEvent(self, event):
        """Handle right-click context menu"""
        item = self.itemAt(event.pos())
        if item is None:
            return
        
        tag, parent_tag, parent_key, tag_name = self._extract_item_data(item)
        
        menu = QMenu(self)
        
        if tag is not None and can_add_to_tag(tag):
            create_action = menu.addAction("Create Tag")
            create_action.triggered.connect(lambda: self._handle_create_tag(tag))
        
        if parent_tag is not None and can_delete_from_parent(parent_tag):
            delete_action = menu.addAction("Delete Tag")
            delete_action.triggered.connect(lambda: self._handle_delete_tag(tag_name, parent_tag, parent_key))
        
        if parent_tag is not None and isinstance(parent_tag, CompoundTag) and parent_key is not None:
            rename_action = menu.addAction("Rename Tag")
            rename_action.triggered.connect(lambda: self._handle_rename_tag(tag_name, parent_tag, parent_key))
        
        if not menu.isEmpty():
            menu.exec_(event.globalPos())
    
    def _handle_create_tag(self, parent_tag: Tag) -> None:
        """Handle create tag from context menu"""
        def refresh_callback():
            if self.on_value_changed:
                self.on_value_changed()
            self._select_tag_in_tree(parent_tag)
        
        self.action_controller.create_tag(
            parent_tag,
            on_success=refresh_callback
        )
    
    def _handle_delete_tag(
        self,
        tag_name: str,
        parent_tag: Tag,
        parent_key: Any
    ) -> None:
        """Handle delete tag from context menu"""
        def refresh_callback():
            if self.on_value_changed:
                self.on_value_changed()
            self.clearSelection()
        
        self.action_controller.delete_tag(
            tag_name,
            parent_tag,
            parent_key,
            on_success=refresh_callback,
            on_unselect=lambda: self.clearSelection()
        )
    
    def _handle_rename_tag(
        self,
        tag_name: str,
        parent_tag: CompoundTag,
        parent_key: Any
    ) -> None:
        """Handle rename tag from context menu"""
        tag_value = parent_tag[parent_key] if parent_key in parent_tag else None
        
        def refresh_callback():
            if self.on_value_changed:
                self.on_value_changed()
            if tag_value is not None:
                self._select_tag_in_tree(tag_value)
        
        self.action_controller.rename_tag(
            tag_name,
            parent_tag,
            parent_key,
            on_success=refresh_callback
        )
    
    def _select_tag_in_tree(self, target_tag: Tag) -> None:
        """Helper to find and select a tag in the tree"""
        def find_item(parent_item):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                child_tag = child.data(0, Qt.UserRole)
                if child_tag is target_tag:
                    return child
                found = find_item(child)
                if found:
                    return found
            return None
        
        root = self.topLevelItem(0)
        if root:
            found = find_item(root)
            if found:
                self.setCurrentItem(found)
                self.on_selection_changed()

