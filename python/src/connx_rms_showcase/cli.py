"""Read-only command line access to the mapped RMS customer file."""

import argparse
import json
import sys

import pyodbc

from .config import get_settings
from .repository import CustomerNotFoundError, CustomerRepository


def _print(customer: object) -> None:
    payload = customer.model_dump() if hasattr(customer, "model_dump") else [item.model_dump() for item in customer]
    print(json.dumps(payload, indent=2, default=str))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read customers from the CONNX RMS mapping (read-only)")
    commands = parser.add_subparsers(dest="command", required=True)

    list_parser = commands.add_parser("list", help="list customers in key order")
    list_parser.add_argument("--limit", type=int, default=10)
    list_parser.add_argument("--offset", type=int, default=0)

    get_parser = commands.add_parser("get", help="show one customer by ID")
    get_parser.add_argument("customer_id")

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    repository = CustomerRepository(get_settings())
    try:
        if args.command == "list":
            _print(repository.list(args.limit, args.offset))
        else:
            _print(repository.get(args.customer_id))
    except CustomerNotFoundError:
        parser.exit(1, "Customer not found.\n")
    except pyodbc.Error as exc:
        print(f"CONNX/ODBC error: {exc}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
