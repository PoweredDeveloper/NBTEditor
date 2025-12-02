"""
NBT Editor - Main Application
A simple GUI application for editing Minecraft NBT files.
"""
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QLabel, QPushButton,
    QToolBar, QStatusBar, QFileDialog, QMessageBox,
    QGroupBox, QFormLayout, QTextEdit
)
from PyQt5.QtCore import Qt
from nbt import (
    NBTFile, CompoundTag,
    IntTag, FloatTag, StringTag, ByteTag, ShortTag, LongTag, DoubleTag,
    ByteArrayTag, IntArrayTag, LongArrayTag, ListTag
)
from nbt_handler import load_nbt_file, save_nbt_file, validate_nbt_file


def get_minecraft_folder() -> str:
    """
    Get the Minecraft folder path based on the operating system.
    """
    if sys.platform.startswith('win'):
        # Windows: %APPDATA%\.minecraft
        appdata = os.getenv('APPDATA')
        if appdata:
            minecraft_path = os.path.join(appdata, '.minecraft')
            if os.path.exists(minecraft_path):
                return minecraft_path
        return os.path.expanduser('~')
    elif sys.platform.startswith('darwin'):
        # macOS: ~/Library/Application Support/minecraft
        minecraft_path = os.path.expanduser('~/Library/Application Support/minecraft')
        if os.path.exists(minecraft_path):
            return minecraft_path
        return os.path.expanduser('~')
    else:
        # Linux and other Unix-like systems: ~/.minecraft
        minecraft_path = os.path.expanduser('~/.minecraft')
        if os.path.exists(minecraft_path):
            return minecraft_path
        return os.path.expanduser('~')


class NBTTreeWidget(QTreeWidget):
    """Custom tree widget for displaying NBT structure"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel("NBT Structure")
        self.itemSelectionChanged.connect(self.on_selection_changed)
        self.current_nbt_file = None
        self.on_tag_selected = None
    
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
        item.setData(1, Qt.UserRole, parent_tag)  # Store parent tag
        item.setData(2, Qt.UserRole, parent_key)  # Store key name in parent
        
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


class PropertyEditor(QWidget):
    """Widget for editing selected NBT tag properties"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_tag = None
        self.current_name = None
        self.current_parent_tag = None
        self.current_parent_key = None
        self.on_value_changed = None
        self.on_delete_requested = None
        
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
        
        # Delete button group
        self.delete_group = QGroupBox("Actions")
        self.delete_group.hide()
        delete_layout = QVBoxLayout()
        
        self.delete_button = QPushButton("Delete This Tag")
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self.delete_tag)
        self.delete_button.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; }")
        
        delete_layout.addWidget(self.delete_button)
        self.delete_group.setLayout(delete_layout)
        layout.addWidget(self.delete_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def set_tag(self, name: str, tag, parent_tag=None, parent_key=None):
        """Set the currently selected tag for editing"""
        self.current_tag = tag
        self.current_name = name
        self.current_parent_tag = parent_tag
        self.current_parent_key = parent_key
        
        if tag is None:
            self.tag_name_label.setText("No tag selected")
            self.tag_type_label.setText("-")
            self.tag_value_label.setText("-")
            self.value_editor.setEnabled(False)
            self.apply_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.editor_group.hide()
            self.delete_group.hide()
            return
        
        self.editor_group.show()
        self.delete_group.show()
        
        tag_type = type(tag).__name__
        tag_value = str(tag)
        
        self.tag_name_label.setText(name)
        self.tag_type_label.setText(tag_type)
        
        # For arrays, show formatted display
        if isinstance(tag, (ByteArrayTag, IntArrayTag, LongArrayTag)):
            if len(tag) > 0:
                tag_value = ", ".join(map(str, tag.value))
            else:
                tag_value = "(empty)"
        elif isinstance(tag, ListTag):
            tag_value = f"List with {len(tag)} items"
        elif isinstance(tag, CompoundTag):
            tag_value = f"Compound with {len(tag)} entries"
        else:
            tag_value = str(tag.value)
        
        self.tag_value_label.setText(tag_value)
        
        # Enable editing for primitive types and arrays
        if isinstance(tag, (IntTag, FloatTag, StringTag, ByteTag, ShortTag, LongTag, DoubleTag)):
            self.value_editor.setEnabled(True)
            self.apply_button.setEnabled(True)
            self.value_editor.setPlainText(str(tag.value))
            self.value_editor.setMaximumHeight(50)
        elif isinstance(tag, (ByteArrayTag, IntArrayTag, LongArrayTag)):
            self.value_editor.setEnabled(True)
            self.apply_button.setEnabled(True)
            if len(tag) > 0:
                self.value_editor.setPlainText(", ".join(map(str, tag.value)))
            else:
                self.value_editor.setPlainText("")
            self.value_editor.setMaximumHeight(150)
        else:
            self.value_editor.setEnabled(False)
            self.apply_button.setEnabled(False)
            self.value_editor.setPlainText("")
        
        # Enable delete button if tag has a parent (can be deleted from compound)
        self.delete_button.setEnabled(parent_tag is not None and isinstance(parent_tag, CompoundTag))
    
    def apply_edit(self):
        """Apply the edited value to the tag"""
        if self.current_tag is None:
            return
        
        try:
            new_value = self.value_editor.toPlainText().strip()
            
            if isinstance(self.current_tag, IntTag):
                self.current_tag.value = int(new_value)
            elif isinstance(self.current_tag, FloatTag):
                self.current_tag.value = float(new_value)
            elif isinstance(self.current_tag, StringTag):
                self.current_tag.value = new_value
            elif isinstance(self.current_tag, ByteTag):
                self.current_tag.value = int(new_value) & 0xFF
            elif isinstance(self.current_tag, ShortTag):
                self.current_tag.value = int(new_value) & 0xFFFF
            elif isinstance(self.current_tag, LongTag):
                self.current_tag.value = int(new_value)
            elif isinstance(self.current_tag, DoubleTag):
                self.current_tag.value = float(new_value)
            elif isinstance(self.current_tag, ByteArrayTag):
                # Parse comma-separated values
                if new_value:
                    values = [int(x.strip()) & 0xFF for x in new_value.split(",")]
                    self.current_tag.value = values
                else:
                    self.current_tag.value = []
            elif isinstance(self.current_tag, IntArrayTag):
                # Parse comma-separated values
                if new_value:
                    values = [int(x.strip()) for x in new_value.split(",")]
                    self.current_tag.value = values
                else:
                    self.current_tag.value = []
            elif isinstance(self.current_tag, LongArrayTag):
                # Parse comma-separated values
                if new_value:
                    values = [int(x.strip()) for x in new_value.split(",")]
                    self.current_tag.value = values
                else:
                    self.current_tag.value = []
            
            # Update display
            if isinstance(self.current_tag, (ByteArrayTag, IntArrayTag, LongArrayTag)):
                if len(self.current_tag) > 0:
                    display_value = ", ".join(map(str, self.current_tag.value))
                else:
                    display_value = "(empty)"
                self.tag_value_label.setText(display_value)
            else:
                self.tag_value_label.setText(str(self.current_tag.value))
            
            if self.on_value_changed:
                self.on_value_changed()
                
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Value", f"Could not set value: {str(e)}\n\nFor arrays, use comma-separated values (e.g., 1, 2, 3)")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to update value: {str(e)}")
    
    def delete_tag(self):
        """Delete the current tag from its parent compound"""
        if self.current_parent_tag is None or not isinstance(self.current_parent_tag, CompoundTag):
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
                QMessageBox.information(self, "Success", f"Tag '{self.current_name}' deleted successfully.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete tag: {str(e)}")


class NBTEditorMainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.current_file_path = None
        self.current_nbt_file = None
        self.setWindowTitle("NBT Editor")
        self.setGeometry(100, 100, 1000, 700)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        
        self.tree_widget = NBTTreeWidget()
        self.tree_widget.on_tag_selected = self.on_tag_selected
        main_layout.addWidget(self.tree_widget, 1)
        
        self.property_editor = PropertyEditor()
        self.property_editor.on_value_changed = self.on_value_changed
        main_layout.addWidget(self.property_editor, 1)
        
        central_widget.setLayout(main_layout)
        
        self.create_menu_bar()
        
        self.create_toolbar()
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("File")
        
        open_action = file_menu.addAction("Open...")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        
        save_action = file_menu.addAction("Save")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        
        save_as_action = file_menu.addAction("Save As...")
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_file_as)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
    
    def create_toolbar(self):
        """Create the toolbar"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.open_file)
        toolbar.addWidget(open_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_file)
        toolbar.addWidget(save_btn)
    
    def open_file(self):
        """Open an NBT file"""
        default_dir = get_minecraft_folder()
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open NBT File",
            default_dir,
            "NBT Files (*.dat *.nbt);;All Files (*)"
        )
        
        if filepath:
            try:
                nbt_file = load_nbt_file(filepath)
                self.current_nbt_file = nbt_file
                self.current_file_path = filepath
                self.tree_widget.load_nbt(nbt_file)
                self.status_bar.showMessage(f"Opened: {os.path.basename(filepath)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file:\n{str(e)}")
    
    def save_file(self):
        """Save the current NBT file"""
        if self.current_nbt_file is None:
            QMessageBox.warning(self, "No File", "No file is currently open.")
            return
        
        if self.current_file_path is None:
            self.save_file_as()
            return
        
        try:
            save_nbt_file(self.current_nbt_file, self.current_file_path)
            
            is_valid, issues = validate_nbt_file(self.current_nbt_file, self.current_file_path)
            
            if is_valid and len(issues) == 0:
                self.status_bar.showMessage(f"Saved: {os.path.basename(self.current_file_path)} (Valid)")
                QMessageBox.information(self, "Success", "File saved successfully and validated.")
            elif is_valid:
                self.status_bar.showMessage(f"Saved: {os.path.basename(self.current_file_path)} (Warnings: {len(issues)})")
                msg = "File saved successfully with warnings:\n\n" + "\n".join(issues)
                QMessageBox.warning(self, "Saved with Warnings", msg)
            else:
                self.status_bar.showMessage(f"Saved: {os.path.basename(self.current_file_path)} (Validation failed)")
                msg = "File saved but validation failed:\n\n" + "\n".join(issues)
                QMessageBox.critical(self, "Validation Failed", msg)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")
    
    def save_file_as(self):
        """Save the current NBT file with a new name"""
        if self.current_nbt_file is None:
            QMessageBox.warning(self, "No File", "No file is currently open.")
            return
        
        # Use current file path if available, otherwise default to Minecraft folder
        default_dir = self.current_file_path or get_minecraft_folder()
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save NBT File",
            default_dir,
            "NBT Files (*.dat *.nbt);;All Files (*)"
        )
        
        if filepath:
            try:
                save_nbt_file(self.current_nbt_file, filepath)
                self.current_file_path = filepath
                
                is_valid, issues = validate_nbt_file(self.current_nbt_file, filepath)
                
                if is_valid and len(issues) == 0:
                    self.status_bar.showMessage(f"Saved: {os.path.basename(filepath)} (Valid)")
                    QMessageBox.information(self, "Success", "File saved successfully and validated.")
                elif is_valid:
                    self.status_bar.showMessage(f"Saved: {os.path.basename(filepath)} (Warnings: {len(issues)})")
                    msg = "File saved successfully with warnings:\n\n" + "\n".join(issues)
                    QMessageBox.warning(self, "Saved with Warnings", msg)
                else:
                    self.status_bar.showMessage(f"Saved: {os.path.basename(filepath)} (Validation failed)")
                    msg = "File saved but validation failed:\n\n" + "\n".join(issues)
                    QMessageBox.critical(self, "Validation Failed", msg)
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")
    
    def on_tag_selected(self, name: str, tag, parent_tag=None, parent_key=None):
        """Handle tag selection from tree"""
        self.property_editor.set_tag(name, tag, parent_tag, parent_key)
    
    def on_value_changed(self):
        """Handle value change in property editor"""
        if self.current_nbt_file:
            self.tree_widget.load_nbt(self.current_nbt_file)


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    window = NBTEditorMainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

