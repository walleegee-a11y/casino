"""
Configuration management for Treem Casino application.
Centralizes all settings, colors, and configuration options.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Tuple
from pathlib import Path


@dataclass
class ColorScheme:
    """Application color scheme configuration."""

    # Primary colors from original
    olive: str = "#778a35"
    sage_green: str = "#d1e2c4"
    pewter: str = "#ebebe8"
    olive_green: str = "#31352e"
    ivory: str = "#EBECE0"
    white: str = "#F7F8F8"

    # Accent colors
    dark_blue: str = "#051537"
    chili_pepper: str = "#BC3110"
    burnt_sienna: str = "#BE6310"
    blue_grotto: str = "#43B0F1"
    scarlet: str = "#88070B"
    ebony: str = "#32291C"
    tan: str = "#856536"

    # UI specific colors
    background: str = "#ebebe8"
    tree_background: str = "#F7F8F8"
    button_primary: str = "#778a35"
    button_secondary: str = "#d1e2c4"
    button_danger: str = "#88070B"
    button_warning: str = "#BC3110"

    # Text colors
    text_primary: str = "black"
    text_secondary: str = "#31352e"
    text_highlight: str = "brown"
    text_accent: str = "blue"
    text_pattern_match: str = "#045AB7"


@dataclass
class FontConfig:
    """Font configuration for the application."""

    primary_family: str = "Terminus"
    primary_size: int = 12
    secondary_size: int = 8

    def get_font_tuple(self, size: int = None) -> Tuple[str, int]:
        """Get font tuple for Qt font creation."""
        return (self.primary_family, size or self.primary_size)


@dataclass
class PathConfig:
    """Path configuration for the application."""

    def __post_init__(self):
        """Initialize paths from environment variables."""
        self.project_base = Path(os.getenv('casino_prj_base', ''))
        self.project_name = os.getenv('casino_prj_name', '')
        self.base_directory = self.project_base / self.project_name

        # Design environment variables
        self.design_ver = os.getenv('casino_design_ver', '')
        self.dk_ver = os.getenv('casino_dk_ver', '')
        self.tag = os.getenv('casino_tag', '')

        # Shared directory for memos
        self.shared_dir = self.project_base / "shared" if self.project_base else Path.home()
        self.memo_file = self.shared_dir / "directory_memos.yaml"


@dataclass
class UIConfig:
    """UI-specific configuration."""

    # Window settings
    default_width: int = 600
    default_height: int = 300
    minimum_width: int = 400
    minimum_height: int = 300

    # Tree view settings
    tree_minimum_height: int = 400
    max_directory_depth: int = 6
    initial_scan_depth: int = 3  # NEW: Only scan 3 levels initially for speed

    # Terminal settings
    terminal_geometry: str = "120x40"
    terminal_bg_color: str = "#0c0c1e"
    terminal_fg_color: str = "#e2e8f0"

    # Button sizes
    button_spacing: int = 5
    depth_button_width: int = 65

    # Timing
    blink_interval: int = 500
    file_watch_delay: int = 100

    # NEW: Performance settings
    fast_scan_mode: bool = True  # Skip expensive metadata checks during refresh
    lazy_load_metadata: bool = True  # Load metadata only when needed
    skip_empty_checks: bool = True  # Don't check if directories are empty

@dataclass
class AppConfig:
    """Main application configuration container."""

    colors: ColorScheme = field(default_factory=ColorScheme)
    fonts: FontConfig = field(default_factory=FontConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    ui: UIConfig = field(default_factory=UIConfig)

    # Application metadata
    app_name: str = "Treem Casino"
    version: str = "2.0.0"

    # Feature flags
    enable_async_operations: bool = True
    enable_search: bool = True
    enable_dark_mode: bool = False
    enable_plugins: bool = False

    def get_environment_pattern(self) -> str:
        """Get the environment pattern for highlighting."""
        if all([self.paths.design_ver, self.paths.dk_ver, self.paths.tag]):
            return f"{self.paths.design_ver}_{self.paths.dk_ver}_{self.paths.tag}"
        return ""

    def get_user_workspace_pattern(self) -> str:
        """Get the user workspace pattern."""
        import getpass
        return f"works_{getpass.getuser()}"

    def ensure_shared_directory(self) -> bool:
        """Ensure shared directory exists with proper permissions."""
        try:
            self.paths.shared_dir.mkdir(mode=0o775, parents=True, exist_ok=True)

            # Try to set group ownership if possible
            if self.paths.project_base.exists():
                try:
                    import stat
                    project_stat = self.paths.project_base.stat()
                    os.chown(
                        self.paths.shared_dir,
                        -1,
                        project_stat.st_gid
                    )
                except (OSError, AttributeError):
                    pass  # Ignore if we can't set group ownership

            return True
        except Exception as e:
            print(f"Warning: Could not create shared directory: {e}")
            return False


# Global configuration instance
config = AppConfig()
