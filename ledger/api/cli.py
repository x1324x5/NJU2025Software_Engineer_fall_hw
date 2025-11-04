"""Simple CLI entrypoint."""
from __future__ import annotations
import argparse

def main() -> None:
    parser = argparse.ArgumentParser(description="Ledger CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("hello", help="Say hello")
    args = parser.parse_args()
    if args.command == "hello":
        print("Hello from Ledger CLI")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
