# Copyright (c) 2026, Salesforce, Inc.
# SPDX-License-Identifier: Apache-2.0

"""Detect Tableau file type and handle twbx/tdsx zip round-trips in memory."""

import os
import zipfile

RAW_EXTS = (".twb", ".tds")
ZIP_EXTS = (".twbx", ".tdsx")
INNER_EXTS = (".twb", ".tds")


class ArchiveError(Exception):
    """Unsupported extension, corrupt zip, or wrong inner-document count."""


def _ext(path):
    return os.path.splitext(path)[1].lower()


def is_zip_kind(path):
    return _ext(path) in ZIP_EXTS


def validate_extension(path):
    if _ext(path) not in RAW_EXTS + ZIP_EXTS:
        raise ArchiveError(
            "expected .twb/.twbx/.tds/.tdsx, got '{}'".format(_ext(path) or "no extension")
        )


def _is_inner_document(name):
    if name.startswith("__MACOSX/") or "/__MACOSX/" in name:
        return False
    base = name.rsplit("/", 1)[-1]
    if base.startswith("._"):
        return False
    return os.path.splitext(name)[1].lower() in INNER_EXTS


def _load_raw(path):
    with open(path, "rb") as fh:
        data = fh.read()

    def repack(new_xml, out_path):
        with open(out_path, "wb") as out:
            out.write(new_xml)

    return data, repack


def _load_zip(path):
    try:
        with zipfile.ZipFile(path) as zin:
            infos = zin.infolist()
            inner = [i for i in infos if _is_inner_document(i.filename)]
            if len(inner) != 1:
                raise ArchiveError(f"expected exactly one inner .twb/.tds, found {len(inner)}")
            inner_name = inner[0].filename
            entries = [(i, zin.read(i)) for i in infos]
            inner_data = next(d for i, d in entries if i.filename == inner_name)
    except zipfile.BadZipFile as exc:
        raise ArchiveError("not a valid zip archive") from exc

    def repack(new_xml, out_path):
        with zipfile.ZipFile(out_path, "w") as zout:
            for info, data in entries:
                payload = new_xml if info.filename == inner_name else data
                zout.writestr(info, payload)

    return inner_data, repack


def load(path):
    """Return (inner_xml_bytes, repack). repack(new_xml, out_path) writes output."""
    if is_zip_kind(path):
        return _load_zip(path)
    return _load_raw(path)
