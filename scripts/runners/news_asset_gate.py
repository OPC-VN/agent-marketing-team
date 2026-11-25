"""Validate an edition's local visuals and prepare the chapters used by Top Story."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path, PureWindowsPath
import stat
from urllib.parse import parse_qsl, urlencode, urlsplit

from PIL import Image, ImageOps
from video_studio.image_right import ICONS

PATTERNS = {"process": "IG-04", "bars": "IG-07", "stats": "IG-08", "tags": "IG-01",
            "bullets": "IG-01", "compare": "IG-03", "timeline": "IG-06"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fingerprint(path):
    with Image.open(path) as image:
        gray = ImageOps.exif_transpose(image).convert("RGB").convert("L").resize(
            (9, 8), Image.Resampling.LANCZOS)
        visual = sum(1 << (y * 8 + x) for y in range(8) for x in range(8)
                     if gray.getpixel((x, y)) > gray.getpixel((x + 1, y)))
    return sha(path), visual


def local_asset(root, name):
    relative = PureWindowsPath(name)
    if relative.anchor or not relative.parts or any(
            part in (".", "..") or ":" in part for part in relative.parts):
        raise ValueError("asset must be a local relative path within this edition")
    path = root
    for part in relative.parts:
        path = path / part
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(
                stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
            raise ValueError("asset cannot use symlinks or junctions")
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("asset must be a regular local file within this edition")
    return path


def text(value):
    return isinstance(value, str) and bool(value.strip())


def source(value):
    url = urlsplit(value)
    if url.scheme != "https" or not url.hostname or url.username is not None:
        raise ValueError("an HTTPS source URL is required")
    return value


def image_key(value):
    url = urlsplit(source(value))
    query = [(name, val) for name, val in parse_qsl(url.query, keep_blank_values=True)
             if not name.lower().startswith("utm_") and name.lower() not in {"gclid", "fbclid"}]
    return url._replace(fragment="", query=urlencode(sorted(query))).geturl()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def history_index(directory, root, edition):
    images, urls = {}, set()
    prior = sorted(p for p in directory.iterdir() if p.is_dir() and p != root and p.name < edition)[-30:]
    for folder in prior:
        for p in folder.glob("*-top.json"):
            for chapter in read_json(p).get("top_story", {}).get("sections", []):
                for media in chapter.get("media") or []:
                    if not isinstance(media, dict):
                        continue
                    src = media.get("src", "")
                    if isinstance(src, str) and src.startswith("https://"):
                        urls.add(image_key(src))
        for p in folder.glob("*-assets.json"):
            report = read_json(p)
            for record in report.get("scenes", report.get("chapters", [])):
                if record.get("asset_url"):
                    urls.add(image_key(record["asset_url"]))
                if record.get("signature"):
                    images[tuple(record["signature"])] = folder.name
        for p in folder.iterdir():
            if p.is_file() and not p.is_symlink() and p.suffix.lower() in IMAGE_SUFFIXES:
                try:
                    images[fingerprint(p)] = folder.name
                except OSError:
                    continue
    return images, urls


def prepare(top, *, history=None, expected_chapters=4):
    root = top.resolve().parent
    data = read_json(top)
    story = data["top_story"]
    sections = story["sections"]
    if not isinstance(sections, list) or not sections or (
            expected_chapters and len(sections) != expected_chapters):
        required = str(expected_chapters) if expected_chapters else "at least one"
        raise ValueError(f"storyboard needs {required} chapters")
    if not all(text(story.get(k)) for k in ("headline", "intro", "intro_short", "outro", "outro_short")):
        raise ValueError("storyboard needs a headline and both intros/outros")
    edition = top.name.removesuffix("-top.json")
    images, urls = history_index(history or root.parent, root, edition)
    records = []
    story["visual_layout"] = "image-right"
    scenes = [story.get("cover_visual"), *sections, story.get("outro_visual")]
    for index, scene in enumerate(scenes):
        label = {0: "cover", len(scenes) - 1: "outro"}.get(index, f"chapter {index}")
        try:
            if not isinstance(scene, dict) or not text(scene.get("title")):
                raise ValueError("missing scene title or scene")
            if index in range(1, len(scenes) - 1) and not all(
                    text(scene.get(key)) for key in ("lead", "narration_short")):
                raise ValueError("missing Full/Short narration")
            diagram = scene["diagram"]
            pattern = PATTERNS.get(diagram["type"])
            items = diagram.get("items")
            if (not pattern or not isinstance(items, list) or not 2 <= len(items) <= 4 or not all(
                    isinstance(item, dict) and text(item.get("t")) and item.get("icon") in ICONS
                    for item in items)):
                raise ValueError("expected 2–4 infographic actions with supported semantic icons")
            proof = scene.pop("asset_proof")
            if proof.get("route", "image") != "image":
                raise ValueError("the right column needs a relevant standalone still image")
            if not all(text(proof.get(k)) for k in ("relevance", "credit", "motion_cue")):
                raise ValueError("document the image relevance, credit and infographic timing")
            fact_url = source(proof["fact_source_url"])
            image = local_asset(root, proof["image"])
            if image.suffix.lower() not in IMAGE_SUFFIXES:
                raise ValueError("expected a local still image")
            with Image.open(image) as decoded:
                if max(decoded.size) < 800 or min(decoded.size) < 300 or getattr(decoded, "is_animated", False):
                    raise ValueError("image must be a still large enough for Full/Short")
            signature = fingerprint(image)
            for earlier, origin in images.items():
                if earlier[0] == signature[0] or (earlier[1] ^ signature[1]).bit_count() <= 3:
                    raise ValueError(f"visual repeats or closely matches {origin}")
            link = source(proof["asset_url"])
            if image_key(link) in urls:
                raise ValueError("source image URL repeats")
            images[signature] = scene["title"]
            urls.add(image_key(link))
            relative = image.relative_to(root).as_posix()
            scene["media"] = [{"type": "image", "src": relative}]
            scene["media_credit"] = proof["credit"]
            scene["media_alt"] = proof["relevance"]
            if index in (0, len(scenes) - 1):
                key = "intro" if index == 0 else "outro"
                full, short = story[key], story[f"{key}_short"]
            else:
                narration = [scene["lead"], *[point.get("say") for point in (scene.get("points") or [])],
                             diagram.get("say"), *[item.get("say") for item in items]]
                full = " ".join(line for line in narration if text(line))
                short = scene["narration_short"]
            records.append({"chapter": scene["title"], "fact_source_url": fact_url, "asset_url": link,
                            "signature": signature, "vlog_pattern": pattern, "credit": proof["credit"],
                            "relevance": proof["relevance"], "motion_cue": proof["motion_cue"], "asset": relative,
                            "full": full, "short": short, "diagram": diagram})
        except (KeyError, OSError, ValueError, TypeError, AttributeError) as exc:
            raise ValueError(f"{label}: {exc}") from exc
    return data, {"headline": story["headline"], "scenes": records}


def write_json(path, data):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    temp.replace(path)


def write_storyboard(path, board):
    esc = html.escape
    parts = ["<!doctype html><html lang='vi'><meta charset='utf-8'><title>Storyboard</title>"
             "<style>body{font:18px system-ui;max-width:920px;margin:40px auto;padding:0 18px}"
             "article{border-top:1px solid #aaa;padding:14px 0;display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:20px 0}img{max-width:100%}</style>",
             f'<h1>{esc(board["headline"])}</h1>']
    for scene in board["scenes"]:
        asset = esc(scene["asset"])
        parts.append(f'<article><div class="copy"><h2>{esc(scene["chapter"])}</h2><ol>')
        for action in scene["diagram"]["items"]:
            parts.append(f'<li><b>{esc(action["t"])}</b> {esc(action.get("d", ""))}</li>')
        parts.append(f'</ol><p>{esc(scene["vlog_pattern"])} · {esc(scene["motion_cue"])}</p>'
                     f'<p><b>Full</b> {esc(scene["full"])}</p><p><b>Short</b> {esc(scene["short"])}</p></div>'
                     f'<figure><img src="{asset}" alt="{esc(scene["relevance"])}">'
                     f'<figcaption>{esc(scene["credit"])} · <a href="{esc(scene["asset_url"])}">Ảnh</a>'
                     f' · <a href="{esc(scene["fact_source_url"])}">Nguồn nội dung</a></figcaption></figure></article>')
    path.write_text("\n".join(parts) + "</html>\n", encoding="utf-8", newline="\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("top", type=Path)
    parser.add_argument("--history", type=Path)
    parser.add_argument("--expected-chapters", type=int, default=4, help="0 allows any nonempty chapter list")
    args = parser.parse_args()
    if args.expected_chapters < 0:
        parser.error("--expected-chapters must be nonnegative")
    prefix = args.top.name.removesuffix("-top.json")
    prepared = args.top.with_name(f"{prefix}-ready.json")
    prepared.unlink(missing_ok=True)
    try:
        data, board = prepare(args.top, history=args.history, expected_chapters=args.expected_chapters)
        write_storyboard(args.top.with_name(f"{prefix}-storyboard.html"), board)
        write_json(args.top.with_name(f"{prefix}-assets.json"), board)
        write_json(prepared, data)
    except (KeyError, OSError, ValueError, TypeError) as exc:
        parser.exit(2, f"Asset gate HOLD: {exc}\n")
    print(f"Asset gate PASS: {len(board['scenes'])} scenes; Full/Short storyboard ready")


if __name__ == "__main__":
    main()
