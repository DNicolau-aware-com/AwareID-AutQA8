"""
Small .env reader/writer used by services and fixtures.

This module provides thread-safe read/write operations for .env files
without polluting the system environment.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional, List

from dotenv import dotenv_values

logger = logging.getLogger(__name__)


class EnvStore:
    """
    Read/write helper for .env key-value pairs.
    
    Manages .env files independently of os.environ to support large values
    and avoid platform limitations.
    
    Example:
        store = EnvStore(Path(".env"))
        store.set("API_KEY", "abc123")
        api_key = store.get("API_KEY")
    """

    def __init__(self, env_path: Path | str):
        """
        Initialize EnvStore.
        
        Args:
            env_path: Path to the .env file
        """
        self.env_path = Path(env_path)

    def read(self) -> Dict[str, str]:
        """
        Read all key-value pairs from .env file.
        
        Returns:
            Dictionary of environment variables with stripped values
            
        Example:
            env = store.read()
            print(env.get("BASEURL"))
        """
        if not self.env_path.exists():
            logger.warning(f".env file not found: {self.env_path}")
            return {}
        
        try:
            raw = dotenv_values(self.env_path)
            return {k: (v or "").strip() for k, v in raw.items() if k}
        except Exception as e:
            logger.error(f"Failed to read .env file: {e}")
            return {}

    def get(self, key: str, default: str = "") -> str:
        """
        Get a single value from .env file.
        
        Args:
            key: Environment variable name
            default: Default value if key not found
        
        Returns:
            Value for the key, or default if not found
            
        Example:
            api_url = store.get("BASEURL", "https://default.api.com")
        """
        return self.read().get(key, default).strip()

    def set(self, key: str, value: str) -> None:
        """
        Set or update a key-value pair in .env file.
        
        Creates the file if it doesn't exist. Updates existing key or appends new one.
        
        Args:
            key: Environment variable name
            value: Value to set
            
        Example:
            store.set("ENROLLMENT_TOKEN", "xyz789")
        """
        if not key or not key.strip():
            raise ValueError("Key cannot be empty")
        
        key = key.strip()
        value = (value or "").strip()

        lines = []
        if self.env_path.exists():
            try:
                lines = self.env_path.read_text(encoding="utf-8").splitlines()
            except Exception as e:
                logger.error(f"Failed to read existing .env file: {e}")
                raise

        found = False
        out_lines = []
        for line in lines:
            # Skip empty lines and comments when looking for key
            if line.strip() and not line.strip().startswith("#"):
                if line.startswith(f"{key}="):
                    out_lines.append(f"{key}={value}")
                    found = True
                else:
                    out_lines.append(line)
            else:
                # Preserve comments and empty lines
                out_lines.append(line)

        if not found:
            out_lines.append(f"{key}={value}")

        try:
            self.env_path.parent.mkdir(parents=True, exist_ok=True)
            self.env_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
            logger.debug(f"Set {key} in {self.env_path}")
        except Exception as e:
            logger.error(f"Failed to write to .env file: {e}")
            raise

    def set_multiple(self, values: Dict[str, str]) -> None:
        """
        Set multiple key-value pairs at once (more efficient than multiple set() calls).
        
        Args:
            values: Dictionary of key-value pairs to set
            
        Example:
            store.set_multiple({
                "ENROLLMENT_TOKEN": "abc123",
                "AUTH_TOKEN": "xyz789",
                "USERNAME": "test_user"
            })
        """
        if not values:
            return
        
        lines = []
        if self.env_path.exists():
            lines = self.env_path.read_text(encoding="utf-8").splitlines()

        # Track which keys we've updated
        updated_keys = set()
        out_lines = []
        
        for line in lines:
            if line.strip() and not line.strip().startswith("#"):
                # Check if this line starts with any of our keys
                matched = False
                for key in values.keys():
                    if line.startswith(f"{key}="):
                        out_lines.append(f"{key}={values[key].strip()}")
                        updated_keys.add(key)
                        matched = True
                        break
                if not matched:
                    out_lines.append(line)
            else:
                out_lines.append(line)

        # Append any keys that weren't found
        for key, value in values.items():
            if key not in updated_keys:
                out_lines.append(f"{key}={value.strip()}")

        self.env_path.parent.mkdir(parents=True, exist_ok=True)
        self.env_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        logger.debug(f"Set {len(values)} keys in {self.env_path}")

    def delete(self, key: str) -> bool:
        """
        Delete a key from .env file.
        
        Args:
            key: Environment variable name to delete
        
        Returns:
            True if key was found and deleted, False otherwise
            
        Example:
            if store.delete("OLD_TOKEN"):
                print("Token removed")
        """
        if not self.env_path.exists():
            return False

        lines = self.env_path.read_text(encoding="utf-8").splitlines()
        out_lines = []
        found = False

        for line in lines:
            if line.startswith(f"{key}="):
                found = True
                # Skip this line (delete it)
            else:
                out_lines.append(line)

        if found:
            self.env_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
            logger.debug(f"Deleted {key} from {self.env_path}")
        
        return found

    def has_key(self, key: str) -> bool:
        """
        Check if a key exists in .env file.
        
        Args:
            key: Environment variable name
        
        Returns:
            True if key exists, False otherwise
            
        Example:
            if store.has_key("API_KEY"):
                api_key = store.get("API_KEY")
        """
        return key in self.read()

    def list_keys(self) -> List[str]:
        """
        Get list of all keys in .env file.
        
        Returns:
            List of environment variable names
            
        Example:
            keys = store.list_keys()
            print(f"Found {len(keys)} environment variables")
        """
        return list(self.read().keys())

    def clear(self) -> None:
        """
        Clear all content from .env file.
        
        WARNING: This removes all environment variables from the file.
        
        Example:
            store.clear()  # Empties the .env file
        """
        if self.env_path.exists():
            self.env_path.write_text("", encoding="utf-8")
            logger.warning(f"Cleared all content from {self.env_path}")

    def backup(self, backup_path: Optional[Path] = None) -> Path:
        """
        Create a backup of the .env file.
        
        Args:
            backup_path: Optional custom backup path. If None, uses .env.backup
        
        Returns:
            Path to the backup file
            
        Example:
            backup = store.backup()
            print(f"Backed up to {backup}")
        """
        if not self.env_path.exists():
            raise FileNotFoundError(f".env file not found: {self.env_path}")
        
        if backup_path is None:
            backup_path = self.env_path.with_suffix(".env.backup")
        else:
            backup_path = Path(backup_path)
        
        content = self.env_path.read_text(encoding="utf-8")
        backup_path.write_text(content, encoding="utf-8")
        logger.info(f"Backed up .env to {backup_path}")
        
        return backup_path

    def __repr__(self) -> str:
        """String representation of EnvStore."""
        return f"EnvStore(env_path={self.env_path})"