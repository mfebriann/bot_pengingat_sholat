"""
Quote image rendering utilities.

Generates a simple white-background image containing an italic quote and an
optional source line (if available).
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Iterable

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]


def _candidate_font_paths(names: Iterable[str]) -> list[str]:
    candidates: list[str] = []

    windows_fonts = Path("C:/Windows/Fonts")
    if windows_fonts.exists():
        for name in names:
            candidates.append(str(windows_fonts / name))

    # Linux (Debian/Ubuntu) standard locations
    linux_bases = [
        Path("/usr/share/fonts/truetype/dejavu"),
        Path("/usr/share/fonts/truetype/liberation"),
        Path("/usr/share/fonts"),
        Path("/usr/local/share/fonts"),
    ]
    for base in linux_bases:
        if not base.exists():
            continue
        for name in names:
            # Check direct match
            p = base / name
            if p.exists():
                candidates.append(str(p))
            else:
                # Check recursively (limit depth to avoid performance issues)
                try:
                    for found in base.rglob(name):
                        candidates.append(str(found))
                        break # Take the first one we find for this name
                except Exception:
                    pass

    # macOS locations
    mac_bases = [
        Path("/Library/Fonts"),
        Path("/System/Library/Fonts"),
    ]
    for base in mac_bases:
        if base.exists():
            for name in names:
                candidates.append(str(base / name))

    # Also try bare names (Pillow can sometimes resolve)
    candidates.extend(names)
    return candidates


def _load_font(names: Iterable[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if ImageFont is None:  # pragma: no cover
        raise RuntimeError("Pillow is required to render quote images.")
    for path in _candidate_font_paths(names):
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    text = " ".join(text.replace("\n", " ").split())
    if not text:
        return [""]

    words = text.split(" ")
    lines: list[str] = []
    current: list[str] = []

    for word in words:
        test = (" ".join(current + [word])).strip()
        if draw.textlength(test, font=font) <= max_width or not current:
            current.append(word)
            continue

        lines.append(" ".join(current))
        current = [word]

    if current:
        lines.append(" ".join(current))
    return lines


def _faux_italic_render(
    base: Image.Image,
    position: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    shear: float = 0.22,
) -> None:
    tmp = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    tmp_draw = ImageDraw.Draw(tmp)
    bbox = tmp_draw.textbbox((0, 0), text, font=font)
    w = max(1, bbox[2] - bbox[0])
    h = max(1, bbox[3] - bbox[1])

    pad = 8
    text_img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_img)
    text_draw.text((pad - bbox[0], pad - bbox[1]), text, font=font, fill=fill)

    new_w = int(text_img.size[0] + abs(shear) * text_img.size[1]) + 1
    slanted = text_img.transform(
        (new_w, text_img.size[1]),
        Image.AFFINE,
        (1, shear, 0, 0, 1, 0),
        resample=Image.BICUBIC,
    )
    base.alpha_composite(slanted, dest=position)


def generate_quote_image_jpeg(
    quote_text: str,
    *,
    source_text: str | None = None,
    width: int = 1080,
    height: int = 1080,
) -> BytesIO:
    """
    Render quote text to a JPEG and return as a BytesIO (ready for Telegram).
    """
    if Image is None or ImageDraw is None or ImageFont is None:  # pragma: no cover
        raise RuntimeError("Pillow is not installed. Install it with: pip install Pillow")
    image = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)

    margin = 90
    max_width = width - margin * 2

    quote_font = _load_font(
        [
            "timesi.ttf",
            "georgiai.ttf",
            "calibrii.ttf",
            "ariali.ttf",
            "DejaVuSerif-Italic.ttf",
            "DejaVuSans-Oblique.ttf",
            "DejaVuSans.ttf",
        ],
        size=52,
    )
    source_font = _load_font(
        [
            "times.ttf",
            "georgia.ttf",
            "calibri.ttf",
            "arial.ttf",
            "DejaVuSerif.ttf",
            "DejaVuSans.ttf",
        ],
        size=30,
    )

    quote_lines = _wrap_text(draw, quote_text, quote_font, max_width=max_width)
    source_lines: list[str] = []
    if source_text:
        source_lines = _wrap_text(draw, f"— {source_text}", source_font, max_width=max_width)

    line_gap = 14
    source_gap = 24 if source_lines else 0

    quote_heights = [draw.textbbox((0, 0), line, font=quote_font)[3] for line in quote_lines]
    source_heights = [draw.textbbox((0, 0), line, font=source_font)[3] for line in source_lines]

    total_h = 0
    if quote_lines:
        total_h += sum(quote_heights) + line_gap * (len(quote_lines) - 1)
    if source_lines:
        total_h += source_gap + sum(source_heights) + 8 * (len(source_lines) - 1)

    y = max(margin, (height - total_h) // 2)

    for idx, line in enumerate(quote_lines):
        bbox = draw.textbbox((0, 0), line, font=quote_font)
        line_w = bbox[2] - bbox[0]
        x = (width - line_w) // 2
        _faux_italic_render(image, (x, y), line, quote_font, (0, 0, 0))
        y += quote_heights[idx] + line_gap

    if source_lines:
        y += source_gap
        for idx, line in enumerate(source_lines):
            bbox = draw.textbbox((0, 0), line, font=source_font)
            line_w = bbox[2] - bbox[0]
            x = (width - line_w) // 2
            draw.text((x, y), line, font=source_font, fill=(0, 0, 0))
            y += source_heights[idx] + 8

    out = BytesIO()
    rgb = image.convert("RGB")
    rgb.save(out, format="JPEG", quality=92, optimize=True)
    out.seek(0)
    return out
