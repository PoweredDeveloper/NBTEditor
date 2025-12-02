import sys, os

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
