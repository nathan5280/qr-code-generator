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
  the command line. Generated images are written to an `output/`
  subdirectory next to it, which is gitignored -- the config is the
  thing worth version-controlling, not the "compiled" images.
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
| `format` | `svg`, `isvg` (inverted svg, see below), `png`, or `jpg`. |
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
<base>-<error_correction>-<dimensions>-<padded|not_padded>[-inverted].<format>
```

- `<base>` is `output_filename` if set, otherwise a filesystem-safe slug
  of the full URL (e.g. `https://www.goldenmakers.org` ->
  `https-www-goldenmakers-org`), so codes for different URLs dropped into
  the same directory stay distinguishable without decoding them.
- The error_correction/dimensions/padded differentiators are always
  included, even when a run doesn't vary that axis, so filenames stay
  consistent whether or not the config used lists.
- `-inverted` only appears for `isvg` output (a real `.svg` file,
  despite the config value) -- it doesn't apply to `svg`/`png`/`jpg`,
  so those filenames are unchanged.

## Inverted SVGs (`isvg`) for cutting/engraving

Motivating case: physically cutting or engraving a QR code where the
light area gets burned/cut away and the dark modules are what remain.
Doing that in Inkscape means selecting the shape you're going to cut --
and in a normal SVG, that shape is the union of the (scattered, many)
dark modules, not the thing being removed.

- Normal `svg`: the dark modules are combined into one `<path>` (so
  Inkscape sees one selectable object instead of one `<rect>` per
  module), sitting on a plain whole-canvas background `<rect>`.
- `isvg`: same two-shape structure, but which side is "the combined
  path" flips. The path instead unions every *light* cell, including
  the quiet zone, so selecting it targets everything to be cut/burned
  away. The background rect (now colored with what was
  `foreground_color`) represents what's left afterward.
- The final on-screen colors are identical between `svg` and its `isvg`
  counterpart -- `invert` changes which region is modeled as "the
  simple whole-canvas rect" vs. "the one editable combined path," not
  the colors themselves.
- Only meaningful for SVG; PNG/JPG have no equivalent "selectable
  path" concept, so `isvg` has no raster counterpart.

## Out of scope / explicitly deferred

- No support for embedding a logo/image in the center of the QR code.
- No support for rounded/dot-style modules (square modules only).
- `padding.width` and `padding.seed` are single values, not lists.
- `isvg`'s combined paths are simple per-module rectangle subpaths, not
  a true geometric union (adjacent same-color modules aren't merged
  into larger rectangles) -- sufficient for "one selectable object in
  Inkscape," not a minimal-vertex-count outline.
