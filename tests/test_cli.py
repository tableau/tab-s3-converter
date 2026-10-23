# Copyright (c) 2026, Salesforce, Inc.
# SPDX-License-Identifier: Apache-2.0

# tests/test_cli.py
import contextlib
import io
import os
import sys
import tempfile
import unittest

from tab_s3_converter.cli import default_output_path, run

MINIMAL_S3 = (
    b"<?xml version='1.0' encoding='utf-8' ?>\n"
    b"<workbook>"
    b"<connection class='federated'><named-connections>"
    b"<named-connection name='s3.ABC'>"
    b"<connection class='s3' connectionData='"
    b'{"appSnapshot": {"bucket": "b", "region": "r"}}\' server=\'s3\' />'
    b"</named-connection></named-connections>"
    b"<relation connection='s3.ABC' name='x' table='[x]' type='table'>"
    b"<columns><column name='c0' ordinal='0' /></columns></relation>"
    b"</connection></workbook>\n"
)

NO_S3 = (
    b"<?xml version='1.0' encoding='utf-8' ?>\n"
    b"<workbook><connection class='federated' /></workbook>\n"
)


def run_capturing(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = run(argv)
    return code, out.getvalue(), err.getvalue()


class DefaultOutputTest(unittest.TestCase):
    def test_inserts_converted_before_extension(self):
        self.assertEqual(default_output_path("a/b.twb"), "a/b.converted.twb")
        self.assertEqual(default_output_path("x.twbx"), "x.converted.twbx")


class RunTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def _write(self, name, data):
        path = os.path.join(self.dir, name)
        with open(path, "wb") as fh:
            fh.write(data)
        return path

    def test_success_writes_converted_file(self):
        src = self._write("in.twb", MINIMAL_S3)
        out = os.path.join(self.dir, "out.twb")
        code, stdout, _ = run_capturing([src, "-o", out])
        self.assertEqual(code, 0)
        self.assertIn("converted 1", stdout)
        with open(out, "rb") as fh:
            body = fh.read()
        self.assertIn(b"amazon-s3", body)
        self.assertNotIn(b"class='s3'", body)
        self.assertNotIn(b'class="s3"', body)

    def test_missing_input_exits_2(self):
        code, _, err = run_capturing([os.path.join(self.dir, "nope.twb")])
        self.assertEqual(code, 2)
        self.assertIn("error:", err)

    def test_bad_extension_exits_2(self):
        src = self._write("in.xml", b"<x/>")
        code, _, err = run_capturing([src])
        self.assertEqual(code, 2)
        self.assertIn("error:", err)

    def test_existing_output_without_force_exits_2(self):
        src = self._write("in.twb", MINIMAL_S3)
        out = self._write("out.twb", b"existing")
        code, _, err = run_capturing([src, "-o", out])
        self.assertEqual(code, 2)
        self.assertIn("error:", err)

    def test_force_overwrites_existing_output(self):
        src = self._write("in.twb", MINIMAL_S3)
        out = self._write("out.twb", b"existing")
        code, _, _ = run_capturing([src, "-o", out, "--force"])
        self.assertEqual(code, 0)

    def test_no_s3_connections_exits_0_writes_nothing(self):
        src = self._write("in.twb", NO_S3)
        out = os.path.join(self.dir, "out.twb")
        code, stdout, _ = run_capturing([src, "-o", out])
        self.assertEqual(code, 0)
        self.assertIn("nothing to convert", stdout)
        self.assertFalse(os.path.exists(out))

    def test_malformed_xml_exits_3(self):
        src = self._write("in.twb", b"<workbook><unclosed>")
        code, _, err = run_capturing([src])
        self.assertEqual(code, 3)
        self.assertIn("error:", err)

    def test_bad_connection_data_exits_4(self):
        broken = MINIMAL_S3.replace(
            b'connectionData=\'{"appSnapshot": {"bucket": "b", "region": "r"}}\'',
            b"connectionData='not json'",
        )
        src = self._write("in.twb", broken)
        code, _, err = run_capturing([src])
        self.assertEqual(code, 4)
        self.assertIn("error:", err)

    def test_default_output_used_when_no_o(self):
        src = self._write("in.twb", MINIMAL_S3)
        code, _, _ = run_capturing([src])
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(os.path.join(self.dir, "in.converted.twb")))

    @unittest.skipIf(
        sys.platform.startswith("win") or getattr(os, "geteuid", lambda: 1000)() == 0,
        "skip as root or on Windows",
    )
    def test_unreadable_input_exits_2(self):
        """Unreadable input file raises OSError and exits 2 with error message."""
        src = self._write("in.twb", MINIMAL_S3)
        try:
            os.chmod(src, 0o000)
            code, _, err = run_capturing([src])
            self.assertEqual(code, 2)
            self.assertIn("error:", err)
        finally:
            os.chmod(src, 0o644)

    def test_unwritable_output_exits_2(self):
        """Output path in non-existent directory raises OSError and exits 2."""
        src = self._write("in.twb", MINIMAL_S3)
        out = os.path.join(self.dir, "nope_subdir", "out.twb")
        code, _, err = run_capturing([src, "-o", out])
        self.assertEqual(code, 2)
        self.assertIn("error:", err)
