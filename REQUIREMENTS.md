# Requirements

## Goal

A Python script that generates QR codes as SVG (and PNG/JPG) files, driven
by a config file that lives alongside its generated output. Support
generating a matched family of related QR codes (same URL, different
sizes/formats/settings) in one run, self-named so the family stays
distinguishable in one directory without decoding each file.

## Environment

- A virtual environment (`venv/`) in the project's base directory, with
  dependencies pinned in `requirements.txt`.
- The output/config directory is a command-line argument, not hardcoded --
  each QR code (or family of them) gets its own directory.

## Config file

- TOML format, named `config.toml`, expected in the directory passed on
  the command line. Generated images are written into that same directory.
- `config.example.toml` in the repo serves as the copyable template.

### `[qr]`

| Key | Meaning |
|---|---|
| `url` | The URL/text to encode. Required. |
| `error_correction` | `L`/`M`/`Q`/`H`. Higher survives more damage/dirt but produces a denser code. |
| `version` | QR "version" 1-40: the grid density/data capacity, distinct from the final image's pixel dimensions. `"auto"` picks the smallest version that fits the URL. |
| `border` | Quiet zone width in modules. The QR spec's minimum is 4; don't go lower for anything meant to be scanned reliably. |

### `[image]`

| Key | Meaning |
|---|---|
| `dimensions` | Output image size in pixels (square). Avoids a separate resize step, and matters for PNG/JPG where there's no inherent vector scale. |
| `format` | `svg`, `png`, or `jpg`. |
| `foreground_color` | CSS color name or hex code. |
| `background_color` | CSS color name, hex code, or `"transparent"` (SVG/PNG only -- JPG has no alpha channel, so this combination is a config error). |
| `output_filename` | Base filename. Blank auto-generates one from the URL (see Output naming below). |

### `[padding]`

| Key | Meaning |
|---|---|
| `enabled` | Turns on a decorative ring of fake QR-like modules outside the real quiet zone. |
| `width` | Width of that ring, in modules. |
| `seed` | RNG seed for the fake pattern, so re-running the same config reproduces the same image. |

A QR scanner locks onto the three finder squares and then expects a clean
quiet zone around them before it starts reading; anything further out is
invisible to the scanner. That makes it safe to fill the space just beyond
the quiet zone with fake-looking noise for visual effect -- e.g. trimming
a QR code into a round or irregular shape (a moon graphic on a sticker)
without breaking scannability.

## Generating a family of QR codes

`error_correction`, `dimensions`, `format`, and `padding.enabled` can each
be a single value or a list. When any are lists, every combination is
generated in one run (e.g. 2 formats x 2 dimensions x 2 padding settings =
8 files), so a matched family can be produced from one config and one
invocation.

`padding.width` and `padding.seed` are not list-capable -- there's one
padding look per run, just an on/off toggle for whether it's applied.

## Output naming

Every generated file is named:

```
<base>-<error_correction>-<dimensions>-<padded|not_padded>.<format>
```

- `<base>` is `output_filename` if set, otherwise a filesystem-safe slug
  of the full URL (e.g. `https://www.goldenmakers.org` ->
  `https-www-goldenmakers-org`), so codes for different URLs dropped into
  the same directory stay distinguishable without decoding them.
- All four differentiators are always included, even when a run doesn't
  vary that axis, so filenames stay consistent whether or not the config
  used lists.

## Out of scope / explicitly deferred

- No support for embedding a logo/image in the center of the QR code.
- No support for rounded/dot-style modules (square modules only).
- `padding.width` and `padding.seed` are single values, not lists.
