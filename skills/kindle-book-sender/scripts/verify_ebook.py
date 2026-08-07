#!/usr/bin/env python3
"""Validate an EPUB or PDF before Kindle delivery."""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path


def fail(message: str) -> None:
    print(json.dumps({"valid": False, "error": message}))
    raise SystemExit(1)


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
            return {
                "valid": True,
                "format": "epub",
                "bytes": path.stat().st_size,
                "members": len(archive.infolist()),
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
