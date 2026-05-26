#!/usr/bin/env python3
"""
sqlite2dbml — Generate DBML from a SQLite database.

Usage:
    python3 scripts/sqlite2dbml.py <path/to/database.db> [-o output.dbml]

Handles:
    - Tables, columns, types, primary keys, defaults, not-null
    - Logical foreign key relationships (by naming convention)
    - Indexes (unique and non-unique)
    - Multi-tenant server_user_id refs
    - Internal SQLite tables are excluded
"""

import argparse
import os
import sqlite3
import sys
from pathlib import Path


def map_type(sqlite_type: str) -> str:
    """Map SQLite type to DBML-compatible type."""
    if not sqlite_type:
        return "VARCHAR"
    t = sqlite_type.upper()
    if "INT" in t:
        return "INTEGER"
    if "FLOAT" in t or "DOUBLE" in t or "REAL" in t:
        return "FLOAT"
    if "BLOB" in t:
        return "BLOB"
    if "TIMESTAMP" in t or "DATETIME" in t or "DATE" in t:
        return "TIMESTAMP"
    if "BOOL" in t:
        return "BOOLEAN"
    if "TEXT" in t or "CHAR" in t or "CLOB" in t:
        return "VARCHAR"
    return t


def get_tables(conn) -> list[str]:
    cursor = conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name"
    )
    return [r[0] for r in cursor.fetchall()]


def get_columns(conn, table: str) -> list[dict]:
    cursor = conn.execute(f"PRAGMA table_info({table})")
    cols = []
    for row in cursor.fetchall():
        cid, name, dtype, notnull, default, pk = row
        cols.append({
            "name": name,
            "type": map_type(dtype),
            "notnull": bool(notnull),
            "pk": bool(pk),
            "default": default,
        })
    return cols


def get_indexes(conn, table: str) -> list[dict]:
    indexes = []
    for idx_row in conn.execute(f"PRAGMA index_list({table})").fetchall():
        seq, idx_name, unique = idx_row[0], idx_row[1], idx_row[2]
        cols = conn.execute(f"PRAGMA index_info({idx_name})").fetchall()
        col_names = [c[2] for c in cols]
        if idx_name.startswith("sqlite_autoindex"):
            continue  # skip auto-generated unique indexes
        indexes.append({
            "name": idx_name,
            "columns": col_names,
            "unique": bool(unique),
        })
    return indexes


def generate_dbml(db_path: str, output_path: str | None = None) -> str:
    conn = sqlite3.connect(db_path)
    tables = get_tables(conn)

    lines = []
    lines.append("// ═══════════════════════════════════════════════════════════════")
    lines.append("// Notes.ai — Database Schema (auto-generated)")
    lines.append(f"// Source: {os.path.basename(db_path)}")
    lines.append(f"// Generated: {sqlite3.connect(db_path).execute('SELECT datetime()').fetchone()[0]}")
    lines.append("// ═══════════════════════════════════════════════════════════════")
    lines.append("")

    for t in tables:
        cols = get_columns(conn, t)
        lines.append(f"Table {t} {{")
        for c in cols:
            parts = [c["name"], c["type"]]
            if c["pk"]:
                parts.append("[pk]")
            elif c["notnull"]:
                parts.append("[not null]")
            if c["default"] is not None:
                parts.append(f"[default: `{c['default']}`]")
            if t == "users" and c["name"] == "email":
                parts.append("[unique]")
            lines.append("  " + " ".join(parts))
        lines.append("}")
        lines.append("")

        # Indexes for this table
        for idx in get_indexes(conn, t):
            col_str = ", ".join(idx["columns"])
            unique = "unique " if idx["unique"] else ""
            lines.append(f"  Index: ({col_str}) [{unique}index]")
        if get_indexes(conn, t):
            lines.append("")

    # Logical foreign key relationships (SwiftData naming conventions)
    child_parent_map = [
        ("ZNOTEBOOK", "ZWORKSPACE", "ZWORKSPACE", "Z_PK"),
        ("ZPAGE", "ZNOTEBOOK", "ZNOTEBOOK", "Z_PK"),
        ("ZNOTETEXT", "ZPAGE", "ZPAGE", "Z_PK"),
        ("ZNOTEIMAGE", "ZPAGE", "ZPAGE", "Z_PK"),
        ("ZAUDIOOBJECT", "ZPAGE", "ZPAGE", "Z_PK"),
        ("ZSHAPEOBJECT", "ZPAGE", "ZPAGE", "Z_PK"),
        ("ZTABLEOBJECT", "ZPAGE", "ZPAGE", "Z_PK"),
        ("ZBROWSEROBJECT", "ZPAGE", "ZPAGE", "Z_PK"),
        ("ZAICHATMESSAGE", "ZSESSION", "ZAICHATSESSION", "Z_PK"),
    ]

    for child, col, parent, parent_col in child_parent_map:
        if child in tables and parent in tables:
            lines.append(f"Ref: {child}.{col} > {parent}.{parent_col}")

    # Multi-tenant server_user_id references
    for t in tables:
        if t != "users":
            cols = [c["name"] for c in get_columns(conn, t)]
            if "server_user_id" in cols:
                lines.append(f"Ref: {t}.server_user_id > users.id")

    lines.append("")
    lines.append("// ═══════════════════════════════════════════════════════════════")
    lines.append("// Relationships")
    lines.append("// ═══════════════════════════════════════════════════════════════")
    lines.append("")
    lines.append("// Workspace → Notebook → Page hierarchy")
    lines.append("//   ZWORKSPACE  1 ── * ZNOTEBOOK")
    lines.append("//   ZNOTEBOOK   1 ── * ZPAGE")
    lines.append("//")
    lines.append("// Page canvas objects")
    lines.append("//   ZPAGE  1 ── * ZNOTETEXT, ZNOTEIMAGE, ZAUDIOOBJECT,")
    lines.append("//                   ZSHAPEOBJECT, ZTABLEOBJECT, ZBROWSEROBJECT")
    lines.append("//")
    lines.append("// AI Chat")
    lines.append("//   ZAICHATSESSION  1 ── * ZAICHATMESSAGE")
    lines.append("//")
    lines.append("// Multi-tenant (all data tables)")
    lines.append("//   users  1 ── * (every content table via server_user_id)")
    lines.append("")

    conn.close()
    result = "\n".join(lines)

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w") as f:
            f.write(result)
        print(f"✅ DBML generated: {output_path}")
        print(f"   Tables: {len(tables)}")
        print(f"   Size: {len(result)} bytes")

    return result


def main():
    parser = argparse.ArgumentParser(description="Generate DBML from SQLite database")
    parser.add_argument("database", help="Path to SQLite database file")
    parser.add_argument("-o", "--output", default="db.dbml",
                        help="Output DBML file path (default: db.dbml)")
    args = parser.parse_args()

    if not os.path.exists(args.database):
        print(f"❌ Database not found: {args.database}")
        sys.exit(1)

    generate_dbml(args.database, args.output)


if __name__ == "__main__":
    main()
