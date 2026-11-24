from collections.abc import Iterator
from contextlib import contextmanager

import pyodbc

from .config import Settings
from .models import Customer

_COLUMNS = "customerid, customername, customeraddress, customercity, customerstate, customerzip, customercountry, customerphone"


class CustomerNotFoundError(Exception):
    pass


class CustomerRepository:
    """Read-only access to the mapped RMS customer file. The samples never write to RMS."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def table(self) -> str:
        # This is deployment configuration, not request input. Keep it a fixed
        # identifier supplied by the operator; values are never user-controlled.
        return self.settings.table

    @contextmanager
    def _connection(self) -> Iterator[pyodbc.Connection]:
        connection = pyodbc.connect(
            self.settings.connection_string(),
            timeout=self.settings.connect_timeout_seconds,
            autocommit=True,
        )
        connection.timeout = self.settings.query_timeout_seconds
        try:
            yield connection
        finally:
            connection.close()

    @staticmethod
    def _customer(row: pyodbc.Row) -> Customer:
        values = zip(_COLUMNS.split(", "), row, strict=True)
        return Customer.model_validate({column: (value.rstrip() if isinstance(value, str) else value) for column, value in values})

    def list(self, limit: int, offset: int) -> list[Customer]:
        # CONNX is configured for strict ANSI-92, so avoid OFFSET/FETCH. Read only
        # the first offset + limit rows of the ordered result instead of the whole
        # table, then apply the presentation window.
        sql = f"SELECT {_COLUMNS} FROM {self.table} ORDER BY customerid"
        with self._connection() as connection:
            cursor = connection.cursor()
            rows = cursor.execute(sql).fetchmany(offset + limit)
        return [self._customer(row) for row in rows[offset:]]

    def ping(self) -> None:
        """Verify that CONNX accepts a trivial query on the configured connection."""
        with self._connection() as connection:
            connection.cursor().execute("SELECT 1").fetchone()

    def get(self, customer_id: str) -> Customer:
        with self._connection() as connection:
            cursor = connection.cursor()
            row = cursor.execute(f"SELECT {_COLUMNS} FROM {self.table} WHERE customerid = ?", customer_id).fetchone()
        if row is None:
            raise CustomerNotFoundError(customer_id)
        return self._customer(row)
