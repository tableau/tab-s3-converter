# Copyright (c) 2026, Salesforce, Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import tempfile
import unittest
import zipfile

from tab_s3_converter.archive import (
    ArchiveError,
    is_zip_kind,
    load,
    validate_extension,
)


class ExtensionTest(unittest.TestCase):
    def test_is_zip_kind(self):
        self.assertTrue(is_zip_kind("a.twbx"))
        self.assertTrue(is_zip_kind("A.TDSX"))
        self.assertFalse(is_zip_kind("a.twb"))

    def test_validate_extension_accepts_supported(self):
        for name in ("a.twb", "a.tds", "a.twbx", "a.tdsx", "A.TWB"):
            validate_extension(name)  # no raise

    def test_validate_extension_rejects_other(self):
        with self.assertRaises(ArchiveError):
            validate_extension("a.xml")


class LoadRawTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_raw_twb_roundtrip(self):
        src = os.path.join(self.dir, "in.twb")
        with open(src, "wb") as fh:
            fh.write(b"<workbook />")
        data, repack = load(src)
        self.assertEqual(data, b"<workbook />")
        out = os.path.join(self.dir, "out.twb")
        repack(b"<workbook converted='1' />", out)
        with open(out, "rb") as fh:
            self.assertEqual(fh.read(), b"<workbook converted='1' />")


class LoadZipTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.src = os.path.join(self.dir, "in.twbx")
        with zipfile.ZipFile(self.src, "w") as zf:
            zf.writestr("Data/extract.hyper", b"BINARY-DATA")
            zf.writestr("in.twb", b"<workbook />")

    def test_zip_returns_inner_document_bytes(self):
        data, _ = load(self.src)
        self.assertEqual(data, b"<workbook />")

    def test_zip_repack_substitutes_only_inner_doc(self):
        _, repack = load(self.src)
        out = os.path.join(self.dir, "out.twbx")
        repack(b"<workbook converted='1' />", out)
        with zipfile.ZipFile(out) as zf:
            self.assertEqual(zf.read("in.twb"), b"<workbook converted='1' />")
            self.assertEqual(zf.read("Data/extract.hyper"), b"BINARY-DATA")
            self.assertEqual(sorted(zf.namelist()), ["Data/extract.hyper", "in.twb"])

    def test_zip_with_no_inner_document_raises(self):
        bad = os.path.join(self.dir, "none.twbx")
        with zipfile.ZipFile(bad, "w") as zf:
            zf.writestr("Data/x.hyper", b"x")
        with self.assertRaises(ArchiveError):
            load(bad)

    def test_zip_with_two_inner_documents_raises(self):
        bad = os.path.join(self.dir, "two.twbx")
        with zipfile.ZipFile(bad, "w") as zf:
            zf.writestr("a.twb", b"<workbook />")
            zf.writestr("b.twb", b"<workbook />")
        with self.assertRaises(ArchiveError):
            load(bad)

    def test_macosx_entries_ignored_for_detection(self):
        ok = os.path.join(self.dir, "mac.twbx")
        with zipfile.ZipFile(ok, "w") as zf:
            zf.writestr("__MACOSX/._in.twb", b"junk")
            zf.writestr("in.twb", b"<workbook />")
        data, _ = load(ok)
        self.assertEqual(data, b"<workbook />")

    def test_not_a_zip_raises(self):
        bad = os.path.join(self.dir, "fake.twbx")
        with open(bad, "wb") as fh:
            fh.write(b"not a zip")
        with self.assertRaises(ArchiveError):
            load(bad)
