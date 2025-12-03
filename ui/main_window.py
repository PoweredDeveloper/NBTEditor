"""
Main Window
Main application window for the NBT Editor.
"""
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QPushButton,
    QToolBar, QStatusBar, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from nbt.nbt import NBTFile, CompoundTag
from ui.tree_widget import NBTTreeWidget
from ui.property_editor import PropertyEditor
from utils.file_system import get_minecraft_folder
from utils.file_operations import (
    handle_file_open, handle_file_save, get_validation_results, show_validation_results
)


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
    
    def create_toolbar(self):
        """Create the toolbar"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        toolbar.setMovable(False)
        
        create_btn = QPushButton("Create NBT File")
        create_btn.clicked.connect(self.create_new_file)
        toolbar.addWidget(create_btn)
        
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
            nbt_file, error = handle_file_open(filepath)
            if error:
                QMessageBox.critical(self, "Error", error)
            else:
                self.current_nbt_file = nbt_file
                self.current_file_path = filepath
                self.tree_widget.load_nbt(nbt_file)
                self.status_bar.showMessage(f"Opened: {filepath}")
    
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
        filename = os.path.basename(self.current_file_path)
        
        if is_valid and len(issues) == 0:
            self.status_bar.showMessage(f"Saved: {filename} (Valid)")
        elif is_valid:
            self.status_bar.showMessage(f"Saved: {filename} (Warnings: {len(issues)})")
        else:
            self.status_bar.showMessage(f"Saved: {filename} (Validation failed)")
        
        show_validation_results(self, is_valid, issues, filename)
    
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
            filename = os.path.basename(filepath)
            
            if is_valid and len(issues) == 0:
                self.status_bar.showMessage(f"Saved: {filename} (Valid)")
            elif is_valid:
                self.status_bar.showMessage(f"Saved: {filename} (Warnings: {len(issues)})")
            else:
                self.status_bar.showMessage(f"Saved: {filename} (Validation failed)")
            
            show_validation_results(self, is_valid, issues, filename)
    
    def on_tag_selected(self, name: str, tag, parent_tag=None, parent_key=None):
        """Handle tag selection from tree"""
        self.property_editor.set_tag(name, tag, parent_tag, parent_key)
    
    def on_value_changed(self):
        """Handle value change in property editor"""
        if self.current_nbt_file:
            self.tree_widget.load_nbt(self.current_nbt_file)
    
    def on_tag_unselected(self):
        """Handle tag unselection"""
        self.tree_widget.clearSelection()
        self.property_editor.set_tag(None, None)
    
    def create_new_file(self):
        """Create a new empty NBT file"""
        new_file = NBTFile(CompoundTag(), "")
        self.current_nbt_file = new_file
        self.current_file_path = None
        self.tree_widget.load_nbt(new_file)
        
        # Automatically select the root tag so user can add tags immediately
        root_items = self.tree_widget.findItems("root", Qt.MatchExactly | Qt.MatchRecursive, 0)
        if root_items:
            self.tree_widget.setCurrentItem(root_items[0])
            self.tree_widget.on_selection_changed()
        
        self.status_bar.showMessage("New NBT file created")

