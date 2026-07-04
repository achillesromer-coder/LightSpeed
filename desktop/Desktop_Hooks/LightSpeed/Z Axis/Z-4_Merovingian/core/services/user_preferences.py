"""
User Preferences Service
LightSpeed Type I Civilization Platform

Manages per-user settings and preferences including:
- Theme selection (dark, light, high contrast, custom)
- Font size and family
- Accent colors
- Widget layout
- Custom preferences

Each user's settings are isolated and persist across sessions.

Author: LightSpeed Team
Version: 0.9.5
Date: December 22, 2025

CODEX NOTE (2026-02-03):
- Runtime must not implicitly mutate DB schema. The `user_preferences` table is created by
  Trinity's explicit migration tool (`Z Axis/Z+3_Trinity/tools/initialize_database.py`) via
  the IT Portal approval flow. If the table is missing, this service degrades to in-memory
  defaults and will not create tables.
"""

import json
from typing import Dict, Any, Optional

from .database import DatabaseService, get_db


class UserPreferences:
    """
    Per-user preferences management.

    Stores and retrieves user-specific UI and application settings.
    Settings are persisted in the database and applied on login.

    Usage:
        prefs = UserPreferences(user_id="nathaniel.bouwer")
        prefs.set_theme("dark")
        theme = prefs.get_theme()  # Returns "dark"

        # Apply to UI
        prefs.apply_to_ui(root_window)
    """

    # Default preferences
    DEFAULTS = {
        "theme": "dark",
        "font_size": 10,
        "font_family": "Segoe UI",
        "accent_color": "#007acc",
        "widget_layout": None,  # JSON layout
        "show_tooltips": True,
        "enable_animations": True,
        "auto_save": True,
        "log_level": "INFO",
    }

    def __init__(self, user_id: str, db: Optional[DatabaseService] = None):
        """
        Initialize user preferences.

        Args:
            user_id: Unique user identifier
            db: Database service instance (optional, will use singleton)
        """
        self.user_id = user_id
        self.db = db or get_db()
        self._cache: Dict[str, Any] = {}

        self._warned_missing_table = False
        self.table_available = self._check_table()

    def _check_table(self) -> bool:
        """Check whether the `user_preferences` table exists (read-only)."""
        try:
            row = self.db.fetchone(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='user_preferences'",
                (),
            )
            return bool(row)
        except Exception:
            return False

    def _warn_missing_table_once(self) -> None:
        if self.table_available or self._warned_missing_table:
            return
        self._warned_missing_table = True
        try:
            print(
                "[UserPreferences] user_preferences table missing. "
                "Run Trinity migration tool: Z Axis/Z+3_Trinity/tools/initialize_database.py"
            )
        except Exception:
            pass

    def get_theme(self) -> str:
        """Get user's theme preference."""
        if "theme" in self._cache:
            return self._cache["theme"]

        if not self.table_available:
            self._warn_missing_table_once()
            theme = str(self.DEFAULTS["theme"])
            self._cache["theme"] = theme
            return theme

        result = self.db.fetchone(
            "SELECT theme FROM user_preferences WHERE user_id = ?",
            (self.user_id,),
        )
        theme = result[0] if result else self.DEFAULTS["theme"]
        self._cache["theme"] = theme
        return theme

    def set_theme(self, theme: str):
        """
        Set user's theme preference.

        Args:
            theme: Theme name ('dark', 'light', 'high_contrast', etc.)
        """
        self._cache["theme"] = theme
        if not self.table_available:
            self._warn_missing_table_once()
            return

        self.db.execute(
            """
            INSERT INTO user_preferences (user_id, theme, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                theme = excluded.theme,
                updated_at = CURRENT_TIMESTAMP
            """,
            (self.user_id, theme),
        )

    def get_font_size(self) -> int:
        """Get user's font size preference."""
        if "font_size" in self._cache:
            return int(self._cache["font_size"])

        if not self.table_available:
            self._warn_missing_table_once()
            size = int(self.DEFAULTS["font_size"])
            self._cache["font_size"] = size
            return size

        result = self.db.fetchone(
            "SELECT font_size FROM user_preferences WHERE user_id = ?",
            (self.user_id,),
        )
        font_size = result[0] if result else self.DEFAULTS["font_size"]
        self._cache["font_size"] = int(font_size)
        return int(font_size)

    def set_font_size(self, size: int):
        """
        Set user's font size preference.

        Args:
            size: Font size (8-18 recommended)
        """
        size = max(8, min(18, int(size)))
        self._cache["font_size"] = size

        if not self.table_available:
            self._warn_missing_table_once()
            return

        self.db.execute(
            """
            INSERT INTO user_preferences (user_id, font_size, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                font_size = excluded.font_size,
                updated_at = CURRENT_TIMESTAMP
            """,
            (self.user_id, size),
        )

    def get_font_family(self) -> str:
        """Get user's font family preference."""
        if "font_family" in self._cache:
            return str(self._cache["font_family"])

        if not self.table_available:
            self._warn_missing_table_once()
            family = str(self.DEFAULTS["font_family"])
            self._cache["font_family"] = family
            return family

        result = self.db.fetchone(
            "SELECT font_family FROM user_preferences WHERE user_id = ?",
            (self.user_id,),
        )
        font_family = result[0] if result else self.DEFAULTS["font_family"]
        self._cache["font_family"] = font_family
        return str(font_family)

    def set_font_family(self, family: str):
        """Set user's font family preference."""
        self._cache["font_family"] = family
        if not self.table_available:
            self._warn_missing_table_once()
            return

        self.db.execute(
            """
            INSERT INTO user_preferences (user_id, font_family, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                font_family = excluded.font_family,
                updated_at = CURRENT_TIMESTAMP
            """,
            (self.user_id, family),
        )

    def get_accent_color(self) -> str:
        """Get user's accent color preference."""
        if "accent_color" in self._cache:
            return str(self._cache["accent_color"])

        if not self.table_available:
            self._warn_missing_table_once()
            color = str(self.DEFAULTS["accent_color"])
            self._cache["accent_color"] = color
            return color

        result = self.db.fetchone(
            "SELECT accent_color FROM user_preferences WHERE user_id = ?",
            (self.user_id,),
        )
        accent_color = result[0] if result else self.DEFAULTS["accent_color"]
        self._cache["accent_color"] = accent_color
        return str(accent_color)

    def set_accent_color(self, color: str):
        """
        Set user's accent color preference.

        Args:
            color: Hex color code (e.g., "#007acc")
        """
        self._cache["accent_color"] = color
        if not self.table_available:
            self._warn_missing_table_once()
            return

        self.db.execute(
            """
            INSERT INTO user_preferences (user_id, accent_color, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                accent_color = excluded.accent_color,
                updated_at = CURRENT_TIMESTAMP
            """,
            (self.user_id, color),
        )

    def get_widget_layout(self) -> Optional[Dict[str, Any]]:
        """Get user's widget layout configuration."""
        if "widget_layout" in self._cache:
            return self._cache["widget_layout"]

        if not self.table_available:
            self._warn_missing_table_once()
            return None

        result = self.db.fetchone(
            "SELECT widget_layout FROM user_preferences WHERE user_id = ?",
            (self.user_id,),
        )

        if result and result[0]:
            try:
                layout = json.loads(result[0])
            except Exception:
                layout = None
            self._cache["widget_layout"] = layout
            return layout

        return None

    def set_widget_layout(self, layout: Dict[str, Any]):
        """
        Set user's widget layout configuration.

        Args:
            layout: Dictionary describing widget positions and sizes
        """
        self._cache["widget_layout"] = layout
        if not self.table_available:
            self._warn_missing_table_once()
            return

        layout_json = json.dumps(layout)
        self.db.execute(
            """
            INSERT INTO user_preferences (user_id, widget_layout, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                widget_layout = excluded.widget_layout,
                updated_at = CURRENT_TIMESTAMP
            """,
            (self.user_id, layout_json),
        )

    def clear_widget_layout(self):
        """Clear user's widget layout (set to NULL)."""
        self._cache.pop("widget_layout", None)
        if not self.table_available:
            self._warn_missing_table_once()
            return
        self.db.execute(
            """
            INSERT INTO user_preferences (user_id, widget_layout, updated_at)
            VALUES (?, NULL, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                widget_layout = NULL,
                updated_at = CURRENT_TIMESTAMP
            """,
            (self.user_id,),
        )

    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Get custom preference value.

        Args:
            key: Preference key
            default: Default value if not found

        Returns:
            Preference value or default
        """
        cache_key = f"custom_{key}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        if not self.table_available:
            self._warn_missing_table_once()
            return default

        result = self.db.fetchone(
            "SELECT preferences_json FROM user_preferences WHERE user_id = ?",
            (self.user_id,),
        )

        if result and result[0]:
            try:
                prefs = json.loads(result[0])
            except Exception:
                prefs = {}
            value = prefs.get(key, default) if isinstance(prefs, dict) else default
            self._cache[cache_key] = value
            return value

        return default

    def set_preference(self, key: str, value: Any):
        """
        Set custom preference value.

        Args:
            key: Preference key
            value: Preference value (must be JSON-serializable)
        """
        self._cache[f"custom_{key}"] = value
        if not self.table_available:
            self._warn_missing_table_once()
            return

        result = self.db.fetchone(
            "SELECT preferences_json FROM user_preferences WHERE user_id = ?",
            (self.user_id,),
        )

        try:
            prefs = json.loads(result[0]) if (result and result[0]) else {}
        except Exception:
            prefs = {}
        if not isinstance(prefs, dict):
            prefs = {}
        prefs[key] = value
        prefs_json = json.dumps(prefs)

        self.db.execute(
            """
            INSERT INTO user_preferences (user_id, preferences_json, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                preferences_json = excluded.preferences_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (self.user_id, prefs_json),
        )

    def get_all(self) -> Dict[str, Any]:
        """
        Get all user preferences.

        Returns:
            Dictionary of all preferences
        """
        if not self.table_available:
            self._warn_missing_table_once()
            return self.DEFAULTS.copy()

        result = self.db.fetchone(
            """
            SELECT theme, font_size, font_family, accent_color,
                   widget_layout, preferences_json
            FROM user_preferences WHERE user_id = ?
            """,
            (self.user_id,),
        )

        if not result:
            return self.DEFAULTS.copy()

        prefs: Dict[str, Any] = {
            "theme": result[0] or self.DEFAULTS["theme"],
            "font_size": result[1] or self.DEFAULTS["font_size"],
            "font_family": result[2] or self.DEFAULTS["font_family"],
            "accent_color": result[3] or self.DEFAULTS["accent_color"],
            "widget_layout": json.loads(result[4]) if result[4] else None,
        }

        if result[5]:
            try:
                custom = json.loads(result[5])
            except Exception:
                custom = {}
            if isinstance(custom, dict):
                prefs.update(custom)

        return prefs

    def reset_to_defaults(self):
        """Reset all preferences to defaults."""
        if not self.table_available:
            self._warn_missing_table_once()
            self._cache.clear()
            return

        self.db.execute(
            "DELETE FROM user_preferences WHERE user_id = ?",
            (self.user_id,),
        )
        self._cache.clear()

    def export_preferences(self) -> str:
        """
        Export preferences as JSON string.

        Returns:
            JSON string of all preferences
        """
        return json.dumps(self.get_all(), indent=2)

    def import_preferences(self, json_str: str):
        """
        Import preferences from JSON string.

        Args:
            json_str: JSON string of preferences
        """
        prefs = json.loads(json_str)

        if "theme" in prefs:
            self.set_theme(prefs["theme"])
        if "font_size" in prefs:
            self.set_font_size(prefs["font_size"])
        if "font_family" in prefs:
            self.set_font_family(prefs["font_family"])
        if "accent_color" in prefs:
            self.set_accent_color(prefs["accent_color"])
        if "widget_layout" in prefs:
            self.set_widget_layout(prefs["widget_layout"])

        for key, value in prefs.items():
            if key not in ["theme", "font_size", "font_family", "accent_color", "widget_layout"]:
                self.set_preference(key, value)

    def apply_to_ui(self, root):
        """
        Apply user preferences to UI root window.

        Args:
            root: tkinter root window

        Note: This requires theme and font systems to be available
        """
        # Apply theme (best-effort; may not exist in all runtimes)
        try:
            from core.ui.themes import apply_theme  # type: ignore

            theme = self.get_theme()
            apply_theme(root, theme)
        except Exception:
            pass

        # Apply font size
        font_size = self.get_font_size()
        font_family = self.get_font_family()

        try:
            import tkinter.font as tkfont

            default_font = tkfont.nametofont("TkDefaultFont")
            default_font.configure(family=font_family, size=font_size)

            text_font = tkfont.nametofont("TkTextFont")
            text_font.configure(family=font_family, size=font_size)
        except Exception:
            pass


# ============================================================================
# Global singleton cache
# ============================================================================

_user_prefs_cache: Dict[str, UserPreferences] = {}


def get_user_preferences(user_id: str) -> UserPreferences:
    """
    Get UserPreferences instance for user (singleton per user).

    Args:
        user_id: User identifier

    Returns:
        UserPreferences instance for the user
    """
    if user_id not in _user_prefs_cache:
        _user_prefs_cache[user_id] = UserPreferences(user_id)
    return _user_prefs_cache[user_id]


if __name__ == "__main__":
    # Test suite (requires DB schema to exist; does not create tables).
    print("=" * 70)
    print("USER PREFERENCES - Test Suite")
    print("=" * 70)

    prefs = UserPreferences("test_user")
    if not prefs.table_available:
        print("user_preferences table missing. Run Trinity initialize_database.py first.")
        raise SystemExit(2)

    print("\n[1] Theme Preferences")
    prefs.set_theme("light")
    print(f"  Set theme: light")
    print(f"  Get theme: {prefs.get_theme()}")

    print("\n[2] Font Preferences")
    prefs.set_font_size(12)
    prefs.set_font_family("Arial")
    print(f"  Font: {prefs.get_font_family()}, Size: {prefs.get_font_size()}")

    print("\n[3] Custom Preferences")
    prefs.set_preference("show_tooltips", False)
    prefs.set_preference("log_level", "DEBUG")
    print(f"  Tooltips: {prefs.get_preference('show_tooltips')}")
    print(f"  Log level: {prefs.get_preference('log_level')}")

    print("\n[4] Widget Layout")
    layout = {
        "dashboard": {
            "widgets": [
                {"type": "task", "x": 0, "y": 0, "w": 2, "h": 2},
                {"type": "metric", "x": 2, "y": 0, "w": 1, "h": 1},
            ]
        }
    }
    prefs.set_widget_layout(layout)
    loaded_layout = prefs.get_widget_layout()
    print(f"  Layout widgets: {len((loaded_layout or {}).get('dashboard', {}).get('widgets', []))}")

    print("\n[5] Export/Import")
    exported = prefs.export_preferences()
    print(f"  Exported {len(exported)} characters")

    prefs2 = UserPreferences("test_user_2")
    prefs2.import_preferences(exported)
