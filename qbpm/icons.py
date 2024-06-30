import re
import shutil
from collections.abc import Callable, Iterator
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

import httpx
from PIL import Image

from . import Profile, __version__, favicon
from .favicon import Icon
from .utils import error, info

# TODO more preferences: 16x16, 32, 0, other
PREFERRED_ICONS = [
    re.compile(p)
    for p in [
        r"favicon.*\.svg$",
        r"favicon.*\.ico$",
        r"favicon.*\.png$",
        r"\.ico$",
        r"icon\.png$",
        r"\.svg$",
    ]
]


def choose_icon(icons: list[Icon]) -> Iterator[Icon]:
    preferred = PREFERRED_ICONS
    for pattern in preferred:
        for icon in icons:
            if pattern.search(icon.url.path):
                info(f"chose {icon.url}")
                yield icon
                icons.remove(icon)
                yield from choose_icon(icons)


headers = {"user-agent": f"qbpm/{__version__}"}


def download_icon(profile: Profile, home_page: str, overwrite: bool) -> Optional[Path]:
    base_url = httpx.URL(home_page)
    if not base_url.scheme:
        base_url = httpx.URL("https://" + home_page)
    client = httpx.Client(base_url=base_url, headers=headers, follow_redirects=True)
    tmp_dir = TemporaryDirectory()
    work_dir = Path(tmp_dir.name)
    try:
        for icon in choose_icon(favicon.get(client)):
            icon_body = client.get(icon.url)
            if icon_body.status_code != 200:
                info(f"got bad response code {icon_body.status_code} for {icon.url}")
                return None
            elif not icon_body.headers["Content-Type"].startswith("image"):
                info(f"{icon.url} is not an image")
                return None
            icon_body.raise_for_status()
            work_icon = work_dir / f"favicon{icon.format}"
            with work_icon.open("wb") as icon_file:
                for chunk in icon_body.iter_bytes(1024):
                    icon_file.write(chunk)
            icon_path = install_icon_file(profile, work_icon, overwrite, icon.url)
            if icon_path:
                # print(f"installed {client.base_url.join(icon.url)}")
                return icon_path
        if not icon_path:
            # TODO pretty print
            info(f"no favicons found matching one of {PREFERRED_ICONS}")
            return None
    except Exception as e:
        # info(str(e))
        raise e
        error(f"failed to fetch favicon from {home_page}")
        return None
    finally:
        tmp_dir.cleanup()
        client.close()

    return None


def icon_for_profile(profile: Profile) -> Optional[str]:
    icon_file = next(find_icon_files(profile), None)
    if icon_file and icon_file.suffix == ".name":
        return icon_file.read_text()
    return str(icon_file) if icon_file else None


def install_icon_file(
    profile: Profile, src: Path, overwrite: bool, origin: Optional[str] = None
) -> Optional[Path]:
    clean_icons = check_for_icons(profile, overwrite)
    if clean_icons is None:
        return None
    icon_format = src.suffix
    dest = profile.root / f"icon{icon_format}"
    if icon_format not in {".png", ".svg"}:
        dest = dest.with_suffix(".png")
        try:
            image = Image.open(src)
            clean_icons(set())
            image.save(dest, format="png")
        except Exception as e:
            error(str(e))
            error(f"failed to convert {origin or src} to png")
            dest.unlink(missing_ok=True)
            return None
    else:
        if src.resolve() != dest:
            shutil.copy(src, dest)
        clean_icons({dest})
    print(dest)
    return dest.absolute()


def install_icon_by_name(profile: Profile, icon_name: str, overwrite: bool) -> bool:
    clean_icons = check_for_icons(profile, overwrite)
    if clean_icons is None:
        return False
    clean_icons(set())
    file = profile.root / "icon.name"
    file.write_text(icon_name)
    return True


def check_for_icons(
    profile: Profile, overwrite: bool
) -> Callable[[set[Path]], None] | None:
    existing_icons = set(find_icon_files(profile))
    if existing_icons and not overwrite:
        error(f"icon already exists in {profile.root}, pass --overwrite to replace it")
        return None

    def clean_icons(keep: set[Path]) -> None:
        for icon in existing_icons - keep:
            icon.unlink()

    return clean_icons


def find_icon_files(profile: Profile) -> Iterator[Path]:
    for ext in ["png", "svg", "name"]:
        icon = profile.root / f"icon.{ext}"
        if icon.is_file():
            yield icon.absolute()
