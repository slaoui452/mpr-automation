"""Société Générale palette (light theme). styles.qss refers to these names as $name."""

COLORS = {
    # Brand
    "red": "#E9041E",            # SG red: accents, focus, running state
    "red_hover": "#C80319",
    "red_pressed": "#A30214",
    "red_tint": "#FDECEE",       # light red background (drop highlight, file error)
    "black": "#000000",          # SG black: header
    "black_hover": "#2B2B2B",
    "white": "#FFFFFF",
    # Neutrals
    "text": "#1A1A1A",
    "muted": "#6B6B6B",
    "canvas": "#F5F5F5",         # window background
    "surface": "#FFFFFF",        # cards, tiles, panels
    "surface_alt": "#FAFAFA",    # empty drop zone
    "border": "#DADADA",
    "border_strong": "#B5B5B5",
    "divider": "#EFEFEF",
    "disabled_bg": "#E6E6E6",
    "disabled_text": "#A3A3A3",
    # Status
    "success": "#1B7F3B",
    "warning": "#B26A00",
    "error": "#C80319",
}

FONT_FAMILY = "Segoe UI"
FONT_SIZE_PT = 10
MONO_FAMILY = "Consolas"

# Letter spacing in px for the uppercase labels, by role (Qt stylesheets can't set it).
LETTER_SPACING = {"company": 2.0, "sectionTitle": 1.5, "tileTitle": 1.0, "badge": 1.0}
