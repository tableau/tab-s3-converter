# Copyright (c) 2026, Salesforce, Inc.
# SPDX-License-Identifier: Apache-2.0

"""Command-line orchestration for tab-s3-converter."""

import argparse
import os
import sys
import xml.etree.ElementTree as ET

from . import archive, serialize, transform

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_PARSE = 3
EXIT_CONNECTION_DATA = 4


def default_output_path(input_path):
    root, ext = os.path.splitext(input_path)
    return f"{root}.converted{ext}"


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="tab_s3_converter",
        description="Migrate a Tableau file from the s3 connector to amazon-s3.",
    )
    parser.add_argument("input", help="path to a .twb/.tds/.twbx/.tdsx file")
    parser.add_argument("-o", "--output", help="output path (default: <name>.converted.<ext>)")
    parser.add_argument("--force", action="store_true", help="overwrite output if it exists")
    parser.add_argument("--debug", action="store_true", help="re-raise errors with traceback")
    return parser


def run(argv):
    args = _build_parser().parse_args(argv)
    debug = args.debug

    def fail(message, code):
        exc = sys.exc_info()[1]
        if debug and exc is not None:
            raise exc
        print(f"error: {message}", file=sys.stderr)
        return code

    try:
        archive.validate_extension(args.input)
    except archive.ArchiveError as exc:
        return fail(str(exc), EXIT_USAGE)

    if not os.path.isfile(args.input):
        return fail(f"no such file: {args.input}", EXIT_USAGE)

    output = args.output or default_output_path(args.input)
    if os.path.exists(output) and not args.force:
        return fail(f"output exists (use --force): {output}", EXIT_USAGE)

    try:
        xml_bytes, repack = archive.load(args.input)
    except archive.ArchiveError as exc:
        return fail(str(exc), EXIT_PARSE)
    except OSError as exc:
        return fail(f"cannot read input: {exc}", EXIT_USAGE)

    try:
        root, prefix = serialize.parse_document(xml_bytes)
    except ET.ParseError as exc:
        return fail(f"could not parse XML: {exc}", EXIT_PARSE)

    try:
        count = transform.convert(root)
    except transform.TransformError as exc:
        return fail(str(exc), EXIT_CONNECTION_DATA)

    if count == 0:
        print("nothing to convert (no s3 connections found)")
        return EXIT_OK

    new_bytes = serialize.serialize_document(root, prefix)
    try:
        repack(new_bytes, output)
    except OSError:
        return fail(f"cannot write output: {output}", EXIT_USAGE)
    print(f"converted {count} connection(s) -> {output}")
    return EXIT_OK
