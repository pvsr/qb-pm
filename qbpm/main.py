import sys
from pathlib import Path
from typing import Any, Callable, NoReturn, Optional

import click

from . import operations, profiles
from .profiles import Profile
from .utils import SUPPORTED_MENUS, default_profile_dir, error, user_data_dir

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


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


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
@click.option(
    "-P",
    "--profile-dir",
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    envvar="QBPM_PROFILE_DIR",
    show_envvar=True,
    default=default_profile_dir,
    help="Defaults to $XDG_DATA_HOME/qutebrowser-profiles.",
)
@click.pass_context
def main(ctx: click.Context, profile_dir: Path) -> None:
    ctx.obj = profile_dir


@main.command()
@click.argument("profile_name")
@click.argument("home_page", required=False)
@creator_options
@click.pass_obj
def new(profile_dir: Path, profile_name: str, **kwargs: Any) -> None:
    """Create a new profile."""
    profile = Profile(profile_name, profile_dir)
    then_launch(profiles.new_profile, profile, **kwargs)


@main.command()
@click.argument("session")
@click.argument("profile_name", required=False)
@creator_options
@click.pass_obj
def from_session(
    profile_dir: Path,
    session: str,
    profile_name: Optional[str],
    **kwargs: Any,
) -> None:
    """Create a new profile from a saved qutebrowser session.
    SESSION may be the name of a session in the global qutebrowser profile
    or a path to a session yaml file.
    """
    profile, session_path = session_info(session, profile_name, profile_dir)
    then_launch(operations.from_session, profile, session_path=session_path, **kwargs)


@main.command()
@click.argument("profile_name")
@click.pass_obj
def desktop(
    profile_dir: Path,
    profile_name: str,
) -> None:
    """Create a desktop file for an existing profile."""
    profile = Profile(profile_name, profile_dir)
    exit_with(operations.desktop(profile))


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
def launch(profile_dir: Path, profile_name: str, **kwargs: Any) -> None:
    """Launch qutebrowser with a specific profile. All QB_ARGS are passed on to qutebrowser."""
    profile = Profile(profile_name, profile_dir)
    exit_with(operations.launch(profile, **kwargs))


@main.command(context_settings={"ignore_unknown_options": True})
@click.argument("qb_args", nargs=-1, type=click.UNPROCESSED)
@click.option(
    "-m",
    "--menu",
    metavar="COMMAND",
    help=f"A dmenu-compatible command or one of the following supported menus: {', '.join(sorted(SUPPORTED_MENUS))}",
)
@click.option("-f", "--foreground", is_flag=True)
@click.pass_obj
def choose(profile_dir: Path, **kwargs: Any) -> None:
    """Choose a profile to launch.
    Support is built in for many X and Wayland launchers, as well as applescript dialogs.
    All QB_ARGS are passed on to qutebrowser."
    """
    exit_with(operations.choose(profile_dir=profile_dir, **kwargs))


@main.command()
@click.argument("profile_name")
@click.pass_obj
def edit(profile_dir: Path, profile_name: str) -> None:
    """Edit a profile's config.py."""
    profile = Profile(profile_name, profile_dir)
    if not profile.exists():
        error(f"profile {profile.name} not found at {profile.root}")
        sys.exit(1)
    click.edit(filename=str(profile.root / "config" / "config.py"))


@main.command(name="list")
@click.pass_obj
def list_(profile_dir: Path) -> None:
    """List existing profiles."""
    for profile in sorted(profile_dir.iterdir()):
        print(profile.name)


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
    session: str, profile_name: Optional[str], profile_dir: Path
) -> tuple[Profile, Path]:
    user_session_dir = user_data_dir() / "sessions"
    session_paths = []
    if "/" not in session:
        session_paths.append(user_session_dir / (session + ".yml"))
    session_paths.append(Path(session))
    session_path = next(filter(lambda path: path.is_file(), session_paths), None)

    if not session_path:
        tried = ", ".join([str(p.resolve()) for p in session_paths])
        error(f"could not find session at the following paths: {tried}")
        sys.exit(1)

    return (Profile(profile_name or session_path.stem, profile_dir), session_path)


def exit_with(result: bool) -> NoReturn:
    sys.exit(0 if result else 1)
