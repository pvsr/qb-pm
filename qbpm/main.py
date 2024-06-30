import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, NoReturn, Optional

import click

from . import Profile, operations, profiles
from .utils import SUPPORTED_MENUS, default_profile_dir, error, or_phrase, user_data_dir

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@dataclass
class Context:
    profile_dir: Path
    qb_config_dir: Optional[Path]


def creator_options(f: Callable[..., Any]) -> Callable[..., Any]:
    for opt in reversed(
        [
            click.option("-l", "--launch", is_flag=True, help="Launch the profile."),
            click.option(
                "-f",
                "--foreground",
                is_flag=True,
                help="If --launch is set, run qutebrowser in the foreground.",
            ),
            # TODO --no-icon?
            click.option(
                "--no-desktop-file",
                "desktop_file",
                default=True,
                is_flag=True,
                flag_value=False,
                help="Do not generate a .desktop file for the profile.",
            ),
            click.option(
                "--overwrite",
                is_flag=True,
                help="Replace the current profile configuration if it exists.",
            ),
        ]
    ):
        f = opt(f)
    return f


class LowerCaseFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record.levelname = record.levelname.lower()
        return super().format(record)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
@click.option(
    "-P",
    "--profile-dir",
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    envvar="QBPM_PROFILE_DIR",
    show_envvar=True,
    default=default_profile_dir,
    help="Location to store qutebrowser profiles.",
)
@click.option(
    "-C",
    "--config-dir",
    type=click.Path(file_okay=False, readable=True, path_type=Path),
    help="Location of the qutebrowser config to inherit from.",
)
@click.option(
    "-l",
    "--log-level",
    default="error",
    type=click.Choice(["debug", "info", "error"], case_sensitive=False),
)
@click.pass_context
def main(
    ctx: click.Context, profile_dir: Path, config_dir: Optional[Path], log_level: str
) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())
    handler = logging.StreamHandler()
    handler.setFormatter(LowerCaseFormatter("{levelname}: {message}", style="{"))
    root_logger.addHandler(handler)
    if not profile_dir.is_dir():
        error(f"{profile_dir} is not a directory")
        sys.exit(1)
    if config_dir and not config_dir.is_dir():
        error(f"{config_dir} is not a directory")
        sys.exit(1)
    ctx.obj = Context(profile_dir, config_dir)


@main.command()
@click.argument("profile_name")
@click.argument("home_page", required=False)
@creator_options
@click.pass_obj
def new(context: Context, profile_name: str, **kwargs: Any) -> None:
    """Create a new profile."""
    profile = Profile(profile_name, **vars(context))
    then_launch(profiles.new_profile, profile, **kwargs)


@main.command()
@click.argument("session")
@click.argument("profile_name", required=False)
@creator_options
@click.pass_obj
def from_session(
    context: Context,
    session: str,
    profile_name: Optional[str],
    **kwargs: Any,
) -> None:
    """Create a new profile from a saved qutebrowser session.
    SESSION may be the name of a session in the global qutebrowser profile
    or a path to a session yaml file.
    """
    profile, session_path = session_info(session, profile_name, context)
    then_launch(operations.from_session, profile, session_path=session_path, **kwargs)


@main.command(context_settings={"ignore_unknown_options": True})
@click.argument("profile_name")
@click.argument("qb_args", nargs=-1, type=click.UNPROCESSED)
@click.option(
    "-f", "--foreground", is_flag=True, help="Run qutebrowser in the foreground."
)
@click.option(
    "-c", "--create", is_flag=True, help="Create the profile if it does not exist."
)
@click.pass_obj
def launch(context: Context, profile_name: str, **kwargs: Any) -> None:
    """Launch qutebrowser with a specific profile. All QB_ARGS are passed on to qutebrowser."""
    profile = Profile(profile_name, **vars(context))
    exit_with(operations.launch(profile, **kwargs))


@main.command(context_settings={"ignore_unknown_options": True})
@click.argument("qb_args", nargs=-1, type=click.UNPROCESSED)
@click.option(
    "-m",
    "--menu",
    metavar="COMMAND",
    help=f"A dmenu-compatible command or one of the following supported menus: {', '.join(sorted(SUPPORTED_MENUS))}",
)
@click.option(
    "-f", "--foreground", is_flag=True, help="Run qutebrowser in the foreground."
)
@click.option(
    "-i",
    "--icon",
    "force_icon",
    is_flag=True,
    help="Attach icons to menu items using rofi's extended dmenu spec even if your menu is not known to support it. Only works if at least one profile has an icon installed.",
)
@click.pass_obj
def choose(context: Context, **kwargs: Any) -> None:
    """Choose a profile to launch.
    Support is built in for many X and Wayland launchers, as well as applescript dialogs.
    All QB_ARGS are passed on to qutebrowser."
    """
    exit_with(operations.choose(profile_dir=context.profile_dir, **kwargs))


@main.command()
@click.argument("profile_name")
@click.pass_obj
def edit(context: Context, profile_name: str) -> None:
    """Edit a profile's config.py."""
    profile = Profile(profile_name, **vars(context))
    if not profile.exists():
        error(f"profile {profile.name} not found at {profile.root}")
        sys.exit(1)
    click.edit(filename=str(profile.root / "config" / "config.py"))


@main.command(name="list")
@click.pass_obj
def list_(context: Context) -> None:
    """List existing profiles."""
    for profile in sorted(context.profile_dir.iterdir()):
        print(profile.name)


@main.command()
@click.argument("profile_name")
@click.pass_obj
def desktop(
    context: Context,
    profile_name: str,
) -> None:
    """Create a desktop file for an existing profile."""
    profile = Profile(profile_name, **vars(context))
    exit_with(operations.desktop(profile))


@main.command()
@click.argument("profile_name")
@click.argument("icon", metavar="ICON_LOCATION")
@click.option(
    "-n",
    "--by-name",
    is_flag=True,
    help="interpret ICON_LOCATION as the name of an icon in an installed icon theme instead of a file or url.",
)
@click.option("--overwrite", is_flag=True, help="Replace the current icon.")
@click.pass_obj
def icon(context: Context, profile_name: str, **kwargs: Any) -> None:
    """Install an icon for the profile. ICON_LOCATION may be a url to download a favicon from,
    a path to an image file, or, with --by-name, the name of an xdg icon installed on your system.
    """
    profile = Profile(profile_name, **vars(context))
    exit_with(operations.icon(profile, **kwargs))


def then_launch(
    operation: Callable[..., bool],
    profile: Profile,
    launch: bool,
    foreground: bool,
    qb_args: tuple[str, ...] = (),
    **kwargs: Any,
) -> None:
    exit_with(
        operation(profile, **kwargs)
        and ((not launch) or operations.launch(profile, False, foreground, qb_args))
    )


def session_info(
    session: str, profile_name: Optional[str], context: Context
) -> tuple[Profile, Path]:
    user_session_dir = user_data_dir() / "sessions"
    session_paths = []
    if "/" not in session:
        session_paths.append(user_session_dir / (session + ".yml"))
    session_paths.append(Path(session))
    session_path = next(filter(lambda path: path.is_file(), session_paths), None)

    if not session_path:
        tried = or_phrase([str(p.resolve()) for p in session_paths])
        error(f"could not find session file at {tried}")
        sys.exit(1)

    return (Profile(profile_name or session_path.stem, **vars(context)), session_path)


def exit_with(result: bool) -> NoReturn:
    sys.exit(0 if result else 1)
