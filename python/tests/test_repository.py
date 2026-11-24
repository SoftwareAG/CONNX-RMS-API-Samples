from contextlib import contextmanager

from connx_rms_showcase.config import Settings
from connx_rms_showcase.repository import CustomerRepository


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.requested = None

    def execute(self, sql, *params):
        return self

    def fetchmany(self, size):
        self.requested = size
        return self.rows[:size]


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor


def test_list_reads_only_offset_plus_limit_rows():
    rows = [(f"{n:05d}", f"Customer {n}   ", None, None, None, None, None, None) for n in range(10)]
    cursor = FakeCursor(rows)
    repository = CustomerRepository(Settings(_env_file=None))
    repository._connection = contextmanager(lambda: (yield FakeConnection(cursor)))

    customers = repository.list(limit=3, offset=4)

    assert cursor.requested == 7
    assert [c.customer_id for c in customers] == ["00004", "00005", "00006"]
    assert customers[0].name == "Customer 4"


def test_connection_string_leaves_plain_credentials_unquoted():
    # CONNX treats braces literally, so ordinary values must not be quoted.
    settings = Settings(_env_file=None, dsn="CONNX_RMS", user="demo", password="secret")
    assert settings.connection_string() == "DSN=CONNX_RMS;UID=demo;PWD=secret;"


def test_connection_string_quotes_credentials_with_separators():
    settings = Settings(_env_file=None, dsn="CONNX_RMS", user="demo", password="p;w}d")
    assert settings.connection_string() == "DSN=CONNX_RMS;UID=demo;PWD={p;w}}d};"
