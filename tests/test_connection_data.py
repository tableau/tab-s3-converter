# Copyright (c) 2026, Salesforce, Inc.
# SPDX-License-Identifier: Apache-2.0

import unittest

from tab_s3_converter.connection_data import ConnectionDataError, parse_connection_data


class ParseConnectionDataTest(unittest.TestCase):
    def test_reads_bucket_and_region_from_app_snapshot(self):
        raw = '{"appSnapshot": {"bucket": "b1", "region": "us-west-2"}}'
        self.assertEqual(
            parse_connection_data(raw),
            {"bucket": "b1", "region": "us-west-2"},
        )

    def test_prefers_app_snapshot_over_handler_inputs(self):
        raw = (
            '{"appSnapshot": {"bucket": "snap", "region": "r-snap"},'
            ' "handlerInputs": [{"data": {"bucket": "hand", "region": "r-hand"}}]}'
        )
        self.assertEqual(
            parse_connection_data(raw),
            {"bucket": "snap", "region": "r-snap"},
        )

    def test_falls_back_to_handler_inputs_when_app_snapshot_absent(self):
        raw = '{"handlerInputs": [{"data": {"bucket": "hb", "region": "hr"}}]}'
        self.assertEqual(
            parse_connection_data(raw),
            {"bucket": "hb", "region": "hr"},
        )

    def test_falls_back_when_app_snapshot_missing_region(self):
        raw = (
            '{"appSnapshot": {"bucket": "snap"},'
            ' "handlerInputs": [{"data": {"bucket": "hb", "region": "hr"}}]}'
        )
        self.assertEqual(
            parse_connection_data(raw),
            {"bucket": "hb", "region": "hr"},
        )

    def test_raises_on_invalid_json(self):
        with self.assertRaises(ConnectionDataError):
            parse_connection_data("{not json")

    def test_raises_when_bucket_or_region_missing_everywhere(self):
        with self.assertRaises(ConnectionDataError):
            parse_connection_data('{"appSnapshot": {"bucket": "b"}}')

    def test_raises_on_empty_values(self):
        with self.assertRaises(ConnectionDataError):
            parse_connection_data('{"appSnapshot": {"bucket": "", "region": ""}}')
