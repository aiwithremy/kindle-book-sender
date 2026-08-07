#!/usr/bin/env python3
"""Validate an EPUB or PDF before Kindle delivery."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


def fail(message: str) -> None:
    print(json.dumps({"valid": False, "error": message}))
    raise SystemExit(1)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def epub_rootfile(archive: zipfile.ZipFile) -> str:
    try:
        container = ET.fromstring(archive.read("META-INF/container.xml"))
    except (KeyError, ET.ParseError) as error:
        fail(f"invalid EPUB container metadata: {error}")
    for element in container.iter():
        if local_name(element.tag) == "rootfile" and element.get("full-path"):
            return element.get("full-path")
    fail("EPUB container has no package rootfile")


def validate_epub_quality(archive: zipfile.ZipFile, opf_path: str) -> dict[str, object]:
    try:
        package = ET.fromstring(archive.read(opf_path))
    except (KeyError, ET.ParseError) as error:
        fail(f"invalid EPUB package metadata: {error}")

    manifest = next((element for element in package.iter() if local_name(element.tag) == "manifest"), None)
    if manifest is None:
        fail("EPUB package has no manifest")
    items = [element for element in manifest if local_name(element.tag) == "item"]
    by_id = {item.get("id"): item for item in items if item.get("id")}
    cover_ids = {
        item.get("id")
        for item in items
        if "cover-image" in item.get("properties", "").split()
    }
    for element in package.iter():
        if local_name(element.tag) == "meta" and element.get("name") == "cover" and element.get("content"):
            cover_ids.add(element.get("content"))
    cover_items = [by_id[cover_id] for cover_id in cover_ids if cover_id in by_id]
    if not cover_items:
        fail("missing embedded EPUB cover image; add a PNG or JPEG title cover before delivery")
    if not any(item.get("media-type") in {"image/png", "image/jpeg"} for item in cover_items):
        fail("EPUB cover must be PNG or JPEG; SVG-only covers are not Kindle-safe")

    prefix = Path(opf_path).parent
    xhtml_paths = []
    for item in items:
        if item.get("media-type") in {"application/xhtml+xml", "text/html"} and item.get("href"):
            xhtml_paths.append(str(prefix / item.get("href")))
    if not xhtml_paths:
        fail("EPUB has no readable XHTML chapters")

    narrow_layout = []
    width_attribute = re.compile(r"<(?:table|td|div|section)[^>]*\bwidth\s*=\s*['\"]?([1-9]\d{0,2})\b", re.I)
    fixed_css = re.compile(r"(?:width|max-width)\s*:\s*([1-9]\d{0,2})px\b", re.I)
    for chapter in xhtml_paths:
        try:
            markup = archive.read(chapter).decode("utf-8", errors="ignore")
        except KeyError:
            fail(f"manifest chapter is missing: {chapter}")
        if width_attribute.search(markup) or fixed_css.search(markup):
            narrow_layout.append(chapter)
    if narrow_layout:
        fail(f"EPUB contains narrow fixed-width reading layout in {narrow_layout[0]}")
    return {"cover": "raster", "chapters": len(xhtml_paths), "layout": "reflowable"}


def validate_epub(path: Path) -> dict[str, object]:
    try:
        with zipfile.ZipFile(path) as archive:
            corrupted = archive.testzip()
            if corrupted:
                fail(f"corrupt EPUB member: {corrupted}")
            if "mimetype" not in archive.namelist():
                fail("missing EPUB mimetype entry")
            if archive.read("mimetype") != b"application/epub+zip":
                fail("invalid EPUB mimetype entry")
            if "META-INF/container.xml" not in archive.namelist():
                fail("missing EPUB container metadata")
            first_entry = archive.infolist()[0]
            if first_entry.filename != "mimetype" or first_entry.compress_type != zipfile.ZIP_STORED:
                fail("EPUB mimetype entry must be first and uncompressed")
            quality = validate_epub_quality(archive, epub_rootfile(archive))
            return {
                "valid": True,
                "format": "epub",
                "bytes": path.stat().st_size,
                "members": len(archive.infolist()),
                **quality,
            }
    except (OSError, zipfile.BadZipFile) as error:
        fail(f"unreadable EPUB: {error}")


def validate_pdf(path: Path) -> dict[str, object]:
    try:
        if not path.read_bytes().startswith(b"%PDF-"):
            fail("file does not have a PDF header")
        try:
            from pypdf import PdfReader
        except ImportError:
            return {"valid": True, "format": "pdf", "bytes": path.stat().st_size}
        pages = len(PdfReader(path).pages)
        if not pages:
            fail("PDF contains no pages")
        return {
            "valid": True,
            "format": "pdf",
            "bytes": path.stat().st_size,
            "pages": pages,
        }
    except OSError as error:
        fail(f"unreadable PDF: {error}")
    except Exception as error:
        fail(f"invalid PDF: {error}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    path = args.file.expanduser().resolve()
    if not path.is_file():
        fail("file does not exist")

    suffix = path.suffix.lower()
    if suffix == ".epub":
        result = validate_epub(path)
    elif suffix == ".pdf":
        result = validate_pdf(path)
    else:
        fail("supported formats are .epub and .pdf")
    result["file"] = str(path)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
