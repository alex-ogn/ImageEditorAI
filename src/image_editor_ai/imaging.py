"""Pure image helpers, independent of Tk so they can be unit-tested."""

from pathlib import Path

from PIL import Image, ImageOps

SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tif", ".tiff")

Box = tuple[float, float, float, float]  # left, top, right, bottom as image fractions (0..1)


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


def fitted_origin(fitted_w: int, fitted_h: int, box_w: int, box_h: int) -> tuple[int, int]:
    """Top-left corner of a fitted image centered in the box."""
    return ((box_w - fitted_w) // 2, (box_h - fitted_h) // 2)


def box_to_canvas(
    box: Box, img_w: int, img_h: int, box_w: int, box_h: int
) -> tuple[int, int, int, int]:
    """Map a (left, top, right, bottom) box in image fractions onto the fitted, centered image."""
    fitted_w, fitted_h = fit_size(img_w, img_h, box_w, box_h)
    x, y = fitted_origin(fitted_w, fitted_h, box_w, box_h)
    left, top, right, bottom = box
    return (
        x + round(left * fitted_w),
        y + round(top * fitted_h),
        x + round(right * fitted_w),
        y + round(bottom * fitted_h),
    )


def load_image(path: str | Path) -> Image.Image:
    """Open an image fully into memory, applying its EXIF orientation."""
    with Image.open(Path(path)) as img:
        img.load()
        return ImageOps.exif_transpose(img)


# Formats offered by "Save As…"; other extensions Pillow knows also work.
SAVE_FORMATS = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".webp": "WEBP"}


def edited_filename(name: str | Path) -> str:
    """Default "Save As…" name for an image opened as `name`, e.g. 'photo-edited.png'."""
    stem = Path(name).stem or "image"
    return f"{stem}-edited.png"


def save_image(image: Image.Image, path: str | Path) -> Path:
    """Save `image` at full resolution, picking the format from the file extension.

    JPEG has no alpha channel, so transparent images are flattened onto white first.
    """
    path = Path(path)
    ext = path.suffix.lower()
    fmt = SAVE_FORMATS.get(ext) or Image.registered_extensions().get(ext)
    if fmt is None:
        raise ValueError(f"Unsupported file extension: {path.suffix or '(none)'}")
    if fmt == "JPEG" and image.mode not in ("RGB", "L"):
        rgba = image.convert("RGBA")
        flat = Image.new("RGB", rgba.size, "white")
        flat.paste(rgba, mask=rgba.getchannel("A"))
        image = flat
    image.save(path, format=fmt)
    return path
