"""
CachyOS Game Optimizer - Wine/Proton Downloader Service
Fetches releases from GitHub API for Proton-GE and Wine-GE with caching and rate limit handling.
"""

import json
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import threading


class ToolType(Enum):
    PROTON_GE = "proton-ge"
    WINE_GE = "wine-ge"


@dataclass
class ReleaseAsset:
    name: str
    url: str
    size: int
    content_type: str


@dataclass
class Release:
    tag_name: str
    name: str
    published_at: str
    body: str
    assets: List[ReleaseAsset]
    html_url: str
    prerelease: bool = False
    draft: bool = False


@dataclass
class DownloadProgress:
    release_tag: str
    asset_name: str
    downloaded: int
    total: int
    status: str  # "downloading", "extracting", "completed", "failed"
    error: str = ""


class WineProtonDownloader:
    """Service for fetching and downloading Wine/Proton releases from GitHub."""

    GITHUB_API_BASE = "https://api.github.com"
    REPOS = {
        ToolType.PROTON_GE: "GloriousEggroll/proton-ge-custom",
        ToolType.WINE_GE: "GloriousEggroll/wine-ge-custom",
    }

    # Cache file for offline/rate-limited scenarios
    CACHE_DIR = Path.home() / ".cache" / "cachy-game-optimizer"
    CACHE_FILE = CACHE_DIR / "wine_proton_releases.json"
    CACHE_TTL = 3600  # 1 hour

    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token
        self._cache: Dict[ToolType, List[Release]] = {}
        self._cache_timestamps: Dict[ToolType, float] = {}
        self._lock = threading.Lock()
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._load_cache()

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CachyOS-Game-Optimizer/1.0",
        }
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        return headers

    def _load_cache(self):
        """Load cached releases from disk."""
        if not self.CACHE_FILE.exists():
            return
        try:
            with open(self.CACHE_FILE, "r") as f:
                data = json.load(f)
            for tool_type_str, releases_data in data.items():
                tool_type = ToolType(tool_type_str)
                self._cache[tool_type] = [
                    Release(
                        tag_name=r["tag_name"],
                        name=r["name"],
                        published_at=r["published_at"],
                        body=r["body"],
                        assets=[ReleaseAsset(**a) for a in r["assets"]],
                        html_url=r["html_url"],
                        prerelease=r.get("prerelease", False),
                        draft=r.get("draft", False),
                    )
                    for r in releases_data
                ]
                self._cache_timestamps[tool_type] = data.get(f"_timestamp_{tool_type_str}", 0)
        except Exception:
            # Corrupted cache - ignore
            self._cache = {}
            self._cache_timestamps = {}

    def _save_cache(self):
        """Save releases to cache file."""
        try:
            data = {}
            for tool_type, releases in self._cache.items():
                data[tool_type.value] = [
                    {
                        "tag_name": r.tag_name,
                        "name": r.name,
                        "published_at": r.published_at,
                        "body": r.body,
                        "assets": [
                            {
                                "name": a.name,
                                "url": a.url,
                                "size": a.size,
                                "content_type": a.content_type,
                            }
                            for a in r.assets
                        ],
                        "html_url": r.html_url,
                        "prerelease": r.prerelease,
                        "draft": r.draft,
                    }
                    for r in releases
                ]
                data[f"_timestamp_{tool_type.value}"] = self._cache_timestamps.get(tool_type, 0)
            with open(self.CACHE_FILE, "w") as f:
                json.dump(data, f)
        except Exception:
            pass  # Cache write failure is non-fatal

    def _is_cache_valid(self, tool_type: ToolType) -> bool:
        """Check if cache is still valid."""
        if tool_type not in self._cache_timestamps:
            return False
        return (time.time() - self._cache_timestamps[tool_type]) < self.CACHE_TTL

    def fetch_releases(
        self,
        tool_type: ToolType,
        force_refresh: bool = False,
        max_releases: int = 20,
    ) -> List[Release]:
        """
        Fetch releases from GitHub API with caching and rate limit handling.
        Returns cached data if API fails.
        """
        with self._lock:
            # Return valid cache if available and not forced
            if not force_refresh and self._is_cache_valid(tool_type) and tool_type in self._cache:
                return self._cache[tool_type][:max_releases]

        repo = self.REPOS[tool_type]
        url = f"{self.GITHUB_API_BASE}/repos/{repo}/releases"

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                params={"per_page": max_releases},
                timeout=15,
            )

            # Handle rate limiting
            if response.status_code == 403:
                remaining = response.headers.get("X-RateLimit-Remaining", "0")
                reset_time = response.headers.get("X-RateLimit-Reset", "0")
                if remaining == "0":
                    wait_time = max(int(reset_time) - int(time.time()), 60)
                    raise RateLimitError(
                        f"GitHub API rate limit exceeded. Try again in {wait_time} seconds.",
                        reset_time=int(reset_time),
                    )
                raise GitHubAPIError(f"GitHub API forbidden: {response.text}")

            if response.status_code == 404:
                raise GitHubAPIError(f"Repository not found: {repo}")

            response.raise_for_status()
            data = response.json()

            releases = []
            for item in data:
                if item.get("draft"):
                    continue
                assets = [
                    ReleaseAsset(
                        name=a["name"],
                        url=a["browser_download_url"],
                        size=a["size"],
                        content_type=a.get("content_type", ""),
                    )
                    for a in item.get("assets", [])
                    if a["name"].endswith((".tar.gz", ".tar.xz", ".tar.zst"))
                ]
                if not assets:
                    continue  # Skip releases without valid archives
                releases.append(
                    Release(
                        tag_name=item["tag_name"],
                        name=item["name"] or item["tag_name"],
                        published_at=item["published_at"],
                        body=item.get("body", "") or "",
                        assets=assets,
                        html_url=item["html_url"],
                        prerelease=item.get("prerelease", False),
                        draft=item.get("draft", False),
                    )
                )

            # Update cache
            with self._lock:
                self._cache[tool_type] = releases
                self._cache_timestamps[tool_type] = time.time()
                self._save_cache()

            return releases

        except RateLimitError:
            raise
        except GitHubAPIError:
            raise
        except requests.RequestException as e:
            # Network error - return stale cache if available
            with self._lock:
                if tool_type in self._cache and self._cache[tool_type]:
                    return self._cache[tool_type][:max_releases]
            raise NetworkError(f"Failed to fetch releases: {e}")

    def get_latest_release(self, tool_type: ToolType) -> Optional[Release]:
        """Get the latest non-prerelease release."""
        releases = self.fetch_releases(tool_type)
        for r in releases:
            if not r.prerelease:
                return r
        return releases[0] if releases else None

    def find_asset(self, release: Release, arch: str = "x86_64") -> Optional[ReleaseAsset]:
        """Find the best matching asset for architecture."""
        # Priority: x86_64 > generic > others
        for asset in release.assets:
            if arch in asset.name:
                return asset
        for asset in release.assets:
            if "x86_64" not in asset.name and "amd64" not in asset.name:
                return asset
        return release.assets[0] if release.assets else None


class GitHubAPIError(Exception):
    """GitHub API returned an error."""

    pass


class RateLimitError(GitHubAPIError):
    """GitHub API rate limit exceeded."""

    def __init__(self, message: str, reset_time: int = 0):
        super().__init__(message)
        self.reset_time = reset_time


class NetworkError(Exception):
    """Network connectivity error."""

    pass


def format_changelog(body: str, max_lines: int = 10) -> str:
    """Format release body into a simplified changelog."""
    if not body:
        return "No changelog available."
    lines = []
    for line in body.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Keep bullet points, version headers, and significant lines
        if line.startswith(("-", "*", "•", "##", "###")) or len(line) > 20:
            lines.append(line)
        if len(lines) >= max_lines:
            break
    return "\n".join(lines) if lines else "No significant changes listed."


def format_file_size(size_bytes: int) -> str:
    """Format file size human-readable."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"