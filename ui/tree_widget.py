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
    
    def _get_tag_name_from_item(self, item: QTreeWidgetItem) -> str:
        # item text looks like: "<name> (<TagType...>)" so the name is before " ("
        return item.text(0).split(" (")[0]

    def _get_item_path(self, item: QTreeWidgetItem) -> Tuple[str, ...]:
        """
        Build a stable path for a tree item based on displayed tag keys.
        This avoids identity comparison because the NBT tag objects are recreated on refresh.
        """
        parts = []
        current = item
        while current is not None:
            parts.append(self._get_tag_name_from_item(current))
            current = current.parent()
        return tuple(reversed(parts))

    def _select_item_by_path(self, path: Tuple[str, ...]) -> None:
        """Select an item by its stable path (best-effort)."""
        if not path:
            return

        root = self.topLevelItem(0)
        if not root:
            return
        if self._get_tag_name_from_item(root) != path[0]:
            return

        current_item = root
        for name in path[1:]:
            found = None
            for i in range(current_item.childCount()):
                child = current_item.child(i)
                if self._get_tag_name_from_item(child) == name:
                    found = child
                    break
            if found is None:
                return
            current_item = found

        self.setCurrentItem(current_item)
        self.on_selection_changed()

    def _get_expanded_state(self) -> Set[Tuple[str, ...]]:
        """
        Get the set of expanded tag paths.
        """
        expanded = set()

        def collect_expanded(item: QTreeWidgetItem, path_prefix: Tuple[str, ...]) -> None:
            name = self._get_tag_name_from_item(item)
            path = path_prefix + (name,)
            if item.isExpanded():
                expanded.add(path)
            for i in range(item.childCount()):
                collect_expanded(item.child(i), path)

        root = self.topLevelItem(0)
        if root:
            collect_expanded(root, ())

        return expanded
    
    def _restore_expanded_state(self, expanded_state: Set[Tuple[str, ...]]) -> None:
        """
        Restore expanded state based on tag paths.
        """
        def restore_item(item: QTreeWidgetItem, path_prefix: Tuple[str, ...]) -> None:
            name = self._get_tag_name_from_item(item)
            path = path_prefix + (name,)
            item.setExpanded(path in expanded_state)
            for i in range(item.childCount()):
                restore_item(item.child(i), path)

        root = self.topLevelItem(0)
        if root:
            restore_item(root, ())
    
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
        selected_path = None
        if selected_items:
            selected_path = self._get_item_path(selected_items[0])

        self.load_nbt(self.current_nbt_file, preserve_state=True)

        if selected_path is not None:
            self._select_item_by_path(selected_path)
    
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
        item_path = self._get_item_path(item)
        
        menu = QMenu(self)
        
        if tag is not None and can_add_to_tag(tag):
            create_action = menu.addAction("Create Tag")
            create_action.triggered.connect(lambda: self._handle_create_tag(tag, item_path))
        
        if parent_tag is not None and can_delete_from_parent(parent_tag):
            delete_action = menu.addAction("Delete Tag")
            delete_action.triggered.connect(lambda: self._handle_delete_tag(tag_name, parent_tag, parent_key))
        
        if parent_tag is not None and isinstance(parent_tag, CompoundTag) and parent_key is not None:
            rename_action = menu.addAction("Rename Tag")
            rename_action.triggered.connect(lambda: self._handle_rename_tag(item_path, tag_name, parent_tag, parent_key))
        
        if not menu.isEmpty():
            menu.exec_(event.globalPos())
    
    def _handle_create_tag(self, parent_tag: Tag, parent_path: Tuple[str, ...]) -> None:
        """Handle create tag from context menu"""
        # Ensure the clicked node is the selection before we refresh.
        self._select_item_by_path(parent_path)

        success, _name, _new_tag = self.action_controller.create_tag(parent_tag, on_success=None)
        if success and self.on_value_changed:
            self.on_value_changed()
            self._select_item_by_path(parent_path)
    
    def _handle_delete_tag(
        self,
        tag_name: str,
        parent_tag: Tag,
        parent_key: Any
    ) -> None:
        """Handle delete tag from context menu"""
        success = self.action_controller.delete_tag(
            tag_name,
            parent_tag,
            parent_key,
            on_success=None,
            on_unselect=None,
        )
        if success and self.on_value_changed:
            self.on_value_changed()
        self.clearSelection()
    
    def _handle_rename_tag(
        self,
        old_item_path: Tuple[str, ...],
        tag_name: str,
        parent_tag: CompoundTag,
        parent_key: Any
    ) -> None:
        """Handle rename tag from context menu"""
        success, new_name = self.action_controller.rename_tag(
            tag_name,
            parent_tag,
            parent_key,
            on_success=None
        )
        if success and new_name and self.on_value_changed:
            # Refresh tree first, then select using updated path (the key changed).
            self.on_value_changed()
            new_path = old_item_path[:-1] + (new_name,)
            self._select_item_by_path(new_path)
    
    # NOTE: identity-based selection was intentionally removed.
    # Selection is restored via stable tag paths to survive tree refreshes.

