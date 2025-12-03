"""
NBT Editor - Main Entry Point
Simple GUI application for editing Minecraft NBT files.
"""
import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import NBTEditorMainWindow


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    window = NBTEditorMainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
