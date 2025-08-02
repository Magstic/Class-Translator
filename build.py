import PyInstaller.__main__
import shutil
import time
from pathlib import Path

# --- Configuration ---
APP_NAME = "CLASS編輯器"
APP_VERSION = "1.0.0"  # <--- UPDATE VERSION HERE
MAIN_SCRIPT = "main.py"

# The name of the icon file. Set to None if no icon.
# Ensure the icon is in the project root or provide a relative path.
ICON_FILE = None  # Example: "assets/app.ico"

# Directories to clean before and after the build
CLEAN_DIRS = ["build", "dist"]

# Data files and directories to be included in the build
# Format: ("source_path", "destination_in_bundle")
DATA_TO_ADD = [
    ("Azure-ttk-theme-main", "Azure-ttk-theme-main"),
    ("config", "config"),
    ("config.json", "."),  # Add config.json to the root
]

# PyInstaller hidden imports
# Add modules that PyInstaller might not detect automatically
HIDDEN_IMPORTS = [
    "PIL.ImageTk",
    "sv_ttk",
]

# --- End of Configuration ---


def get_build_version():
    """Generates a build version string with a timestamp."""
    timestamp = time.strftime("%Y%m%d")
    return f"{APP_VERSION}_{timestamp}"

def build():
    """Main build function to run PyInstaller and package the app."""
    project_root = Path(__file__).parent
    build_version = get_build_version()
    exe_name = f"{APP_NAME}_v{build_version}"

    # 1. Clean up previous builds
    print("--- Cleaning up old build directories ---")
    for dir_name in CLEAN_DIRS:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"Removing directory: {dir_path}")
            shutil.rmtree(dir_path)

    # 2. Assemble PyInstaller command
    print("\n--- Assembling PyInstaller command ---")
    args = [
        "--onefile",
        "--windowed",
        "--noconfirm",
        f"--name={exe_name}",
    ]

    if ICON_FILE:
        icon_path = project_root / ICON_FILE
        if icon_path.exists():
            args.append(f"--icon={icon_path}")
            print(f"Icon added: {icon_path}")
        else:
            print(f"Warning: Icon file not found at {icon_path}")

    for src, dest in DATA_TO_ADD:
        src_path = project_root / src
        if src_path.exists():
            args.append(f"--add-data={src_path};{dest}")
            print(f"Data added: {src_path} -> {dest}")
        else:
            print(f"Warning: Data source not found at {src_path}")

    for hidden_import in HIDDEN_IMPORTS:
        args.append(f"--hidden-import={hidden_import}")
        print(f"Hidden import added: {hidden_import}")

    script_path = project_root / MAIN_SCRIPT
    if not script_path.exists():
        print(f"Error: Main script '{script_path}' not found!")
        return
    args.append(str(script_path))

    print(f"\nBuild command: pyinstaller {' '.join(args)}")

    # 3. Run PyInstaller
    print("\n--- Starting PyInstaller build ---")
    try:
        PyInstaller.__main__.run(args)
        print("\n--- Build successful! ---")
        dist_path = project_root / "dist"
        print(f"Executable created at: {dist_path / (exe_name + '.exe')}")
    except Exception as e:
        print(f"\n--- Build failed! ---")
        print(f"Error: {e}")
        return

    # 4. Create a zip archive of the result
    print("\n--- Creating distributable zip archive ---")
    dist_path = project_root / "dist"
    archive_name = f"{APP_NAME}_v{build_version}"
    archive_path = project_root / archive_name

    try:
        shutil.make_archive(str(archive_path), 'zip', dist_path)
        print(f"Successfully created zip file: {archive_path}.zip")
    except Exception as e:
        print(f"Failed to create zip file: {e}")


if __name__ == "__main__":
    build()
