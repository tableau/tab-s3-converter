# Copyright (c) 2026, Salesforce, Inc.
# SPDX-License-Identifier: Apache-2.0

"""Parse Tableau XML preserving the declaration + leading comment, and re-serialize."""

import xml.etree.ElementTree as ET


def parse_document(xml_bytes):
    """Return (root, prefix). prefix is the verbatim bytes before the root tag.

    Raises xml.etree.ElementTree.ParseError on malformed XML.
    """
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    root = ET.fromstring(xml_bytes, parser=parser)
    marker = b"<" + root.tag.encode("utf-8")
    index = xml_bytes.find(marker)
    prefix = xml_bytes[:index] if index != -1 else b""
    return root, prefix


def serialize_document(root, prefix):
    """Return prefix + ET-serialized root, UTF-8 encoded, with no extra declaration."""
    body = ET.tostring(root, encoding="unicode").encode("utf-8")
    return prefix + body
