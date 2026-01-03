#!/usr/bin/env python3
"""
Build script for CADHY Blender Add-on
Generates installable ZIP file for Blender.
"""

import os
import sys
import shutil
import zipfile
import argparse
from pathlib import Path
from datetime import datetime


# Configuration
ADDON_NAME = "cadhy"
VERSION_FILE = Path("cadhy/__init__.py")

# Files/folders to exclude from build
EXCLUDE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".git",
    ".gitignore",
    ".DS_Store",
    "Thumbs.db",
    "*.blend1",
    "*.blend2",
    ".vscode",
    ".idea",
    "*.egg-info",
    ".pytest_cache",
    ".ruff_cache",
    "venv",
    ".venv",
    "node_modules",
]


def get_version() -> str:
    """Extract version from __init__.py"""
    version_file = Path(__file__).parent.parent / VERSION_FILE
    
    with open(version_file, 'r') as f:
        content = f.read()
    
    # Find version tuple in bl_info
    import re
    match = re.search(r'"version":\s*\((\d+),\s*(\d+),\s*(\d+)\)', content)
    if match:
        return f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
    
    return "0.0.0"


def should_exclude(path: Path) -> bool:
    """Check if path should be excluded from build."""
    name = path.name
    
    for pattern in EXCLUDE_PATTERNS:
        if pattern.startswith("*"):
            if name.endswith(pattern[1:]):
                return True
        elif name == pattern:
            return True
    
    return False


def build_addon(output_dir: Path = None, include_version: bool = True) -> Path:
    """
    Build the addon ZIP file.
    
    Args:
        output_dir: Output directory for ZIP file
        include_version: Include version in filename
        
    Returns:
        Path to created ZIP file
    """
    project_root = Path(__file__).parent.parent
    addon_dir = project_root / ADDON_NAME
    
    if output_dir is None:
        output_dir = project_root / "dist"
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get version
    version = get_version()
    
    # Create ZIP filename
    if include_version:
        zip_name = f"{ADDON_NAME}-{version}.zip"
    else:
        zip_name = f"{ADDON_NAME}.zip"
    
    zip_path = output_dir / zip_name
    
    # Remove existing ZIP
    if zip_path.exists():
        zip_path.unlink()
    
    print(f"Building {ADDON_NAME} v{version}...")
    print(f"Output: {zip_path}")
    
    # Create ZIP
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        file_count = 0
        
        for root, dirs, files in os.walk(addon_dir):
            root_path = Path(root)
            
            # Filter directories
            dirs[:] = [d for d in dirs if not should_exclude(root_path / d)]
            
            for file in files:
                file_path = root_path / file
                
                if should_exclude(file_path):
                    continue
                
                # Calculate archive path (relative to project root)
                arc_path = file_path.relative_to(project_root)
                
                zf.write(file_path, arc_path)
                file_count += 1
        
        print(f"Added {file_count} files to archive")
    
    # Print ZIP size
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"ZIP size: {size_mb:.2f} MB")
    
    return zip_path


def clean_build():
    """Clean build artifacts."""
    project_root = Path(__file__).parent.parent
    
    # Clean dist
    dist_dir = project_root / "dist"
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print("Cleaned dist/")
    
    # Clean __pycache__
    for pycache in project_root.rglob("__pycache__"):
        shutil.rmtree(pycache)
        print(f"Cleaned {pycache}")


def main():
    parser = argparse.ArgumentParser(description="Build CADHY Blender Add-on")
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output directory for ZIP file"
    )
    parser.add_argument(
        "--no-version",
        action="store_true",
        help="Don't include version in filename"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts"
    )
    
    args = parser.parse_args()
    
    if args.clean:
        clean_build()
        return
    
    zip_path = build_addon(
        output_dir=args.output,
        include_version=not args.no_version
    )
    
    print(f"\n✓ Build complete: {zip_path}")
    print(f"\nInstall in Blender:")
    print(f"  Edit > Preferences > Add-ons > Install... > Select {zip_path.name}")


if __name__ == "__main__":
    main()
