"""Read-only: list the columns and primary key of the configured CONNX table.

Use it when adapting the samples to your own RMS file. It reads only ODBC catalog
metadata and never prints row contents or credentials.
"""

import sys

import pyodbc

from connx_rms_showcase.config import get_settings


def main() -> int:
    settings = get_settings()
    parts = settings.table.split(".")
    if len(parts) != 3:
        print(f"CONNX_RMS_TABLE must be catalog.schema.table, got {settings.table!r}.", file=sys.stderr)
        return 1
    catalog, schema, table = parts
    try:
        with pyodbc.connect(settings.connection_string(), timeout=settings.connect_timeout_seconds) as connection:
            cursor = connection.cursor()
            columns = cursor.columns(table=table, catalog=catalog, schema=schema).fetchall()
            key = [row.column_name for row in sorted(cursor.primaryKeys(table=table, catalog=catalog, schema=schema).fetchall(), key=lambda row: row.key_seq)]
    except pyodbc.Error as exc:
        print(f"CONNX/ODBC error: {exc}", file=sys.stderr)
        return 3
    if not columns:
        print(f"No columns found for {settings.table}. Check CONNX_RMS_TABLE and that the DSN points at the right CDD.", file=sys.stderr)
        return 1
    print(f"{settings.table}")
    print(f"{'Column':<32} {'Type':<12} {'Size':>6}  Nullable")
    for column in columns:
        print(f"{column.column_name:<32} {column.type_name:<12} {column.column_size:>6}  {'yes' if column.nullable else 'no'}")
    print(f"Primary key: {', '.join(key) if key else '(none reported)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
