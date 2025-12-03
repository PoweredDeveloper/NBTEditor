"""
Property Editor Widget
Widget for viewing and editing selected NBT tag properties.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox, QFormLayout,
    QTextEdit, QMessageBox, QDialog, QInputDialog
)
from nbt.nbt import CompoundTag
from utils.tag_helpers import (
    can_add_to_tag, can_edit_tag, can_delete_from_parent, is_array_tag
)
from utils.tag_value_editor import (
    update_tag_value, get_tag_display_value, get_tag_edit_value
)
from utils.add_tag_dialog import AddTagDialog


class PropertyEditor(QWidget):
    """Widget for editing selected NBT tag properties"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_tag = None
        self.current_name = None
        self.current_parent_tag = None
        self.current_parent_key = None
        self.on_value_changed = None
        self.on_tag_unselected = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout()
        
        # Tag info group
        info_group = QGroupBox("Tag Information")
        info_layout = QFormLayout()
        
        self.tag_name_label = QLabel("No tag selected")
        self.tag_type_label = QLabel("-")
        self.tag_value_label = QLabel("-")
        
        info_layout.addRow("Name:", self.tag_name_label)
        info_layout.addRow("Type:", self.tag_type_label)
        info_layout.addRow("Value:", self.tag_value_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Editor group
        self.editor_group = QGroupBox("Edit Value")
        self.editor_group.hide()
        editor_layout = QVBoxLayout()
        
        self.value_editor = QTextEdit()
        self.value_editor.setEnabled(False)
        self.value_editor.setMaximumHeight(150)
        self.value_editor.setPlaceholderText("Enter new value...")
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.setEnabled(False)
        self.apply_button.clicked.connect(self.apply_edit)
        
        editor_layout.addWidget(QLabel("New Value (comma-separated for arrays):"))
        editor_layout.addWidget(self.value_editor)
        editor_layout.addWidget(self.apply_button)
        
        self.editor_group.setLayout(editor_layout)
        layout.addWidget(self.editor_group)
        
        # Actions button group
        self.actions_group = QGroupBox("Actions")
        self.actions_group.hide()
        actions_layout = QVBoxLayout()
        
        self.add_button = QPushButton("Add Tag")
        self.add_button.setEnabled(False)
        self.add_button.clicked.connect(self.add_tag)
        actions_layout.addWidget(self.add_button)
        
        self.delete_button = QPushButton("Delete This Tag")
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self.delete_tag)
        actions_layout.addWidget(self.delete_button)
        
        self.actions_group.setLayout(actions_layout)
        layout.addWidget(self.actions_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def set_tag(self, name: str, tag, parent_tag=None, parent_key=None):
        """Set the currently selected tag for editing"""
        self.current_tag = tag
        self.current_name = name
        self.current_parent_tag = parent_tag
        self.current_parent_key = parent_key
        
        if tag is None:
            self._clear_editor()
            return
        
        self._populate_editor(tag, name, parent_tag)
    
    def _clear_editor(self):
        """Clear the editor when no tag is selected"""
        self.tag_name_label.setText("No tag selected")
        self.tag_type_label.setText("-")
        self.tag_value_label.setText("-")
        self.value_editor.setEnabled(False)
        self.apply_button.setEnabled(False)
        self.add_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.editor_group.hide()
        self.actions_group.hide()
    
    def _populate_editor(self, tag, name: str, parent_tag):
        """Populate editor with tag information"""
        from utils.tag_helpers import get_tag_type_name
        
        self.editor_group.show()
        self.actions_group.show()
        
        self.tag_name_label.setText(name)
        self.tag_type_label.setText(get_tag_type_name(tag))
        self.tag_value_label.setText(get_tag_display_value(tag))
        
        # Configure editor based on tag type
        if can_edit_tag(tag):
            self.value_editor.setEnabled(True)
            self.apply_button.setEnabled(True)
            self.value_editor.setPlainText(get_tag_edit_value(tag))
            # Set height based on tag type
            if is_array_tag(tag):
                self.value_editor.setMaximumHeight(150)
            else:
                self.value_editor.setMaximumHeight(50)
        else:
            self.value_editor.setEnabled(False)
            self.apply_button.setEnabled(False)
            self.value_editor.setPlainText("")
        
        # Enable buttons based on tag capabilities
        self.add_button.setEnabled(can_add_to_tag(tag))
        self.delete_button.setEnabled(can_delete_from_parent(parent_tag))
    
    def apply_edit(self):
        """Apply the edited value to the tag"""
        if self.current_tag is None:
            return
        
        try:
            new_value = self.value_editor.toPlainText().strip()
            update_tag_value(self.current_tag, new_value)
            
            # Update display
            self.tag_value_label.setText(get_tag_display_value(self.current_tag))
            
            if self.on_value_changed:
                self.on_value_changed()
                
        except ValueError as e:
            QMessageBox.warning(
                self, 
                "Invalid Value", 
                f"Could not set value: {str(e)}\n\nFor arrays, use comma-separated values (e.g., 1, 2, 3)"
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to update value: {str(e)}")
    
    def delete_tag(self):
        """Delete the current tag from its parent compound"""
        if not can_delete_from_parent(self.current_parent_tag):
            return
        
        if self.current_parent_key is None:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{self.current_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                del self.current_parent_tag[self.current_parent_key]
                if self.on_value_changed:
                    self.on_value_changed()
                if self.on_tag_unselected:
                    self.on_tag_unselected()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete tag: {str(e)}")
    
    def add_tag(self):
        """Add a new tag to the current tag (compound, list, or array)"""
        if self.current_tag is None:
            return
        
        try:
            from nbt.nbt import ListTag, ByteArrayTag, IntArrayTag, LongArrayTag
            
            if isinstance(self.current_tag, CompoundTag):
                self._add_to_compound()
            elif isinstance(self.current_tag, ListTag):
                self._add_to_list()
            elif isinstance(self.current_tag, ByteArrayTag):
                self._add_to_byte_array()
            elif isinstance(self.current_tag, IntArrayTag):
                self._add_to_int_array()
            elif isinstance(self.current_tag, LongArrayTag):
                self._add_to_long_array()
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to add tag: {str(e)}")
    
    def _add_to_compound(self):
        """Add a key-value pair to a compound tag"""
        dialog = AddTagDialog(self, require_name=True)
        if dialog.exec_() == QDialog.Accepted:
            name, new_tag = dialog.get_result()
            if name in self.current_tag:
                QMessageBox.warning(self, "Duplicate Key", f"A tag with name '{name}' already exists.")
                return
            self.current_tag[name] = new_tag
            if self.on_value_changed:
                self.on_value_changed()
    
    def _add_to_list(self):
        """Add an item to a list tag"""
        from nbt.nbt import ListTag
        list_type = None
        if len(self.current_tag) > 0:
            list_type = type(self.current_tag[0])
        
        dialog = AddTagDialog(self, require_name=False, list_type=list_type)
        if dialog.exec_() == QDialog.Accepted:
            _, new_tag = dialog.get_result()
            if list_type is not None and type(new_tag) != list_type:
                QMessageBox.warning(
                    self,
                    "Type Mismatch",
                    f"List expects {list_type.__name__}, but got {type(new_tag).__name__}."
                )
                return
            self.current_tag.append(new_tag)
            if self.on_value_changed:
                self.on_value_changed()
    
    def _add_to_byte_array(self):
        """Add an element to a byte array"""
        value, ok = QInputDialog.getInt(self, "Add Byte", "Enter byte value (0-255):", 0, 0, 255, 1)
        if ok:
            self.current_tag.value.append(value & 0xFF)
            if self.on_value_changed:
                self.on_value_changed()
    
    def _add_to_int_array(self):
        """Add an element to an int array"""
        value, ok = QInputDialog.getInt(
            self, "Add Integer", "Enter integer value:", 0, -2147483648, 2147483647, 1
        )
        if ok:
            self.current_tag.value.append(value)
            if self.on_value_changed:
                self.on_value_changed()
    
    def _add_to_long_array(self):
        """Add an element to a long array"""
        value, ok = QInputDialog.getInt(
            self, "Add Long", "Enter long value:", 0, -9223372036854775808, 9223372036854775807, 1
        )
        if ok:
            self.current_tag.value.append(value)
            if self.on_value_changed:
                self.on_value_changed()

