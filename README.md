# NBT Editor

A simple, cross-platform GUI application for viewing and editing Minecraft NBT (Named Binary Tag) files. Built with Python and PyQt5, featuring a custom NBT library implementation.

## Features

- **Open and View NBT Files**: Browse NBT file structure in a hierarchical tree view
- **Edit Values**: Modify primitive values (integers, floats, strings) and arrays
- **Array Editing**: Edit byte arrays, int arrays, and long arrays using comma-separated values
- **Delete Tags**: Remove key-value pairs from compound tags
- **File Validation**: Automatic validation after saving to ensure file integrity and game compatibility
- **Minecraft Integration**: Automatically opens in your Minecraft folder for easy access to world and player data
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Requirements

- Python 3.9 or higher
- PyQt5

## Installation

1. Clone or download this repository

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

```bash
python main.py
```

### Opening Files

1. Click **File → Open** or use the toolbar button
2. The file dialog will open in your Minecraft folder by default:
   - **Windows**: `%APPDATA%\.minecraft`
   - **macOS**: `~/Library/Application Support/minecraft`
   - **Linux**: `~/.minecraft`
3. Navigate to your desired NBT file (e.g., `saves/<world>/level.dat` or `saves/<world>/playerdata/*.dat`)

### Editing Values

1. Select a tag in the tree view on the left
2. View tag information in the property editor on the right
3. For editable tags (primitives and arrays), enter a new value:
   - **Primitives**: Enter the value directly (e.g., `42`, `3.14`, `"Hello"`)
   - **Arrays**: Enter comma-separated values (e.g., `1, 2, 3, 4`)
4. Click **Apply** to save changes

### Deleting Tags

1. Select a tag that is inside a compound tag
2. Click the **Delete This Tag** button
3. Confirm the deletion

### Saving Files

1. Click **File → Save** (Ctrl+S) to save to the current file
2. Click **File → Save As** (Ctrl+Shift+S) to save to a new location
3. The application will validate the file after saving and show any warnings or errors

## File Structure

```
NBTEditor/
├── main.py              # Main application and GUI
├── nbt.py               # Custom NBT library implementation
├── nbt_handler.py       # NBT file operations and validation
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Supported NBT Tag Types

- **Primitives**: Byte, Short, Int, Long, Float, Double, String
- **Arrays**: ByteArray, IntArray, LongArray
- **Complex**: List, Compound

## Validation

The application performs two types of validation:

1. **Format Validation**: Ensures the NBT file structure is valid
2. **Game Compatibility**: Checks for required fields in:
   - `level.dat` files (Data, DataVersion, Version tags)
   - Player data files (DataVersion tag)

## Custom NBT Library

This project includes a custom NBT library implementation (`nbt.py`) that:

- Implements the complete NBT specification
- Supports all NBT tag types
- Handles gzip compression/decompression
- Works with Python 3.9+
- Has no external dependencies (besides PyQt5 for the GUI)

## Platform Support

- **Windows**: Tested on Windows 10/11
- **macOS**: Tested on macOS 10.15+
- **Linux**: Should work on most Linux distributions

## Notes

- Always backup your Minecraft world files before editing
- Invalid edits may corrupt your world files
- The application validates files after saving, but it's recommended to test in a backup world first
- Some NBT structures may be read-only (compounds, lists) - only their child values can be edited

## Keyboard Shortcuts

- **Ctrl+O**: Open file
- **Ctrl+S**: Save file
- **Ctrl+Shift+S**: Save As
- **Ctrl+Q**: Exit application

## Troubleshooting

**File won't open:**

- Ensure the file is a valid NBT file
- Check if the file is corrupted
- Try opening with a different NBT viewer to verify

**Changes not saving:**

- Check file permissions
- Ensure you have write access to the file location
- Verify the file isn't locked by Minecraft or another application

**Validation errors:**

- Review the validation messages carefully
- Some warnings may be acceptable depending on your use case
- Format errors indicate the file structure is invalid

## License

This project is provided as-is for educational and personal use.

## Contributing

Feel free to submit issues or pull requests for improvements.
