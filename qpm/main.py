import argparse
import sys
from pathlib import Path
from typing import Callable, Optional

from qpm import config, operations, profiles
from qpm.profiles import Profile
from qpm.utils import error


def main() -> None:
    parser = argparse.ArgumentParser(description="Qutebrowser profile manager")
    parser.set_defaults(operation=lambda args: parser.print_help())
    parser.add_argument(
        "-P",
        "--profile-dir",
        metavar="directory",
        type=Path,
        help="directory in which profiles are stored",
    )

    subparsers = parser.add_subparsers()
    new = subparsers.add_parser("new", help="create a new profile")
    new.set_defaults(
        operation=lambda args: wrap_op(args.profile_name, profiles.new_profile)
    )
    new.add_argument("profile_name", metavar="name", help="name of the new profile")
    creator_args(new)

    session = subparsers.add_parser(
        "from-session", help="create a new profile from a qutebrowser session"
    )
    session.set_defaults(
        operation=lambda args: operations.from_session(args.session, args.profile_name),
    )
    session.add_argument(
        "session", help="session to create a new profile from",
    )
    session.add_argument(
        "profile_name",
        metavar="name",
        nargs="?",
        help="name of the new profile. if unset the session name will be used",
    )
    creator_args(session)

    launch = subparsers.add_parser(
        "launch", aliases=["run"], help="launch qutebrowser with the given profile"
    )
    launch.set_defaults(
        operation=lambda args: wrap_op(
            args.profile_name,
            lambda profile: operations.launch(
                profile, args.strict, args.foreground, args.qb_args or []
            ),
        )
    )
    launch.add_argument(
        "profile_name",
        metavar="name",
        help="profile to launch. it will be created if it does not exist, unless -s is set",
    )
    launch.add_argument(
        "-n",
        "--new",
        action="store_false",
        dest="strict",
        help="create the profile if it doesn't exist",
    )
    launch.add_argument(
        "-f",
        "--foreground",
        action="store_true",
        help="launch qutebrowser in the foreground and print its stdout and stderr to the console",
    )

    raw_args = parser.parse_known_args()
    args = raw_args[0]
    args.qb_args = raw_args[1]
    if args.profile_dir:
        if not args.profile_dir.is_dir():
            error(f"{args.profile_dir} is not a directory")
            sys.exit(1)
        config.profiles_dir = args.profile_dir
    args.operation(args)


def creator_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-l",
        "--launch",
        action=ThenLaunchAction,
        dest="operation",
        help="launch the profile after creating",
    )
    parser.set_defaults(
        strict=True, foreground=False,
    )


def wrap_op(profile_name: str, op: Callable[[Profile], bool]) -> Optional[Profile]:
    profile = Profile(profile_name)
    return profile if op(profile) else None


class ThenLaunchAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=0, **kwargs):
        super(ThenLaunchAction, self).__init__(
            option_strings, dest, nargs=nargs, **kwargs
        )

    def __call__(self, parser, namespace, values, option_string=None):
        operation = getattr(namespace, self.dest)
        if operation:
            composed = lambda args: then_launch(args, operation)
            setattr(namespace, self.dest, composed)


def then_launch(
    args: argparse.Namespace,
    operation: Callable[[argparse.Namespace], Optional[Profile]],
) -> bool:
    profile = operation(args)
    if profile:
        return operations.launch(profile, args.strict, args.foreground, [])
    return False


if __name__ == "__main__":
    main()
