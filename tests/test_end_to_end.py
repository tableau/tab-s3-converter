# Copyright (c) 2026, Salesforce, Inc.
# SPDX-License-Identifier: Apache-2.0

# tests/test_end_to_end.py
import contextlib
import io
import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

from tab_s3_converter import serialize
from tab_s3_converter.cli import run

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def run_capturing(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = run(argv)
    return code, out.getvalue(), err.getvalue()


class EndToEndTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_converts_real_eps_workbook(self):
        out = os.path.join(self.dir, "out.twb")
        code, _, _ = run_capturing([os.path.join(FIX, "s3_eps.twb"), "-o", out])
        self.assertEqual(code, 0)
        root = ET.parse(out).getroot()
        classes = [c.get("class") for c in root.iter("connection")]
        self.assertIn("amazon-s3", classes)
        self.assertNotIn("s3", classes)

    def test_ordinals_and_local_names_preserved(self):
        out = os.path.join(self.dir, "out.twb")
        run_capturing([os.path.join(FIX, "s3_eps.twb"), "-o", out])
        root = ET.parse(out).getroot()
        records = root.findall(".//metadata-record")
        ordinals = [r.find("ordinal").text for r in records if r.find("ordinal") is not None]
        local_names = [
            r.find("local-name").text for r in records if r.find("local-name") is not None
        ]
        self.assertEqual(ordinals, [str(i) for i in range(27)])
        self.assertIn("[column_0]", local_names)
        # local-type carried forward unchanged (all string in this fixture)
        local_types = {
            r.find("local-type").text for r in records if r.find("local-type") is not None
        }
        self.assertEqual(local_types, {"string"})

    def test_remote_name_takes_remote_alias_on_real_fixture(self):
        out = os.path.join(self.dir, "out.twb")
        run_capturing([os.path.join(FIX, "s3_eps.twb"), "-o", out])
        root = ET.parse(out).getroot()
        records = root.findall(".//metadata-record[@class='column']")
        # In the source the header lives in remote-alias (e.g. "key", "num0");
        # after conversion remote-name must equal remote-alias for every record.
        for rec in records:
            remote_name = rec.find("remote-name")
            remote_alias = rec.find("remote-alias")
            self.assertIsNotNone(remote_alias)
            self.assertEqual(remote_name.text, remote_alias.text)
        # And the first column really did change away from the generic name.
        self.assertEqual(records[0].find("remote-name").text, "key")

    def test_idempotent_second_run_finds_nothing(self):
        out = os.path.join(self.dir, "out.twb")
        run_capturing([os.path.join(FIX, "s3_eps.twb"), "-o", out])
        out2 = os.path.join(self.dir, "out2.twb")
        code, stdout, _ = run_capturing([out, "-o", out2])
        self.assertEqual(code, 0)
        self.assertIn("nothing to convert", stdout)
        self.assertFalse(os.path.exists(out2))

    def test_worksheets_and_thumbnail_survive(self):
        out = os.path.join(self.dir, "out.twb")
        run_capturing([os.path.join(FIX, "s3_eps.twb"), "-o", out])
        root = ET.parse(out).getroot()
        self.assertIsNotNone(root.find(".//worksheet"))
        self.assertIsNotNone(root.find(".//thumbnail"))

    def test_twbx_supporting_files_preserved(self):
        out = os.path.join(self.dir, "out.twbx")
        code, _, _ = run_capturing([os.path.join(FIX, "s3_eps.twbx"), "-o", out])
        self.assertEqual(code, 0)
        with zipfile.ZipFile(out) as zf:
            self.assertEqual(zf.read("Data/dummy.txt"), b"supporting file")
            self.assertIn(b"amazon-s3", zf.read("s3_eps.twb"))


class SecurityTest(unittest.TestCase):
    def test_billion_laughs_does_not_expand(self):
        bomb = (
            b"<?xml version='1.0'?>"
            b"<!DOCTYPE lolz [<!ENTITY a 'aaaaaaaaaa'>"
            b"<!ENTITY b '&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;'>]>"
            b"<workbook>&b;</workbook>"
        )
        # ET must not blow up memory: it either raises or leaves entity unexpanded.
        try:
            root, _ = serialize.parse_document(bomb)
        except ET.ParseError:
            return
        text = root.text or ""
        self.assertLess(len(text), 10_000)

    def test_zip_entry_with_traversal_name_stays_in_archive(self):
        d = tempfile.mkdtemp()
        src = os.path.join(d, "in.twbx")
        with zipfile.ZipFile(src, "w") as zf:
            zf.writestr("in.twb", b"<workbook><connection class='federated'/></workbook>")
            zf.writestr("../evil.txt", b"pwn")
        out = os.path.join(d, "out.twbx")
        # No s3 connections -> exits 0, writes nothing; the point is load() must not
        # write '../evil.txt' to disk during processing.
        run_capturing([src, "-o", out])
        self.assertFalse(os.path.exists(os.path.join(d, "..", "evil.txt")))
