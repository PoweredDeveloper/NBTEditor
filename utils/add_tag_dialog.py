"""
Add Tag Dialog
Dialog for creating new NBT tags.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QTextEdit, QMessageBox, QFormLayout, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QRegExpValidator
from PyQt5.QtCore import QRegExp
from nbt.nbt import (
    ByteTag, ShortTag, IntTag, LongTag, FloatTag, DoubleTag, StringTag,
    ByteArrayTag, IntArrayTag, LongArrayTag, ListTag, CompoundTag
)


class AddTagDialog(QDialog):
    """Dialog for creating a new NBT tag"""
    
    TAG_TYPES = {
        "Byte": ByteTag,
        "Short": ShortTag,
        "Int": IntTag,
        "Long": LongTag,
        "Float": FloatTag,
        "Double": DoubleTag,
        "String": StringTag,
        "ByteArray": ByteArrayTag,
        "IntArray": IntArrayTag,
        "LongArray": LongArrayTag,
        "List": ListTag,
        "Compound": CompoundTag,
    }
    
    def __init__(self, parent=None, require_name=True, list_type=None):
        """
        Initialize the dialog.
        
        Args:
            parent: Parent widget
            require_name: Whether name field is required (for compound entries)
            list_type: Required tag type for list items (None if not adding to list)
        """
        super().__init__(parent)
        self.require_name = require_name
        self.list_type = list_type
        self.created_tag = None
        self.tag_name = ""
        
        self.setWindowTitle("Add New Tag")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Tag type selection
        type_group = QGroupBox("Tag Type")
        type_layout = QVBoxLayout()
        
        self.type_combo = QComboBox()
        if self.list_type is not None:
            # If adding to a list, only show the list's type
            found = False
            for name, tag_class in self.TAG_TYPES.items():
                if tag_class == self.list_type:
                    self.type_combo.addItem(name, tag_class)
                    found = True
                    break
            if not found:
                # If list type not found, show all types
                for name in self.TAG_TYPES.keys():
                    self.type_combo.addItem(name, self.TAG_TYPES[name])
            else:
                self.type_combo.setEnabled(False)
        else:
            # Show all tag types
            for name in self.TAG_TYPES.keys():
                self.type_combo.addItem(name, self.TAG_TYPES[name])
        
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        type_layout.addWidget(self.type_combo)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # Name input (for compound entries)
        if self.require_name:
            name_group = QGroupBox("Tag Name")
            name_layout = QVBoxLayout()
            
            self.name_input = QLineEdit()
            self.name_input.setPlaceholderText("Enter tag name...")
            name_layout.addWidget(self.name_input)
            name_group.setLayout(name_layout)
            layout.addWidget(name_group)
        else:
            self.name_input = None
        
        # Value input
        value_group = QGroupBox("Tag Value")
        value_layout = QVBoxLayout()
        
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Enter value (comma-separated for arrays)...")
        value_layout.addWidget(self.value_input)
        value_group.setLayout(value_layout)
        layout.addWidget(value_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.create_button = QPushButton("Create")
        self.create_button.clicked.connect(self.create_tag)
        self.create_button.setDefault(True)
        button_layout.addWidget(self.create_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Set initial state
        self.on_type_changed()
    
    def on_type_changed(self):
        """Handle tag type selection change"""
        current_type = self.type_combo.currentData()
        
        # Clear previous validator
        self.value_input.setValidator(None)
        
        if current_type in (ListTag, CompoundTag):
            # Complex types don't need values
            self.value_input.setPlaceholderText("(No value needed - will create empty structure)")
            self.value_input.setEnabled(False)
        elif current_type in (ByteTag, ShortTag, IntTag, LongTag):
            # Integer types - only numbers
            validator = QIntValidator()
            self.value_input.setValidator(validator)
            self.value_input.setPlaceholderText("Enter integer value...")
            self.value_input.setEnabled(True)
        elif current_type in (FloatTag, DoubleTag):
            # Float types - numbers with optional decimal point
            # Use regex to allow typing dots and intermediate states like ".", "1.", ".5"
            # Allows: empty, sign only, digits, dot, digits with dot, etc.
            regex = QRegExp(r'^[+-]?(\d*\.?\d*|\.\d*)$')
            validator = QRegExpValidator(regex)
            self.value_input.setValidator(validator)
            self.value_input.setPlaceholderText("Enter float value...")
            self.value_input.setEnabled(True)
        elif current_type == StringTag:
            # String - any text
            self.value_input.setPlaceholderText("Enter string value...")
            self.value_input.setEnabled(True)
        elif current_type in (ByteArrayTag, IntArrayTag, LongArrayTag):
            # Arrays - comma-separated integers
            regex = QRegExp(r'^[\d\s,+-]+$')
            validator = QRegExpValidator(regex)
            self.value_input.setValidator(validator)
            self.value_input.setPlaceholderText("Enter comma-separated values (e.g., 1, 2, 3)")
            self.value_input.setEnabled(True)
        else:
            self.value_input.setPlaceholderText("Enter value...")
            self.value_input.setEnabled(True)
    
    def create_tag(self):
        """Create the tag based on user input"""
        # Validate name if required
        if self.require_name:
            name = self.name_input.text().strip()
            if not name:
                QMessageBox.warning(self, "Invalid Input", "Tag name is required.")
                return
            self.tag_name = name
        
        # Get selected tag type
        tag_class = self.type_combo.currentData()
        value_text = self.value_input.text().strip()
        
        try:
            # Create tag based on type
            if tag_class == ByteTag:
                if not value_text:
                    value = 0
                else:
                    value = int(value_text) & 0xFF
                self.created_tag = ByteTag(value)
            
            elif tag_class == ShortTag:
                if not value_text:
                    value = 0
                else:
                    value = int(value_text) & 0xFFFF
                self.created_tag = ShortTag(value)
            
            elif tag_class == IntTag:
                if not value_text:
                    value = 0
                else:
                    value = int(value_text)
                self.created_tag = IntTag(value)
            
            elif tag_class == LongTag:
                if not value_text:
                    value = 0
                else:
                    value = int(value_text)
                self.created_tag = LongTag(value)
            
            elif tag_class == FloatTag:
                if not value_text:
                    value = 0.0
                else:
                    value = float(value_text)
                self.created_tag = FloatTag(value)
            
            elif tag_class == DoubleTag:
                if not value_text:
                    value = 0.0
                else:
                    value = float(value_text)
                self.created_tag = DoubleTag(value)
            
            elif tag_class == StringTag:
                self.created_tag = StringTag(value_text)
            
            elif tag_class == ByteArrayTag:
                if value_text:
                    values = [int(x.strip()) & 0xFF for x in value_text.split(",")]
                else:
                    values = []
                self.created_tag = ByteArrayTag(values)
            
            elif tag_class == IntArrayTag:
                if value_text:
                    values = [int(x.strip()) for x in value_text.split(",")]
                else:
                    values = []
                self.created_tag = IntArrayTag(values)
            
            elif tag_class == LongArrayTag:
                if value_text:
                    values = [int(x.strip()) for x in value_text.split(",")]
                else:
                    values = []
                self.created_tag = LongArrayTag(values)
            
            elif tag_class == ListTag:
                self.created_tag = ListTag([])
            
            elif tag_class == CompoundTag:
                self.created_tag = CompoundTag({})
            
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Value", f"Could not parse value: {str(e)}\n\nFor arrays, use comma-separated values (e.g., 1, 2, 3)")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to create tag: {str(e)}")
    
    def get_result(self):
        """Get the created tag and name"""
        return self.tag_name, self.created_tag

