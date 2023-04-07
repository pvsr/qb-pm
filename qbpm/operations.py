import shutil
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from sys import platform
from typing import Optional

from xdg import BaseDirectory

from . import Profile, config, icons, profiles
from .utils import env_menus, error, installed_menus, or_phrase, qutebrowser_exe


def from_session(
    profile: Profile,
    session_path: Path,
    desktop_file: bool = True,
    overwrite: bool = False,
) -> bool:
    if not profiles.new_profile(profile, None, desktop_file, overwrite):
        return False

    session_dir = profile.root / "data" / "sessions"
    session_dir.mkdir(parents=True, exist_ok=overwrite)
    shutil.copy(session_path, session_dir / "_autosave.yml")

    return True


def launch(
    profile: Profile, create: bool, foreground: bool, qb_args: tuple[str, ...]
) -> bool:
    if not profiles.ensure_profile_exists(profile, create, desktop_file=True):
        return False

    args = profile.cmdline() + list(qb_args)
    return launch_internal(foreground, args)


def launch_qutebrowser(foreground: bool, qb_args: tuple[str, ...]) -> bool:
    return launch_internal(foreground, [qutebrowser_exe(), *qb_args])


def launch_internal(foreground: bool, args: list[str]) -> bool:
    if not shutil.which(args[0]):
        error("qutebrowser is not installed")
        return False

    if foreground:
        return subprocess.run(args, check=False).returncode == 0
    else:
        p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            # give qb a chance to validate input before returning to shell
            stdout, stderr = p.communicate(timeout=0.1)
            print(stderr.decode(errors="ignore"), end="")
        except subprocess.TimeoutExpired:
            pass

    return True


application_dir = Path(BaseDirectory.xdg_data_home) / "applications" / "qbpm"


def desktop(profile: Profile) -> bool:
    exists = profile.exists()
    if exists:
        profiles.create_desktop_file(profile, icons.icon_for_profile(profile))
    else:
        error(f"profile {profile.name} not found at {profile.root}")
    return exists


def icon(profile: Profile, icon: str, by_name: bool, overwrite: bool) -> bool:
    if not profile.exists():
        error(f"profile {profile.name} not found at {profile.root}")
        return False
    if by_name:
        icon_id = icon if icons.install_icon_by_name(profile, icon, overwrite) else None
    else:
        if Path(icon).is_file():
            icon_file = icons.install_icon_file(profile, Path(icon), overwrite)
        else:
            icon_file = icons.download_icon(profile, icon, overwrite)
        icon_id = str(icon_file) if icon_file else None
    if icon_id:
        profiles.add_to_desktop_file(profile, "Icon", icon_id)
    return icon_id is not None


def choose(
    profile_dir: Path,
    menu: Optional[str],
    foreground: bool,
    qb_args: tuple[str, ...],
    force_icon: bool,
) -> bool:
    menu = menu or next(installed_menus(), None)
    if not menu:
        possible_menus = or_phrase([menu for menu in env_menus() if menu != "fzf-tmux"])
        error(
            "no menu program found, use --menu to provide a dmenu-compatible menu or install one of "
            + possible_menus
        )
        return False
    if menu == "applescript" and platform != "darwin":
        error(f"applescript cannot be used on a {platform} host")
        return False
    real_profiles = {
        Profile(profile.name, profile_dir) for profile in sorted(profile_dir.iterdir())
    }
    if len(real_profiles) == 0:
        error("no profiles")
        return False

    menu_cmd = menu_command(menu, real_profiles, qb_args)
    if not menu_cmd:
        return False

    use_icon = menu_cmd.icon_support or force_icon
    menu_items = build_menu_items(real_profiles, use_icon)
    qb_entry = icon_entry("qutebrowser", "qutebrowser") if use_icon else "qutebrowser"
    menu_items += f"\n{qb_entry}"

    selection_cmd = subprocess.run(
        menu_cmd.command,
        input=menu_items,
        text=True,
        # TODO remove shell dependency
        shell=True,
        stdout=subprocess.PIPE,
        stderr=None,
        check=False,
    )
    out = selection_cmd.stdout
    selection = out and out.rstrip("\n")

    if selection == "qutebrowser" and "qutebrowser" not in real_profiles:
        return launch_qutebrowser(foreground, qb_args)
    elif selection:
        profile = Profile(selection, profile_dir)
        return launch(profile, False, foreground, qb_args)
    else:
        error("no profile selected")
        return False


@dataclass
class Menu:
    command: str
    icon_support: bool


def menu_command(
    menu: str, profiles: Iterable[Profile], qb_args: tuple[str, ...]
) -> Optional[Menu]:
    icon = False
    arg_string = " ".join(qb_args)
    if menu == "applescript":
        profile_list = '", "'.join([p.name for p in profiles])
        return Menu(
            f"""osascript -e \'set profiles to {{"{profile_list}"}}
set profile to choose from list profiles with prompt "qutebrowser: {arg_string}" default items {{item 1 of profiles}}
item 1 of profile\'""",
            icon,
        )

    prompt = "-p qutebrowser"
    command = menu
    # TODO arg
    if len(menu.split(" ")) == 1:
        program = Path(menu).name
        if program == "rofi":
            icon = True
            command = f"{menu} -dmenu -no-custom {prompt} -mesg '{arg_string}'"
        elif program == "wofi":
            command = f"{menu} --dmenu {prompt}"
        elif program.startswith("dmenu"):
            command = f"{menu} {prompt}"
        elif program.startswith("fzf"):
            command = f"{menu} --prompt 'qutebrowser '"
        elif program == "fuzzel":
            icon = True
            command = f"{menu} -d"
    exe = command.split(" ")[0]
    if not shutil.which(exe):
        error(f"command '{exe}' not found")
        return None
    return Menu(command, icon)


def build_menu_items(profiles: Iterable[Profile], icon: bool) -> str:
    if icon and any(profile_icons := [icons.icon_for_profile(p) for p in profiles]):
        menu_items = [
            icon_entry(p.name, icon) for (p, icon) in zip(profiles, profile_icons)
        ]
    else:
        menu_items = [p.name for p in profiles]

    return "\n".join(menu_items)


def icon_entry(name: str, icon: Optional[str]) -> str:
    return f"{name}\0icon\x1f{icon or config.default_icon}"
