"""
Tag Action Controller
Unified controller for all tag operations with consistent UI handling and callbacks.
Separates UI concerns from logic.
"""
from typing import Optional, Callable, Tuple, Any
from PyQt5.QtWidgets import QWidget, QMessageBox, QInputDialog, QLineEdit, QDialog
from nbt.nbt import (
    CompoundTag, ListTag, ByteArrayTag, IntArrayTag, LongArrayTag, Tag, TagType
)
from utils.tag_helpers import can_delete_from_parent, can_add_to_tag
from utils.add_tag_dialog import AddTagDialog


class TagActionController:
    """
    Unified controller for tag operations.
    Handles UI interactions and delegates logic to pure functions.
    """
    
    def __init__(self, parent_widget: Optional[QWidget] = None):
        """
        Initialize the controller.
        """
        self.parent_widget = parent_widget
    
    def delete_tag(
        self,
        tag_name: str,
        parent_tag: Tag,
        parent_key: Any,
        on_success: Optional[Callable] = None,
        on_unselect: Optional[Callable] = None
    ) -> bool:
        """
        Delete a tag from its parent (Compound or List).
        """
        if not can_delete_from_parent(parent_tag):
            return False
        
        if parent_key is None:
            return False
        
        reply = QMessageBox.question(
            self.parent_widget,
            "Confirm Delete",
            f"Are you sure you want to delete '{tag_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return False
        
        try:
            if isinstance(parent_tag, CompoundTag):
                del parent_tag[parent_key]
            elif isinstance(parent_tag, ListTag):
                # For ListTag, parent_key is an index
                if isinstance(parent_key, int) and 0 <= parent_key < len(parent_tag):
                    del parent_tag.value[parent_key]
                else:
                    raise IndexError(f"Invalid list index: {parent_key}")
            else:
                return False
            
            if on_success:
                on_success()
            if on_unselect:
                on_unselect()
            
            return True
        except Exception as e:
            QMessageBox.warning(
                self.parent_widget,
                "Error",
                f"Failed to delete tag: {str(e)}"
            )
            return False
    
    def create_tag(
        self,
        parent_tag: Tag,
        on_success: Optional[Callable] = None
    ) -> Tuple[bool, Optional[str], Optional[Tag]]:
        """
        Create and add a new tag to a parent tag.
        """
        if parent_tag is None:
            return False, None, None
        
        if not can_add_to_tag(parent_tag):
            return False, None, None
        
        try:
            if isinstance(parent_tag, CompoundTag):
                return self._create_in_compound(parent_tag, on_success)
            elif isinstance(parent_tag, ListTag):
                return self._create_in_list(parent_tag, on_success)
            elif isinstance(parent_tag, ByteArrayTag):
                return self._create_in_byte_array(parent_tag, on_success)
            elif isinstance(parent_tag, IntArrayTag):
                return self._create_in_int_array(parent_tag, on_success)
            elif isinstance(parent_tag, LongArrayTag):
                return self._create_in_long_array(parent_tag, on_success)
            else:
                return False, None, None
        except Exception as e:
            QMessageBox.warning(
                self.parent_widget,
                "Error",
                f"Failed to add tag: {str(e)}"
            )
            return False, None, None
    
    def _create_in_compound(
        self,
        compound_tag: CompoundTag,
        on_success: Optional[Callable] = None
    ) -> Tuple[bool, Optional[str], Optional[Tag]]:
        """Add a key-value pair to a compound tag"""
        dialog = AddTagDialog(self.parent_widget, require_name=True)
        if dialog.exec_() == QDialog.Accepted:
            name, new_tag = dialog.get_result()
            if name in compound_tag:
                QMessageBox.warning(
                    self.parent_widget,
                    "Duplicate Key",
                    f"A tag with name '{name}' already exists."
                )
                return False, None, None
            compound_tag[name] = new_tag
            if on_success:
                on_success()
            return True, name, new_tag
        return False, None, None
    
    def _create_in_list(
        self,
        list_tag: ListTag,
        on_success: Optional[Callable] = None
    ) -> Tuple[bool, Optional[str], Optional[Tag]]:
        """Add an item to a list tag"""
        is_empty = (len(list_tag) == 0 or 
                   list_tag.list_tag_type is None or 
                   list_tag.list_tag_type == TagType.END)
        
        list_type = None
        if not is_empty:
            list_type = type(list_tag[0])
        
        dialog = AddTagDialog(self.parent_widget, require_name=False, list_type=list_type)
        if dialog.exec_() == QDialog.Accepted:
            _, new_tag = dialog.get_result()
            if list_type is not None and type(new_tag) != list_type:
                QMessageBox.warning(
                    self.parent_widget,
                    "Type Mismatch",
                    f"List expects {list_type.__name__}, but got {type(new_tag).__name__}."
                )
                return False, None, None
            
            if list_tag.list_tag_type == TagType.END:
                list_tag.list_tag_type = None
            
            list_tag.append(new_tag)
            if on_success:
                on_success()
            return True, None, new_tag
        return False, None, None
    
    def _create_in_byte_array(
        self,
        array_tag: ByteArrayTag,
        on_success: Optional[Callable] = None
    ) -> Tuple[bool, Optional[str], Optional[Tag]]:
        """Add an element to a byte array"""
        value, ok = QInputDialog.getInt(
            self.parent_widget,
            "Add Byte",
            "Enter byte value (0-255):",
            0, 0, 255, 1
        )
        if ok:
            array_tag.value.append(value & 0xFF)
            if on_success:
                on_success()
            return True, None, None
        return False, None, None
    
    def _create_in_int_array(
        self,
        array_tag: IntArrayTag,
        on_success: Optional[Callable] = None
    ) -> Tuple[bool, Optional[str], Optional[Tag]]:
        """Add an element to an int array"""
        value, ok = QInputDialog.getInt(
            self.parent_widget,
            "Add Integer",
            "Enter integer value:",
            0,
            -2147483648,
            2147483647,
            1
        )
        if ok:
            array_tag.value.append(value)
            if on_success:
                on_success()
            return True, None, None
        return False, None, None
    
    def _create_in_long_array(
        self,
        array_tag: LongArrayTag,
        on_success: Optional[Callable] = None
    ) -> Tuple[bool, Optional[str], Optional[Tag]]:
        """Add an element to a long array"""
        value, ok = QInputDialog.getInt(
            self.parent_widget,
            "Add Long",
            "Enter long value:",
            0,
            -9223372036854775808,
            9223372036854775807,
            1
        )
        if ok:
            array_tag.value.append(value)
            if on_success:
                on_success()
            return True, None, None
        return False, None, None
    
    def rename_tag(
        self,
        tag_name: str,
        parent_tag: CompoundTag,
        parent_key: Any,
        on_success: Optional[Callable] = None
    ) -> Tuple[bool, Optional[str]]:
        if not isinstance(parent_tag, CompoundTag):
            return False, None
        
        if parent_key is None:
            return False, None
        
        if parent_key not in parent_tag:
            return False, None
        
        new_name, ok = QInputDialog.getText(
            self.parent_widget,
            "Rename Tag",
            f"Enter new name for '{tag_name}':",
            echo=QLineEdit.Normal,
            text=tag_name
        )
        
        if not ok:
            return False, None
        
        new_name = new_name.strip()
        
        if not new_name:
            QMessageBox.warning(
                self.parent_widget,
                "Invalid Name",
                "Tag name cannot be empty."
            )
            return False, None
        
        if new_name == str(parent_key):
            return True, new_name
        
        if new_name in parent_tag:
            QMessageBox.warning(
                self.parent_widget,
                "Duplicate Key",
                f"A tag with name '{new_name}' already exists."
            )
            return False, None
        
        try:
            tag_value = parent_tag[parent_key]
            del parent_tag[parent_key]
            parent_tag[new_name] = tag_value
            
            if on_success:
                on_success()
            
            return True, new_name
        except Exception as e:
            QMessageBox.warning(
                self.parent_widget,
                "Error",
                f"Failed to rename tag: {str(e)}"
            )
            return False, None
    
    def move_tag(
        self,
        tag_name: str,
        source_parent: CompoundTag,
        source_key: Any,
        target_parent: CompoundTag,
        target_key: Optional[str] = None,
        on_success: Optional[Callable] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Move a tag from one parent to another (or reorder within same parent).
        
        Args:
            tag_name: Name of the tag to move
            source_parent: Current parent compound tag
            source_key: Current key in source parent
            target_parent: Target parent compound tag
            target_key: Target key (if None, uses source_key or prompts user)
            on_success: Callback called after successful move
            
        Returns:
            Tuple of (success, new_key)
        """
        if not isinstance(source_parent, CompoundTag):
            return False, None
        
        if not isinstance(target_parent, CompoundTag):
            return False, None
        
        if source_key is None or source_key not in source_parent:
            return False, None
        
        if source_parent is target_parent:
            if target_key is None or target_key == source_key:
                return True, source_key
            
            if target_key in target_parent:
                QMessageBox.warning(
                    self.parent_widget,
                    "Duplicate Key",
                    f"A tag with name '{target_key}' already exists."
                )
                return False, None
            
            try:
                tag_value = source_parent[source_key]
                del source_parent[source_key]
                target_parent[target_key] = tag_value
                if on_success:
                    on_success()
                return True, target_key
            except Exception as e:
                QMessageBox.warning(
                    self.parent_widget,
                    "Error",
                    f"Failed to move tag: {str(e)}"
                )
                return False, None
        
        if target_key is None:
            target_key, ok = QInputDialog.getText(
                self.parent_widget,
                "Move Tag",
                f"Enter new name for '{tag_name}' in target:",
                echo=QLineEdit.Normal,
                text=tag_name
            )
            if not ok:
                return False, None
            target_key = target_key.strip()
            if not target_key:
                QMessageBox.warning(
                    self.parent_widget,
                    "Invalid Name",
                    "Tag name cannot be empty."
                )
                return False, None
        
        if target_key in target_parent:
            QMessageBox.warning(
                self.parent_widget,
                "Duplicate Key",
                f"A tag with name '{target_key}' already exists in target."
            )
            return False, None
        
        try:
            tag_value = source_parent[source_key]
            del source_parent[source_key]
            target_parent[target_key] = tag_value
            if on_success:
                on_success()
            return True, target_key
        except Exception as e:
            QMessageBox.warning(
                self.parent_widget,
                "Error",
                f"Failed to move tag: {str(e)}"
            )
            return False, None

