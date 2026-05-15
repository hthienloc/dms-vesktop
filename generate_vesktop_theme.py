#!/usr/bin/env python3
"""
Generate a standalone Discord theme for Vesktop (Linux) based on Dank Material Shell colors.
Uses dynamic attribute selectors and specific overrides for guilds and user areas.
"""

import json
import subprocess
import os
import pathlib
from pathlib import Path
from typing import Dict, Any

# Default Material Design colors (fallback)
DEFAULT_COLORS = {
    "primary": "#d3bcfd",
    "background": "#151218",
    "surface": "#151218",
    "error": "#ffb4ab",
    "success": "#7efd99",
    "warning": "#ffda72",
    "text": "#f5efff",
    "text_secondary": "#cbc4cf",
    "wallpaper": "",
}

# --- THEME SETTINGS ---
# Change this to False if you want a solid color background without glassmorphism
ENABLE_TRANSPARENCY = False

# GNOME accent name to hex

GNOME_ACCENT_MAP = {
    "purple": "#9b59b6",
    "blue": "#3498db",
    "green": "#2ecc71",
    "yellow": "#f1c40f",
    "orange": "#e67e22",
    "red": "#e74c3c",
    "pink": "#ff69b4",
    "brown": "#8e44ad",
    "light blue": "#87cefa",
    "lavender": "#e6e6fa",
}


def get_vesktop_themes_dir() -> Path:
    """Detect Vesktop themes directory on Linux."""
    home = Path.home()
    # Prefer Flatpak path (common)
    flatpak = home / ".var/app/dev.vencord.Vesktop/config/vesktop/themes"
    if flatpak.exists():
        return flatpak
    # Native installation
    native = home / ".config/vesktop/themes"
    native.mkdir(parents=True, exist_ok=True)
    return native


def get_author() -> str:
    """Try to get the author name from git or env."""
    try:
        return subprocess.check_output(["git", "config", "user.name"], text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return os.environ.get("USER", "Anonymous")


def get_colors_from_dms() -> Dict[str, str]:
    """Read colors and wallpaper from Dank Material Shell files."""
    colors = {}
    
    # 1. Try colors from cache
    colors_file = Path.home() / ".cache" / "DankMaterialShell" / "dms-colors.json"
    if colors_file.exists():
        try:
            data = json.loads(colors_file.read_text(encoding="utf-8"))
            dark_colors = data.get("colors", {}).get("dark", {})
            if dark_colors:
                colors["primary"] = dark_colors.get("primary")
                colors["background"] = dark_colors.get("background")
                colors["surface"] = dark_colors.get("surface_container")
                colors["error"] = dark_colors.get("error")
                colors["text"] = dark_colors.get("on_surface")
                colors["text_secondary"] = dark_colors.get("on_surface_variant")
        except Exception as e:
            print(f"⚠️ Error reading dms-colors.json: {e}")

    # 2. Try wallpaper from session state
    session_file = Path.home() / ".local" / "state" / "DankMaterialShell" / "session.json"
    if session_file.exists():
        try:
            data = json.loads(session_file.read_text(encoding="utf-8"))
            wp = data.get("wallpaperPath")
            if wp:
                colors["wallpaper"] = wp
        except Exception as e:
            print(f"⚠️ Error reading session.json: {e}")

    return {k: v for k, v in colors.items() if v}


def get_colors_from_gsettings() -> Dict[str, str]:
    """Fallback: query gsettings for colors and wallpaper."""
    colors = {}
    try:
        # Accent color
        accent = subprocess.check_output(
            ["gsettings", "get", "org.gnome.desktop.interface", "accent-color"],
            text=True
        ).strip().strip("'")
        if accent in GNOME_ACCENT_MAP:
            colors["primary"] = GNOME_ACCENT_MAP[accent]

        # Wallpaper
        wallpaper = subprocess.check_output(
            ["gsettings", "get", "org.gnome.desktop.background", "picture-uri-dark"],
            text=True
        ).strip().strip("'")
        if not wallpaper or wallpaper == 'none':
            wallpaper = subprocess.check_output(
                ["gsettings", "get", "org.gnome.desktop.background", "picture-uri"],
                text=True
            ).strip().strip("'")
        
        if wallpaper and wallpaper.startswith("file://"):
            colors["wallpaper"] = wallpaper.replace("file://", "")

    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return colors


def merge_colors(*dicts: Dict[str, str]) -> Dict[str, str]:
    """Merge multiple color dicts, later ones override earlier."""
    result = DEFAULT_COLORS.copy()
    for d in dicts:
        result.update(d)
    return result


def hex_to_rgb(hex_color: str) -> str:
    """Helper to convert hex to comma-separated RGB."""
    if not isinstance(hex_color, str) or not hex_color.startswith('#'):
        return "0, 0, 0"
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c*2 for c in hex_color)
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r}, {g}, {b}"
    except (ValueError, IndexError):
        return "0, 0, 0"


def adjust_brightness(hex_color: str, factor: float) -> str:
    """Darken or lighten a hex color."""
    if not isinstance(hex_color, str) or not hex_color.startswith('#'):
        return hex_color
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c*2 for c in hex_color)
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = min(255, max(0, int(r * factor)))
        g = min(255, max(0, int(g * factor)))
        b = min(255, max(0, int(b * factor)))
        return f"#{r:02x}{g:02x}{b:02x}"
    except (ValueError, IndexError):
        return f"#{hex_color}"


def generate_full_theme_css(colors: Dict[str, str], author: str) -> str:
    """Generate complete CSS theme with robust attribute selectors."""
    primary = colors.get("primary", DEFAULT_COLORS["primary"])
    hover = adjust_brightness(primary, 0.8)
    bg_main = colors.get("background", DEFAULT_COLORS["background"])
    bg_secondary = colors.get("surface", DEFAULT_COLORS["surface"])
    text_normal = colors.get("text", DEFAULT_COLORS["text"])
    text_muted = colors.get("text_secondary", DEFAULT_COLORS["text_secondary"])
    wallpaper_path = colors.get("wallpaper", "")

    # Properly format wallpaper URI
    if wallpaper_path and ENABLE_TRANSPARENCY:
        wallpaper_uri = pathlib.Path(wallpaper_path).as_uri()
    else:
        wallpaper_uri = ""

    bg_opacity = "0.75" if wallpaper_uri else "1.0"
    backdrop_blur = "24px" if wallpaper_uri else "0px"
    
    bg_secondary_alt = adjust_brightness(bg_secondary, 0.9)
    bg_tertiary = adjust_brightness(bg_main, 0.8)

    floating_opacity = "0.85" if ENABLE_TRANSPARENCY else "1.0"
    textarea_bg = "0.2" if ENABLE_TRANSPARENCY else "0.4"
    textarea_hover = "0.3" if ENABLE_TRANSPARENCY else "0.5"

    t_guilds = "background-color: rgba(0, 0, 0, 0.2) !important;" if ENABLE_TRANSPARENCY else "background-color: var(--dank-bg-main) !important;"
    t_sidebar = "background-color: rgba(0, 0, 0, 0.25) !important;" if ENABLE_TRANSPARENCY else "background-color: var(--dank-bg-main) !important;"
    t_panels = "background-color: rgba(0, 0, 0, 0.3) !important;" if ENABLE_TRANSPARENCY else "background-color: var(--dank-bg-main) !important;"
    t_transparent = "background: transparent !important;" if ENABLE_TRANSPARENCY else "background-color: transparent !important;"
    t_chat = "background-color: rgba(0, 0, 0, 0.1) !important;" if ENABLE_TRANSPARENCY else "background-color: var(--dank-bg-main) !important;"
    t_input = f"background-color: rgba({hex_to_rgb(bg_main)}, 0.6) !important;" if ENABLE_TRANSPARENCY else "background-color: var(--dank-bg-main) !important;"
    t_blur = "backdrop-filter: blur(12px);" if ENABLE_TRANSPARENCY else ""
    t_blur_heavy = "backdrop-filter: blur(16px);" if ENABLE_TRANSPARENCY else ""
    t_border = "border: 1px solid rgba(255, 255, 255, 0.1);" if ENABLE_TRANSPARENCY else ""
    t_border_soft = "border: 1px solid rgba(255, 255, 255, 0.05);" if ENABLE_TRANSPARENCY else ""

    css = f"""/**
 * @name Dank Material
 * @author {author}
 * @version 1.4.0
 * @description Modern Material theme generated from Dank Material Shell colors
 * @source https://github.com/loccun/dms-vesktop
 */

:root {{
  /* Material Design 3 inspired tokens */
  --dank-primary: {primary};
  --dank-primary-hover: {hover};
  --dank-bg-main: {bg_main};
  --dank-bg-secondary: {bg_secondary};
  --dank-bg-secondary-alt: {bg_secondary_alt};
  --dank-bg-tertiary: {bg_tertiary};
  --dank-text-normal: {text_normal};
  --dank-text-muted: {text_muted};
  
  --dank-wallpaper: url("{wallpaper_uri}");
  --dank-bg-opacity: {bg_opacity};
  --dank-blur: {backdrop_blur};
  
  --radius-xl: 20px;
  --radius-l: 14px;
  --radius-m: 10px;
}}
"""

    css += f"""
/* App Background - The Foundation */
#app-mount,
[class^="bg_"],
[class^="appMount_"] {{
"""
    if ENABLE_TRANSPARENCY:
        css += f"""  background-image: var(--dank-wallpaper) !important;
  background-position: center !important;
  background-size: cover !important;
  background-attachment: fixed !important;
  background-color: transparent !important;
}}
"""
    else:
        css += f"""  background-color: var(--dank-bg-main) !important;
  background-image: none !important;
}}
"""

    if ENABLE_TRANSPARENCY:
        css += f"""
/* Global Transparency - Making every possible layer transparent */
:is(html, body, #app-mount),
[class^="app_"],
[class^="bg_"],
[class^="layer_"],
[class^="container_"],
[class^="guilds_"],
[class^="sidebar_"],
[class^="sidebarRegion_"],
[class^="chat_"],
[class^="members_"],
[class^="content_"],
[class^="scrollableContainer_"],
[class^="channelTextArea_"],
[class^="standardSidebarView_"],
[class^="contentRegion_"],
[class^="contentRegionScroller_"],
[class^="wrapper_"],
[class^="scroller_"],
[class^="privateChannels_"],
[class^="panels_"],
[class^="root_"],
[class^="container_"] > [class^="nav_"] {{
  background-color: transparent !important;
  background: transparent !important;
}}

/* Main App Container Glassmorphism Overlay */
[class^="app_"] {{
  background-color: rgba(0, 0, 0, 0.15) !important;
  backdrop-filter: blur(var(--dank-blur));
}}
"""

    if ENABLE_TRANSPARENCY:
        bg_primary_val = f"rgba({hex_to_rgb(bg_main)}, var(--dank-bg-opacity))"
        bg_secondary_val = f"rgba({hex_to_rgb(bg_secondary)}, var(--dank-bg-opacity))"
        bg_secondary_alt_val = f"rgba({hex_to_rgb(bg_secondary_alt)}, var(--dank-bg-opacity))"
        bg_tertiary_val = f"rgba({hex_to_rgb(bg_tertiary)}, var(--dank-bg-opacity))"
        bg_floating_val = f"rgba({hex_to_rgb(bg_secondary)}, {floating_opacity})"
    else:
        bg_primary_val = "var(--dank-bg-main)"
        bg_secondary_val = "var(--dank-bg-secondary)"
        bg_secondary_alt_val = "var(--dank-bg-secondary-alt)"
        bg_tertiary_val = "var(--dank-bg-tertiary)"
        bg_floating_val = "var(--dank-bg-secondary)"

    css += f"""
/* ===== Discord Theme Variables - Full Override ===== */
.theme-dark {{
  /* Classic background vars */
  --background-primary: {bg_primary_val};
  --background-secondary: {bg_secondary_val};
  --background-secondary-alt: {bg_secondary_alt_val};
  --background-tertiary: {bg_tertiary_val};
  --background-floating: {bg_floating_val};
  --background-nested-floating: {bg_floating_val};
  --background-accent: {bg_secondary_val};

  /* Newer bg-overlay/bg-surface vars (Discord rebrand) */
  --bg-overlay-chat: {bg_primary_val};
  --bg-overlay-app-frame: {bg_tertiary_val};
  --bg-overlay-3: {bg_primary_val};
  --bg-overlay-6: {bg_secondary_val};
  --bg-base-primary: {bg_primary_val};
  --bg-base-secondary: {bg_secondary_val};
  --bg-base-tertiary: {bg_tertiary_val};

  /* bg-surface-* (latest Discord design tokens) */
  --bg-surface-raised: {bg_secondary_val};
  --bg-surface-overlay: {bg_floating_val};
  --bg-surface-overlay-higher: {bg_floating_val};

  /* Brand */
  --brand-experiment: var(--dank-primary);
  --brand-experiment-560: var(--dank-primary);
  --brand-500: var(--dank-primary);
  --brand-360: var(--dank-primary);

  /* Text */
  --text-normal: var(--dank-text-normal);
  --text-muted: var(--dank-text-muted);
  --header-primary: var(--dank-text-normal);
  --header-secondary: var(--dank-text-muted);
  --interactive-normal: var(--dank-text-muted);
  --interactive-hover: var(--dank-text-normal);
  --interactive-active: var(--dank-primary);

  /* Background modifiers */
  --background-modifier-hover: rgba(255, 255, 255, 0.08);
  --background-modifier-active: rgba(255, 255, 255, 0.12);
  --background-modifier-selected: rgba(255, 255, 255, 0.16);
  --background-modifier-accent: rgba(255, 255, 255, 0.24);
  --background-mentioned: rgba({hex_to_rgb(primary)}, 0.15);
  --background-mentioned-hover: rgba({hex_to_rgb(primary)}, 0.25);
  --border-mentioned: rgba({hex_to_rgb(primary)}, 0.5);

  /* Input/textarea */
  --channeltextarea-background: rgba(0, 0, 0, {textarea_bg});
  --channeltextarea-background-hover: rgba(0, 0, 0, {textarea_hover});
  --input-background: {bg_secondary_val};
  --deprecated-panel-background: {bg_secondary_val};
  --deprecated-panel-header-background: {bg_secondary_val};
  --deprecated-text-input-bg: {bg_secondary_val};

  /* Scrollbar */
  --scrollbar-auto-thumb: var(--dank-primary);
  --scrollbar-auto-track: transparent;
  --scrollbar-thin-thumb: var(--dank-primary);
  --scrollbar-thin-track: transparent;
}}

/* --- Solid Mode: Force Uniform Background on ALL layout containers --- */
/* bg_ is intentionally excluded to avoid hiding server icon background images */
[class*="app_"],
[class*="layers_"],
[class*="layer_"],
[class*="chat_"],
[class*="content_"],
[class*="container_"]:not([class*="containerWithMargin_"]),
[class*="base_"],
[class*="layout_"],
[class*="scrollerBase_"],
[class*="scroller_"],
[class*="stack_"],
[class*="itemsContainer_"],
[class*="tutorialContainer_"],
[class*="listItem_"],
[class*="listItemWrapper_"],
[class*="standardSidebarView_"],
[class*="contentRegion_"],
[class*="contentRegionScroller_"],
[class*="privateChannels_"],
[class*="sidebarRegion_"],
[class*="memberSidebarSection_"],
[class*="memberContainer_"],
[class*="containerCompact_"],
[class*="textContainer_"],
[class*="messageContainer_"],
[class*="contentContainer_"],
[class*="exampleMessage_"],
[class*="root_"] {{
  {t_guilds}
}}

/* --- Accessibility: Buttons (actual <button> elements only) --- */
/* interactive_ and clickable_ intentionally excluded:
   they match DM/channel list rows, NOT real buttons. */
button[class*="button_"] {{
  border-radius: var(--radius-m) !important;
  transition: background-color 0.15s ease !important;
}}

/* lookBlank + colorBrand = icon-only buttons (Mute, Deafen, Settings, etc.)
   Use transparent (1st surface) so they blend with the uniform background. */
button[class*="button_"][class*="lookBlank_"],
button[class*="button_"][class*="lookGhost_"],
button[class*="button_"][class*="colorGrey_"],
button[class*="button_"][class*="colorWhite_"] {{
  background-color: transparent !important;
}}
button[class*="button_"][class*="lookBlank_"]:hover,
button[class*="button_"][class*="lookGhost_"]:hover,
button[class*="button_"][class*="colorGrey_"]:hover,
button[class*="button_"][class*="colorWhite_"]:hover {{
  background-color: rgba(255, 255, 255, 0.1) !important;
}}

/* lookFilled + colorBrand = real CTA buttons (Save, Login, Join, etc.) */
button[class*="button_"][class*="lookFilled_"][class*="colorBrand_"],
button[class*="button_"][class*="lookFilled_"][class*="colorBrand_"] [class*="contents_"],
button[class*="button_"][class*="lookFilled_"][class*="colorBrand_"] [class*="label_"],
[class*="lookFilled_"][class*="colorBrand_"] {{
  background-color: var(--dank-primary) !important;
  color: #100e13 !important;
}}
button[class*="button_"][class*="lookFilled_"][class*="colorBrand_"]:hover,
[class*="lookFilled_"][class*="colorBrand_"]:hover {{
  background-color: var(--dank-primary-hover) !important;
}}

/* Destructive buttons */
button[class*="button_"][class*="colorRed_"],
button[class*="button_"][class*="colorDanger_"],
button[class*="button_"][class*="colorRed_"] [class*="contents_"],
button[class*="button_"][class*="colorDanger_"] [class*="contents_"],
button[class*="button_"][class*="colorRed_"] [class*="label_"],
button[class*="button_"][class*="colorDanger_"] [class*="label_"] {{
  background-color: #f04747 !important;
  color: #ffffff !important;
}}

/* Secondary / Primary (Grey) buttons - e.g. Reply */
button[class*="button_"][class*="lookFilled_"][class*="colorPrimary_"],
button[class*="button_"][class*="lookFilled_"][class*="colorGrey_"],
button[class*="button_"][class*="lookFilled_"][class*="colorPrimary_"] [class*="contents_"],
button[class*="button_"][class*="lookFilled_"][class*="colorPrimary_"] [class*="label_"] {{
  background-color: rgba(255, 255, 255, 0.1) !important;
  color: #ffffff !important;
}}
button[class*="button_"][class*="lookFilled_"][class*="colorPrimary_"]:hover,
button[class*="button_"][class*="lookFilled_"][class*="colorGrey_"]:hover {{
  background-color: rgba(255, 255, 255, 0.15) !important;
}}

/* Channel/DM list rows - reset to transparent, hover via Discord's native var */
[class*="linkButton_"] {{
  background-color: transparent !important;
  border-radius: var(--radius-m) !important;
}}
/* Selected/active state for channel rows */
[class*="interactiveSelected_"] {{
  background-color: rgba(255, 255, 255, 0.1) !important;
}}

/* --- UI Panels Polishing --- */

/* Server List (Guilds) */
[class^="guilds_"] {{
  {t_guilds}
  margin: 8px 0 8px 8px;
  border-radius: var(--radius-l);
}}

/* Guild nav inner scroller and all sub-elements — must match main bg.
   Key classes identified from Discord's live DOM:
   - scroller_ef3116 / scrollerBase_d125d2: the server list scroller
   - listItem__650eb: each server row wrapper
   - wrapper__58105 / overlay__58105: the pill/indicator overlay
   - blobContainer_e5445c: SVG blob wrapper (note capital C, not caught by container_)
   - childWrapper__6e9f8: acronym fallback for servers without icons
   - circleIconButton__5bc7e: "Add Server" / "Discover" buttons */
[class*="guilds_"] [class*="scroller_"],
[class*="guilds_"] [class*="scrollerBase_"],
[class*="guilds_"] [class*="tree_"],
[class*="guilds_"] [class*="itemsContainer_"],
[class*="guilds_"] [class*="stack_"],
[class*="guildsnav_"],
[class*="listNavigator_"],
[class*="listItem_"],
[class*="blobContainer_"],
[class*="childWrapper_"],
[class*="tutorialContainer_"],
[class*="listItemWrapper_"],
[class*="folderGroup_"],
[class*="folderButton_"] {{
  background-color: var(--dank-bg-main) !important;
}}

/* Server acronym icons should use a subtle surface so they're visible */
[class*="childWrapper_"][class*="acronym_"] {{
  background-color: rgba(255, 255, 255, 0.08) !important;
  color: var(--dank-text-normal) !important;
}}

/* Reset backgrounds for all common text-based components to prevent unintended highlights */
[class*="title_"],
[class*="heading-"],
[class*="text_"],
[class*="label_"],
[class*="contents_"],
[class*="content_"],
[class*="defaultColor_"] {{
  background-color: transparent !important;
}}

/* Discord Home button (Logo) background = Accent Color */
[data-list-item-id="guildsnav___home"] [class*="childWrapper_"] {{
  background-color: var(--dank-primary) !important;
  color: #100e13 !important;
}}

/* "Add Server" / "Discover" circle icons */
[class*="circleIconButton_"] {{
  background-color: rgba(255, 255, 255, 0.06) !important;
}}
[class*="circleIconButton_"]:hover {{
  background-color: rgba(255, 255, 255, 0.12) !important;
}}

/* Sidebar (Channels List) */
[class^="sidebar_"] {{
  {t_sidebar}
  border-radius: var(--radius-l);
  margin: 8px 4px;
}}
[class^="sidebar_"]::after {{
  background-color: var(--dank-bg-main) !important;
}}
/* Hide scrollbar in Channel List */
[class^="sidebar_"] [class*="scroller_"]::-webkit-scrollbar {{
  display: none !important;
  width: 0 !important;
}}
/* Channel Names & Links Visibility */
[class*="sidebar_"] [class*="name_"],
[class*="sidebar_"] [class*="link_"] [class*="name_"] {{
  color: var(--interactive-normal) !important;
}}
[class*="sidebar_"] [class*="link_"]:hover [class*="name_"] {{
  color: var(--interactive-hover) !important;
}}
[class*="sidebar_"] [class*="link_"][class*="modeSelected_"] [class*="name_"] {{
  color: var(--interactive-active) !important;
}}

/* User Area (Bottom Left) */
[class^="panels_"] {{
  {t_panels}
  border-radius: var(--radius-m);
  margin: 4px;
  overflow: hidden;
}}

/* User Panel specifically */
[class^="container_"][class*="canCopy_"],
[class^="container_"] > [class^="avatarWrapper_"] {{
  {t_transparent}
}}

/* Chat Area */
[class^="chatContent_"] {{
  {t_chat}
  border-radius: var(--radius-l);
  margin: 8px 4px;
}}

/* Member List */
[class*="membersWrap_"],
[class*="container_"] > [class*="members_"] {{
  {t_sidebar}
  border-radius: var(--radius-l);
  margin: 8px 8px 8px 4px;
}}

/* New Messages / Jump to Present Bars */
[class*="newMessagesBar_"],
[class*="jumpToPresentBar_"] {{
  background-color: var(--dank-primary) !important;
  border-radius: var(--radius-m);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
  color: #100e13 !important;
}}

[class*="newMessagesBar_"] {{
  inset: 8px 8px auto 8px !important;
}}

[class*="jumpToPresentBar_"] {{
  inset: auto 8px 8px 8px !important;
}}

[class*="newMessagesBar_"] [class*="barButtonBase_"],
[class*="newMessagesBar_"] [class*="span_"],
[class*="newMessagesBar_"] [class*="markAsReadText_"],
[class*="newMessagesBar_"] [class*="barButtonIcon_"],
[class*="jumpToPresentBar_"] [class*="barButtonBase_"],
[class*="jumpToPresentBar_"] [class*="barButtonMain_"] {{
  color: #100e13 !important;
}}

/* Booster Card & Promotional Containers */
[class*="memberSidebarSection_"],
[class*="containerWithMargin_"],
[class*="inner_"][class*="containerWithMargin_"] {{
  background-color: var(--dank-primary) !important;
  background: var(--dank-primary) !important;
  border-radius: var(--radius-m);
  padding: 12px;
  margin: 12px 8px;
  color: #100e13 !important;
  border: none !important;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
}}

/* Ensure all text inside these accent sections is dark */
[class*="memberSidebarSection_"] [class*="text-"],
[class*="memberSidebarSection_"] [class*="defaultColor_"],
[class*="memberSidebarSection_"] [class*="username_"],
[class*="memberSidebarSection_"] a,
[class*="containerWithMargin_"] [class*="text-"],
[class*="containerWithMargin_"] [class*="defaultColor_"],
[class*="containerWithMargin_"] a {{
  color: #100e13 !important;
}}

/* Buttons inside these accent sections use the main background */
[class*="memberSidebarSection_"] button,
[class*="containerWithMargin_"] button,
[class*="button_"][class*="primary_"][class*="hasText_"] {{
  background-color: var(--dank-bg-main) !important;
  color: var(--header-primary) !important;
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}}

[class*="memberSidebarSection_"] button:hover,
[class*="containerWithMargin_"] button:hover,
[class*="button_"][class*="primary_"][class*="hasText_"]:hover {{
  transform: scale(1.02);
  background-color: var(--dank-bg-secondary) !important;
}}

/* Ensure button text/icons are correctly colored (White system text) */
[class*="memberSidebarSection_"] button [class*="contents_"],
[class*="containerWithMargin_"] button [class*="contents_"],
[class*="button_"][class*="primary_"][class*="hasText_"] [class*="contents_"],
[class*="memberSidebarSection_"] button svg,
[class*="containerWithMargin_"] button svg,
[class*="button_"][class*="primary_"][class*="hasText_"] svg {{
  color: var(--header-primary) !important;
}}

/* Remove gradients and conflicting inner backgrounds */
[class*="memberGradientOverlay_"],
[class*="memberContainer_"],
[class*="containerCompact_"],
[class*="textContainer_"],
[class*="messageContainer_"],
[class*="contentContainer_"],
[class*="exampleMessage_"],
[class*="inner_"][class*="containerWithMargin_"] {{
  background: none !important;
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
}}

/* Input Area Glass */
[class^="channelTextArea_"] {{
  {t_transparent}
  border-radius: var(--radius-l);
  margin-bottom: 24px;
  padding: 0 16px;
}}
[class^="scrollableContainer_"] {{
  {t_input}
  border-radius: var(--radius-m);
  {t_border}
  {t_blur}
}}

/* Mentions */
[class^="mention_"] {{
  background: rgba({hex_to_rgb(primary)}, 0.35) !important;
  color: #ffffff !important;
  border-radius: 4px;
  font-weight: 600;
}}

/* Floating Elements (Popouts, Context Menus, Modals, Search Results) */
[class^="userPopout_"],
[class^="menu_"],
[class^="modal_"],
[class^="searchResultsWrap_"],
[class^="autocomplete_"] {{
  background-color: rgba({hex_to_rgb(bg_secondary)}, {floating_opacity}) !important;
  {t_blur_heavy}
  {t_border_soft}
  border-radius: var(--radius-m);
}}

/* Settings Sidebar specific fix */
[class^="sidebarRegionScroller_"] {{
  {t_transparent}
}}

/* Better Scrollbars */
::-webkit-scrollbar {{
  width: 6px !important;
}}
::-webkit-scrollbar-thumb {{
  background: var(--dank-primary) !important;
  border-radius: 10px !important;
}}

/* Full app layout spacing */
[class^="base_"] {{
  padding: 8px;
}}

/* Universal Solid Unification - Stripping inner backgrounds to reveal the main theme color */
[class*="sidebarList_"],
[class*="title_"],
[class*="header_"],
[class*="searchBar_"],
[class*="search_"],
[class*="container_"] > [class*="nav_"],
[class*="themed_"],
[class*="children_"] {{
  {t_transparent}
}}
[class*="children_"]::after {{
  background-color: var(--dank-bg-main) !important;
}}
"""
    return css


def main():
    themes_dir = get_vesktop_themes_dir()
    output_file = themes_dir / "DankMaterial.theme.css"
    author = get_author()

    print(f"🎨 Generating modern theme for {author}...")
    print(f"📁 Output: {output_file}")

    dms_colors = get_colors_from_dms()
    gsettings_colors = get_colors_from_gsettings()

    if not dms_colors and not gsettings_colors:
        print("⚠️ No DMS config or gsettings found. Using defaults.")
    else:
        print("✅ Config loaded.")

    colors = merge_colors(gsettings_colors, dms_colors)
    
    # Debug: show if wallpaper was found
    if colors.get("wallpaper"):
        print(f"🖼️ Wallpaper detected: {colors['wallpaper']}")
    else:
        print("ℹ️ No wallpaper detected, using solid background.")

    css = generate_full_theme_css(colors, author)
    output_file.write_text(css, encoding="utf-8")

    print(f"✨ Success! Restart Vesktop and enable 'Dank Material'.")


if __name__ == "__main__":
    main()
