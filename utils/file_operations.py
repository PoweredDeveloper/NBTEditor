"""
File Operation Helpers
Utility functions for file operations with error handling and user feedback.
"""
import os
from typing import Tuple, Optional
from PyQt5.QtWidgets import QMessageBox
from nbt.nbt_handler import load_nbt_file, save_nbt_file, validate_nbt_file
from nbt.nbt import NBTFile


def handle_file_open(filepath: str) -> Tuple[Optional[NBTFile], Optional[str]]:
    """
    Open an NBT file with error handling.
    
    Args:
        filepath: Path to the NBT file to open
        
    Returns:
        Tuple of (NBTFile, error_message)
        If successful, error_message is None
    """
    try:
        nbt_file = load_nbt_file(filepath)
        return nbt_file, None
    except Exception as e:
        return None, f"Failed to open file: {str(e)}"


def handle_file_save(nbt_file: NBTFile, filepath: str, compressed: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Save an NBT file with error handling.
    """
    try:
        save_nbt_file(nbt_file, filepath, compressed)
        return True, None
    except Exception as e:
        return False, f"Failed to save file: {str(e)}"


def get_validation_results(nbt_file: NBTFile, filepath: str) -> Tuple[bool, list]:
    """
    Validate an NBT file and return results.
    """
    return validate_nbt_file(nbt_file, filepath)


def show_validation_results(parent, is_valid: bool, issues: list, filename: str) -> None:
    """
    Display validation results to the user.
    """
    if is_valid and len(issues) == 0:
        QMessageBox.information(parent, "Success", "File saved successfully and validated.")
    elif is_valid:
        msg = "File saved successfully with warnings:\n\n" + "\n".join(issues)
        QMessageBox.warning(parent, "Saved with Warnings", msg)
    else:
        msg = "File saved but validation failed:\n\n" + "\n".join(issues)
        QMessageBox.critical(parent, "Validation Failed", msg)

