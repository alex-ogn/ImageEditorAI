"""Pure image helpers, independent of Tk so they can be unit-tested."""

from pathlib import Path

from PIL import Image, ImageOps

SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tif", ".tiff")


def fit_size(img_w: int, img_h: int, box_w: int, box_h: int) -> tuple[int, int]:
    """Largest size that fits inside the box while keeping the image's aspect ratio.

    A single scale factor is applied to both sides, so the ratio never changes
    (apart from rounding to whole pixels). Images are scaled up or down.
    """
    if img_w <= 0 or img_h <= 0:
        raise ValueError("Image dimensions must be positive")
    if box_w <= 0 or box_h <= 0:
        return (0, 0)
    scale = min(box_w / img_w, box_h / img_h)
    return (max(1, round(img_w * scale)), max(1, round(img_h * scale)))


def load_image(path: str | Path) -> Image.Image:
    """Open an image fully into memory, applying its EXIF orientation."""
    with Image.open(Path(path)) as img:
        img.load()
        return ImageOps.exif_transpose(img)
