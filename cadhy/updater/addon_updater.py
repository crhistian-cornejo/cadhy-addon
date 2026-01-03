"""
Addon Updater Module
Core updater functionality for CADHY addon.

Based on CGCookie's blender-addon-updater pattern.
https://github.com/CGCookie/blender-addon-updater
"""

import json
import os
import shutil
import tempfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from typing import Optional, Tuple

from ..core.util.versioning import CADHY_VERSION, CADHY_VERSION_STRING

# GitHub repository info
GITHUB_USER = "crhistian-cornejo"
GITHUB_REPO = "cadhy-addon"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"


@dataclass
class ReleaseInfo:
    """Information about a GitHub release."""

    version: Tuple[int, int, int]
    version_string: str
    tag_name: str
    download_url: str
    release_notes: str
    published_at: str


class AddonUpdater:
    """
    Handles checking for and installing addon updates.
    """

    def __init__(self):
        self._latest_release: Optional[ReleaseInfo] = None
        self._update_available: bool = False
        self._last_check: Optional[str] = None
        self._error: Optional[str] = None

    @property
    def update_available(self) -> bool:
        """Check if an update is available."""
        return self._update_available

    @property
    def latest_release(self) -> Optional[ReleaseInfo]:
        """Get latest release info."""
        return self._latest_release

    @property
    def error(self) -> Optional[str]:
        """Get last error message."""
        return self._error

    def check_for_updates(self, timeout: int = 10) -> bool:
        """
        Check GitHub for available updates.

        Args:
            timeout: Request timeout in seconds

        Returns:
            True if check was successful
        """
        self._error = None

        try:
            # Create request with headers
            request = urllib.request.Request(
                GITHUB_API_URL,
                headers={
                    "User-Agent": f"CADHY-Addon/{CADHY_VERSION_STRING}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )

            # Make request
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))

            # Parse release info
            tag_name = data.get("tag_name", "")
            version_string = tag_name.lstrip("v")

            # Parse version tuple
            try:
                version_parts = version_string.split(".")
                version = tuple(int(p) for p in version_parts[:3])
            except Exception:
                version = (0, 0, 0)

            # Find download URL (look for .zip asset)
            download_url = None
            for asset in data.get("assets", []):
                if asset.get("name", "").endswith(".zip"):
                    download_url = asset.get("browser_download_url")
                    break

            # Fallback to zipball
            if not download_url:
                download_url = data.get("zipball_url")

            self._latest_release = ReleaseInfo(
                version=version,
                version_string=version_string,
                tag_name=tag_name,
                download_url=download_url,
                release_notes=data.get("body", ""),
                published_at=data.get("published_at", ""),
            )

            # Check if update is available
            self._update_available = version > CADHY_VERSION

            from datetime import datetime

            self._last_check = datetime.now().isoformat()

            return True

        except urllib.error.URLError as e:
            self._error = f"Network error: {e.reason}"
        except json.JSONDecodeError:
            self._error = "Invalid response from GitHub"
        except Exception as e:
            self._error = f"Update check failed: {str(e)}"

        return False

    def download_update(self, download_dir: Optional[str] = None) -> Optional[str]:
        """
        Download the latest release.

        Args:
            download_dir: Directory to download to (uses temp if None)

        Returns:
            Path to downloaded zip file or None
        """
        if not self._latest_release or not self._latest_release.download_url:
            self._error = "No release available to download"
            return None

        if download_dir is None:
            download_dir = tempfile.gettempdir()

        try:
            filename = f"cadhy-{self._latest_release.version_string}.zip"
            filepath = os.path.join(download_dir, filename)

            # Download file
            request = urllib.request.Request(
                self._latest_release.download_url, headers={"User-Agent": f"CADHY-Addon/{CADHY_VERSION_STRING}"}
            )

            with urllib.request.urlopen(request) as response:
                with open(filepath, "wb") as f:
                    f.write(response.read())

            return filepath

        except Exception as e:
            self._error = f"Download failed: {str(e)}"
            return None

    def install_update(self, zip_path: str) -> bool:
        """
        Install update from downloaded zip file.

        Args:
            zip_path: Path to downloaded zip file

        Returns:
            True if installation successful
        """
        backup_dir = None

        try:
            # Get addon directory (cadhy/)
            # __file__ is: .../addons/cadhy/updater/addon_updater.py
            # dirname x2 gives us: .../addons/cadhy/
            addon_dir = os.path.dirname(os.path.dirname(__file__))
            addons_dir = os.path.dirname(addon_dir)  # .../addons/

            # Verify we're in the right place (safety check)
            if not addon_dir.endswith("cadhy"):
                self._error = f"Unexpected addon directory: {addon_dir}"
                return False

            # Create backup
            backup_dir = os.path.join(addons_dir, "cadhy_backup")
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            shutil.copytree(addon_dir, backup_dir)

            # Extract new version
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # Check ZIP structure - our ZIPs have cadhy/ as root
                names = zip_ref.namelist()
                if not names:
                    self._error = "Empty ZIP file"
                    return False

                root_folder = names[0].split("/")[0]

                # Extract to temp location
                temp_extract = os.path.join(addons_dir, "cadhy_update_temp")
                if os.path.exists(temp_extract):
                    shutil.rmtree(temp_extract)
                zip_ref.extractall(temp_extract)

                # The extracted content should be at temp_extract/cadhy/
                extracted_addon = os.path.join(temp_extract, root_folder)

                if not os.path.exists(extracted_addon):
                    self._error = f"Expected folder '{root_folder}' not found in ZIP"
                    shutil.rmtree(temp_extract)
                    return False

                # Verify it looks like a valid addon
                init_file = os.path.join(extracted_addon, "__init__.py")
                if not os.path.exists(init_file):
                    self._error = "Invalid addon: __init__.py not found"
                    shutil.rmtree(temp_extract)
                    return False

                # Remove old addon
                shutil.rmtree(addon_dir)

                # Move new addon to addons directory
                shutil.move(extracted_addon, addon_dir)

                # Cleanup temp
                if os.path.exists(temp_extract):
                    shutil.rmtree(temp_extract)

            # Remove backup on success
            if backup_dir and os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)

            return True

        except Exception as e:
            self._error = f"Installation failed: {str(e)}"

            # Try to restore backup
            try:
                if backup_dir and os.path.exists(backup_dir):
                    if os.path.exists(addon_dir):
                        shutil.rmtree(addon_dir)
                    shutil.move(backup_dir, addon_dir)
            except Exception:
                pass

            return False

    def get_status_message(self) -> str:
        """Get human-readable status message."""
        if self._error:
            return f"Error: {self._error}"

        if self._update_available and self._latest_release:
            return f"Update available: v{self._latest_release.version_string}"

        if self._latest_release:
            return f"Up to date (v{CADHY_VERSION_STRING})"

        return "Update status unknown"


# Global updater instance
updater = AddonUpdater()
