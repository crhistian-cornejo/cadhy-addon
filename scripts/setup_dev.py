#!/usr/bin/env python3
"""
Development setup script for CADHY Blender Add-on.
Creates symlinks to Blender's addons folder for live development.

Works on Windows, macOS, and Linux.
"""

import os
import sys
import platform
import argparse
from pathlib import Path


def get_blender_addons_paths() -> list:
    """
    Get possible Blender addons directories.
    
    Returns:
        List of potential addon directories
    """
    system = platform.system()
    home = Path.home()
    
    paths = []
    
    # Common Blender versions to check
    versions = ["4.3", "4.2", "4.1", "4.0", "3.6"]
    
    if system == "Windows":
        # Windows paths
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            base = Path(appdata) / "Blender Foundation" / "Blender"
            for ver in versions:
                paths.append(base / ver / "scripts" / "addons")
        
        # Also check Program Files for portable installs
        for pf in ["PROGRAMFILES", "PROGRAMFILES(X86)"]:
            pf_path = os.environ.get(pf, "")
            if pf_path:
                for ver in versions:
                    paths.append(Path(pf_path) / "Blender Foundation" / f"Blender {ver}" / ver / "scripts" / "addons")
    
    elif system == "Darwin":  # macOS
        base = home / "Library" / "Application Support" / "Blender"
        for ver in versions:
            paths.append(base / ver / "scripts" / "addons")
    
    else:  # Linux
        # Standard config location
        config_base = home / ".config" / "blender"
        for ver in versions:
            paths.append(config_base / ver / "scripts" / "addons")
        
        # Snap installation
        snap_base = home / "snap" / "blender" / "common" / ".config" / "blender"
        for ver in versions:
            paths.append(snap_base / ver / "scripts" / "addons")
        
        # Flatpak installation
        flatpak_base = home / ".var" / "app" / "org.blender.Blender" / "config" / "blender"
        for ver in versions:
            paths.append(flatpak_base / ver / "scripts" / "addons")
    
    return paths


def find_blender_addons_dir() -> Path:
    """
    Find an existing Blender addons directory.
    
    Returns:
        Path to addons directory or None
    """
    for path in get_blender_addons_paths():
        if path.exists():
            return path
    
    return None


def create_symlink(source: Path, target: Path, force: bool = False) -> bool:
    """
    Create a symbolic link.
    
    Args:
        source: Source directory (addon)
        target: Target path (in Blender addons)
        force: Remove existing link/directory
        
    Returns:
        True if successful
    """
    system = platform.system()
    
    if target.exists() or target.is_symlink():
        if force:
            if target.is_symlink():
                target.unlink()
            elif target.is_dir():
                import shutil
                shutil.rmtree(target)
            else:
                target.unlink()
            print(f"Removed existing: {target}")
        else:
            print(f"Target already exists: {target}")
            print("Use --force to overwrite")
            return False
    
    try:
        if system == "Windows":
            # Windows requires admin or developer mode for symlinks
            # Try symlink first, fall back to junction
            try:
                target.symlink_to(source, target_is_directory=True)
            except OSError:
                # Try using mklink /J (junction) as fallback
                import subprocess
                result = subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(target), str(source)],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    raise OSError(f"Failed to create junction: {result.stderr}")
        else:
            target.symlink_to(source)
        
        print(f"Created symlink: {target} -> {source}")
        return True
        
    except OSError as e:
        print(f"Error creating symlink: {e}")
        if system == "Windows":
            print("\nOn Windows, you may need to:")
            print("1. Run as Administrator, or")
            print("2. Enable Developer Mode in Settings > Update & Security > For developers")
        return False


def setup_development(blender_path: Path = None, force: bool = False) -> bool:
    """
    Set up development environment.
    
    Args:
        blender_path: Custom Blender addons path
        force: Force overwrite existing
        
    Returns:
        True if successful
    """
    # Find addon source
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    addon_source = project_root / "cadhy"
    
    if not addon_source.exists():
        print(f"Error: Addon source not found: {addon_source}")
        return False
    
    # Find Blender addons directory
    if blender_path:
        addons_dir = Path(blender_path)
        if not addons_dir.exists():
            print(f"Creating directory: {addons_dir}")
            addons_dir.mkdir(parents=True, exist_ok=True)
    else:
        addons_dir = find_blender_addons_dir()
        if not addons_dir:
            print("Could not find Blender addons directory.")
            print("\nPossible locations checked:")
            for path in get_blender_addons_paths():
                print(f"  {path}")
            print("\nPlease specify path with --blender-path")
            return False
    
    print(f"Blender addons directory: {addons_dir}")
    
    # Create symlink
    target = addons_dir / "cadhy"
    return create_symlink(addon_source, target, force)


def remove_development(blender_path: Path = None) -> bool:
    """
    Remove development symlink.
    
    Args:
        blender_path: Custom Blender addons path
        
    Returns:
        True if successful
    """
    if blender_path:
        addons_dir = Path(blender_path)
    else:
        addons_dir = find_blender_addons_dir()
        if not addons_dir:
            print("Could not find Blender addons directory.")
            return False
    
    target = addons_dir / "cadhy"
    
    if target.is_symlink():
        target.unlink()
        print(f"Removed symlink: {target}")
        return True
    elif target.exists():
        print(f"Warning: {target} is not a symlink")
        return False
    else:
        print(f"Symlink does not exist: {target}")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Set up CADHY development environment"
    )
    parser.add_argument(
        "--blender-path", "-b",
        type=Path,
        help="Custom Blender addons directory path"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force overwrite existing symlink"
    )
    parser.add_argument(
        "--remove", "-r",
        action="store_true",
        help="Remove development symlink"
    )
    parser.add_argument(
        "--list-paths",
        action="store_true",
        help="List possible Blender addon paths"
    )
    
    args = parser.parse_args()
    
    if args.list_paths:
        print("Possible Blender addon directories:")
        for path in get_blender_addons_paths():
            exists = "✓" if path.exists() else "✗"
            print(f"  {exists} {path}")
        return
    
    if args.remove:
        success = remove_development(args.blender_path)
    else:
        success = setup_development(args.blender_path, args.force)
    
    if success:
        print("\n✓ Done!")
        if not args.remove:
            print("\nNext steps:")
            print("1. Open Blender")
            print("2. Go to Edit > Preferences > Add-ons")
            print("3. Search for 'CADHY' and enable it")
            print("4. Press N in 3D View to see CADHY panel")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
