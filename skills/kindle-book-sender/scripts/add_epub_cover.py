#!/usr/bin/env python3
"""Embed a Kindle-safe PNG title cover in an EPUB without changing its chapters."""

from __future__ import annotations

import argparse
import html
import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path, PurePosixPath

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as error:
    raise SystemExit("Pillow is required to create a PNG cover: pip install Pillow") from error


OPF = "http://www.idpf.org/2007/opf"
DC = "http://purl.org/dc/elements/1.1/"
ET.register_namespace("", OPF)
ET.register_namespace("dc", DC)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child(root: ET.Element, name: str) -> ET.Element:
    found = next((element for element in root if local_name(element.tag) == name), None)
    if found is None:
        raise SystemExit(f"EPUB package is missing {name}")
    return found


def rootfile(archive: zipfile.ZipFile) -> str:
    container = ET.fromstring(archive.read("META-INF/container.xml"))
    for element in container.iter():
        if local_name(element.tag) == "rootfile" and element.get("full-path"):
            return element.get("full-path")
    raise SystemExit("EPUB container has no package rootfile")


def font(size: int):
    for path in (
        "/System/Library/Fonts/Supplemental/Georgia.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def wrapped(draw: ImageDraw.ImageDraw, text: str, face, maximum: int) -> list[str]:
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if not current or draw.textlength(candidate, font=face) <= maximum:
            current = candidate
        else:
            lines.append(current)
            current = word
    return lines + ([current] if current else [])


def cover_png(title: str, author: str) -> bytes:
    image = Image.new("RGB", (1600, 2560), "#f6f1e5")
    draw = ImageDraw.Draw(image)
    navy, gold = "#172b3a", "#b08a40"
    draw.rectangle((90, 90, 1510, 2470), outline=gold, width=8)
    title_font, author_font = font(116), font(66)
    lines = wrapped(draw, title, title_font, 1120)
    y = 980 - (len(lines) - 1) * 75
    for line in lines:
        bounds = draw.textbbox((0, 0), line, font=title_font)
        draw.text(((1600 - (bounds[2] - bounds[0])) / 2, y), line, fill=navy, font=title_font)
        y += 160
    bounds = draw.textbbox((0, 0), author, font=author_font)
    draw.text(((1600 - (bounds[2] - bounds[0])) / 2, 1900), author, fill=navy, font=author_font)
    output = BytesIO()
    image.save(output, "PNG", optimize=True)
    return output.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--title")
    parser.add_argument("--author", default="")
    parser.add_argument("--replace", action="store_true", help="replace an existing EPUB cover declaration")
    args = parser.parse_args()
    if args.output.resolve() == args.input.resolve():
        raise SystemExit("write to a different output path; preserve the original EPUB")

    with zipfile.ZipFile(args.input) as source:
        opf_path = rootfile(source)
        package = ET.fromstring(source.read(opf_path))
        metadata, manifest, spine = (child(package, name) for name in ("metadata", "manifest", "spine"))
        items = [element for element in manifest if local_name(element.tag) == "item"]
        has_cover = any("cover-image" in item.get("properties", "").split() for item in items)
        if has_cover and not args.replace:
            raise SystemExit("EPUB already declares a cover; use --replace only when that cover is unsuitable")
        title = args.title or next((element.text for element in metadata.iter() if local_name(element.tag) == "title" and element.text), args.input.stem)

        for item in items:
            properties = [value for value in item.get("properties", "").split() if value != "cover-image"]
            if properties:
                item.set("properties", " ".join(properties))
            else:
                item.attrib.pop("properties", None)
        for element in list(metadata):
            if local_name(element.tag) == "meta" and element.get("name") == "cover":
                metadata.remove(element)

        opf_dir = PurePosixPath(opf_path).parent
        cover_png_path = str(opf_dir / "kindle-cover.png")
        cover_xhtml_path = str(opf_dir / "kindle-cover.xhtml")
        ET.SubElement(manifest, f"{{{OPF}}}item", {"id": "kindle-cover-image", "href": "kindle-cover.png", "media-type": "image/png", "properties": "cover-image"})
        ET.SubElement(manifest, f"{{{OPF}}}item", {"id": "kindle-cover-page", "href": "kindle-cover.xhtml", "media-type": "application/xhtml+xml"})
        ET.SubElement(metadata, f"{{{OPF}}}meta", {"name": "cover", "content": "kindle-cover-image"})
        spine.insert(0, ET.Element(f"{{{OPF}}}itemref", {"idref": "kindle-cover-page"}))
        image_ref = "kindle-cover.png"
        cover_xhtml = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>{html.escape(title)}</title><style>html,body{{margin:0;padding:0;height:100%;}}img{{height:100%;width:100%;object-fit:contain;}}</style></head><body><img src="{image_ref}" alt="{html.escape(title)}"/></body></html>'''.encode("utf-8")
        replacements = {
            opf_path: ET.tostring(package, encoding="utf-8", xml_declaration=True),
            cover_png_path: cover_png(title, args.author),
            cover_xhtml_path: cover_xhtml,
        }
        with zipfile.ZipFile(args.output, "w") as destination:
            mimetype = source.read("mimetype")
            info = zipfile.ZipInfo("mimetype")
            info.compress_type = zipfile.ZIP_STORED
            destination.writestr(info, mimetype)
            for source_info in source.infolist():
                if source_info.filename == "mimetype" or source_info.filename in replacements:
                    continue
                destination.writestr(source_info, source.read(source_info.filename))
            for name, data in replacements.items():
                destination.writestr(name, data)
    print(f"Added PNG cover: {args.output}")


if __name__ == "__main__":
    main()
