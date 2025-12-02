"""
NBT File Handler
Handles loading, saving, and validation of NBT files for Minecraft.
"""
import os
from typing import Tuple, List
from nbt import NBTFile, CompoundTag


class NBTValidationError(Exception):
    """Custom exception for NBT validation errors"""
    pass


def load_nbt_file(filepath: str) -> NBTFile:
    try:
        try:
            nbt_file = NBTFile.load(filepath, gzipped=True)
            return nbt_file
        except:
            nbt_file = NBTFile.load(filepath, gzipped=False)
            return nbt_file
    except Exception as e:
        raise Exception(f"Failed to load NBT file: {str(e)}")


def save_nbt_file(nbt_file: NBTFile, filepath: str, compressed: bool = True) -> None:
    try:
        nbt_file.save(filepath, gzipped=compressed)
    except Exception as e:
        raise Exception(f"Failed to save NBT file: {str(e)}")


def validate_nbt_format(nbt_file: NBTFile) -> Tuple[bool, List[str]]:
    errors = []
    
    try:
        if nbt_file.root is None:
            errors.append("NBT file has no root tag")
            return False, errors
        
        _ = nbt_file.root.serialize()
        
    except Exception as e:
        errors.append(f"Invalid NBT structure: {str(e)}")
        return False, errors
    
    return True, errors


def validate_game_compatibility(nbt_file: NBTFile, filepath: str) -> Tuple[bool, List[str]]:
    warnings = []
    filename = os.path.basename(filepath).lower()
    
    if filename == "level.dat":
        root = nbt_file.root
        if not isinstance(root, CompoundTag):
            warnings.append("level.dat root should be a Compound tag")
        else:
            if "Data" not in root:
                warnings.append("level.dat missing 'Data' tag")
            elif isinstance(root["Data"], CompoundTag):
                data = root["Data"]
                if "DataVersion" not in data:
                    warnings.append("level.dat missing 'DataVersion' tag")
                if "Version" not in data:
                    warnings.append("level.dat missing 'Version' tag")
    
    elif filename.endswith(".dat") and "playerdata" in filepath.lower():
        root = nbt_file.root
        if not isinstance(root, CompoundTag):
            warnings.append("Player data file root should be a Compound tag")
        else:
            if "DataVersion" not in root:
                warnings.append("Player data file missing 'DataVersion' tag")
            if len(root) == 0:
                warnings.append("Player data file appears to be empty")
    
    return len(warnings) == 0, warnings


def validate_nbt_file(nbt_file: NBTFile, filepath: str) -> Tuple[bool, List[str]]:
    all_issues = []
    
    format_valid, format_errors = validate_nbt_format(nbt_file)
    if not format_valid:
        all_issues.extend(format_errors)
        return False, all_issues
    
    _, game_warnings = validate_game_compatibility(nbt_file, filepath)
    all_issues.extend(game_warnings)
    
    return format_valid, all_issues

