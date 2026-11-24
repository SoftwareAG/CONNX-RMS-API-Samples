"""Read-only connectivity smoke test for the configured CONNX RMS table."""
import sys
from pathlib import Path

import pyodbc

sys.path.insert(0, str(Path(__file__).parent / "src"))
from connx_rms_showcase.config import get_settings


def main() -> int:
    settings = get_settings()
    table = settings.table
    print(f"Connecting through DSN '{settings.dsn}'...")
    try:
        connection = pyodbc.connect(settings.connection_string(), timeout=settings.connect_timeout_seconds, autocommit=True)
        try:
            connection.timeout = settings.query_timeout_seconds
            cursor = connection.cursor()
            row = cursor.execute(f"SELECT * FROM {table}").fetchone()
            if row is None:
                print(f"SUCCESS: connected and queried {table}; table returned no rows.")
            else:
                print(f"SUCCESS: connected and queried {table}; at least one row is available ({len(row)} columns).")
            return 0
        finally:
            connection.close()
    except pyodbc.Error as exc:
        print("FAILED: CONNX/ODBC could not access the configured RMS table.", file=sys.stderr)
        print(f"ODBC error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
