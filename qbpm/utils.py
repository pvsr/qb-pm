import platform
from collections.abc import Generator
from os import environ
from pathlib import Path
from shutil import which
from sys import exit, stderr

from xdg import BaseDirectory

WAYLAND_MENUS = ["fuzzel", "wofi", "dmenu-wl"]
X11_MENUS = ["rofi", "dmenu"]
AUTO_MENUS = WAYLAND_MENUS + X11_MENUS
SUPPORTED_MENUS = [*AUTO_MENUS, "fzf", "applescript"]


def error(msg: str) -> None:
    print(f"error: {msg}", file=stderr)


def default_profile_dir() -> Path:
    return Path(BaseDirectory.save_data_path("qutebrowser-profiles"))


def user_data_dir() -> Path:
    if platform.system() == "Linux":
        return Path(BaseDirectory.xdg_data_home) / "qutebrowser"
    if platform.system() == "Darwin":
        return Path.home() / "Library" / "Application Support" / "qutebrowser"
    error("This operation is only implemented for linux and macOS.")
    print(
        "If you're interested in adding support for another OS, send a PR "
        "to github.com/pvsr/qbpm adding the location of qutebrowser data such "
        "as history.sqlite on your OS to user_data_dir() in qbpm/utils.py.",
        file=stderr,
    )
    exit(1)


def user_config_dir() -> Path:
    return Path(BaseDirectory.xdg_config_home) / "qutebrowser"


def installed_menus() -> Generator[str, None, None]:
    if platform.system() == "Darwin":
        yield "applescript"
    if environ.get("WAYLAND_DISPLAY"):
        for menu_cmd in WAYLAND_MENUS:
            if which(menu_cmd) is not None:
                yield menu_cmd
    if environ.get("DISPLAY"):
        for menu_cmd in X11_MENUS:
            if which(menu_cmd) is not None:
                yield menu_cmd
    if environ.get("TMUX") and which("fzf-tmux") is not None:
        yield "fzf-tmux"
    # if there's no display and fzf is installed we're probably(?) in a term
    if which("fzf") is not None:
        print("no graphical launchers found, trying fzf", file=stderr)
        yield "fzf"
