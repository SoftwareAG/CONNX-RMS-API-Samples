import sys

import pyodbc
import pytest

from connx_rms_showcase import cli
from connx_rms_showcase.models import Customer
from connx_rms_showcase.repository import CustomerNotFoundError


class FakeRepository:
    def __init__(self, settings=None):
        pass

    def list(self, limit, offset):
        FakeRepository.window = (limit, offset)
        return [Customer(customerid="ABCDE", customername="Ada Demo", customercity="Boston")]

    def get(self, customer_id):
        if customer_id != "ABCDE":
            raise CustomerNotFoundError(customer_id)
        return Customer(customerid="ABCDE", customername="Ada Demo", customercity="Boston")


class BrokenRepository(FakeRepository):
    def get(self, customer_id):
        raise pyodbc.Error("connection failed")


def run_cli(monkeypatch, repository_class, *args):
    monkeypatch.setattr(cli, "CustomerRepository", repository_class)
    monkeypatch.setattr(sys, "argv", ["cli", *args])
    cli.main()


def test_cli_list_passes_window_and_prints_json(monkeypatch, capsys):
    run_cli(monkeypatch, FakeRepository, "list", "--limit", "5", "--offset", "2")
    assert FakeRepository.window == (5, 2)
    assert '"customer_id": "ABCDE"' in capsys.readouterr().out


def test_cli_get_prints_customer(monkeypatch, capsys):
    run_cli(monkeypatch, FakeRepository, "get", "ABCDE")
    assert '"city": "Boston"' in capsys.readouterr().out


def test_cli_reports_not_found_without_traceback(monkeypatch, capsys):
    with pytest.raises(SystemExit) as exit_info:
        run_cli(monkeypatch, FakeRepository, "get", "ZZZZZ")
    assert exit_info.value.code == 1
    assert "Customer not found." in capsys.readouterr().err


def test_cli_reports_odbc_error_without_traceback(monkeypatch, capsys):
    with pytest.raises(SystemExit) as exit_info:
        run_cli(monkeypatch, BrokenRepository, "get", "ABCDE")
    assert exit_info.value.code == 3
    assert "CONNX/ODBC error" in capsys.readouterr().err


@pytest.mark.parametrize("command", ["create", "update", "delete"])
def test_cli_has_no_write_commands(monkeypatch, command):
    with pytest.raises(SystemExit) as exit_info:
        run_cli(monkeypatch, FakeRepository, command, "ABCDE")
    assert exit_info.value.code == 2
