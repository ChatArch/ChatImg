"""Local four-square diamond weaving; no generation, profiles or network IO."""

from __future__ import annotations

from collections.abc import Sequence
from math import floor
from os import PathLike
from pathlib import Path

from PIL import Image, ImageChops, ImageOps

ImageSource = str | PathLike[str] | Image.Image

__all__ = ["create_diamond_collage", "save_diamond_collage"]


def create_diamond_collage(
    images: Sequence[ImageSource], *, tile_height: int = 300
) -> Image.Image:
    """Weave four square images into one RGB image on a black background.

    Sources may be paths or Pillow images and are not modified. Quadrants run
    TL, TR, BR, BL, rotating -45, 45, 135 and 225 degrees respectively. The
    original recipe's two offset layers, repeated first quadrant and cropped
    edges are retained. Odd square sizes keep their last row and column.

    ``tile_height`` must be an integer from 2 to 2000. Width is
    ``int(tile_height * 1.426)``; canvas dimensions are 4.5 widths by 2.5 heights
    (rounded down), matching the supplied recipe. Transparent pixels flatten
    onto black. No intermediate files are created.
    """
    if isinstance(images, (str, bytes, PathLike)) or len(images) != 4:
        raise ValueError("Exactly four square images are required.")
    if type(tile_height) is not int or not 2 <= tile_height <= 2000:
        raise ValueError("tile_height must be an integer from 2 to 2000.")

    h = tile_height
    w = int(h * 1.426)
    canvas = Image.new("RGBA", (int(4.5 * w), int(2.5 * h)), "black")
    occupied = Image.new("L", canvas.size, 0)
    # Input order is significant. Draw the second layer after the first,
    # rather than adding uint8 pixels (which corrupts colors and alpha).
    rows = (
        ((0, 0), (0, 2 * h)),
        ((0, h),),
        ((-w / 2, -h / 2), (-w / 2, 1.5 * h)),
        ((-w / 2, h / 2),),
    )
    turns = (None, Image.Transpose.ROTATE_90,
             Image.Transpose.ROTATE_180, Image.Transpose.ROTATE_270)
    for index, (source, positions) in enumerate(zip(images, rows), 1):
        if isinstance(source, Image.Image):
            image = ImageOps.exif_transpose(source).convert("RGBA")
        else:
            with Image.open(source) as opened:
                image = ImageOps.exif_transpose(opened).convert("RGBA")
        side = image.width
        if side != image.height:
            raise ValueError(f"Image {index} must be square, got {image.size}.")
        if side < 2:
            raise ValueError(f"Image {index} must be at least 2 by 2 pixels.")
        half = side // 2
        boxes = ((0, 0, half, half), (half, 0, side, half),
                 (half, half, side, side), (0, half, half, side))
        for quadrant, (box, turn) in enumerate(zip(boxes, turns)):
            piece = image.crop(box)
            if turn is not None:
                piece = piece.transpose(turn)
            pw, ph = piece.size
            # Inverse of a -45 degree rotation followed by independent x/y
            # scaling. Mapping edge-to-edge avoids rotate(expand=True)'s extra
            # padding and keeps neighboring diamonds joined.
            for x, y in positions:
                px, py = floor(x), floor(y)
                dx, dy = px - x, py - y
                # Preserve exact half-tile positions when w/h are odd. Rounding
                # the row origin before sampling leaves one-pixel black seams.
                # A tiny inward sampling bias includes exact boundary pixels
                # despite floating-point roundoff; ownership below ensures
                # those pixels are used once, including with transparent input.
                sx, sy = pw * (1 - 1e-10), ph * (1 - 1e-10)
                matrix = (
                    sx / w, sx / h, pw / 2 - sx + sx * (dx / w + dy / h),
                    -sy / w, sy / h, ph / 2 + sy * (-dx / w + dy / h),
                )
                diamond = piece.transform(
                    (w + 1, h + 1), Image.Transform.AFFINE,
                    matrix,
                    resample=Image.Resampling.BICUBIC,
                    fillcolor=(0, 0, 0, 0),
                )
                footprint = Image.new("RGBA", piece.size, "white").transform(
                    diamond.size, Image.Transform.AFFINE, matrix,
                    resample=Image.Resampling.BICUBIC, fillcolor=(0, 0, 0, 0),
                ).getchannel("A")
                columns = (quadrant, 4) if quadrant == 0 else (quadrant,)
                for column in columns:
                    dest = (px + column * w, py)
                    box = (*dest, dest[0] + diamond.width, dest[1] + diamond.height)
                    available = ImageChops.subtract(footprint, occupied.crop(box))
                    canvas.paste(diamond, dest, available)
                    occupied.paste(255, dest, footprint)
    result = Image.new("RGB", canvas.size, "black")
    result.paste(canvas, mask=canvas.getchannel("A"))
    return result


def save_diamond_collage(
    images: Sequence[ImageSource],
    output: str | PathLike[str],
    *,
    tile_height: int = 300,
) -> Path:
    """Create the weave and save one PNG/JPEG/WebP; never overwrite a file.

    Return the output Path. Parent directories are created after inputs have
    validated. A failed encode removes only the newly created partial file.
    """
    path = Path(output)
    formats = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".webp": "WEBP"}
    image_format = formats.get(path.suffix.lower())
    if image_format is None:
        raise ValueError("Output must use .png, .jpg, .jpeg or .webp.")
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"Output already exists: {path}")
    image = create_diamond_collage(images, tile_height=tile_height)
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("xb")
    try:
        with stream:
            image.save(stream, format=image_format)
    except Exception:
        # Close before unlinking, including on Windows.
        path.unlink(missing_ok=True)
        raise
    return path
