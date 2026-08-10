"""Image discovery and wallpaper rotation logic."""

from __future__ import annotations

import os
import random
from typing import List, Optional, Sequence


class WallpaperController:
    """Maintains wallpaper pools from folders and/or individual image files."""

    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif"}

    def __init__(self) -> None:
        self.folders: List[str] = []
        self.files: List[str] = []
        self.images: List[str] = []
        self.index: int = 0
        self.preview_index: int = 0

    @property
    def image_count(self) -> int:
        return len(self.images)

    def load_folders(self, folders: List[str]) -> None:
        """Scan folders for supported images and rebuild the wallpaper pool."""
        self.load_sources(folders, [])

    def load_sources(
        self,
        folders: Sequence[str],
        files: Optional[Sequence[str]] = None,
    ) -> None:
        """Scan folders and include individual image files in the pool."""
        files = list(files or [])
        valid_folders = [folder for folder in folders if folder and os.path.isdir(folder)]
        valid_files: List[str] = []
        for path in files:
            if not path:
                continue
            abs_path = os.path.abspath(path)
            if not os.path.isfile(abs_path):
                continue
            _, extension = os.path.splitext(abs_path.lower())
            if extension in self.SUPPORTED_EXTENSIONS:
                valid_files.append(abs_path)

        if not valid_folders and not valid_files:
            raise FileNotFoundError(
                "No valid image folders or image files were provided."
            )

        found: List[str] = []
        missing_folders: List[str] = []

        for folder in valid_folders:
            if not os.path.isdir(folder):
                missing_folders.append(folder)
                continue

            for name in os.listdir(folder):
                _, extension = os.path.splitext(name.lower())
                if extension in self.SUPPORTED_EXTENSIONS:
                    found.append(os.path.abspath(os.path.join(folder, name)))

        for path in valid_files:
            if path not in found:
                found.append(path)

        if missing_folders and not found:
            raise FileNotFoundError(
                "Selected folders are missing or inaccessible: "
                + ", ".join(missing_folders)
            )

        if not found:
            raise ValueError(
                "No supported image files were found in the selected sources."
            )

        found.sort()
        self.folders = valid_folders
        self.files = valid_files
        self.images = found
        self.index = 0
        self.preview_index = 0

    def next_image(self, random_mode: bool) -> str:
        """Return the next wallpaper path according to the active mode."""
        if not self.images:
            raise RuntimeError("No wallpapers are loaded.")

        if random_mode:
            return random.choice(self.images)

        path = self.images[self.index]
        self.index = (self.index + 1) % len(self.images)
        return path

    def preview_at(self, index: int) -> Optional[str]:
        """Return the image path at a preview index, clamped to valid bounds."""
        if not self.images:
            return None
        self.preview_index = max(0, min(index, len(self.images) - 1))
        return self.images[self.preview_index]

    def step_preview(self, delta: int) -> Optional[str]:
        """Move the preview cursor and return the image path."""
        if not self.images:
            return None
        return self.preview_at(self.preview_index + delta)

    def sync_preview_to_path(self, image_path: str) -> None:
        """Align preview index with the currently applied wallpaper."""
        try:
            self.preview_index = self.images.index(image_path)
        except ValueError:
            pass
