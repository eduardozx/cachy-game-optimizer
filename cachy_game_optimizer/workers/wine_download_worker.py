"""
CachyOS Game Optimizer - Wine/Proton Download Worker
Background thread for downloading and extracting Wine/Proton archives.
"""

import hashlib
import shutil
import tarfile
import requests
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal

from ..wine_downloader import ReleaseAsset, DownloadProgress


class WineDownloadWorker(QThread):
    """Worker thread for downloading and extracting Wine/Proton archives."""

    progress = pyqtSignal(object)  # DownloadProgress
    finished = pyqtSignal(bool, str)  # success, message
    log = pyqtSignal(str)

    def __init__(
        self,
        asset: ReleaseAsset,
        destination_dir: Path,
        verify_checksum: bool = True,
    ):
        super().__init__()
        self.asset = asset
        self.destination_dir = Path(destination_dir)
        self.verify_checksum = verify_checksum
        self._should_stop = False
        self._temp_file: Optional[Path] = None

    def stop(self):
        """Signal the worker to stop gracefully."""
        self._should_stop = True

    def run(self):
        try:
            self.destination_dir.mkdir(parents=True, exist_ok=True)

            # Download
            self.log.emit(f"⬇️ Downloading {self.asset.name}...")
            self._download()

            if self._should_stop:
                self.finished.emit(False, "Download cancelled")
                return

            # Verify checksum if available
            if self.verify_checksum:
                self.log.emit("🔍 Verifying checksum...")
                if not self._verify_checksum():
                    self.finished.emit(False, "Checksum verification failed")
                    return

            # Extract
            self.log.emit("📦 Extracting archive...")
            self._extract()

            if self._should_stop:
                self.finished.emit(False, "Extraction cancelled")
                return

            # Cleanup temp file
            if self._temp_file and self._temp_file.exists():
                self._temp_file.unlink()

            self.progress.emit(
                DownloadProgress(
                    release_tag="",
                    asset_name=self.asset.name,
                    downloaded=self.asset.size,
                    total=self.asset.size,
                    status="completed",
                )
            )
            self.finished.emit(True, f"Successfully installed to {self.destination_dir}")

        except Exception as e:
            self.log.emit(f"✗ Error: {e}")
            self.finished.emit(False, str(e))

    def _download(self):
        """Download the asset with progress reporting."""
        response = requests.get(self.asset.url, stream=True, timeout=300)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", self.asset.size))
        downloaded = 0

        # Use a temp file in the destination directory
        self._temp_file = self.destination_dir / f".tmp_{self.asset.name}"

        with open(self._temp_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if self._should_stop:
                    raise InterruptedError("Download cancelled")
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    self.progress.emit(
                        DownloadProgress(
                            release_tag="",
                            asset_name=self.asset.name,
                            downloaded=downloaded,
                            total=total_size,
                            status="downloading",
                        )
                    )

    def _verify_checksum(self) -> bool:
        """Verify SHA256 checksum if available in asset name or sidecar file."""
        # Check if there's a .sha256 or .sha256sum file alongside
        checksum_urls = [
            self.asset.url + ".sha256",
            self.asset.url + ".sha256sum",
            self.asset.url.replace(".tar.gz", ".sha256").replace(".tar.xz", ".sha256"),
        ]

        expected_hash = None
        for checksum_url in checksum_urls:
            try:
                resp = requests.get(checksum_url, timeout=10)
                if resp.status_code == 200:
                    # Parse checksum file (format: "hash  filename" or just "hash")
                    content = resp.text.strip()
                    expected_hash = content.split()[0]
                    break
            except Exception:
                continue

        if not expected_hash:
            self.log.emit("⚠ No checksum file found, skipping verification")
            return True

        # Calculate actual hash
        sha256 = hashlib.sha256()
        with open(self._temp_file, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        actual_hash = sha256.hexdigest()

        if actual_hash.lower() != expected_hash.lower():
            self.log.emit(f"✗ Checksum mismatch! Expected: {expected_hash}, Got: {actual_hash}")
            return False

        self.log.emit("✓ Checksum verified")
        return True

    def _extract(self):
        """Extract the downloaded archive."""
        # Determine extraction directory name from asset name
        # e.g., "Proton-9.0-GE-1.tar.gz" -> "Proton-9.0-GE-1"
        extract_name = self.asset.name
        for suffix in [".tar.gz", ".tar.xz", ".tar.zst", ".tgz", ".txz"]:
            if extract_name.endswith(suffix):
                extract_name = extract_name[: -len(suffix)]
                break

        extract_dir = self.destination_dir / extract_name

        # Remove existing directory if present
        if extract_dir.exists():
            shutil.rmtree(extract_dir)

        # Extract based on file type
        if self.asset.name.endswith((".tar.gz", ".tgz", ".tar.xz", ".txz", ".tar.zst")):
            with tarfile.open(self._temp_file, "r:*") as tar:
                # Security: prevent path traversal
                def is_safe_path(base: Path, target: Path) -> bool:
                    try:
                        target.resolve().relative_to(base.resolve())
                        return True
                    except ValueError:
                        return False

                for member in tar.getmembers():
                    if not is_safe_path(extract_dir, extract_dir / member.name):
                        raise SecurityError(f"Unsafe path in archive: {member.name}")

                tar.extractall(extract_dir)
        else:
            raise ValueError(f"Unsupported archive format: {self.asset.name}")

        self.log.emit(f"✓ Extracted to {extract_dir}")


class SecurityError(Exception):
    """Security violation during extraction."""

    pass