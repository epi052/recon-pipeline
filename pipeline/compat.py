"""Compatibility helpers for cmd2 2.x used by the legacy CLI.

The old shell supplied colour names as strings. cmd2 2.x requires members of
cmd2.ansi.Fg instead. This translates the legacy colours without replacing the
public cmd2 API or altering command execution.
"""
from cmd2.ansi import Fg, style as _cmd2_style

_OLD_FG = {
    "black": Fg.BLACK,
    "red": Fg.RED,
    "green": Fg.GREEN,
    "yellow": Fg.YELLOW,
    "blue": Fg.BLUE,
    "magenta": Fg.MAGENTA,
    "cyan": Fg.CYAN,
    "white": Fg.WHITE,
    "bright_black": Fg.BLACK,
    "bright_red": getattr(Fg, "LIGHT_RED", Fg.RED),
    "bright_green": getattr(Fg, "LIGHT_GREEN", Fg.GREEN),
    "bright_yellow": getattr(Fg, "LIGHT_YELLOW", Fg.YELLOW),
    "bright_blue": getattr(Fg, "LIGHT_BLUE", Fg.BLUE),
    "bright_magenta": getattr(Fg, "LIGHT_MAGENTA", Fg.MAGENTA),
    "bright_cyan": getattr(Fg, "LIGHT_CYAN", Fg.CYAN),
    "bright_white": getattr(Fg, "LIGHT_WHITE", Fg.WHITE),
}


def style(value, *, fg=None, **kwargs):
    """Format text with either a legacy colour string or a native Fg member."""
    if isinstance(fg, str):
        fg = _OLD_FG[fg]
    return _cmd2_style(value, fg=fg, **kwargs)
