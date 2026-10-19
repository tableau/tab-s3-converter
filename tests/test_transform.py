# Copyright (c) 2026, Salesforce, Inc.
# SPDX-License-Identifier: Apache-2.0

import unittest
import xml.etree.ElementTree as ET

from tab_s3_converter.transform import TransformError, convert

S3_DOC = """<workbook>
  <datasources>
    <datasource>
      <connection class='federated'>
        <named-connections>
          <named-connection caption='Amazon S3' name='s3.ABC'>
            <connection
              authentication='auth-none'
              class='s3'
              connectionData='{"appSnapshot": {"bucket": "example-bucket", "region": "us-west-2"}}'
              directory=''
              eps-alpha-version='12082020'
              eps-connection-id=''
              is-eps-taco='true'
              server='s3'
            />
          </named-connection>
        </named-connections>
        <relation connection='s3.ABC' name='Calcs.csv' table='[Calcs.csv]' type='table'>
          <columns>
            <column datatype='string' name='column_0' ordinal='0' />
            <column datatype='string' name='column_1' ordinal='1' />
          </columns>
        </relation>
        <metadata-records>
          <metadata-record class='column'>
            <remote-name>column_0</remote-name>
            <local-name>[column_0]</local-name>
            <parent-name>[Calcs.csv]</parent-name>
            <remote-alias>key</remote-alias>
            <ordinal>0</ordinal>
            <local-type>string</local-type>
          </metadata-record>
        </metadata-records>
      </connection>
      <object-graph>
        <objects>
          <object caption='Calcs.csv' id='x'>
            <properties context=''>
              <relation connection='s3.ABC' name='Calcs.csv' table='[Calcs.csv]' type='table'>
                <columns>
                  <column datatype='string' name='column_0' ordinal='0' />
                </columns>
              </relation>
            </properties>
          </object>
        </objects>
      </object-graph>
    </datasource>
  </datasources>
</workbook>"""


class ConvertTest(unittest.TestCase):
    def parse(self, text=S3_DOC):
        return ET.fromstring(text)

    def test_returns_count_of_converted_connections(self):
        root = self.parse()
        self.assertEqual(convert(root), 1)

    def test_no_s3_connection_returns_zero_and_no_change(self):
        root = ET.fromstring("<workbook><connection class='federated' /></workbook>")
        self.assertEqual(convert(root), 0)
        self.assertEqual(root.find(".//connection").get("class"), "federated")

    def test_connection_class_becomes_amazon_s3(self):
        root = self.parse()
        convert(root)
        classes = [c.get("class") for c in root.iter("connection")]
        self.assertIn("amazon-s3", classes)
        self.assertNotIn("s3", classes)

    def test_new_connection_has_exact_attribute_set(self):
        root = self.parse()
        convert(root)
        conn = next(c for c in root.iter("connection") if c.get("class") == "amazon-s3")
        self.assertEqual(
            dict(conn.attrib),
            {
                "authentication": "auth-user-pass",
                "bucket": "example-bucket",
                "class": "amazon-s3",
                "dbname": "",
                "location": "",
                "materialize": "",
                "region": "us-west-2",
                "sslmode": "",
                "username": "",
            },
        )

    def test_old_s3_only_attributes_are_dropped(self):
        root = self.parse()
        convert(root)
        conn = next(c for c in root.iter("connection") if c.get("class") == "amazon-s3")
        for gone in (
            "connectionData",
            "directory",
            "eps-alpha-version",
            "eps-connection-id",
            "is-eps-taco",
            "server",
        ):
            self.assertIsNone(conn.get(gone))

    def test_attribute_insertion_order_matches_native(self):
        root = self.parse()
        convert(root)
        conn = next(c for c in root.iter("connection") if c.get("class") == "amazon-s3")
        self.assertEqual(
            list(conn.attrib.keys()),
            [
                "authentication",
                "bucket",
                "class",
                "dbname",
                "location",
                "materialize",
                "region",
                "sslmode",
                "username",
            ],
        )

    def test_named_connection_id_is_renamed(self):
        root = self.parse()
        convert(root)
        names = [nc.get("name") for nc in root.iter("named-connection")]
        self.assertEqual(names, ["amazon-s3.ABC"])

    def test_all_relation_references_are_rewritten(self):
        root = self.parse()
        convert(root)
        refs = [r.get("connection") for r in root.iter("relation")]
        self.assertEqual(refs, ["amazon-s3.ABC", "amazon-s3.ABC"])

    def test_relation_column_list_replaced_with_csv_options(self):
        root = self.parse()
        convert(root)
        for relation in root.iter("relation"):
            columns = relation.find("columns")
            self.assertEqual(len(list(columns)), 0)  # no <column> children
            self.assertEqual(columns.get("character-set"), "UTF-8")
            self.assertEqual(columns.get("header"), "yes")
            self.assertEqual(columns.get("locale"), "en_US")
            self.assertEqual(columns.get("separator"), ",")
            self.assertEqual(columns.get("text-qualifier"), '"')

    def test_metadata_ordinal_local_name_and_type_preserved(self):
        root = self.parse()
        convert(root)
        rec = root.find(".//metadata-record")
        self.assertEqual(rec.find("local-name").text, "[column_0]")
        self.assertEqual(rec.find("ordinal").text, "0")
        self.assertEqual(rec.find("local-type").text, "string")

    def test_remote_name_takes_content_of_remote_alias(self):
        root = self.parse()
        convert(root)
        rec = root.find(".//metadata-record")
        self.assertEqual(rec.find("remote-name").text, "key")
        # remote-alias itself is left in place unchanged.
        self.assertEqual(rec.find("remote-alias").text, "key")

    def test_remote_name_untouched_when_alias_absent(self):
        no_alias = S3_DOC.replace("<remote-alias>key</remote-alias>\n            ", "")
        root = ET.fromstring(no_alias)
        convert(root)
        rec = root.find(".//metadata-record")
        self.assertIsNone(rec.find("remote-alias"))
        self.assertEqual(rec.find("remote-name").text, "column_0")

    def test_remote_name_untouched_when_parent_name_does_not_match(self):
        # parent-name points at a table no converted relation references, so the
        # record must be left alone even though remote-alias is present.
        mismatch = S3_DOC.replace(
            "<parent-name>[Calcs.csv]</parent-name>",
            "<parent-name>[Other.csv]</parent-name>",
        )
        root = ET.fromstring(mismatch)
        convert(root)
        rec = root.find(".//metadata-record")
        self.assertEqual(rec.find("remote-name").text, "column_0")

    def test_remote_name_untouched_when_parent_name_absent(self):
        no_parent = S3_DOC.replace("<parent-name>[Calcs.csv]</parent-name>\n            ", "")
        root = ET.fromstring(no_parent)
        convert(root)
        rec = root.find(".//metadata-record")
        self.assertIsNone(rec.find("parent-name"))
        self.assertEqual(rec.find("remote-name").text, "column_0")

    def test_bad_connection_data_raises_transform_error_naming_connection(self):
        bad = S3_DOC.replace(
            'connectionData=\'{"appSnapshot": {"bucket": "example-bucket", "region": "us-west-2"}}\'',
            "connectionData='not json'",
        )
        root = ET.fromstring(bad)
        with self.assertRaises(TransformError) as ctx:
            convert(root)
        self.assertIn("s3.ABC", str(ctx.exception))

    def test_two_s3_connections_both_converted(self):
        # Remove the closing tags from S3_DOC and append a second datasource
        without_closing = S3_DOC[: S3_DOC.rfind("</datasources>")]
        two = (
            without_closing
            + """
    <datasource>
      <connection class='federated'>
        <named-connections>
          <named-connection name='s3.DEF'>
            <connection
              class='s3'
              connectionData='{"appSnapshot": {"bucket": "b2", "region": "r2"}}'
              server='s3'
            />
          </named-connection>
        </named-connections>
        <relation connection='s3.DEF' name='x' table='[x]' type='table'>
          <columns><column name='c0' ordinal='0' /></columns>
        </relation>
      </connection>
    </datasource>
  </datasources>
</workbook>"""
        )
        root = ET.fromstring(two)
        self.assertEqual(convert(root), 2)
        self.assertEqual(
            sorted(nc.get("name") for nc in root.iter("named-connection")),
            ["amazon-s3.ABC", "amazon-s3.DEF"],
        )

    def test_s3_connection_with_non_s3_named_connection_raises_error(self):
        """s3 connection inside named-connection not starting with 's3.' raises TransformError."""
        bad = S3_DOC.replace("name='s3.ABC'", "name='legacy.ABC'")
        root = ET.fromstring(bad)
        with self.assertRaises(TransformError) as ctx:
            convert(root)
        self.assertIn("legacy.ABC", str(ctx.exception))

    def test_s3_connection_without_named_connection_raises_error(self):
        """s3 connection with no enclosing named-connection raises TransformError."""
        orphan = """<workbook>
  <datasources>
    <datasource>
      <connection class='federated'>
        <connection
          class='s3'
          connectionData='{"appSnapshot": {"bucket": "b1", "region": "r1"}}'
          server='s3'
        />
      </connection>
    </datasource>
  </datasources>
</workbook>"""
        root = ET.fromstring(orphan)
        with self.assertRaises(TransformError) as ctx:
            convert(root)
        self.assertIn("expected an enclosing named-connection", str(ctx.exception))

    def test_named_connection_without_name_attribute_raises_transform_error(self):
        """named-connection with no name attribute raises TransformError (not AttributeError)."""
        no_name = """<workbook>
  <datasources>
    <datasource>
      <connection class='federated'>
        <named-connections>
          <named-connection caption='No Name'>
            <connection
              class='s3'
              connectionData='{"appSnapshot": {"bucket": "b1", "region": "r1"}}'
              server='s3'
            />
          </named-connection>
        </named-connections>
      </connection>
    </datasource>
  </datasources>
</workbook>"""
        root = ET.fromstring(no_name)
        with self.assertRaises(TransformError) as ctx:
            convert(root)
        self.assertIn("expected an enclosing named-connection", str(ctx.exception))
