#!/usr/bin/env python3
"""Generate an SVG/PNG/JPG QR code from a config.toml file.

Usage:
    python qr_gen.py /path/to/output/directory

The directory must contain a config.toml (see config.example.toml for the
template). The generated image is written into that same directory, next
to the config file.
"""

import argparse
import random
import sys
from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q
from PIL import Image, ImageColor, ImageDraw

try:
    import tomllib
except ImportError:
    import tomli as tomllib

CONFIG_FILENAME = "config.toml"

ERROR_CORRECTION_LEVELS = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}


def load_config(config_path: Path) -> dict:
    with config_path.open("rb") as f:
        return tomllib.load(f)


def build_module_grid(url, error_correction, version, border, padding_width, seed):
    """Return a square 2D list of booleans (True = dark module).

    The grid has three concentric regions, edge to center:
      - a decorative padding ring (fake modules, seeded random)
      - the quiet zone (must stay blank -- see note below)
      - the real QR matrix

    A scanner finds the QR by locking onto the three big finder squares
    and then expects a clean, empty margin (the "quiet zone") around
    them before it starts reading. Anything further out than that is
    invisible to the scanner, so the padding ring can be filled with
    fake-looking noise for visual effect without breaking scannability.
    """
    qr = qrcode.QRCode(
        version=None if version == "auto" else version,
        error_correction=ERROR_CORRECTION_LEVELS[error_correction],
        border=0,  # we draw the quiet zone ourselves below
    )
    qr.add_data(url)
    qr.make(fit=(version == "auto"))
    core = qr.get_matrix()  # list[list[bool]], core_size x core_size
    core_size = len(core)

    offset = padding_width + border
    grid_size = core_size + 2 * offset
    grid = [[False] * grid_size for _ in range(grid_size)]

    rng = random.Random(seed)
    for row in range(grid_size):
        for col in range(grid_size):
            dist_from_edge = min(row, col, grid_size - 1 - row, grid_size - 1 - col)
            if dist_from_edge < padding_width:
                grid[row][col] = rng.random() < 0.5
            elif dist_from_edge < offset:
                pass  # quiet zone: stays blank
            else:
                grid[row][col] = core[row - offset][col - offset]
    return grid


def resolve_color(value: str, need_alpha: bool):
    """Turn a config color string into an RGB(A) tuple for Pillow.

    'transparent' isn't a real CSS/Pillow color name -- it just means
    alpha=0 -- so it's handled as a special case here.
    """
    if value.lower() == "transparent":
        if not need_alpha:
            raise ValueError("background_color = \"transparent\" needs format = \"svg\" or \"png\" (jpg has no alpha channel)")
        return (0, 0, 0, 0)
    rgb = ImageColor.getrgb(value)  # accepts names ("white") and hex ("#1a1a1a")
    return (*rgb, 255) if need_alpha else rgb


def render_svg(grid, dimensions, fg_color, bg_color) -> str:
    # SVG understands color names, hex codes, and the "transparent"
    # keyword natively, so the config strings can be passed straight
    # through as fill attributes -- no color resolution needed here.
    grid_size = len(grid)
    module_px = dimensions / grid_size
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{dimensions}" height="{dimensions}" '
        f'viewBox="0 0 {dimensions} {dimensions}">',
        f'<rect width="{dimensions}" height="{dimensions}" fill="{bg_color}"/>',
    ]
    for row in range(grid_size):
        for col in range(grid_size):
            if grid[row][col]:
                x = col * module_px
                y = row * module_px
                parts.append(
                    f'<rect x="{x:.3f}" y="{y:.3f}" width="{module_px:.3f}" height="{module_px:.3f}" fill="{fg_color}"/>'
                )
    parts.append("</svg>")
    return "\n".join(parts)


def render_raster(grid, dimensions, fg, bg, mode) -> Image.Image:
    grid_size = len(grid)
    module_px = dimensions / grid_size
    img = Image.new(mode, (dimensions, dimensions), bg)
    draw = ImageDraw.Draw(img)
    for row in range(grid_size):
        for col in range(grid_size):
            if grid[row][col]:
                x0 = col * module_px
                y0 = row * module_px
                draw.rectangle([x0, y0, x0 + module_px, y0 + module_px], fill=fg)
    return img


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Directory containing config.toml; output is written here too.")
    args = parser.parse_args()

    config_path = args.directory / CONFIG_FILENAME
    if not config_path.exists():
        sys.exit(f"No {CONFIG_FILENAME} found in {args.directory}")
    config = load_config(config_path)

    qr_cfg = config.get("qr", {})
    image_cfg = config.get("image", {})
    padding_cfg = config.get("padding", {})

    if "url" not in qr_cfg:
        sys.exit("config.toml: [qr].url is required")
    url = qr_cfg["url"]
    error_correction = qr_cfg.get("error_correction", "M").upper()
    if error_correction not in ERROR_CORRECTION_LEVELS:
        sys.exit(f"config.toml: [qr].error_correction must be one of L, M, Q, H (got {error_correction!r})")
    version = qr_cfg.get("version", "auto")
    border = qr_cfg.get("border", 4)  # 4 modules is the QR spec's standard minimum quiet zone

    dimensions = image_cfg.get("dimensions", 600)
    fmt = image_cfg.get("format", "svg").lower()
    fg_color = image_cfg.get("foreground_color", "black")
    bg_color = image_cfg.get("background_color", "white")
    output_filename = image_cfg.get("output_filename", "qrcode")

    padding_enabled = padding_cfg.get("enabled", False)
    padding_width = padding_cfg.get("width", 0) if padding_enabled else 0
    seed = padding_cfg.get("seed", 0)

    grid = build_module_grid(url, error_correction, version, border, padding_width, seed)
    output_path = args.directory / f"{output_filename}.{fmt}"

    if fmt == "svg":
        output_path.write_text(render_svg(grid, dimensions, fg_color, bg_color))
    elif fmt in ("png", "jpg", "jpeg"):
        need_alpha = fmt == "png"
        try:
            fg = resolve_color(fg_color, need_alpha)
            bg = resolve_color(bg_color, need_alpha)
        except ValueError as exc:
            sys.exit(f"config.toml: {exc}")
        mode = "RGBA" if need_alpha else "RGB"
        img = render_raster(grid, dimensions, fg, bg, mode)
        img.save(output_path, format="PNG" if fmt == "png" else "JPEG")
    else:
        sys.exit(f"config.toml: [image].format must be svg, png, or jpg (got {fmt!r})")

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
