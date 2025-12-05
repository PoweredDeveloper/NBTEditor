"""
Main Window
Main application window for the NBT Editor.
"""
import os
import webbrowser
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QPushButton,
    QToolBar, QStatusBar, QFileDialog, QMessageBox, QAction, QStyle
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QKeySequence
from nbt.nbt import NBTFile, CompoundTag
from ui.tree_widget import NBTTreeWidget
from ui.property_editor import PropertyEditor
from utils.file_system import get_minecraft_folder
from utils.file_operations import (
    handle_file_open, handle_file_save, get_validation_results, show_validation_results
)
from utils.type_icon import get_icon_for_toolbar
from utils.tag_helpers import can_add_to_tag, can_delete_from_parent
from constants import GITHUB_URL

class NBTEditorMainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.current_file_path = None
        self.current_nbt_file = None
        self.setWindowTitle("NBT Editor")
        self.setGeometry(100, 100, 1000, 700)

        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.toolbar_icon_sheet_path = os.path.join(script_dir, "assets", "toolbar_icon_sheet_scaled.png")
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        
        self.tree_widget = NBTTreeWidget()
        self.tree_widget.on_tag_selected = self.on_tag_selected
        self.tree_widget.on_value_changed = self.on_value_changed
        main_layout.addWidget(self.tree_widget, 1)
        
        self.property_editor = PropertyEditor()
        self.property_editor.hide()
        self.property_editor.on_value_changed = self.on_value_changed
        self.property_editor.on_tag_unselected = self.on_tag_unselected
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

        about_menu = menubar.addMenu("About")

        github_action = about_menu.addAction("Github")
        github_action = about_menu.triggered.connect(lambda: webbrowser.open(GITHUB_URL))
    
    def create_toolbar(self):
        """Create the toolbar"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        toolbar.setMovable(False)
        
        # File operations
        style = self.style()
        new_action = QAction(get_icon_for_toolbar("NewFile", self.toolbar_icon_sheet_path), "New NBT", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.setToolTip("Create a new NBT file")
        new_action.triggered.connect(self.create_new_file)
        toolbar.addAction(new_action)
        
        open_action = QAction(get_icon_for_toolbar("OpenFile", self.toolbar_icon_sheet_path), "Open NBT", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.setToolTip("Open an NBT file")
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)
        
        save_action = QAction(get_icon_for_toolbar("SaveFile", self.toolbar_icon_sheet_path), "Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.setToolTip("Save the current NBT file")
        save_action.triggered.connect(self.save_file)
        toolbar.addAction(save_action)
        
        save_as_action = QAction(get_icon_for_toolbar("SaveFileAs", self.toolbar_icon_sheet_path), "Save As", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.setToolTip("Save the current NBT file with a new name")
        save_as_action.triggered.connect(self.save_file_as)
        toolbar.addAction(save_as_action)
        
        # Separator
        toolbar.addSeparator()
        
        # Tag actions
        self.add_tag_action = QAction(style.standardIcon(QStyle.SP_FileDialogNewFolder), "Add Tag", self)
        self.add_tag_action.setToolTip("Add a new tag to the selected tag")
        self.add_tag_action.triggered.connect(self._add_tag_to_selected)
        self.add_tag_action.setEnabled(False)
        toolbar.addAction(self.add_tag_action)
        
        self.delete_tag_action = QAction(style.standardIcon(QStyle.SP_TrashIcon), "Delete Tag", self)
        self.delete_tag_action.setToolTip("Delete the selected tag")
        self.delete_tag_action.triggered.connect(self._delete_selected_tag)
        self.delete_tag_action.setEnabled(False)
        toolbar.addAction(self.delete_tag_action)
        
        self.rename_tag_action = QAction(style.standardIcon(QStyle.SP_FileDialogDetailedView), "Rename Tag", self)
        self.rename_tag_action.setToolTip("Rename the selected tag")
        self.rename_tag_action.triggered.connect(self._rename_selected_tag)
        self.rename_tag_action.setEnabled(False)
        toolbar.addAction(self.rename_tag_action)
        
        # Store reference to toolbar for later use
        self.toolbar = toolbar
    
    def open_file(self):
        """Open an NBT file"""
        default_dir = get_minecraft_folder()
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open NBT File",
            default_dir,
            "NBT Files (*.dat* *.nbt);;All Files (*)"
        )
        
        if filepath:
            nbt_file, error = handle_file_open(filepath)
            if error:
                QMessageBox.critical(self, "Error", error)
            else:
                self.current_nbt_file = nbt_file
                self.current_file_path = filepath
                self.tree_widget.load_nbt(nbt_file)
                self.status_bar.showMessage(f"Opened: {filepath}")
    
    def _handle_save_result(self, filepath: str, is_valid: bool, issues: list):
        """
        Handle save result and display appropriate messages.
        """
        filename = os.path.basename(filepath)
        
        if is_valid and len(issues) == 0:
            self.status_bar.showMessage(f"Saved: {filename} (Valid)")
        elif is_valid:
            self.status_bar.showMessage(f"Saved: {filename} (Warnings: {len(issues)})")
        else:
            self.status_bar.showMessage(f"Saved: {filename} (Validation failed)")
        
        show_validation_results(self, is_valid, issues, filename)
    
    def save_file(self):
        """Save the current NBT file"""
        if self.current_nbt_file is None:
            QMessageBox.warning(self, "No File", "No file is currently open.")
            return
        
        if self.current_file_path is None:
            self.save_file_as()
            return
        
        success, error = handle_file_save(self.current_nbt_file, self.current_file_path)
        if not success:
            QMessageBox.critical(self, "Error", error)
            return
        
        is_valid, issues = get_validation_results(self.current_nbt_file, self.current_file_path)
        self._handle_save_result(self.current_file_path, is_valid, issues)
    
    def save_file_as(self):
        """Save the current NBT file with a new name"""
        if self.current_nbt_file is None:
            QMessageBox.warning(self, "No File", "No file is currently open.")
            return
        
        default_dir = self.current_file_path or get_minecraft_folder()
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save NBT File",
            default_dir,
            "NBT Files (*.dat *.nbt);;All Files (*)"
        )
        
        if filepath:
            success, error = handle_file_save(self.current_nbt_file, filepath)
            if not success:
                QMessageBox.critical(self, "Error", error)
                return
            
            self.current_file_path = filepath
            
            is_valid, issues = get_validation_results(self.current_nbt_file, filepath)
            self._handle_save_result(filepath, is_valid, issues)
    
    def on_tag_selected(self, name: str, tag, parent_tag=None, parent_key=None):
        """Handle tag selection from tree"""
        self.property_editor.set_tag(name, tag, parent_tag, parent_key)
        self.property_editor.show()
        self._update_tag_action_buttons(tag, parent_tag, parent_key)
    
    def on_value_changed(self):
        """Handle value change in property editor"""
        if self.current_nbt_file:
            self.tree_widget.refresh_tree()
    
    def on_tag_unselected(self):
        """Handle tag unselection"""
        self.tree_widget.clearSelection()
        self.property_editor.set_tag(None, None)
        self.property_editor.hide()
        self._update_tag_action_buttons(None, None, None)
    
    def create_new_file(self):
        """Create a new empty NBT file"""
        new_file = NBTFile(CompoundTag(), "")
        self.current_nbt_file = new_file
        self.current_file_path = None
        self.tree_widget.load_nbt(new_file)
        
        root_items = self.tree_widget.findItems("root", Qt.MatchExactly | Qt.MatchRecursive, 0)
        if root_items:
            self.tree_widget.setCurrentItem(root_items[0])
            self.tree_widget.on_selection_changed()
        
        self.status_bar.showMessage("New NBT file created")
    
    def _update_tag_action_buttons(self, tag, parent_tag=None, parent_key=None):
        """Update the enabled state of tag action buttons based on current selection"""
        if tag is None:
            self.add_tag_action.setEnabled(False)
            self.delete_tag_action.setEnabled(False)
            self.rename_tag_action.setEnabled(False)
            return
        
        # Add tag button - enabled if current tag can have children
        self.add_tag_action.setEnabled(can_add_to_tag(tag))
        
        # Delete tag button - enabled if tag can be deleted from parent
        self.delete_tag_action.setEnabled(can_delete_from_parent(parent_tag) and parent_key is not None)
        
        # Rename tag button - enabled only for CompoundTag entries
        from nbt.nbt import CompoundTag
        self.rename_tag_action.setEnabled(
            isinstance(parent_tag, CompoundTag) and parent_key is not None
        )
    
    def _add_tag_to_selected(self):
        """Add a new tag to the currently selected tag"""
        if self.property_editor.current_tag is None:
            return
        self.property_editor.add_tag()
    
    def _delete_selected_tag(self):
        """Delete the currently selected tag"""
        if (self.property_editor.current_tag is None or 
            self.property_editor.current_parent_tag is None or
            self.property_editor.current_parent_key is None):
            return
        self.property_editor.delete_tag()
    
    def _rename_selected_tag(self):
        """Rename the currently selected tag"""
        if (self.property_editor.current_tag is None or 
            self.property_editor.current_parent_tag is None or
            self.property_editor.current_parent_key is None):
            return
        self.property_editor.rename_tag()

