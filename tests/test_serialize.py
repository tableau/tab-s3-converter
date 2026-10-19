# Copyright (c) 2026, Salesforce, Inc.
# SPDX-License-Identifier: Apache-2.0

import unittest
import xml.etree.ElementTree as ET

from tab_s3_converter.serialize import parse_document, serialize_document

DOC = (
    b"<?xml version='1.0' encoding='utf-8' ?>\r\n\r\n"
    b"<!-- build main.26.0707.1649 -->\r\n"
    b"<workbook version='18.1'><datasources /></workbook>\r\n"
)


class SerializeTest(unittest.TestCase):
    def test_prefix_captures_declaration_and_comment(self):
        root, prefix = parse_document(DOC)
        self.assertEqual(root.tag, "workbook")
        self.assertIn(b"<?xml", prefix)
        self.assertIn(b"<!-- build main.26.0707.1649 -->", prefix)
        self.assertTrue(prefix.rstrip().endswith(b"-->"))

    def test_roundtrip_preserves_declaration_and_comment(self):
        root, prefix = parse_document(DOC)
        out = serialize_document(root, prefix)
        self.assertTrue(out.startswith(b"<?xml version='1.0' encoding='utf-8' ?>"))
        self.assertIn(b"<!-- build main.26.0707.1649 -->", out)
        self.assertIn(b"<workbook", out)

    def test_output_reparses_to_equivalent_tree(self):
        root, prefix = parse_document(DOC)
        out = serialize_document(root, prefix)
        reparsed = ET.fromstring(out)
        self.assertEqual(reparsed.tag, "workbook")
        self.assertEqual(reparsed.get("version"), "18.1")

    def test_only_one_xml_declaration(self):
        root, prefix = parse_document(DOC)
        out = serialize_document(root, prefix)
        self.assertEqual(out.count(b"<?xml"), 1)

    def test_malformed_xml_raises_parse_error(self):
        with self.assertRaises(ET.ParseError):
            parse_document(b"<workbook><unclosed>")

    def test_datasource_root_supported(self):
        doc = b"<?xml version='1.0' encoding='utf-8' ?>\n<datasource name='x' />\n"
        root, prefix = parse_document(doc)
        self.assertEqual(root.tag, "datasource")
        out = serialize_document(root, prefix)
        self.assertIn(b"<datasource", out)
