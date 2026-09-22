# qr-code-generator

Generates SVG/PNG/JPG QR codes from a TOML config file. The config file
lives in the same directory as its generated output.

## Setup (run once)

```
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Reactivate the venv (`source venv/bin/activate`) each new shell session
before running the script.

## Usage

```
mkdir -p output/my-qr-code
cp config.example.toml output/my-qr-code/config.toml
# edit output/my-qr-code/config.toml
python qr_gen.py output/my-qr-code
```

Images are written alongside config.toml in that directory.

## Generating a family of QR codes

`error_correction`, `dimensions`, `format`, and `[padding].enabled` can
each be a single value or a list. When any are lists, every combination
is generated in one run -- e.g. `format = ["svg", "png"]` with
`dimensions = [300, 600]` writes 4 files. This is handy for keeping a
matched set (same URL, different sizes and formats) together in one
directory.

Every generated file is named
`<base>-<error_correction>-<dimensions>-<padded|not_padded>.<format>` so
the family stays distinguishable and collision-free. `<base>` is
`output_filename` if you set one, otherwise a slug of the URL.

## Config reference

See `config.example.toml` for the full commented template. Summary:

| Section     | Key                 | Meaning                                                                 |
|-------------|---------------------|--------------------------------------------------------------------------|
| `[qr]`      | `url`               | The URL/text to encode                                                   |
|             | `error_correction`  | `L`/`M`/`Q`/`H` -- higher tolerates more damage but denser code -- value or list |
|             | `version`           | `"auto"` or `1`-`40` -- QR grid density/data capacity, not pixel size    |
|             | `border`            | Quiet zone width in modules (spec minimum is 4)                          |
| `[image]`   | `dimensions`        | Output pixel size (square) -- value or list                              |
|             | `format`            | `svg`, `png`, `jpg` -- value or list                                     |
|             | `foreground_color`  | Color name or hex code                                                   |
|             | `background_color`  | Color name, hex code, or `"transparent"` (svg/png only)                  |
|             | `output_filename`   | Base filename; blank auto-generates one from the URL                     |
| `[padding]` | `enabled`           | Turn on the decorative fake-QR-content ring outside the quiet zone -- value or list |
|             | `width`             | Width of that ring, in modules                                           |
|             | `seed`              | RNG seed so the fake pattern is reproducible across runs                 |

Scanners lock onto the QR's finder squares and expect a clean quiet zone
around them; the `[padding]` ring sits *outside* that zone, so it's
invisible to scanners but renders as more QR-like noise -- handy for
trimming a QR code into a round or irregular shape (e.g. dropping it
into a moon graphic on a sticker) without breaking scannability.
