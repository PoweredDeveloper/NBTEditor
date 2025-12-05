"""
Property Editor Widget
Widget for viewing and editing selected NBT tag properties.
"""
from typing import Optional, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox, QFormLayout,
    QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt
from nbt.nbt import CompoundTag, Tag
from utils.tag_helpers import (
    can_add_to_tag, can_edit_tag, can_delete_from_parent, is_array_tag
)
from utils.tag_value_editor import (
    update_tag_value, get_tag_display_value, get_tag_edit_value
)
from utils.tag_action_controller import TagActionController


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
        self.action_controller = TagActionController(self)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout()
        
        info_group = QGroupBox("Tag Information")
        info_layout = QFormLayout()
        info_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.tag_name_label = QLabel("No tag selected")
        self.tag_type_label = QLabel("-")
        self.tag_value_label = QLabel("-")
        
        info_layout.addRow("Name:", self.tag_name_label)
        info_layout.addRow("Type:", self.tag_type_label)
        info_layout.addRow("Value:", self.tag_value_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
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
        
        self.rename_button = QPushButton("Rename Tag")
        self.rename_button.setEnabled(False)
        self.rename_button.clicked.connect(self.rename_tag)
        actions_layout.addWidget(self.rename_button)
        
        self.actions_group.setLayout(actions_layout)
        layout.addWidget(self.actions_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def set_tag(
        self,
        name: str,
        tag: Optional[Tag],
        parent_tag: Optional[Tag] = None,
        parent_key: Any = None
    ) -> None:
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
        self.rename_button.setEnabled(False)
        self.editor_group.hide()
        self.actions_group.hide()
    
    def _populate_editor(
        self,
        tag: Tag,
        name: str,
        parent_tag: Optional[Tag]
    ) -> None:
        """Populate editor with tag information"""
        from utils.tag_helpers import get_tag_type_name
        
        self.editor_group.show()
        self.actions_group.show()
        
        self.tag_name_label.setText(name)
        self.tag_type_label.setText(get_tag_type_name(tag))
        self.tag_value_label.setText(get_tag_display_value(tag))
        
        if can_edit_tag(tag):
            self.value_editor.setEnabled(True)
            self.apply_button.setEnabled(True)
            self.value_editor.setPlainText(get_tag_edit_value(tag))
            if is_array_tag(tag):
                self.value_editor.setMaximumHeight(150)
            else:
                self.value_editor.setMaximumHeight(50)
        else:
            self.value_editor.setEnabled(False)
            self.apply_button.setEnabled(False)
            self.value_editor.setPlainText("")
        
        self.add_button.setEnabled(can_add_to_tag(tag))
        self.delete_button.setEnabled(can_delete_from_parent(parent_tag))
        self.rename_button.setEnabled(isinstance(parent_tag, CompoundTag) and self.current_parent_key is not None)
    
    def apply_edit(self):
        """Apply the edited value to the tag"""
        if self.current_tag is None:
            return
        
        try:
            new_value = self.value_editor.toPlainText().strip()
            update_tag_value(self.current_tag, new_value)
            
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
        self.action_controller.delete_tag(
            self.current_name,
            self.current_parent_tag,
            self.current_parent_key,
            on_success=self.on_value_changed,
            on_unselect=self.on_tag_unselected
        )
    
    def add_tag(self):
        """Add a new tag to the current tag (compound, list, or array)"""
        if self.current_tag is None:
            return
        
        self.action_controller.create_tag(
            self.current_tag,
            on_success=self.on_value_changed
        )
    
    def rename_tag(self):
        """Rename the current tag in its parent compound"""
        self.action_controller.rename_tag(
            self.current_name,
            self.current_parent_tag,
            self.current_parent_key,
            on_success=self.on_value_changed
        )

