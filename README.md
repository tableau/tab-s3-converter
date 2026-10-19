# tab-s3-converter

Migrate a Tableau workbook or data source from the legacy **S3** connector
(`class='s3'`) to the modern **Amazon S3** connector (`class='amazon-s3'`).

The tool has **no runtime dependencies** — it uses only the Python standard
library. Dev/test tooling (pytest, ruff) is managed with [uv](https://docs.astral.sh/uv/).

## Usage

    python -m tab_s3_converter <input> [-o output] [--force] [--debug]

- `<input>` — a `.twb`, `.tds`, `.twbx`, or `.tdsx` file.
- `-o/--output` — output path (default: `<name>.converted.<ext>`).
- `--force` — overwrite an existing output file.
- `--debug` — print a traceback instead of a one-line error.

The original file is never modified. `.twbx`/`.tdsx` archives are rewritten
with all supporting files preserved byte-for-byte; only the inner document is
converted.

## What it does

For each `s3` connection it: parses `bucket`/`region` out of the JSON
`connectionData`, rewrites the connection to the `amazon-s3` attribute set
(auth `auth-user-pass`, blank credentials — Tableau prompts on open), renames
the `s3.<id>` named-connection to `amazon-s3.<id>` and updates all references,
and replaces the relation's column list with CSV parse options. Per-column
`<metadata-records>` are preserved unchanged, so `ordinal`, `local-name`, and
`local-type` carry forward exactly.

## Development

    uv run pytest          # run the test suite
    uvx ruff check .       # lint
    uvx ruff format .      # format
