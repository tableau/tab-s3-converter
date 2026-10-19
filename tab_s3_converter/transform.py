# Copyright (c) 2026, Salesforce, Inc.
# SPDX-License-Identifier: Apache-2.0

"""Convert legacy s3 connections in a Tableau ElementTree to amazon-s3."""

from .connection_data import ConnectionDataError, parse_connection_data

OLD_PREFIX = "s3."
NEW_PREFIX = "amazon-s3."

AMAZON_S3_ATTRS_ORDER = [
    "authentication",
    "bucket",
    "class",
    "dbname",
    "location",
    "materialize",
    "region",
    "sslmode",
    "username",
]

RELATION_COLUMNS_ATTRS = {
    "character-set": "UTF-8",
    "header": "yes",
    "locale": "en_US",
    "separator": ",",
    "text-qualifier": '"',
}


class TransformError(Exception):
    """A single s3 connection could not be converted."""


def _build_parent_map(root):
    return {child: parent for parent in root.iter() for child in parent}


def _named_connection_of(conn, parents):
    node = parents.get(conn)
    while node is not None and node.tag != "named-connection":
        node = parents.get(node)
    return node


def _rewrite_connection_element(conn, bucket, region):
    conn.attrib.clear()
    values = {
        "authentication": "auth-user-pass",
        "bucket": bucket,
        "class": "amazon-s3",
        "dbname": "",
        "location": "",
        "materialize": "",
        "region": region,
        "sslmode": "",
        "username": "",
    }
    for key in AMAZON_S3_ATTRS_ORDER:
        conn.set(key, values[key])


def _federated_connection_of(node, parents):
    while node is not None and not (node.tag == "connection" and node.get("class") == "federated"):
        node = parents.get(node)
    return node


def _carry_remote_alias_to_remote_name(federated, tables):
    """Set each metadata-record's <remote-name> to its <remote-alias> content.

    The legacy s3 connector stores a generic <remote-name> (e.g. ``column_0``)
    while the real CSV header lives in <remote-alias>. Carry the alias forward
    into remote-name so downstream consumers see the header name.

    Only records whose <parent-name> matches the ``table`` attribute of a
    relation referencing the s3 connection being converted are rewritten
    (``tables`` is that set of table values). Records lacking either element,
    or whose <parent-name> is absent or unmatched, are left untouched.
    """
    if federated is None:
        return
    for record in federated.iter("metadata-record"):
        parent_name = record.find("parent-name")
        if parent_name is None or parent_name.text not in tables:
            continue
        remote_name = record.find("remote-name")
        remote_alias = record.find("remote-alias")
        if remote_name is not None and remote_alias is not None:
            remote_name.text = remote_alias.text


def _relation_tables_for(root, connection_id):
    """Return the set of ``table`` values on relations referencing connection_id."""
    tables = set()
    for relation in root.iter("relation"):
        if relation.get("connection") == connection_id:
            table = relation.get("table")
            if table is not None:
                tables.add(table)
    return tables


def _replace_relation_columns(root, old_id, new_id):
    for relation in root.iter("relation"):
        if relation.get("connection") != old_id:
            continue
        relation.set("connection", new_id)
        columns = relation.find("columns")
        # Only replace a column *list*; leave already-CSV-options columns alone.
        if columns is not None and len(list(columns)) > 0:
            for child in list(columns):
                columns.remove(child)
            columns.attrib.clear()
            for key, value in RELATION_COLUMNS_ATTRS.items():
                columns.set(key, value)


def convert(root):
    """Convert every s3 connection in place; return how many were converted.

    All-or-nothing: raises TransformError before any partial state matters to
    the caller (the caller discards the tree on raise).
    """
    parents = _build_parent_map(root)
    s3_conns = [c for c in root.iter("connection") if c.get("class") == "s3"]
    if not s3_conns:
        return 0

    for conn in s3_conns:
        named = _named_connection_of(conn, parents)
        old_id = named.get("name") if named is not None else None
        label = old_id or "<unknown>"

        # Enforce all-or-nothing: s3 connection MUST have an enclosing
        # named-connection whose name starts with "s3."
        if named is None or not old_id or not old_id.startswith(OLD_PREFIX):
            raise TransformError(
                f"connection {label}: expected an enclosing named-connection "
                f"with a name starting with 's3.'"
            )

        try:
            fields = parse_connection_data(conn.get("connectionData", ""))
        except ConnectionDataError as exc:
            raise TransformError(f"connection {label}: {exc}") from exc

        _rewrite_connection_element(conn, fields["bucket"], fields["region"])

        # Capture the relations' table values BEFORE the rename below rewrites
        # their connection attribute from old_id to new_id.
        tables = _relation_tables_for(root, old_id)

        new_id = NEW_PREFIX + old_id[len(OLD_PREFIX) :]
        named.set("name", new_id)
        _replace_relation_columns(root, old_id, new_id)
        _carry_remote_alias_to_remote_name(_federated_connection_of(conn, parents), tables)

    return len(s3_conns)
