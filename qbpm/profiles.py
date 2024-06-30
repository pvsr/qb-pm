from functools import partial
from pathlib import Path
from typing import Optional

from xdg import BaseDirectory
from xdg.DesktopEntry import DesktopEntry

from . import Profile, config, icons
from .utils import error, or_phrase, user_config_dirs


def create_profile(profile: Profile, overwrite: bool = False) -> bool:
    if not profile.check():
        return False

    if not overwrite and profile.root.exists():
        error(f"{profile.root} already exists")
        return False

    config_dir = profile.root / "config"
    config_dir.mkdir(parents=True, exist_ok=overwrite)
    print(profile.root)
    return True


def create_config(
    profile: Profile,
    qb_config_dir: Path,
    home_page: Optional[str] = None,
    overwrite: bool = False,
) -> None:
    user_config = profile.root / "config" / "config.py"
    with user_config.open(mode="w" if overwrite else "x") as dest_config:
        out = partial(print, file=dest_config)
        out("config.load_autoconfig()")
        title_prefix = "{perc}{current_title}{title_sep}"
        out(f"c.window.title_format = '{title_prefix} qutebrowser ({profile.name})'")
        if home_page:
            out(f"c.url.start_pages = ['{home_page}']")
        out(f"config.source(r'{qb_config_dir / 'config.py'}')")
        for conf in qb_config_dir.glob("conf.d/*.py"):
            out(f"config.source(r'{conf}')")


application_dir = Path(BaseDirectory.xdg_data_home) / "applications" / "qbpm"


def create_desktop_file(profile: Profile, icon: Optional[str] = None) -> None:
    desktop = DesktopEntry(str(application_dir / f"{profile.name}.desktop"))
    desktop.set("Name", f"{profile.name}{config.application_name_suffix}")
    desktop.set("Icon", icon or config.default_icon)
    desktop.set("Exec", " ".join(profile.cmdline()) + " %u")
    desktop.set("Categories", ["Network"])
    desktop.set("Terminal", False)
    desktop.set("StartupNotify", True)
    desktop.write()


def add_to_desktop_file(profile: Profile, key: str, value: str) -> None:
    desktop_file = application_dir / f"{profile.name}.desktop"
    if not desktop_file.exists():
        return
    desktop = DesktopEntry(str(application_dir / f"{profile.name}.desktop"))
    desktop.set(key, value)
    desktop.write()


def ensure_profile_exists(
    profile: Profile, create: bool = True, desktop_file: bool = False
) -> bool:
    if profile.root.exists() and not profile.root.is_dir():
        error(f"{profile.root} is not a directory")
        return False
    if not profile.root.exists() and create:
        return new_profile(profile, desktop_file=desktop_file)
    if not profile.root.exists():
        error(f"{profile.root} does not exist")
        return False
    return True


def new_profile(
    profile: Profile,
    home_page: Optional[str] = None,
    desktop_file: bool = True,
    overwrite: bool = False,
) -> bool:
    qb_config_dir = get_qb_config_dir(profile)
    if not qb_config_dir:
        return False
    if create_profile(profile, overwrite):
        create_config(profile, qb_config_dir, home_page, overwrite)
        icon = None
        if home_page:
            # TODO catch errors?
            icon = icons.download_icon(profile, home_page, overwrite)
        if desktop_file:
            create_desktop_file(profile, str(icon) if icon else None)
        return True
    return False


def get_qb_config_dir(profile: Profile) -> Optional[Path]:
    config_file = "config.py"
    dirs = (
        [profile.qb_config_dir, profile.qb_config_dir / "config"]
        if profile.qb_config_dir
        else user_config_dirs()
    )
    for config_dir in dirs:
        if (config_dir / config_file).exists():
            return config_dir.absolute()
    error(f"could not find {config_file} in {or_phrase(dirs)}")
    return None
