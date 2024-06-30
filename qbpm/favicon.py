"""
SPDX-License-Identifier: MIT
derived from favicon.py by Scott Werner
https://github.com/scottwernervt/favicon/tree/123e431f53b2c4903b540246a85db0b1633d4786
"""

import re
from collections import defaultdict, namedtuple
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import httpx

LINK_RELS = [
    "icon",
    "shortcut icon",
]

SIZE_RE = re.compile(r"(?P<width>\d{2,4})x(?P<height>\d{2,4})", flags=re.IGNORECASE)

Icon = namedtuple("Icon", ["url", "width", "height", "format", "src"])


def get(client: httpx.Client) -> list[Icon]:
    response = client.get("")
    response.raise_for_status()
    client.base_url = response.url

    icons = {icon.url: icon for icon in tags(response.text)}

    fallback_icon = fallback(client)
    if fallback_icon and fallback_icon.src not in icons:
        icons[fallback_icon.url] = fallback_icon

    # print(f"{icons=}")
    return list(icons.values())
    # return sorted(icons, key=lambda i: i.width + i.height, reverse=True)


def fallback(client: httpx.Client) -> Icon | None:
    response = client.head("favicon.ico")
    if response.status_code == 200 and response.headers["Content-Type"].startswith(
        "image"
    ):
        return Icon(response.url, 0, 0, ".ico", "default")
    return None


class LinkRelParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.icons: dict[str, set[str]] = defaultdict(set)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "link":
            data = dict(attrs)
            rel = data.get("rel")
            if rel in LINK_RELS and (href := data.get("href") or data.get("content")):
                # TODO replace with data
                self.icons[rel].add(href)


def tags(html: str) -> set[Icon]:
    parser = LinkRelParser()
    parser.feed(html[0 : html.find("</head>")])
    hrefs = {link.strip() for links in parser.icons.values() for link in links}

    icons = set()
    for href in hrefs:
        if not href or href.startswith("data:image/"):
            continue

        # url_parsed = urlparse(url)
        # repair '//cdn.network.com/favicon.png' or `icon.png?v2`
        href_parsed = httpx.URL(href)

        width, height = (0, 0)  # dimensions(tag)
        ext = Path(href_parsed.path).suffix

        icon = Icon(
            href_parsed,
            width,
            height,
            ext.lower(),
            "TODO",
        )
        icons.add(icon)

    return icons


def dimensions(tag: Any) -> tuple[int, int]:
    """Get icon dimensions from size attribute or icon filename.

    :param tag: Link or meta tag.
    :type tag: :class:`bs4.element.Tag`

    :return: If found, width and height, else (0,0).
    :rtype: tuple(int, int)
    """
    sizes = tag.get("sizes", "")
    if sizes and sizes != "any":
        size = sizes.split(" ")  # '16x16 32x32 64x64'
        size.sort(reverse=True)
        width, height = re.split(r"[x\xd7]", size[0])
    else:
        filename = tag.get("href") or tag.get("content")
        size = SIZE_RE.search(filename)
        if size:
            width, height = size.group("width"), size.group("height")
        else:
            width, height = "0", "0"

    # repair bad html attribute values: sizes='192x192+'
    width = "".join(c for c in width if c.isdigit())
    height = "".join(c for c in height if c.isdigit())
    return int(width), int(height)
