# Copyright (c) 2026, Salesforce, Inc.
# SPDX-License-Identifier: Apache-2.0

"""Parse the JSON blob carried in a legacy s3 connection's connectionData attribute."""

import json


class ConnectionDataError(Exception):
    """Raised when connectionData cannot be parsed or lacks bucket/region."""


def _candidate_sources(data):
    """Yield dicts that may carry bucket/region, most-preferred first."""
    snapshot = data.get("appSnapshot")
    if isinstance(snapshot, dict):
        yield snapshot
    handler_inputs = data.get("handlerInputs")
    if isinstance(handler_inputs, list):
        for entry in handler_inputs:
            if isinstance(entry, dict) and isinstance(entry.get("data"), dict):
                yield entry["data"]


def parse_connection_data(raw):
    """Return {"bucket", "region"} from a connectionData JSON string.

    Reads appSnapshot first, then handlerInputs[].data. Raises
    ConnectionDataError on invalid JSON or if no source has both values.
    """
    try:
        data = json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise ConnectionDataError("connectionData is not valid JSON") from exc
    if not isinstance(data, dict):
        raise ConnectionDataError("connectionData is not a JSON object")
    for source in _candidate_sources(data):
        bucket = source.get("bucket")
        region = source.get("region")
        if bucket and region:
            return {"bucket": bucket, "region": region}
    raise ConnectionDataError("connectionData has no bucket/region")
