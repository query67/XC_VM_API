import requests
import re
from typing import List, Optional, Dict
import logging
import time

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitHubReleases:
    def __init__(self, owner: str, repo: str, token: Optional[str] = None):
        """
        Initialize a GitHubReleases instance for accessing release data of a GitHub repository.

        Args:
            owner (str): Repository owner (e.g., "Vateron-Media").
            repo (str): Repository name (e.g., "XC_VM").
            token (Optional[str]): GitHub API token for authentication (optional).

        Example:
            >>> repo = GitHubReleases("Vateron-Media", "XC_VM", token="ghp_...")
        """
        self.owner = owner
        self.repo = repo
        self.api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
        self.headers = {"Authorization": f"token {token}"} if token else {}
        self.timeout = 5  # Request timeout in seconds
        self._cache: Optional[Dict] = None  # Cache for release data
        self._cache_timestamp: Optional[float] = None  # Timestamp of last cache update
        self._cache_ttl: float = 1800  # Cache TTL in seconds (30 minutes)

    def clear_cache(self) -> None:
        """
        Clear the cached release data to force a new API request.

        Example:
            >>> repo = GitHubReleases("Vateron-Media", "XC_VM")
            >>> repo.clear_cache()
        """
        self._cache = None
        self._cache_timestamp = None
        logger.info(f"Cache cleared for {self.owner}/{self.repo}")

    def _is_cache_valid(self) -> bool:
        """
        Check if the cache is still valid based on TTL.

        Returns:
            bool: True if cache is valid, False otherwise.
        """
        if self._cache is None or self._cache_timestamp is None:
            return False
        return (time.time() - self._cache_timestamp) < self._cache_ttl

    def get_releases(self) -> List[str]:
        """
        Fetch all release versions (tags) from the GitHub repository, using cache if valid.

        Returns:
            List[str]: A list of version tags in descending order (latest first).

        Raises:
            requests.exceptions.RequestException: If the request fails.

        Example:
            >>> repo = GitHubReleases("Vateron-Media", "XC_VM")
            >>> repo.get_releases()
            ['v1.0.2', 'v1.0.1', 'v1.0.0']
        """
        if self._is_cache_valid():
            logger.info(f"Using cached releases for {self.owner}/{self.repo}")
            releases = [
                release.get("tag_name", "")
                for release in self._cache
                if release.get("tag_name")
            ]
            return releases

        try:
            response = requests.get(
                self.api_url, headers=self.headers, timeout=self.timeout
            )
            response.raise_for_status()
            self._cache = response.json()
            self._cache_timestamp = time.time()
            releases = [
                release.get("tag_name", "")
                for release in self._cache
                if release.get("tag_name")
            ]
            logger.info(
                f"Retrieved and cached {len(releases)} releases from {self.owner}/{self.repo}"
            )
            return releases
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch releases: {e}")
            raise

    def get_latest_version(self) -> Optional[str]:
        """
        Get the latest release version (based on the order returned by GitHub).

        Returns:
            Optional[str]: The latest version tag, or None if no releases exist.

        Example:
            >>> repo = GitHubReleases("Vateron-Media", "XC_VM")
            >>> repo.get_latest_version()
            'v1.0.2'
        """
        releases = self.get_releases()
        return releases[0] if releases else None

    def get_next_version(self, current_version: str) -> Optional[str]:
        """
        Get the next version tag that comes after the specified current version.

        Args:
            current_version (str): The current version tag (e.g., "v1.0.0").

        Returns:
            Optional[str]: The next version tag, or None if it's the latest or not found.

        Example:
            >>> repo = GitHubReleases("Vateron-Media", "XC_VM")
            >>> repo.get_next_version("v1.0.0")
            'v1.0.1'
        """
        releases = self.get_releases()
        if current_version not in releases:
            logger.warning(f"Version {current_version} not found in releases")
            return None
        index = releases.index(current_version)
        return releases[index - 1] if index > 0 else None

    def get_asset_hash(
        self, version: str, asset_name: str, hash_file_suffix: str = ".md5"
    ) -> Optional[str]:
        """
        Retrieve the MD5 hash of a release asset from its corresponding hash file.

        This method looks for a plain text file named with the asset file name plus a suffix
        (e.g., "update.tar.gz.md5" for "update.tar.gz"). The hash file must contain a single line
        with a valid 32-character MD5 hash.

        Args:
            version (str): The release tag (e.g., "v1.0.0").
            asset_name (str): The asset file name to get the hash for (e.g., "update.tar.gz").
            hash_file_suffix (str): The suffix appended to the asset name to form the hash file name. Default is ".md5".

        Returns:
            Optional[str]: The MD5 hash string, or None if not found or invalid.

        Raises:
            requests.exceptions.RequestException: If the request fails.

        Example:
            >>> repo = GitHubReleases("Vateron-Media", "XC_VM")
            >>> repo.get_asset_hash("v1.0.0", "update.tar.gz")
            'd41d8cd98f00b204e9800998ecf8427e'
            >>> repo.get_asset_hash("v1.0.0", "update.tar.gz", hash_file_suffix=".hash")
            'd41d8cd98f00b204e9800998ecf8427e'
        """
        try:
            # Use cached data if valid
            if not self._is_cache_valid():
                response = requests.get(
                    self.api_url, headers=self.headers, timeout=self.timeout
                )
                response.raise_for_status()
                self._cache = response.json()
                self._cache_timestamp = time.time()
                logger.info(f"Updated cache for {self.owner}/{self.repo}")
            releases = self._cache

            for release in releases:
                if release.get("tag_name") == version:
                    assets = release.get("assets", [])
                    hash_file_name = f"{asset_name}{hash_file_suffix}"

                    for asset in assets:
                        if asset.get("name") == hash_file_name:
                            hash_response = requests.get(
                                asset.get("browser_download_url"),
                                headers=self.headers,
                                timeout=self.timeout,
                            )
                            hash_response.raise_for_status()
                            hash_text = hash_response.text.strip()

                            if re.match(r"^[0-9a-fA-F]{32}$", hash_text):
                                logger.info(
                                    f"Retrieved MD5 hash for {asset_name} in version {version}"
                                )
                                return hash_text

                            logger.warning(
                                f"Invalid MD5 hash format in {hash_file_name} for version {version}"
                            )
                            return None

                    logger.warning(
                        f"Hash file {hash_file_name} not found for version {version}"
                    )
                    return None

            logger.warning(f"Version {version} not found")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch asset hash: {e}")
            return None

    def get_changelog(self, changelog_file_url: str) -> Dict:
        """
        Retrieve the changelog for all releases from changelog.json files in JSON format.

        Each release must include a changelog.json file in its assets, containing an array of strings
        with changes. Returns a JSON object with the structure:
        [{"version": "v1.0.0", "changes": ["change1", "change2"]}, ...].

        Args:
            changelog_file_url (str): Link to file with changelog.

        Returns:
            Dict: A JSON-compatible dictionary containing the changelog.

        Raises:
            requests.exceptions.RequestException: If the request fails.

        Example:
            >>> repo = GitHubReleases("Vateron-Media", "XC_VM")
            >>> repo.get_changelog()[
                {"version": "v1.0.2", "changes": ["Fixed bug X", "Added feature Y"]},
                {"version": "v1.0.1", "changes": ["Improved performance", "Updated docs"]},
                {"version": "v1.0.0", "changes": ["Initial release", "Added core features"]}
            ]
        """
        try:
            # Use cached data if valid
            if not self._is_cache_valid():
                response = requests.get(
                    self.api_url, headers=self.headers, timeout=self.timeout
                )
                response.raise_for_status()
                self._cache = response.json()
                self._cache_timestamp = time.time()
                logger.info(f"Updated cache for {self.owner}/{self.repo}")
            releases = self._cache

            response = requests.get(changelog_file_url, timeout=self.timeout)
            # Check status codes explicitly
            if response.status_code == 200:
                changelog = response.json()
                # Get list of valid release versions
                valid_versions = {release['tag_name'] for release in releases}
                # Filter changelog to only include entries with matching release versions
                filtered_changelog = [
                    entry for entry in changelog 
                    if entry.get('version') in valid_versions
                ]
                logger.info(
                    f"Successfully retrieved changelog with {len(filtered_changelog)} versions "
                    f"after filtering (original: {len(changelog)} versions)"
                )
                return filtered_changelog
            elif response.status_code == 404:
                logger.error("Changelog file not found (404)")
                return []
            elif response.status_code == 403:
                logger.error(
                    "Access forbidden (403) - Check API rate limits or permissions"
                )
                return []
            elif response.status_code == 500:
                logger.error("Server error (500) while fetching changelog")
                return []
            else:
                logger.error(f"Unexpected HTTP status code: {response.status_code}")
                return []

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Failed to fetch changelog: {e} (Status code: {response.status_code if 'response' in locals() else 'N/A'})"
            )
            return []
        
    @staticmethod
    def is_valid_version(version: str) -> bool:
        """
        Validate whether a version string follows the format vX.Y.Z.

        Args:
            version (str): The version string to validate (e.g., "v1.0.0").

        Returns:
            bool: True if valid, False otherwise.

        Raises:
            ValueError: If the version string is too long or contains invalid parts.

        Example:
            >>> GitHubReleases.is_valid_version("v1.0.0")
            True
            >>> GitHubReleases.is_valid_version("v1.0")
            False
            >>> GitHubReleases.is_valid_version("v01.0.0")
            False
        """
        if not isinstance(version, str):
            logger.error("Version must be a string")
            return False

        if len(version) > 20:
            logger.error("Version string too long")
            raise ValueError("Version string is too long")

        pattern = r"^v[0-9]+\.[0-9]+\.[0-9]+$"
        if not re.match(pattern, version):
            logger.warning(f"Invalid version format: {version}")
            return False

        try:
            parts = version[1:].split(".")
            if len(parts) != 3:
                logger.warning(f"Version must have three parts: {version}")
                return False

            for part in parts:
                num = int(part)
                if num < 0:
                    logger.warning(
                        f"Negative numbers are not allowed in version: {version}"
                    )
                    return False
                if part.startswith("0") and len(part) > 1:
                    logger.warning(
                        f"Leading zeros are not allowed in version: {version}"
                    )
                    return False

            return True
        except ValueError as e:
            logger.error(f"Error parsing version {version}: {e}")
            return False


if __name__ == "__main__":
    repo = GitHubReleases("Vateron-Media", "XC_VM")

    print("📦 Latest version:", repo.get_latest_version())

    current = "v1.0.0"
    next_version = repo.get_next_version(current)
    print(f"🔁 Next version after {current}:", next_version)

    hash_value = repo.get_asset_hash("v1.0.0", "update.tar.gz")
    print("🔑 Resource hash:", hash_value)

    notes = repo.get_changelog("https://raw.githubusercontent.com/Vateron-Media/XC_VM_Update/refs/heads/main/changelog.json")
    print("📝 Release notes:", notes)
