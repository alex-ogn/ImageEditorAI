import pytest
from PIL import Image

from image_editor_ai.imaging import (
    box_to_canvas,
    edited_filename,
    fit_size,
    load_image,
    save_image,
)


@pytest.mark.parametrize(
    ("img", "box"),
    [
        ((1920, 1080), (1200, 740)),  # landscape, downscale
        ((1080, 1920), (1200, 740)),  # portrait
        ((100, 50), (1200, 740)),  # tiny image, upscale
        ((10000, 3000), (800, 600)),  # huge panorama
        ((500, 500), (300, 900)),  # square into tall box
    ],
)
def test_fit_size_fits_box_and_keeps_ratio(img, box):
    w, h = fit_size(*img, *box)
    assert w <= box[0] and h <= box[1]
    # At least one side touches the box edge: all available space is used.
    assert w == box[0] or h == box[1]
    # Aspect ratio preserved within one pixel of rounding.
    assert abs(w / h - img[0] / img[1]) <= img[0] / img[1] * (1 / min(w, h))


def test_fit_size_empty_box():
    assert fit_size(100, 100, 0, 50) == (0, 0)


def test_fit_size_rejects_invalid_image():
    with pytest.raises(ValueError):
        fit_size(0, 100, 100, 100)


def test_load_image_applies_exif_orientation(tmp_path):
    path = tmp_path / "rotated.jpg"
    exif = Image.Exif()
    exif[0x0112] = 6  # rotate 90° clockwise
    Image.new("RGB", (40, 20)).save(path, exif=exif)

    img = load_image(path)
    assert img.size == (20, 40)


def test_box_to_canvas_landscape_in_wide_box():
    # 200x100 image fitted into 800x200 -> 400x200, centered with x offset 200.
    assert box_to_canvas((0.0, 0.0, 1.0, 1.0), 200, 100, 800, 200) == (200, 0, 600, 200)
    assert box_to_canvas((0.25, 0.5, 0.75, 1.0), 200, 100, 800, 200) == (300, 100, 500, 200)


def test_box_to_canvas_portrait_in_tall_box():
    # 100x200 image fitted into 300x900 -> 300x600, centered with y offset 150.
    assert box_to_canvas((0.5, 0.25, 1.0, 0.5), 100, 200, 300, 900) == (150, 300, 300, 450)


@pytest.mark.parametrize(
    ("name", "fmt"),
    [("out.png", "PNG"), ("out.JPG", "JPEG"), ("out.jpeg", "JPEG"), ("out.webp", "WEBP")],
)
def test_save_image_picks_format_from_extension(tmp_path, name, fmt):
    path = save_image(Image.new("RGB", (30, 20), "red"), tmp_path / name)
    with Image.open(path) as saved:
        assert saved.format == fmt
        assert saved.size == (30, 20)


def test_save_image_flattens_alpha_for_jpeg(tmp_path):
    image = Image.new("RGBA", (10, 10), (0, 0, 0, 0))  # fully transparent
    path = save_image(image, tmp_path / "flat.jpg")
    with Image.open(path) as saved:
        assert saved.mode == "RGB"
        assert all(c > 250 for c in saved.getpixel((5, 5)))  # flattened onto white


def test_save_image_keeps_alpha_for_png(tmp_path):
    image = Image.new("RGBA", (10, 10), (10, 20, 30, 40))
    path = save_image(image, tmp_path / "alpha.png")
    with Image.open(path) as saved:
        assert saved.mode == "RGBA"
        assert saved.getpixel((0, 0)) == (10, 20, 30, 40)


def test_save_image_rejects_unknown_extension(tmp_path):
    with pytest.raises(ValueError):
        save_image(Image.new("RGB", (5, 5)), tmp_path / "image.xyz")
    with pytest.raises(ValueError):
        save_image(Image.new("RGB", (5, 5)), tmp_path / "noextension")


def test_edited_filename():
    assert edited_filename("photo.jpg") == "photo-edited.png"
    assert edited_filename("my.holiday.webp") == "my.holiday-edited.png"
