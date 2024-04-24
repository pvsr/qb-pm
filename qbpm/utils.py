import logging
import platform
from collections.abc import Iterator
from os import environ
from pathlib import Path
from shutil import which

from click import get_app_dir
from xdg import BaseDirectory

WAYLAND_MENUS = ["fuzzel", "wofi", "dmenu-wl"]
X11_MENUS = ["rofi", "dmenu"]
AUTO_MENUS = WAYLAND_MENUS + X11_MENUS
SUPPORTED_MENUS = [*AUTO_MENUS, "fzf", "applescript"]


def info(msg: str) -> None:
    logging.info(msg)


def error(msg: str) -> None:
    logging.error(msg)


def default_profile_dir() -> Path:
    return Path(BaseDirectory.save_data_path("qutebrowser-profiles"))


def user_data_dir() -> Path:
    if platform.system() == "Linux":
        return Path(BaseDirectory.xdg_data_home) / "qutebrowser"
    # TODO confirm this works on windows
    return Path(get_app_dir("qutebrowser"), roaming=True)


def user_config_dirs() -> list[Path]:
    # deduplicate while maintaining order
    return list(
        dict.fromkeys(
            [
                Path(get_app_dir("qutebrowser", roaming=True)),
                Path(BaseDirectory.xdg_config_home) / "qutebrowser",
                Path.home() / ".qutebrowser",
            ]
        )
    )


def installed_menus() -> Iterator[str]:
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
        info("no graphical launchers found, trying fzf")
        yield "fzf"


def or_phrase(items: list) -> str:
    strings = list(map(str, items))
    size = len(strings)
    if size == 0:
        return "[]"
    elif size == 1:
        return strings[0]
    elif size == 2:
        return " or ".join(strings)
    else:
        return ", or ".join([", ".join(strings[0:-1]), strings[-1]])
