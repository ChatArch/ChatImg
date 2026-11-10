"""Offline contracts for the four-square, two-layer diamond weave."""

import importlib
import importlib.util
from pathlib import Path

import pytest
from click.testing import CliRunner
from PIL import Image, ImageDraw

from chatimg.cli import main


COLORS = (
    ((210, 30, 40), (230, 70, 30), (240, 130, 40), (200, 90, 100)),
    ((20, 160, 80), (40, 190, 100), (90, 170, 60), (20, 130, 120)),
    ((30, 70, 210), (60, 100, 230), (80, 140, 210), (100, 60, 190)),
    ((210, 140, 20), (230, 170, 30), (200, 190, 40), (180, 120, 50)),
)


def api():
    assert importlib.util.find_spec("chatimg.collage") is not None, (
        "ChatImg needs an importable local collage API"
    )
    return importlib.import_module("chatimg.collage")


def square(colors, size=80):
    image = Image.new("RGB", (size, size))
    half = size // 2
    boxes = ((0, 0, half, half), (half, 0, size, half),
             (half, half, size, size), (0, half, half, size))
    for box, color in zip(boxes, colors):
        image.paste(color, box)
    return image


@pytest.fixture
def paths(tmp_path):
    result = []
    for index, colors in enumerate(COLORS, 1):
        path = tmp_path / f"{index}.png"
        square(colors).save(path)
        result.append(path)
    return result


def test_layout_preserves_image_quadrant_order_repetition_and_offset(paths):
    h = 80
    w = int(h * 1.426)
    result = api().create_diamond_collage(paths, tile_height=h)
    assert result.size == (int(4.5 * w), int(2.5 * h))
    assert result.mode == "RGB"
    # Layer one: image 1 then image 2, with quadrant 1 repeated at right.
    for image_index, y in ((0, h // 2), (1, h + h // 2)):
        for tile in range(5):
            x = tile * w + w // 2
            if x < result.width:
                assert result.getpixel((x, y)) == COLORS[image_index][tile % 4]
    # Layer two: image 4 in the middle, image 3 at the bottom offset row.
    for image_index, y in ((3, h), (2, 2 * h)):
        for tile in range(1, 5):
            assert result.getpixel((tile * w, y)) == COLORS[image_index][tile % 4]
    # The two clipped rows preserve the original image 3 top and image 1 bottom.
    assert result.getpixel((w, 1)) == COLORS[2][1]
    assert result.getpixel((w // 2, result.height - 2)) == COLORS[0][0]


def test_quadrants_rotate_minus45_plus45_plus135_plus225():
    image = Image.new("RGB", (160, 160), "#223344")
    draw = ImageDraw.Draw(image)
    for x, y in ((0, 0), (80, 0), (80, 80), (0, 80)):
        draw.rectangle((x + 52, y + 12, x + 68, y + 28), fill="white")
    h = 120
    w = int(h * 1.426)
    result = api().create_diamond_collage([image] * 4, tile_height=h)
    # The same upper-right source marker goes right/up/left/down by quadrant.
    for tile, (u, v) in enumerate(((0.75, 0.5), (0.5, 0.25),
                                 (0.25, 0.5), (0.5, 0.75))):
        pixel = result.getpixel((int((tile + u) * w), int(v * h)))
        assert min(pixel) > 240


def test_default_dimensions_match_original_recipe():
    image = Image.new("RGB", (8, 8), "red")
    result = api().create_diamond_collage([image] * 4)
    assert result.size == (int(4.5 * int(300 * 1.426)), int(2.5 * 300))


def test_odd_squares_keep_last_row_and_column_without_mutating_input():
    image = Image.new("RGB", (5, 5), "black")
    image.putpixel((4, 4), (255, 255, 255))
    before = image.tobytes()
    result = api().create_diamond_collage([image] * 4, tile_height=40)
    assert result.getbbox() is not None
    assert image.tobytes() == before


def test_transparent_inputs_composite_on_black_without_alpha_overflow():
    image = Image.new("RGBA", (32, 32), (200, 100, 50, 128))
    result = api().create_diamond_collage([image] * 4, tile_height=40)
    w = int(40 * 1.426)
    assert result.getpixel((w // 2, 20)) == (100, 50, 25)
    empty = Image.new("RGBA", (32, 32), (255, 255, 255, 0))
    assert api().create_diamond_collage([empty] * 4, tile_height=40).getbbox() is None


@pytest.mark.parametrize("height", [2, 3, 29, 30, 40, 41, 80, 299, 300, 301])
def test_opaque_white_weave_has_no_black_gaps_or_pixel_addition_overflow(height):
    image = Image.new("RGB", (9, 9), "white")
    result = api().create_diamond_collage([image] * 4, tile_height=height)
    assert result.getextrema() == ((255, 255),) * 3
    translucent = Image.new("RGBA", (9, 9), (200, 100, 50, 128))
    result = api().create_diamond_collage([translucent] * 4, tile_height=height)
    assert result.getextrema() == ((100, 100), (50, 50), (25, 25))


@pytest.mark.parametrize("count", [0, 3, 5])
def test_api_requires_exactly_four_images(count):
    image = Image.new("RGB", (8, 8))
    with pytest.raises(ValueError, match="four"):
        api().create_diamond_collage([image] * count)


@pytest.mark.parametrize("size", [(32, 16), (1, 1)])
def test_api_rejects_non_square_or_too_small_sources(size):
    image = Image.new("RGB", size)
    with pytest.raises(ValueError, match="square|least"):
        api().create_diamond_collage([image] * 4)


@pytest.mark.parametrize("height", [0, -1, True, 1.5, 2001])
def test_invalid_tile_height_is_rejected(height):
    image = Image.new("RGB", (8, 8))
    with pytest.raises(ValueError, match="tile_height"):
        api().create_diamond_collage([image] * 4, tile_height=height)


def test_save_api_creates_only_the_final_output(paths, tmp_path):
    output = tmp_path / "nested" / "collage.png"
    saved = api().save_diamond_collage(paths, output, tile_height=40)
    assert saved == output
    with Image.open(output) as result:
        assert result.format == "PNG"
        assert result.size == (int(4.5 * int(40 * 1.426)), 100)
    assert list(output.parent.iterdir()) == [output]


def test_save_refuses_existing_file_and_preserves_its_bytes(paths):
    before = paths[0].read_bytes()
    with pytest.raises(FileExistsError):
        api().save_diamond_collage(paths, paths[0], tile_height=40)
    assert paths[0].read_bytes() == before


def test_cli_generates_an_actual_image_offline(paths, tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Local collage must not initialize a generator or credentials")

    monkeypatch.setattr("chatimg.image.cli.create_generator", forbidden)
    output = tmp_path / "cli.png"
    result = CliRunner().invoke(main, ["collage", "diamond", *map(str, paths),
                                      "--tile-height", "40", "-o", str(output)])
    assert result.exit_code == 0, result.output
    assert str(output) in result.output
    with Image.open(output) as image:
        assert image.size == (int(4.5 * int(40 * 1.426)), 100)


@pytest.mark.parametrize("count", [3, 5])
def test_cli_rejects_wrong_image_count(paths, tmp_path, count):
    output = tmp_path / "missing.png"
    inputs = (paths + [paths[0]])[:count]
    result = CliRunner().invoke(main, ["collage", "diamond", *map(str, inputs),
                                      "-o", str(output)])
    assert result.exit_code != 0
    assert "No such command" not in result.output
    assert not output.exists()


def test_cli_tree_exposes_implemented_collage_command():
    result = CliRunner().invoke(main, ["--tree"])
    assert result.exit_code == 0
    assert "collage  #" in result.output
    assert "diamond" in result.output
    assert "--tile-height TILE-HEIGHT" in result.output
