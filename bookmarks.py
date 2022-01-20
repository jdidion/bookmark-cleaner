import hashlib
import json
import logging
from pathlib import Path
import sys
from typing import Optional
import urllib.parse
import webbrowser

from autoclick import group
#from ping3 import ping
import requests
import requests.exceptions
from xphyle import open_


DEFAULT_BOOKMARK_PATH = Path(
    "~/Library/Application Support/Google/Chrome/Default/Bookmarks"
).expanduser()
FIREFOX_USER_AGENT = \
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) "\
    "Gecko/2009021910 Firefox/3.0.7"
IGNORE_TAGS = {"Bookmarks Bar"}

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
LOG = logging.getLogger()


@group()
def bookmarks():
    pass


@bookmarks.command()
def clean(
    infile: Path = DEFAULT_BOOKMARK_PATH,
    outfile: Optional[Path] = None,
    invalid_file: Optional[Path] = None,
    check_urls: bool = True,
    browse_invalid: bool = False,
    ignore_ssl_errors: bool = True
):
    if outfile is None:
        outfile = Path("Bookmarks.cleaned.json")

    with open(infile, "rt") as inp:
        bm = json.load(inp)

    md5 = hashlib.md5()
    invalid = []

    for key, root in bm["roots"].items():
        if key != "sync_transaction_version":
            handle_node(
                root, md5, invalid, check_urls, browse_invalid, ignore_ssl_errors
            )

    bm["checksum"] = md5.hexdigest()

    with open(outfile, "wt") as out:
        json.dump(bm, out)

    if browse_invalid:
        with open_(invalid_file, "wt") as inv:
            json.dump({"invalid": invalid}, inv)


def handle_node(
    node,
    md5,
    invalid,
    check_urls=True,
    browse_invalid=False,
    ignore_ssl_errors=True,
    tags=None
):
    if node["type"] != "url":
        md5.update(node["id"].encode())
        md5.update(node["name"].encode("utf-16le"))
        md5.update(b"folder")
        if "children" in node:
            tag = node["name"]
            if tag not in IGNORE_TAGS:
                new_tags = set()
                if tags:
                    new_tags.update(tags)
                new_tags.add(tag)
            else:
                new_tags = tags
            node["children"] = [
                c for c in node["children"] if handle_node(
                    c, md5, invalid, check_urls, ignore_ssl_errors, new_tags
                )
            ]
        return True
    else:
        node["tags"] = list(tags) if tags else []
        code, reason = _check_url(node, ignore_ssl_errors) if check_urls else (0, None)
        if code == 0:
            md5.update(node["id"].encode())
            md5.update(node["name"].encode("utf-16le"))
            md5.update(b"url")
            md5.update(node["url"].encode())
            return True
        else:
            node["code"] = code
            node["reason"] = reason
            invalid.append(node)
            if browse_invalid:
                _browse(node)
            return False


@bookmarks.command()
def check(url: str):
    _open_url(url)


def _check_url(node, ignore_ssl_errors):
    url = node["url"]
    parsed = urllib.parse.urlparse(url)
    code = 0
    reason = None

    if parsed.scheme in ("http", "https"):
        LOG.debug(f"Checking URL {url}")
        try:
            r = _open_url(url)
            LOG.debug(f"URL {url} is valid")
            if r.url != url:
                LOG.info(f"{url} redirected to {r.url}")
                node["url"] = r.url
        except requests.RequestException as err:
            if ignore_ssl_errors and isinstance(err, requests.exceptions.SSLError):
                LOG.warning("Ignoring SSL error {err}")
            else:
                LOG.exception(f"Error for URL {url}")
                code = err.errno
                reason = err.strerror

    # See if the host is still valid
    #host = parsed.netloc
    #if not ping(host):
    #    LOG.error(f"Invalid host: {host}")

    return code, reason


def _open_url(url):
    return requests.head(
        url,
        allow_redirects=True,
        timeout=5,
        headers={"User-Agent": FIREFOX_USER_AGENT}
    )


@bookmarks.command()
def browseall(infile: Path):
    with open(infile, "rt") as inp:
        sites = json.load(inp)

    if "invalid" not in sites:
        print("No sites to open")
        return

    for site in sites["invalid"]:
        print(f"Opening {site['name']}")
        _browse(site)


def _browse(node):
    webbrowser.open_new_tab(node["url"])


if __name__ == "__main__":
    bookmarks()
